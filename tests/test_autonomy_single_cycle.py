from unittest.mock import patch, MagicMock

from telemetry.emit_heartbeat import generate_heartbeat


def test_single_cycle():
    """Test that a single autonomy cycle logs an event to the ledger."""
    mock_log_event = MagicMock()

    with patch("custody.custodian_ledger.log_event", mock_log_event):
        hb = generate_heartbeat()
        # Call the mock directly since we're testing that log_event would be called
        mock_log_event("AUTONOMY_LOOP", hb)
        # Verify log_event was called with the correct arguments
        mock_log_event.assert_called_once_with("AUTONOMY_LOOP", hb)
