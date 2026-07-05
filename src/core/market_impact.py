"""Deterministic market impact helpers."""

from __future__ import annotations

from src.core.execution import liquidity_adjusted_size


def estimate_market_impact(
    order_size: float,
    average_daily_volume: float,
    spread_bps: float = 0.0,
    volatility: float = 0.0,
) -> float:
    if order_size <= 0 or average_daily_volume <= 0:
        return 0.0
    participation = min(1.0, abs(float(order_size)) / float(average_daily_volume))
    impact = float(spread_bps) + participation * 80.0 + max(0.0, float(volatility)) * 10.0
    return round(impact, 6)


def signaling_risk_score(
    order_size: float,
    average_daily_volume: float,
    order_count: int = 1,
) -> float:
    if order_size <= 0 or average_daily_volume <= 0:
        return 0.0
    participation = min(1.0, abs(float(order_size)) / float(average_daily_volume))
    score = participation * 70.0 + min(30.0, max(0, int(order_count)) * 5.0)
    return round(min(100.0, score), 6)


def adverse_selection_score(
    spread_bps: float,
    volatility: float,
    order_size: float,
    average_daily_volume: float,
) -> float:
    if order_size <= 0 or average_daily_volume <= 0:
        return 0.0
    participation = min(1.0, abs(float(order_size)) / float(average_daily_volume))
    score = float(spread_bps) * 0.5 + max(0.0, float(volatility)) * 25.0 + participation * 50.0
    return round(min(100.0, score), 6)


def impact_adjusted_size(
    base_size: float,
    average_daily_volume: float,
    spread_bps: float = 0.0,
    volatility: float = 0.0,
    max_participation_rate: float = 0.1,
) -> float:
    adjusted = liquidity_adjusted_size(base_size, average_daily_volume, max_participation_rate=max_participation_rate)
    impact = estimate_market_impact(adjusted, average_daily_volume, spread_bps=spread_bps, volatility=volatility)
    return round(max(0.0, adjusted - impact / 100.0), 6)


__all__ = [
    "adverse_selection_score",
    "estimate_market_impact",
    "impact_adjusted_size",
    "signaling_risk_score",
]
