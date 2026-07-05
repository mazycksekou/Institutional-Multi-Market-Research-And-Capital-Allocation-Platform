from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.runtime_facade import get_scheduler_health  # noqa: E402


def _summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "ok": result.get("ok", True),
        "dry_run": result.get("dry_run", True),
        "human_approval_required": result.get("human_approval_required", True),
        "auto_execution_enabled": result.get("auto_execution_enabled", False),
        "counts": {
            "review_queue_count": result.get("review_queue_count", 0),
            "provider_count": result.get("provider_count", 0),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a compact scheduler health summary.")
    parser.add_argument("--base-data-dir", default=None, help="Override the base data directory.")
    args = parser.parse_args(argv)

    result = get_scheduler_health(base_data_dir=args.base_data_dir)
    print(json.dumps(_summary(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
