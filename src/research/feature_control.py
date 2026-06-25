from __future__ import annotations

from collections.abc import Mapping, Sequence
from importlib import import_module
from typing import Any

from src.market_intelligence.feature_packs import (
    evaluate_market_feature_readiness,
    evaluate_sport_feature_readiness,
    get_market_feature_pack,
    get_sport_feature_pack,
    normalize_market_family,
    normalize_sport_key,
)


FEATURE_ABLATION_LAB_VERSION = "10H15"
CALIBRATION_STRATEGY_FILTER_VERSION = "10H16"

ABLATION_NEVER_FEATURE_FIELDS: list[str] = [
    "final_result",
    "winner",
    "home_score",
    "away_score",
    "profit_loss",
    "closing_odds",
    "closing_line",
    "clv",
    "result",
    "settled_result",
    "bet_result",
    "outcome",
]

BASE_FIELD_GROUPS: list[dict[str, Any]] = [
    {
        "group_name": "market_context",
        "fields": [
            "sport",
            "league",
            "market",
            "selection",
            "event_date",
            "home_team",
            "away_team",
            "team_name",
            "player_name",
        ],
    },
    {
        "group_name": "price_context",
        "fields": [
            "odds_at_decision_time",
            "opening_odds",
            "current_line",
            "opening_line",
            "market_implied_probability",
            "implied_probability",
            "line_value",
        ],
    },
    {
        "group_name": "signal_context",
        "fields": [
            "confidence",
            "expected_move",
            "support",
            "resistance",
            "risk",
            "stop",
            "invalidation",
            "liquidity_score",
        ],
    },
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _all_safe_fields_for_combination(
    sport: Any,
    market: Any,
) -> list[str]:
    base_fields: set[str] = set()
    for group in BASE_FIELD_GROUPS:
        base_fields.update(group.get("fields", []))
    base_fields.update(get_sport_feature_pack(sport).get("recommended_fields", []))
    base_fields.update(get_market_feature_pack(market, sport=sport).get("recommended_fields", []))
    base_fields.difference_update(ABLATION_NEVER_FEATURE_FIELDS)
    return sorted(field for field in base_fields if field)


def apply_field_ablation(
    rows: Sequence[Mapping[str, Any]],
    *,
    selected_fields: Sequence[str] | None = None,
    removed_fields: Sequence[str] | None = None,
    selected_groups: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    selected = {str(field).strip() for field in (selected_fields or ()) if str(field).strip()}
    removed = {str(field).strip() for field in (removed_fields or ()) if str(field).strip()}
    chosen_groups = {str(group).strip() for group in (selected_groups or ()) if str(group).strip()}
    group_fields: set[str] = set()
    for group in BASE_FIELD_GROUPS:
        if not chosen_groups or group.get("group_name") in chosen_groups:
            group_fields.update(group.get("fields", []))
    if not selected:
        selected = set(group_fields)
    selected.update(group_fields)
    selected.difference_update(removed)
    selected.difference_update(ABLATION_NEVER_FEATURE_FIELDS)
    ablated: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        ablated.append({key: value for key, value in row.items() if key in selected})
    return ablated


def run_feature_ablation_lab(*args: Any, **kwargs: Any) -> Any:
    legacy = import_module("automation_scheduler.feature_ablation_lab")
    return legacy.run_feature_ablation_lab(*args, **kwargs)


def run_calibration_strategy_filter(*args: Any, **kwargs: Any) -> Any:
    legacy = import_module("automation_scheduler.calibration_strategy_filter")
    return legacy.run_calibration_strategy_filter(*args, **kwargs)


__all__ = [
    "ABLATION_NEVER_FEATURE_FIELDS",
    "BASE_FIELD_GROUPS",
    "CALIBRATION_STRATEGY_FILTER_VERSION",
    "FEATURE_ABLATION_LAB_VERSION",
    "_all_safe_fields_for_combination",
    "_safe_float",
    "_safe_int",
    "_safe_str",
    "apply_field_ablation",
    "evaluate_market_feature_readiness",
    "evaluate_sport_feature_readiness",
    "get_market_feature_pack",
    "get_sport_feature_pack",
    "normalize_market_family",
    "normalize_sport_key",
    "run_calibration_strategy_filter",
    "run_feature_ablation_lab",
]
