from __future__ import annotations

from typing import Any

from src.market_intelligence.manifold_feature_builder import build_manifold_feature_vector
from src.market_intelligence.cross_asset_manifold_router import map_cross_asset_item
from src.research.representation_feature_builder import build_representation_vector
from src.security.policy import locked_safety_flags


def route_cross_asset_embedding(
    item: dict[str, Any] | None,
    *,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    source = dict(item or {})
    feature_vector = build_manifold_feature_vector(source)
    state = map_cross_asset_item(source, historical_records=historical_records, base_data_dir=base_data_dir)
    payload = {
        "ok": True,
        "status": "cross_asset_embedding_routed",
        "representation": build_representation_vector(source),
        "asset_type": state.get("asset_type") or feature_vector.get("asset_type"),
        "market_type": state.get("market_type") or feature_vector.get("market_type"),
        "manifold_state": dict(state or {}),
        "nearest_neighbor_summary": {
            "nearest_historical_neighbors": int(state.get("nearest_historical_neighbors", 0) or 0),
            "nearest_neighbor_distance": state.get("nearest_neighbor_distance"),
            "neighbor_sample_size": len(state.get("neighbors") or []),
        },
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
    }
    payload["representation"] = build_representation_vector(source)
    payload["asset_type"] = payload.get("asset_type") or payload["representation"].get("asset_type")
    payload["market_type"] = payload.get("market_type") or payload["representation"].get("market_type")
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
