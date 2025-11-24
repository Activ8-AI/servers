"""Lightweight vector store stub used for compatibility checks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VectorRecord:
    key: str
    vector: List[float]


class VectorStore:
    def __init__(self) -> None:
        self._records: Dict[str, VectorRecord] = {}

    def upsert(self, key: str, vector: List[float]) -> None:
        self._records[key] = VectorRecord(key=key, vector=vector)

    def similarity_search(self, query: List[float]) -> List[VectorRecord]:
        # Simple placeholder, returns all vectors without actual similarity math.
        return list(self._records.values())


if __name__ == "__main__":
    store = VectorStore()
    store.upsert("demo", [0.1, 0.2, 0.3])
    print(store.similarity_search([0.1, 0.2, 0.3]))
