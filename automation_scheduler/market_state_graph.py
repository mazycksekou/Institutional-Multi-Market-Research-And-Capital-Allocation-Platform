from __future__ import annotations

from typing import Any

from src.market_intelligence.manifold import GRAPH_RELATIONSHIP_VERSION, infer_graph_asset_type as _infer_graph_asset_type, relationship_templates_for_item as _relationship_templates_for_item


def infer_graph_asset_type(item: dict[str, Any] | None) -> str:
    return _infer_graph_asset_type(item)


def relationship_templates_for_item(item: dict[str, Any] | None) -> list[dict[str, Any]]:
    return _relationship_templates_for_item(item)
