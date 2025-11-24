"""Placeholder module for forwarding signals to Notion."""
from __future__ import annotations

from typing import Any, Dict


def dispatch(page_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[notion] page={page_id} payload={payload}")
    return {"page_id": page_id, "status": "sent", "payload": payload}
