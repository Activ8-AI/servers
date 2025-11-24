from __future__ import annotations

import argparse

from charter.governor import PolicyEnforcedGovernor
from custodian_log_binder import CustodianLogBinder
from genesis_trace import GenesisTrace


def build_governor() -> PolicyEnforcedGovernor:
    return PolicyEnforcedGovernor(
        name="Personal Governor",
        domain_policy_file="personal_domain_policy.json",
        copilot_policy_file="personal-copilot.json",
        token_env="PAT_PERSONAL",
        binder=CustodianLogBinder(),
        tracer=GenesisTrace(),
    )


def run(*, ci: bool = False, dry_run: bool = False):
    governor = build_governor()
    result = governor.run(ci=ci, dry_run=dry_run)
    print(f"Personal Governor run status: {result.status}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Personal governor sweep")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(ci=args.ci, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
