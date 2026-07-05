from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.runtime_facade import run_scheduler_once  # noqa: E402


def _summary(result: dict[str, object]) -> dict[str, object]:
    report = result.get("report") or {}
    if not isinstance(report, dict):
        report = {}
    return {
        "run_id": result.get("run_id"),
        "dry_run": result.get("dry_run"),
        "report_path": report.get("path"),
        "review_count": result.get("review_queue_size", 0),
        "skipped_count": result.get("skipped_count", 0),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the scheduler once and print a compact JSON summary.")
    parser.add_argument("--base-data-dir", default=None, help="Override the base data directory.")
    parser.add_argument("--run-key", default=None, help="Optional run key for deterministic outputs.")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True, help="Run the scheduler in dry-run mode.")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Run the scheduler without dry-run mode.")
    args = parser.parse_args(argv)

    result = run_scheduler_once(base_data_dir=args.base_data_dir, dry_run=args.dry_run, run_key=args.run_key)
    print(json.dumps(_summary(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
