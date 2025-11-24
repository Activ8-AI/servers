#!/usr/bin/env python3
"""
codex_digest_report

Generates aggregate digests over PreservationVault runs.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce Codex digests.")
    parser.add_argument("--vault", default="PreservationVault", help="Vault root path.")
    parser.add_argument(
        "--output",
        help="Optional file to write the digest to. Defaults to stdout.",
    )
    parser.add_argument(
        "--runs-subdir",
        help="Override runs directory (defaults to config/environment.yaml).",
    )
    parser.add_argument(
        "--digests-subdir",
        help="Override digests directory (defaults to config/environment.yaml).",
    )
    return parser.parse_args()


def load_env_config() -> Dict[str, Any]:
    path = Path("config/environment.yaml")
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
        return data if isinstance(data, dict) else {}


def list_run_dirs(vault: Path, runs_subdir: str) -> List[Path]:
    runs_root = vault / runs_subdir
    if not runs_root.exists():
        return []
    return sorted([p for p in runs_root.iterdir() if p.is_dir()])


def read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
        return data if isinstance(data, dict) else None


def aggregate_scores(runs: List[Dict[str, Any]]) -> Dict[str, float]:
    totals: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)
    for run in runs:
        results = run.get("evaluation", {}).get("results") or {}
        for key, value in results.items():
            try:
                totals[key] += float(value)
                counts[key] += 1
            except (TypeError, ValueError):
                continue
    averages = {}
    for key, total in totals.items():
        if counts[key]:
            averages[key] = total / counts[key]
    return averages


def build_digest(
    vault: Path, runs: List[Path], runs_subdir: str, digests_subdir: str
) -> Dict[str, Any]:
    run_records: List[Dict[str, Any]] = []
    for run in runs:
        run_records.append(
            {
                "run_id": run.name,
                "evaluation": read_json(run / "evaluation.json") or {},
                "relay": read_json(run / "relay.json") or {},
                "log": read_json(run / "log.json") or {},
            }
        )

    digest = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "vault": str(vault),
        "runs_subdir": runs_subdir,
        "digests_subdir": digests_subdir,
        "total_runs": len(run_records),
        "average_scores": aggregate_scores(run_records),
        "runs": run_records,
    }
    return digest


def emit_digest(digest: Dict[str, Any], output: str | None, vault: Path, digests_subdir: str) -> None:
    if output:
        output_path = Path(output)
    else:
        digests_dir = vault / digests_subdir
        digests_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        output_path = digests_dir / f"digest-{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(digest, handle, indent=2)
    print(json.dumps(digest, indent=2))


def main() -> None:
    args = parse_args()
    env_cfg = load_env_config()
    runs_subdir = args.runs_subdir or env_cfg.get("environment", {}).get("runs_subdir", "runs")
    digests_subdir = args.digests_subdir or env_cfg.get("environment", {}).get("digests_subdir", "digests")

    vault = Path(args.vault)
    runs = list_run_dirs(vault, runs_subdir)
    digest = build_digest(vault, runs, runs_subdir, digests_subdir)
    emit_digest(digest, args.output, vault, digests_subdir)


if __name__ == "__main__":
    main()
