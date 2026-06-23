from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHB_SERVICE_LAYER_OWNERSHIP_AUDIT.md",
    ROOT / "SERVICE_LAYER_FUNCTION_INVENTORY_AFTER_10K8ZHB.md",
    ROOT / "SERVICE_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHB.md",
    ROOT / "SERVICE_LAYER_THINNING_SEQUENCE_AFTER_10K8ZHB.md",
]


def test_service_layer_docs_capture_ownership_and_thinning() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "service_orchestration_owner",
        "migrate_to_src_core",
        "compatibility_shim_candidate",
        "src/services/decision_engine.py",
        "src/services/enrichment_service.py",
        "src/services/odds_runtime_bridge.py",
        "src/services/prediction_market_runtime_bridge.py",
        "screenshot_intake.py",
        "bet_log.py",
        "bet_decision_engine.py",
        "ai/llm remains deferred",
        "brokerage/live execution remains deferred",
    ]:
        assert phrase in text


def test_service_layer_modules_import_safely() -> None:
    modules = [
        "src.services.decision_engine",
        "src.services.enrichment_service",
        "src.services.action_betting_service",
        "src.services.bet_csv_service",
        "src.services.model_backtest_service",
        "src.services.odds_runtime_bridge",
        "src.services.prediction_market_runtime_bridge",
        "bet_log",
        "bet_decision_engine",
        "screenshot_intake",
    ]
    imported = [importlib.import_module(name) for name in modules]
    assert [module.__name__ for module in imported] == modules


def test_service_decision_engine_remains_disabled_for_live_execution() -> None:
    decision_engine = importlib.import_module("src.services.decision_engine")
    result = decision_engine.build_decision_summary({"american_odds": -110, "model_probability": 0.57, "market_probability": 0.53, "bankroll": 1000})
    assert result["execution_enabled"] is False
    assert result["live_connector_enabled"] is False
    assert result["summary"]["edge_percent"] is not None


def test_service_layer_sources_have_no_live_network_clients() -> None:
    forbidden = ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]
    for relpath in [
        "src/services/decision_engine.py",
        "src/services/enrichment_service.py",
        "src/services/action_betting_service.py",
        "src/services/bet_csv_service.py",
        "src/services/model_backtest_service.py",
        "src/services/odds_runtime_bridge.py",
        "src/services/prediction_market_runtime_bridge.py",
        "bet_log.py",
        "bet_decision_engine.py",
        "screenshot_intake.py",
    ]:
        text = (ROOT / relpath).read_text(encoding="utf-8").lower()
        for item in forbidden:
            assert item not in text, relpath
