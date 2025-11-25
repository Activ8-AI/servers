from unittest.mock import patch, MagicMock

from agent_hub.activate import activate


def test_agent_activation():
    """Test that agent activation logs an event to the ledger."""
    mock_log_event = MagicMock()

    with patch("custody.custodian_ledger.log_event", mock_log_event), \
         patch("agent_hub.activate.log_event", mock_log_event):
        activate()
        # Verify log_event was called at least once (for AGENT_ACTIVATED)
        mock_log_event.assert_called()
        # Verify it was called with the correct event type
        event_types = [args[0] for args, _ in mock_log_event.call_args_list]
        assert "AGENT_ACTIVATED" in event_types
