from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from charter.paths import LOG_ROOT


class GenesisTrace:
    """Fine-grained trace log used for auditing governor steps."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (LOG_ROOT / "genesis_trace.log")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, phase: str, data: Optional[Dict[str, Any]] = None) -> None:
        entry = {
            "phase": phase,
            "payload": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
