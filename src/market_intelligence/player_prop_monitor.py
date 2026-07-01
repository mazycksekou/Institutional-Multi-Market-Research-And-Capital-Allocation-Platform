from __future__ import annotations

from typing import Any


def _index_props(rows: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        key = "|".join(
            [
                str(row.get("player") or "player"),
                str(row.get("market") or "market"),
                str(row.get("selection") or "selection"),
            ]
        )
        indexed[key] = row
    return indexed


def monitor_player_props(
    *,
    previous_snapshot: list[dict[str, Any]] | None,
    current_snapshot: list[dict[str, Any]] | None,
    provider: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    previous_index = _index_props(previous_snapshot)
    current_index = _index_props(current_snapshot)
    candidates = []
    for key, current in current_index.items():
        previous = previous_index.get(key, {})
        current_line = float(current.get("line", 0) or 0)
        previous_line = float(previous.get("line", current_line) or current_line)
        current_odds = float(current.get("odds_american", 0) or 0)
        previous_odds = float(previous.get("odds_american", current_odds) or current_odds)
        movement_strength = abs(current_line - previous_line) * 12 + abs(current_odds - previous_odds)
        if movement_strength <= 0:
            continue
        liquidity = float(current.get("liquidity", 0.45) or 0.45)
        candidates.append(
            {
                "source": "player_prop_monitor",
                "provider": provider,
                "market_type": "sports_player_props",
                "sport_or_symbol": current.get("sport") or current.get("league") or "sports_props",
                "market": current.get("market", "player_prop"),
                "selection": current.get("selection") or current.get("player") or "unknown",
                "odds_or_price": current_odds,
                "movement": {
                    "line_change": round(current_line - previous_line, 4),
                    "odds_change": current_odds - previous_odds,
                },
                "movement_strength": movement_strength,
                "edge_percent": min(18.0, movement_strength / 10.0),
                "confidence": 0.52,
                "liquidity": liquidity,
                "data_quality": 0.85 if current.get("sample_size") else 0.55,
                "market_depth": 0.55,
                "timing_signal": 0.66,
                "model_fit": 0.56,
                "risk_level_numeric": 0.42,
                "volatility_percent": min(40.0, movement_strength),
                "source_consensus": 0.6,
                "execution_feasibility": 0.58,
                "expected_roi_percent": min(15.0, movement_strength / 4.0),
                "reason": "Player prop movement detected for manual review.",
            }
        )
    return {
        "snapshot": {"provider": provider, "previous_count": len(previous_index), "current_count": len(current_index)},
        "candidates": candidates,
    }
