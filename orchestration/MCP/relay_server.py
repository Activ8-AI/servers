"""
Minimal relay server stub that wires up configured relays.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Tuple, Union

from relay import NotionRelay, SlackSignalRelay, TeamworkSinkRelay

logger = logging.getLogger(__name__)


class RelayServer:
    def __init__(self, relays: Iterable | None = None):
        self.relays: List = list(relays) if relays is not None else [
            NotionRelay(),
            SlackSignalRelay(),
            TeamworkSinkRelay(),
        ]

    def broadcast(self, payload: Dict[str, Any]) -> Dict[str, Union[List[str], List[Tuple[str, str]]]]:
        """
        Broadcast a payload to all registered relays.

        Args:
            payload: Dictionary containing the message or data to broadcast.

        Returns:
            A dictionary with "successes" and "failures" lists.
            Each failure is a tuple of (relay_name, error_message).
        """
        successes: List[str] = []
        failures: List[Tuple[str, str]] = []

        for relay in self.relays:
            relay_name = getattr(relay, "name", relay.__class__.__name__)
            try:
                relay.send(payload)
                successes.append(relay_name)
            except Exception as exc:
                logger.warning("Relay %s failed to send: %s", relay_name, exc)
                failures.append((relay_name, str(exc)))

        return {"successes": successes, "failures": failures}


__all__ = ["RelayServer"]
