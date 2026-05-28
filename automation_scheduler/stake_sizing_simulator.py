from __future__ import annotations

from typing import Any

_PROFILE_MULTIPLIERS = {
    "conservative": 0.01,
    "standard": 0.02,
    "aggressive": 0.03,
}

_RISK_CAPS = {
    "low": 0.01,
    "medium": 0.02,
    "high": 0.03,
}


def simulate_stake_plan(
    candidate: dict[str, Any],
    *,
    bankroll: float,
    risk_profile: str = "medium",
) -> dict[str, Any]:
    bankroll_value = max(0.0, float(bankroll))
    risk_cap = _RISK_CAPS.get(str(risk_profile).lower(), 0.02)
    total_cap = bankroll_value * risk_cap
    candidate_type = candidate.get("candidate_type") or "positive_ev"
    base_roi = float(candidate.get("estimated_roi_percent") or candidate.get("ev_percent") or 0.0)
    max_gain = float(candidate.get("max_gain") or 0.0)
    max_loss = float(candidate.get("max_loss") or total_cap)

    plans = []
    for profile, multiplier in _PROFILE_MULTIPLIERS.items():
        suggested_stake = round(min(bankroll_value * multiplier, total_cap), 2)
        expected_value = round(suggested_stake * (base_roi / 100.0), 4)
        if candidate_type == "arbitrage_candidate" and candidate.get("stake_plan"):
            total_candidate_stake = sum(float(item.get("stake", 0)) for item in candidate["stake_plan"]) or 1.0
            scaled_plan = []
            for item in candidate["stake_plan"]:
                scaled = suggested_stake * (float(item.get("stake", 0)) / total_candidate_stake)
                scaled_plan.append({**item, "stake": round(scaled, 2)})
            plan_value = scaled_plan
        else:
            plan_value = [{"selection": candidate.get("selection"), "stake": suggested_stake}]
        plans.append(
            {
                "profile": profile,
                "suggested_stake": suggested_stake,
                "stake_plan": plan_value,
                "max_loss": round(min(total_cap, max_loss if max_loss > 0 else suggested_stake), 2),
                "max_gain": round(max(max_gain, expected_value), 2),
                "expected_value": expected_value,
                "expected_roi": round(base_roi, 4),
                "review_only": True,
                "human_approval_required": True,
                "auto_execution_enabled": False,
            }
        )

    return {
        "candidate_type": candidate_type,
        "bankroll": bankroll_value,
        "risk_profile": risk_profile,
        "risk_cap": round(total_cap, 2),
        "profiles": plans,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
    }
