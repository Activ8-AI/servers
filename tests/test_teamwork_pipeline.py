from __future__ import annotations

import pytest

from modules.teamwork_pipeline import ExecutionIntent, TeamworkPipeline
from modules.teamwork_pipeline.pipeline import (
    BriefWriter,
    CustodianLogger,
    Notifier,
    TeamworkClient,
)


class StubTeamworkClient(TeamworkClient):
    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, object]] = {}
        self.subtasks: dict[str, list[str]] = {}
        self.sprints: dict[str, dict[str, object]] = {}
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter}"

    def create_task(
        self,
        *,
        project_id: str,
        task_name: str,
        description: str,
        due: str | None,
        tags: list[str],
        evidence_urls: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> str:
        task_id = self._next_id("task")
        self.tasks[task_id] = {
            "project_id": project_id,
            "name": task_name,
            "description": description,
            "due": due,
            "tags": tags,
            "evidence_urls": evidence_urls or [],
            "assignees": assignees or [],
        }
        self.subtasks[task_id] = []
        return task_id

    def create_subtask(
        self, *, parent_id: str, task_name: str, project_id: str
    ) -> str:
        subtask_id = self._next_id("subtask")
        self.subtasks[parent_id].append(task_name)
        return subtask_id

    def create_sprint(
        self,
        *,
        project_id: str,
        name: str,
        tasks: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        sprint_id = self._next_id("sprint")
        self.sprints[sprint_id] = {
            "project_id": project_id,
            "name": name,
            "tasks": tasks,
            "start_date": start_date,
            "end_date": end_date,
        }
        return sprint_id


class StubWriter(BriefWriter):
    def attach_brief(self, execution_intent: ExecutionIntent) -> str:
        return execution_intent.description


class StubLogger(CustodianLogger):
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    def audit(self, **payload):
        self.entries.append(payload)


class StubNotifier(Notifier):
    def __init__(self) -> None:
        self.messages: list[tuple[list[str], str]] = []

    def notify(self, *, role_ids, message, metadata):
        self.messages.append((list(role_ids), message))


@pytest.fixture()
def pipeline() -> tuple[TeamworkPipeline, StubTeamworkClient, StubNotifier, StubLogger]:
    client = StubTeamworkClient()
    notifier = StubNotifier()
    logger = StubLogger()
    pipeline = TeamworkPipeline(
        teamwork=client,
        client_matrix={
            "wilson_case": {
                "teamwork_project_id": "proj-1",
                "default_role_ids": ["role-1"],
                "default_assignees": ["user-1"],
            }
        },
        writer=StubWriter(),
        logger=logger,
        notifier=notifier,
    )
    return pipeline, client, notifier, logger


def test_dispatch_creates_task_and_subtasks(pipeline):
    pipeline_instance, client, notifier, logger = pipeline
    payload = {
        "client_id": "wilson_case",
        "reflex": "competitor_reflex",
        "urgency": 4,
        "title": "Competitor Price Change Detected",
        "description": "Competitor X adjusted pricing by 7%.",
        "actions": [
            "Run Pricing Impact Model",
            "Update Competitor Watch",
            "Generate Positioning Brief",
        ],
        "due_date": "2025-11-02",
        "tags": ["pricing"],
        "evidence_urls": ["https://example.com/source"],
        "source_event": "event_id:maos.competitor.signal:abc123",
        "confidence": 0.91,
    }

    task_id = pipeline_instance.dispatch(payload)

    assert task_id in client.tasks
    assert client.subtasks[task_id] == payload["actions"]
    assert notifier.messages, "Expected notifier to be invoked"
    assert logger.entries[0]["task_id"] == task_id


def test_dispatch_creates_sprint_when_urgency_high(pipeline):
    pipeline_instance, client, *_ = pipeline
    payload = {
        "client_id": "wilson_case",
        "reflex": "market_reflex",
        "urgency": 5,
        "title": "Market Shock",
        "description": "Systemic shift detected",
        "actions": ["Assess Impact"],
        "due_date": "2025-11-02",
        "tags": ["market"],
        "evidence_urls": ["https://example.com/source"],
        "source_event": "event_id:market:xyz",
        "confidence": 0.8,
    }

    pipeline_instance.dispatch(payload)

    assert client.sprints, "High urgency reflex should create sprint"
