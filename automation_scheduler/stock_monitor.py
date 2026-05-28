from __future__ import annotations

from typing import Any


def _index_rows(rows: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or row.get("ticker") or "").upper()
        if symbol:
            indexed[symbol] = row
    return indexed


def monitor_stocks(
    *,
    previous_snapshot: list[dict[str, Any]] | None,
    current_snapshot: list[dict[str, Any]] | None,
    provider: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    previous_index = _index_rows(previous_snapshot)
    current_index = _index_rows(current_snapshot)
    candidates = []
    for symbol, current in current_index.items():
        previous = previous_index.get(symbol, {})
        current_price = float(current.get("price", 0) or 0)
        previous_price = float(previous.get("price", current_price) or current_price)
        price_move_pct = ((current_price - previous_price) / previous_price * 100) if previous_price else 0.0
        volume_ratio = float(current.get("volume_ratio", 1.0) or 1.0)
        volatility = float(current.get("volatility_percent", abs(price_move_pct)) or abs(price_move_pct))
        news_change = float(current.get("news_change_score", 0.0) or 0.0)
        movement_strength = abs(price_move_pct) + max(0.0, volume_ratio - 1.0) * 10 + abs(news_change)
        if movement_strength <= 0:
            continue
        candidates.append(
            {
                "source": "stock_monitor",
                "provider": provider,
                "market_type": "stocks_watchlist",
                "sport_or_symbol": symbol,
                "market": "equity_watch",
                "selection": symbol,
                "odds_or_price": current_price,
                "movement": {
                    "price_move_percent": round(price_move_pct, 4),
                    "volume_ratio": volume_ratio,
                    "news_change_score": news_change,
                },
                "movement_strength": movement_strength,
                "edge_percent": min(15.0, movement_strength / 2.0),
                "confidence": 0.55,
                "liquidity": float(current.get("liquidity", 0.8) or 0.8),
                "data_quality": 0.8,
                "market_depth": 0.85,
                "timing_signal": 0.72,
                "model_fit": 0.5,
                "risk_level_numeric": 0.48,
                "volatility_percent": volatility,
                "source_consensus": 0.62,
                "execution_feasibility": float(current.get("execution_feasibility", 0.9) or 0.9),
                "expected_roi_percent": min(20.0, abs(price_move_pct) * 2.0),
                "reason": "Stock movement detected for watchlist monitoring only.",
            }
        )
    return {
        "snapshot": {"provider": provider, "previous_count": len(previous_index), "current_count": len(current_index)},
        "candidates": candidates,
    }
