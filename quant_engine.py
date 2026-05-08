def american_to_decimal(odds: int | float) -> float:
    if odds > 0:
        return 1 + (odds / 100)
    return 1 + (100 / abs(odds))


def implied_probability_from_american(odds: int | float) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def expected_value_per_unit(odds: int | float, true_probability: float) -> float:
    decimal_odds = american_to_decimal(odds)
    profit_per_unit = decimal_odds - 1
    loss_probability = 1 - true_probability
    return (true_probability * profit_per_unit) - loss_probability


def expected_value_dollars(odds: int | float, true_probability: float, stake: float) -> float:
    return expected_value_per_unit(odds, true_probability) * stake


def kelly_fraction(odds: int | float, true_probability: float) -> float:
    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1
    p = true_probability
    q = 1 - p
    if b <= 0:
        return 0
    return max(0, ((b * p) - q) / b)


def suggested_bet_size(
    bankroll: float,
    kelly: float,
    fractional_kelly: float = 0.25,
    max_bankroll_risk: float = 0.02,
) -> float:
    stake = bankroll * kelly * fractional_kelly
    return max(0, min(stake, bankroll * max_bankroll_risk))


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
