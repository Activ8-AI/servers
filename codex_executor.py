#!/usr/bin/env python3
"""
codex_executor

Executes the resolved relay payload by synthesizing a normalized JSON response
for each agent declared in the stack configuration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute a Codex relay payload.")
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Directory containing relay.json and where executor output will live.",
    )
    parser.add_argument(
        "--output-file",
        default="executor.json",
        help="Filename for execution results (written inside run directory).",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
        if not isinstance(data, dict):
            raise SystemExit(f"Expected JSON object in {path}")
        return data


def summarize_payload(payload: Dict[str, Any]) -> List[str]:
    if not payload:
        return ["No payload provided; defaulting to advisory heuristics."]
    summary = []
    for key, value in payload.items():
        summary.append(f"{key}={value!r}")
    return summary


def synthesize_agent_response(
    agent: Dict[str, Any], persona: str, role: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    advisory_points = summarize_payload(payload)
    created = datetime.now(tz=timezone.utc).isoformat()
    return {
        "agent": agent.get("name"),
        "model": agent.get("model"),
        "created_at": created,
        "role_context": f"{persona}:{role}",
        "advice": [
            "Maintain charter alignment and document key assumptions.",
            *advisory_points,
            "Output normalized per CFMS requirements.",
        ],
    }


def build_execution_record(relay: Dict[str, Any]) -> Dict[str, Any]:
    persona = relay.get("persona", "unknown")
    role = relay.get("role", "unspecified")
    payload = relay.get("payload") or {}
    agents = relay.get("agents") or []

    responses = [
        synthesize_agent_response(agent, persona, role, payload) for agent in agents
    ]

    return {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "persona": persona,
        "role": role,
        "responses": responses,
    }


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    relay_path = run_dir / "relay.json"
    relay_data = load_json(relay_path)
    record = build_execution_record(relay_data)

    output_path = run_dir / args.output_file
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)

    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
