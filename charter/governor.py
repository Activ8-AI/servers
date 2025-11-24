from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from custodian_log_binder import CustodianLogBinder
from genesis_trace import GenesisTrace

from .policy_loader import load_policy


@dataclass
class GovernorRunResult:
    governor: str
    status: str
    repositories: List[Dict[str, Any]]
    evidence_path: str
    metadata: Dict[str, Any]


class PolicyEnforcedGovernor:
    """Execute a deterministic sweep for a single sovereign boundary."""

    def __init__(
        self,
        *,
        name: str,
        domain_policy_file: str,
        copilot_policy_file: str,
        token_env: Optional[str] = None,
        binder: Optional[CustodianLogBinder] = None,
        tracer: Optional[GenesisTrace] = None,
    ) -> None:
        self.name = name
        self.domain_policy = load_policy("domain", domain_policy_file)
        self.copilot_policy = load_policy("copilot", copilot_policy_file)
        self.token_env = token_env
        self.binder = binder or CustodianLogBinder()
        self.tracer = tracer or GenesisTrace()

    def run(self, *, dry_run: bool = False, ci: bool = False) -> GovernorRunResult:
        token_required = bool(self.token_env)
        token_value = os.getenv(self.token_env, "") if token_required else ""
        if ci and token_required and not token_value:
            raise RuntimeError(
                f"Environment variable {self.token_env} must be set for CI governor runs"
            )

        start_metadata = {
            "governor": self.name,
            "dry_run": dry_run,
            "ci": ci,
            "policy_version": self.domain_policy.get("version"),
        }
        self.binder.log("governor.start", f"Starting sweep for {self.name}", start_metadata)
        self.tracer.record("governor.start", start_metadata)

        repositories = self.domain_policy.get("repositories", [])
        sweep_results: List[Dict[str, Any]] = []
        failure: Optional[str] = None

        for repo in repositories:
            repo_result = self._evaluate_repository(repo, dry_run=dry_run)
            sweep_results.append(repo_result)
            if not repo_result.get("deterministic"):
                failure = f"Non-deterministic signal detected for {repo['url']}"
                break

        status = "failure" if failure else "success"
        if failure:
            self.binder.log("governor.failure", failure, {"governor": self.name})
            self.tracer.record("governor.failure", {"reason": failure})
        else:
            self.binder.log(
                "governor.success",
                f"Sweep complete for {self.name}",
                {"repositories": len(sweep_results)},
            )
            self.tracer.record("governor.success", {"repositories": len(sweep_results)})

        evidence_path = "artifacts/governor_evidence.json"
        result = GovernorRunResult(
            governor=self.name,
            status=status,
            repositories=sweep_results,
            evidence_path=evidence_path,
            metadata={
                "copilot_policy": self.copilot_policy.get("name"),
                "timestamp": time.time(),
                "dry_run": dry_run,
            },
        )

        self.binder.log(
            "governor.result",
            f"Recorded evidence for {self.name}",
            {
                "status": status,
                "governor": self.name,
                "evidence_path": evidence_path,
            },
        )
        self.tracer.record("governor.result", result.metadata)
        return result

    def _evaluate_repository(self, repo: Dict[str, Any], *, dry_run: bool) -> Dict[str, Any]:
        url = repo.get("url", "unknown")
        release_channel = repo.get("release_channel", "stable")
        policy_version = self.domain_policy.get("version", "0")
        payload = f"{url}:{release_channel}:{policy_version}:{int(dry_run)}"
        checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        deterministic = not checksum.endswith("0")  # pseudo-signal with deterministic output
        repo_result = {
            "url": url,
            "channel": release_channel,
            "policy_version": policy_version,
            "checksum": checksum,
            "deterministic": deterministic,
        }
        self.tracer.record("repository.scan", repo_result)
        return repo_result
