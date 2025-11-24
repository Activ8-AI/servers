from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Iterable, Mapping, MutableMapping, Protocol, Sequence, runtime_checkable


class TeamworkPipelineError(RuntimeError):
    """Raised when the Teamwork pipeline cannot fulfill a dispatch request."""


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    """
    Canonical representation of a reflex execution intent payload.

    The dataclass enforces the schema described in the reflex → execution
    pipeline specification and offers helpers for hashing and tag handling.
    """

    client_id: str
    reflex: str
    urgency: int
    title: str
    description: str
    actions: tuple[str, ...]
    due_date: str | None
    tags: tuple[str, ...]
    evidence_urls: tuple[str, ...]
    source_event: str
    confidence: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    REQUIRED_KEYS: tuple[str, ...] = (
        "client_id",
        "reflex",
        "urgency",
        "title",
        "description",
        "actions",
        "due_date",
        "tags",
        "evidence_urls",
        "source_event",
        "confidence",
    )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ExecutionIntent":
        """Validate raw payload data and convert it into an ExecutionIntent."""
        missing = [key for key in cls.REQUIRED_KEYS if key not in payload]
        if missing:
            raise TeamworkPipelineError(
                f"Execution intent missing required fields: {', '.join(missing)}"
            )

        actions = tuple(cls._normalize_list(payload["actions"], "actions"))
        tags = tuple(cls._normalize_list(payload["tags"], "tags"))
        evidence = tuple(cls._normalize_list(payload["evidence_urls"], "evidence_urls"))

        urgency = int(payload["urgency"])
        if not 0 <= urgency <= 5:
            raise TeamworkPipelineError("Urgency must be between 0 and 5.")

        confidence = float(payload["confidence"])
        if not 0 <= confidence <= 1:
            raise TeamworkPipelineError("Confidence must be between 0 and 1.")

        due_date = payload.get("due_date")
        if due_date:
            # Basic ISO-8601 validation
            try:
                date.fromisoformat(due_date)
            except ValueError as exc:  # pragma: no cover - isoformat failure path
                raise TeamworkPipelineError("due_date must be ISO-8601 formatted.") from exc

        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise TeamworkPipelineError("metadata must be a mapping.")

        return cls(
            client_id=str(payload["client_id"]),
            reflex=str(payload["reflex"]),
            urgency=urgency,
            title=str(payload["title"]),
            description=str(payload["description"]),
            actions=actions,
            due_date=due_date,
            tags=tags,
            evidence_urls=evidence,
            source_event=str(payload["source_event"]),
            confidence=confidence,
            metadata=metadata,
        )

    @staticmethod
    def _normalize_list(value: Any, field_name: str) -> tuple[str, ...]:
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            raise TeamworkPipelineError(f"{field_name} must be a list of strings.")
        normalized = tuple(str(item) for item in value if str(item).strip())
        if not normalized:
            raise TeamworkPipelineError(f"{field_name} must contain at least one entry.")
        return normalized

    def merged_tags(self) -> tuple[str, ...]:
        """Return the tag set with mandatory reflex metadata."""
        base = {"reflex", "auto", self.reflex}
        base.update(self.tags)
        return tuple(sorted(base))

    def content_hash(self) -> str:
        """Stable SHA-256 hash of the normalized payload, used for SRR logging."""
        payload = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@runtime_checkable
