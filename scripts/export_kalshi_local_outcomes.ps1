Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

@'
import json
from automation_scheduler.outcome_migration import build_kalshi_outcome_migration_package, write_migration_package

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
'@ | python -

exit $LASTEXITCODE
