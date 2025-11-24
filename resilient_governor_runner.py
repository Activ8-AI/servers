from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import List

from charter.governor import PolicyEnforcedGovernor, GovernorRunResult
from custodian_log_binder import CustodianLogBinder
from genesis_trace import GenesisTrace


@dataclass
class GovernorSpec:
    name: str
    domain_policy: str
    copilot_policy: str
    token_env: str


GOVERNOR_SPECS: List[GovernorSpec] = [
    GovernorSpec(
        name="Activ8 AI Governor",
        domain_policy="activ8_domain_policy.json",
        copilot_policy="activ8-ai-copilot.json",
        token_env="PAT_ACTIV8_AI",
    ),
    GovernorSpec(
        name="LMAOS Governor",
        domain_policy="lma_domain_policy.json",
        copilot_policy="lma-copilot.json",
        token_env="PAT_LMA",
    ),
    GovernorSpec(
        name="Personal Governor",
        domain_policy="personal_domain_policy.json",
        copilot_policy="personal-copilot.json",
        token_env="PAT_PERSONAL",
    ),
]


def run_spec(spec: GovernorSpec, *, dry_run: bool, ci: bool) -> GovernorRunResult:
    binder = CustodianLogBinder()
    tracer = GenesisTrace()
    governor = PolicyEnforcedGovernor(
        name=spec.name,
        domain_policy_file=spec.domain_policy,
        copilot_policy_file=spec.copilot_policy,
        token_env=spec.token_env,
        binder=binder,
        tracer=tracer,
    )

    retry_backoff = governor.domain_policy.get("sweep", {}).get("retry_backoff_seconds", [30, 60, 120])
    attempts = len(retry_backoff) + 1

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return governor.run(dry_run=dry_run, ci=ci)
        except Exception as exc:  # pragma: no cover - resilience path
            last_error = exc
            binder.log(
                "governor.retry",
                f"{spec.name} attempt {attempt} failed: {exc}",
                {"governor": spec.name, "attempt": attempt},
            )
            if attempt == attempts:
                break
            sleep_for = retry_backoff[min(attempt - 1, len(retry_backoff) - 1)]
            time.sleep(sleep_for)

    assert last_error is not None
    raise last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Resiliently execute all governors")
    parser.add_argument("--dry-run", action="store_true", help="Run without enforcing mutations")
    parser.add_argument("--subset", choices=["activ8", "lma", "personal", "all"], default="all")
    args = parser.parse_args()

    specs = GOVERNOR_SPECS if args.subset == "all" else [
        next(spec for spec in GOVERNOR_SPECS if args.subset in spec.name.lower())
    ]

    for spec in specs:
        result = run_spec(spec, dry_run=args.dry_run, ci=True)
        print(f"{spec.name} -> {result.status}")


if __name__ == "__main__":
    main()
