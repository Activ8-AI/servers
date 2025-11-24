"""Placeholder activate module for the agent hub."""
from __future__ import annotations

import json
from datetime import datetime, timezone


def activate(agent_name: str = "codex-core") -> str:
    payload = {
        "agent": agent_name,
        "activated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    message = json.dumps(payload)
    print(message)
    return message


if __name__ == "__main__":
    activate()
