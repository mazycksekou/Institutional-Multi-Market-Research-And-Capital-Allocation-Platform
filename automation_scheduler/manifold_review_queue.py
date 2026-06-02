from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import get_storage_health, resolve_base_data_dir
from .market_state_manifold import map_market_state
from .scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso


MANIFOLD_REVIEW_QUEUE_SCHEMA_VERSION = f"{SCHEMA_VERSION}.market_state_manifold.review_queue.v1"


def _review_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "manifold" / "review_queue"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _review_dir(base_data_dir) / "latest.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def compact_manifold_item(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source_summary") if isinstance(item.get("source_summary"), dict) else {}
    return {
        "asset_symbol": source.get("asset_symbol"),
        "asset_type": item.get("asset_type"),
        "market_type": item.get("market_type"),
        "manifold_cluster_id": item.get("manifold_cluster_id"),
        "manifold_cluster_name": item.get("manifold_cluster_name"),
        "nearest_historical_neighbors": int(item.get("nearest_historical_neighbors", 0) or 0),
        "neighbor_sample_size": int(item.get("neighbor_sample_size", 0) or 0),
        "centroid_distance": item.get("centroid_distance"),
        "nearest_neighbor_distance": item.get("nearest_neighbor_distance"),
        "out_of_distribution_risk": item.get("out_of_distribution_risk"),
        "out_of_distribution_score": item.get("out_of_distribution_score"),
        "cluster_reliability_score": item.get("cluster_reliability_score"),
        "no_bet_trap_score": item.get("no_bet_trap_score"),
        "no_trade_trap_score": item.get("no_trade_trap_score"),
        "review_priority_adjustment": item.get("review_priority_adjustment"),
        "recommended_action": item.get("recommended_action"),
        "insufficient_sample": bool(item.get("insufficient_sample", True)),
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


def summarize_mapped_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    action_counts: dict[str, int] = {}
    for item in items:
        action = str(item.get("recommended_action") or "UNKNOWN")
        action_counts[action] = action_counts.get(action, 0) + 1
    return {
        "items_scanned": len(items),
        "items_mapped": len(items),
        "active_review_count": action_counts.get("ACTIVE_REVIEW", 0),
        "watchlist_review_count": action_counts.get("WATCHLIST_REVIEW", 0),
        "low_priority_review_count": action_counts.get("LOW_PRIORITY_REVIEW", 0),
        "no_review_count": action_counts.get("NO_REVIEW", 0),
        "data_insufficient_count": action_counts.get("DATA_INSUFFICIENT", 0),
        "no_bet_trap_count": len([item for item in items if bool(item.get("trap_cluster_detected")) and float(item.get("no_bet_trap_score") or 0.0) >= 65.0]),
        "no_trade_trap_count": len([item for item in items if bool(item.get("trap_cluster_detected")) and float(item.get("no_trade_trap_score") or 0.0) >= 65.0]),
        "out_of_distribution_count": len([item for item in items if item.get("out_of_distribution_risk") in {"high", "extreme"}]),
        "execution_allowed_count": 0,
        "action_counts": action_counts,
    }


def build_manifold_review_queue(
    items: list[dict[str, Any]] | None,
    *,
    registry: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
    persist: bool = False,
    max_items: int = 250,
) -> dict[str, Any]:
    rows = [row for row in (items or []) if isinstance(row, dict)][: max(1, min(int(max_items or 250), 1000))]
    mapped = [
        map_market_state(
            row,
            registry=registry,
            calibration_report=calibration_report,
            historical_records=historical_records,
            base_data_dir=base_data_dir,
        )
        for row in rows
    ]
    summary = summarize_mapped_items(mapped)
    payload = {
        "ok": True,
        "status": "manifold_review_complete",
        "schema_version": MANIFOLD_REVIEW_QUEUE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        **summary,
        "items": mapped,
        "sample_items": [compact_manifold_item(item) for item in mapped[:10]],
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
        "storage_backend": "file",
        "storage_health": get_storage_health(),
    }
    if persist:
        payload.update(write_manifold_review_queue(payload, base_data_dir=base_data_dir))
    return payload


def write_manifold_review_queue(payload: dict[str, Any], *, base_data_dir: str = "data") -> dict[str, Any]:
    safe_items = [compact_manifold_item(item) for item in payload.get("items", []) if isinstance(item, dict)]
    safe_payload = dict(payload)
    safe_payload["items"] = safe_items
    safe_payload["sample_items"] = safe_items[:10]
    safe_payload["provider_write"] = False
    safe_payload["execution_allowed"] = False
    safe_payload["live_execution_enabled"] = False
    safe_payload["human_approval_required"] = True
    safe_payload["auto_execution"] = False
    safe_payload["auto_execution_enabled"] = False
    safe_payload["actual_orders_submitted"] = 0
    safe_payload["actual_bets_submitted"] = 0
    safe_payload["actual_trades_submitted"] = 0
    latest = _latest_path(base_data_dir)
    history = _review_dir(base_data_dir) / f"{sanitize_filename(utc_now_iso()[:10])}.json"
    _atomic_write_json(latest, safe_payload)
    _atomic_write_json(history, safe_payload)
    return {
        "storage_backend": "file",
        "manifold_review_queue_path": _project_relative_path(base_data_dir, latest),
        "manifold_review_queue_history_path": _project_relative_path(base_data_dir, history),
    }


def load_manifold_review_queue(*, base_data_dir: str = "data") -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    if isinstance(payload, dict):
        payload["storage_health"] = get_storage_health()
        return payload
    return {
        "ok": True,
        "status": "empty",
        "items_scanned": 0,
        "items_mapped": 0,
        "active_review_count": 0,
        "watchlist_review_count": 0,
        "no_bet_trap_count": 0,
        "out_of_distribution_count": 0,
        "sample_items": [],
        "items": [],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "human_approval_required": True,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "storage_backend": "file",
        "storage_health": get_storage_health(),
    }


def compact_manifold_review_response(payload: dict[str, Any], *, limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    sample = payload.get("sample_items")
    if not isinstance(sample, list):
        sample = [compact_manifold_item(item) for item in payload.get("items", []) if isinstance(item, dict)]
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "manifold_review_complete"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "items_scanned": int(payload.get("items_scanned", 0) or 0),
        "items_mapped": int(payload.get("items_mapped", 0) or 0),
        "active_review_count": int(payload.get("active_review_count", 0) or 0),
        "watchlist_review_count": int(payload.get("watchlist_review_count", 0) or 0),
        "low_priority_review_count": int(payload.get("low_priority_review_count", 0) or 0),
        "no_review_count": int(payload.get("no_review_count", 0) or 0),
        "data_insufficient_count": int(payload.get("data_insufficient_count", 0) or 0),
        "no_bet_trap_count": int(payload.get("no_bet_trap_count", 0) or 0),
        "no_trade_trap_count": int(payload.get("no_trade_trap_count", 0) or 0),
        "out_of_distribution_count": int(payload.get("out_of_distribution_count", 0) or 0),
        "execution_allowed_count": 0,
        "sample_items": sample[:cap],
        "storage_backend": payload.get("storage_backend", "file"),
        "storage": payload.get("storage_health"),
        "raw_payload_included": False,
    }
