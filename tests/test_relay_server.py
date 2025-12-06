"""Tests for RelayServer class."""

from orchestration.MCP.relay_server import RelayServer


class MockRelay:
    """Mock relay for testing."""

    def __init__(self, name: str, should_fail: bool = False, error_msg: str = "Mock error"):
        self.name = name
        self.should_fail = should_fail
        self.error_msg = error_msg
        self.sent_payloads = []

    def send(self, payload):
        if self.should_fail:
            raise Exception(self.error_msg)
        self.sent_payloads.append(payload)


class MockRelayWithoutName:
    """Mock relay without a name attribute."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_payloads = []

    def send(self, payload):
        if self.should_fail:
            raise Exception("Relay failed")
        self.sent_payloads.append(payload)


def test_broadcast_returns_successes_list():
    """Test that successful broadcasts return relay names in the 'successes' list."""
    relay1 = MockRelay("relay1")
    relay2 = MockRelay("relay2")
    server = RelayServer(relays=[relay1, relay2])

    result = server.broadcast({"message": "test"})

    assert "successes" in result
    assert "relay1" in result["successes"]
    assert "relay2" in result["successes"]
    assert len(result["failures"]) == 0


def test_broadcast_captures_failures():
    """Test that failed relay sends are captured in the 'failures' list."""
    relay1 = MockRelay("relay1", should_fail=True, error_msg="Connection error")
    relay2 = MockRelay("relay2")
    server = RelayServer(relays=[relay1, relay2])

    result = server.broadcast({"message": "test"})

    assert "failures" in result
    assert len(result["failures"]) == 1
    assert result["failures"][0][0] == "relay1"
    assert "Connection error" in result["failures"][0][1]


def test_broadcast_continues_after_failure():
    """Test that broadcasting continues even when individual relays fail."""
    relay1 = MockRelay("relay1", should_fail=True)
    relay2 = MockRelay("relay2")
    relay3 = MockRelay("relay3", should_fail=True)
    relay4 = MockRelay("relay4")
    server = RelayServer(relays=[relay1, relay2, relay3, relay4])

    result = server.broadcast({"message": "test"})

    # Should have attempted all relays
    assert len(result["successes"]) == 2
    assert len(result["failures"]) == 2
    assert "relay2" in result["successes"]
    assert "relay4" in result["successes"]


def test_broadcast_returns_correct_structure():
    """Test that the returned dictionary has the documented format."""
    relay = MockRelay("test_relay")
    server = RelayServer(relays=[relay])

    result = server.broadcast({"data": "value"})

    # Verify structure
    assert isinstance(result, dict)
    assert "successes" in result
    assert "failures" in result
    assert isinstance(result["successes"], list)
    assert isinstance(result["failures"], list)


def test_broadcast_uses_class_name_when_no_name_attribute():
    """Test that broadcast uses class name when relay has no name attribute."""
    relay = MockRelayWithoutName()
    server = RelayServer(relays=[relay])

    result = server.broadcast({"message": "test"})

    # Should use class name as fallback
    assert "MockRelayWithoutName" in result["successes"]


def test_broadcast_payload_delivered_to_relays():
    """Test that the payload is actually delivered to successful relays."""
    relay1 = MockRelay("relay1")
    relay2 = MockRelay("relay2")
    server = RelayServer(relays=[relay1, relay2])

    payload = {"message": "test", "data": 123}
    server.broadcast(payload)

    # Verify payload was received
    assert len(relay1.sent_payloads) == 1
    assert relay1.sent_payloads[0] == payload
    assert len(relay2.sent_payloads) == 1
    assert relay2.sent_payloads[0] == payload


def test_broadcast_failure_includes_error_message():
    """Test that failures include the relay name and error message."""
    error_msg = "Network timeout occurred"
    relay = MockRelay("failing_relay", should_fail=True, error_msg=error_msg)
    server = RelayServer(relays=[relay])

    result = server.broadcast({"message": "test"})

    assert len(result["failures"]) == 1
    failure = result["failures"][0]
    assert failure[0] == "failing_relay"
    assert error_msg in failure[1]
