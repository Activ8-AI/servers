from __future__ import annotations

import argparse
from datetime import datetime, timezone

from custodian_log_binder import CustodianLogBinder


def check_staleness(threshold_minutes: int) -> bool:
    binder = CustodianLogBinder()
    entries = binder.tail(limit=1)
    if not entries:
        return False
    timestamp = entries[0].get("timestamp")
    if not timestamp:
        return False
    last_event = datetime.fromisoformat(timestamp)
    delta = datetime.now(timezone.utc) - last_event
    delta_minutes = delta.total_seconds() / 60
    return delta_minutes <= threshold_minutes


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect stale governors and escalate if needed")
    parser.add_argument("--threshold", type=int, default=60, help="Maximum allowed silence in minutes")
    args = parser.parse_args()
    healthy = check_staleness(args.threshold)
    if healthy:
        print("Watchdog: governors healthy")
    else:
        raise SystemExit("Watchdog: stale governor activity detected")


if __name__ == "__main__":
    main()
