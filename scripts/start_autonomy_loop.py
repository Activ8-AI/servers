#!/usr/bin/env python3
"""Baseline autonomy loop that records ledger events."""
from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from custody.custodian_ledger import ledger_from_config, load_global_config


def _install_signal_handler() -> None:
    def _handler(signum, frame):  # type: ignore[override]
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def main() -> None:
    config = load_global_config()
    ledger = ledger_from_config()
    interval = config.get("autonomy_loop", {}).get("interval_seconds", 2)
    payload_template: Dict[str, Any] = config.get("autonomy_loop", {}).get("payload", {})

    print("[autonomy] starting loop, press Ctrl+C to exit", flush=True)
    _install_signal_handler()

    iteration = 0
    try:
        while True:
            iteration += 1
            payload = {**payload_template, "iteration": iteration}
            entry = ledger.record_entry("AUTONOMY_LOOP", payload)
            print(f"[autonomy] recorded entry: {json.dumps(entry)}", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[autonomy] loop stopped", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
