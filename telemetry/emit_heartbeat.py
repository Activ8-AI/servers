"""
Heartbeat generation helpers.
"""

from __future__ import annotations

import platform
import socket
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from custody.custodian_ledger import log_event


def generate_heartbeat(metadata: Dict[str, Any] | None = None, persist: bool = False) -> Dict[str, Any]:
    """
    Generate a simple heartbeat payload.
    """

    payload: Dict[str, Any] = {
        "heartbeat_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "status": "ok",
    }

    if metadata:
        payload["metadata"] = metadata

    if persist:
        log_event("HEARTBEAT_EMIT", payload)

    return payload


__all__ = ["generate_heartbeat"]
