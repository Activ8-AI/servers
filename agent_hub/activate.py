"""
Simple activation helper that logs the event and returns the latest heartbeat.
"""

from __future__ import annotations

from typing import Iterable, List

from custody.custodian_ledger import log_event
from relay.notion_relay import NotionRelay
from relay.slack_signal import SlackSignalRelay
from relay.teamwork_sink import TeamworkSinkRelay
from telemetry.emit_heartbeat import generate_heartbeat

from .orchestrator import Orchestrator


class _LedgerAdapter:
    @staticmethod
    def log_event(event_type, payload=None):
        log_event(event_type, payload or {})


def _default_relays() -> List:
    return [NotionRelay(), SlackSignalRelay(), TeamworkSinkRelay()]


def activate(relays: Iterable | None = None):
    """
    Bootstraps the orchestrator, logs the activation event, and returns a heartbeat payload.
    """

    relays = list(relays) if relays is not None else _default_relays()
    orchestrator = Orchestrator(_LedgerAdapter(), relays)

    heartbeat = generate_heartbeat()
    log_event(
        "AGENT_ACTIVATED",
        {
            "relays": [relay.name for relay in relays],
            "heartbeat_id": heartbeat["heartbeat_id"],
            "relay_count": len(relays),
        },
    )
    return {"heartbeat": heartbeat, "orchestrator": orchestrator}


__all__ = ["activate"]
