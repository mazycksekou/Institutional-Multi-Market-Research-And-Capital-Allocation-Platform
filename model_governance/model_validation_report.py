from __future__ import annotations

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
