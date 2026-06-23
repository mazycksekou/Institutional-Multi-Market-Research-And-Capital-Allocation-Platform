from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHA_CORE_ENGINE_MIGRATION_CHECKPOINT.md",
    ROOT / "POST_CORE_ENGINE_ARCHITECTURE_MAP_AFTER_10K8ZHA.md",
    ROOT / "REMAINING_SERVICE_DASHBOARD_API_QUEUE_AFTER_10K8ZHA.md",
    ROOT / "NEXT_AI_BROKERAGE_DEFERRED_PLAN_AFTER_10K8ZHA.md",
]


def test_checkpoint_docs_state_architecture_and_deferrals() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Pricing ownership: `src/core/pricing.py`",
        "Probability ownership: `src/core/probability.py`",
        "Risk ownership: `src/core/risk.py`",
        "Portfolio ownership: `src/core/portfolio.py`",
        "Execution/game-theory ownership: `src/core/execution.py`",
        "Service orchestration ownership: `src/services/decision_engine.py`",
        "AI/LLM deferred",
        "Brokerage/live execution deferred",
        "Dashboard/API cleanup remains",
    ]:
        assert phrase in text


def test_checkpoint_modules_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    for module_name in [
        "src.core.pricing",
        "src.core.probability",
        "src.core.risk",
        "src.core.portfolio",
        "src.core.execution",
        "src.core.market_impact",
        "src.core.game_theory",
        "src.services.decision_engine",
    ]:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_remaining_legacy_owners_are_documented() -> None:
    text = (ROOT / "POST_CORE_ENGINE_ARCHITECTURE_MAP_AFTER_10K8ZHA.md").read_text(encoding="utf-8")
    for filename in [
        "quant_engine.py",
        "market_pricing.py",
        "model_probability.py",
        "risk_engine.py",
        "bet_decision_engine.py",
        "screenshot_intake.py",
        "main.py",
        "streamlit_app.py",
    ]:
        assert filename in text
