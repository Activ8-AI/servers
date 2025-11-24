"""
Slack relay stub.
"""

from __future__ import annotations

from typing import Any, Dict

from custody.custodian_ledger import log_event


class SlackSignalRelay:
    name = "slack"

    def send(self, payload: Dict[str, Any]) -> None:
        log_event("RELAY_SLACK_SEND", {"payload": payload})


__all__ = ["SlackSignalRelay"]
