## Teamwork Pipeline (Reflex → Execution)

The Teamwork pipeline turns Reflex DAG execution intents into real, charter-compliant
work items inside Teamwork.  It performs the following steps for every intent:

1. Validate the canonical execution intent payload (`modules/teamwork_pipeline/pipeline.py`)
2. Resolve the client → Teamwork project mapping from `configs/client_matrix.yaml`
3. Create the primary task, attach the generated charter brief, and stamp reflex tags
4. Fan out subtasks for each prescribed action
5. Optionally spin up a “{client} – Reflex Window – {date}” sprint when urgency ≥ 4 and reflex ∈ {algorithm_reflex, competitor_reflex, market_reflex}
6. Ping the configured role IDs / Slack webhook with assignment context
7. Log a signed entry to the Custodian Hub (JSONL) including the SRR content hash

### Execution Intent Schema

```json
{
  "client_id": "wilson_case",
  "reflex": "competitor_reflex",
  "urgency": 4,
  "title": "Competitor Price Change Detected",
  "description": "Competitor X adjusted pricing by 7%.",
  "actions": ["Run Pricing Impact Model"],
  "due_date": "2025-11-02",
  "tags": ["reflex", "auto", "competitor", "pricing"],
  "evidence_urls": ["https://example.com/source"],
  "source_event": "event_id:maos.competitor.signal:abc123",
  "confidence": 0.91
}
```

Use `ExecutionIntent.from_payload(...)` to enforce this contract and generate the SRR `content_hash`.

### Configuration

* `configs/action_matrix.yaml` maps reflex types to the `TeamworkPipeline.dispatch` handler
* `configs/client_matrix.yaml` pairs each `client_id` with the upstream Teamwork project plus role IDs/assignees

### Agent Hub Wiring

`agent_hub.py` boots the pipeline with lightweight defaults:

* `InMemoryTeamworkClient` – development stub (replace with HTTP client for prod)
* `CharterBriefWriter` – renders the charter brief that is attached to every task
* `CustodianHubLogger` – streams SRR entries into `logs/custodian_hub.log`
* `SlackNotifier` – prints Slack-style messages or POSTs to `TEAMWORK_PIPELINE_SLACK_WEBHOOK`
* `ActionMatrix` – minimal dispatcher that routes reflexes to the execution pipeline

Production deployments can set their own dependencies (real Teamwork API client, notifier, etc.) before binding the pipeline:

```python
ACTION_MATRIX.bind_execution_pipeline(
    TeamworkPipeline(
        teamwork=YourTeamworkClient(...),
        client_matrix=load_client_matrix(),
        writer=YourCharterWriter(),
        logger=CustodianHubLogger(...),
        notifier=SlackNotifier(os.getenv("TEAMWORK_PIPELINE_SLACK_WEBHOOK")),
    )
)
```

With this wiring in place every reflex automatically materializes as Teamwork work with auditable custody logs and sprint scaffolding for high-signal events.
