from __future__ import annotations

from typing import Any


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _score_threshold(value: float | None, levels: list[tuple[float, float]], missing: float = 0.0) -> float:
    if value is None:
        return missing
    for threshold, score in levels:
        if value >= threshold:
            return score
    return levels[-1][1] if levels else missing


def _spread_score(spread_percent: float | None) -> float:
    if spread_percent is None:
        return 35.0
    if spread_percent <= 0.10:
        return 96.0
    if spread_percent <= 0.30:
        return 88.0
    if spread_percent <= 0.75:
        return 72.0
    if spread_percent <= 1.50:
        return 52.0
    if spread_percent <= 3.00:
        return 30.0
    return 10.0


def _tier(score: float) -> str:
    if score < 20:
        return "very_low"
    if score < 40:
        return "low"
    if score < 65:
        return "moderate"
    if score < 85:
        return "strong"
    return "institutional"


def calculate_float_rotation(daily_volume: Any, float_shares: Any) -> float | None:
    volume = _num(daily_volume)
    shares = _num(float_shares)
    if volume is None or shares is None or shares <= 0:
        return None
    return round(volume / shares, 6)


def score_stock_liquidity(row: dict[str, Any]) -> dict[str, Any]:
    price = _num(row.get("price"))
    daily_volume = _num(row.get("daily_volume", row.get("volume")))
    float_shares = _num(row.get("float_shares"))
    dollar_volume = _num(row.get("dollar_volume"))
    if dollar_volume is None and price is not None and daily_volume is not None:
        dollar_volume = price * daily_volume
    relative_volume = _num(row.get("relative_volume", row.get("volume_ratio")), 0.0)
    spread_percent = _num(row.get("spread_percent"))
    bid_ask_depth = _num(row.get("bid_ask_depth"))
    halt_risk = _num(row.get("halt_risk", row.get("halt_risk_score")), 0.0) or 0.0
    dilution_risk = _num(row.get("dilution_risk", row.get("dilution_risk_score")), 0.0) or 0.0

    dollar_volume_score = _score_threshold(
        dollar_volume,
        [(50_000_000, 96.0), (10_000_000, 88.0), (2_000_000, 72.0), (500_000, 52.0), (100_000, 30.0), (0, 10.0)],
    )
    relative_volume_score = _score_threshold(relative_volume, [(10.0, 96.0), (5.0, 86.0), (2.0, 68.0), (1.0, 45.0), (0, 18.0)])
    spread_slippage_score = _spread_score(spread_percent)
    order_book_depth_score = _score_threshold(
        bid_ask_depth,
        [(1_000_000, 94.0), (250_000, 84.0), (50_000, 70.0), (10_000, 50.0), (1, 30.0), (0, 20.0)],
        missing=42.0,
    )
    risk_penalty = min(30.0, halt_risk * 0.12 + dilution_risk * 0.08)
    raw_score = (
        dollar_volume_score * 0.30
        + relative_volume_score * 0.25
        + spread_slippage_score * 0.25
        + order_book_depth_score * 0.20
        - risk_penalty
    )
    liquidity_score = round(_clamp(raw_score), 2)
    blockers: list[str] = []
    if price is None or price <= 0:
        blockers.append("missing_or_invalid_price")
    if daily_volume is None or daily_volume <= 0:
        blockers.append("missing_or_invalid_daily_volume")
    if dollar_volume is not None and dollar_volume < 100_000:
        blockers.append("dollar_volume_too_low")
    if spread_percent is not None and spread_percent > 3.0:
        blockers.append("spread_too_wide")
    if liquidity_score < 40:
        blockers.append("liquidity_score_below_40")

    float_rotation = calculate_float_rotation(daily_volume, float_shares)
    slippage_risk_score = round(_clamp(100.0 - spread_slippage_score + max(0.0, 55.0 - order_book_depth_score) * 0.35), 2)
    return {
        "asset_type": "stock",
        "price": price,
        "float_shares": float_shares,
        "shares_outstanding": _num(row.get("shares_outstanding")),
        "daily_volume": daily_volume,
        "relative_volume": relative_volume,
        "dollar_volume": round(dollar_volume, 2) if dollar_volume is not None else None,
        "spread_percent": spread_percent,
        "bid_ask_depth": bid_ask_depth,
        "average_true_range": _num(row.get("average_true_range")),
        "halt_risk": halt_risk,
        "dilution_risk": dilution_risk,
        "short_interest": _num(row.get("short_interest")),
        "borrow_fee": _num(row.get("borrow_fee")),
        "float_rotation": float_rotation,
        "liquidity_score": liquidity_score,
        "spread_slippage_score": round(spread_slippage_score, 2),
        "dollar_volume_score": round(dollar_volume_score, 2),
        "order_book_depth_score": round(order_book_depth_score, 2),
        "relative_volume_score": round(relative_volume_score, 2),
        "liquidity_tier": _tier(liquidity_score),
        "liquidity_blockers": blockers,
        "slippage_risk_score": slippage_risk_score,
    }


