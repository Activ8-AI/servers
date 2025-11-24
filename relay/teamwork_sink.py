"""Placeholder module for piping events into a teamwork sink."""
from __future__ import annotations

from typing import Any, Dict


def log(event: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[teamwork] event={event}")
    return {"status": "logged", "event": event}
