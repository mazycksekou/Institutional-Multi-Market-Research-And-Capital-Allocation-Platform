from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, compact_list, normalize_text, safe_float
from .confidence import build_confidence_profile
from .flow import build_flow_summary
from .liquidity import build_liquidity_zones
from .prediction_markets import build_prediction_market_intelligence_report
from .report import build_market_intelligence_report
from .sports import build_sports_intelligence_report
from .targets import build_targets


FEATURE_VECTOR_VERSION = "market_intelligence_manifold_features_v1"
GRAPH_RELATIONSHIP_VERSION = "market_intelligence_market_state_graph_v1"

RELATIONSHIP_CATALOG: dict[str, list[dict[str, Any]]] = {
    "sportsbook": [
        {"path": ["player", "injury", "usage_change", "prop_line"], "hypothesis": "injury_confirmed_increases_player_usage", "fields": ["injury_news_score", "prop_context_score"]},
        {"path": ["team", "pace", "total", "player_points"], "hypothesis": "pace_up_increases_total_points_prop_hit_rate", "fields": ["game_script_score"]},
        {"path": ["team", "defensive_weakness", "player_stat_category"], "hypothesis": "defensive_weakness_increases_matching_prop_rate", "fields": ["prop_context_score"]},
    ],
    "prediction_market": [
        {"path": ["contract", "event", "settlement_rule", "liquidity_zone"], "hypothesis": "settlement_rule_uncertainty_changes_liquidity_quality", "fields": ["settlement_uncertainty_score", "liquidity_score"]},
        {"path": ["event", "news_catalyst", "price_movement"], "hypothesis": "news_catalyst_moves_contract_price", "fields": ["catalyst_score"]},
        {"path": ["market", "close_time", "settlement_uncertainty"], "hypothesis": "close_time_pressure_increases_settlement_uncertainty", "fields": ["close_time_pressure_score", "time_to_close_seconds"]},
        {"path": ["orderbook", "spread", "fake_edge_risk"], "hypothesis": "wide_spread_creates_fake_prediction_market_edge", "fields": ["bid_ask_spread", "spread_score"]},
    ],
    "stock": [
        {"path": ["company", "balance_sheet", "dilution_risk", "momentum_trap"], "hypothesis": "poor_balance_sheet_increases_dilution_trap_risk", "fields": ["balance_sheet_quality_score", "dilution_risk_score"]},
        {"path": ["catalyst", "volume_expansion", "breakout_candidate"], "hypothesis": "catalyst_volume_expansion_increases_breakout_follow_through", "fields": ["catalyst_quality_score", "relative_volume"]},
    ],
    "crypto": [
        {"path": ["funding", "leverage_pressure", "liquidation_risk"], "hypothesis": "funding_extreme_increases_crypto_reversal_risk", "fields": ["funding_rate", "liquidation_cluster_risk"]},
        {"path": ["open_interest", "squeeze_potential"], "hypothesis": "open_interest_expansion_increases_squeeze_potential", "fields": ["open_interest"]},
    ],
    "bond_rate": [
        {"path": ["macro_event", "yield_move", "etf_reaction"], "hypothesis": "macro_event_surprise_increases_bond_rate_volatility", "fields": ["macro_event_score", "yield_change"]},
        {"path": ["inflation_print", "policy_repricing"], "hypothesis": "inflation_print_changes_policy_repricing", "fields": ["inflation_repricing_score", "policy_repricing_score"]},
    ],
    "major_asset": [
        {"path": ["macro_event", "risk_on_risk_off", "major_asset_reaction"], "hypothesis": "macro_event_changes_risk_regime", "fields": ["macro_event_score", "risk_on_risk_off_score"]},
    ],
}


def infer_asset_type(item: Mapping[str, Any] | None) -> str:
    row = dict(item or {})
    text = normalize_text(row.get("asset_type") or row.get("asset_class") or row.get("market_type"))
    if "prediction" in text or "kalshi" in normalize_text(row.get("provider")):
        return "prediction_market"
    if text in {"sportsbook", "sports"} or row.get("sport") or row.get("league"):
        return "sportsbook"
    if text in {"crypto", "spot"} or row.get("funding_rate") is not None:
        return "crypto"
    if text in {"futures", "future"}:
        return "futures"
    if text in {"bond_rate", "rate", "rates"}:
        return "futures"
    return "stock"


