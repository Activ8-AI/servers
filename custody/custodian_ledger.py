"""Simple JSONL-based ledger utilities for the autonomy loop."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_PATH = Path("configs/global_config.yaml")
DEFAULT_LEDGER_PATH = Path("custody/ledger.jsonl")


def load_global_config(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load the global configuration stored as JSON-compatible YAML."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file missing: {config_path}")
    text = config_path.read_text(encoding="utf-8").strip()
    return json.loads(text or "{}")


class CustodianLedger:
    """Append-only ledger backed by newline-delimited JSON."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else DEFAULT_LEDGER_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record_entry(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        entry = {
            "ts": time.time(),
            "event_type": event_type,
            "payload": payload,
        }
        encoded = json.dumps(entry, separators=(",", ":"), sort_keys=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(encoded + "\n")
        return entry

    def tail(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
        return [json.loads(line) for line in lines if line.strip()]


def ledger_from_config() -> CustodianLedger:
    config = load_global_config()
    ledger_path = Path(config.get("ledger", {}).get("path", DEFAULT_LEDGER_PATH))
    return CustodianLedger(ledger_path)


def record_autonomy_event(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ledger = ledger_from_config()
    return ledger.record_entry("AUTONOMY_LOOP", payload)


if __name__ == "__main__":
    event = record_autonomy_event({"source": "manual"})
    print(json.dumps(event, indent=2))
