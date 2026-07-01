from __future__ import annotations

from typing import Any

from src.core.risk_engine import (
    EXPOSURE_LIMITS as LIMITS,
    apply_all_exposure_caps as _risk_apply_all_exposure_caps,
    cap_correlated_exposure as _risk_cap_correlated_exposure,
    cap_daily_exposure as _risk_cap_daily_exposure,
    cap_market_group_exposure as _risk_cap_market_group_exposure,
    cap_single_bet_exposure as _risk_cap_single_bet_exposure,
    cap_value as _risk_cap_value,
    cap_weekly_exposure as _risk_cap_weekly_exposure,
)

def _cap(value: float, cap_value: float) -> float:
    return _risk_cap_value(value, cap_value)


def cap_single_bet_exposure(stake_percent: float) -> float:
    return _risk_cap_single_bet_exposure(stake_percent)


def cap_daily_exposure(stake_percent: float, daily_exposure_percent: float) -> float:
    return _risk_cap_daily_exposure(stake_percent, daily_exposure_percent)


def cap_weekly_exposure(stake_percent: float, weekly_exposure_percent: float) -> float:
    return _risk_cap_weekly_exposure(stake_percent, weekly_exposure_percent)


def cap_market_group_exposure(stake_percent: float, market_group_exposure_percent: float) -> float:
    return _risk_cap_market_group_exposure(stake_percent, market_group_exposure_percent)


def cap_correlated_exposure(stake_percent: float, correlated_exposure_percent: float) -> float:
    return _risk_cap_correlated_exposure(stake_percent, correlated_exposure_percent)


def apply_all_exposure_caps(stake_percent: float, exposures: dict[str, Any]) -> dict[str, Any]:
    return _risk_apply_all_exposure_caps(stake_percent, exposures)
