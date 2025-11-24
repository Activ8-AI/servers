"""Emit heartbeat telemetry events and persist their latest state."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from custody.custodian_ledger import ledger_from_config, load_global_config


class HeartbeatEmitter:
    def __init__(self) -> None:
        self.config = load_global_config()
        telemetry_cfg = self.config.get("telemetry", {})
        status_path = telemetry_cfg.get("status_file", "telemetry/.heartbeat-state.json")
        self.status_path = Path(status_path)
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger_from_config()

    def emit(self) -> Dict[str, Any]:
        payload = {
            "status": "alive",
            "service": self.config.get("relay", {}).get("service_name", "codex-relay"),
            "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self.status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.ledger.record_entry("HEARTBEAT", payload)
        return payload


def emit_heartbeat() -> Dict[str, Any]:
    return HeartbeatEmitter().emit()


if __name__ == "__main__":
    print(json.dumps(emit_heartbeat(), indent=2))
