from datetime import date
from collections.abc import Iterable, Mapping
from typing import Any

from src.core.math_utils import (
    american_to_decimal as _core_american_to_decimal,
    american_to_implied_probability as _core_american_to_implied_probability,
    book_hold_n_way as _core_book_hold_n_way,
    book_hold_two_way as _core_book_hold_two_way,
    break_even_probability_american as _core_break_even_probability_american,
    break_even_probability_decimal as _core_break_even_probability_decimal,
    decimal_to_american as _core_decimal_to_american,
    decimal_to_implied_probability as _core_decimal_to_implied_probability,
    edge_percent as _core_edge_percent,
    expected_value as _core_expected_value,
    expected_value_per_100 as _core_expected_value_per_100,
    expected_value_per_dollar as _core_expected_value_per_dollar,
    expected_value_per_unit as _core_expected_value_per_unit,
    fair_decimal_odds_from_probability as _core_fair_decimal_odds_from_probability,
    fair_odds_american_from_probability as _core_fair_odds_american_from_probability,
    fractional_kelly as _core_fractional_kelly,
    fractional_kelly_percent as _core_fractional_kelly_percent,
    full_kelly_fraction as _core_full_kelly_fraction,
    full_kelly_percent as _core_full_kelly_percent,
    implied_probability_from_decimal as _core_implied_probability_from_decimal,
    implied_probability_to_american as _core_implied_probability_to_american,
    no_vig_probabilities_n_way as _core_no_vig_probabilities_n_way,
    no_vig_probabilities_three_way as _core_no_vig_probabilities_three_way,
    no_vig_probabilities_two_way as _core_no_vig_probabilities_two_way,
)
from risk_engine import (
    confidence_adjusted_stake as _risk_confidence_adjusted_stake,
    exposure_check as _risk_exposure_check,
    risk_adjusted_stake as _risk_adjusted_stake,
    risk_profile_settings as _risk_profile_settings,
    suggested_bet_size as _risk_suggested_bet_size,
    suggested_stake as _risk_suggested_stake,
    suggested_stake_with_risk_controls as _risk_suggested_stake_with_risk_controls,
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
    return _core_decimal_to_american(decimal_odds)


def probability_to_fair_american(probability: float) -> int:
    return _core_implied_probability_to_american(probability)


def expected_value_per_unit(odds: int | float, true_probability: float) -> float:
    return _core_expected_value_per_unit(odds, true_probability)


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
    return _risk_suggested_stake(
        bankroll,
        american_odds,
        true_probability,
        fractional_kelly=fractional_kelly,
        max_bankroll_pct=max_bankroll_pct,
    )


def suggested_bet_size(
    bankroll: float,
    kelly: float,
    fractional_kelly: float = 0.25,
    max_bankroll_risk: float = 0.02,
) -> float:
    return _risk_suggested_bet_size(bankroll, kelly, fractional_kelly, max_bankroll_risk)


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
    return _risk_exposure_check(bankroll, suggested_stake, current_group_exposure, group_exposure_cap)


# --- Extended quant primitives (betting evaluation engine) ---


PAPER_ONLY_EVALUATION_REQUIRED_FIELDS: tuple[str, ...] = (
    "fixture_id",
    "sport_or_market",
    "event_id",
    "prediction_target",
    "selection",
    "model_probability",
    "market_odds_american",
    "implied_probability",
    "expected_value",
    "stake_units",
    "bankroll_snapshot",
    "result_label",
    "outcome_known",
    "source_type",
    "execution_mode",
)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return None


def _paper_result_from_row(result_label: Any, outcome_known: Any) -> str:
    if not bool(outcome_known):
        return "pending"

    label = str(result_label or "").strip().lower()
    if any(token in label for token in ("win", "won")):
        return "paper_win"
    if any(token in label for token in ("loss", "lost")):
        return "paper_loss"
    if any(token in label for token in ("push", "tie", "refund")):
        return "paper_push"
    return "paper_observed"


def evaluate_paper_only_fixture_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Evaluate local fixture rows without starting live prediction testing.

    no prediction testing started in 10K8F.
    no live connectors.
    no API calls.
    no database writes.
    do not label quality automatically.
    do not hide valid results because sample size is low.
    user threshold review-only.
    validity check only.
    paper_only.
    fixture_only.
    local_fixture.
    """

    rows_tested = 0
    rows_valid = 0
    rows_invalid = 0
    missing_field_reasons: list[str] = []
    warning_reasons: list[str] = []
    evaluations: list[dict[str, Any]] = []
    observed_source_types: set[str] = set()
    observed_execution_modes: set[str] = set()

    for row in rows:
        rows_tested += 1
        row_missing: list[str] = []
        row_warnings: list[str] = []

        for field in PAPER_ONLY_EVALUATION_REQUIRED_FIELDS:
            value = row.get(field)
            if value in (None, ""):
                row_missing.append(field)

        source_type = str(row.get("source_type") or "").strip().lower()
        if source_type:
            observed_source_types.add(source_type)
        if "fixture" not in source_type:
            row_missing.append("source_type")
            row_warnings.append(f"invalid_source_type:{source_type or 'missing'}")

        execution_mode = str(row.get("execution_mode") or "").strip().lower()
        if execution_mode:
            observed_execution_modes.add(execution_mode)
        if execution_mode not in {"paper_only", "fixture_only"}:
            row_missing.append("execution_mode")
            row_warnings.append(f"invalid_execution_mode:{execution_mode or 'missing'}")

        model_probability = _safe_float(row.get("model_probability"))
        implied_probability = _safe_float(row.get("implied_probability"))
        expected_value = _safe_float(row.get("expected_value"))
        stake_units = _safe_float(row.get("stake_units"))
        bankroll_snapshot = _safe_float(row.get("bankroll_snapshot"))
        market_odds_american = _safe_float(row.get("market_odds_american"))

        for field_name, numeric_value in (
            ("model_probability", model_probability),
            ("implied_probability", implied_probability),
        ):
            if numeric_value is None:
                row_warnings.append(f"invalid_numeric_value:{field_name}")
            elif not 0.0 <= numeric_value <= 1.0:
                row_warnings.append(f"probability_out_of_range:{field_name}")

        for field_name, numeric_value in (
            ("expected_value", expected_value),
            ("stake_units", stake_units),
            ("bankroll_snapshot", bankroll_snapshot),
            ("market_odds_american", market_odds_american),
        ):
            if numeric_value is None:
                row_warnings.append(f"invalid_numeric_value:{field_name}")

        if row_missing:
            rows_invalid += 1
            missing_field_reasons.extend(row_missing)
        else:
            rows_valid += 1

        paper_result = _paper_result_from_row(row.get("result_label"), row.get("outcome_known"))
        paper_edge = None
        if model_probability is not None and implied_probability is not None:
            paper_edge = model_probability - implied_probability

        evaluations.append(
            {
                "fixture_id": row.get("fixture_id"),
                "sport_or_market": row.get("sport_or_market"),
                "event_id": row.get("event_id"),
                "prediction_target": row.get("prediction_target"),
                "selection": row.get("selection"),
                "model_probability": model_probability,
                "implied_probability": implied_probability,
                "market_odds_american": market_odds_american,
                "expected_value": expected_value,
                "stake_units": stake_units,
                "bankroll_snapshot": bankroll_snapshot,
                "outcome_known": row.get("outcome_known"),
                "result_label": row.get("result_label"),
                "paper_edge": paper_edge,
                "paper_ev": expected_value,
                "paper_stake_units": stake_units,
                "paper_result": paper_result,
                "source_type": source_type,
                "execution_mode": execution_mode,
            }
        )
        warning_reasons.extend(row_warnings)

    execution_mode_result = "mixed"
    if len(observed_execution_modes) == 1:
        execution_mode_result = next(iter(observed_execution_modes))
    elif not observed_execution_modes:
        execution_mode_result = ""

    source_type_result = "mixed"
    if len(observed_source_types) == 1:
        source_type_result = next(iter(observed_source_types))
    elif not observed_source_types:
        source_type_result = ""

    return {
        "rows_tested": rows_tested,
        "rows_valid": rows_valid,
        "rows_invalid": rows_invalid,
        "missing_field_reasons": missing_field_reasons,
        "warning_reasons": warning_reasons,
        "evaluations": evaluations,
        "source_type": source_type_result,
        "execution_mode": execution_mode_result,
        "prediction_testing_started": False,
        "live_connectors_enabled": False,
        "api_calls_enabled": False,
        "database_writes_enabled": False,
    }


def decimal_to_implied_probability(decimal_odds: float) -> float:
    return _core_decimal_to_implied_probability(decimal_odds)


def break_even_probability_american(odds: int | float) -> float:
    """Minimum win rate to break even betting at these odds (equals implied prob)."""
    return _core_break_even_probability_american(odds)


def book_hold_two_way(implied_a: float, implied_b: float) -> float:
    """Overround / vig as implied_a + implied_b - 1."""
    return _core_book_hold_two_way(implied_a, implied_b)


def no_vig_probabilities_two_way(implied_a: float, implied_b: float) -> tuple[float, float]:
    return _core_no_vig_probabilities_two_way(implied_a, implied_b)


def no_vig_probabilities_three_way(p1: float, p2: float, p3: float) -> tuple[float, float, float]:
    return _core_no_vig_probabilities_three_way(p1, p2, p3)


def no_vig_probabilities_n_way(implied: list[float]) -> list[float]:
    return _core_no_vig_probabilities_n_way(implied)


def fair_odds_american_from_probability(probability: float) -> int:
    return _core_fair_odds_american_from_probability(probability)


def edge_percentage(true_probability: float, implied_probability: float) -> float:
    return _core_edge_percent(true_probability, implied_probability)


def expected_value_per_100(odds: int | float, true_probability: float) -> float:
    return _core_expected_value_per_100(odds, true_probability)


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
    return _risk_confidence_adjusted_stake(base_stake, confidence_0_100)


def risk_adjusted_stake(base_stake: float, risk_multiplier: float) -> float:
    """risk_multiplier in (0, 1] reduces stake for higher perceived risk."""
    return _risk_adjusted_stake(base_stake, risk_multiplier)


def book_hold_n_way(implied_probabilities: list[float]) -> float:
    """Total overround / vig for N outcomes: sum(implied) - 1."""
    return _core_book_hold_n_way(implied_probabilities)


def implied_probability_from_decimal(decimal_odds: float) -> float:
    return _core_implied_probability_from_decimal(decimal_odds)


def break_even_probability_decimal(decimal_odds: float) -> float:
    return _core_break_even_probability_decimal(decimal_odds)


def expected_value_per_dollar(odds: int | float, true_probability: float) -> float:
    return _core_expected_value_per_dollar(odds, true_probability)


def full_kelly_fraction(odds: int | float, true_probability: float) -> float:
    return _core_full_kelly_fraction(odds, true_probability)


def fair_decimal_odds_from_probability(probability: float) -> float:
    return _core_fair_decimal_odds_from_probability(probability)


def full_kelly_percent(odds: int | float, true_probability: float) -> float:
    return round(_core_full_kelly_percent(odds, true_probability), 4)


def fractional_kelly_percent(odds: int | float, true_probability: float, fraction: float = 0.25) -> float:
    return round(_core_fractional_kelly_percent(odds, true_probability, fraction=fraction), 4)


def risk_profile_settings(risk_profile: str | None = "standard") -> dict[str, float | str]:
    return _risk_profile_settings(risk_profile)


def suggested_stake_with_risk_controls(
    bankroll: float,
    american_odds: int | float,
    true_probability: float,
    risk_profile: str | None = "standard",
    confidence_0_100: float | None = None,
) -> float:
    return _risk_suggested_stake_with_risk_controls(
        bankroll,
        american_odds,
        true_probability,
        risk_profile,
        confidence_0_100,
    )


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

# Canonical compatibility imports
from src.core.pricing import *  # noqa: F401,F403
from src.core.probability import *  # noqa: F401,F403
from src.core.portfolio import *  # noqa: F401,F403
from src.core.execution import *  # noqa: F401,F403
from src.core.market_impact import *  # noqa: F401,F403
from src.core.game_theory import *  # noqa: F401,F403
from src.core.risk import *  # noqa: F401,F403
