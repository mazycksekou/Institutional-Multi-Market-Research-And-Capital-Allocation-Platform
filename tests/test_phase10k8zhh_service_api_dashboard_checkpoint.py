from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHH_SERVICE_API_DASHBOARD_CHECKPOINT.md",
    ROOT / "POST_SERVICE_THINNING_ARCHITECTURE_MAP_AFTER_10K8ZHH.md",
    ROOT / "REMAINING_MIGRATION_QUEUE_AFTER_10K8ZHH.md",
    ROOT / "NEXT_DATA_BACKTESTING_LAYER_PLAN_AFTER_10K8ZHH.md",
]


def test_checkpoint_docs_summarize_the_remaining_queue() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "service layer: canonical orchestration and bridge ownership",
        "screenshot workflow: still a compatibility shell",
        "decision/bet log: decision orchestration is canonical, bet logging remains root-level storage shell",
        "api layer: mostly thin",
        "dashboard/entrypoints: remain shell boundaries and are not deletion candidates",
        "automation scheduler: remains a decommission target",
        "src/services/screenshot_workflow.py",
        "ai/llm deferred",
        "brokerage deferred",
        "live production deferred",
    ]:
        assert phrase in text


def test_checkpoint_canonical_modules_import_safely() -> None:
    modules = [
        "src.services.decision_engine",
        "src.services.enrichment_service",
        "src.api.model_card_service",
        "src.providers.provider_router",
        "src.providers.registry",
        "src.providers.health",
        "src.connectors.prediction_market_data",
        "src.connectors.odds_data",
    ]
    imported = [importlib.import_module(name) for name in modules]
    assert [module.__name__ for module in imported] == modules


def test_checkpoint_files_remain_shell_boundaries() -> None:
    for relpath in ["main.py", "streamlit_app.py", "screenshot_intake.py", "bet_log.py", "bet_decision_engine.py"]:
        assert (ROOT / relpath).exists()
