from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "CORE_ENGINE_COMPATIBILITY_WRAPPER_REPORT_AFTER_10K8ZH9.md",
    ROOT / "ROOT_ENGINE_IMPORT_SCAN_AFTER_10K8ZH9.md",
    ROOT / "CORE_ENGINE_MIGRATION_COMPLETION_STATUS_AFTER_10K8ZH9.md",
]


def test_wrapper_docs_state_compatibility_status() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "quant_engine.py",
        "market_pricing.py",
        "model_probability.py",
        "risk_engine.py",
        "bet_decision_engine.py",
        "Legacy root engine files remain importable as compatibility wrappers.",
    ]:
        assert phrase in text


def test_root_engine_wrappers_import_and_match_canonical(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    pricing = importlib.import_module("src.core.pricing")
    probability = importlib.import_module("src.core.probability")
    risk = importlib.import_module("src.core.risk")
    quant_engine = importlib.import_module("src.core.quant_engine")
    market_pricing = importlib.import_module("src.core.market_pricing")
    model_probability = importlib.import_module("src.core.model_probability")
    risk_engine = importlib.import_module("src.core.risk_engine")
    bet_decision_engine = importlib.import_module("src.services.bet_decision_engine")

    assert quant_engine.american_to_decimal(-110) == pricing.american_to_decimal(-110)
    assert market_pricing.american_to_decimal(-110) == pricing.american_to_decimal(-110)
    assert model_probability.IndependentInputs.__name__ == probability.IndependentInputs.__name__
    assert risk_engine.sharpe_ratio(0.1, 0.2, 0.02) == risk.sharpe_ratio(0.1, 0.2, 0.02)
    assert callable(bet_decision_engine.evaluate_lines_payload)


def test_root_engine_files_have_no_live_dependencies() -> None:
    for relpath in [
        "src/core/quant_engine.py",
        "src/core/market_pricing.py",
        "src/core/model_probability.py",
        "src/core/risk_engine.py",
        "src/services/bet_decision_engine.py",
    ]:
        text = (ROOT / relpath).read_text(encoding="utf-8").lower()
        for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
            assert forbidden not in text
