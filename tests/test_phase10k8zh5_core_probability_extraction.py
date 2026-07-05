from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZH5_CORE_PROBABILITY_EXTRACTION.md",
    ROOT / "CORE_PROBABILITY_OWNERSHIP_MAP_AFTER_10K8ZH5.md",
    ROOT / "CORE_PROBABILITY_COMPATIBILITY_REPORT_AFTER_10K8ZH5.md",
]


def test_docs_state_probability_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Probability ownership is canonical in `src/core/probability.py`.",
        "model_probability.py",
        "calibration-safe",
        "canonical target: `src/core/probability.py`",
    ]:
        assert phrase in text


def test_probability_imports_and_behave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    probability = importlib.import_module("src.core.probability")
    model_probability = importlib.import_module("model_probability")

    inputs = probability.IndependentInputs(projection_probability=0.55, weather_adjustment=0.02)
    assert len(inputs.get_active_inputs()) == 2
    assert probability.calculate_data_quality_score(inputs) > 0
    assert probability.normalize_probability(0.55) == pytest.approx(0.55, abs=1e-9)
    assert probability.probability_to_edge(0.55, 0.52) == pytest.approx(0.03, abs=1e-9)

    result = probability.blend_probabilities(0.55, inputs)
    assert result.probability_type == "blended_market_and_projection"
    assert result.final_probability != 0.55
    assert result.confidence_grade in {"A", "B", "C", "D", "F"}

    response = probability.create_probability_response(0.55, inputs)
    assert response["ok"] is True
    assert response["probability_type"] == "blended_market_and_projection"

    assert model_probability.IndependentInputs.__name__ == probability.IndependentInputs.__name__


def test_probability_module_has_no_live_dependencies() -> None:
    text = (ROOT / "src/core/probability.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
        assert forbidden not in text
