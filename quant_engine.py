from datetime import date
from typing import Any

from src.core.math_utils import (
    american_to_decimal as _core_american_to_decimal,
    american_to_implied_probability as _core_american_to_implied_probability,
    calculate_kelly_stake as _core_calculate_kelly_stake,
    edge_percent as _core_edge_percent,
    expected_value as _core_expected_value,
    fractional_kelly as _core_fractional_kelly,
    implied_probability_to_american as _core_implied_probability_to_american,
)


def _validate_american_odds(odds: int | float) -> float:
    if odds == 0:
        raise ValueError("American odds must be positive or negative.")
    return float(odds)


def _validate_probability(probability: float) -> float:
    probability = float(probability)
    if probability <= 0 or probability >= 1:
        raise ValueError("True probability must be between 0 and 1.")
    return probability


def american_to_decimal(odds: int | float) -> float:
    return _core_american_to_decimal(odds)


def american_to_implied_probability(odds: int | float) -> dict[str, float]:
    probability = implied_probability_from_american(odds)
    return {
        "decimal": probability,
        "percent": round(probability * 100, 2),
    }


def implied_probability_from_american(odds: int | float) -> float:
    return _core_american_to_implied_probability(odds)


def decimal_to_american(decimal_odds: float) -> int:
    decimal_odds = float(decimal_odds)
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1.")
    if decimal_odds >= 2:
        return int(round((decimal_odds - 1) * 100))
    return int(round(-100 / (decimal_odds - 1)))


def probability_to_fair_american(probability: float) -> int:
    return _core_implied_probability_to_american(probability)


def expected_value_per_unit(odds: int | float, true_probability: float) -> float:
    return _core_expected_value(odds, true_probability, stake=1.0)


def expected_value_dollars(odds: int | float, true_probability: float, stake: float) -> float:
    return expected_value_per_unit(odds, true_probability) * stake


def kelly_fraction(odds: int | float, true_probability: float) -> float:
    return _core_fractional_kelly(odds, true_probability, fraction=1.0)


