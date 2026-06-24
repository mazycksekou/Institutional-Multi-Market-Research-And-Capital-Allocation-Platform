from __future__ import annotations

import importlib
import inspect
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHV_ANALYTICS_DOWNSTREAM_REDIRECTION.md",
    ROOT / "ANALYTICS_DOWNSTREAM_REDIRECTION_MAP_AFTER_10K8ZHV.md",
    ROOT / "ANALYTICS_DOWNSTREAM_COMPATIBILITY_REPORT_AFTER_10K8ZHV.md",
    ROOT / "ANALYTICS_DOWNSTREAM_DELETE_READINESS_AFTER_10K8ZHV.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_analytics_downstream_docs_capture_redirection_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "Analytics Downstream Redirection",
        "src.analytics.governance.build_governance_health",
        "model_governance/governance_health.py",
        "Compatibility wrapper",
        "No legacy analytics file was deleted",
    ]:
        assert fragment.lower() in text.lower()


def test_governance_health_redirects_to_canonical_helper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )
    monkeypatch.chdir(tmp_path)

    reports_dir = tmp_path / "data" / "performance_reports"
    audits_dir = tmp_path / "data" / "governance_audit"
    reports_dir.mkdir(parents=True)
    audits_dir.mkdir(parents=True)
    (reports_dir / "one.json").write_text(
        json.dumps({"performance_status": "backtest_complete", "blocked_reasons": ["blocked_by_performance"]}),
        encoding="utf-8",
    )
    (reports_dir / "two.json").write_text(
        json.dumps({"performance_status": "review_required", "blocked_reasons": ["blocked_by_calibration"]}),
        encoding="utf-8",
    )
    (audits_dir / "audit.json").write_text(json.dumps({"ok": True}), encoding="utf-8")

    import model_governance.governance_health as legacy_health
    from src.analytics.governance import build_governance_health

    monkeypatch.setattr(
        legacy_health,
        "inventory_counts",
        lambda: {
            "model_inventory_count": 2,
            "active_scoring_ready_count": 1,
            "production_candidate_count": 1,
        },
    )
    monkeypatch.setattr(
        legacy_health,
        "get_model_inventory",
        lambda: [{"model_id": "m1", "activation_tier": "research_only"}],
    )
    monkeypatch.setattr(
        legacy_health,
        "default_governance_config",
        lambda: {"human_approval_required": True, "auto_execution_enabled": False},
    )

    wrapper_health = legacy_health.get_governance_health()
    canonical_health = build_governance_health(
        {
            "model_inventory_count": 2,
            "active_scoring_ready_count": 1,
            "production_candidate_count": 1,
        },
        {"blocked_model_count": 1},
        config={"human_approval_required": True, "auto_execution_enabled": False},
        reports_dir=reports_dir,
        audit_dir=audits_dir,
    )

    assert wrapper_health == canonical_health
    assert wrapper_health["governance_status"] == "ok"
    assert wrapper_health["backtest_ready_count"] == 1
    assert wrapper_health["blocked_by_performance_count"] == 1
    assert wrapper_health["blocked_by_calibration_count"] == 1
    assert wrapper_health["blocked_models_count"] == 1


def test_analytics_sources_remain_local_only() -> None:
    for name in [
        "src.analytics.governance",
        "src.analytics.reports",
        "model_governance.governance_health",
    ]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name
        for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic"]:
            assert token not in source, f"{token} found in {name}"


def test_legacy_analytics_files_remain_preserved() -> None:
    for relpath in [
        "model_governance/governance_health.py",
        "model_governance/governance_report.py",
        "model_governance/model_validation_report.py",
    ]:
        assert (ROOT / relpath).exists()
