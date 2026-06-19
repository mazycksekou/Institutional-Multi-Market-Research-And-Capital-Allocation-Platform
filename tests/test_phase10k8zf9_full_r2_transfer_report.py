from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF9_FULL_R2_TRANSFER_AND_VERIFIED_LOCAL_DELETION_REPORT.md"
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
PIPELINE = ROOT / "scripts" / "r2_archive_pipeline.py"
ADAPTER = ROOT / "src" / "storage" / "r2_archive_adapter.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str]) -> None:
    for item in items:
        assert item in text, f"missing: {item}"


def test_phase10k8zf9_full_transfer_report_and_safety_text() -> None:
    assert REPORT.exists()

    report = read_text(REPORT)
    readme = read_text(README)
    gitignore = read_text(GITIGNORE)
    pipeline = read_text(PIPELINE)
    adapter = read_text(ADAPTER)

    sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZF8",
        "R2 Environment Preflight",
        "Credential Safety Review",
        "Local Data Inventory",
        "Candidate Data Scope",
        "Excluded Data Scope",
        "Transfer Batch Plan",
        "Transfer Batch Results",
        "Archive Output",
        "Manifest Output",
        "R2 Object Keys",
        "Upload Verification Results",
        "Cleanup Eligibility Results",
        "Verified Local Deletion Results",
        "Files Deleted",
        "Files Preserved",
        "Safety Gate Results",
        "Secret Hygiene Review",
        "Git Ignore Review",
        "Storage Reduction Summary",
        "Remaining Local Data",
        "Remaining Blockers",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in sections:
        assert f"## {section}" in report

    required_strings = [
        "10K8ZF9",
        "Full R2 Transfer + Verified Local Storage Deletion",
        "verified local raw/generated data deletion",
        "R2 environment variables were checked without printing secrets",
        "R2 credentials come from environment variables only",
        "no credentials committed",
        "no secrets printed",
        "scripts/r2_archive_pipeline.py",
        "src/storage/r2_archive_adapter.py",
        "src/storage/archive_manifest.py",
        "compressed JSONL",
        "jsonl.gz",
        "archive manifest",
        "upload_status",
        "verification_status",
        "deletion_eligible",
        "deletion_performed",
        "deleted_source_file_count",
        "deleted_source_byte_count",
        "source code was preserved",
        "tests/fixtures were preserved",
        "manifests were preserved",
        "archives were preserved",
        "tracked files were preserved",
        "files outside approved input directory were preserved",
        "no broker execution",
        "no real trade execution",
        "no scraper actions",
        "no controlled data loader",
        "no backtest runner",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF9",
        "transfer_status: blocked_env_missing",
        "cleanup_status: not_attempted",
        "no local data deletion performed",
    ]
    assert_contains_all(report, required_strings)

    assert "transfer_status: uploaded_and_verified" not in report
    assert "transfer_status: partial_uploaded_and_verified" not in report
    assert "cleanup_status: verified_local_deletion_performed" not in report
    assert "cleanup_status: partial_verified_local_deletion_performed" not in report

    forbidden_strings = [
        "automatic local deletion enabled",
        "delete real /data now",
        "full local data deletion completed",
        "production live trading enabled",
        "broker orders enabled",
        "real trades enabled",
    ]
    for forbidden in forbidden_strings:
        assert forbidden not in report
        assert forbidden not in readme

    assert re.search(r"(?<!no )guaranteed profit", report) is None
    assert re.search(r"(?<!no )assured profit", report) is None
    assert re.search(r"(?<!no )guaranteed profit", readme) is None
    assert re.search(r"(?<!no )assured profit", readme) is None

    assert_contains_all(
        readme,
        [
            "10K8ZF7 R2 Archive Pipeline",
            "scripts/r2_archive_pipeline.py",
            "cleanup mode is explicit and gated",
            "no cleanup runs by default",
            "verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed",
        ],
    )

    assert_contains_all(
        gitignore,
        [
            ".r2.env",
            "r2.env",
            ".r2/",
            "r2_credentials.json",
            "cloudflare_credentials.json",
            "credentials.json",
            "token.json",
            "data/",
            "reports/",
            "archives/",
        ],
    )

    assert "--cleanup" in pipeline
    assert "--allow-delete-local-raw" in pipeline
    assert "validate_cleanup_gates" in pipeline
    assert "deletion_performed" in pipeline

    assert "os.environ" in adapter
    assert "repr=False" in adapter
    assert "R2_SECRET_ACCESS_KEY" in adapter
    assert "upload_archive" in adapter
    assert "verify_archive_object" in adapter

    secret_patterns = [
        r"AKIA[0-9A-Z]{16}",
        r"ASIA[0-9A-Z]{16}",
        r"your_real_secret",
        r"secret_access_key\s*=\s*['\"](?!<placeholder>|\\s*os\\.environ)",
    ]
    for text in (report, readme):
        for pattern in secret_patterns:
            assert re.search(pattern, text) is None

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))
