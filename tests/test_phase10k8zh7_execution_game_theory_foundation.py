from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZH7_EXECUTION_GAME_THEORY_FOUNDATION.md",
    ROOT / "EXECUTION_GAME_THEORY_FUNCTION_MAP_AFTER_10K8ZH7.md",
    ROOT / "MARKET_IMPACT_VALIDATION_AFTER_10K8ZH7.md",
    ROOT / "POSITION_ACCUMULATION_VALIDATION_AFTER_10K8ZH7.md",
]


def test_docs_state_execution_game_theory_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "src/core/execution.py",
        "src/core/market_impact.py",
        "src/core/game_theory.py",
        "position_accumulation_plan",
        "thesis_break_triggered",
        "No order placement",
    ]:
        assert phrase in text


def test_execution_modules_import_and_behave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    execution = importlib.import_module("src.core.execution")
    market_impact = importlib.import_module("src.core.market_impact")
    game_theory = importlib.import_module("src.core.game_theory")

    assert execution.split_order(10, 4)
    assert sum(execution.split_order(10, 4)) == pytest.approx(10.0, abs=1e-6)
    assert execution.liquidity_adjusted_size(100, 1000, max_participation_rate=0.1) == pytest.approx(100.0, abs=1e-6)
    assert execution.estimate_slippage(100, 1000, spread_bps=5) > 0

    assert market_impact.estimate_market_impact(100, 1000, spread_bps=5, volatility=0.2) > 0
    assert market_impact.signaling_risk_score(100, 1000, order_count=3) > 0
    assert market_impact.adverse_selection_score(5, 0.2, 100, 1000) > 0

    plan = game_theory.position_accumulation_plan(9, tranches=3, average_daily_volume=90)
    assert plan["target_size"] == pytest.approx(9.0, abs=1e-6)
    assert len(plan["tranches"]) == 3
    assert game_theory.thesis_break_triggered(0.42, 0.5, tolerance=0.05) is True


def test_execution_files_have_no_live_dependencies() -> None:
    for relpath in [
        "src/core/execution.py",
        "src/core/market_impact.py",
        "src/core/game_theory.py",
    ]:
        text = (ROOT / relpath).read_text(encoding="utf-8").lower()
        for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
            assert forbidden not in text