class TeamworkClient(Protocol):
    """Minimal Teamwork client interface required by the pipeline."""

    def create_task(
        self,
        *,
        project_id: str,
        task_name: str,
        description: str,
        due: str | None,
        tags: Sequence[str],
        evidence_urls: Sequence[str] | None = None,
        assignees: Sequence[str] | None = None,
    ) -> str: ...

    def create_subtask(
        self, *, parent_id: str, task_name: str, project_id: str
    ) -> str: ...

    def create_sprint(
        self,
        *,
        project_id: str,
        name: str,
        tasks: Sequence[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str: ...


@runtime_checkable
class BriefWriter(Protocol):
    """Writer agent responsible for attaching the charter-standard brief."""

    def attach_brief(self, execution_intent: ExecutionIntent) -> str: ...


@runtime_checkable
class CustodianLogger(Protocol):
    """Custodian Hub logger contract."""

    def audit(self, **payload: Any) -> None: ...


@runtime_checkable
class Notifier(Protocol):
    """Notification interface (e.g., Slack or other role ID routers)."""

    def notify(
        self,
        *,
        role_ids: Sequence[str],
        message: str,
        metadata: Mapping[str, Any],
    ) -> None: ...


ClientMatrix = Mapping[str, Mapping[str, Any]]


class TeamworkPipeline:
    """Convert reflex execution intents into structured Teamwork work."""

    DEFAULT_SPRINT_REFLEXES = {
        "algorithm_reflex",
        "competitor_reflex",
        "market_reflex",
    }

    def __init__(
        self,
        *,
        teamwork: TeamworkClient,
        client_matrix: ClientMatrix,
        writer: BriefWriter,
        logger: CustodianLogger,
        notifier: Notifier | None = None,
        signer: str = "teamwork_pipeline_v1",
        sprint_reflexes: Iterable[str] | None = None,
    ) -> None:
        if not isinstance(client_matrix, Mapping):
            raise TeamworkPipelineError("client_matrix must be a mapping.")

        self.teamwork = teamwork
        self.client_matrix = client_matrix
        self.writer = writer
        self.logger = logger
        self.notifier = notifier
        self.signer = signer
        self.sprint_reflexes = (
            set(sprint_reflexes) if sprint_reflexes else self.DEFAULT_SPRINT_REFLEXES
        )

    def dispatch(self, execution_intent: Mapping[str, Any]) -> str:
        """
        Primary entry point for Action Matrix → Teamwork work creation.

        Returns the Teamwork task ID created for the provided execution intent.
        """
        intent = (
            execution_intent
            if isinstance(execution_intent, ExecutionIntent)
            else ExecutionIntent.from_payload(execution_intent)
        )

        client_info = self._resolve_client(intent.client_id)
        project_id = client_info["teamwork_project_id"]
        description = self.writer.attach_brief(intent)

        task_id = self.teamwork.create_task(
            project_id=project_id,
            task_name=intent.title,
            description=description,
            due=intent.due_date,
            tags=intent.merged_tags(),
            evidence_urls=intent.evidence_urls,
            assignees=client_info.get("default_assignees"),
        )

        for action in intent.actions:
            self.teamwork.create_subtask(
                parent_id=task_id,
                task_name=action,
                project_id=project_id,
            )

        sprint_id = None
        if self._should_create_sprint(intent):
            sprint_name = self._build_sprint_name(intent)
            sprint_id = self.teamwork.create_sprint(
                project_id=project_id,
                name=sprint_name,
                tasks=[task_id],
                start_date=intent.metadata.get("window_start"),
                end_date=intent.metadata.get("window_end") or intent.due_date,
            )

        self._notify_roles(intent, client_info, task_id, sprint_id)
        self._log_dispatch(intent, task_id, sprint_id)

        return task_id

    def _resolve_client(self, client_id: str) -> MutableMapping[str, Any]:
        if client_id not in self.client_matrix:
            raise TeamworkPipelineError(f"Unknown client '{client_id}' in execution intent.")
        client_info = dict(self.client_matrix[client_id])
        project_id = client_info.get("teamwork_project_id")
        if not project_id:
            raise TeamworkPipelineError(
                f"Client '{client_id}' is missing a teamwork_project_id mapping."
            )
        return client_info

    def _should_create_sprint(self, intent: ExecutionIntent) -> bool:
        return intent.urgency >= 4 and intent.reflex in self.sprint_reflexes

    def _build_sprint_name(self, intent: ExecutionIntent) -> str:
        due = intent.due_date or date.today().isoformat()
        return f"{intent.client_id} – Reflex Window – {due}"

    def _notify_roles(
        self,
        intent: ExecutionIntent,
        client_info: Mapping[str, Any],
        task_id: str,
        sprint_id: str | None,
    ) -> None:
        if not self.notifier:
            return
        role_ids = client_info.get("role_ids") or client_info.get("default_role_ids")
        if not role_ids:
            return
        metadata = {
            "task_id": task_id,
            "client_id": intent.client_id,
            "sprint_id": sprint_id,
            "source_event": intent.source_event,
            "urgency": intent.urgency,
        }
        message = (
            f"[Reflex:{intent.reflex}] {intent.title} is live in Teamwork "
            f"for client {intent.client_id}"
        )
        self.notifier.notify(role_ids=role_ids, message=message, metadata=metadata)

    def _log_dispatch(
        self,
        intent: ExecutionIntent,
        task_id: str,
        sprint_id: str | None,
    ) -> None:
        payload = {
            "event": "teamwork_pipeline_dispatch",
            "client": intent.client_id,
            "task_id": task_id,
            "sprint_id": sprint_id,
            "event_id": intent.source_event,
            "confidence": intent.confidence,
            "due": intent.due_date,
            "signer": self.signer,
            "content_hash": intent.content_hash(),
            "tags": intent.merged_tags(),
        }
        payload.update(intent.metadata or {})
        self.logger.audit(**payload)
