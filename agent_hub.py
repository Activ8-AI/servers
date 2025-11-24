"""
Agent Hub wiring for the Reflex → Teamwork execution pipeline.

This module loads the Action Matrix execution mapping, initializes the Teamwork
pipeline, and provides a minimal in-memory Action Matrix capable of routing
reflex intents to the pipeline.  The lightweight client + notifier
implementations can be replaced with production-grade integrations while
keeping the binding contract identical.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Mapping

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

from modules.teamwork_pipeline import ExecutionIntent, TeamworkPipeline
from modules.teamwork_pipeline.pipeline import (
    BriefWriter,
    CustodianLogger,
    Notifier,
    TeamworkClient,
    TeamworkPipelineError,
)

ROOT = Path(__file__).parent
CONFIG_ROOT = ROOT / "configs"


def _load_yaml_config(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to load configuration files. "
            "Install it with `pip install pyyaml`."
        )
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, Mapping):
        raise ValueError(f"Configuration at {path} must be a mapping.")
    return data


class InMemoryTeamworkClient(TeamworkClient):
    """
    Simple in-memory Teamwork client used for development and tests.

    Production deployments should replace this with an HTTP client that
    integrates with the actual Teamwork Projects API.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.tasks: dict[str, dict[str, Any]] = {}
        self.sprints: dict[str, dict[str, Any]] = {}

    def create_task(
        self,
        *,
        project_id: str,
        task_name: str,
        description: str,
        due: str | None,
        tags: list[str] | tuple[str, ...],
        evidence_urls: list[str] | tuple[str, ...] | None = None,
        assignees: list[str] | tuple[str, ...] | None = None,
    ) -> str:
        with self._lock:
            task_id = uuid.uuid4().hex
            self.tasks[task_id] = {
                "project_id": project_id,
                "name": task_name,
                "description": description,
                "due": due,
                "tags": list(tags),
                "evidence_urls": list(evidence_urls or []),
                "assignees": list(assignees or []),
                "subtasks": [],
            }
        return task_id

    def create_subtask(
        self, *, parent_id: str, task_name: str, project_id: str
    ) -> str:
        with self._lock:
            if parent_id not in self.tasks:
                raise TeamworkPipelineError(f"Parent task {parent_id} not found.")
            subtask_id = uuid.uuid4().hex
            subtask = {
                "id": subtask_id,
                "name": task_name,
                "project_id": project_id,
            }
            self.tasks[parent_id]["subtasks"].append(subtask)
        return subtask_id

    def create_sprint(
        self,
        *,
        project_id: str,
        name: str,
        tasks: list[str] | tuple[str, ...],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        with self._lock:
            sprint_id = uuid.uuid4().hex
            self.sprints[sprint_id] = {
                "project_id": project_id,
                "name": name,
                "tasks": list(tasks),
                "start_date": start_date,
                "end_date": end_date,
            }
        return sprint_id


class CharterBriefWriter(BriefWriter):
    """Default writer that generates a charter-standard brief body."""

    def attach_brief(self, execution_intent: ExecutionIntent) -> str:
        summary = {
            "title": execution_intent.title,
            "description": execution_intent.description,
            "actions": execution_intent.actions,
            "evidence": execution_intent.evidence_urls,
        }
        return (
            "## Charter Brief\n"
            f"**Reflex:** {execution_intent.reflex}\n"
            f"**Urgency:** {execution_intent.urgency}\n"
            f"**Source Event:** {execution_intent.source_event}\n\n"
            f"{execution_intent.description}\n\n"
            "### Operational Payload\n"
            f"```json\n{json.dumps(summary, indent=2)}\n```"
        )


class CustodianHubLogger(CustodianLogger):
    """Simple logger that appends audit entries to a JSONL log file."""

    def __init__(self, log_path: Path | None = None) -> None:
        self.log_path = log_path or (ROOT / "logs" / "custodian_hub.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def audit(self, **payload: Any) -> None:
        entry = json.dumps(payload, sort_keys=True)
        with self._lock:
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(entry + "\n")


class SlackNotifier(Notifier):
    """Notifier that writes Slack-style notifications to stdout or a webhook."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url

    def notify(
        self,
        *,
        role_ids: list[str] | tuple[str, ...],
        message: str,
        metadata: Mapping[str, Any],
    ) -> None:
        if self.webhook_url:
            try:
                import urllib.request

                req = urllib.request.Request(
                    self.webhook_url,
                    data=json.dumps(
                        {"text": message, "metadata": dict(metadata), "roles": role_ids}
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception:  # pragma: no cover - network best effort
                pass
        else:
            print(f"[Notifier] {message} :: roles={role_ids} meta={metadata}")


class ActionMatrix:
    """Minimal action matrix that routes reflexes to an execution pipeline."""

    def __init__(self, execution_map: Mapping[str, str]) -> None:
        self.execution_map = execution_map
        self._execution_pipeline: TeamworkPipeline | None = None

    def bind_execution_pipeline(self, pipeline: TeamworkPipeline) -> None:
        self._execution_pipeline = pipeline

    def handle(self, reflex: str, execution_intent: Mapping[str, Any]) -> str:
        if not self._execution_pipeline:
            raise RuntimeError("Execution pipeline has not been bound.")
        handler_name = self.execution_map.get(reflex)
        if not handler_name:
            raise TeamworkPipelineError(f"No execution pipeline configured for '{reflex}'.")
        handler = getattr(self._execution_pipeline, handler_name, None)
        if not handler:
            raise AttributeError(f"Pipeline missing handler '{handler_name}'.")
        return handler(execution_intent)


def _load_client_matrix() -> Mapping[str, Any]:
    path = CONFIG_ROOT / "client_matrix.yaml"
    return _load_yaml_config(path).get("clients", {})


def _load_action_matrix() -> Mapping[str, Any]:
    path = CONFIG_ROOT / "action_matrix.yaml"
    config = _load_yaml_config(path)
    return config.get("execution_pipeline", {})


# Instantiate dependencies using the lightweight defaults above.  Production
# deployments can override these via dependency injection.
TEAMWORK_CLIENT: TeamworkClient = InMemoryTeamworkClient()
CLIENT_MATRIX = _load_client_matrix()
WRITER_AGENT: BriefWriter = CharterBriefWriter()
CUSTODIAN_LOGGER: CustodianLogger = CustodianHubLogger()
SLACK_WEBHOOK = os.environ.get("TEAMWORK_PIPELINE_SLACK_WEBHOOK")
SLACK_NOTIFIER: Notifier | None = SlackNotifier(SLACK_WEBHOOK) if SLACK_WEBHOOK else SlackNotifier()


TEAMWORK_PIPELINE = TeamworkPipeline(
    teamwork=TEAMWORK_CLIENT,
    client_matrix=CLIENT_MATRIX,
    writer=WRITER_AGENT,
    logger=CUSTODIAN_LOGGER,
    notifier=SLACK_NOTIFIER,
)

ACTION_MATRIX = ActionMatrix(_load_action_matrix())
ACTION_MATRIX.bind_execution_pipeline(TEAMWORK_PIPELINE)
