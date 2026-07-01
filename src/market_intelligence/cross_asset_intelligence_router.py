from __future__ import annotations

from typing import Any

from src.research.causal_scaffold import build_causal_scaffold_report
from .cross_asset_embedding_router import route_cross_asset_embedding
from .graph_relationship_mapper import map_graph_relationships
from src.security.policy import detect_execution_authority_violations, locked_safety_flags
from src.research import build_model_maturity_registry


def _fatal_safety_blockers(item: dict[str, Any]) -> list[str]:
    blockers = [
        str(reason)
        for reason in item.get("blockers", [])
        if "fatal" in str(reason).lower()
        or "execution" in str(reason).lower()
        or "provider_write" in str(reason).lower()
        or "secret" in str(reason).lower()
    ]
    violations = detect_execution_authority_violations(item)
    blockers.extend(f"security_policy:{violation}" for violation in violations)
    return sorted(set(blockers))


def route_cross_asset_intelligence(
    item: dict[str, Any] | None,
    *,
    historical_records: list[dict[str, Any]] | None = None,
    total_labeled_outcomes: int = 0,
    outcome_coverage_by_asset_type: dict[str, Any] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    source = dict(item or {})
    safety_blockers = _fatal_safety_blockers(source)
    embedding = route_cross_asset_embedding(
        source,
        historical_records=historical_records,
        base_data_dir=base_data_dir,
    )
    graph = map_graph_relationships(source)
    causal = build_causal_scaffold_report(records=historical_records or [])
    maturity = build_model_maturity_registry(
        total_labeled_outcomes=total_labeled_outcomes,
        outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,
    )
    manifold = dict(embedding.get("manifold_state") or {})
    graph_adjustment = float(graph.get("graph_review_adjustment", 0.0) or 0.0)
    manifold_adjustment = float(manifold.get("review_priority_adjustment", 0.0) or 0.0)
    raw_adjustment = round(manifold_adjustment + graph_adjustment, 2)
    if safety_blockers:
        final_review_adjustment = min(0.0, raw_adjustment) - 25.0
        affects_review_queue = False
        final_review_action = "NO_TRADE_SESSION_LOCK"
    else:
        final_review_adjustment = raw_adjustment
        affects_review_queue = str(manifold.get("recommended_action") or "") in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW", "LOW_PRIORITY_REVIEW"}
        final_review_action = str(manifold.get("recommended_action") or "DATA_INSUFFICIENT")
    payload = {
        "ok": True,
        "status": "cross_asset_intelligence_routed",
        "asset_type": embedding.get("asset_type"),
        "market_type": embedding.get("market_type"),
        "model_family": "hybrid_cross_asset_intelligence_stack",
        "model_name": "Hybrid Cross-Asset Intelligence Router",
        "model_maturity_status": "active_review" if not safety_blockers else "blocked_safety_review",
        "representation": {
            "representation_version": embedding.get("representation", {}).get("representation_version"),
            "embedding_kind": embedding.get("representation", {}).get("embedding_kind"),
            "embedding_dimension": embedding.get("representation", {}).get("embedding_dimension"),
            "normalized_scores": embedding.get("representation", {}).get("normalized_scores"),
            "missing_feature_count": embedding.get("representation", {}).get("missing_feature_count"),
        },
        "nearest_neighbor_summary": embedding.get("nearest_neighbor_summary", {}),
        "manifold_state": manifold,
        "graph_relationships": graph,
        "causal_scaffold": {
            "causal_status": causal.get("causal_status"),
            "total_hypotheses": causal.get("total_hypotheses"),
            "not_ready_count": causal.get("not_ready_count"),
            "high_confounding_risk_count": causal.get("high_confounding_risk_count"),
            "recommendation_impact_allowed": False,
        },
        "maturity_summary": {
            "total_models": maturity.get("total_models"),
            "active_review_count": maturity.get("active_review_count"),
            "active_calibration_count": maturity.get("active_calibration_count"),
            "calibration_only_count": maturity.get("calibration_only_count"),
            "research_only_count": maturity.get("research_only_count"),
            "blocked_count": maturity.get("blocked_count"),
        },
        "safety_blockers": safety_blockers,
        "fatal_safety_blockers": safety_blockers,
        "safety_override_applied": bool(safety_blockers),
        "final_review_action": final_review_action,
        "final_review_adjustment": round(final_review_adjustment, 2),
        "affects_review_queue": bool(affects_review_queue),
        "affects_execution": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
