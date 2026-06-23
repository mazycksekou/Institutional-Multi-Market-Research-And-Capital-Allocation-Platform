"""Bankroll and exposure risk calculations (stateless helpers)."""
from __future__ import annotations

from typing import Any, Optional

from src.core.clv import average_clv as _core_average_clv
from src.core.math_utils import calculate_kelly_stake


RISK_PROFILE_SETTINGS = {
    "conservative": {"risk_profile": "conservative", "kelly_fraction": 0.125, "max_bankroll_pct": 0.01, "confidence_multiplier": 0.75},
    "standard": {"risk_profile": "standard", "kelly_fraction": 0.25, "max_bankroll_pct": 0.02, "confidence_multiplier": 1.0},
    "aggressive": {"risk_profile": "aggressive", "kelly_fraction": 0.5, "max_bankroll_pct": 0.03, "confidence_multiplier": 1.15},
}

EXPOSURE_LIMITS = {
    "max_single_bet_bankroll_percent": 5.0,
    "max_single_trade_portfolio_percent": 5.0,
    "max_daily_kelly_exposure_percent": 12.0,
    "max_weekly_kelly_exposure_percent": 25.0,
    "max_market_group_exposure_percent": 10.0,
    "portfolio_kelly_cap": 25.0,
    "correlation_exposure_cap": 10.0,
}

STAKE_PROFILE_MULTIPLIERS = {
    "conservative": 0.01,
    "standard": 0.02,
    "aggressive": 0.03,
}

STAKE_RISK_CAPS = {
    "low": 0.01,
    "medium": 0.02,
    "high": 0.03,
}


def bankroll_percentage_risked(stake: float, bankroll: float) -> float:
    if bankroll <= 0:
        return 0.0
    return max(0.0, min(1.0, stake / bankroll))


def exposure_single_bet(stake: float) -> float:
    return max(0.0, float(stake))


def exposure_daily(stakes: list[float]) -> float:
    return sum(max(0.0, s) for s in stakes)


def exposure_by_key(stakes_by_key: dict[str, float], key: str) -> float:
    return max(0.0, float(stakes_by_key.get(key, 0.0)))


def correlation_group_exposure(stakes_by_group: dict[str, float], group: str) -> float:
    return exposure_by_key(stakes_by_group, group)


def max_loss_correlated_bets(stakes: list[float], correlation_matrix_max: float = 1.0) -> float:
    """Upper bound if all legs lose together."""
    if not stakes:
        return 0.0
    return sum(stakes) * min(1.0, max(0.0, correlation_matrix_max))


def drawdown_tracker(equity_series: list[float]) -> dict[str, Any]:
    if not equity_series:
        return {"max_drawdown_pct": None, "current_drawdown_pct": None}
    peak = equity_series[0]
    max_dd = 0.0
    for x in equity_series:
        peak = max(peak, x)
        dd = (peak - x) / peak if peak else 0.0
        max_dd = max(max_dd, dd)
    cur_peak = max(equity_series)
    cur = equity_series[-1]
    cur_dd = (cur_peak - cur) / cur_peak if cur_peak else 0.0
    return {"max_drawdown_pct": round(max_dd * 100, 2), "current_drawdown_pct": round(cur_dd * 100, 2)}


def risk_of_ruin_estimate(
    win_prob: float,
    payoff_ratio: float,
    bankroll_units: float,
    units_risked: float,
    trials: int = 1000,
) -> float:
    """
    Very rough Monte-Carlo-free upper bound using gambler's ruin approximation for even bets.
    For production use simulation. Returns approximate probability (0-1).
    """
    if win_prob <= 0 or win_prob >= 1 or bankroll_units <= 0 or units_risked <= 0:
        return 1.0
    q = 1 - win_prob
    if abs(payoff_ratio - 1) < 1e-9:
        try:
            r = q / win_prob
            if r >= 1:
                return min(1.0, (q / win_prob) ** bankroll_units)
        except Exception:
            pass
    return min(1.0, max(0.0, (1 - win_prob) ** 10))


def risk_profile_settings(risk_profile: str | None = "standard") -> dict[str, float | str]:
    return RISK_PROFILE_SETTINGS.get((risk_profile or "standard").strip().lower(), RISK_PROFILE_SETTINGS["standard"]).copy()


def confidence_adjusted_stake(base_stake: float, confidence_0_100: float) -> float:
    confidence = max(0.0, min(100.0, float(confidence_0_100))) / 100.0
    return max(0.0, float(base_stake) * confidence)


def risk_adjusted_stake(base_stake: float, risk_multiplier: float) -> float:
    multiplier = max(0.0, min(1.0, float(risk_multiplier)))
    return max(0.0, float(base_stake) * multiplier)


def suggested_stake(
    bankroll: float,
    american_odds: int | float,
    true_probability: float,
    fractional_kelly: float = 0.25,
    max_bankroll_pct: float = 0.02,
) -> float:
    return calculate_kelly_stake(
        bankroll,
        american_odds,
        true_probability,
        fraction=fractional_kelly,
        max_bankroll_pct=max_bankroll_pct,
    )


def suggested_bet_size(
    bankroll: float,
    kelly: float,
    fractional_kelly: float = 0.25,
    max_bankroll_risk: float = 0.02,
) -> float:
    stake = float(bankroll) * float(kelly) * float(fractional_kelly)
    return max(0.0, min(stake, float(bankroll) * float(max_bankroll_risk)))


def suggested_stake_with_risk_controls(
    bankroll: float,
    american_odds: int | float,
    true_probability: float,
    risk_profile: str | None = "standard",
    confidence_0_100: float | None = None,
) -> float:
    profile = risk_profile_settings(risk_profile)
    stake = suggested_stake(
        bankroll,
        american_odds,
        true_probability,
        fractional_kelly=float(profile["kelly_fraction"]),
        max_bankroll_pct=float(profile["max_bankroll_pct"]),
    )
    if confidence_0_100 is not None:
        stake = confidence_adjusted_stake(stake, confidence_0_100)
    return round(stake, 2)


