from __future__ import annotations

import gzip
import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
REPORT = ROOT / "PHASE10K8ZF7_R2_ARCHIVE_PIPELINE.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


class FakeR2Client:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []
        self.objects: dict[tuple[str, str], Path] = {}

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        path = Path(filename)
        self.uploads.append((filename, bucket, key))
        self.objects[(bucket, key)] = path

    def head_object(self, Bucket: str, Key: str) -> dict[str, object]:
        path = self.objects[(Bucket, Key)]
        return {"ContentLength": path.stat().st_size, "ETag": '"etag"', "Bucket": Bucket, "Key": Key}


class FakeR2ClientMismatch(FakeR2Client):
    def head_object(self, Bucket: str, Key: str) -> dict[str, object]:
        path = self.objects[(Bucket, Key)]
        return {"ContentLength": path.stat().st_size + 1, "ETag": '"etag"', "Bucket": Bucket, "Key": Key}


def make_input_tree(base: Path) -> dict[str, Path]:
    input_dir = base / "input"
    (input_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
    object_file = input_dir / "object.json"
    array_file = input_dir / "array.json"
    invalid_file = input_dir / "invalid.json"
    fixture_file = input_dir / "tests" / "fixtures" / "keep.json"
    object_file.write_text(json.dumps({"game_id": "g1", "price": 1}), encoding="utf-8")
    array_file.write_text(json.dumps([{"game_id": "g2"}, {"game_id": "g3"}]), encoding="utf-8")
    invalid_file.write_text('{"bad":', encoding="utf-8")
    fixture_file.write_text(json.dumps({"fixture": True}), encoding="utf-8")
    return {
        "input_dir": input_dir,
        "object_file": object_file,
        "array_file": array_file,
        "invalid_file": invalid_file,
        "fixture_file": fixture_file,
    }


def assert_required_strings(text: str, strings: list[str], label: str) -> None:
    for needle in strings:
        assert needle in text, f"Missing {label} string: {needle}"


def test_phase10k8zf7_r2_archive_pipeline(monkeypatch, tmp_path) -> None:
    readme_text = read_text(README)
    gitignore_text = read_text(GITIGNORE)
    report_text = read_text(REPORT)

    assert_required_strings(
        readme_text,
        [
            "10K8ZF7 R2 Archive Pipeline",
            "scripts/r2_archive_pipeline.py",
            "dry-run mode writes nothing",
            "bundle mode writes local jsonl.gz archive and manifest",
            "upload mode requires R2 environment variables",
            "verify mode checks the remote object before cleanup eligibility",
            "cleanup-plan mode marks eligibility only",
            "cleanup mode is explicit and gated",
            "no cleanup runs by default",
            "verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed",
            "the intended end state is R2 transfer verified and eligible local raw/generated data removed from local storage",
            "credentials must remain in local environment variables or ignored local config",
        ],
        "README",
    )

    assert_required_strings(
        report_text,
        [
            "10K8ZF7",
            "R2 Archive Pipeline",
            "Bundle + Upload + Verify + Delete Verified Local Raw Data",
            "scripts/r2_archive_pipeline.py",
            "src/storage/archive_manifest.py",
            "src/storage/r2_archive_adapter.py",
            "local-only dry-run",
            "bundle mode writes local jsonl.gz archive and manifest",
            "upload mode requires explicit --upload",
            "verify mode checks remote object metadata",
            "cleanup-plan mode marks eligibility only",
            "cleanup mode is explicit and gated",
            "no cleanup runs by default",
            "verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed",
            "the intended end state is R2 transfer verified and eligible local raw/generated data removed from local storage",
            "R2 credentials come from environment variables only",
            "do not commit R2 access keys",
            "do not commit secret keys",
            "do not commit tokens",
            "compressed JSONL",
            "jsonl.gz",
            "sha256",
            "archive manifest",
            "source_file_count",
            "source_byte_count",
            "archive_byte_count",
            "checksum",
            "object key",
            "market-data/{environment}/{source}/{market}/{yyyy}/{mm}/{dd}/{bundle_name}.{ext}",
            "market-data/local/theoddsapi/nba/2026/01/31/theoddsapi_nba_2026-01-31.jsonl.gz",
            "uploaded_at_utc is null before upload",
            "upload_status is not_uploaded before upload",
            "verification_status is not_verified before verification",
            "deletion_eligible is false before cleanup-plan",
            "deletion_performed is false by default",
            "deletion_completed_at_utc",
            "deleted_source_file_count",
            "deleted_source_byte_count",
            "skipped_invalid_json_count",
            "skipped_files",
            "boto3 import is isolated to src/storage/r2_archive_adapter.py",
            "no pandas import",
            "no pyarrow import",
            "no streamlit import",
            "no fastapi import",
            "no requests import",
            "no broker execution",
            "no real trade execution",
            "no live connectors",
            "no scraper actions",
            "no database writes without explicit storage phase",
            "no guaranteed profit language",
            "no assured profit language",
            "implementation reviewed in 10K8ZF7",
        ],
        "report",
    )

    assert_required_strings(
        gitignore_text,
        [
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
        ],
        ".gitignore",
    )

    cwd = tmp_path / "import-cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    old_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pipeline = fresh_import("scripts.r2_archive_pipeline")
        archive_manifest = fresh_import("src.storage.archive_manifest")
        adapter = fresh_import("src.storage.r2_archive_adapter")
    finally:
        sys.dont_write_bytecode = old_dont_write

    assert not any(cwd.iterdir()), "Importing the modules should not write files in the working directory."

    for name in [
        "sanitize_slug",
        "parse_trading_date",
        "utc_now_iso",
        "build_bundle_name",
        "build_archive_paths",
        "build_r2_object_key",
        "sha256_file",
        "build_manifest",
        "write_manifest",
        "read_manifest",
        "mark_uploaded",
        "mark_verified",
        "mark_cleanup_eligible",
        "mark_deletion_performed",
        "validate_cleanup_gates",
    ]:
        assert hasattr(archive_manifest, name), name

    for name in [
        "R2ArchiveConfig",
        "R2ArchiveUploadResult",
        "R2ArchiveVerificationResult",
        "load_r2_config_from_env",
        "create_r2_client",
        "upload_archive",
        "verify_archive_object",
    ]:
        assert hasattr(adapter, name), name

    for name in [
        "parse_args",
        "iter_candidate_json_files",
        "load_json_records",
        "write_archive",
        "run_dry_run",
        "run_bundle",
        "run_upload",
        "run_verify",
        "run_cleanup_plan",
        "run_cleanup",
        "main",
    ]:
        assert hasattr(pipeline, name), name

    pipeline_text = read_text(Path(pipeline.__file__))
    manifest_text = read_text(Path(archive_manifest.__file__))
    adapter_text = read_text(Path(adapter.__file__))
    for token in ["pandas", "pyarrow", "streamlit", "fastapi", "requests"]:
        assert token not in pipeline_text
        assert token not in manifest_text
    assert "boto3" not in pipeline_text
    assert "boto3" not in manifest_text
    assert "boto3" in adapter_text

    monkeypatch.setenv("R2_ACCOUNT_ID", "example-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "example-access-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "example-secret-key")
    monkeypatch.setenv("R2_BUCKET_NAME", "example-bucket")
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://example.invalid/r2")

    data = make_input_tree(tmp_path)
    input_dir = data["input_dir"]
    object_file = data["object_file"]
    array_file = data["array_file"]
    invalid_file = data["invalid_file"]
    fixture_file = data["fixture_file"]

    dry_run_output = tmp_path / "dry-run-output"
    assert pipeline.main(
        [
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(dry_run_output),
            "--environment",
            "local",
            "--source",
            "theoddsapi",
            "--market",
            "nba",
            "--trading-date",
            "2026-01-31",
            "--dry-run",
        ]
    ) == 0
    assert not dry_run_output.exists() or not any(dry_run_output.rglob("*"))
    assert object_file.exists()
    assert array_file.exists()
    assert invalid_file.exists()

    bundle_output = tmp_path / "bundle-output"
    assert pipeline.main(
        [
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(bundle_output),
            "--environment",
            "local",
            "--source",
            "theoddsapi",
            "--market",
            "nba",
            "--trading-date",
            "2026-01-31",
            "--bundle",
        ]
    ) == 0

    archive_files = list((bundle_output / "archives" / "local").rglob("*.jsonl.gz"))
    manifest_files = list((bundle_output / "reports" / "archive_manifests").glob("*.json"))
    assert len(archive_files) == 1
    assert len(manifest_files) == 1
    archive_path = archive_files[0]
    manifest_path = manifest_files[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    with gzip.open(archive_path, "rt", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]

    assert len(records) == 3
    for record in records:
        for field in ["_source_file", "_archive_id", "_trading_date", "_source", "_market", "_environment"]:
            assert field in record
        assert record["_source"] == "theoddsapi"
        assert record["_market"] == "nba"
        assert record["_environment"] == "local"

    assert manifest["source_file_count"] == 3
    assert manifest["skipped_invalid_json_count"] == 1
    assert any("invalid.json" in item for item in manifest["skipped_files"])
    assert manifest["upload_status"] == "not_uploaded"
    assert manifest["verification_status"] == "not_verified"
    assert manifest["deletion_eligible"] is False
    assert manifest["deletion_performed"] is False
    assert manifest["deletion_allowed_by_user"] is False
    assert manifest["uploaded_at_utc"] is None
    assert manifest["checksum_algorithm"] == "sha256"
    assert manifest["checksum"]
    assert manifest["archive_byte_count"] > 0
    assert manifest["r2_object_key"] == "market-data/local/theoddsapi/nba/2026/01/31/theoddsapi_nba_2026-01-31.jsonl.gz"
    assert object_file.exists()
    assert array_file.exists()
    assert invalid_file.exists()
    assert fixture_file.exists()

    manifest_only_output = tmp_path / "manifest-only-output"
    assert pipeline.main(
        [
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(manifest_only_output),
            "--environment",
            "local",
            "--source",
            "theoddsapi",
            "--market",
            "nba",
            "--trading-date",
            "2026-01-31",
            "--manifest-only",
        ]
    ) == 0
    manifest_only_archives = list((manifest_only_output / "archives").rglob("*.jsonl.gz"))
    manifest_only_manifests = list((manifest_only_output / "reports" / "archive_manifests").glob("*.json"))
    assert not manifest_only_archives
    assert len(manifest_only_manifests) == 1
    manifest_only = json.loads(manifest_only_manifests[0].read_text(encoding="utf-8"))
    assert manifest_only["upload_status"] == "not_uploaded"
    assert manifest_only["verification_status"] == "not_verified"
    assert manifest_only["deletion_eligible"] is False

    for key in [
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
        "R2_ENDPOINT_URL",
    ]:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        adapter.load_r2_config_from_env()
    assert "R2_ACCOUNT_ID" in str(excinfo.value)
    assert "example-secret-key" not in str(excinfo.value)

    monkeypatch.setenv("R2_ACCOUNT_ID", "account-123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "access-123")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret-123")
    monkeypatch.setenv("R2_BUCKET_NAME", "bucket-123")
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://example.invalid/r2")
    config = adapter.load_r2_config_from_env()
    assert "access-123" not in repr(config)
    assert "secret-123" not in repr(config)
    assert config.bucket_alias == "bucket-123"

    sample_archive = tmp_path / "sample.jsonl.gz"
    sample_archive.write_bytes(b"sample-archive-bytes")
    fake_upload_client = FakeR2Client()
    upload_result = adapter.upload_archive(
        fake_upload_client,
        config,
        sample_archive,
        "market-data/local/theoddsapi/nba/2026/01/31/sample.jsonl.gz",
    )
    assert fake_upload_client.uploads
    assert upload_result.bucket_alias == "bucket-123"
    assert upload_result.object_key.endswith("sample.jsonl.gz")
    assert upload_result.archive_byte_count == sample_archive.stat().st_size

    verify_ok = adapter.verify_archive_object(
        fake_upload_client,
        config,
        "market-data/local/theoddsapi/nba/2026/01/31/sample.jsonl.gz",
        expected_byte_count=sample_archive.stat().st_size,
    )
    assert verify_ok.verified is True
    assert verify_ok.content_length == sample_archive.stat().st_size

    mismatch_client = FakeR2ClientMismatch()
    mismatch_client.upload_file(str(sample_archive), config.bucket_name, "market-data/local/theoddsapi/nba/2026/01/31/sample.jsonl.gz")
    verify_bad = adapter.verify_archive_object(
        mismatch_client,
        config,
        "market-data/local/theoddsapi/nba/2026/01/31/sample.jsonl.gz",
        expected_byte_count=sample_archive.stat().st_size,
    )
    assert verify_bad.verified is False

    cleanup_data = make_input_tree(tmp_path / "cleanup-case")
    cleanup_input = cleanup_data["input_dir"]
    cleanup_object = cleanup_data["object_file"]
    cleanup_array = cleanup_data["array_file"]
    cleanup_invalid = cleanup_data["invalid_file"]
    cleanup_fixture = cleanup_data["fixture_file"]
    cleanup_output = tmp_path / "cleanup-output"
    fake_client = FakeR2Client()
    monkeypatch.setattr(pipeline, "create_r2_client", lambda config: fake_client)

    assert pipeline.main(
        [
            "--input-dir",
            str(cleanup_input),
            "--output-dir",
            str(cleanup_output),
            "--environment",
            "local",
            "--source",
            "theoddsapi",
            "--market",
            "nba",
            "--trading-date",
            "2026-01-31",
            "--bundle",
            "--upload",
            "--verify",
            "--cleanup-plan",
        ]
    ) == 0

    cleanup_manifest_path = next((cleanup_output / "reports" / "archive_manifests").glob("*.json"))
    cleanup_manifest = json.loads(cleanup_manifest_path.read_text(encoding="utf-8"))
    assert cleanup_manifest["deletion_eligible"] is True
    assert cleanup_manifest["deletion_performed"] is False
    assert cleanup_object.exists()
    assert cleanup_array.exists()
    assert cleanup_invalid.exists()
    assert cleanup_fixture.exists()

    assert (
        pipeline.main(
            [
                "--input-dir",
                str(cleanup_input),
                "--output-dir",
                str(cleanup_output),
                "--environment",
                "local",
                "--source",
                "theoddsapi",
                "--market",
                "nba",
                "--trading-date",
                "2026-01-31",
                "--cleanup",
                "--manifest-path",
                str(cleanup_manifest_path),
            ]
        )
        == 0
    )
    assert cleanup_object.exists()
    assert cleanup_array.exists()
    assert cleanup_invalid.exists()
    assert cleanup_fixture.exists()

    assert (
        pipeline.main(
            [
                "--input-dir",
                str(cleanup_input),
                "--output-dir",
                str(cleanup_output),
                "--environment",
                "local",
                "--source",
                "theoddsapi",
                "--market",
                "nba",
                "--trading-date",
                "2026-01-31",
                "--cleanup",
                "--allow-delete-local-raw",
                "--manifest-path",
                str(cleanup_manifest_path),
            ]
        )
        == 0
    )
    assert not cleanup_object.exists()
    assert not cleanup_array.exists()
    assert not cleanup_invalid.exists()
    assert cleanup_fixture.exists()
    assert cleanup_output.joinpath("archives", "local", "theoddsapi", "nba", "2026", "01", "31", "theoddsapi_nba_2026-01-31.jsonl.gz").exists()
    assert cleanup_manifest_path.exists()
    final_manifest = json.loads(cleanup_manifest_path.read_text(encoding="utf-8"))
    assert final_manifest["deletion_performed"] is True
    assert final_manifest["deletion_completed_at_utc"]
    assert final_manifest["deleted_source_file_count"] >= 3
    assert final_manifest["deleted_source_byte_count"] > 0

    for forbidden in [
        "active R2 upload enabled",
        "production R2 upload enabled",
        "live R2 connection enabled",
        "automatic local deletion enabled",
        "upload now",
        "delete local data now",
        "live-execution engine",
        "broker orders enabled",
        "real trades enabled",
    ]:
        assert forbidden not in readme_text
        assert forbidden not in report_text
