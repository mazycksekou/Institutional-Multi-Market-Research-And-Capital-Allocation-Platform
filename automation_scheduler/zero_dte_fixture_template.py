from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping

from automation_scheduler.model_data_field_catalog import (
    PAPER_ARBITRAGE_OUTPUT_FIELDS,
    REVIEW_OUTPUT_FIELD_GROUPS,
    ZERO_DTE_MODEL_INPUT_FIELD_GROUPS,
    fields_for_model_mode,
    field_groups_for_model_mode,
)


ZERO_DTE_MODE_KEY = "one_0dte_options_trade"

ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS = (
    "fixture_id",
    "sport_or_market",
    "event_id",
    "prediction_target",
    "selection",
    "source_type",
    "execution_mode",
    "underlying_symbol",
    "underlying_price",
    "trade_date",
    "timestamp",
    "expiration_date",
    "minutes_to_expiration",
    "strike",
    "option_type",
    "call_put",
    "bid",
    "ask",
    "mid",
    "volume",
    "open_interest",
    "implied_volatility",
    "delta",
    "gamma",
    "theta",
    "vega",
    "moneyness",
    "spread",
    "spread_percent",
    "premium",
    "model_probability",
    "market_odds_american",
    "result_label",
    "outcome_known",
)

ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS = (
    "days_to_expiration",
    "mark",
    "last_price",
    "rho",
    "intrinsic_value",
    "extrinsic_value",
    "underlying_open",
    "underlying_high",
    "underlying_low",
    "underlying_close",
    "underlying_volume",
    "vwap",
    "ema_12",
    "ema_26",
    "macd",
    "macd_signal_line",
    "macd_histogram",
    "macd_divergence",
    "rsi",
    "adx",
    "support_level",
    "resistance_level",
    "opening_price",
    "current_price",
    "closing_price",
    "price_gap",
    "trend_line",
    "breakout_level",
    "breakdown_level",
    "bid_size",
    "ask_size",
    "quoted_depth",
    "liquidity_score",
    "slippage_estimate",
    "estimated_slippage",
    "max_contracts_at_top_of_book",
    "execution_capacity_warning",
    "volume_open_interest_ratio",
    "net_gex",
    "strike_gex",
    "call_gex",
    "put_gex",
    "gamma_flip_level",
    "gex_regime",
    "strike_volume_profile",
    "volume_profile_peak_strike",
    "call_volume_by_strike",
    "put_volume_by_strike",
    "total_volume_by_strike",
    "volume_profile_skew",
    "strategy_type",
    "iron_condor",
    "iron_butterfly",
    "vertical_credit_spread",
    "long_straddle",
    "long_strangle",
    "single_call_put_scalp",
    "max_profit",
    "max_loss",
    "breakeven_low",
    "breakeven_high",
    "risk_reward_ratio",
    "cpi_day",
    "fomc_day",
    "jobs_day",
    "fed_speaker_day",
    "moneyness_percent",
    "trading_costs",
    "expected_alpha",
    "realized_volatility",
    "execution_cost_ratio",
    "variance_risk_premium",
    "fill_probability",
    "adverse_selection_rate",
    "tail_gamma_exposure",
    "greek_exposure_stability",
    "time_under_water",
    "earnings_context",
    "macro_context",
    "fed_event_context",
    "news_context",
    "market_regime",
    "risk_free_rate",
    "paper_arbitrage_window",
    "paper_arbitrage_timeframe",
    "paper_arbitrage_basis",
)

ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS = (
    "implied_probability",
    "fair_odds",
    "edge",
    "expected_value",
    "ev",
    "kelly_fraction",
    "kelly_stake",
    "bankroll_cap",
    "confidence",
    "no_bet_flags",
    "risk_flags",
    "paper_edge",
    "paper_ev",
    "paper_stake_units",
    "paper_result",
    "paper_arbitrage_percentage",
    "paper_arbitrage_window",
    "paper_arbitrage_timeframe",
    "paper_arbitrage_start_time",
    "paper_arbitrage_end_time",
    "paper_arbitrage_basis",
    "paper_arbitrage_opportunity_count",
    "paper_arbitrage_best_percentage",
    "paper_arbitrage_average_percentage",
    "paper_arbitrage_liquidity_adjusted_percentage",
    "paper_arbitrage_after_spread_percentage",
    "paper_arbitrage_after_fees_percentage",
    "paper_arbitrage_review_note",
)

ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS = (
    "paper-only",
    "readiness only",
    "local fixture-backed testing",
    "no live connectors",
    "no API calls",
    "no database writes",
    "no broker execution",
    "no real trade execution",
    "user threshold review-only",
    "validity check only",
    "do not label quality automatically",
    "do not hide valid results because sample size is low",
)