def score_crypto_liquidity(row: dict[str, Any]) -> dict[str, Any]:
    volume_24h = _num(row.get("volume_24h", row.get("daily_volume")))
    relative_volume = _num(row.get("relative_volume"), 0.0)
    spread_percent = _num(row.get("spread_percent"))
    depth_1pct = _num(row.get("order_book_depth_1pct"))
    depth_2pct = _num(row.get("order_book_depth_2pct"))
    exchange_count = _num(row.get("exchange_count"), 0.0) or 0.0
    slippage_estimate = _num(row.get("slippage_estimate"))
    liquidation_cluster_risk = _num(row.get("liquidation_cluster_risk"), 0.0) or 0.0
    volatility_score = _num(row.get("volatility_score"), 50.0) or 50.0

    dollar_volume_score = _score_threshold(
        volume_24h,
        [(500_000_000, 96.0), (100_000_000, 88.0), (20_000_000, 74.0), (5_000_000, 56.0), (1_000_000, 36.0), (0, 12.0)],
    )
    relative_volume_score = _score_threshold(relative_volume, [(5.0, 90.0), (2.0, 74.0), (1.0, 52.0), (0, 25.0)])
    spread_slippage_score = min(_spread_score(spread_percent), _spread_score(slippage_estimate) if slippage_estimate is not None else 100.0)
    depth_value = max(depth_1pct or 0.0, (depth_2pct or 0.0) * 0.55)
    order_book_depth_score = _score_threshold(
        depth_value,
        [(25_000_000, 96.0), (5_000_000, 86.0), (1_000_000, 72.0), (250_000, 55.0), (50_000, 34.0), (0, 14.0)],
        missing=25.0,
    )
    exchange_score = _score_threshold(exchange_count, [(20, 95.0), (10, 82.0), (5, 65.0), (2, 45.0), (1, 28.0), (0, 10.0)])
    risk_penalty = min(28.0, liquidation_cluster_risk * 0.12 + max(0.0, volatility_score - 70.0) * 0.20)
    raw_score = (
        dollar_volume_score * 0.28
        + relative_volume_score * 0.18
        + spread_slippage_score * 0.24
        + order_book_depth_score * 0.22
        + exchange_score * 0.08
        - risk_penalty
    )
    liquidity_score = round(_clamp(raw_score), 2)
    blockers: list[str] = []
    if volume_24h is None or volume_24h <= 0:
        blockers.append("missing_or_invalid_volume_24h")
    if spread_percent is not None and spread_percent > 3.0:
        blockers.append("spread_too_wide")
    if depth_value <= 0:
        blockers.append("missing_order_book_depth")
    if liquidity_score < 40:
        blockers.append("liquidity_score_below_40")
    return {
        "asset_type": "crypto",
        "market_cap": _num(row.get("market_cap")),
        "volume_24h": volume_24h,
        "relative_volume": relative_volume,
        "exchange_count": exchange_count,
        "order_book_depth_1pct": depth_1pct,
        "order_book_depth_2pct": depth_2pct,
        "spread_percent": spread_percent,
        "slippage_estimate": slippage_estimate,
        "funding_rate": _num(row.get("funding_rate")),
        "open_interest": _num(row.get("open_interest")),
        "liquidation_cluster_risk": liquidation_cluster_risk,
        "volatility_score": volatility_score,
        "liquidity_score": liquidity_score,
        "spread_slippage_score": round(spread_slippage_score, 2),
        "dollar_volume_score": round(dollar_volume_score, 2),
        "order_book_depth_score": round(order_book_depth_score, 2),
        "relative_volume_score": round(relative_volume_score, 2),
        "liquidity_tier": _tier(liquidity_score),
        "liquidity_blockers": blockers,
        "slippage_risk_score": round(_clamp(100.0 - spread_slippage_score + max(0.0, 55.0 - order_book_depth_score) * 0.35), 2),
    }


def score_liquidity_context(row: dict[str, Any], asset_type: str | None = None) -> dict[str, Any]:
    kind = str(asset_type or row.get("asset_type") or "stock").lower()
    if kind == "crypto":
        return score_crypto_liquidity(row)
    return score_stock_liquidity(row)
