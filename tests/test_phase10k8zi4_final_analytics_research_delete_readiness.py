from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI4_FINAL_ANALYTICS_RESEARCH_DELETE_READINESS.md",
    ROOT / "FINAL_ANALYTICS_RESEARCH_IMPORT_SCAN_AFTER_10K8ZI4.md",
    ROOT / "FINAL_ANALYTICS_RESEARCH_TEST_SCAN_AFTER_10K8ZI4.md",
    ROOT / "FINAL_ANALYTICS_RESEARCH_DELETE_DECISION_AFTER_10K8ZI4.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_final_delete_readiness_docs_cover_all_candidates() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "model_governance/governance_health.py",
        "model_governance/governance_report.py",
        "model_governance/model_validation_report.py",
        "research/market_research_schema.py",
        "research/market_research_store.py",
        "automation_scheduler/deep_learning_research_lanes.py",
        "automation_scheduler/tabular_ml_research.py",
        "automation_scheduler/model_maturity_registry.py",
        "DELETE_READY_AFTER_PROOF",
    ]:
        assert fragment.lower() in text.lower()


def test_final_canonical_architecture_imports_safely() -> None:
    analytics = importlib.import_module("src.analytics")
    research = importlib.import_module("src.research")
    model_governance = importlib.import_module("model_governance")

    assert analytics.build_governance_health({"model_inventory_count": 0}, {"blocked_model_count": 0})["governance_status"] == "ok"
    assert research.build_model_maturity_registry(total_labeled_outcomes=0)["status"] == "model_maturity_registry"
    assert callable(model_governance.get_governance_health)
    assert callable(research.build_deep_learning_research_lanes)


def test_no_deleted_wrappers_reintroduced_in_proof_phase() -> None:
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
