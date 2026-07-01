from __future__ import annotations

from typing import Any


def evaluate_risk_of_ruin(inputs: dict[str, Any]) -> dict[str, Any]:
    losing_streak_risk = float(inputs.get("estimated_losing_streak_risk", 0))
    survival = float(inputs.get("bankroll_survival_score", 100))
    ruin_score = max(0.0, min(100.0, ((losing_streak_risk * 0.6) + ((100.0 - survival) * 0.4))))
    if ruin_score >= 80:
        status = "severe"
    elif ruin_score >= 60:
        status = "high"
    elif ruin_score >= 40:
        status = "medium"
    else:
        status = "low"
    return {
        "estimated_losing_streak_risk": losing_streak_risk,
        "bankroll_survival_score": survival,
        "ruin_risk_score": round(ruin_score, 2),
        "risk_of_ruin_status": status,
        "full_kelly_blocked": status in {"high", "severe"},
        "no_stake_required": status == "severe",
        "stress_test_bankroll_path": "placeholder",
    }
