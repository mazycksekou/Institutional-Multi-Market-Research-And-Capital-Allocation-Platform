from __future__ import annotations

from typing import Any

from src.services.snapshot_store import SnapshotStore


def _index_rows(rows: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        key = "|".join(
            [
                str(row.get("event_id") or row.get("event") or "event"),
                str(row.get("market") or "market"),
                str(row.get("selection") or "selection"),
            ]
        )
        indexed[key] = row
    return indexed


def monitor_odds_lines(
    *,
    previous_snapshot: list[dict[str, Any]] | None,
    current_snapshot: list[dict[str, Any]] | None,
    provider: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    previous_index = _index_rows(previous_snapshot)
    current_index = _index_rows(current_snapshot)
    candidates = []
    for key, current in current_index.items():
        previous = previous_index.get(key, {})
        current_odds = float(current.get("odds_american", 0) or 0)
        previous_odds = float(previous.get("odds_american", current_odds) or current_odds)
        current_line = float(current.get("line", 0) or 0)
        previous_line = float(previous.get("line", current_line) or current_line)
        books = list(current.get("books") or [])
        disagreement = 0.0
        if books:
            prices = [float(book.get("odds_american", current_odds) or current_odds) for book in books if isinstance(book, dict)]
            if prices:
                disagreement = abs(max(prices) - min(prices))
        movement_strength = abs(current_odds - previous_odds) + (abs(current_line - previous_line) * 10)
        steam = movement_strength >= 20
        reverse = bool(current.get("public_betting_percent", 0) > 65 and current_odds > previous_odds)
        if movement_strength <= 0 and disagreement <= 0:
            continue
        candidates.append(
            {
                "source": "odds_line_monitor",
                "provider": provider,
                "market_type": "sports_pregame_main",
                "sport_or_symbol": current.get("sport") or current.get("league") or "sports",
                "market": current.get("market", "unknown"),
                "selection": current.get("selection", "unknown"),
                "odds_or_price": current_odds,
                "movement": {
                    "odds_change": current_odds - previous_odds,
                    "line_change": round(current_line - previous_line, 4),
                    "steam": steam,
                    "reverse_movement": reverse,
                    "book_disagreement": disagreement,
                },
                "movement_strength": movement_strength,
                "edge_percent": min(20.0, disagreement / 10.0 + movement_strength / 8.0),
                "confidence": 0.58 if steam else 0.48,
                "liquidity": 0.65 if books else 0.45,
                "data_quality": 0.8 if previous else 0.55,
                "market_depth": 0.7 if len(books) >= 3 else 0.45,
                "timing_signal": 0.75 if steam else 0.55,
                "model_fit": 0.5,
                "risk_level_numeric": 0.45 if reverse else 0.35,
                "volatility_percent": min(50.0, movement_strength),
                "source_consensus": 0.7 if disagreement >= 15 else 0.5,
                "execution_feasibility": 0.65,
                "expected_roi_percent": min(18.0, movement_strength / 2.5),
                "reason": "Monitor odds movement and book disagreement for human review.",
            }
        )
    return {
        "snapshot": {
            "provider": provider,
            "previous_count": len(previous_index),
            "current_count": len(current_index),
            "candidates": len(candidates),
            "diff": SnapshotStore.diff_snapshots(
                {"payload": previous_index},
                {"payload": current_index},
            ),
        },
        "candidates": candidates,
    }
