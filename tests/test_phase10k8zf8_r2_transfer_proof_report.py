from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF8_R2_TRANSFER_PROOF_AND_STORAGE_CLEARANCE_REPORT.md"
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
PIPELINE = ROOT / "scripts" / "r2_archive_pipeline.py"
ADAPTER = ROOT / "src" / "storage" / "r2_archive_adapter.py"
MANIFEST = ROOT / "src" / "storage" / "archive_manifest.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str]) -> None:
    for item in items:
        assert item in text, f"missing: {item}"


def test_phase10k8zf8_transfer_proof_report_and_safety_text() -> None:
    assert REPORT.exists()

    report = read_text(REPORT)
    readme = read_text(README)
    gitignore = read_text(GITIGNORE)
    pipeline = read_text(PIPELINE)
    adapter = read_text(ADAPTER)
    manifest = read_text(MANIFEST)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZF7",
        "Credential Safety Review",
        "R2 Environment Preflight",
        "Controlled Transfer Trial",
        "Trial Input",
        "Trial Archive Output",
        "Trial Manifest Output",
        "Trial R2 Object Key",
        "Trial Upload Result",
        "Trial Verification Result",
        "Trial Cleanup Eligibility Result",
        "Local Data Deletion Status",
        "Secret Hygiene Review",
        "Git Ignore Review",
        "Local Storage Clearance Plan",
        "Full Transfer Readiness",
        "Remaining Blockers",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    required_report_strings = [
        "10K8ZF8",
        "R2 Transfer Proof Review",
        "Local Storage Clearance Report",
        "controlled tiny R2 upload trial",
        "tmp/r2_transfer_trial/input/",
        "no real /data deletion in 10K8ZF8",
        "no full local data transfer in 10K8ZF8",
        "no credentials committed",
        "no secrets printed",
        ".r2.env is ignored by git",
        "R2 credentials come from environment variables only",
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
        "deletion_performed remains false in 10K8ZF8",
        "source sample files remain local",
        "full transfer is deferred to 10K8ZF9",
        "verified local deletion is deferred to 10K8ZF9",
        "source code must not be deleted",
        "tests/fixtures must not be deleted",
        "manifests must not be deleted",
        "archives must not be deleted in this phase",
        "tracked files must not be deleted",
        "files outside approved input directory must not be deleted",
        "no broker execution",
        "no real trade execution",
        "no scraper actions",
        "no controlled data loader",
        "no backtest runner",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF8",
    ]
    assert_contains_all(report, required_report_strings)

    assert "transfer_trial_status: skipped_env_missing" in report
    assert "real R2 upload was skipped because required environment variables were missing" in report

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

    assert re.search(r"(?<!no )guaranteed profit", report) is None
    assert re.search(r"(?<!no )assured profit", report) is None

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

    assert "--allow-delete-local-raw" in pipeline
    assert "--cleanup" in pipeline
    assert "R2_SECRET_ACCESS_KEY =" not in pipeline
    assert "R2_SECRET_ACCESS_KEY=" not in pipeline
    assert "os.environ" in adapter
    assert "repr=False" in adapter
    assert "boto3" not in manifest

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
