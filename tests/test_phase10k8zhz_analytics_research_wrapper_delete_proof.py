from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHZ_ANALYTICS_RESEARCH_WRAPPER_DELETE_PROOF.md",
    ROOT / "ANALYTICS_RESEARCH_WRAPPER_IMPORT_SCAN_AFTER_10K8ZHZ.md",
    ROOT / "ANALYTICS_RESEARCH_WRAPPER_TEST_SCAN_AFTER_10K8ZHZ.md",
    ROOT / "ANALYTICS_RESEARCH_WRAPPER_DELETE_READINESS_AFTER_10K8ZHZ.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_wrapper_delete_proof_docs_capture_classifications() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "DELETE_READY_AFTER_PROOF",
        "ACTIVE_TEST_DEPENDENCY",
        "FILE_IO_OR_STORAGE_BLOCKED",
        "SCHEDULER_COUPLED_BLOCKED",
        "COMPATIBILITY_WRAPPER_ONLY",
        "src/analytics/model_governance/governance_health.py",
        "research/market_research_store.py",
        "automation_scheduler/model_maturity_registry.py",
    ]:
        assert fragment.lower() in text.lower()


def test_canonical_analytics_and_research_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    analytics = importlib.reload(importlib.import_module("src.analytics"))
    research = importlib.reload(importlib.import_module("src.research"))

    performance = analytics.build_performance_summary([0.1, -0.05, 0.2])
    attribution = analytics.build_attribution_summary({"alpha": 0.2, "beta": 0.1}, total=0.3)
    governance = analytics.summarize_governance(blockers=("x",))
    health = analytics.build_governance_health(
        {"model_inventory_count": 1, "active_scoring_ready_count": 1, "production_candidate_count": 0},
        {"blocked_model_count": 0},
    )
    lane = research.build_research_lane_descriptor("lane-1", "Lane One")
    experiment = research.build_experiment_metadata("exp-1", lane.lane_id, "Objective")
    ablation = research.build_ablation_plan("exp-1", ["feature_a"])
    schema = research.describe_research_schema()

    assert performance.sample_count == 3
    assert attribution.residual == pytest.approx(0.0)
    assert governance.status == "review_required"
    assert health["governance_status"] == "ok"
    assert lane.local_only is True
    assert experiment.local_only is True
    assert ablation.local_only is True
    assert schema.local_only is True


def test_canonical_packages_remain_and_wrappers_are_not_required() -> None:
    for relpath in [
        "src/analytics/__init__.py",
        "src/research/__init__.py",
        "src/analytics/governance.py",
        "src/research/maturity.py",
        "src/analytics/model_governance/__init__.py",
        'src/automation_scheduler_legacy/__init__.py',
    ]:
        if relpath.startswith("src/automation_scheduler_legacy/"):
            assert not (ROOT / relpath).exists()
        else:
            assert (ROOT / relpath).exists()


def test_wrapper_sources_are_local_only() -> None:
    for name in [
        "src.analytics.governance",
        "src.analytics.reports",
        "src.research.maturity",
        "src.research.storage",
        "src.analytics.model_governance",
    ]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic", "deepseek"]:
            assert token not in source, f"{token} found in {name}"


def test_model_governance_enforcement_remains_preserved() -> None:
    import src.analytics.model_governance as mg

    assert mg.default_governance_config()["human_approval_required"] is True
    assert mg.contains_banned_language("can't lose")
    assert mg.safe_decision_label("can't lose") == "blocked_by_governance"
    assert callable(mg.generate_governance_report)
    assert callable(mg.get_governance_health)


def test_automation_scheduler_remains_decommission_target() -> None:
    text = _read(ROOT / "PHASE10K8ZHZ_ANALYTICS_RESEARCH_WRAPPER_DELETE_PROOF.md")
    assert "automation_scheduler remains a decommission target" in text.lower() or "scheduler-coupled" in text.lower()


def test_no_deleted_odds_or_prediction_shells_reintroduced() -> None:
    for relpath in [
        "kalshi_client.py",
        "providers/kalshi_provider.py",
        "betting_providers/kalshi_api.py",
        'src/automation_scheduler_legacy/kalshi_readonly_adapter.py',
        'src/automation_scheduler_legacy/kalshi_market_provider.py',
        "sharp_client.py",
        "providers/sharp_provider.py",
        "betting_providers/sharp_api.py",
        "betting_providers/the_odds_api.py",
        "betting_providers/sportsgameodds.py",
        'src/automation_scheduler_legacy/sharp_sportsbook_adapter.py',
        'src/automation_scheduler_legacy/sportsbook_odds_provider.py',
    ]:
        assert not (ROOT / relpath).exists()
