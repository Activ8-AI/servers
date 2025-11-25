from unittest.mock import patch

from agent_hub.activate import activate
from custody.custodian_ledger import get_last_events


def test_agent_activation():
    """Test that agent activation logs an event to the ledger."""
    fake_ledger = []

    def fake_get_last_events(n):
        return fake_ledger[-n:]

    def fake_log_event(event_type, event_data=None):
        fake_ledger.append((event_type, event_data))

    with patch("custody.custodian_ledger.get_last_events", side_effect=fake_get_last_events), \
         patch("custody.custodian_ledger.log_event", side_effect=fake_log_event), \
         patch("agent_hub.activate.log_event", side_effect=fake_log_event):
        before = len(fake_get_last_events(100))
        activate()
        after = len(fake_get_last_events(100))
        assert after == before + 1
