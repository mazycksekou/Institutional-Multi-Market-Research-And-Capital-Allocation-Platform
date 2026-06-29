from __future__ import annotations

from typing import Any

from .scheduler_config import clamp


def liquidity_score(*, limit_estimate: Any, spread_percent: Any = 0, book_count: Any = 1) -> float:
    limit_value = max(0.0, float(limit_estimate or 0))
    spread_value = max(0.0, float(spread_percent or 0))
    books = max(1.0, float(book_count or 1))
    score = (min(limit_value / 500.0, 1.0) * 6.0) + (min(books / 5.0, 1.0) * 2.0) + max(0.0, 2.0 - spread_value)
    return round(clamp(score, 0, 10), 2)


def estimate_limit_risk(limit_estimate: Any, target_stake: Any) -> float:
    limit_value = max(0.0, float(limit_estimate or 0))
    stake_value = max(0.0, float(target_stake or 0))
    if stake_value == 0:
        return 0.0
    return round(clamp(1 - (limit_value / stake_value), 0, 1), 4)


def estimate_stale_odds_risk(age_seconds: Any, max_age_seconds: Any) -> float:
    age_value = max(0.0, float(age_seconds or 0))
    max_age = max(1.0, float(max_age_seconds or 1))
    return round(clamp(age_value / max_age, 0, 1), 4)


def score_stale_data_risk(age_seconds: Any, max_age_seconds: Any) -> float:
    return estimate_stale_odds_risk(age_seconds, max_age_seconds)


def estimate_execution_feasibility(*, liquidity_score_value: Any, stale_odds_risk: Any, settlement_risk: Any = 0) -> float:
    liquidity = clamp(liquidity_score_value, 0, 10) / 10.0
    stale = clamp(stale_odds_risk, 0, 1)
    settlement = clamp(settlement_risk, 0, 1)
    return round(clamp((liquidity * 0.7) + ((1 - stale) * 0.2) + ((1 - settlement) * 0.1), 0, 1), 4)


def score_execution_feasibility(*, liquidity_score_value: Any, stale_odds_risk: Any, settlement_risk: Any = 0) -> float:
    return estimate_execution_feasibility(
        liquidity_score_value=liquidity_score_value,
        stale_odds_risk=stale_odds_risk,
        settlement_risk=settlement_risk,
    )


def block_low_liquidity_arbitrage(*, liquidity_score_value: Any, watch_only: bool = False) -> dict[str, Any]:
    score = clamp(liquidity_score_value, 0, 10)
    blocked = score < 4 and not watch_only
    return {
        "blocked": blocked,
        "watch_only": watch_only or score < 4,
        "reason": "low_liquidity" if blocked else None,
    }
