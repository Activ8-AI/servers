"""
High-level command orchestrator for coordinating agent helpers.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable

from telemetry.emit_heartbeat import generate_heartbeat

# Pattern for valid command names: alphanumeric with underscores allowed as separators
_VALID_CMD_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class Orchestrator:
    def __init__(self, ledger, relays: Iterable[Any]):
        """
        Initialize the Orchestrator.

        Args:
            ledger: An object that provides event logging functionality. It must implement a
                method `log_event(event_type: str, payload: dict) -> None`.
            relays: An iterable of relay objects. Each relay should implement the required
                interface for your orchestration logic (e.g., methods for communication or coordination).

        Example:
            class SimpleLedger:
                def log_event(self, event_type, payload):
                    print(f"{event_type}: {payload}")

            class Relay:
                pass

            ledger = SimpleLedger()
            relays = [Relay(), Relay()]
            orch = Orchestrator(ledger, relays)
        """
        self.ledger = ledger
        self.relays = list(relays)
    def log(self, event_type: str, payload: Dict[str, Any] | None = None) -> None:
        self.ledger.log_event(event_type, payload or {})

    def run_command(self, cmd: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute a command by name.

        Args:
            cmd: The command name to execute. Must be alphanumeric (with underscores allowed),
                start with a letter, and cannot start with an underscore. Available commands
                are methods prefixed with 'cmd_' (e.g., 'mvp_health_check' calls 'cmd_mvp_health_check').
            payload: Optional dictionary of parameters to pass to the command handler.

        Returns:
            A dictionary with 'status' key ('ok', 'error', 'invalid_command', or 'unknown_command')
            and optionally 'result' or 'error' keys.

        Available commands:
            - mvp_health_check: Performs a basic health check of MCP, heartbeat, and ledger.
        """
        # Validate command name format
        if not cmd or not isinstance(cmd, str):
            self.log("ORCH_COMMAND_INVALID", {"cmd": cmd, "reason": "empty or invalid type"})
            return {"status": "invalid_command", "error": "Command must be a non-empty string"}

        if not _VALID_CMD_PATTERN.match(cmd):
            self.log("ORCH_COMMAND_INVALID", {"cmd": cmd, "reason": "invalid format"})
            return {"status": "invalid_command", "error": "Command must be alphanumeric with underscores allowed, start with a letter"}

        # Prevent calling internal methods (those starting with underscore)
        if cmd.startswith("_"):
            self.log("ORCH_COMMAND_INVALID", {"cmd": cmd, "reason": "internal method access"})
            return {"status": "invalid_command", "error": "Cannot call internal methods"}

        self.log("ORCH_COMMAND_RECEIVED", {"cmd": cmd})

        handler = getattr(self, f"cmd_{cmd}", None)
        if not handler:
            self.log("ORCH_COMMAND_UNKNOWN", {"cmd": cmd})
            return {"status": "unknown_command"}

        try:
            result = handler(payload or {})
            self.log("ORCH_COMMAND_SUCCESS", {"cmd": cmd})
            return {"status": "ok", "result": result}
        except Exception as exc:  # pragma: no cover - defensive
            self.log("ORCH_COMMAND_FAILURE", {"cmd": cmd, "error": str(exc)})
            return {"status": "error", "error": str(exc)}

    # Example command
    def cmd_mvp_health_check(self, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "mcp": "unknown",
            "heartbeat": None,
            "ledger": "unknown",
        }

        # MCP health (stub)
        res["mcp"] = "ok"

        # Heartbeat
        hb = generate_heartbeat()
        self.log("ORCH_STEP_HEARTBEAT", hb)
        res["heartbeat"] = hb

        # Ledger check
        res["ledger"] = "ok"

        return res
