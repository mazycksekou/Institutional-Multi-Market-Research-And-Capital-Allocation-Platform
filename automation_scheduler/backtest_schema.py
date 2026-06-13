"""Canonical backtest schema, alias normalization, and leakage guards.

This module is the single registry for historical backtest rows.

It does not run backtests. The canonical backtest engine remains:
automation_scheduler.backtesting_engine
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REQUIRED_BACKTEST_FIELDS: tuple[str, ...] = (
    "event_id",
    "contract_id",
    "sport",
    "league",
    "market",
    "decision_time",
    "odds_at_decision_time",
    "features_known_at_decision_time",
    "model_probability",
    "market_implied_probability",
    "edge",
    "stake",
    "final_result",
    "profit_loss",
    "closing_line",
    "clv",
)


BACKTEST_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "event_id": ("event_id", "event", "game_id", "match_id", "fixture_id"),
    "contract_id": ("contract_id", "kalshi_contract_id", "ticker", "market_id"),
    "sport": ("sport", "sport_key", "league_sport"),
    "league": ("league", "competition", "season_league"),
    "market": ("market", "market_type", "bet_type", "prop_type"),
    "decision_time": ("decision_time", "created_at", "timestamp", "bet_time", "placed_at", "paper_created_at"),
    "odds_at_decision_time": ("odds_at_decision_time", "odds", "american_odds", "recommended_odds", "price", "line_price", "entry_odds"),
    "features_known_at_decision_time": ("features_known_at_decision_time", "features", "feature_snapshot", "model_features", "pre_event_features"),
    "model_probability": ("model_probability", "model_prob", "predicted_probability", "probability", "win_probability"),
    "market_implied_probability": ("market_implied_probability", "implied_probability", "market_probability", "book_probability"),
    "edge": ("edge", "edge_percent", "ev_percent", "estimated_edge", "model_edge"),
    "stake": ("stake", "paper_stake", "recommended_stake", "unit_size", "bet_size"),
    "final_result": ("final_result", "result", "result_status", "outcome", "final_outcome", "settlement_result", "paper_result"),
    "profit_loss": ("profit_loss", "pnl", "profit", "loss", "paper_profit_loss", "closed_pnl", "realized_pnl"),
    "closing_line": ("closing_line", "closing_odds", "closing_price", "close_price", "closing_line_value"),
    "clv": ("clv", "clv_percent", "closing_line_value", "closing_line_value_pct"),
}


# These fields are allowed for settlement/evaluation, but not inside model feature snapshots.
LEAKAGE_FIELD_ALIASES: tuple[str, ...] = (
    "actual_result",
    "final_result",
    "result",
    "result_status",
    "outcome",
    "final_outcome",
    "settlement_result",
    "settled_yes",
    "settled_no",
    "paper_result",
    "profit_loss",
    "pnl",
    "profit",
    "loss",
    "paper_profit_loss",
    "closed_pnl",
    "realized_pnl",
    "closing_line",
    "closing_odds",
    "closing_price",
    "close_price",
    "closing_line_value",
    "closing_line_value_pct",
    "clv",
    "clv_percent",
)


def _first_present(row: Mapping[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in row and row.get(alias) not in (None, ""):
            return row.get(alias)
    return None


def normalize_backtest_row(row: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a canonical backtest row while preserving original fields.

    Canonical fields are added from aliases, but original keys are retained so
    existing call sites continue to work during migration.
    """

    source: dict[str, Any] = dict(row or {})
    normalized: dict[str, Any] = dict(source)

    for canonical, aliases in BACKTEST_FIELD_ALIASES.items():
        if normalized.get(canonical) in (None, ""):
            value = _first_present(source, aliases)
            if value not in (None, ""):
                normalized[canonical] = value

    # Existing engine names.
    if normalized.get("recommended_odds") in (None, "") and normalized.get("odds_at_decision_time") not in (None, ""):
        normalized["recommended_odds"] = normalized["odds_at_decision_time"]

    if normalized.get("paper_stake") in (None, "") and normalized.get("stake") not in (None, ""):
        normalized["paper_stake"] = normalized["stake"]

    if normalized.get("result_status") in (None, "") and normalized.get("final_result") not in (None, ""):
        normalized["result_status"] = normalized["final_result"]

    if normalized.get("closing_odds") in (None, "") and normalized.get("closing_line") not in (None, ""):
        normalized["closing_odds"] = normalized["closing_line"]

    if normalized.get("market_type") in (None, "") and normalized.get("market") not in (None, ""):
        normalized["market_type"] = normalized["market"]

    return normalized


def normalize_backtest_rows(rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None) -> list[dict[str, Any]]:
    return [normalize_backtest_row(row) for row in (rows or [])]


def get_backtest_feature_snapshot(row: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = normalize_backtest_row(row)
    features = normalized.get("features_known_at_decision_time")

    if isinstance(features, Mapping):
        return dict(features)

    return {}


def find_leakage_fields_in_features(features: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(features, Mapping):
        return []

    blocked = {field.lower() for field in LEAKAGE_FIELD_ALIASES}
    found: list[str] = []

    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, Mapping):
            for key, inner in value.items():
                key_text = str(key)
                full_key = f"{prefix}.{key_text}" if prefix else key_text
                if key_text.lower() in blocked:
                    found.append(full_key)
                walk(full_key, inner)
        elif isinstance(value, list):
            for idx, inner in enumerate(value):
                walk(f"{prefix}[{idx}]", inner)

    walk("", dict(features))
    return sorted(set(found))


def validate_no_leakage_features(row: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate that model features only contain pre-decision information."""

    features = get_backtest_feature_snapshot(row)
    leakage_fields = find_leakage_fields_in_features(features)

    return {
        "ok": not leakage_fields,
        "leakage_fields": leakage_fields,
        "blocked_reason": "feature_snapshot_contains_future_or_settlement_fields" if leakage_fields else None,
    }


def missing_required_backtest_fields(row: Mapping[str, Any] | None) -> list[str]:
    normalized = normalize_backtest_row(row)
    return [
        field
        for field in REQUIRED_BACKTEST_FIELDS
        if normalized.get(field) in (None, "")
    ]


def describe_backtest_schema() -> dict[str, Any]:
    return {
        "required_fields": list(REQUIRED_BACKTEST_FIELDS),
        "aliases": {key: list(value) for key, value in BACKTEST_FIELD_ALIASES.items()},
        "leakage_field_aliases": list(LEAKAGE_FIELD_ALIASES),
    }
