from __future__ import annotations

import re
from pathlib import Path

from scripts import daily_data_hygiene as hygiene


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "archive" / "historical_reports" / "PHASE10K8ZFE2_DAILY_DATA_HYGIENE_SCHEDULER_REPORT.md"
SCRIPT = ROOT / "scripts" / "daily_data_hygiene.py"
POWERSHELL = ROOT / "scripts" / "run_daily_data_hygiene.ps1"
DOCS = ROOT / "docs" / "operations" / "DAILY_DATA_HYGIENE_SCHEDULER.md"
README = ROOT / "README.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zfe2_daily_data_hygiene_scheduler_contract(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sample.json").write_text("{}", encoding="utf-8")
    (data_dir / "sample.jsonl").write_text("{}\n", encoding="utf-8")
    (data_dir / "sample.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (data_dir / "notes.md").write_text("# note", encoding="utf-8")
    (data_dir / "storage.db").write_text("db", encoding="utf-8")

    report = read_text(REPORT)
    script_text = read_text(SCRIPT)
    powershell_text = read_text(POWERSHELL)
    docs_text = read_text(DOCS)
    readme_text = read_text(README)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Why This Phase Exists",
        "Daily Hygiene Contract",
        "10 PM Schedule Policy",
        "R2 Verification Policy",
        "Deletion Safety Policy",
        "Dry-Run Behavior",
        "Execute Behavior",
        "PowerShell Runner",
        "Windows Task Scheduler Setup",
        "Agent Policy",
        "Files Changed",
        "Tests Run",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    required_strings = [
        "10K8ZFE2",
        "Daily Data Hygiene Scheduler",
        "10 PM Verified Cleanup",
        "let generated files build during the day",
        "run cleanup around 10 PM",
        "dry-run by default",
        "execute requires explicit flag",
        "archive before delete",
        "upload_status",
        "verification_status",
        "deletion_eligible",
        "deletion_performed",
        "manifest-listed files only",
        "no blind delete",
        "markdown files preserved",
        "DB files preserved",
        "source code preserved",
        "tests/fixtures preserved",
        "tracked files preserved",
        "manifests preserved",
        "archives preserved",
        "files outside data/ preserved",
        "no credentials committed",
        "no secrets printed",
        "R2 credentials come from environment variables only",
        "Windows Task Scheduler",
        "agent is advisory only",
        "agent does not directly delete files",
        "no AI integration",
        "no ML training",
        "no backtest runner",
        "no broker execution",
        "no real trade execution",
        "no scraper actions",
        "Proceed to 10K8ZFF Canonical Owner Decision Report",
    ]
    for item in required_strings:
        assert item in report

    assert "Set-StrictMode -Version Latest" in powershell_text
    assert "-Execute" in powershell_text
    assert "-DryRun" in powershell_text
    assert "daily_data_hygiene.py" in powershell_text

    assert "schtasks /Create /TN" in docs_text
    assert "Run from the repo root" in docs_text
    assert "The repository does not auto-register the task" in docs_text

    args = hygiene.parse_args([])
    assert args.execute is False
    assert args.dry_run is False

    execute_args = hygiene.parse_args(["--execute", "--upload", "--verify", "--cleanup", "--allow-delete-local-raw"])
    assert execute_args.execute is True
    assert execute_args.upload is True
    assert execute_args.verify is True
    assert execute_args.cleanup is True
    assert execute_args.allow_delete_local_raw is True

    inventory = hygiene.inspect_inventory(data_dir)
    assert inventory["json_files"] == 1
    assert inventory["jsonl_files"] == 1
    assert inventory["csv_files"] == 1
    assert inventory["markdown_files"] == 1
    assert inventory["db_files"] == 1

    plan = hygiene.build_daily_hygiene_plan(
        hygiene.parse_args(["--input-dir", str(data_dir)]),
        inventory=inventory,
        env_status={name: "MISSING" for name in hygiene.R2_ENV_VARS},
    )
    assert plan["status"] == "dry_run"
    assert plan["execute_requested"] is False

    blocked_plan = hygiene.build_daily_hygiene_plan(
        hygiene.parse_args(["--input-dir", str(data_dir), "--execute", "--upload", "--verify", "--cleanup", "--allow-delete-local-raw"]),
        inventory=inventory,
        env_status={name: "MISSING" for name in hygiene.R2_ENV_VARS},
    )
    assert blocked_plan["status"] == "blocked"

    ready_plan = hygiene.build_daily_hygiene_plan(
        hygiene.parse_args(["--input-dir", str(data_dir), "--execute", "--upload", "--verify", "--cleanup", "--allow-delete-local-raw"]),
        inventory=inventory,
        env_status={name: "SET" for name in hygiene.R2_ENV_VARS},
    )
    assert ready_plan["status"] == "ready"
    assert ready_plan["reason"] == "eligible generated files ready for archive before delete"
    assert ready_plan["batches"]

    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None
    assert "your_real_secret" not in report
    assert "your_real_secret" not in readme_text
    assert re.search(r"AKIA[0-9A-Z]{16}", script_text) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", script_text) is None
    assert "your_real_secret" not in script_text

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))
