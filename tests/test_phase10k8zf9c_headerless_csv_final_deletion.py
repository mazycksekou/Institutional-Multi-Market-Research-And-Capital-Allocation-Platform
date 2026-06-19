from __future__ import annotations

import importlib
import importlib.util
import json
import inspect
import re
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF9C_HEADERLESS_CSV_FINAL_DELETION_REPORT.md"


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


def assert_required_strings(text: str, strings: list[str], label: str) -> None:
    for needle in strings:
        assert needle in text, f"Missing {label} string: {needle}"


def make_headerless_csv_tree(base: Path) -> dict[str, Path]:
    input_dir = base / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)

    target_csv = input_dir / "E0_2024_2025.csv"
    target_csv.write_text("1,2\n3,4\n", encoding="utf-8")
    other_csv = input_dir / "other.csv"
    other_csv.write_text("column_a,column_b\nx,y\n", encoding="utf-8")
    markdown = input_dir / "notes.md"
    markdown.write_text("keep me", encoding="utf-8")
    database = input_dir / "state.db"
    database.write_bytes(b"db-bytes")
    fixture = input_dir / "tests" / "fixtures" / "keep.json"
    fixture.write_text(json.dumps({"fixture": True}), encoding="utf-8")
    outside = base / "outside.json"
    outside.write_text(json.dumps({"outside": True}), encoding="utf-8")

    return {
        "input_dir": input_dir,
        "target_csv": target_csv,
        "other_csv": other_csv,
        "markdown": markdown,
        "database": database,
        "fixture": fixture,
        "outside": outside,
    }


def read_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_manifest_path(output_dir: Path) -> Path:
    manifests = sorted((output_dir / "reports" / "archive_manifests").glob("*.json"), key=lambda path: path.stat().st_mtime)
    assert manifests, "expected manifest output"
    return manifests[-1]


def run_existing_gate(module_filename: str, function_name: str) -> None:
    module_path = ROOT / "tests" / module_filename
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    gate = getattr(module, function_name)
    params = list(inspect.signature(gate).parameters)
    if not params:
        gate()
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        monkeypatch = pytest.MonkeyPatch()
        try:
            gate(monkeypatch, tmp_path)
        finally:
            monkeypatch.undo()


