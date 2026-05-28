from __future__ import annotations

from typing import Any


LIMITS = {
    "max_single_bet_bankroll_percent": 5.0,
    "max_single_trade_portfolio_percent": 5.0,
    "max_daily_kelly_exposure_percent": 12.0,
    "max_weekly_kelly_exposure_percent": 25.0,
    "max_market_group_exposure_percent": 10.0,
    "portfolio_kelly_cap": 25.0,
    "correlation_exposure_cap": 10.0,
}


def _cap(value: float, cap_value: float) -> float:
    return max(0.0, min(float(value), float(cap_value)))


def cap_single_bet_exposure(stake_percent: float) -> float:
    return _cap(stake_percent, LIMITS["max_single_bet_bankroll_percent"])


def cap_daily_exposure(stake_percent: float, daily_exposure_percent: float) -> float:
    remaining = max(0.0, LIMITS["max_daily_kelly_exposure_percent"] - float(daily_exposure_percent))
    return _cap(stake_percent, remaining)


def cap_weekly_exposure(stake_percent: float, weekly_exposure_percent: float) -> float:
    remaining = max(0.0, LIMITS["max_weekly_kelly_exposure_percent"] - float(weekly_exposure_percent))
    return _cap(stake_percent, remaining)


def cap_market_group_exposure(stake_percent: float, market_group_exposure_percent: float) -> float:
    remaining = max(0.0, LIMITS["max_market_group_exposure_percent"] - float(market_group_exposure_percent))
    return _cap(stake_percent, remaining)


def cap_correlated_exposure(stake_percent: float, correlated_exposure_percent: float) -> float:
    remaining = max(0.0, LIMITS["correlation_exposure_cap"] - float(correlated_exposure_percent))
    return _cap(stake_percent, remaining)


def apply_all_exposure_caps(stake_percent: float, exposures: dict[str, Any]) -> dict[str, Any]:
    s = cap_single_bet_exposure(stake_percent)
    s = cap_daily_exposure(s, float(exposures.get("daily_exposure_percent", 0)))
    s = cap_weekly_exposure(s, float(exposures.get("weekly_exposure_percent", 0)))
    s = cap_market_group_exposure(s, float(exposures.get("market_group_exposure_percent", 0)))
    s = cap_correlated_exposure(s, float(exposures.get("correlated_exposure_percent", 0)))
    blocked = s <= 0
    return {
        "exposure_gate_result": "blocked" if blocked else "pass",
        "capped_stake_percent": round(s, 6),
        "limits": dict(LIMITS),
    }
