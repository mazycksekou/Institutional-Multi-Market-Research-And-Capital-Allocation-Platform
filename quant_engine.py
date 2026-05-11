from datetime import date
from typing import Any


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
    odds = _validate_american_odds(odds)
    if odds > 0:
        return 1 + (odds / 100)
    return 1 + (100 / abs(odds))


def american_to_implied_probability(odds: int | float) -> dict[str, float]:
    probability = implied_probability_from_american(odds)
    return {
        "decimal": probability,
        "percent": round(probability * 100, 2),
    }


def implied_probability_from_american(odds: int | float) -> float:
    odds = _validate_american_odds(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def decimal_to_american(decimal_odds: float) -> int:
    decimal_odds = float(decimal_odds)
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1.")
    if decimal_odds >= 2:
        return int(round((decimal_odds - 1) * 100))
    return int(round(-100 / (decimal_odds - 1)))


def probability_to_fair_american(probability: float) -> int:
    probability = _validate_probability(probability)
    return decimal_to_american(1 / probability)


def expected_value_per_unit(odds: int | float, true_probability: float) -> float:
    true_probability = _validate_probability(true_probability)
    decimal_odds = american_to_decimal(odds)
    profit_per_unit = decimal_odds - 1
    loss_probability = 1 - true_probability
    return (true_probability * profit_per_unit) - loss_probability


def expected_value_dollars(odds: int | float, true_probability: float, stake: float) -> float:
    return expected_value_per_unit(odds, true_probability) * stake


def kelly_fraction(odds: int | float, true_probability: float) -> float:
    true_probability = _validate_probability(true_probability)
    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1
    p = true_probability
    q = 1 - p
    if b <= 0:
        return 0
    return max(0, ((b * p) - q) / b)


def suggested_stake(
    bankroll: float,
    american_odds: int | float,
    true_probability: float,
    fractional_kelly: float = 0.25,
    max_bankroll_pct: float = 0.02,
) -> float:
    bankroll = max(0, float(bankroll))
    fractional_kelly = max(0, float(fractional_kelly))
    max_bankroll_pct = max(0, float(max_bankroll_pct))
    kelly = kelly_fraction(american_odds, true_probability)
    stake = bankroll * kelly * fractional_kelly
    return max(0, min(stake, bankroll * max_bankroll_pct))


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
