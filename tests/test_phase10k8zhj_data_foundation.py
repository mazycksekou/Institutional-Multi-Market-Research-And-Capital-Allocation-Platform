from __future__ import annotations

import importlib
import inspect
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_NAMES = [
    "src.data",
    "src.data.contracts",
    "src.data.metadata",
    "src.data.source_registry",
    "src.data.validation",
    "src.data.local_loader",
]
FORBIDDEN_IMPORTS = [
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_data_foundation_docs_exist_and_state_local_only() -> None:
    docs = [
        ROOT / "PHASE10K8ZHJ_DATA_FOUNDATION.md",
        ROOT / "DATA_FOUNDATION_OWNERSHIP_MAP_AFTER_10K8ZHJ.md",
        ROOT / "DATA_SOURCE_REGISTRY_MAP_AFTER_10K8ZHJ.md",
        ROOT / "DATA_VALIDATION_REPORT_AFTER_10K8ZHJ.md",
    ]
    combined = "\n".join(_read(path) for path in docs)
    for fragment in [
        "PHASE 10K8ZHJ",
        "src.data",
        "local-only",
        "no network calls",
        "no credential reads",
        "local loader",
        "source registry",
        "validation helpers",
        "No live data activation",
    ]:
        assert fragment.lower() in combined.lower()


def test_data_modules_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    modules = [importlib.reload(importlib.import_module(name)) for name in MODULE_NAMES]
    data = modules[0]

    assert hasattr(data, "DataSourceDescriptor")
    assert hasattr(data, "DatasetMetadata")
    assert hasattr(data, "load_local_dataset")
    assert hasattr(data, "create_dataset_metadata")
    assert hasattr(data, "register_local_source")
    assert hasattr(data, "validate_dataset_metadata")


def test_data_registry_metadata_and_loader_behaviour(tmp_path: Path) -> None:
    from src.data import (
        DataSourceDescriptor,
        create_dataset_metadata,
        load_local_dataset,
        list_local_sources,
        register_local_source,
        reset_local_source_registry,
        validate_dataset_metadata,
        validate_local_source_descriptor,
    )

    reset_local_source_registry()
    descriptor = DataSourceDescriptor(
        name="local-paper-ledger",
        source_type="local",
        description="Local test dataset",
        tags=("paper", "ledger"),
    )
    registered = register_local_source(descriptor)
    assert registered is descriptor
    listed = list_local_sources()
    assert listed == (descriptor,)

    metadata = create_dataset_metadata("paper-ledger", descriptor, record_count=2)
    assert metadata.dataset_name == "paper-ledger"
    assert metadata.source_name == "local-paper-ledger"
    assert validate_dataset_metadata(metadata)["ok"] is True
    assert validate_local_source_descriptor(descriptor)["ok"] is True

    rows_path = tmp_path / "rows.json"
    rows_path.write_text(json.dumps([{"timestamp": "2026-01-01T00:00:00Z", "source_name": "local-paper-ledger"}]), encoding="utf-8")
    rows = load_local_dataset(descriptor, path=rows_path)
    assert rows[0]["source_name"] == "local-paper-ledger"

    remote_descriptor = DataSourceDescriptor(
        name="remote-live",
        source_type="http",
        uri="https://example.invalid/live.csv",
        local_only=False,
    )
    with pytest.raises(ValueError):
        load_local_dataset(remote_descriptor)


def test_data_validation_catches_missing_fields() -> None:
    from src.data.validation import validate_dataset_metadata, validate_dataset_rows

    missing = validate_dataset_metadata({"dataset_name": "sample"})
    assert missing["ok"] is False
    assert set(missing["missing_fields"]) == {"source_name", "source_type"}

    row_missing = validate_dataset_rows([{"timestamp": "2026-01-01T00:00:00Z"}])
    assert row_missing["ok"] is False
    assert row_missing["missing_rows"][0]["missing_fields"] == ["source_name"]


def test_data_module_sources_do_not_import_network_or_secret_libraries() -> None:
    forbidden = tuple(FORBIDDEN_IMPORTS)
    for name in MODULE_NAMES:
        module = importlib.import_module(name)
        source = inspect.getsource(module)
        lowered = source.lower()
        for token in forbidden:
            assert token not in lowered, f"{token} found in {name}"
        assert "getenv" not in lowered, name
