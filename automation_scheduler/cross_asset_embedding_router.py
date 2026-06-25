from __future__ import annotations

from typing import Any

from src.market_intelligence.manifold import build_manifold_feature_vector, map_cross_asset_item, route_cross_asset_embedding as _route_cross_asset_embedding
from .representation_feature_builder import build_representation_vector
from .security_policy import locked_safety_flags


def route_cross_asset_embedding(
    item: dict[str, Any] | None,
    *,
    historical_records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    source = dict(item or {})
    payload = _route_cross_asset_embedding(
        source,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )
    payload["representation"] = build_representation_vector(source)
    payload["asset_type"] = payload.get("asset_type") or payload["representation"].get("asset_type")
    payload["market_type"] = payload.get("market_type") or payload["representation"].get("market_type")
    payload["manifold_state"] = dict(payload.get("manifold_state") or {})
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
