from __future__ import annotations

from typing import Any

from .market_state_manifold import map_market_state


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
    return map_market_state(
        row,
        registry=registry,
        calibration_report=calibration_report,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )
