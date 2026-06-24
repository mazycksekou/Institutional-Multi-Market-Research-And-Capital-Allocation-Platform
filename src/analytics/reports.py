from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def build_model_validation_report(model_id: str, activation_tier: str, **sections: Any) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "activation_tier": activation_tier,
        "evidence_summary": sections.get("evidence_summary", {}),
        "test_summary": sections.get("test_summary", {}),
        "input_quality_summary": sections.get("input_quality_summary", {}),
        "calibration_summary": sections.get("calibration_summary", {}),
        "backtest_summary": sections.get("backtest_summary", {}),
        "paper_tracking_summary": sections.get("paper_tracking_summary", {}),
        "clv_summary": sections.get("clv_summary", {}),
        "walk_forward_summary": sections.get("walk_forward_summary", {}),
        "risk_summary": sections.get("risk_summary", {}),
        "Kelly_summary": sections.get("Kelly_summary", {}),
        "cross_book_summary": sections.get("cross_book_summary", {}),
        "settlement_liquidity_summary": sections.get("settlement_liquidity_summary", {}),
        "challenger_summary": sections.get("challenger_summary", {}),
        "promotion_recommendation": sections.get("promotion_recommendation", "review_required"),
        "blocked_reasons": list(sections.get("blocked_reasons", [])),
        "human_approval_required": True,
    }


def generate_governance_report(
    inventory: Iterable[Mapping[str, Any]],
    counts: Mapping[str, Any],
    *,
    audit_records: Iterable[Any] | None = None,
) -> dict[str, Any]:
    inventory_list = [dict(item) for item in inventory]
    inventory_counts = dict(counts)
    blocked = [
        item
        for item in inventory_list
        if item.get("activation_tier") in {"research_only", "backtest_ready", "paper_trade_ready"}
    ]
    audit_entries = list(audit_records or ())
    return {
        "inventory_summary": {"total": len(inventory_list)},
        "tier_counts": inventory_counts,
        "blocked_model_count": len(blocked),
        "eligible_model_count": len(inventory_list) - len(blocked),
        "models_needing_validation": [item["model_id"] for item in blocked],
        "models_with_drift": [],
        "models_blocked_by_input_quality": [],
        "models_blocked_by_risk": [],
        "models_blocked_by_settlement": [],
        "models_blocked_by_Kelly": [],
        "audit_summary": {"records": len(audit_entries)},
        "recommended_next_actions": ["review_required"],
    }

