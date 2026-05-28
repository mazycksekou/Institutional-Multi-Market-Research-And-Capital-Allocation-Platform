from __future__ import annotations

from typing import Any


def compare_champion_challenger(
    *,
    champion_metrics: dict[str, float],
    challenger_metrics: dict[str, float],
    promotion_gate_approved: bool,
    minimum_sample_size: int = 100,
) -> dict[str, Any]:
    champion_wins = 0
    challenger_wins = 0
    comparisons = {
        "calibration": challenger_metrics.get("calibration", 0.0) - champion_metrics.get("calibration", 0.0),
        "clv": challenger_metrics.get("clv", 0.0) - champion_metrics.get("clv", 0.0),
        "drawdown": champion_metrics.get("drawdown", 1.0) - challenger_metrics.get("drawdown", 1.0),
        "roi_reality": challenger_metrics.get("roi_reality", 0.0) - champion_metrics.get("roi_reality", 0.0),
        "stale_data_sensitivity": champion_metrics.get("stale_data_sensitivity", 1.0) - challenger_metrics.get("stale_data_sensitivity", 1.0),
        "risk_adjusted_performance": challenger_metrics.get("risk_adjusted_performance", 0.0) - champion_metrics.get("risk_adjusted_performance", 0.0),
    }
    for delta in comparisons.values():
        if delta > 0:
            challenger_wins += 1
        elif delta < 0:
            champion_wins += 1
    sample_size = int(challenger_metrics.get("sample_size", 0))
    if sample_size < minimum_sample_size:
        decision = "needs_more_data"
    elif challenger_wins >= 5 and promotion_gate_approved:
        decision = "challenger_promoted"
    elif challenger_wins >= 4 and not promotion_gate_approved:
        decision = "needs_more_data"
    elif champion_wins >= challenger_wins:
        decision = "champion_kept"
    else:
        decision = "challenger_rejected"
    return {
        "decision": decision,
        "champion_kept": decision == "champion_kept",
        "challenger_promoted": decision == "challenger_promoted",
        "challenger_rejected": decision == "challenger_rejected",
        "needs_more_data": decision == "needs_more_data",
        "comparisons": comparisons,
        "promotion_gate_approved": bool(promotion_gate_approved),
    }

