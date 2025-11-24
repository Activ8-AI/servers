"""In-memory SQLite-backed store placeholder used by the autonomy loop."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Tuple

DEFAULT_DB = Path("memory/sql_store/cache.db")


class SQLStore:
    def __init__(self, path: Path = DEFAULT_DB) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kv (
                k TEXT PRIMARY KEY,
                v TEXT
            )
            """
        )
        self.conn.commit()

    def set(self, key: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO kv(k, v) VALUES(?, ?)", (key, value))
        self.conn.commit()

    def get(self, key: str) -> str | None:
        cur = self.conn.cursor()
        cur.execute("SELECT v FROM kv WHERE k = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def dump(self) -> Iterable[Tuple[str, str]]:
        cur = self.conn.cursor()
        cur.execute("SELECT k, v FROM kv")
        yield from cur.fetchall()


if __name__ == "__main__":
    store = SQLStore()
    store.set("hello", "world")
    print(dict(store.dump()))
