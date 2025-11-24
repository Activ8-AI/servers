"""
Simple vector store placeholder that records embeddings as flat lists.
"""

from __future__ import annotations

from typing import Dict, Iterable, List


class VectorStore:
    def __init__(self):
        self._vectors: Dict[str, List[float]] = {}

    def upsert(self, key: str, vector: Iterable[float]) -> None:
        self._vectors[key] = list(vector)

    def get(self, key: str) -> List[float] | None:
        return self._vectors.get(key)

    def keys(self):
        return list(self._vectors.keys())


__all__ = ["VectorStore"]