def build_manifold_feature_vector(item: Mapping[str, Any] | None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    asset_type = infer_asset_type(data)
    confidence = clamp(data.get("confidence_score") or data.get("confidence") or 0.0)
    liquidity = clamp(data.get("liquidity_score") or 0.0)
    spread = clamp(data.get("spread_score") or data.get("bid_ask_spread") or 0.0)
    edge = clamp(data.get("estimated_edge") or 0.0)
    normalized = {
        "asset_type_prediction_market": 1.0 if asset_type == "prediction_market" else 0.0,
        "asset_type_sportsbook": 1.0 if asset_type == "sportsbook" else 0.0,
        "asset_type_crypto": 1.0 if asset_type == "crypto" else 0.0,
        "asset_type_futures": 1.0 if asset_type == "futures" else 0.0,
        "confidence_score": confidence / 100.0,
        "liquidity_score": liquidity / 100.0,
        "spread_score": spread / 100.0,
        "estimated_edge": edge / 100.0,
    }
    weighted = [round(value * 100.0, 4) for value in normalized.values()]
    return {
        "feature_vector_version": FEATURE_VECTOR_VERSION,
        "asset_type": asset_type,
        "normalized_features": normalized,
        "feature_vector": list(normalized.values()),
        "weighted_feature_vector": weighted,
    }


def nearest_historical_neighbors(feature_vector: Mapping[str, Any] | None, historical_records: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    records = [dict(row) for row in historical_records or [] if isinstance(row, Mapping)]
    sample = [row for row in records if row.get("final_outcome") is not None or row.get("return_pct") is not None]
    return {
        "nearest_historical_neighbors": len(sample) if feature_vector else 0,
        "nearest_neighbor_distance": 0.0 if sample else None,
        "neighbors": compact_list(sample, limit=10),
    }


def infer_graph_asset_type(item: Mapping[str, Any] | None) -> str:
    asset_type = infer_asset_type(item)
    return asset_type if asset_type in RELATIONSHIP_CATALOG else "stock"


def relationship_templates_for_item(item: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    asset_type = infer_graph_asset_type(item)
    return list(RELATIONSHIP_CATALOG.get(asset_type, []))


def build_market_state_graph(item: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    asset_type = infer_graph_asset_type(data)
    relationships = relationship_templates_for_item(data)
    payload = build_market_intelligence_report(
        {
            "market": asset_type,
            "symbol_or_event": data.get("symbol") or data.get("event") or "",
            "current_price_or_odds": data.get("price") or data.get("current_price") or data.get("yes_price"),
            "bias": "neutral",
            "confidence": clamp(data.get("confidence_score") or 0.0),
            "primary_target": data.get("primary_target") or len(relationships),
            "secondary_target": data.get("secondary_target") or len(relationships) + 1,
            "stretch_target": data.get("stretch_target") or len(relationships) + 2,
            "expected_move": data.get("expected_move") or 0.0,
            "support": data.get("support"),
            "resistance": data.get("resistance"),
            "liquidity_zones": data.get("liquidity_zones") or [],
            "positioning_summary": "Relationship graph computed locally; execution disabled.",
            "flow_summary": "graph-only",
            "catalysts": compact_list(data.get("catalysts") or [], limit=10),
            "trade_plan": "Review only; no live execution.",
            "risk": "low",
            "invalidation": data.get("invalidation") or "relationship templates change materially",
            "reasoning": [f"asset_type={asset_type}", f"relationship_count={len(relationships)}"],
            "no_trade_reason": "graph_only",
            "relationship_paths": relationships,
            "graph_node_count": len(relationships) + 1,
            "graph_edge_count": max(0, len(relationships) * 2),
            "graph_relationship_version": GRAPH_RELATIONSHIP_VERSION,
        }
    )
    payload["status"] = "market_state_graph_complete"
    payload["ok"] = True
    return payload


def nearest_historical_neighbors(feature_vector: Mapping[str, Any] | None, historical_records: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    vector = dict(feature_vector or {})
    records = [dict(row) for row in historical_records or [] if isinstance(row, Mapping)]
    sample = [row for row in records if row.get("final_outcome") is not None or row.get("return_pct") is not None]
    return {
        "nearest_historical_neighbors": len(sample) if vector else 0,
        "nearest_neighbor_distance": 0.0 if sample else None,
        "neighbors": compact_list(sample, limit=10),
    }


def map_prediction_market(item: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    data.setdefault("asset_type", "prediction_market")
    data.setdefault("market_type", "prediction_market")
    payload = build_prediction_market_intelligence_report(data)
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


def map_sportsbook_market(item: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    data.setdefault("asset_type", "sportsbook")
    data.setdefault("market_type", "sportsbook")
    payload = build_sports_intelligence_report(data)
    payload.update(
        {
            "ok": True,
            "status": "sportsbook_map_complete",
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


def map_market_state(item: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    asset_type = infer_asset_type(data)
    if asset_type == "prediction_market":
        return map_prediction_market(data)
    if asset_type == "sportsbook":
        return map_sportsbook_market(data)
    confidence = build_confidence_profile(data)
    liquidity = build_liquidity_zones(data)
    targets = build_targets(data)
    flow = build_flow_summary(data)
    payload = build_market_intelligence_report(
        {
            "market": asset_type,
            "symbol_or_event": data.get("symbol") or data.get("event") or data.get("market_type") or "",
            "current_price_or_odds": data.get("price") or data.get("current_price") or data.get("yes_price"),
            "bias": data.get("bias") or "neutral",
            "confidence": confidence["confidence"],
            "primary_target": targets["primary_target"],
            "secondary_target": targets["secondary_target"],
            "stretch_target": targets["stretch_target"],
            "expected_move": targets["expected_move"],
            "support": targets["support"],
            "resistance": targets["resistance"],
            "liquidity_zones": liquidity["liquidity_zones"],
            "positioning_summary": "Manifold state mapped locally; execution disabled.",
            "flow_summary": flow["flow_summary"],
            "catalysts": compact_list(data.get("catalysts") or [], limit=10),
            "trade_plan": "Review only; no live execution.",
            "risk": "low",
            "stop": data.get("stop"),
            "invalidation": data.get("invalidation") or "state shifts away from support/resistance",
            "reasoning": [f"asset_type={asset_type}", f"confidence={confidence['confidence']}"],
            "no_trade_reason": data.get("no_trade_reason") or "none",
        }
    )
    payload.update(
        {
            "ok": True,
            "status": "manifold_map_complete",
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


def compact_manifold_review_response(payload: Mapping[str, Any] | None = None, *, limit: int = 10) -> dict[str, Any]:
    data = dict(payload or {})
    sample = compact_list(data.get("sample_items") or data.get("items") or [], limit=limit)
    return {
        "ok": bool(data.get("ok", True)),
        "status": data.get("status", "manifold_review_complete"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "items_scanned": int(data.get("items_scanned", 0) or 0),
        "items_mapped": int(data.get("items_mapped", 0) or 0),
        "sample_items": sample,
        "storage_backend": data.get("storage_backend", "local"),
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_manifold_review_queue(
    items: list[Mapping[str, Any]] | None,
    *,
    registry: Mapping[str, Any] | None = None,
    calibration_report: Mapping[str, Any] | None = None,
    historical_records: list[Mapping[str, Any]] | None = None,
    base_data_dir: str = "data",
    persist: bool = False,
    max_items: int = 250,
) -> dict[str, Any]:
    rows = [dict(row) for row in (items or []) if isinstance(row, Mapping)][: max(1, min(int(max_items or 250), 1000))]
    mapped = [map_market_state(row, registry=registry, calibration_report=calibration_report, historical_records=historical_records, base_data_dir=base_data_dir) for row in rows]
    payload = {
        "ok": True,
        "status": "manifold_review_complete",
        "items_scanned": len(rows),
        "items_mapped": len(mapped),
        "sample_items": compact_list(mapped, limit=10),
        "items": mapped,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "storage_backend": "local",
        "raw_payload_included": False,
        "secrets_included": False,
    }
    return payload


def map_cross_asset_item(item: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    return map_market_state(data)


def route_cross_asset_embedding(item: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(item or {})
    data.update(overrides)
    feature_vector = build_manifold_feature_vector(data)
    state = map_cross_asset_item(data)
    neighbors = nearest_historical_neighbors(feature_vector, data.get("historical_records"))
    payload = build_market_intelligence_report(
        {
            "market": "cross_asset_embedding",
            "symbol_or_event": data.get("symbol") or data.get("event") or "",
            "current_price_or_odds": data.get("price") or data.get("current_price"),
            "bias": data.get("bias") or "neutral",
            "confidence": feature_vector["normalized_features"].get("confidence_score", 0.0) * 100.0,
            "primary_target": state.get("primary_target"),
            "secondary_target": state.get("secondary_target"),
            "stretch_target": state.get("stretch_target"),
            "expected_move": state.get("expected_move"),
            "support": state.get("support"),
            "resistance": state.get("resistance"),
            "liquidity_zones": state.get("liquidity_zones"),
            "positioning_summary": "Cross-asset manifold embedding only; execution disabled.",
            "flow_summary": state.get("flow_summary"),
            "catalysts": state.get("catalysts") or [],
            "trade_plan": "Review only; no live order/bet/trade submission.",
            "risk": "low",
            "stop": data.get("stop"),
            "invalidation": data.get("invalidation") or "manifold embedding degrades",
            "reasoning": [f"feature_vector_version={feature_vector['feature_vector_version']}", f"asset_type={feature_vector['asset_type']}"],
            "no_trade_reason": "embedding_only",
            "representation": feature_vector,
            "manifold_state": state,
            "nearest_neighbor_summary": {
                "nearest_historical_neighbors": int(neighbors.get("nearest_historical_neighbors", 0) or 0),
                "nearest_neighbor_distance": neighbors.get("nearest_neighbor_distance"),
                "neighbor_sample_size": len(neighbors.get("neighbors") or []),
            },
            "raw_payload_included": False,
            "secrets_included": False,
        }
    )
    payload.update(
        {
            "ok": True,
            "status": "cross_asset_embedding_routed",
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
