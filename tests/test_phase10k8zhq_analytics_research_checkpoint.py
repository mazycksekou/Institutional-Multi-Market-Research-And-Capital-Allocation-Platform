from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHQ_ANALYTICS_RESEARCH_CHECKPOINT.md",
    ROOT / "POST_ANALYTICS_RESEARCH_ARCHITECTURE_MAP_AFTER_10K8ZHQ.md",
    ROOT / "REMAINING_AI_BROKERAGE_PRODUCTION_QUEUE_AFTER_10K8ZHQ.md",
    ROOT / "NEXT_AI_BROKERAGE_DEFERRED_PLAN_AFTER_10K8ZHQ.md",
]


def test_checkpoint_docs_state_foundations_and_deferrals() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "analytics foundation status",
        "research foundation status",
        "legacy owner map status",
        "no AI/LLM implementation",
        "no live data activation",
        "no broker execution",
        "no production deployment",
        "next AI/brokerage plan remains deferred",
    ]:
        assert phrase.lower() in text.lower()


def test_checkpoint_packages_import_safely() -> None:
    analytics = importlib.import_module("src.analytics")
    research = importlib.import_module("src.research")
    assert hasattr(analytics, "build_model_evaluation_summary")
    assert hasattr(research, "build_ablation_plan")

