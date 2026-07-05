from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHS_RESEARCH_MIGRATION_BATCH_1.md",
    ROOT / "RESEARCH_BATCH_1_MIGRATION_MAP_AFTER_10K8ZHS.md",
    ROOT / "RESEARCH_BATCH_1_COMPATIBILITY_REPORT_AFTER_10K8ZHS.md",
    ROOT / "RESEARCH_BATCH_1_DELETE_READINESS_AFTER_10K8ZHS.md",
]
MODULES = [
    "src.research",
    "src.research.contracts",
    "src.research.lanes",
    "src.research.experiments",
    "src.research.ablation",
    "src.research.storage",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_research_batch_docs_capture_migration_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "Research Migration Batch 1",
        "research lane descriptors",
        "experiment metadata",
        "hypothesis records",
        "ablation plan descriptors",
        "research store descriptors",
        "legacy research/ remains preserved",
        "No deletion occurred",
    ]:
        assert fragment.lower() in text.lower()


def test_research_batch_modules_import_safely(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    modules = [importlib.reload(importlib.import_module(name)) for name in MODULES]
    research = modules[0]
    storage = importlib.import_module("src.research.storage")

    lane = research.build_research_lane_descriptor("lane-1", "Lane One", topic="calibration")
    experiment = research.build_experiment_metadata("exp-1", lane.lane_id, "Experiment One")
    hypothesis = research.build_hypothesis_record("hyp-1", lane.lane_id, "Hypothesis")
    plan = research.build_ablation_plan("exp-1", ["feature_a", "feature_b"], controls=["baseline"], metrics=["roi"])
    schema = storage.describe_research_schema()
    store = storage.describe_research_store(path=str(tmp_path / "market_research.db"))

    db_path = storage.initialize_market_research_db(tmp_path / "market_research.db")
    tables = storage.list_market_research_tables(db_path)

    assert lane.name == "Lane One"
    assert experiment.objective == "Experiment One"
    assert hypothesis.hypothesis_id == "hyp-1"
    assert plan.components == ("feature_a", "feature_b")
    assert schema.schema_version == storage.MARKET_RESEARCH_SCHEMA_VERSION
    assert store.db_filename == storage.DEFAULT_DB_FILENAME
    assert "schema_metadata" in tables
    assert storage.table_exists("schema_metadata", db_path) is True


def test_research_batch_sources_remain_local_only() -> None:
    for name in MODULES:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name
        for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic"]:
            assert token not in source, f"{token} found in {name}"


def test_canonical_research_packages_exist() -> None:
    for relpath in [
        "src/research/__init__.py",
        "src/research/lanes.py",
        "src/research/storage.py",
    ]:
        assert (ROOT / relpath).exists()
