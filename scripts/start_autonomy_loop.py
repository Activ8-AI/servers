"""
Utility script that performs a lightweight autonomy cycle.
"""

from __future__ import annotations

import argparse
import time
from typing import List

from custody.custodian_ledger import log_event
from telemetry.emit_heartbeat import generate_heartbeat


def run_cycle(index: int):
    heartbeat = generate_heartbeat({"cycle": index})
    log_event("AUTONOMY_LOOP", heartbeat)
    return heartbeat


def start_autonomy_loop(cycles: int = 1, sleep_seconds: float = 0.0) -> List[dict]:
    output = []
    for idx in range(cycles):
        output.append(run_cycle(idx))
        if sleep_seconds:
            time.sleep(sleep_seconds)
    return output


def _parse_args():
    parser = argparse.ArgumentParser(description="Run a minimal autonomy loop.")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=0.0)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    data = start_autonomy_loop(args.cycles, args.sleep)
    print(f"Ran {len(data)} cycles.")
