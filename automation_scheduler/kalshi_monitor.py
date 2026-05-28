from __future__ import annotations

from typing import Any


def _index_rows(rows: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").upper()
        if ticker:
            indexed[ticker] = row
    return indexed


def monitor_kalshi_market(
    *,
    previous_snapshot: list[dict[str, Any]] | None,
    current_snapshot: list[dict[str, Any]] | None,
    provider: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    previous_index = _index_rows(previous_snapshot)
    current_index = _index_rows(current_snapshot)
    candidates = []
    for ticker, current in current_index.items():
        previous = previous_index.get(ticker, {})
        current_price = float(current.get("price", 0) or 0)
        previous_price = float(previous.get("price", current_price) or current_price)
        current_spread = float(current.get("spread", 0) or 0)
        previous_spread = float(previous.get("spread", current_spread) or current_spread)
        imbalance = abs(float(current.get("order_book_imbalance", 0) or 0))
        liquidity = float(current.get("liquidity", 0.5) or 0.5)
        movement_strength = abs(current_price - previous_price) + abs(current_spread - previous_spread) + (imbalance * 20)
        if movement_strength <= 0:
            continue
        candidates.append(
            {
                "source": "kalshi_monitor",
                "provider": provider,
                "market_type": "prediction_markets",
                "sport_or_symbol": ticker,
                "market": "prediction_market",
                "selection": ticker,
                "odds_or_price": current_price,
                "movement": {
                    "price_change": round(current_price - previous_price, 4),
                    "spread_change": round(current_spread - previous_spread, 4),
                    "order_book_imbalance": imbalance,
                },
                "movement_strength": movement_strength,
                "edge_percent": min(16.0, movement_strength / 2.0),
                "confidence": 0.57,
                "liquidity": liquidity,
                "data_quality": 0.74,
                "market_depth": 0.72 if liquidity >= 0.5 else 0.4,
                "timing_signal": 0.8,
                "model_fit": 0.52,
                "risk_level_numeric": 0.5,
                "volatility_percent": min(50.0, movement_strength * 2),
                "source_consensus": 0.64,
                "execution_feasibility": 0.68,
                "expected_roi_percent": min(18.0, movement_strength / 1.5),
                "reason": "Prediction market movement detected for dry-run review.",
            }
        )
    return {
        "snapshot": {"provider": provider, "previous_count": len(previous_index), "current_count": len(current_index)},
        "candidates": candidates,
    }
