#!/usr/bin/env python3
"""
codex_logger

Captures metadata for a Codex run, optionally recording an environment snapshot.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Log Codex run metadata.")
    parser.add_argument("--run-dir", required=True, help="Run directory to log against.")
    parser.add_argument(
        "--record-env",
        action="store_true",
        help="Include environment snapshot (sanitized) in the log.",
    )
    parser.add_argument(
        "--output-file",
        default="log.json",
        help="Filename for the log inside the run directory.",
    )
    return parser.parse_args()


def read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
        return data if isinstance(data, dict) else None


def capture_environment() -> Dict[str, Any]:
    snapshot = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "env_vars": {},
        "git_rev": detect_git_rev(),
    }
    allowlist = ["USER", "SHELL", "PYTHONPATH", "VIRTUAL_ENV"]
    for key in allowlist:
        value = os.environ.get(key)
        if value:
            snapshot["env_vars"][key] = value
    return snapshot


def detect_git_rev() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    log_record: Dict[str, Any] = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "relay_snapshot": read_json(run_dir / "relay.json"),
    }

    if args.record_env:
        log_record["environment"] = capture_environment()

    output_path = run_dir / args.output_file
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(log_record, handle, indent=2)

    print(json.dumps(log_record, indent=2))


if __name__ == "__main__":
    main()
