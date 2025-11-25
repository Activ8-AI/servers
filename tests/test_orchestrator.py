"""Tests for the Orchestrator class."""
from agent_hub.orchestrator import Orchestrator


class MockLedger:
    """Mock ledger for testing."""

    def __init__(self):
        self.events = []

    def log_event(self, event_type, payload):
        self.events.append((event_type, payload))


def test_list_commands():
    """Test that list_commands returns available commands."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    commands = orch.list_commands()
    assert "mvp_health_check" in commands


def test_run_command_valid():
    """Test that run_command executes valid commands."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    result = orch.run_command("mvp_health_check")
    assert result["status"] == "ok"
    assert "result" in result


def test_run_command_unknown():
    """Test that run_command handles unknown commands."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    result = orch.run_command("nonexistent_command")
    assert result["status"] == "unknown_command"


def test_run_command_invalid_starts_with_underscore():
    """Test that commands starting with underscore are rejected."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    result = orch.run_command("_private_method")
    assert result["status"] == "invalid_command"


def test_run_command_invalid_with_special_chars():
    """Test that commands with special characters are rejected."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    result = orch.run_command("cmd; rm -rf /")
    assert result["status"] == "invalid_command"


def test_run_command_invalid_empty():
    """Test that empty command names are rejected."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    result = orch.run_command("")
    assert result["status"] == "invalid_command"


def test_run_command_invalid_starts_with_digit():
    """Test that commands starting with a digit are rejected."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    result = orch.run_command("123command")
    assert result["status"] == "invalid_command"


def test_run_command_valid_with_underscores():
    """Test that commands with underscores (not leading) are valid."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    # mvp_health_check contains underscores and should work
    result = orch.run_command("mvp_health_check")
    assert result["status"] == "ok"


def test_validate_command_name_logs_invalid():
    """Test that invalid command names are logged."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])
    orch.run_command("_invalid")
    assert any(event[0] == "ORCH_COMMAND_INVALID" for event in ledger.events)
