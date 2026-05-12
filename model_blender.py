"""Blend model probability with market-derived probabilities (never invent model inputs)."""
from __future__ import annotations

from typing import Optional


def blend_probabilities(
    model_probability: Optional[float],
    market_probability: Optional[float],
    model_weight: float = 0.65,
) -> tuple[float, str]:
    """
    Returns (blended_prob, source_note).
    If model missing, returns (market_probability or 0.0, 'market_only').
    """
    mw = max(0.0, min(1.0, float(model_weight)))
    if model_probability is None:
        if market_probability is None:
            return 0.0, "no_probability"
        return float(market_probability), "market_only_model_missing"
    m = float(model_probability)
    if market_probability is None:
        return m, "model_only"
    mk = float(market_probability)
    blended = m * mw + mk * (1 - mw)
    return max(0.0, min(1.0, blended)), "blended"


def confidence_score(edge_percent: float, num_books: int = 1) -> int:
    base = 40 + edge_percent * 2.5 + min(20, num_books * 3)
    return int(max(0, min(100, round(base))))
