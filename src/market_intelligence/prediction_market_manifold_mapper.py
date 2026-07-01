from __future__ import annotations

from typing import Any

from src.market_intelligence.manifold import map_prediction_market as _map_prediction_market


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
    return _map_prediction_market(
        row,
        registry=registry,
        calibration_report=calibration_report,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )
