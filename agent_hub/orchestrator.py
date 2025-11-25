"""
High-level command orchestrator for coordinating agent helpers.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


class Orchestrator:
    """
    Orchestrator class for coordinating agent commands.

    Commands are methods prefixed with `cmd_` and can be invoked via `run_command`.
    Available commands can be listed using the `list_commands` method.
    """

    # Pattern for valid command names: alphanumeric and underscores only
    _VALID_CMD_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
    _INVALID_CMD_ERROR = (
        "Command name must start with a letter and contain only "
        "alphanumeric characters and underscores"
    )

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

    def list_commands(self) -> List[str]:
        """
        List all available commands.

        Returns:
            A list of command names (without the 'cmd_' prefix) that can be invoked
            via `run_command`.

        Example:
            >>> orch.list_commands()
            ['mvp_health_check']
        """
        return [
            name[4:]  # Remove 'cmd_' prefix
            for name in dir(self)
            if name.startswith("cmd_") and callable(getattr(self, name, None))
        ]

    def _validate_command_name(self, cmd: str) -> bool:
        """
        Validate that a command name is safe to use.

        Args:
            cmd: The command name to validate.

        Returns:
            True if the command name is valid, False otherwise.

        A valid command name:
        - Starts with a letter (not underscore or digit)
        - Contains only alphanumeric characters and underscores
        """
        if not cmd or not isinstance(cmd, str):
            return False
        return bool(self._VALID_CMD_PATTERN.match(cmd))

    def run_command(self, cmd: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute a command by name.

        Args:
            cmd: The command name to execute. Must start with a letter and contain
                only alphanumeric characters and underscores. Commands are mapped
                to methods prefixed with 'cmd_'. Use `list_commands()` to see
                available commands.
            payload: Optional dictionary of parameters to pass to the command.

        Returns:
            A dictionary with 'status' key and optionally 'result' or 'error' keys.
            Status can be 'ok', 'error', 'unknown_command', or 'invalid_command'.

        Example:
            >>> orch.run_command('mvp_health_check')
            {'status': 'ok', 'result': {...}}
        """
        # Validate command name to prevent injection attacks
        if not self._validate_command_name(cmd):
            self.log("ORCH_COMMAND_INVALID", {"cmd": cmd})
            return {"status": "invalid_command", "error": self._INVALID_CMD_ERROR}

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
        from telemetry.emit_heartbeat import generate_heartbeat

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
