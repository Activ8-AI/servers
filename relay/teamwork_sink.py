"""
Teamwork relay stub.
"""

from __future__ import annotations

from typing import Any, Dict

from custody.custodian_ledger import log_event


class TeamworkSinkRelay:
    name = "teamwork"

    def send(self, payload: Dict[str, Any]) -> None:
        log_event("RELAY_TEAMWORK_SEND", {"payload": payload})


__all__ = ["TeamworkSinkRelay"]
