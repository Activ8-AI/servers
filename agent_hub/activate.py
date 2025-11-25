"""
Simple activation helper that logs the event and returns the latest heartbeat.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

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


def activate(relays: Iterable | None = None) -> Dict[str, Any]:
    """
    Bootstrap the orchestrator, log the activation event, and return a heartbeat payload.

    This function initializes the agent orchestration system by creating an Orchestrator
    instance with the provided (or default) relays, logging the activation event to the
    custody ledger, and generating a heartbeat.

    Args:
        relays: Optional iterable of relay objects. Each relay should have a `name` attribute
            and implement the relay interface (e.g., `send(payload)` method). If not provided,
            default relays (NotionRelay, SlackSignalRelay, TeamworkSinkRelay) are used.

    Returns:
        A dictionary containing:
            - "heartbeat": The generated heartbeat dictionary with timing and health info.
            - "orchestrator": The initialized Orchestrator instance for running commands.

    Example:
        >>> result = activate()
        >>> print(result["heartbeat"]["heartbeat_id"])
        'abc123...'
        >>> result["orchestrator"].run_command("mvp_health_check")
        {'status': 'ok', 'result': {...}}

        >>> from relay.notion_relay import NotionRelay
        >>> custom_relays = [NotionRelay()]
        >>> result = activate(relays=custom_relays)
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
