#!/usr/bin/env python3
"""
codex_relay

Responsibilities:
- Resolve persona/role routing for a given stack.
- Merge CFMS invariants declared via YAML includes.
- Normalize the selected configuration and payload to JSON output.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime, timezone

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve Codex stack configuration.")
    parser.add_argument("--persona", required=True, help="Persona identifier to route.")
    parser.add_argument("--role", required=True, help="Role requested for the persona.")
    parser.add_argument(
        "--payload",
        default="{}",
        help="JSON payload representing inputs for the executor.",
    )
    parser.add_argument(
        "--stacks-dir",
        default="stacks",
        help="Directory containing stack definitions.",
    )
    parser.add_argument(
        "--stack-file",
        help="Optional explicit stack file. Overrides persona/role discovery.",
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Directory where run artifacts should be written.",
    )
    return parser.parse_args()


def json_loads(data: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(data or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("Payload JSON must decode to an object")
        return parsed
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid payload JSON: {exc}") from exc


def load_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Stack file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise SystemExit(f"Expected mapping in YAML file: {path}")
        return data


def discover_stack(
    stacks_dir: Path, persona: str, role: str, stack_file: str | None
) -> Tuple[Dict[str, Any], Path]:
    if stack_file:
        path = Path(stack_file)
        return load_yaml_file(path), path

    for path in sorted(stacks_dir.glob("*.yaml")):
        data = load_yaml_file(path)
        routing = data.get("routing") or {}
        if routing.get("persona") == persona and routing.get("role") == role:
            return data, path

    raise SystemExit(
        f"No stack found in {stacks_dir} for persona={persona!r}, role={role!r}"
    )


def deep_merge(target: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in incoming.items():
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, dict)
        ):
            target[key] = deep_merge(target[key], value)
        elif (
            key in target
            and isinstance(target[key], list)
            and isinstance(value, list)
        ):
            target[key] = [*target[key], *value]
        else:
            target[key] = value
    return target


def collect_invariants(stack: Dict[str, Any], stacks_dir: Path) -> Dict[str, Any]:
    aggregate: Dict[str, Any] = {}
    include_files: List[str] = stack.get("include") or []
    for include in include_files:
        include_path = (stacks_dir / include).resolve()
        include_data = load_yaml_file(include_path)
        aggregate = deep_merge(aggregate, include_data)
    return aggregate


def build_record(
    stack: Dict[str, Any],
    stack_path: Path,
    payload: Dict[str, Any],
    invariants: Dict[str, Any],
    persona: str,
    role: str,
) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    return {
        "timestamp": timestamp,
        "persona": persona,
        "role": role,
        "stack_file": str(stack_path),
        "meta": stack.get("meta", {}),
        "routing": stack.get("routing", {}),
        "agents": stack.get("agents", []),
        "cfms_invariants": invariants.get("cfms_invariants", {}),
        "payload": payload,
    }


def ensure_run_dir(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    stacks_dir = Path(args.stacks_dir)
    run_dir = Path(args.run_dir)
    ensure_run_dir(run_dir)

    payload = json_loads(args.payload)
    stack, stack_path = discover_stack(
        stacks_dir=stacks_dir,
        persona=args.persona,
        role=args.role,
        stack_file=args.stack_file,
    )
    invariants = collect_invariants(stack, stacks_dir)
    record = build_record(stack, stack_path, payload, invariants, args.persona, args.role)

    json_output = json.dumps(record, indent=2, sort_keys=False)
    print(json_output)


if __name__ == "__main__":
    main()
