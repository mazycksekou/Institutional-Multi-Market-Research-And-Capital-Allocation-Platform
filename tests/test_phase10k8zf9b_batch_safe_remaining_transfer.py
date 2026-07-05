from __future__ import annotations

import gzip
import importlib
import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REPORT = ROOT / "PHASE10K8ZF9B_BATCH_SAFE_R2_REMAINING_TRANSFER_REPORT.md"
PHASE10K8ZF7_REPORT = ROOT / "PHASE10K8ZF7_R2_ARCHIVE_PIPELINE.md"
PHASE10K8ZF8_REPORT = ROOT / "PHASE10K8ZF8_R2_TRANSFER_PROOF_AND_STORAGE_CLEARANCE_REPORT.md"
PHASE10K8ZF9_REPORT = ROOT / "PHASE10K8ZF9_FULL_R2_TRANSFER_AND_VERIFIED_LOCAL_DELETION_REPORT.md"
PIPELINE = ROOT / "scripts" / "r2_archive_pipeline.py"
MANIFEST = ROOT / "src" / "storage" / "archive_manifest.py"
ADAPTER = ROOT / "src" / "storage" / "r2_archive_adapter.py"


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
        self.uploads.append((filename, bucket, key))
        self.objects[(bucket, key)] = Path(filename)

    def head_object(self, Bucket: str, Key: str) -> dict[str, object]:
        path = self.objects[(Bucket, Key)]
        return {"ContentLength": path.stat().st_size, "ETag": '"etag"', "Bucket": Bucket, "Key": Key}


def assert_required_strings(text: str, strings: list[str], label: str) -> None:
    for needle in strings:
        assert needle in text, f"Missing {label} string: {needle}"


def make_batch_tree(base: Path) -> dict[str, Path]:
    input_dir = base / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
    (input_dir / "notes").mkdir(parents=True, exist_ok=True)

    json_a = input_dir / "alpha.json"
    json_b = input_dir / "beta.json"
    json_a.write_text(json.dumps({"symbol": "A", "value": 1}), encoding="utf-8")
    json_b.write_text(json.dumps({"symbol": "B", "value": 2}), encoding="utf-8")
    fixture = input_dir / "tests" / "fixtures" / "keep.json"
    fixture.write_text(json.dumps({"fixture": True}), encoding="utf-8")

    return {"input_dir": input_dir, "json_a": json_a, "json_b": json_b, "fixture": fixture}


def make_jsonl_tree(base: Path) -> dict[str, Path]:
    input_dir = base / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)

    clean_jsonl = input_dir / "clean.jsonl"
    dirty_jsonl = input_dir / "dirty.jsonl"
    clean_jsonl.write_text('{"row": 1}\n\n{"row": 2}\n', encoding="utf-8")
    dirty_jsonl.write_text('{"row": 3}\n\nnot json\n{"row": 4}\n', encoding="utf-8")
    fixture = input_dir / "tests" / "fixtures" / "keep.json"
    fixture.write_text(json.dumps({"fixture": True}), encoding="utf-8")
    markdown = input_dir / "notes.md"
    markdown.write_text("keep me", encoding="utf-8")
    database = input_dir / "state.db"
    database.write_bytes(b"db-bytes")
    outside = base / "outside.json"
    outside.write_text(json.dumps({"outside": True}), encoding="utf-8")

    return {
        "input_dir": input_dir,
        "clean_jsonl": clean_jsonl,
        "dirty_jsonl": dirty_jsonl,
        "fixture": fixture,
        "markdown": markdown,
        "database": database,
        "outside": outside,
    }


def make_csv_tree(base: Path) -> dict[str, Path]:
    input_dir = base / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)

    header_csv = input_dir / "records.csv"
    header_csv.write_text("team,price,rank\nHome,12.5,1\nAway,8.0,2\n", encoding="utf-8")
    no_header_csv = input_dir / "no_header.csv"
    no_header_csv.write_text("1,2,3\n4,5,6\n", encoding="utf-8")
    fixture = input_dir / "tests" / "fixtures" / "keep.json"
    fixture.write_text(json.dumps({"fixture": True}), encoding="utf-8")
    markdown = input_dir / "notes.md"
    markdown.write_text("keep me", encoding="utf-8")
    database = input_dir / "state.db"
    database.write_bytes(b"db-bytes")
    outside = base / "outside.json"
    outside.write_text(json.dumps({"outside": True}), encoding="utf-8")

    return {
        "input_dir": input_dir,
        "header_csv": header_csv,
        "no_header_csv": no_header_csv,
        "fixture": fixture,
        "markdown": markdown,
        "database": database,
        "outside": outside,
    }


