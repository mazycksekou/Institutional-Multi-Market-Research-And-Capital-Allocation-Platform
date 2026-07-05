from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZH4_CORE_PRICING_EXTRACTION.md",
    ROOT / "CORE_PRICING_OWNERSHIP_MAP_AFTER_10K8ZH4.md",
    ROOT / "CORE_PRICING_COMPATIBILITY_REPORT_AFTER_10K8ZH4.md",
]


def test_docs_exist_and_state_pricing_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Pricing ownership is canonical in `src/core/pricing.py`.",
        "market_pricing.py",
        "quant_engine.py",
        "No live execution",
        "canonical target: `src/core/pricing.py`",
    ]:
        assert phrase in text


def test_pricing_imports_and_wrapper_parity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    pricing = importlib.import_module("src.core.pricing")
    market_pricing = importlib.import_module("market_pricing")
    quant_engine = importlib.import_module("quant_engine")

    assert pricing.american_to_decimal(-110) == pytest.approx(1.909090909, rel=0, abs=1e-9)
    assert pricing.implied_probability_from_american(-110) == pytest.approx(0.5238095238, rel=0, abs=1e-9)
    assert pricing.edge(0.55, 0.52) == pytest.approx(0.03, rel=0, abs=1e-9)
    assert pricing.expected_value_per_unit(-110, 0.55) > 0
    assert pricing.normalize_price_payload({"american_odds": -110, "true_probability": 0.55})["fair_american_odds"] == -122

    assert market_pricing.american_to_decimal(-110) == pricing.american_to_decimal(-110)
    assert quant_engine.american_to_decimal(-110) == pricing.american_to_decimal(-110)


def test_pricing_module_has_no_live_dependencies() -> None:
    text = (ROOT / "src/core/pricing.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
        assert forbidden not in text
