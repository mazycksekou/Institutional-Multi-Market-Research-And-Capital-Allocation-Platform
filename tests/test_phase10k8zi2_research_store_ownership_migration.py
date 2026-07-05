from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI2_RESEARCH_STORE_OWNERSHIP_MIGRATION.md",
    ROOT / "RESEARCH_STORE_MIGRATION_MAP_AFTER_10K8ZI2.md",
    ROOT / "RESEARCH_STORE_COMPATIBILITY_REPORT_AFTER_10K8ZI2.md",
    ROOT / "RESEARCH_STORE_DELETE_READINESS_AFTER_10K8ZI2.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_docs_record_storage_migration_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "src.research.storage",
        "local sqlite",
        "compatibility surfaces",
        "delete-ready",
    ]:
        assert fragment.lower() in text.lower()


def test_canonical_research_storage_is_local_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    storage = importlib.reload(importlib.import_module("src.research.storage"))
    schema = storage.describe_research_schema(metadata={"phase": "10K8ZI2"})
    store = storage.describe_research_store(path=str(tmp_path / "market_research.db"), metadata={"owner": "local"})

    db_path = storage.initialize_market_research_db(tmp_path / "market_research.db")
    tables = storage.list_market_research_tables(db_path)

    assert schema.local_only is True
    assert store.local_only is True
    assert store.db_filename == storage.DEFAULT_DB_FILENAME
    assert "schema_metadata" in tables
    assert storage.table_exists("schema_metadata", db_path) is True


def test_canonical_storage_sources_are_safe() -> None:
    module = importlib.import_module("src.research.storage")
    source = inspect.getsource(module).lower()
    assert "src.connectors" not in source
    for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic"]:
        assert token not in source

