"""
Stub loader that mimics pulling secrets from Notion.
"""

from __future__ import annotations

from typing import Dict


def load_secrets() -> Dict[str, str]:
    return {"NOTION_TOKEN": "placeholder", "DEFAULT_SPACE": "demo"}


if __name__ == "__main__":
    for key, value in load_secrets().items():
        print(f"{key}={value}")