def test_headerless_csv_modes_and_cleanup_safety(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("R2_ACCOUNT_ID", "account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "access")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "bucket")
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://example.invalid/r2")

    old_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pipeline = fresh_import("scripts.r2_archive_pipeline")
    finally:
        sys.dont_write_bytecode = old_dont_write

    tree = make_headerless_csv_tree(tmp_path)
    output_dir = tmp_path / "output"

    strict_result = pipeline.load_json_records(
        input_dir=tree["input_dir"],
        output_dir=output_dir,
        environment="local",
        source="local-data",
        market="raw-generated",
        trading_date="2026-06-19",
        archive_id="archive-strict",
        include_pattern="E0_2024_2025.csv",
        batch_id="csv-headerless-final-001",
        csv_header_mode="strict",
    )
    assert strict_result.records == []
    assert strict_result.source_files == []
    assert strict_result.source_byte_count == 0
    assert any(item.endswith("E0_2024_2025.csv") for item in strict_result.skipped_files)

    generated_result = pipeline.load_json_records(
        input_dir=tree["input_dir"],
        output_dir=output_dir,
        environment="local",
        source="local-data",
        market="raw-generated",
        trading_date="2026-06-19",
        archive_id="archive-generated",
        include_pattern="E0_2024_2025.csv",
        batch_id="csv-headerless-final-001",
        csv_header_mode="generated",
    )
    assert generated_result.source_files == ["E0_2024_2025.csv"]
    assert len(generated_result.records) == 2
    first_record = generated_result.records[0]
    assert first_record["_csv_header_mode"] == "generated"
    assert first_record["_generated_columns"] is True
    assert first_record["_input_format"] == "csv"
    assert first_record["_source_row"] == 1
    assert first_record["column_1"] == "1"
    assert first_record["column_2"] == "2"
    assert all(isinstance(value, str) for key, value in first_record.items() if key.startswith("column_"))
    assert generated_result.records[1]["column_1"] == "3"
    assert generated_result.records[1]["column_2"] == "4"

    fake_client = FakeR2Client()
    monkeypatch.setattr(pipeline, "create_r2_client", lambda config: fake_client)

    assert pipeline.main(
        [
            "--input-dir",
            str(tree["input_dir"]),
            "--output-dir",
            str(output_dir),
            "--environment",
            "local",
            "--source",
            "local-data",
            "--market",
            "raw-generated",
            "--trading-date",
            "2026-06-19",
            "--include-pattern",
            "E0_2024_2025.csv",
            "--batch-id",
            "csv-headerless-final-001",
            "--csv-header-mode",
            "generated",
            "--bundle",
            "--upload",
            "--verify",
            "--cleanup-plan",
        ]
    ) == 0

    manifest_path = latest_manifest_path(output_dir)
    manifest = read_manifest(manifest_path)
    archive_path = Path(manifest["batch_archive_path"])

    assert manifest["upload_status"] == "uploaded"
    assert manifest["verification_status"] == "verified"
    assert manifest["deletion_eligible"] is True
    assert manifest["deletion_performed"] is False
    assert manifest["source_file_count"] == 1
    assert manifest["batch_unique"] is True
    assert manifest["batch_id"] == "csv-headerless-final-001"
    assert manifest["batch_object_key"]
    assert manifest["batch_archive_path"]
    assert archive_path.exists()
    assert manifest["skipped_files"] == []

    assert pipeline.main(
        [
            "--input-dir",
            str(tree["input_dir"]),
            "--output-dir",
            str(output_dir),
            "--environment",
            "local",
            "--source",
            "local-data",
            "--market",
            "raw-generated",
            "--trading-date",
            "2026-06-19",
            "--manifest-path",
            str(manifest_path),
            "--cleanup",
        ]
    ) == 0
    manifest_after_no_allow = read_manifest(manifest_path)
    assert manifest_after_no_allow["deletion_performed"] is False
    assert tree["target_csv"].exists()
    assert tree["other_csv"].exists()
    assert tree["markdown"].exists()
    assert tree["database"].exists()
    assert tree["outside"].exists()
    assert archive_path.exists()
    assert manifest_path.exists()

    assert pipeline.main(
        [
            "--input-dir",
            str(tree["input_dir"]),
            "--output-dir",
            str(output_dir),
            "--environment",
            "local",
            "--source",
            "local-data",
            "--market",
            "raw-generated",
            "--trading-date",
            "2026-06-19",
            "--manifest-path",
            str(manifest_path),
            "--cleanup",
            "--allow-delete-local-raw",
        ]
    ) == 0
    manifest_after_cleanup = read_manifest(manifest_path)
    assert manifest_after_cleanup["deletion_performed"] is True
    assert manifest_after_cleanup["deleted_source_file_count"] == 1
    assert manifest_after_cleanup["deleted_source_byte_count"] > 0
    assert not tree["target_csv"].exists()
    assert tree["other_csv"].exists()
    assert tree["markdown"].exists()
    assert tree["database"].exists()
    assert tree["outside"].exists()
    assert archive_path.exists()
    assert manifest_path.exists()


def test_headerless_csv_report_and_existing_gates() -> None:
    assert REPORT.exists()
    report = read_text(REPORT)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZF9B",
        "Remaining CSV Review",
        "Headerless CSV Policy",
        "Generated Header Mode",
        "R2 Environment Preflight",
        "Transfer Batch Results",
        "Upload Verification Results",
        "Verified Local Deletion Results",
        "Files Deleted",
        "Files Preserved",
        "Remaining Local Data",
        "Safety Gate Results",
        "Secret Hygiene Review",
        "Git Ignore Review",
        "Tests Run",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    assert_required_strings(
        report,
        [
            "10K8ZF9C",
            "Headerless CSV Raw Archive",
            "Verified Final Local Deletion",
            "csv-header-mode generated",
            "generated column names",
            "column_1",
            "_csv_header_mode: generated",
            "_generated_columns: true",
            "batch_id",
            "csv-headerless-final-001",
            "batch_unique: true",
            "batch-specific archive path",
            "batch-specific R2 object key",
            "no archive overwrite",
            "no R2 object overwrite",
            "compressed JSONL",
            "jsonl.gz",
            "archive manifest",
            "upload_status",
            "verification_status",
            "deletion_eligible",
            "deletion_performed",
            "deleted_source_file_count",
            "deleted_source_byte_count",
            "E0_2024_2025.csv",
            "source code was preserved",
            "tests/fixtures were preserved",
            "manifests were preserved",
            "archives were preserved",
            "tracked files were preserved",
            "files outside approved input directory were preserved",
            "markdown files were preserved",
            "DB files were preserved",
            "no credentials committed",
            "no secrets printed",
            "R2 credentials come from environment variables only",
            "no broker execution",
            "no real trade execution",
            "no scraper actions",
            "no controlled data loader",
            "no backtest runner",
            "no AI optimizer implementation",
            "no guaranteed profit language",
            "no assured profit language",
            "implementation reviewed in 10K8ZF9C",
            "transfer_status: blocked",
            "cleanup_status: not_attempted",
        ],
        "report",
    )

    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None

    run_existing_gate("test_phase10k8zf7_r2_archive_pipeline.py", "test_phase10k8zf7_r2_archive_pipeline")
    run_existing_gate("test_phase10k8zf8_r2_transfer_proof_report.py", "test_phase10k8zf8_transfer_proof_report_and_safety_text")
    run_existing_gate("test_phase10k8zf9_full_r2_transfer_report.py", "test_phase10k8zf9_full_transfer_report_and_safety_text")
    run_existing_gate("test_phase10k8zf9b_batch_safe_remaining_transfer.py", "test_batch_safe_paths_and_manifest_fields")
    run_existing_gate("test_phase10k8zf9b_batch_safe_remaining_transfer.py", "test_jsonl_ingestion_and_cleanup_safety")
    run_existing_gate("test_phase10k8zf9b_batch_safe_remaining_transfer.py", "test_csv_ingestion_and_preserved_strings")
    run_existing_gate("test_phase10k8zf9b_batch_safe_remaining_transfer.py", "test_report_and_source_hygiene")
