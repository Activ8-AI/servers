from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from charter.paths import LOG_ROOT


class CustodianLogBinder:
    """Append-only JSONL logger with UTC timestamps and UUID event ids."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (LOG_ROOT / "custodian.log")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log(self, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload = json.dumps(entry, sort_keys=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(payload + "\n")
        return entry

    def tail(self, limit: int = 50) -> list[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
        return [json.loads(line) for line in lines]
