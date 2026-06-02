from __future__ import annotations

from typing import Any

from .manifold_feature_builder import build_manifold_feature_vector
from .market_state_manifold import nearest_historical_neighbors
from .cross_asset_manifold_router import map_cross_asset_item
from .representation_feature_builder import build_representation_vector
from .security_policy import locked_safety_flags


def route_cross_asset_embedding(
    item: dict[str, Any] | None,
    *,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    source = dict(item or {})
    representation = build_representation_vector(source)
    manifold_features = build_manifold_feature_vector(source)
    neighbors = nearest_historical_neighbors(manifold_features, historical_records or [])
    manifold_state = map_cross_asset_item(
        source,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )
    payload = {
        "ok": True,
        "status": "cross_asset_embedding_routed",
        "asset_type": representation.get("asset_type"),
        "market_type": representation.get("market_type"),
        "representation": representation,
        "nearest_neighbor_summary": {
            "nearest_historical_neighbors": int(neighbors.get("nearest_historical_neighbors", 0) or 0),
            "nearest_neighbor_distance": neighbors.get("nearest_neighbor_distance"),
            "neighbor_sample_size": len(neighbors.get("neighbors") or []),
        },
        "manifold_state": {
            "manifold_cluster_id": manifold_state.get("manifold_cluster_id"),
            "manifold_cluster_name": manifold_state.get("manifold_cluster_name"),
            "manifold_family": manifold_state.get("manifold_family"),
            "out_of_distribution_score": manifold_state.get("out_of_distribution_score"),
            "out_of_distribution_risk": manifold_state.get("out_of_distribution_risk"),
            "calibration_status": manifold_state.get("calibration_status"),
            "insufficient_sample": bool(manifold_state.get("insufficient_sample", True)),
            "recommended_action": manifold_state.get("recommended_action"),
            "review_priority_adjustment": manifold_state.get("review_priority_adjustment"),
            "no_bet_trap_score": manifold_state.get("no_bet_trap_score"),
            "no_trade_trap_score": manifold_state.get("no_trade_trap_score"),
            "fatal_safety_blockers": list(manifold_state.get("fatal_safety_blockers") or [])[:10],
        },
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def route_embedding_batch(
    items: list[dict[str, Any]] | None,
    *,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
    limit: int = 250,
) -> dict[str, Any]:
    cap = max(1, min(int(limit or 250), 1000))
    routed = [
        route_cross_asset_embedding(item, historical_records=historical_records, base_data_dir=base_data_dir)
        for item in (items or [])[:cap]
        if isinstance(item, dict)
    ]
    payload = {
        "ok": True,
        "status": "cross_asset_embedding_batch_routed",
        "items_received": len(items or []),
        "items_routed": len(routed),
        "items": routed,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
