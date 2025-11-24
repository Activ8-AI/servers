"""
Stub integration that pretends to send updates to Notion.
"""

from __future__ import annotations

from typing import Any, Dict

from custody.custodian_ledger import log_event


class NotionRelay:
    name = "notion"

    def send(self, payload: Dict[str, Any]) -> None:
        log_event("RELAY_NOTION_SEND", {"payload": payload})


__all__ = ["NotionRelay"]
