from unittest.mock import patch, MagicMock

from scripts.start_autonomy_loop import run_cycle


def test_single_cycle():
    """Test that a single autonomy cycle logs an AUTONOMY_LOOP event."""
    mock_log_event = MagicMock()

    # Patch log_event where it's imported in the autonomy loop module
    with patch("scripts.start_autonomy_loop.log_event", mock_log_event):
        result = run_cycle(0)
        # Verify log_event was called with the correct event type
        mock_log_event.assert_called_once()
        event_type, heartbeat = mock_log_event.call_args[0]
        assert event_type == "AUTONOMY_LOOP"
        assert "heartbeat_id" in heartbeat
        assert result == heartbeat
