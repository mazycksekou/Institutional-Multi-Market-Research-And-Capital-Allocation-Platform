from __future__ import annotations

from typing import Any

from .candlestick_manifold_detector import map_candlestick_context
from src.analytics.manifold_calibration import build_manifold_calibration_report, load_manifold_calibration_report
from .manifold_cluster_registry import compact_cluster_registry, load_cluster_registry
from src.services.execution_service import compact_trap_report, load_trap_report, write_trap_report
from src.analytics.manifold_review_queue import build_manifold_review_queue, compact_manifold_review_response
from .market_state_manifold import map_market_state
from .prediction_market_manifold_mapper import map_prediction_market
from src.providers.sportsbook_manifold_mapper import map_sportsbook_full_board, map_sportsbook_market


def _asset_type(item: dict[str, Any]) -> str:
    text = str(item.get("asset_type") or item.get("asset_class") or item.get("market_type") or "").lower()
    if "prediction" in text or "kalshi" in str(item.get("provider") or "").lower():
        return "prediction_market"
    if text in {"sportsbook", "sports"} or item.get("sport") or item.get("league"):
        return "sportsbook"
    if text in {"stock", "equity"}:
        return "stock"
    if text == "crypto" or item.get("funding_rate") is not None:
        return "crypto"
    if text in {"bond", "bonds", "rate", "rates", "bond_rate", "fixed_income"}:
        return "bond_rate"
    if text == "etf":
        return "etf"
    if text in {"major_asset", "macro"}:
        return "major_asset"
    return "stock"


def map_cross_asset_item(
    item: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    asset_type = _asset_type(item)
    if asset_type == "prediction_market":
        return map_prediction_market(
            item,
            registry=registry,
            calibration_report=calibration_report,
            historical_records=historical_records,
            base_data_dir=base_data_dir,
        )
    if asset_type == "sportsbook":
        return map_sportsbook_market(
            item,
            registry=registry,
            calibration_report=calibration_report,
            historical_records=historical_records,
            base_data_dir=base_data_dir,
        )
    if item.get("candlestick_pattern_id") or item.get("pattern_id"):
        return map_candlestick_context(
            item,
            registry=registry,
            calibration_report=calibration_report,
            historical_records=historical_records,
            base_data_dir=base_data_dir,
        )
    return map_market_state(
        item,
        registry=registry,
        calibration_report=calibration_report,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )


def run_cross_asset_manifold_review(
    items: list[dict[str, Any]] | None,
    *,
    historical_records: list[dict[str, Any]] | None = None,
    persist: bool = True,
    base_data_dir: str = "data",
    max_items: int = 250,
) -> dict[str, Any]:
    registry = load_cluster_registry(base_data_dir=base_data_dir, create_if_missing=True)
    calibration = load_manifold_calibration_report(base_data_dir=base_data_dir)
    queue = build_manifold_review_queue(
        items,
        registry=registry,
        calibration_report=calibration,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
        persist=persist,
        max_items=max_items,
    )
    traps = [item for item in queue.get("items", []) if isinstance(item, dict) and bool(item.get("trap_cluster_detected"))]
    if persist:
        queue.update(write_trap_report(traps, base_data_dir=base_data_dir))
    return queue


def map_manifold_endpoint_item(
    item: dict[str, Any],
    *,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    registry = load_cluster_registry(base_data_dir=base_data_dir, create_if_missing=True)
    calibration = load_manifold_calibration_report(base_data_dir=base_data_dir)
    return {
        "ok": True,
        "status": "manifold_map_complete",
        "item": map_cross_asset_item(
            item,
            registry=registry,
            calibration_report=calibration,
            historical_records=historical_records,
            base_data_dir=base_data_dir,
        ),
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


def get_manifold_cluster_snapshot(*, base_data_dir: str = "data", limit: int = 25) -> dict[str, Any]:
    return compact_cluster_registry(load_cluster_registry(base_data_dir=base_data_dir, create_if_missing=True), limit=limit)


def get_manifold_calibration_snapshot(*, base_data_dir: str = "data", limit: int = 25) -> dict[str, Any]:
    report = build_manifold_calibration_report(base_data_dir=base_data_dir, write_report=True)
    from src.analytics.manifold_calibration import compact_manifold_calibration_report

    return compact_manifold_calibration_report(report, limit=limit)


def get_manifold_trap_snapshot(*, base_data_dir: str = "data", limit: int = 25) -> dict[str, Any]:
    return compact_trap_report(load_trap_report(base_data_dir=base_data_dir), limit=limit)


def compact_cross_asset_review(payload: dict[str, Any], *, limit: int = 10) -> dict[str, Any]:
    return compact_manifold_review_response(payload, limit=limit)


def map_sportsbook_board(
    items: list[dict[str, Any]] | None,
    *,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    registry = load_cluster_registry(base_data_dir=base_data_dir, create_if_missing=True)
    calibration = load_manifold_calibration_report(base_data_dir=base_data_dir)
    return map_sportsbook_full_board(items, registry=registry, calibration_report=calibration, base_data_dir=base_data_dir)
