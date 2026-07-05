"""Deterministic game-theory helpers."""

from __future__ import annotations

from typing import Any

from src.core.execution import liquidity_adjusted_size, split_order
from src.core.market_impact import adverse_selection_score, signaling_risk_score


def position_accumulation_plan(
    target_size: float,
    tranches: int = 3,
    average_daily_volume: float | None = None,
    max_participation_rate: float = 0.1,
) -> dict[str, Any]:
    if target_size <= 0:
        return {"target_size": 0.0, "tranches": [], "liquidity_adjusted_size": 0.0}
    if tranches <= 0:
        raise ValueError("tranches must be positive.")
    chunk_size = max(0.01, float(target_size) / tranches)
    tranche_sizes = split_order(float(target_size), chunk_size)
    liquidity_adjusted = float(target_size)
    if average_daily_volume is not None:
        liquidity_adjusted = liquidity_adjusted_size(
            float(target_size),
            float(average_daily_volume),
            max_participation_rate=max_participation_rate,
        )
    cumulative = 0.0
    schedule = []
    for index, tranche in enumerate(tranche_sizes, start=1):
        cumulative += tranche
        schedule.append(
            {
                "tranche": index,
                "size": round(tranche, 6),
                "cumulative_size": round(cumulative, 6),
            }
        )
    return {
        "target_size": round(float(target_size), 6),
        "tranches": schedule,
        "liquidity_adjusted_size": round(liquidity_adjusted, 6),
        "signaling_risk_score": signaling_risk_score(
            float(target_size),
            float(average_daily_volume or target_size or 1.0),
            order_count=tranches,
        ),
        "adverse_selection_score": adverse_selection_score(
            0.0,
            0.0,
            float(target_size),
            float(average_daily_volume or target_size or 1.0),
        ),
    }


def thesis_break_triggered(
    current_probability: float,
    thesis_probability: float,
    tolerance: float = 0.05,
    min_edge: float = -0.03,
) -> bool:
    current = float(current_probability)
    thesis = float(thesis_probability)
    if current <= 0.0 or current >= 1.0:
        return True
    return abs(current - thesis) >= float(tolerance) or (current - thesis) <= float(min_edge)


__all__ = [
    "position_accumulation_plan",
    "thesis_break_triggered",
]
