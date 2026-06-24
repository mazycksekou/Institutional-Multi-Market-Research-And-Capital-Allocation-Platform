from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHR_ANALYTICS_MIGRATION_BATCH_1.md",
    ROOT / "ANALYTICS_BATCH_1_MIGRATION_MAP_AFTER_10K8ZHR.md",
    ROOT / "ANALYTICS_BATCH_1_COMPATIBILITY_REPORT_AFTER_10K8ZHR.md",
    ROOT / "ANALYTICS_BATCH_1_DELETE_READINESS_AFTER_10K8ZHR.md",
]
MODULES = [
    "src.analytics",
    "src.analytics.performance",
    "src.analytics.attribution",
    "src.analytics.governance",
    "src.analytics.reports",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_analytics_batch_docs_capture_migration_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "Analytics Migration Batch 1",
        "build_model_validation_report",
        "generate_governance_report",
        "summarize_performance",
        "summarize_attribution",
        "summarize_governance",
        "model_governance remains preserved",
        "No deletion occurred",
    ]:
        assert fragment.lower() in text.lower()


def test_analytics_batch_modules_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    modules = [importlib.reload(importlib.import_module(name)) for name in MODULES]
    analytics = modules[0]
    reports = importlib.import_module("src.analytics.reports")

    performance = analytics.build_performance_summary([0.25, -0.1, 0.05])
    attribution = analytics.build_attribution_summary({"alpha": 0.2, "beta": 0.1}, total=0.35)
    governance = analytics.summarize_governance(status="review_required", blockers=("a", "b"))
    calibration = analytics.build_calibration_summary(label="calibration", sample_count=2, calibration_error=0.04, calibration_score=0.96)
    evaluation = analytics.build_model_evaluation_summary("m1", {"accuracy": 0.91})
    validation = reports.build_model_validation_report("model-1", "research_only", evidence_summary={"ok": True})
    governance_report = reports.generate_governance_report(
        [{"model_id": "m1", "activation_tier": "research_only"}],
        {"model_inventory_count": 1, "research_only_count": 1, "backtest_ready_count": 0, "paper_trade_ready_count": 0, "review_queue_ready_count": 0, "active_scoring_ready_count": 0, "production_candidate_count": 0},
        audit_records=(),
    )

    assert performance.sample_count == 3
    assert attribution.residual == pytest.approx(0.05)
    assert governance.status == "review_required"
    assert calibration.sample_count == 2
    assert evaluation.model_id == "m1"
    assert validation["model_id"] == "model-1"
    assert governance_report["blocked_model_count"] == 1


def test_analytics_batch_sources_remain_local_only() -> None:
    for name in MODULES:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name
        for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic"]:
            assert token not in source, f"{token} found in {name}"


def test_legacy_analytics_files_remain_preserved() -> None:
    for relpath in [
        "model_governance/model_validation_report.py",
        "model_governance/governance_report.py",
        "model_governance/governance_health.py",
    ]:
        assert (ROOT / relpath).exists()
