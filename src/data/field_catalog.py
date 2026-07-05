from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.backtesting.dataset_builder import (
    PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS,
    PAPER_ONLY_FIXTURE_REQUIRED_FIELDS,
)


READINESS_DISPLAY_FIELDS: list[str] = [
    "validation_result",
    "evaluation_result",
    "readiness_payload",
    "readiness_rows",
    "validation_status",
    "threshold_review_only",
    "validity_is_backend_gate",
    "low_sample_size_does_not_hide_valid_results",
    "quality_not_automatically_labeled",
    "prediction_testing_started",
    "live_connectors_enabled",
    "api_calls_enabled",
    "database_writes_enabled",
]

REVIEW_OUTPUT_FIELD_GROUPS: dict[str, list[str]] = {
    "universal_row_identity_fields": [
        "fixture_id",
        "sport_or_market",
        "market_type",
        "asset_class",
        "event_id",
        "event_name",
        "event_date",
        "timestamp",
        "prediction_target",
        "selection",
        "source_type",
        "execution_mode",
        "data_source_name",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
    ],
    "readiness_output_fields": list(READINESS_DISPLAY_FIELDS),
    "evaluation_output_fields": [
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "evaluations",
        "evaluations_count",
        "paper_result_counts",
        "total_paper_ev",
        "total_paper_stake_units",
    ],
    "pipeline_output_fields": [
        "validation_result",
        "evaluation_result",
        "readiness_payload",
        "readiness_rows",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "evaluations_count",
        "paper_result_counts",
        "total_paper_ev",
        "total_paper_stake_units",
        "validation_status",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
    ],
    "universal_math_output_fields": [
        "implied_probability",
        "fair_odds",
        "break_even_probability",
        "no_vig_probability",
        "edge",
        "edge_percent",
        "expected_value",
        "ev",
        "kelly_fraction",
        "kelly_stake",
        "bankroll_cap",
        "recommended_stake",
        "confidence",
        "confidence_score",
        "no_bet_flags",
    ],
    "paper_arbitrage_output_fields": [
        "validation_result",
        "evaluation_result",
        "readiness_payload",
        "readiness_rows",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "evaluations_count",
        "paper_result_counts",
        "total_paper_ev",
        "total_paper_stake_units",
    ],
}


OHLCV_FIELDS: list[str] = ["timestamp", "open", "high", "low", "close", "volume"]
TECHNICAL_INDICATOR_FIELDS: list[str] = [
    "ema_12",
    "ema_26",
    "macd",
    "macd_signal_line",
    "macd_histogram",
    "macd_divergence",
    "vwap",
    "rsi",
    "adx",
]
MARKET_PARTICIPATION_FIELDS: list[str] = ["market_breadth", "order_flow", "open_interest"]

TECHNICAL_SIGNAL_FIELDS: list[str] = [
    *OHLCV_FIELDS,
    *TECHNICAL_INDICATOR_FIELDS,
    *MARKET_PARTICIPATION_FIELDS,
    "bid_size",
    "ask_size",
    "quoted_depth",
    "volume_open_interest_ratio",
    "net_gex",
    "strike_gex",
    "call_gex",
    "put_gex",
    "gamma_flip_level",
    "gex_regime",
    "strike_volume_profile",
    "volume_profile_peak_strike",
    "cpi_day",
    "fomc_day",
    "jobs_day",
    "fed_speaker_day",
]

TECHNICAL_SIGNAL_FIELDS_BY_MARKET: dict[str, dict[str, list[str]]] = {
    "stocks": {
        "required": [*OHLCV_FIELDS, *TECHNICAL_INDICATOR_FIELDS, "market_breadth"],
        "optional": ["order_flow", "open_interest"],
    },
    "ETFs": {
        "required": [*OHLCV_FIELDS, *TECHNICAL_INDICATOR_FIELDS, "market_breadth"],
        "optional": ["order_flow", "open_interest"],
    },
    "crypto": {
        "required": [*OHLCV_FIELDS, *TECHNICAL_INDICATOR_FIELDS, "order_flow", "open_interest"],
        "optional": ["market_breadth"],
    },
    "prediction_markets": {
        "required": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal_line",
            "macd_histogram",
            "macd_divergence",
            "rsi",
            "adx",
            "open_interest",
        ],
        "optional": ["vwap", "order_flow", "market_breadth"],
    },
    "sports_odds": {
        "required": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal_line",
            "macd_histogram",
            "macd_divergence",
            "rsi",
            "adx",
        ],
        "optional": ["vwap", "order_flow", "open_interest", "market_breadth"],
    },
    "0dte_options": {
        "required": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal_line",
            "macd_histogram",
            "macd_divergence",
            "vwap",
            "rsi",
            "adx",
        ],
        "optional": [
            "market_breadth",
            "order_flow",
            "open_interest",
            "bid_size",
            "ask_size",
            "quoted_depth",
            "volume_open_interest_ratio",
            "net_gex",
            "strike_gex",
            "call_gex",
            "put_gex",
            "gamma_flip_level",
            "gex_regime",
            "strike_volume_profile",
            "volume_profile_peak_strike",
            "cpi_day",
            "fomc_day",
            "jobs_day",
            "fed_speaker_day",
        ],
    },
}

