from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI5_ANALYTICS_RESEARCH_WRAPPER_DELETION.md",
    ROOT / "ANALYTICS_RESEARCH_WRAPPER_DELETION_PROOF_AFTER_10K8ZI5.md",
    ROOT / "POST_ANALYTICS_RESEARCH_WRAPPER_DELETION_IMPORT_SCAN_AFTER_10K8ZI5.md",
    ROOT / "ANALYTICS_RESEARCH_WRAPPER_DELETION_COMPLETION_STATUS_AFTER_10K8ZI5.md",
]
DELETED = [
    "model_governance/governance_health.py",
    "model_governance/governance_report.py",
    "model_governance/model_validation_report.py",
    "research/market_research_schema.py",
    "research/market_research_store.py",
    "automation_scheduler/deep_learning_research_lanes.py",
    "automation_scheduler/tabular_ml_research.py",
    "automation_scheduler/model_maturity_registry.py",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_docs_record_wrapper_deletion_completion() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "approved deletion targets",
        "canonical ownership remains in src.analytics and src.research",
        "wrapper-only analytics/research shells",
        "no live behavior or AI/brokerage",
    ]:
        assert fragment.lower() in text.lower()


def test_approved_wrappers_are_deleted() -> None:
    for relpath in DELETED:
        assert not (ROOT / relpath).exists()


def test_canonical_packages_import_safely() -> None:
    analytics = importlib.import_module("src.analytics")
    research = importlib.import_module("src.research")
    governance = importlib.import_module("model_governance")
    scheduler = importlib.import_module('src.automation_scheduler_legacy')

    assert analytics.build_governance_health({"model_inventory_count": 0}, {"blocked_model_count": 0})["governance_status"] == "ok"
    assert research.build_model_maturity_registry(total_labeled_outcomes=0)["status"] == "model_maturity_registry"
    assert callable(governance.get_governance_health)
    assert callable(scheduler.get_deep_learning_research_lanes)


def test_runtime_and_test_files_no_longer_require_deleted_wrappers() -> None:
    scan_paths = [
        ROOT / "src" / "automation_scheduler_legacy" / "__init__.py",
        ROOT / "src" / "automation_scheduler_legacy" / "data_intelligence_registry.py",
        ROOT / "src" / "automation_scheduler_legacy" / "cross_asset_intelligence_router.py",
        ROOT / "model_governance" / "__init__.py",
        ROOT / "tests" / "test_governance_health.py",
        ROOT / "tests" / "test_governance_report.py",
        ROOT / "tests" / "test_model_validation_report.py",
        ROOT / "tests" / "test_market_research_store.py",
        ROOT / "tests" / "test_data_intelligence_stack.py",
        ROOT / "tests" / "test_phase10k8zhv_analytics_downstream_redirection.py",
        ROOT / "tests" / "test_phase10k8zhw_research_downstream_redirection.py",
        ROOT / "tests" / "test_phase10k8zhz_analytics_research_wrapper_delete_proof.py",
    ]
    active_markers = ("import ", "from ", "patch(", "monkeypatch", "mock.patch", "importlib.import_module")
    for path in scan_paths:
        content = path.read_text(encoding="utf-8")
        for deleted in [
            "model_governance.governance_health",
            "model_governance.governance_report",
            "model_governance.model_validation_report",
            "research.market_research_schema",
            "research.market_research_store",
            "automation_scheduler.deep_learning_research_lanes",
            "automation_scheduler.tabular_ml_research",
            "automation_scheduler.model_maturity_registry",
        ]:
            for line in content.splitlines():
                if deleted in line and any(marker in line for marker in active_markers):
                    raise AssertionError(f"{deleted} still actively referenced in {path}: {line}")


def test_deleted_legacy_odds_prediction_shells_not_reintroduced() -> None:
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

