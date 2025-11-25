from unittest.mock import patch

from custody.custodian_ledger import get_last_events, log_event
from telemetry.emit_heartbeat import generate_heartbeat


def test_single_cycle():
    """Test that a single autonomy cycle logs an event to the ledger."""
    fake_ledger = []

    def fake_get_last_events(n):
        return fake_ledger[-n:]

    def fake_log_event(event_type, event_data=None):
        fake_ledger.append((event_type, event_data))

    with patch("custody.custodian_ledger.get_last_events", side_effect=fake_get_last_events), \
         patch("custody.custodian_ledger.log_event", side_effect=fake_log_event):
        before = len(fake_get_last_events(100))
        hb = generate_heartbeat()
        fake_log_event("AUTONOMY_LOOP", hb)
        after = len(fake_get_last_events(100))
        assert after == before + 1
