from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZH8_DECISION_ENGINE_SERVICE_PLAN.md",
    ROOT / "DECISION_ENGINE_OWNERSHIP_MAP_AFTER_10K8ZH8.md",
    ROOT / "SERVICE_LAYER_THINNING_PLAN_AFTER_10K8ZH8.md",
]


def test_service_plan_docs_state_orchestration_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "src/services/decision_engine.py",
        "thin orchestration shell",
        "AI/LLM deferred",
        "brokerage/live execution deferred",
    ]:
        assert phrase in text


def test_decision_engine_imports_and_evaluates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    decision_engine = importlib.import_module("src.services.decision_engine")

    result = decision_engine.evaluate_decision(
        {
            "american_odds": -110,
            "market_probability": 0.52,
            "model_probability": 0.55,
            "bankroll": 1000,
            "stake": 50,
            "average_daily_volume": 1000,
            "risk_profile": "standard",
        }
    )
    assert result["execution_enabled"] is False
    assert result["live_connector_enabled"] is False
    assert result["context"]["fair_odds_american"] is not None
    assert decision_engine.build_decision_summary({"american_odds": -110})["decision"] in {"watch", "lean", "bet"}


def test_decision_engine_has_no_live_dependencies() -> None:
    text = (ROOT / "src/services/decision_engine.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
        assert forbidden not in text
