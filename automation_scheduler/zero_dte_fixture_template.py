from __future__ import annotations

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
        }
    )
    return row


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
