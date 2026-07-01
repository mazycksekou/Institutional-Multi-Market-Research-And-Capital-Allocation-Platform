from __future__ import annotations

from typing import Any

from .market_state_manifold import map_market_state


def map_candlestick_context(
    item: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    row = dict(item or {})
    row.setdefault("asset_type", row.get("asset_class") or "stock")
    result = map_market_state(
        row,
        registry=registry,
        calibration_report=calibration_report,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )
    pattern_quality = result.get("normalized_feature_summary", {}).get("pattern_quality_score")
    if pattern_quality is None:
        pattern_quality = row.get("pattern_quality_score")
    reliability = float(result.get("cluster_reliability_score") or 0.0)
    trap = max(float(result.get("no_trade_trap_score") or 0.0), float(result.get("no_bet_trap_score") or 0.0))
    result.update(
        {
            "pattern_id": row.get("pattern_id") or row.get("candlestick_pattern_id"),
            "pattern_quality_score": row.get("pattern_quality_score"),
            "candle_context_cluster": result.get("manifold_cluster_name"),
            "liquidity_context_cluster": result.get("liquidity_quality"),
            "historical_pattern_cluster_performance": {
                "historical_win_rate": result.get("historical_win_rate"),
                "historical_roi": result.get("historical_roi"),
                "insufficient_sample": result.get("insufficient_sample"),
            },
            "pattern_context_reliability_score": round(max(0.0, reliability - trap * 0.25), 2),
            "candlestick_manifold_adjustment": result.get("review_priority_adjustment"),
            "execution_allowed": False,
            "provider_write": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        }
    )
    return result
