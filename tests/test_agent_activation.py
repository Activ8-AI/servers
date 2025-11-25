from agent_hub.activate import activate
from custody.custodian_ledger import get_last_events
from unittest.mock import patch


def test_agent_activation():
    fake_ledger = []

    def fake_get_last_events(n):
        if not fake_ledger:
            return []
        return fake_ledger[-min(n, len(fake_ledger)):]

    def fake_log_event(event_type, event_data=None):
        fake_ledger.append((event_type, event_data))

    with patch("custody.custodian_ledger.get_last_events", side_effect=fake_get_last_events), \
         patch("custody.custodian_ledger.log_event", side_effect=fake_log_event):
        before = len(get_last_events(100))
        activate()
        after = len(get_last_events(100))
        assert after == before + 1
