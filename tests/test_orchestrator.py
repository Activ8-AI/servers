"""Tests for Orchestrator class."""

from agent_hub.orchestrator import Orchestrator


class MockLedger:
    """Mock ledger for testing."""

    def __init__(self):
        self.events = []

    def log_event(self, event_type, payload=None):
        self.events.append((event_type, payload or {}))


def test_list_commands_returns_expected_commands():
    """Test that list_commands() returns the expected command names."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    commands = orch.list_commands()

    # Should include the mvp_health_check command
    assert "mvp_health_check" in commands


def test_list_commands_strips_cmd_prefix():
    """Test that list_commands() correctly strips the 'cmd_' prefix."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    commands = orch.list_commands()

    # No command should start with 'cmd_'
    for cmd in commands:
        assert not cmd.startswith("cmd_"), f"Command {cmd} still has 'cmd_' prefix"


def test_list_commands_only_includes_callable_methods():
    """Test that list_commands() only includes callable methods."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    commands = orch.list_commands()

    # Each command should correspond to a callable method
    for cmd in commands:
        method = getattr(orch, f"cmd_{cmd}", None)
        assert method is not None, f"Command {cmd} has no corresponding method"
        assert callable(method), f"Method for command {cmd} is not callable"


def test_run_command_rejects_empty_string():
    """Test that run_command() rejects empty command names."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    result = orch.run_command("")

    assert result["status"] == "invalid_command"
    assert "error" in result


def test_run_command_rejects_special_characters():
    """Test that run_command() rejects command names with special characters."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    # Test various invalid command names
    invalid_names = ["!invalid", "@command", "cmd-name", "cmd.name", "123start"]

    for name in invalid_names:
        result = orch.run_command(name)
        assert result["status"] == "invalid_command", f"Command '{name}' should be rejected"
        assert "error" in result


def test_run_command_accepts_valid_names():
    """Test that run_command() accepts valid command names."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    # Valid command that exists
    result = orch.run_command("mvp_health_check")
    assert result["status"] == "ok"

    # Valid command name format but doesn't exist
    result = orch.run_command("nonexistent_command")
    assert result["status"] == "unknown_command"


def test_run_command_accepts_alphanumeric_with_underscores():
    """Test that run_command() accepts alphanumeric names with underscores."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    # These are valid formats (even if the command doesn't exist)
    valid_names = ["test", "Test123", "my_command", "CMD_123_test"]

    for name in valid_names:
        result = orch.run_command(name)
        # Should either succeed or be unknown, but not invalid
        assert result["status"] in ["ok", "unknown_command"], f"Command '{name}' format should be valid"


def test_run_command_logs_events():
    """Test that run_command() logs appropriate events."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    # Run a valid command
    orch.run_command("mvp_health_check")

    # Should have logged ORCH_COMMAND_RECEIVED and ORCH_COMMAND_SUCCESS
    event_types = [e[0] for e in ledger.events]
    assert "ORCH_COMMAND_RECEIVED" in event_types
    assert "ORCH_COMMAND_SUCCESS" in event_types


def test_run_command_logs_invalid_command():
    """Test that run_command() logs invalid command attempts."""
    ledger = MockLedger()
    orch = Orchestrator(ledger, [])

    # Run an invalid command
    orch.run_command("!invalid")

    # Should have logged ORCH_COMMAND_INVALID
    event_types = [e[0] for e in ledger.events]
    assert "ORCH_COMMAND_INVALID" in event_types