PAPER_ARBITRAGE_OUTPUT_FIELDS: list[str] = [
    "validation_result",
    "evaluation_result",
    "readiness_payload",
    "readiness_rows",
    "rows_tested",
    "rows_valid",
    "rows_invalid",
    "missing_field_reasons",
    "warning_reasons",
    "evaluations_count",
    "paper_result_counts",
    "total_paper_ev",
    "total_paper_stake_units",
    "paper_arbitrage_percentage",
    "paper_arbitrage_window",
    "paper_arbitrage_timeframe",
    "paper_arbitrage_best_percentage",
    "paper_arbitrage_liquidity_adjusted_percentage",
    "paper_arbitrage_after_spread_percentage",
    "paper_arbitrage_after_fees_percentage",
]

REQUIRED_FIELD_GROUPS: dict[str, list[str]] = {
    "core_event": [
        "sport",
        "league",
        "event_date",
        "home_team",
        "away_team",
    ],
    "line_core": [
        "market",
        "selection",
        "odds_at_decision_time",
        "market_implied_probability",
        "bookmaker",
        "line_value",
    ],
    "line_movement": [
        "opening_odds",
        "closing_odds",
        "opening_line",
        "closing_line",
        "current_odds",
        "current_line",
        "snapshot_time",
        "clv",
    ],
    "settlement": [
        "final_result",
        "winner",
        "home_score",
        "away_score",
        "profit_loss",
    ],
    "team_stats": [
        "home_team_stats",
        "away_team_stats",
        "pace",
        "offensive_rating",
        "defensive_rating",
        "rest_days",
        "injuries",
    ],
    "player_stats": [
        "player_name",
        "player_team",
        "player_prop_type",
        "player_line",
        "player_minutes",
        "player_usage",
        "recent_player_average",
        "opponent_allowed_stat",
    ],
    "projection_control": [
        "model_probability",
        "features_known_at_decision_time",
    ],
}

ZERO_DTE_MODEL_INPUT_FIELD_GROUPS: dict[str, list[str]] = {
    "technical_signal_fields": TECHNICAL_SIGNAL_FIELDS_BY_MARKET["0dte_options"]["required"]
    + TECHNICAL_SIGNAL_FIELDS_BY_MARKET["0dte_options"]["optional"],
    "paper_fixture_fields": [
        *PAPER_ONLY_FIXTURE_REQUIRED_FIELDS,
        *PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS,
    ],
}


def technical_fields_for_market(market: str, include_optional: bool = True) -> list[str]:
    spec = TECHNICAL_SIGNAL_FIELDS_BY_MARKET.get(market, {})
    fields = list(spec.get("required", []))
    if include_optional:
        fields.extend(spec.get("optional", []))
    return list(dict.fromkeys(fields))


def field_groups_for_model_mode(mode: str) -> dict[str, list[str]]:
    from src.data.model_data_field_catalog import (
        field_groups_for_model_mode as legacy_field_groups_for_model_mode,
    )

    return legacy_field_groups_for_model_mode(mode)


def fields_for_model_mode(mode: str) -> list[str]:
    from src.data.model_data_field_catalog import (
        fields_for_model_mode as legacy_fields_for_model_mode,
    )

    return legacy_fields_for_model_mode(mode)


def classify_market_family(market: str | None, selection: str | None = None) -> str:
    if not market:
        return "unknown"
    lower = market.lower().replace(" ", "").replace("-", "").replace("_", "")
    if lower in ("1x2", "moneyline", "ml"):
        return "moneyline_or_1x2"
    if lower in ("runline", "spread", "pointspread"):
        return "spread_or_runline"
    if lower in ("total", "overunder", "totals", "over/under", "o/u", "ou", "gametotal", "totalpoints"):
        return "total"
    if lower.startswith("team_total") or lower in ("team total",):
        return "team_total"
    if selection and "player" in selection.lower():
        return "player_prop"
    if lower in (
        "playerpoints",
        "playerpointsprop",
        "playerprop",
        "player_points",
        "player_points_prop",
    ):
        return "player_prop"
    return "unknown"


