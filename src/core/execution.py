"""Deterministic execution-planning helpers."""

from __future__ import annotations

from math import ceil


def estimate_slippage(
    order_size: float,
    average_daily_volume: float,
    spread_bps: float = 0.0,
    participation_rate: float = 0.1,
) -> float:
    if order_size <= 0 or average_daily_volume <= 0:
        return 0.0
    participation = min(1.0, abs(float(order_size)) / float(average_daily_volume))
    slippage_bps = float(spread_bps) + participation * 100.0 * max(0.0, float(participation_rate))
    return round(slippage_bps, 6)


def split_order(total_size: float, max_chunk_size: float) -> list[float]:
    if total_size <= 0:
        return []
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be positive.")
    total_size = float(total_size)
    max_chunk_size = float(max_chunk_size)
    chunk_count = max(1, ceil(total_size / max_chunk_size))
    base = total_size / chunk_count
    return [round(base, 6) for _ in range(chunk_count)]


def liquidity_adjusted_size(
    base_size: float,
    average_daily_volume: float,
    max_participation_rate: float = 0.1,
) -> float:
    if base_size <= 0 or average_daily_volume <= 0:
        return 0.0
    cap = float(average_daily_volume) * max(0.0, float(max_participation_rate))
    return round(min(float(base_size), cap), 6)


__all__ = [
    "estimate_slippage",
    "liquidity_adjusted_size",
    "split_order",
]
