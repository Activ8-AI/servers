"""
SQLite-backed ledger utility for recording and inspecting orchestration events.
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).with_name("ledger.db")

# Connection timeout in seconds for handling concurrent access
DB_TIMEOUT = 30.0

# Maximum retry attempts for database operations
MAX_RETRIES = 3


def _ensure_db() -> None:
    """
    Ensure the database exists and is properly configured.
    
    Note: This function uses WAL mode for better concurrent access and sets a
    connection timeout to handle database locking scenarios.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
        # Enable WAL mode for better concurrent read/write access
        conn.execute("PRAGMA journal_mode=WAL")
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
    
    Uses retry logic for handling database locking scenarios in concurrent environments.
    """

    if not event_type:
        raise ValueError("event_type is required")

    payload = payload or {}
    _ensure_db()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
                conn.execute(
                    "INSERT INTO ledger (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    (timestamp, event_type, json.dumps(payload)),
                )
                conn.commit()
            return
        except sqlite3.OperationalError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
    
    raise last_error  # type: ignore[misc]


def get_last_events(n: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch the most recent N events (default 10).
    
    Uses retry logic for handling database locking scenarios in concurrent environments.
    """

    if n <= 0:
        return []

    _ensure_db()
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
                cur = conn.execute(
                    "SELECT timestamp, event_type, payload FROM ledger ORDER BY id DESC LIMIT ?",
                    (n,),
                )
                rows = cur.fetchall()
            
            events = []
            for row in rows:
                try:
                    payload_data = json.loads(row[2]) if row[2] else {}
                except json.JSONDecodeError:
                    payload_data = {}
                events.append({
                    "timestamp": row[0],
                    "event": row[1],
                    "payload": payload_data,
                })
            return list(reversed(events))
        except sqlite3.OperationalError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
    
    raise last_error  # type: ignore[misc]


__all__ = ["log_event", "get_last_events", "DB_PATH"]