def get_required_field_groups_for_market(market_family: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {
        "core_event": REQUIRED_FIELD_GROUPS["core_event"],
        "line_core": REQUIRED_FIELD_GROUPS["line_core"],
        "settlement": REQUIRED_FIELD_GROUPS["settlement"],
        "projection_control": REQUIRED_FIELD_GROUPS["projection_control"],
    }
    if market_family == "player_prop":
        groups["player_stats"] = REQUIRED_FIELD_GROUPS["player_stats"]
    if market_family in ("spread_or_runline", "total", "team_total"):
        groups["line_movement"] = REQUIRED_FIELD_GROUPS["line_movement"]
    return groups


def calculate_field_coverage(
    rows: list[dict[str, Any]],
    required_groups: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    coverage: dict[str, dict[str, Any]] = {}
    total = len(rows) or 1
    for group_name, fields in required_groups.items():
        for field in fields:
            present_count = sum(1 for row in rows if field in row and row[field] is not None)
            missing_count = len(rows) - present_count
            coverage_percent = round(present_count / total * 100, 1)
            if coverage_percent >= 99:
                status = "good"
            elif coverage_percent > 0:
                status = "partial"
            else:
                status = "missing"
            coverage[field] = {
                "present_count": present_count,
                "missing_count": missing_count,
                "coverage_percent": coverage_percent,
                "status": status,
                "group": group_name,
            }
    return coverage


def build_market_readiness_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "projection_ready": False,
            "settlement_ready": False,
            "line_movement_ready": False,
            "player_prop_ready": False,
            "team_stats_ready": False,
            "critical_missing_fields": ["No rows available"],
            "warnings": [],
            "reason": "No rows available",
        }

    core_present = any(
        row.get("sport")
        and row.get("league")
        and row.get("event_date")
        and row.get("home_team")
        and row.get("away_team")
        for row in rows
    )
    line_core_present = any(
        row.get("market")
        and row.get("selection")
        and row.get("odds_at_decision_time") is not None
        and row.get("market_implied_probability") is not None
        for row in rows
    )
    settlement_ready = any(
        row.get("final_result") is not None
        or row.get("winner") is not None
        or row.get("home_score") is not None
        for row in rows
    )
    line_movement_ready = any(
        row.get("opening_odds") is not None
        or row.get("closing_odds") is not None
        or row.get("current_odds") is not None
        or row.get("opening_line") is not None
        or row.get("closing_line") is not None
        or row.get("clv") is not None
        for row in rows
    )
    player_prop_ready = any(
        row.get("player_name") is not None
        and row.get("player_prop_type") is not None
        and row.get("player_line") is not None
        for row in rows
    )
    team_stats_ready = any(
        row.get("home_team_stats") is not None
        or row.get("away_team_stats") is not None
        or row.get("pace") is not None
        for row in rows
    )

    critical_missing: list[str] = []
    if not core_present:
        critical_missing.append("Core event fields (sport, league, event_date, home_team, away_team)")
    if not line_core_present:
        critical_missing.append(
            "Line core fields (market, selection, odds_at_decision_time, market_implied_probability)"
        )
    if not settlement_ready:
        critical_missing.append("Settlement data (final_result, winner, scores)")
    projection_ready = core_present and line_core_present and settlement_ready

    warnings: list[str] = []
    if not line_movement_ready:
        warnings.append("No line movement data (opening/closing odds). ROI may be unreliable.")
    if not player_prop_ready:
        warnings.append("No player prop data.")
    if not team_stats_ready:
        warnings.append("No team stats data.")

    reason = "; ".join(critical_missing) if critical_missing else "Data sufficient for projection."
    return {
        "projection_ready": projection_ready,
        "settlement_ready": settlement_ready,
        "line_movement_ready": line_movement_ready,
        "player_prop_ready": player_prop_ready,
        "team_stats_ready": team_stats_ready,
        "critical_missing_fields": critical_missing,
        "warnings": warnings,
        "reason": reason,
    }


__all__ = [
    "OHLCV_FIELDS",
    "PAPER_ARBITRAGE_OUTPUT_FIELDS",
    "PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS",
    "PAPER_ONLY_FIXTURE_REQUIRED_FIELDS",
    "READINESS_DISPLAY_FIELDS",
    "REVIEW_OUTPUT_FIELD_GROUPS",
    "REQUIRED_FIELD_GROUPS",
    "TECHNICAL_INDICATOR_FIELDS",
    "TECHNICAL_SIGNAL_FIELDS",
    "TECHNICAL_SIGNAL_FIELDS_BY_MARKET",
    "ZERO_DTE_MODEL_INPUT_FIELD_GROUPS",
    "build_market_readiness_report",
    "calculate_field_coverage",
    "classify_market_family",
    "field_groups_for_model_mode",
    "fields_for_model_mode",
    "get_required_field_groups_for_market",
    "technical_fields_for_market",
]
