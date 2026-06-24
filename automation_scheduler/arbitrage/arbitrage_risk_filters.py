from __future__ import annotations

from typing import Any

from ..liquidity_risk import block_low_liquidity_arbitrage, estimate_execution_feasibility, estimate_stale_odds_risk
from src.brokerage.settlement import compare_settlement_rules


def stale_price_arbitrage_filter(timestamps: list[int | float], *, max_timestamp_skew_seconds: int = 120) -> dict[str, Any]:
    values = [int(value) for value in timestamps if isinstance(value, (int, float))]
    if len(values) < 2:
        return {"blocked": False, "stale_data_risk": 0.0}
    skew = max(values) - min(values)
    return {
        "blocked": skew > max_timestamp_skew_seconds,
        "timestamp_skew_seconds": skew,
        "stale_data_risk": estimate_stale_odds_risk(skew, max_timestamp_skew_seconds),
    }


def settlement_rule_risk_checker(rule_sets: list[dict[str, Any]]) -> dict[str, Any]:
    result = compare_settlement_rules(rule_sets)
    return {
        "blocked": result["material_mismatch"],
        "settlement_risk": result["settlement_risk"],
        "mismatches": result["mismatches"],
    }


def apply_arbitrage_risk_filters(
    *,
    timestamps: list[int | float],
    rule_sets: list[dict[str, Any]],
    liquidity_score_value: float,
    watch_only: bool = False,
    max_timestamp_skew_seconds: int = 120,
) -> dict[str, Any]:
    stale = stale_price_arbitrage_filter(timestamps, max_timestamp_skew_seconds=max_timestamp_skew_seconds)
    settlement = settlement_rule_risk_checker(rule_sets)
    liquidity = block_low_liquidity_arbitrage(liquidity_score_value=liquidity_score_value, watch_only=watch_only)
    execution = estimate_execution_feasibility(
        liquidity_score_value=liquidity_score_value,
        stale_odds_risk=stale["stale_data_risk"],
        settlement_risk=settlement["settlement_risk"],
    )
    blocked = stale["blocked"] or settlement["blocked"] or liquidity["blocked"]
    return {
        "blocked": blocked,
        "stale_data_risk": stale["stale_data_risk"],
        "settlement_risk": settlement["settlement_risk"],
        "execution_feasibility_score": execution,
        "watch_only": liquidity["watch_only"],
        "blockers": [
            reason
            for reason, active in (
                ("stale_data", stale["blocked"]),
                ("settlement_mismatch", settlement["blocked"]),
                ("low_liquidity", liquidity["blocked"]),
            )
            if active
        ],
    }
