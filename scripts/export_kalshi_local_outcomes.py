from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.outcome_migration import build_kalshi_outcome_migration_package, write_migration_package  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    del argv
    package = build_kalshi_outcome_migration_package()
    write_result = write_migration_package(package, dry_run=True)
    summary = {
        "status": write_result["status"],
        "records_discovered": package.get("records_discovered", 0),
        "records_valid": package.get("records_valid", 0),
        "records_rejected": package.get("records_rejected", 0),
        "duplicate_count": package.get("duplicate_count", 0),
        "raw_duplicate_reference_count": package.get("raw_duplicate_reference_count", package.get("duplicate_count", 0)),
        "logical_duplicate_count": package.get("logical_duplicate_count", 0),
        "final_outcome_counts": package.get("final_outcome_counts", {}),
        "supporting_paper_decision_count": package.get("supporting_paper_decision_count", 0),
        "latest_path": write_result["latest_path"],
        "item_path": write_result["item_path"],
        "daily_json_path": write_result["daily_json_path"],
        "daily_markdown_path": write_result["daily_markdown_path"],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
