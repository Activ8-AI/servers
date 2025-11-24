"""Placeholder module for sending Slack signals."""
from __future__ import annotations

from typing import Any, Dict


def send(channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[slack] channel={channel} payload={payload}")
    return {"channel": channel, "status": "sent", "payload": payload}
