"""Parlay mathematics and correlation warnings."""
from __future__ import annotations

from quant_engine import american_to_decimal, kelly_fraction


def parlay_decimal_odds(american_odds: list[int | float]) -> float:
    d = 1.0
    for o in american_odds:
        d *= american_to_decimal(o)
    return round(d, 6)


def parlay_implied_probability(american_odds: list[int | float]) -> float:
    return round(1 / parlay_decimal_odds(american_odds), 6)


def parlay_independent_win_probability(true_probs: list[float]) -> float:
    p = 1.0
    for t in true_probs:
        p *= float(t)
    return p


def parlay_correlation_adjusted_probability(
    independent_prob: float,
    correlation_factor: float,
) -> float:
    """
    correlation_factor in [0, 1]: 1 = full independence dampening toward max leg prob.
    """
    cf = max(0.0, min(1.0, float(correlation_factor)))
    return max(0.0, min(1.0, independent_prob * (0.5 + 0.5 * cf)))


def parlay_ev(
    parlay_decimal: float,
    true_win_probability: float,
) -> float:
    """EV per $1 staked on parlay."""
    p = float(true_win_probability)
    b = float(parlay_decimal) - 1
    return p * b - (1 - p)


def parlay_kelly(
    parlay_decimal: float,
    true_win_probability: float,
) -> float:
    """Kelly fraction treating parlay as single binary bet."""
    american_equiv = int(round((parlay_decimal - 1) * 100)) if parlay_decimal >= 2 else -100
    try:
        return kelly_fraction(american_equiv, true_win_probability)
    except Exception:
        return 0.0


def same_game_parlay_risk_warning(legs_same_event: bool) -> bool:
    return bool(legs_same_event)


def positive_correlation_flag(correlation: float) -> bool:
    return correlation > 0.15


def negative_correlation_flag(correlation: float) -> bool:
    return correlation < -0.15


def hidden_duplicate_exposure_flag(legs_share_entity: bool) -> bool:
    return bool(legs_share_entity)


def no_bet_parlay_trap_flag(implied_parlay_prob: float, fair_parlay_prob: float) -> bool:
    """Trap if market-implied parlay prob far exceeds independent fair estimate."""
    if fair_parlay_prob <= 0:
        return False
    return implied_parlay_prob > fair_parlay_prob * 1.35
