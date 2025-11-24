"""
Minimal relay server stub that wires up configured relays.
"""

from __future__ import annotations

from typing import Iterable, List

from relay import NotionRelay, SlackSignalRelay, TeamworkSinkRelay


class RelayServer:
    def __init__(self, relays: Iterable | None = None):
        self.relays: List = list(relays) if relays is not None else [
            NotionRelay(),
            SlackSignalRelay(),
            TeamworkSinkRelay(),
        ]

    def broadcast(self, payload):
        for relay in self.relays:
            relay.send(payload)


__all__ = ["RelayServer"]
