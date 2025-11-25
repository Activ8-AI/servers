from unittest.mock import patch

from agent_hub.activate import activate


def test_agent_activation():
    fake_ledger = []

    def fake_log_event(event_type, event_data=None):
        fake_ledger.append((event_type, event_data))

    with patch("agent_hub.activate.log_event", side_effect=fake_log_event):
        before = len(fake_ledger)
        activate()
        after = len(fake_ledger)
        assert after == before + 1
