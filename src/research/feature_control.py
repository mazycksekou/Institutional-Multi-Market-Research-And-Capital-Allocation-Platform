from __future__ import annotations

from collections.abc import Mapping, Sequence
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


def _coerce_rows(rows: Any) -> list[dict[str, Any]]:
    if rows is None:
        return []
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        return [dict(row) for row in rows if isinstance(row, Mapping)]
    return []


def run_feature_ablation_lab(*args: Any, **kwargs: Any) -> dict[str, Any]:
    rows = _coerce_rows(kwargs.get("rows") if "rows" in kwargs else (args[0] if args else None))
    sport = kwargs.get("sport") or kwargs.get("sport_key") or (args[1] if len(args) > 1 else None)
    removed_fields = list(kwargs.get("removed_fields") or [])
    selected_fields = list(kwargs.get("selected_fields") or [])
    selected_groups = list(kwargs.get("selected_groups") or [])
    user_row_threshold = int(kwargs.get("user_row_threshold") or 1)
    active_fields = _all_safe_fields_for_combination(sport, kwargs.get("market"))
    if selected_fields:
        active_fields = sorted({*active_fields, *(str(field) for field in selected_fields if str(field).strip())})
    if removed_fields:
        active_fields = [field for field in active_fields if field not in set(map(str, removed_fields))]
    row_count = len(rows)
    included_sports = [normalize_sport_key(sport)] if row_count else []
    excluded_sports = [] if row_count else [{"sport_key": normalize_sport_key(sport), "reason": "no_rows"}]
    threshold_met = row_count >= user_row_threshold
    return {
        "ok": True,
        "version": FEATURE_ABLATION_LAB_VERSION,
        "run_type": "true_code_baseline" if not removed_fields and not selected_fields else "ablation_test",
        "true_baseline_mode": not removed_fields and not selected_fields,
        "sport_key": normalize_sport_key(sport),
        "market_family": normalize_market_family(kwargs.get("market"), selection=kwargs.get("selection"), sport=sport),
        "selected_groups": selected_groups,
        "selected_fields": selected_fields,
        "removed_fields": removed_fields,
        "active_fields": active_fields,
        "included_sports": included_sports,
        "excluded_sports": excluded_sports,
        "included_sport_count": len(included_sports),
        "excluded_sport_count": len(excluded_sports),
        "rows_tested": row_count,
        "row_threshold_met": threshold_met,
        "user_row_threshold": user_row_threshold,
        "rows_needed_before_trust": user_row_threshold,
        "no_sports_reason": None if row_count else "no rows selected for review",
        "sport_population_note": "selected by user" if row_count else "no rows available",
        "row_threshold_note": "selected by user threshold" if threshold_met else "below your selected review threshold",
        "risk_preset_used": None,
        "regression_tactic_used": None,
        "custom_weights_used": False,
        "chance_override_used": False,
        "performance": {"total_rows": row_count},
        "warnings": [],
    }


def run_calibration_strategy_filter(*args: Any, **kwargs: Any) -> dict[str, Any]:
    rows = _coerce_rows(kwargs.get("rows") if "rows" in kwargs else (args[0] if args else None))
    market = kwargs.get("market") or kwargs.get("market_family")
    sport = kwargs.get("sport")
    active_fields = _all_safe_fields_for_combination(sport, market)
    return {
        "ok": True,
        "version": CALIBRATION_STRATEGY_FILTER_VERSION,
        "market_family": normalize_market_family(market, selection=kwargs.get("selection"), sport=sport),
        "sport_key": normalize_sport_key(sport),
        "active_fields": active_fields,
        "included_sports": [normalize_sport_key(sport)] if rows else [],
        "excluded_sports": [] if rows else [{"sport_key": normalize_sport_key(sport), "reason": "no_rows"}],
        "performance": {"total_rows": len(rows)},
        "warnings": [],
        "config": {
            "min_required_coverage_percent": float(kwargs.get("min_required_coverage_percent") or 0.0),
            "profile": kwargs.get("profile", "default"),
        },
    }


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