def latest_manifest_path(output_dir: Path) -> Path:
    manifests = sorted((output_dir / "reports" / "archive_manifests").glob("*.json"), key=lambda path: path.stat().st_mtime)
    assert manifests, "expected manifest output"
    return manifests[-1]


def read_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_archive_lines(path: Path) -> list[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_batch_safe_paths_and_manifest_fields(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    old_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pipeline = fresh_import("scripts.r2_archive_pipeline")
    finally:
        sys.dont_write_bytecode = old_dont_write

    tree = make_batch_tree(tmp_path)
    output_dir = tmp_path / "output"
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
            "*.json",
            "--batch-id",
            "batch-000001",
            "--bundle",
        ]
    ) == 0
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
            "*.json",
            "--batch-id",
            "batch-000002",
            "--bundle",
        ]
    ) == 0

    manifests = sorted((output_dir / "reports" / "archive_manifests").glob("*.json"))
    assert len(manifests) == 2
    by_batch_id = {read_manifest(path)["batch_id"]: read_manifest(path) for path in manifests}
    manifest_one = by_batch_id["batch-000001"]
    manifest_two = by_batch_id["batch-000002"]

    assert manifest_one["batch_id"] == "batch-000001"
    assert manifest_two["batch_id"] == "batch-000002"
    assert manifest_one["batch_unique"] is True
    assert manifest_two["batch_unique"] is True
    assert manifest_one["batch_object_key"]
    assert manifest_one["batch_archive_path"]
    assert manifest_two["batch_object_key"]
    assert manifest_two["batch_archive_path"]
    assert manifest_one["batch_object_key"] != manifest_two["batch_object_key"]
    assert manifest_one["batch_archive_path"] != manifest_two["batch_archive_path"]
    assert manifest_one["local_archive_path"] == manifest_one["batch_archive_path"]
    assert manifest_two["local_archive_path"] == manifest_two["batch_archive_path"]
    assert Path(manifest_one["batch_archive_path"]).exists()
    assert Path(manifest_two["batch_archive_path"]).exists()
    assert Path(manifest_one["batch_archive_path"]).name.endswith("batch-000001.jsonl.gz")
    assert Path(manifest_two["batch_archive_path"]).name.endswith("batch-000002.jsonl.gz")
    assert manifest_one["batch_object_key"].endswith("batch-000001.jsonl.gz")
    assert manifest_two["batch_object_key"].endswith("batch-000002.jsonl.gz")


def test_jsonl_ingestion_and_cleanup_safety(monkeypatch, tmp_path) -> None:
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

    tree = make_jsonl_tree(tmp_path)
    output_dir = tmp_path / "output"
    fake_client = FakeR2Client()
    monkeypatch.setattr(pipeline, "create_r2_client", lambda config: fake_client)

    load_result = pipeline.load_json_records(
        input_dir=tree["input_dir"],
        output_dir=output_dir,
        environment="local",
        source="local-data",
        market="raw-generated",
        trading_date="2026-06-19",
        archive_id="archive-jsonl",
        include_pattern="*.jsonl",
        batch_id="jsonl-batch",
    )
    assert any(item.endswith("clean.jsonl") for item in load_result.source_files)
    assert not any(item.endswith("dirty.jsonl") for item in load_result.source_files)
    assert load_result.skipped_invalid_json_count == 1
    assert any("dirty.jsonl:L3" in item for item in load_result.skipped_files)

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
            "*.jsonl",
            "--batch-id",
            "jsonl-batch",
            "--bundle",
            "--upload",
            "--verify",
        ]
    ) == 0
    manifest_path = latest_manifest_path(output_dir)
    manifest = read_manifest(manifest_path)
    archive_path = Path(manifest["batch_archive_path"])
    assert archive_path.exists()
    records = read_archive_lines(archive_path)
    assert len(records) == 4
    for record in records:
        assert record["_input_format"] == "jsonl"
        assert record["_batch_id"] == "jsonl-batch"
        assert "_source_line" in record
        assert record["_source_file"].endswith(("clean.jsonl", "dirty.jsonl"))

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
    assert manifest_after_no_allow["deletion_eligible"] is False
    assert tree["clean_jsonl"].exists()
    assert tree["dirty_jsonl"].exists()
    assert tree["fixture"].exists()
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
            "--cleanup-plan",
        ]
    ) == 0
    manifest_after_plan = read_manifest(manifest_path)
    assert manifest_after_plan["deletion_eligible"] is True

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
    manifest_after_still_no_allow = read_manifest(manifest_path)
    assert manifest_after_still_no_allow["deletion_performed"] is False

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
    assert not tree["clean_jsonl"].exists()
    assert tree["dirty_jsonl"].exists()
    assert tree["fixture"].exists()
    assert tree["markdown"].exists()
    assert tree["database"].exists()
    assert tree["outside"].exists()
    assert archive_path.exists()
    assert manifest_path.exists()


