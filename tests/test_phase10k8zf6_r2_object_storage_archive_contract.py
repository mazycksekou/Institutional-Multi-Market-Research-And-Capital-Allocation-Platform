from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
REPORT = ROOT / "PHASE10K8ZF6_R2_OBJECT_STORAGE_ARCHIVE_CONTRACT.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, strings: list[str], label: str) -> None:
    for needle in strings:
        assert needle in text, f"Missing {label} string: {needle}"


def test_phase10k8zf6_r2_object_storage_archive_contract() -> None:
    assert README.is_file(), "Expected README.md to exist."
    assert GITIGNORE.is_file(), "Expected .gitignore to exist."
    assert REPORT.is_file(), "Expected the 10K8ZF6 report to exist."

    readme_text = read_text(README)
    gitignore_text = read_text(GITIGNORE)
    report_text = read_text(REPORT)
    combined_text = "\n".join([readme_text, report_text])

    required_readme_strings = [
        "R2 Object Storage Archive Policy",
        "R2 object storage is the archive layer for large local market data bundles.",
        "R2 is not the live application database.",
        "Do not upload thousands of tiny JSON files.",
        "Aggregate raw JSON into daily archive bundles before upload.",
        "Use one object per date/source/market bundle.",
        "Keep a manifest for every archive bundle.",
        "Verify upload before local deletion.",
        "Local deletion is off by default.",
        "Credentials must come from environment variables or ignored local config only.",
        "Do not commit R2 access keys",
        "Do not paste real R2 credentials into source code, README examples, tests, or committed config.",
        "Core math, risk, signals, metrics, backtester, and dashboard code must not import R2 clients directly.",
        "Future R2 adapter code belongs behind src/storage/ or a storage-provider boundary.",
        "End-of-day archive scripts belong in scripts/.",
        "Only tiny deterministic fixtures belong in tests/fixtures/.",
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
        "R2_ENDPOINT_URL",
        "The real R2 key is first used in 10K8ZF8/10K8ZF9, not 10K8ZF6.",
        "10K8ZF6 performs no upload.",
    ]
    assert_contains_all(readme_text, required_readme_strings, "README")

    required_gitignore_strings = [
        "data/",
        "reports/",
        ".r2.env",
        "r2.env",
        ".r2/",
        "r2_credentials.json",
        "cloudflare_credentials.json",
        "credentials.json",
        "token.json",
        "*.pem",
        "*.key",
        "*.parquet",
        "*.jsonl",
        "*.csv.gz",
        "*.json.gz",
        "*.tar.gz",
    ]
    assert_contains_all(gitignore_text, required_gitignore_strings, ".gitignore")

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Product Decision",
        "R2 Object Storage Role",
        "Not a Database Boundary",
        "Local Data Context",
        "Archive Eligibility Rules",
        "Non-Archive / Must-Keep Rules",
        "Deterministic Fixture Policy",
        "Daily Archive Bundle Format",
        "Object Key Naming Convention",
        "Archive Manifest Contract",
        "Upload Verification Contract",
        "Local Deletion Eligibility Contract",
        "R2 Credential Timing",
        "Required R2 Environment Variables",
        "Credential and Secret Policy",
        "Code Ownership Boundary",
        "Future src/storage Boundary",
        "Future scripts Boundary",
        "Forbidden Imports Boundary",
        "End-of-Day Archive Flow",
        "Failure and Retry Policy",
        "Audit Log / Manifest Policy",
        "Pre-Backtest Cleanup Impact",
        "Next Phase Recommendation",
    ]
    assert_contains_all(report_text, required_sections, "report section")

    required_report_strings = [
        "10K8ZF6",
        "Local Data Object Storage Archive Contract",
        "R2 Object Storage Archive Contract",
        "R2 object storage is the archive layer",
        "R2 is not the live application database",
        "do not upload thousands of tiny JSON files",
        "aggregate raw JSON into daily archive bundles",
        "one object per date/source/market bundle",
        "manifest required before upload",
        "upload verification required before local deletion",
        "local deletion is off by default",
        "credentials must come from environment variables or ignored local config only",
        "do not commit R2 access keys",
        "do not commit secret keys",
        "do not commit tokens",
        "do not commit credential files",
        "do not paste real R2 credentials into source code",
        "10K8ZF6 performs no upload",
        "R2 credentials are first used by implementation phases 10K8ZF8 and 10K8ZF9",
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
        "R2_ENDPOINT_URL",
        "core math must not import R2 clients directly",
        "risk logic must not import R2 clients directly",
        "signals must not import R2 clients directly",
        "metrics must not import R2 clients directly",
        "backtester must not import R2 clients directly",
        "dashboard must not import R2 clients directly",
        "future R2 adapter belongs behind src/storage/ or a storage-provider boundary",
        "end-of-day archive scripts belong in scripts/",
        "only tiny deterministic fixtures belong in tests/fixtures/",
        "data/",
        "reports/",
        "archive manifest",
        "checksum",
        "object key",
        "object size",
        "upload timestamp",
        "source file count",
        "source byte count",
        "dry-run mode required for implementation phase",
        "no real upload in 10K8ZF6",
        "no local deletion in 10K8ZF6",
        "pre-backtest cleanup must finish before controlled data loader or backtest runner",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls without explicit provider phase",
        "no database writes without explicit storage phase",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF6",
    ]
    assert_contains_all(report_text, required_report_strings, "report")

    manifest_fields = [
        "archive_id",
        "environment",
        "source",
        "market",
        "trading_date",
        "archive_format",
        "local_archive_path",
        "r2_bucket_alias",
        "r2_object_key",
        "source_file_count",
        "source_byte_count",
        "archive_byte_count",
        "checksum_algorithm",
        "checksum",
        "created_at_utc",
        "uploaded_at_utc",
        "upload_status",
        "verification_status",
        "deletion_eligible",
        "deletion_performed",
        "notes",
    ]
    assert_contains_all(report_text, manifest_fields, "manifest field")

    deletion_gates = [
        "source file is ignored by git",
        "source file is listed in manifest",
        "archive was created successfully",
        "upload completed successfully",
        "remote object verification passed",
        "checksum or size verification exists",
        "source file is not referenced by tests",
        "source file is not under tests/fixtures/",
        "source file is not required for deterministic test runs",
        "user explicitly enables cleanup mode",
    ]
    assert_contains_all(report_text, deletion_gates, "deletion gate")

    object_key = "market-data/{environment}/{source}/{market}/{yyyy}/{mm}/{dd}/{bundle_name}.{ext}"
    example_object_key = "market-data/local/theoddsapi/nba/2026/01/31/theoddsapi_nba_2026-01-31.jsonl.gz"
    assert object_key in report_text
    assert example_object_key in report_text

    forbidden_claims = [
        "active R2 upload enabled",
        "production R2 upload enabled",
        "live R2 connection enabled",
        "automatic local deletion enabled",
        "upload now",
        "delete local data now",
        "live-execution engine",
        "broker orders enabled",
        "real trades enabled",
    ]
    for needle in forbidden_claims:
        assert needle not in combined_text, f"Unexpected forbidden claim: {needle}"

    secret_like_patterns = [
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\bASIA[0-9A-Z]{16}\b",
        r"\b[0-9a-f]{40}\b",
    ]
    for pattern in secret_like_patterns:
        matches = re.findall(pattern, combined_text, flags=re.IGNORECASE)
        if pattern == r"\b[0-9a-f]{40}\b":
            assert not any(token not in {"72181ac8f6304988174deaba011777e31b8b22e0"} for token in matches), (
                "Unexpected secret-like hex token in README or report."
            )
        else:
            assert not matches, f"Unexpected secret-like token pattern: {pattern}"

    implementation_paths = [
        "src/storage/r2",
        "src/providers/r2",
        "scripts/r2",
        "scripts/archive",
    ]
    for fragment in implementation_paths:
        assert not list(ROOT.rglob(f"{fragment}*")), f"Unexpected implementation files matching {fragment}*"

    frontend_globs = [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]
    for pattern in frontend_globs:
        assert not list(ROOT.glob(pattern)), f"Unexpected frontend page files matching {pattern}"
