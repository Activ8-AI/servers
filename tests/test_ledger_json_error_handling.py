"""
Tests for JSON decode error handling in the ledger.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from custody.custodian_ledger import get_last_events, DB_PATH


def test_get_last_events_handles_malformed_json():
    """Test that get_last_events() gracefully handles malformed JSON payloads."""
    # Use a temporary database for test isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_ledger.db"
        
        with patch("custody.custodian_ledger.DB_PATH", test_db_path):
            # Set up the database with proper schema
            with sqlite3.connect(test_db_path, timeout=30.0) as conn:
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
                # Insert a valid JSON row
                conn.execute(
                    "INSERT INTO ledger (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    ("2024-01-01T00:00:00Z", "VALID_EVENT", '{"key": "value"}'),
                )
                # Insert a malformed JSON row
                conn.execute(
                    "INSERT INTO ledger (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    ("2024-01-02T00:00:00Z", "MALFORMED_EVENT", '{invalid json}'),
                )
                # Insert another valid JSON row
                conn.execute(
                    "INSERT INTO ledger (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    ("2024-01-03T00:00:00Z", "ANOTHER_VALID_EVENT", '{"another": "data"}'),
                )
                conn.commit()

            # Call get_last_events and verify behavior
            events = get_last_events(10)

            # Should return all 3 events without crashing
            assert len(events) == 3

            # Verify the valid events have their payloads
            assert events[0]["event"] == "VALID_EVENT"
            assert events[0]["payload"] == {"key": "value"}

            # Verify the malformed JSON event has an empty payload dict
            assert events[1]["event"] == "MALFORMED_EVENT"
            assert events[1]["payload"] == {}

            # Verify the third valid event also has its payload
            assert events[2]["event"] == "ANOTHER_VALID_EVENT"
            assert events[2]["payload"] == {"another": "data"}


def test_get_last_events_handles_empty_payload():
    """Test that get_last_events() handles empty string payloads gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_ledger.db"
        
        with patch("custody.custodian_ledger.DB_PATH", test_db_path):
            with sqlite3.connect(test_db_path, timeout=30.0) as conn:
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
                # Insert a row with empty payload
                conn.execute(
                    "INSERT INTO ledger (timestamp, event_type, payload) VALUES (?, ?, ?)",
                    ("2024-01-01T00:00:00Z", "EMPTY_PAYLOAD_EVENT", ''),
                )
                conn.commit()

            events = get_last_events(10)

            assert len(events) == 1
            assert events[0]["event"] == "EMPTY_PAYLOAD_EVENT"
            assert events[0]["payload"] == {}
