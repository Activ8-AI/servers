# Meta Mega Codex — Charter Standard Execution

This repository now embeds the full Meta Mega Codex stack. Each layer maps to concrete artifacts to keep deterministic, auditable multi-governor sweeps online.

## Layer Overview

1. **Charter Doctrine**
   - Immutability enforced through append-only logs in `logs/` and JSON artifacts in `artifacts/`.
   - Determinism achieved via policy-pinned binaries plus GitHub workflows locked to `ubuntu-22.04`, `actions/checkout@v4.1.0`, and `actions/setup-python@v4.7.0`.

2. **Policies**
   - Domain policies live under `policies/domain/*.json`.
   - Copilot policies live under `policies/copilot/*.json`.

3. **Governors**
   - `activ8_governor.py`
   - `lma_governor.py`
   - `personal_governor.py`
   - Each imports the shared `charter.PolicyEnforcedGovernor` base and enforces the matching domain/copilot pair.

4. **Resilience**
   - `resilient_governor_runner.py` orchestrates retries/backoff per policy.
   - `watchdog.py` flags stale activity windows.
   - `governor_evidence_aggregator.py` condenses custodian logs into JSON dashboards.

5. **Logging Spine**
   - `custodian_log_binder.py` (JSONL audit log).
   - `genesis_trace.py` (fine-grained trace log).

6. **Router**
   - `mcp_governor_router.py` dispatches CLI requests to specific governors or the entire set.

7. **Workflows**
   - All governor automations are defined in `.github/workflows/*.yml` with deterministic runners and pip caching.

8. **Operations**
   - Local commands align with the charter invocation phrases:
     - `PAT_ACTIV8_AI=<token> python activ8_governor.py --ci`
     - `PAT_LMA=<token> python lma_governor.py --ci`
     - `PAT_PERSONAL=<token> python personal_governor.py --ci`
     - `PAT_ACTIV8_AI=<token> PAT_LMA=<token> PAT_PERSONAL=<token> python resilient_governor_runner.py`
     - `python governor_evidence_aggregator.py`
     - `python watchdog.py --threshold 60`

Use “Charter On — Execute Meta Mega Codex.” to flip the entire system live and “Run Governors — Activ8 AI, LMAOS, PERSONAL — Charter Standard Execution.” for full sweeps.
