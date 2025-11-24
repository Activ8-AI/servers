from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .paths import POLICIES_ROOT


class PolicyNotFoundError(FileNotFoundError):
    """Raised when a requested policy file does not exist."""


def _policy_path(kind: str, filename: str) -> Path:
    path = POLICIES_ROOT / kind / filename
    if not path.is_file():
        raise PolicyNotFoundError(f"Policy file not found: {path}")
    return path


def load_policy(kind: str, filename: str) -> Dict[str, Any]:
    """Load a JSON policy from disk with UTF-8 decoding."""
    path = _policy_path(kind, filename)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
