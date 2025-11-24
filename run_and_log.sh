#!/usr/bin/env bash
set -euo pipefail
STACK_PATH="${1:?Usage: ./run_and_log.sh stacks/<stack>.yaml}"
TS="$(date -u +%Y-%m-%d/%H%M%S)"
RUN_DIR="PreservationVault/runs/${TS}"
mkdir -p "${RUN_DIR}/outputs"
python3 codex_relay.py --persona kim --role advisor --payload "{}" --stacks-dir "stacks" --run-dir "${RUN_DIR}" > "${RUN_DIR}/relay.json"
python3 codex_logger.py --run-dir "${RUN_DIR}" --record-env
cp codex_evaluation.json "${RUN_DIR}/evaluation.json"
git -C PreservationVault add .
git -C PreservationVault commit -m "Run ${TS}"