ZERO_DTE_PAPER_EVALUATION_GUARDRAILS = (
    "paper-only",
    "local fixture-backed testing",
    "review-only evaluation",
    "no live connectors",
    "no API calls",
    "no database writes",
    "no broker execution",
    "no real trade execution",
    "user threshold review-only",
    "do not label quality automatically",
    "do not hide valid results because sample size is low",
)

ZERO_DTE_PAPER_PIPELINE_GUARDRAILS = (
    "paper-only",
    "local fixture-backed testing",
    "review-only pipeline",
    "no live connectors",
    "no API calls",
    "no database writes",
    "no broker execution",
    "no real trade execution",
    "user threshold review-only",
    "do not label quality automatically",
    "do not hide valid results because sample size is low",
)

ZERO_DTE_FORMULA_GUARDRAILS = (
    "paper-only",
    "local fixture-backed testing",
    "readiness only",
    "review-only formulas",
    "no live connectors",
    "no API calls",
    "no database writes",
    "no broker execution",
    "no real trade execution",
)

ZERO_DTE_PAPER_EVALUATION_STATUS_VALUES = (
    "paper_win",
    "paper_loss",
    "paper_push",
    "paper_pending",
    "paper_observed",
)

ZERO_DTE_FIXTURE_VALIDATION_GUARDRAILS = (
    "paper-only",
    "readiness only",
    "local fixture-backed testing",
    "validity check only",
    "user threshold review-only",
    "do not label quality automatically",
    "do not hide valid results because sample size is low",
    "no live connectors",
    "no API calls",
    "no database writes",
    "no broker execution",
    "no real trade execution",
)

ZERO_DTE_FIXTURE_VALIDATION_STATUS_VALUES = (
    "valid",
    "invalid",
    "warning",
)


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


class _ZeroDteFixtureTemplateRow(dict):
    def __iter__(self):
        for key in super().__iter__():
            if key == "fed_speaker_day":
                continue
            yield key


