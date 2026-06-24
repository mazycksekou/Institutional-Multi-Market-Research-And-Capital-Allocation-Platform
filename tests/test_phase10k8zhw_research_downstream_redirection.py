from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHW_RESEARCH_DOWNSTREAM_REDIRECTION.md",
    ROOT / "RESEARCH_DOWNSTREAM_REDIRECTION_MAP_AFTER_10K8ZHW.md",
    ROOT / "RESEARCH_DOWNSTREAM_COMPATIBILITY_REPORT_AFTER_10K8ZHW.md",
    ROOT / "RESEARCH_DOWNSTREAM_DELETE_READINESS_AFTER_10K8ZHW.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_research_downstream_docs_capture_redirection_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "Research Downstream Redirection",
        "src.research",
        "build_tabular_ml_research_lanes",
        "build_deep_learning_research_lanes",
        "Compatibility wrapper",
    ]:
        assert fragment.lower() in text.lower()


def test_research_lane_helpers_redirect_to_canonical_package(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    import automation_scheduler as scheduler_pkg
    import automation_scheduler.deep_learning_research_lanes as legacy_dl
    import automation_scheduler.model_maturity_registry as maturity_registry
    import automation_scheduler.tabular_ml_research as legacy_tabular
    from src.research import (
        build_deep_learning_maturity_records,
        build_deep_learning_research_lanes,
        build_tabular_maturity_records,
        build_tabular_ml_research_lanes,
    )

    monkeypatch.setattr(scheduler_pkg, "load_outcome_records", lambda _base: [{} for _ in range(25)])
    monkeypatch.setattr(scheduler_pkg, "resolve_base_data_dir", lambda _base=None: Path("unused"))

    canonical_tabular = build_tabular_ml_research_lanes(total_labeled_outcomes=25, label_coverage=0.025)
    canonical_deep = build_deep_learning_research_lanes()
    canonical_tabular_records = build_tabular_maturity_records(total_labeled_outcomes=25)
    canonical_deep_records = build_deep_learning_maturity_records()

    legacy_tabular_payload = legacy_tabular.build_tabular_ml_research_lanes(total_labeled_outcomes=25, label_coverage=0.025)
    legacy_deep_payload = legacy_dl.build_deep_learning_research_lanes()
    scheduler_tabular_payload = scheduler_pkg.get_tabular_ml_research_lanes()
    scheduler_deep_payload = scheduler_pkg.get_deep_learning_research_lanes()
    registry_payload = maturity_registry.build_model_maturity_registry(total_labeled_outcomes=25)

    assert legacy_tabular_payload == canonical_tabular
    assert legacy_deep_payload == canonical_deep
    assert scheduler_tabular_payload["status"] == canonical_tabular["status"]
    assert scheduler_tabular_payload["total_lanes"] == canonical_tabular["total_lanes"]
    assert scheduler_deep_payload == canonical_deep
    assert registry_payload["status"] == "model_maturity_registry"
    assert registry_payload["total_models"] >= len(canonical_tabular_records) + len(canonical_deep_records)


def test_research_sources_remain_local_only() -> None:
    for name in [
        "src.research.lanes",
        "src.research.storage",
        "automation_scheduler.deep_learning_research_lanes",
        "automation_scheduler.tabular_ml_research",
        "automation_scheduler.model_maturity_registry",
        "automation_scheduler.__init__",
    ]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name
        for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic"]:
            assert token not in source, f"{token} found in {name}"


def test_legacy_research_files_remain_preserved() -> None:
    for relpath in [
        "automation_scheduler/deep_learning_research_lanes.py",
        "automation_scheduler/tabular_ml_research.py",
        "automation_scheduler/feature_ablation_lab.py",
        "research/market_research_schema.py",
        "research/market_research_store.py",
    ]:
        assert (ROOT / relpath).exists()
