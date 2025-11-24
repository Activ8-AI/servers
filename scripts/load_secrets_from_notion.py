#!/usr/bin/env python3
"""Stub script that simulates syncing secrets from Notion."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

SECRETS_PATH = Path(".secrets/local_secrets.json")


def main() -> None:
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "synced_at": datetime.now(tz=timezone.utc).isoformat(),
        "source": "notion",
        "status": "stubbed",
    }
    SECRETS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[secrets] wrote stub secrets to {SECRETS_PATH}")


if __name__ == "__main__":
    main()