def exposure_check(
    bankroll: float,
    suggested_stake: float,
    current_group_exposure: float,
    group_exposure_cap: float = 0.05,
) -> dict[str, Any]:
    max_group_exposure = float(bankroll) * float(group_exposure_cap)
    projected_group_exposure = float(current_group_exposure) + float(suggested_stake)
    allowed_stake = max(0.0, max_group_exposure - float(current_group_exposure))
    approved = projected_group_exposure <= max_group_exposure
    return {
        "approved": approved,
        "max_group_exposure": round(max_group_exposure, 2),
        "projected_group_exposure": round(projected_group_exposure, 2),
        "allowed_stake": round(allowed_stake if not approved else float(suggested_stake), 2),
        "message": "Exposure acceptable" if approved else "Exposure cap exceeded",
    }


def cap_value(value: float, cap_value: float) -> float:
    return max(0.0, min(float(value), float(cap_value)))


def cap_single_bet_exposure(stake_percent: float) -> float:
    return cap_value(stake_percent, EXPOSURE_LIMITS["max_single_bet_bankroll_percent"])


def cap_daily_exposure(stake_percent: float, daily_exposure_percent: float) -> float:
    remaining = max(0.0, EXPOSURE_LIMITS["max_daily_kelly_exposure_percent"] - float(daily_exposure_percent))
    return cap_value(stake_percent, remaining)


def cap_weekly_exposure(stake_percent: float, weekly_exposure_percent: float) -> float:
    remaining = max(0.0, EXPOSURE_LIMITS["max_weekly_kelly_exposure_percent"] - float(weekly_exposure_percent))
    return cap_value(stake_percent, remaining)


def cap_market_group_exposure(stake_percent: float, market_group_exposure_percent: float) -> float:
    remaining = max(0.0, EXPOSURE_LIMITS["max_market_group_exposure_percent"] - float(market_group_exposure_percent))
    return cap_value(stake_percent, remaining)


def cap_correlated_exposure(stake_percent: float, correlated_exposure_percent: float) -> float:
    remaining = max(0.0, EXPOSURE_LIMITS["correlation_exposure_cap"] - float(correlated_exposure_percent))
    return cap_value(stake_percent, remaining)


def apply_all_exposure_caps(stake_percent: float, exposures: dict[str, Any]) -> dict[str, Any]:
    capped = cap_single_bet_exposure(stake_percent)
    capped = cap_daily_exposure(capped, float(exposures.get("daily_exposure_percent", 0)))
    capped = cap_weekly_exposure(capped, float(exposures.get("weekly_exposure_percent", 0)))
    capped = cap_market_group_exposure(capped, float(exposures.get("market_group_exposure_percent", 0)))
    capped = cap_correlated_exposure(capped, float(exposures.get("correlated_exposure_percent", 0)))
    blocked = capped <= 0
    return {
        "exposure_gate_result": "blocked" if blocked else "pass",
        "capped_stake_percent": round(capped, 6),
        "limits": dict(EXPOSURE_LIMITS),
    }


def simulate_stake_plan(
    candidate: dict[str, Any],
    *,
    bankroll: float,
    risk_profile: str = "medium",
    max_loss_cap: float | None = None,
) -> dict[str, Any]:
    bankroll_value = max(0.0, float(bankroll))
    risk_cap = STAKE_RISK_CAPS.get(str(risk_profile).lower(), 0.02)
    total_cap = bankroll_value * risk_cap
    candidate_type = candidate.get("candidate_type") or "positive_ev"
    base_roi = float(candidate.get("estimated_roi_percent") or candidate.get("ev_percent") or 0.0)
    max_gain = float(candidate.get("max_gain") or 0.0)
    max_loss = float(candidate.get("max_loss") or total_cap)
    max_loss_limit = min(total_cap, float(max_loss_cap)) if max_loss_cap is not None else total_cap

    plans = []
    for profile, multiplier in STAKE_PROFILE_MULTIPLIERS.items():
        suggested = round(min(bankroll_value * multiplier, total_cap), 2)
        expected_value = round(suggested * (base_roi / 100.0), 4)
        if candidate_type == "arbitrage_candidate" and candidate.get("stake_plan"):
            total_candidate_stake = sum(float(item.get("stake", 0)) for item in candidate["stake_plan"]) or 1.0
            plan_value = [
                {**item, "stake": round(suggested * (float(item.get("stake", 0)) / total_candidate_stake), 2)}
                for item in candidate["stake_plan"]
            ]
        else:
            plan_value = [{"selection": candidate.get("selection"), "stake": suggested}]
        plans.append(
            {
                "profile": profile,
                "suggested_stake": suggested,
                "stake_plan": plan_value,
                "max_loss": round(min(max_loss_limit, max_loss if max_loss > 0 else suggested), 2),
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


def roi_pct(profit: float, staked: float) -> Optional[float]:
    if staked == 0:
        return None
    return round(profit / staked * 100, 2)


def yield_pct(profit: float, num_bets: int) -> Optional[float]:
    if num_bets == 0:
        return None
    return round(profit / num_bets, 4)


def profit_factor(gross_wins: float, gross_losses: float) -> Optional[float]:
    if gross_losses == 0:
        return None if gross_wins == 0 else float("inf")
    return round(gross_wins / abs(gross_losses), 3)


def average_clv(clv_values: list[Optional[float]]) -> Optional[float]:
    return _core_average_clv(clv_values)

# Canonical compatibility imports
from src.core.risk import *  # noqa: F401,F403
