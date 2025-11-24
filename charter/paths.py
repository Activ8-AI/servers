from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICIES_ROOT = ROOT / "policies"
LOG_ROOT = ROOT / "logs"
ARTIFACTS_ROOT = ROOT / "artifacts"

for path in (POLICIES_ROOT, LOG_ROOT, ARTIFACTS_ROOT):
    path.mkdir(parents=True, exist_ok=True)
