from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from charter.paths import ARTIFACTS_ROOT
from custodian_log_binder import CustodianLogBinder


def aggregate(output: Path = ARTIFACTS_ROOT / "governor_evidence.json") -> Path:
    binder = CustodianLogBinder()
    log_path = binder.path
    evidence: Dict[str, Dict[str, str]] = {}

    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("event_type") != "governor.result":
                    continue
                metadata = entry.get("metadata", {})
                governor = metadata.get("governor", "unknown")
                evidence[governor] = {
                    "status": metadata.get("status", "unknown"),
                    "evidence_path": metadata.get("evidence_path", str(output)),
                    "timestamp": entry.get("timestamp", ""),
                }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, sort_keys=True)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate governor evidence into JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=ARTIFACTS_ROOT / "governor_evidence.json",
        help="Path to write aggregated evidence",
    )
    args = parser.parse_args()
    result = aggregate(args.output)
    print(f"Evidence aggregated at {result}")


if __name__ == "__main__":
    main()
