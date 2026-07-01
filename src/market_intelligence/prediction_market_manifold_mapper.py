from __future__ import annotations

from typing import Any

from src.market_intelligence.prediction_markets import build_prediction_market_intelligence_report


def map_prediction_market(
    item: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    row = dict(item or {})
    row.setdefault("asset_type", "prediction_market")
    row.setdefault("market_type", "prediction_market")
    payload = build_prediction_market_intelligence_report(row)
    payload.update(
        {
            "ok": True,
            "status": "prediction_market_map_complete",
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    )
    return payload
