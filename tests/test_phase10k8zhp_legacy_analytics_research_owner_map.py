from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "LEGACY_ANALYTICS_RESEARCH_OWNER_MAP_AFTER_10K8ZHP.md",
    ROOT / "ANALYTICS_RESEARCH_MIGRATION_SEQUENCE_AFTER_10K8ZHP.md",
    ROOT / "ANALYTICS_RESEARCH_DELETE_READINESS_AFTER_10K8ZHP.md",
]


def test_legacy_analytics_research_docs_cover_expected_classifications() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "MIGRATE_TO_SRC_ANALYTICS",
        "MIGRATE_TO_SRC_RESEARCH",
        "MIGRATE_TO_SRC_SERVICES",
        "KEEP_MODEL_GOVERNANCE_FOR_NOW",
        "COMPATIBILITY_SHIM_CANDIDATE",
        "DELETE_CANDIDATE_AFTER_PROOF",
        "UNSAFE_TO_TOUCH_AI_OR_LIVE",
        "automation_scheduler/deepseek_daily_report.py",
        "automation_scheduler/feature_ablation_lab.py",
        "model_governance/model_validation_report.py",
        "research/market_research_schema.py",
        "automation_scheduler remains a decommission target",
        "model_governance remains preserved until migration proof",
        "src.analytics",
        "src.research",
    ]:
        assert phrase in text


def test_legacy_analytics_research_packages_exist_and_import() -> None:
    analytics = importlib.import_module("src.analytics")
    research = importlib.import_module("src.research")
    assert hasattr(analytics, "summarize_performance")
    assert hasattr(research, "build_research_lane_descriptor")

