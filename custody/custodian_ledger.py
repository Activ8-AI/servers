"""
SQLite-backed ledger utility for recording and inspecting orchestration events.

Thread-safety: This module uses SQLite's WAL mode for better concurrent access.
For multi-process scenarios, consider using a dedicated database server.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).with_name("ledger.db")

# Database connection timeout in seconds
DB_TIMEOUT = 30.0


def _get_connection() -> sqlite3.Connection:
    """Get a database connection with appropriate settings for concurrent access."""
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    # Enable WAL mode for better concurrent read/write access
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        conn.commit()


def log_event(event_type: str, payload: Dict[str, Any] | None = None) -> None:
    """
    Append an event to the ledger.
    """

    if not event_type:
        raise ValueError("event_type is required")

    payload = payload or {}
    _ensure_db()
    timestamp = datetime.now(timezone.utc).isoformat()
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO ledger (timestamp, event_type, payload) VALUES (?, ?, ?)",
            (timestamp, event_type, json.dumps(payload)),
        )
        conn.commit()


def get_last_events(n: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch the most recent N events (default 10).
    """

    if n <= 0:
        return []

    _ensure_db()
    with _get_connection() as conn:
        cur = conn.execute(
            "SELECT timestamp, event_type, payload FROM ledger ORDER BY id DESC LIMIT ?",
            (n,),
        )
        rows = cur.fetchall()

    events = [
        {
            "timestamp": row[0],
            "event": row[1],
            "payload": json.loads(row[2]) if row[2] else {},
        }
        for row in rows
    ]
    return list(reversed(events))


__all__ = ["log_event", "get_last_events", "DB_PATH"]