def test_csv_ingestion_and_preserved_strings(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    old_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pipeline = fresh_import("scripts.r2_archive_pipeline")
    finally:
        sys.dont_write_bytecode = old_dont_write

    tree = make_csv_tree(tmp_path)
    output_dir = tmp_path / "output"

    load_result = pipeline.load_json_records(
        input_dir=tree["input_dir"],
        output_dir=output_dir,
        environment="local",
        source="local-data",
        market="raw-generated",
        trading_date="2026-06-19",
        archive_id="archive-csv",
        include_pattern="*.csv",
        batch_id="csv-batch",
    )
    assert len(load_result.records) == 2
    assert load_result.source_files == ["records.csv"]
    assert load_result.skipped_invalid_json_count == 0
    assert any(item.endswith("no_header.csv") for item in load_result.skipped_files)

    record = load_result.records[0]
    assert record["_input_format"] == "csv"
    assert record["_batch_id"] == "csv-batch"
    assert record["_source_row"] == 2
    assert record["team"] == "Home"
    assert record["price"] == "12.5"
    assert record["rank"] == "1"

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
            "*.csv",
            "--batch-id",
            "csv-batch",
            "--bundle",
        ]
    ) == 0
    manifest_path = latest_manifest_path(output_dir)
    manifest = read_manifest(manifest_path)
    archive_path = Path(manifest["batch_archive_path"])
    assert archive_path.exists()
    records = read_archive_lines(archive_path)
    assert len(records) == 2
    for item in records:
        assert item["_input_format"] == "csv"
        assert item["_batch_id"] == "csv-batch"
        assert "_source_row" in item
        assert isinstance(item["team"], str)
        assert isinstance(item["price"], str)
        assert isinstance(item["rank"], str)
    assert manifest["skipped_files"] == ["no_header.csv"]


def test_report_and_source_hygiene(monkeypatch, tmp_path) -> None:
    readme_text = read_text(README)
    report_text = read_text(REPORT)
    phase7_text = read_text(PHASE10K8ZF7_REPORT)
    phase8_text = read_text(PHASE10K8ZF8_REPORT)
    phase9_text = read_text(PHASE10K8ZF9_REPORT)
    pipeline_text = read_text(PIPELINE)
    manifest_text = read_text(MANIFEST)
    adapter_text = read_text(ADAPTER)

    assert REPORT.exists()
    assert_required_strings(
        report_text,
        [
            "10K8ZF9B",
            "Batch-Safe R2 Archive Naming",
            "CSV/JSONL Remaining Transfer",
            "batch_id",
            "batch_unique: true",
            "batch-specific archive path",
            "batch-specific R2 object key",
            "no archive overwrite",
            "no R2 object overwrite",
            "JSONL ingestion",
            "CSV ingestion",
            "standard library csv",
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
            "implementation reviewed in 10K8ZF9B",
        ],
        "report",
    )
    assert "transfer_status: partial_remaining_uploaded_and_verified" in report_text
    assert "cleanup_status: partial_remaining_verified_local_deletion_performed" in report_text
    assert "remaining_local_data_requires_review" in report_text

    assert "automatic local deletion enabled" not in readme_text
    assert "delete real /data now" not in readme_text
    assert "production live trading enabled" not in readme_text
    assert "broker orders enabled" not in readme_text
    assert "real trades enabled" not in readme_text
    assert not re.search(r"(?<!no )guaranteed profit", readme_text.lower())
    assert not re.search(r"(?<!no )assured profit", readme_text.lower())

    for text in [readme_text, report_text]:
        assert "your_real_secret" not in text
        assert not re.search(r"\bAKIA[0-9A-Z]{16}\b", text)
        assert not re.search(r"\bASIA[0-9A-Z]{16}\b", text)

    assert "--cleanup" in pipeline_text
    assert "--allow-delete-local-raw" in pipeline_text
    assert "validate_cleanup_gates" in pipeline_text
    assert "deletion_performed" in pipeline_text
    assert "os.environ" in adapter_text
    assert "repr=False" in adapter_text
    assert "R2_SECRET_ACCESS_KEY" in adapter_text
    assert "upload_archive" in adapter_text
    assert "verify_archive_object" in adapter_text

    assert "10K8ZF7" in phase7_text
    assert "10K8ZF8" in phase8_text
    assert "10K8ZF9" in phase9_text

    assert not list(ROOT.glob("pages/*.py"))
    assert not list(ROOT.glob("app/pages/*.py"))
    assert not list(ROOT.glob("frontend/*.py"))
    assert not list(ROOT.glob("frontend/pages/*.py"))
