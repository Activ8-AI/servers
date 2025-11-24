"""
Simple in-memory SQL-like store placeholder.
"""

from __future__ import annotations

from typing import Any, Dict


class SQLStore:
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def all(self) -> Dict[str, Any]:
        return dict(self._data)


__all__ = ["SQLStore"]
