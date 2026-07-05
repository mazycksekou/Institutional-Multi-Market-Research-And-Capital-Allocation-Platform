from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZH6_PORTFOLIO_FOUNDATION.md",
    ROOT / "CORE_PORTFOLIO_FUNCTION_MAP_AFTER_10K8ZH6.md",
    ROOT / "CORE_PORTFOLIO_VALIDATION_AFTER_10K8ZH6.md",
]


def test_docs_state_portfolio_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Portfolio ownership is canonical in `src/core/portfolio.py`.",
        "position_exposure",
        "portfolio_summary",
    ]:
        assert phrase in text


def test_portfolio_imports_and_behave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    portfolio = importlib.import_module("src.core.portfolio")

    positions = {"A": 100.0, "B": {"exposure": 200.0}}
    assert portfolio.position_exposure(100.0) == pytest.approx(100.0, abs=1e-9)
    assert portfolio.total_exposure(positions) == pytest.approx(300.0, abs=1e-9)
    weights = portfolio.exposure_weights(positions)
    assert weights["A"] == pytest.approx(100.0 / 300.0, abs=1e-9)
    assert portfolio.concentration_score(positions) == pytest.approx(200.0 / 300.0, abs=1e-9)
    summary = portfolio.portfolio_summary(positions)
    assert summary["total_exposure"] == pytest.approx(300.0, abs=1e-9)
    assert summary["positions"]["A"]["exposure_pct"] == pytest.approx(100.0 / 300.0, abs=1e-9)


def test_portfolio_module_has_no_live_dependencies() -> None:
    text = (ROOT / "src/core/portfolio.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
        assert forbidden not in text
