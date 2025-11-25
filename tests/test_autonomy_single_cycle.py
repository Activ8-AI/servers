from custody.custodian_ledger import get_last_events, log_event
from telemetry.emit_heartbeat import generate_heartbeat
from unittest.mock import patch


def test_single_cycle():
    fake_ledger = []

    def fake_get_last_events(n):
        return fake_ledger[-n:]

    def fake_log_event(event_type, event_data):
        fake_ledger.append((event_type, event_data))

    with patch("custody.custodian_ledger.get_last_events", side_effect=fake_get_last_events), \
         patch("custody.custodian_ledger.log_event", side_effect=fake_log_event):
        before = len(get_last_events(100))
        hb = generate_heartbeat()
        log_event("AUTONOMY_LOOP", hb)
        after = len(get_last_events(100))
        assert after == before + 1