def suggested_stake(
    bankroll: float,
    american_odds: int | float,
    true_probability: float,
    fractional_kelly: float = 0.25,
    max_bankroll_pct: float = 0.02,
) -> float:
    return _core_calculate_kelly_stake(
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
    stake = bankroll * kelly * fractional_kelly
    return max(0, min(stake, bankroll * max_bankroll_risk))


def classify_edge(edge_pct: float, ev_per_unit: float) -> str:
    if edge_pct is None or ev_per_unit is None:
        return "NO DATA"
    if ev_per_unit <= 0 or edge_pct <= 0:
        return "BAD PRICE"
    if edge_pct >= 2.5 and ev_per_unit >= 0.02:
        return "BET"
    if edge_pct > 0 and ev_per_unit > 0:
        return "LEAN"
    return "PASS"


def build_market_pricing_row(input_data: dict[str, Any], output_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": date.today().isoformat(),
        "type": "market_pricing",
        "event": input_data.get("event"),
        "provider": input_data.get("provider"),
        "sportsbook": input_data.get("sportsbook"),
        "league": input_data.get("league"),
        "market": input_data.get("market"),
        "selection": input_data.get("selection"),
        "american_odds": input_data.get("american_odds"),
        "decimal_odds": output_data.get("decimal_odds"),
        "implied_probability": output_data.get("implied_probability"),
        "implied_probability_percent": output_data.get("implied_probability_percent"),
        "true_probability": input_data.get("true_probability"),
        "true_probability_percent": output_data.get("true_probability_percent"),
        "edge": output_data.get("edge"),
        "edge_percent": output_data.get("edge_percent"),
        "fair_american_odds": output_data.get("fair_american_odds"),
        "ev_per_unit": output_data.get("ev_per_unit"),
        "ev_per_100": output_data.get("ev_per_100"),
        "kelly_fraction": output_data.get("kelly_fraction"),
        "kelly_percent": output_data.get("kelly_percent"),
        "bankroll": input_data.get("bankroll"),
        "stake": input_data.get("stake"),
        "suggested_stake": output_data.get("suggested_stake"),
        "correlation_group": input_data.get("correlation_group"),
        "decision": output_data.get("decision"),
        "risk_warning": output_data.get("risk_warning"),
        "result": "pending",
        "profit_or_loss": 0,
        "notes": input_data.get("notes"),
    }


def capm_required_return(risk_free_rate_pct: float, beta: float, expected_market_return_pct: float) -> float:
    return risk_free_rate_pct + beta * (expected_market_return_pct - risk_free_rate_pct)


def stock_alpha(expected_stock_return_pct: float, capm_required_return_pct: float) -> float:
    return expected_stock_return_pct - capm_required_return_pct


def classify_bet(edge_pct: float, ev_per_100: float, kelly_pct: float) -> str:
    if edge_pct <= 0 or ev_per_100 <= 0:
        return "PASS"
    if edge_pct >= 5 and kelly_pct >= 5:
        return "STRONG CONSIDERATION"
    if edge_pct >= 2.5 and kelly_pct > 0:
        return "CONSIDER"
    return "LEAN ONLY"


def classify_stock(alpha_pct: float) -> str:
    if alpha_pct >= 5:
        return "STRONG CONSIDERATION"
    if alpha_pct >= 2:
        return "CONSIDER"
    if alpha_pct >= 0:
        return "WATCHLIST"
    return "PASS"


def exposure_check(
    bankroll: float,
    suggested_stake: float,
    current_group_exposure: float,
    group_exposure_cap: float = 0.05,
) -> dict:
    max_group_exposure = bankroll * group_exposure_cap
    projected_group_exposure = current_group_exposure + suggested_stake
    allowed_stake = max(0, max_group_exposure - current_group_exposure)
    approved = projected_group_exposure <= max_group_exposure
    return {
        "approved": approved,
        "max_group_exposure": round(max_group_exposure, 2),
        "projected_group_exposure": round(projected_group_exposure, 2),
        "allowed_stake": round(allowed_stake if not approved else suggested_stake, 2),
        "message": "Exposure acceptable" if approved else "Exposure cap exceeded",
    }


# --- Extended quant primitives (betting evaluation engine) ---


def decimal_to_implied_probability(decimal_odds: float) -> float:
    d = float(decimal_odds)
    if d <= 1:
        raise ValueError("Decimal odds must be greater than 1.")
    return 1 / d


def break_even_probability_american(odds: int | float) -> float:
    """Minimum win rate to break even betting at these odds (equals implied prob)."""
    return implied_probability_from_american(odds)


def book_hold_two_way(implied_a: float, implied_b: float) -> float:
    """Overround / vig as implied_a + implied_b - 1."""
    return float(implied_a) + float(implied_b) - 1


def no_vig_probabilities_two_way(implied_a: float, implied_b: float) -> tuple[float, float]:
    s = implied_a + implied_b
    if s <= 0:
        raise ValueError("Implied probabilities must sum to a positive value.")
    return implied_a / s, implied_b / s


def no_vig_probabilities_three_way(p1: float, p2: float, p3: float) -> tuple[float, float, float]:
    s = p1 + p2 + p3
    if s <= 0:
        raise ValueError("Implied probabilities must sum to a positive value.")
    return p1 / s, p2 / s, p3 / s


def no_vig_probabilities_n_way(implied: list[float]) -> list[float]:
    s = sum(implied)
    if s <= 0:
        raise ValueError("Implied probabilities must sum to a positive value.")
    return [p / s for p in implied]


def fair_odds_american_from_probability(probability: float) -> int:
    return probability_to_fair_american(probability)


def edge_percentage(true_probability: float, implied_probability: float) -> float:
    return _core_edge_percent(true_probability, implied_probability)


def expected_value_per_100(odds: int | float, true_probability: float) -> float:
    return expected_value_per_unit(odds, true_probability) * 100


def kelly_half(odds: int | float, true_probability: float) -> float:
    return kelly_fraction(odds, true_probability) * 0.5


def kelly_quarter(odds: int | float, true_probability: float) -> float:
    return kelly_fraction(odds, true_probability) * 0.25


def kelly_capped_fraction(odds: int | float, true_probability: float, max_kelly: float = 0.05) -> float:
    """Full Kelly fraction capped at max_kelly (e.g. 0.05 = 5% of bankroll max Kelly stake)."""
    return min(kelly_fraction(odds, true_probability), float(max_kelly))


def suggested_unit_size(
    bankroll: float,
    unit_size: float,
    kelly_fractional: float,
    american_odds: int | float,
    true_probability: float,
    max_bankroll_pct: float = 0.02,
) -> float:
    """Suggested stake in units (unit_size dollars per unit)."""
    stake_dollars = suggested_stake(bankroll, american_odds, true_probability, fractional_kelly=kelly_fractional, max_bankroll_pct=max_bankroll_pct)
    if unit_size <= 0:
        return 0
    return round(stake_dollars / unit_size, 2)


def confidence_adjusted_stake(base_stake: float, confidence_0_100: float) -> float:
    c = max(0, min(100, float(confidence_0_100))) / 100
    return max(0, float(base_stake) * c)


def risk_adjusted_stake(base_stake: float, risk_multiplier: float) -> float:
    """risk_multiplier in (0, 1] reduces stake for higher perceived risk."""
    m = max(0, min(1, float(risk_multiplier)))
    return max(0, float(base_stake) * m)


def book_hold_n_way(implied_probabilities: list[float]) -> float:
    """Total overround / vig for N outcomes: sum(implied) - 1."""
    return float(sum(implied_probabilities)) - 1


def implied_probability_from_decimal(decimal_odds: float) -> float:
    return decimal_to_implied_probability(decimal_odds)


def break_even_probability_decimal(decimal_odds: float) -> float:
    return implied_probability_from_decimal(decimal_odds)


def expected_value_per_dollar(odds: int | float, true_probability: float) -> float:
    return expected_value_per_unit(odds, true_probability)


def full_kelly_fraction(odds: int | float, true_probability: float) -> float:
    return kelly_fraction(odds, true_probability)


def fair_decimal_odds_from_probability(probability: float) -> float:
    p = _validate_probability(probability)
    return 1 / p


def full_kelly_percent(odds: int | float, true_probability: float) -> float:
    return round(full_kelly_fraction(odds, true_probability) * 100, 4)


def fractional_kelly_percent(odds: int | float, true_probability: float, fraction: float = 0.25) -> float:
    return round(full_kelly_fraction(odds, true_probability) * max(0, float(fraction)) * 100, 4)


def risk_profile_settings(risk_profile: str | None = "standard") -> dict[str, float | str]:
    profiles = {
        "conservative": {"risk_profile": "conservative", "kelly_fraction": 0.125, "max_bankroll_pct": 0.01, "confidence_multiplier": 0.75},
        "standard": {"risk_profile": "standard", "kelly_fraction": 0.25, "max_bankroll_pct": 0.02, "confidence_multiplier": 1.0},
        "aggressive": {"risk_profile": "aggressive", "kelly_fraction": 0.5, "max_bankroll_pct": 0.03, "confidence_multiplier": 1.15},
    }
    return profiles.get((risk_profile or "standard").strip().lower(), profiles["standard"]).copy()


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


def quant_engine_component_foundation() -> dict[str, Any]:
    return {
        "component_name": "quant_engine_foundation",
        "component_status": "research_mode_not_bettable",
        "required_inputs": ["american_odds", "true_probability", "bankroll", "risk_profile"],
        "optional_inputs": ["unit_size", "confidence", "max_stake_cap", "current_exposure"],
        "missing_inputs": [],
        "data_provider_needs": ["sportsbook odds", "independent model probability", "risk ledger"],
        "backtest_requirements": ["settled outcomes", "closing-line history", "probability calibration buckets"],
        "calibration_requirements": ["edge bucket calibration", "Kelly drawdown review", "confidence calibration"],
        "no_bet_flags": ["missing required input", "negative EV", "risk cap exceeded", "low confidence", "no backtest proof"],
        "output_fields": [
            "decimal_odds",
            "implied_probability",
            "fair_american_odds",
            "edge",
            "ev_per_100",
            "full_kelly_percent",
            "fractional_kelly_percent",
            "suggested_stake",
            "bankroll_cap",
            "risk_profile",
            "confidence",
            "no_bet_flags",
        ],
        "notes": [
            "Includes American odds conversion, implied probability, fair odds, edge, EV, Kelly, bankroll caps, risk profile handling, confidence handling, and no-bet flags.",
            "This component is math-only and does not create confirmed bets.",
        ],
    }