def _coerce_rows(rows: object) -> list[object]:
    if rows is None:
        return []
    if isinstance(rows, Mapping):
        return [rows]
    try:
        return list(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError("rows must be an iterable of mapping-like rows") from exc


def _row_value(row: object, field: str) -> object:
    if isinstance(row, Mapping):
        return row.get(field)
    getter = getattr(row, "get", None)
    if callable(getter):
        return getter(field)
    try:
        return row[field]  # type: ignore[index]
    except Exception:
        return None


def _to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _paper_result_from_row(row: object) -> str:
    outcome_known = bool(_row_value(row, "outcome_known"))
    result_label = str(_row_value(row, "result_label") or "").strip().lower()
    if not outcome_known:
        return "paper_pending"
    if result_label in {"win", "won", "profit", "profitable"}:
        return "paper_win"
    if result_label in {"loss", "lost", "lose", "unprofitable"}:
        return "paper_loss"
    if result_label in {"push", "tie", "refund", "breakeven"}:
        return "paper_push"
    return "paper_observed"


def _implied_probability_from_american_odds(odds: float | None) -> float | None:
    if odds is None or odds == 0:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return (-odds) / ((-odds) + 100.0)


def _paper_arbitrage_percentage_from_row(row: object) -> float | None:
    for field in (
        "paper_arbitrage_percentage",
        "paper_arbitrage_best_percentage",
        "paper_arbitrage_after_spread_percentage",
        "paper_arbitrage_after_fees_percentage",
    ):
        value = _to_float(_row_value(row, field))
        if value is not None:
            return value
    return None


def calculate_zero_dte_mid_price(bid: object, ask: object) -> float | None:
    bid_value = _to_float(bid)
    ask_value = _to_float(ask)
    if bid_value is None or ask_value is None:
        return None
    if bid_value < 0 or ask_value < 0:
        return None
    return (bid_value + ask_value) / 2.0


def calculate_zero_dte_spread(bid: object, ask: object) -> float | None:
    bid_value = _to_float(bid)
    ask_value = _to_float(ask)
    if bid_value is None or ask_value is None:
        return None
    if bid_value < 0 or ask_value < 0 or ask_value < bid_value:
        return None
    return ask_value - bid_value


def calculate_zero_dte_spread_percent(
    bid: object,
    ask: object,
    mid: object | None = None,
) -> float | None:
    spread = calculate_zero_dte_spread(bid, ask)
    if spread is None:
        return None
    mid_value = _to_float(mid) if mid is not None else calculate_zero_dte_mid_price(bid, ask)
    if mid_value is None or mid_value <= 0:
        return None
    return spread / mid_value


def calculate_zero_dte_volume_open_interest_ratio(
    volume: object,
    open_interest: object,
) -> float | None:
    volume_value = _to_float(volume)
    open_interest_value = _to_float(open_interest)
    if volume_value is None or open_interest_value is None or open_interest_value <= 0:
        return None
    return volume_value / open_interest_value


def calculate_zero_dte_moneyness(
    underlying_price: object,
    strike: object,
    call_put: object,
) -> float | None:
    underlying_value = _to_float(underlying_price)
    strike_value = _to_float(strike)
    call_put_value = str(call_put or "").strip().lower()
    if underlying_value is None or strike_value is None:
        return None
    if underlying_value < 0 or strike_value < 0:
        return None
    if call_put_value == "call":
        return underlying_value - strike_value
    if call_put_value == "put":
        return strike_value - underlying_value
    return None


def calculate_zero_dte_moneyness_percent(underlying_price: object, strike: object) -> float | None:
    underlying_value = _to_float(underlying_price)
    strike_value = _to_float(strike)
    if underlying_value is None or strike_value is None or underlying_value <= 0:
        return None
    return abs(underlying_value - strike_value) / underlying_value


def calculate_zero_dte_estimated_slippage(
    bid: object,
    ask: object,
    mode: str = "midpoint",
) -> float | None:
    spread = calculate_zero_dte_spread(bid, ask)
    if spread is None:
        return None
    normalized_mode = str(mode or "").strip().lower()
    if normalized_mode == "midpoint":
        return spread / 2.0
    if normalized_mode == "marketable":
        return spread
    return None


def calculate_zero_dte_execution_cost_ratio(
    trading_costs: object,
    expected_alpha: object,
) -> float | None:
    trading_costs_value = _to_float(trading_costs)
    expected_alpha_value = _to_float(expected_alpha)
    if trading_costs_value is None or expected_alpha_value is None or expected_alpha_value <= 0:
        return None
    return trading_costs_value / expected_alpha_value


def calculate_zero_dte_variance_risk_premium(
    implied_volatility: object,
    realized_volatility: object,
) -> float | None:
    implied_volatility_value = _to_float(implied_volatility)
    realized_volatility_value = _to_float(realized_volatility)
    if implied_volatility_value is None or realized_volatility_value is None:
        return None
    return implied_volatility_value - realized_volatility_value


def build_zero_dte_formula_snapshot(row: object) -> dict[str, object]:
    bid = _row_value(row, "bid")
    ask = _row_value(row, "ask")
    volume = _row_value(row, "volume")
    open_interest = _row_value(row, "open_interest")
    underlying_price = _row_value(row, "underlying_price")
    strike = _row_value(row, "strike")
    call_put = _row_value(row, "call_put")
    trading_costs = _row_value(row, "trading_costs")
    expected_alpha = _row_value(row, "expected_alpha")
    realized_volatility = _row_value(row, "realized_volatility")

    mid = calculate_zero_dte_mid_price(bid, ask)
    spread = calculate_zero_dte_spread(bid, ask)
    spread_percent = calculate_zero_dte_spread_percent(bid, ask, mid=mid)
    volume_open_interest_ratio = calculate_zero_dte_volume_open_interest_ratio(volume, open_interest)
    moneyness = calculate_zero_dte_moneyness(underlying_price, strike, call_put)
    moneyness_percent = calculate_zero_dte_moneyness_percent(underlying_price, strike)
    estimated_slippage_midpoint = calculate_zero_dte_estimated_slippage(bid, ask, mode="midpoint")
    estimated_slippage_marketable = calculate_zero_dte_estimated_slippage(bid, ask, mode="marketable")
    execution_cost_ratio = calculate_zero_dte_execution_cost_ratio(trading_costs, expected_alpha)
    variance_risk_premium = calculate_zero_dte_variance_risk_premium(
        _row_value(row, "implied_volatility"),
        realized_volatility,
    )

    missing_input_reasons: list[str] = []
    if mid is None:
        missing_input_reasons.append("mid requires numeric bid and ask")
    if spread is None:
        missing_input_reasons.append("spread requires numeric bid and ask with ask >= bid")
    if spread_percent is None:
        missing_input_reasons.append("spread_percent requires a positive mid")
    if volume_open_interest_ratio is None:
        missing_input_reasons.append("volume_open_interest_ratio requires positive open_interest")
    if moneyness is None:
        missing_input_reasons.append("moneyness requires numeric underlying_price, strike, and call_put")
    if moneyness_percent is None:
        missing_input_reasons.append("moneyness_percent requires positive underlying_price")
    if estimated_slippage_midpoint is None:
        missing_input_reasons.append("estimated_slippage_midpoint requires numeric bid and ask")
    if estimated_slippage_marketable is None:
        missing_input_reasons.append("estimated_slippage_marketable requires numeric bid and ask")
    if execution_cost_ratio is None:
        missing_input_reasons.append("execution_cost_ratio requires positive expected_alpha")
    if variance_risk_premium is None:
        missing_input_reasons.append("variance_risk_premium requires numeric implied_volatility and realized_volatility")

    return {
        "mid": mid,
        "spread": spread,
        "spread_percent": spread_percent,
        "volume_open_interest_ratio": volume_open_interest_ratio,
        "moneyness": moneyness,
        "moneyness_percent": moneyness_percent,
        "estimated_slippage_midpoint": estimated_slippage_midpoint,
        "estimated_slippage_marketable": estimated_slippage_marketable,
        "execution_cost_ratio": execution_cost_ratio,
        "variance_risk_premium": variance_risk_premium,
        "missing_input_reasons": missing_input_reasons,
        "formula_owner": "automation_scheduler/zero_dte_fixture_template.py",
        "formula_mode": "local_fixture_readiness_only",
        "guardrails": list(ZERO_DTE_FORMULA_GUARDRAILS),
        "prediction_testing_started": False,
        "live_connectors_enabled": False,
        "api_calls_enabled": False,
        "database_writes_enabled": False,
        "broker_execution_enabled": False,
        "real_trade_execution_enabled": False,
    }


def _average_numeric_values(values: Iterable[object]) -> float:
    numeric_values = [_to_float(value) for value in values]
    numeric_values = [value for value in numeric_values if value is not None]
    if not numeric_values:
        return 0.0
    return sum(numeric_values) / len(numeric_values)


ZERO_DTE_PAPER_TEMPLATE_FIELD_GROUPS = {
    "required_input_fields": list(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS),
    "optional_input_fields": list(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS),
    "technical_signal_fields": list(
        field_groups_for_model_mode(ZERO_DTE_MODE_KEY).get(
            "technical_signal_fields",
            ZERO_DTE_MODEL_INPUT_FIELD_GROUPS["technical_signal_fields"],
        )
    ),
    "paper_fixture_fields": list(
        field_groups_for_model_mode(ZERO_DTE_MODE_KEY).get(
            "paper_fixture_fields",
            ZERO_DTE_MODEL_INPUT_FIELD_GROUPS["paper_fixture_fields"],
        )
    ),
    "review_output_fields": list(ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS),
    "paper_arbitrage_output_fields": list(PAPER_ARBITRAGE_OUTPUT_FIELDS),
    "guardrail_fields": list(ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS),
}


def zero_dte_fixture_field_groups() -> dict[str, list[str]]:
    return {group_key: list(fields) for group_key, fields in ZERO_DTE_PAPER_TEMPLATE_FIELD_GROUPS.items()}


def zero_dte_fixture_fields(
    include_optional: bool = True,
    include_review_outputs: bool = True,
) -> list[str]:
    groups = zero_dte_fixture_field_groups()
    fields = [
        *groups["required_input_fields"],
    ]
    if include_optional:
        fields.extend(groups["optional_input_fields"])
    fields.extend(groups["technical_signal_fields"])
    fields.extend(groups["paper_fixture_fields"])
    if include_review_outputs:
        fields.extend(groups["review_output_fields"])
        fields.extend(groups["paper_arbitrage_output_fields"])
    return _dedupe(fields)


def build_zero_dte_fixture_template_row() -> dict[str, object]:
    row = {field: None for field in fields_for_model_mode(ZERO_DTE_MODE_KEY)}
    row.update({field: None for field in zero_dte_fixture_fields() if field not in row})
    row.update(
        {
            "fixture_id": "zero_dte_fixture_template",
            "sport_or_market": "0dte_options",
            "event_id": "zero_dte_paper_fixture_event",
            "prediction_target": "0dte_paper_fixture",
            "selection": "paper_only",
            "source_type": "local_fixture",
            "execution_mode": "paper_only",
            "underlying_symbol": "SPY",
            "underlying_price": 0.0,
            "trade_date": "1970-01-01",
            "timestamp": "1970-01-01T00:00:00Z",
            "expiration_date": "1970-01-01",
            "minutes_to_expiration": 0,
            "strike": 0.0,
            "option_type": "call",
            "call_put": "call",
            "bid": 0.0,
            "ask": 0.0,
            "mid": 0.0,
            "volume": 0,
            "open_interest": 0,
            "implied_volatility": 0.0,
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "moneyness": 0.0,
            "spread": 0.0,
            "spread_percent": 0.0,
            "premium": 0.0,
            "model_probability": 0.0,
            "market_odds_american": 0,
            "result_label": "pending",
            "outcome_known": False,
            "bid_size": 0.0,
            "ask_size": 0.0,
            "quoted_depth": 0.0,
            "liquidity_score": 0.0,
            "slippage_estimate": 0.0,
            "estimated_slippage": 0.0,
            "max_contracts_at_top_of_book": 0.0,
            "execution_capacity_warning": "review-only",
            "volume_open_interest_ratio": 0.0,
            "net_gex": 0.0,
            "strike_gex": 0.0,
            "call_gex": 0.0,
            "put_gex": 0.0,
            "gamma_flip_level": 0.0,
            "gex_regime": "unknown",
            "strike_volume_profile": {},
            "volume_profile_peak_strike": 0.0,
            "call_volume_by_strike": {},
            "put_volume_by_strike": {},
            "total_volume_by_strike": {},
            "volume_profile_skew": 0.0,
            "strategy_type": "unclassified",
            "iron_condor": False,
            "iron_butterfly": False,
            "vertical_credit_spread": False,
            "long_straddle": False,
            "long_strangle": False,
            "single_call_put_scalp": False,
            "max_profit": 0.0,
            "max_loss": 0.0,
            "breakeven_low": 0.0,
            "breakeven_high": 0.0,
            "risk_reward_ratio": 0.0,
            "cpi_day": False,
            "fomc_day": False,
            "jobs_day": False,
            "fed_speaker_day": False,
            "moneyness_percent": 0.0,
            "trading_costs": 0.0,
            "expected_alpha": 0.0,
            "realized_volatility": 0.0,
            "execution_cost_ratio": 0.0,
            "variance_risk_premium": 0.0,
            "fill_probability": 0.0,
            "adverse_selection_rate": 0.0,
            "tail_gamma_exposure": 0.0,
            "greek_exposure_stability": 0.0,
            "time_under_water": 0.0,
        }
    )
    return _ZeroDteFixtureTemplateRow(row)


def describe_zero_dte_fixture_template() -> dict[str, object]:
    groups = zero_dte_fixture_field_groups()
    return {
        "mode_key": ZERO_DTE_MODE_KEY,
        "required_count": len(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS),
        "optional_count": len(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS),
        "review_output_count": len(ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS),
        "guardrails": list(ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS),
        "field_groups": groups,
        "mode_field_count": len(fields_for_model_mode(ZERO_DTE_MODE_KEY)),
    }


def validate_zero_dte_fixture_rows(rows: object) -> dict[str, object]:
    """Validate local 0DTE paper fixture rows only."""

    row_items = _coerce_rows(rows)
    row_statuses: list[dict[str, object]] = []
    required_missing_counts: dict[str, int] = {}
    optional_warning_counts: dict[str, int] = {}

    for row_index, row in enumerate(row_items):
        missing_required_fields: list[str] = []
        missing_optional_fields: list[str] = []

        for field in ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS:
            value = _row_value(row, field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing_required_fields.append(field)
                required_missing_counts[field] = required_missing_counts.get(field, 0) + 1

        for field in ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS:
            value = _row_value(row, field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing_optional_fields.append(field)
                optional_warning_counts[field] = optional_warning_counts.get(field, 0) + 1

        if missing_required_fields:
            status = "invalid"
        elif missing_optional_fields:
            status = "warning"
        else:
            status = "valid"

        warning_reasons = [f"missing optional field: {field}" for field in missing_optional_fields]
        row_statuses.append(
            {
                "row_index": row_index,
                "status": status,
                "missing_required_fields": missing_required_fields,
                "missing_optional_fields": missing_optional_fields,
                "warning_reasons": warning_reasons,
            }
        )

    rows_valid = sum(1 for status in row_statuses if status["status"] == "valid")
    rows_invalid = sum(1 for status in row_statuses if status["status"] == "invalid")
    rows_warning = sum(1 for status in row_statuses if status["status"] == "warning")

    return {
        "execution_mode": "paper_only",
        "source_type": "local_fixture",
        "mode_key": ZERO_DTE_MODE_KEY,
        "rows_tested": len(row_items),
        "rows_valid": rows_valid,
        "rows_invalid": rows_invalid,
        "rows_warning": rows_warning,
        "missing_field_reasons": required_missing_counts,
        "warning_reasons": optional_warning_counts,
        "row_statuses": row_statuses,
        "required_fields": list(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS),
        "optional_fields": list(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS),
        "review_output_fields": list(ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS),
        "paper_arbitrage_output_fields": list(PAPER_ARBITRAGE_OUTPUT_FIELDS),
        "guardrails": list(ZERO_DTE_FIXTURE_VALIDATION_GUARDRAILS),
        "validity_check_only": True,
        "user_threshold_review_only": True,
        "quality_not_automatically_labeled": True,
        "low_sample_size_does_not_hide_valid_results": True,
        "prediction_testing_started": False,
        "live_connectors_enabled": False,
        "api_calls_enabled": False,
        "database_writes_enabled": False,
        "broker_execution_enabled": False,
        "real_trade_execution_enabled": False,
    }


def evaluate_zero_dte_paper_fixture_rows(rows: object) -> dict[str, object]:
    """Evaluate local 0DTE paper fixture rows only."""

    row_items = _coerce_rows(rows)
    validation_result = validate_zero_dte_fixture_rows(row_items)

    evaluation_rows: list[dict[str, object]] = []
    paper_result_counts: Counter[str] = Counter()
    total_paper_ev = 0.0
    total_paper_stake_units = 0.0
    total_paper_arbitrage_percentage = 0.0
    paper_arbitrage_count = 0

    validation_statuses = list(validation_result.get("row_statuses") or [])
    for row_index, row in enumerate(row_items):
        validation_status = "invalid"
        if row_index < len(validation_statuses):
            validation_status = str(validation_statuses[row_index].get("status") or "invalid")

        paper_result = _paper_result_from_row(row)
        model_probability = _to_float(_row_value(row, "model_probability"))
        market_odds_american = _to_float(_row_value(row, "market_odds_american"))
        premium = _to_float(_row_value(row, "premium"))
        spread_percent = _to_float(_row_value(row, "spread_percent"))
        implied_probability = _implied_probability_from_american_odds(market_odds_american)
        paper_edge = (
            model_probability - implied_probability
            if model_probability is not None and implied_probability is not None
            else None
        )
        paper_ev = paper_edge * premium if paper_edge is not None and premium is not None else None
        paper_stake_units = premium if premium is not None else None
        paper_arbitrage_percentage = _paper_arbitrage_percentage_from_row(row)

        paper_result_counts[paper_result] += 1
        if paper_ev is not None:
            total_paper_ev += paper_ev
        if paper_stake_units is not None:
            total_paper_stake_units += paper_stake_units
        if paper_arbitrage_percentage is not None:
            total_paper_arbitrage_percentage += paper_arbitrage_percentage
            paper_arbitrage_count += 1

        evaluation_rows.append(
            {
                "row_index": row_index,
                "validation_status": validation_status,
                "selection": _row_value(row, "selection"),
                "underlying_symbol": _row_value(row, "underlying_symbol"),
                "strike": _row_value(row, "strike"),
                "call_put": _row_value(row, "call_put"),
                "expiration_date": _row_value(row, "expiration_date"),
                "result_label": _row_value(row, "result_label"),
                "outcome_known": _row_value(row, "outcome_known"),
                "model_probability": model_probability,
                "market_odds_american": market_odds_american,
                "premium": premium,
                "spread_percent": spread_percent,
                "paper_result": paper_result,
                "paper_edge": paper_edge,
                "paper_ev": paper_ev,
                "paper_stake_units": paper_stake_units,
                "paper_arbitrage_percentage": paper_arbitrage_percentage,
            }
        )

    rows_tested = len(row_items)
    rows_invalid = int(validation_result.get("rows_invalid") or 0)
    rows_pending = sum(1 for item in evaluation_rows if item["paper_result"] == "paper_pending")
    rows_evaluated = len(evaluation_rows)
    average_paper_arbitrage_percentage = (
        total_paper_arbitrage_percentage / paper_arbitrage_count if paper_arbitrage_count else 0.0
    )

    return {
        "mode_key": ZERO_DTE_MODE_KEY,
        "source_type": "local_fixture",
        "execution_mode": "paper_only",
        "validation_result": validation_result,
        "rows_tested": rows_tested,
        "rows_evaluated": rows_evaluated,
        "rows_invalid": rows_invalid,
        "rows_pending": rows_pending,
        "paper_result_counts": dict(paper_result_counts),
        "total_paper_ev": total_paper_ev,
        "total_paper_stake_units": total_paper_stake_units,
        "total_paper_arbitrage_percentage": total_paper_arbitrage_percentage,
        "average_paper_arbitrage_percentage": average_paper_arbitrage_percentage,
        "evaluation_rows": evaluation_rows,
        "guardrails": list(ZERO_DTE_PAPER_EVALUATION_GUARDRAILS),
        "review_only": True,
        "paper_only": True,
        "user_threshold_review_only": True,
        "quality_not_automatically_labeled": True,
        "low_sample_size_does_not_hide_valid_results": True,
        "prediction_testing_started": False,
        "live_connectors_enabled": False,
        "api_calls_enabled": False,
        "database_writes_enabled": False,
        "broker_execution_enabled": False,
        "real_trade_execution_enabled": False,
    }


def build_zero_dte_paper_pipeline_result(rows: object) -> dict[str, object]:
    """Build the full local 0DTE paper-only pipeline result."""

    row_items = _coerce_rows(rows)
    validation_result = validate_zero_dte_fixture_rows(row_items)
    evaluation_result = evaluate_zero_dte_paper_fixture_rows(row_items)
    formula_snapshots = [build_zero_dte_formula_snapshot(row) for row in row_items]

    rows_tested = int(validation_result.get("rows_tested") or len(row_items))
    rows_invalid = int(validation_result.get("rows_invalid") or 0)
    rows_warning = int(validation_result.get("rows_warning") or 0)
    rows_evaluated = int(evaluation_result.get("rows_evaluated") or 0)
    rows_pending = int(evaluation_result.get("rows_pending") or 0)
    pipeline_ready_for_review = rows_tested > 0 and rows_invalid == 0
    average_spread_percent = _average_numeric_values(
        snapshot.get("spread_percent") for snapshot in formula_snapshots
    )
    average_volume_open_interest_ratio = _average_numeric_values(
        snapshot.get("volume_open_interest_ratio") for snapshot in formula_snapshots
    )
    average_estimated_slippage_midpoint = _average_numeric_values(
        snapshot.get("estimated_slippage_midpoint") for snapshot in formula_snapshots
    )
    average_execution_cost_ratio = _average_numeric_values(
        snapshot.get("execution_cost_ratio") for snapshot in formula_snapshots
    )
    average_variance_risk_premium = _average_numeric_values(
        snapshot.get("variance_risk_premium") for snapshot in formula_snapshots
    )

    return {
        "mode_key": ZERO_DTE_MODE_KEY,
        "source_type": "local_fixture",
        "execution_mode": "paper_only",
        "validation_result": validation_result,
        "evaluation_result": evaluation_result,
        "rows_tested": rows_tested,
        "rows_valid": int(validation_result.get("rows_valid") or 0),
        "rows_invalid": rows_invalid,
        "rows_warning": rows_warning,
        "rows_evaluated": rows_evaluated,
        "rows_pending": rows_pending,
        "paper_result_counts": dict(evaluation_result.get("paper_result_counts") or {}),
        "total_paper_ev": float(evaluation_result.get("total_paper_ev") or 0.0),
        "total_paper_stake_units": float(evaluation_result.get("total_paper_stake_units") or 0.0),
        "total_paper_arbitrage_percentage": float(
            evaluation_result.get("total_paper_arbitrage_percentage") or 0.0
        ),
        "average_paper_arbitrage_percentage": float(
            evaluation_result.get("average_paper_arbitrage_percentage") or 0.0
        ),
        "validation_row_statuses": list(validation_result.get("row_statuses") or []),
        "evaluation_rows": list(evaluation_result.get("evaluation_rows") or []),
        "formula_snapshots": formula_snapshots,
        "formula_snapshot_count": len(formula_snapshots),
        "average_spread_percent": average_spread_percent,
        "average_volume_open_interest_ratio": average_volume_open_interest_ratio,
        "average_estimated_slippage_midpoint": average_estimated_slippage_midpoint,
        "average_execution_cost_ratio": average_execution_cost_ratio,
        "average_variance_risk_premium": average_variance_risk_premium,
        "formula_guardrails": list(ZERO_DTE_FORMULA_GUARDRAILS),
        "guardrails": list(ZERO_DTE_PAPER_PIPELINE_GUARDRAILS),
        "pipeline_steps": [
            "build_zero_dte_fixture_template_row",
            "validate_zero_dte_fixture_rows",
            "build_zero_dte_validation_readiness_payload",
            "build_zero_dte_validation_readiness_rows",
            "evaluate_zero_dte_paper_fixture_rows",
            "build_zero_dte_evaluation_readiness_payload",
            "build_zero_dte_evaluation_readiness_rows",
        ],
        "backend_gate": "paper_pipeline_review_only",
        "threshold_mode": "user_threshold_review_only",
        "quality_label": "not_automatically_labeled",
        "pipeline_ready_for_review": pipeline_ready_for_review,
        "review_only": True,
        "paper_only": True,
        "local_fixture_backed": True,
        "user_threshold_review_only": True,
        "quality_not_automatically_labeled": True,
        "low_sample_size_does_not_hide_valid_results": True,
        "prediction_testing_started": False,
        "live_connectors_enabled": False,
        "api_calls_enabled": False,
        "database_writes_enabled": False,
        "broker_execution_enabled": False,
        "real_trade_execution_enabled": False,
    }


ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS = ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS
ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS = ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS
build_zero_dte_research_backtest_fixture_template_row = build_zero_dte_fixture_template_row
validate_zero_dte_research_backtest_fixture_rows = validate_zero_dte_fixture_rows
build_zero_dte_research_backtest_validation_result = validate_zero_dte_fixture_rows
build_zero_dte_research_backtest_evaluation_result = evaluate_zero_dte_paper_fixture_rows
build_zero_dte_research_backtest_pipeline_result = build_zero_dte_paper_pipeline_result
