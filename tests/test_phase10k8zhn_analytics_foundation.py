from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHN_ANALYTICS_FOUNDATION.md",
    ROOT / "ANALYTICS_FOUNDATION_OWNERSHIP_MAP_AFTER_10K8ZHN.md",
    ROOT / "ANALYTICS_GOVERNANCE_MIGRATION_MAP_AFTER_10K8ZHN.md",
    ROOT / "ANALYTICS_VALIDATION_REPORT_AFTER_10K8ZHN.md",
]
MODULES = [
    "src.analytics",
    "src.analytics.contracts",
    "src.analytics.performance",
    "src.analytics.attribution",
    "src.analytics.governance",
]
FORBIDDEN = [
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


def test_analytics_docs_capture_foundation_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for phrase in [
        "PHASE 10K8ZHN",
        "src.analytics",
        "reporting",
        "attribution",
        "calibration summaries",
        "governance summaries",
        "performance analytics",
        "model evaluation summaries",
        "no live API calls",
        "no AI/LLM calls",
        "no broker execution",
    ]:
        assert phrase.lower() in text.lower()


def test_analytics_modules_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    modules = [importlib.reload(importlib.import_module(name)) for name in MODULES]
    analytics = modules[0]

    for symbol in [
        "PerformanceSummaryContract",
        "AttributionSummaryContract",
        "CalibrationSummaryContract",
        "GovernanceSummaryContract",
        "ModelEvaluationSummaryContract",
        "summarize_performance",
        "summarize_attribution",
        "summarize_governance",
        "build_performance_summary",
        "build_attribution_summary",
        "build_calibration_summary",
        "build_model_evaluation_summary",
    ]:
        assert hasattr(analytics, symbol), symbol


def test_analytics_summary_helpers_build_local_objects() -> None:
    from src.analytics import (
        build_attribution_summary,
        build_calibration_summary,
        build_model_evaluation_summary,
        build_performance_summary,
        summarize_governance,
    )

    performance = build_performance_summary([0.1, -0.05, 0.15], label="sample")
    attribution = build_attribution_summary({"signal": 0.2, "timing": 0.1}, label="sample", total=0.35)
    governance = summarize_governance(
        label="sample",
        status="review_required",
        blockers=("calibration", "drift"),
        checks={"calibration_ok": True, "drift_ok": False},
    )
    calibration = build_calibration_summary(
        label="sample",
        sample_count=3,
        calibration_error=0.05,
        calibration_score=0.95,
        buckets={"low": 0.2, "high": 0.8},
    )
    evaluation = build_model_evaluation_summary(
        "model-1",
        {"accuracy": 0.91, "precision": 0.9},
        status="approved",
        notes=("local-only",),
    )

    assert performance.sample_count == 3
    assert performance.win_count == 2
    assert round(performance.win_rate, 6) == round(2 / 3, 6)
    assert attribution.total == 0.35
    assert round(attribution.residual, 6) == round(0.05, 6)
    assert governance.status == "review_required"
    assert governance.failing_checks == ("drift_ok",)
    assert calibration.sample_count == 3
    assert evaluation.model_id == "model-1"


def test_analytics_sources_do_not_import_network_or_connector_libraries() -> None:
    for name in MODULES:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        for token in FORBIDDEN:
            assert token not in source, f"{token} found in {name}"
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name

