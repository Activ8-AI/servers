from __future__ import annotations

import argparse
import importlib
from typing import Protocol


class RunFunc(Protocol):
    def __call__(self, *, ci: bool = False, dry_run: bool = False) -> None: ...

ROUTES = {
    "activ8": "activ8_governor",
    "lma": "lma_governor",
    "personal": "personal_governor",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Route invocation to a specific governor")
    parser.add_argument("target", choices=list(ROUTES.keys()) + ["all"], help="Governor to run")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = ROUTES.keys() if args.target == "all" else [args.target]
    for key in targets:
        module_name = ROUTES[key]
        module = importlib.import_module(module_name)
        run: RunFunc = getattr(module, "run")
        run(ci=True, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
