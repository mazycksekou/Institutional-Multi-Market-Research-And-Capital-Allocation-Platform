from __future__ import annotations

import copy
from pathlib import Path
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


FEATURE_CONTROL_VERSION: str = "10H11"
DEFAULT_FEATURE_CONTROL_PROFILE: str = "available_baseline"


def get_feature_control_profiles() -> list[dict[str, str]]:
    return [
        {
            "value": "available_baseline",
            "label": "Available Baseline",
            "meaning": "Use the fields we currently have without pretending missing fields exist",
        },
        {
            "value": "odds_only",
            "label": "Odds Only",
            "meaning": "Test market/odds fields only",
        },
        {
            "value": "no_line_movement",
            "label": "Remove Line Movement",
            "meaning": "Ignore line movement fields when not available",
        },
        {
            "value": "settlement_check",
            "label": "Settlement Check",
            "meaning": "Focus on whether outcomes/results exist",
        },
        {
            "value": "custom",
            "label": "Custom Add/Remove",
            "meaning": "Operator chooses included/excluded fields",
        },
    ]


def get_never_feature_fields() -> list[str]:
    return list(ABLATION_NEVER_FEATURE_FIELDS)


def build_feature_control_config(
    profile: str = DEFAULT_FEATURE_CONTROL_PROFILE,
    include_groups: list[str] | None = None,
    exclude_groups: list[str] | None = None,
    include_fields: list[str] | None = None,
    exclude_fields: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "profile": profile,
        "include_groups": include_groups or [],
        "exclude_groups": exclude_groups or [],
        "include_fields": include_fields or [],
        "exclude_fields": exclude_fields or [],
        "never_feature_fields": get_never_feature_fields(),
        "version": FEATURE_CONTROL_VERSION,
    }


def get_feature_group_definitions() -> dict[str, dict[str, Any]]:
    from src.data.field_catalog import REQUIRED_FIELD_GROUPS

    return {
        "core_event": {
            "label": "Core Event Fields",
            "description": "Sport, league, date, home/away team",
            "fields": REQUIRED_FIELD_GROUPS["core_event"],
        },
        "line_core": {
            "label": "Line Core Fields",
            "description": "Market, selection, odds, implied probability, bookmaker, line value",
            "fields": REQUIRED_FIELD_GROUPS["line_core"],
        },
        "line_movement": {
            "label": "Line Movement Fields",
            "description": "Opening/closing odds, CLV, snapshot time",
            "fields": REQUIRED_FIELD_GROUPS["line_movement"],
        },
        "settlement": {
            "label": "Settlement Fields",
            "description": "Final result, winner, scores, profit/loss",
            "fields": REQUIRED_FIELD_GROUPS["settlement"],
        },
        "team_stats": {
            "label": "Team Stats Fields",
            "description": "Home/away team statistics, pace, ratings, injuries",
            "fields": REQUIRED_FIELD_GROUPS["team_stats"],
        },
        "player_stats": {
            "label": "Player Stats Fields",
            "description": "Player name, prop type, line, minutes, usage",
            "fields": REQUIRED_FIELD_GROUPS["player_stats"],
        },
        "projection_control": {
            "label": "Projection Control Fields",
            "description": "Model probability, features known at decision time",
            "fields": REQUIRED_FIELD_GROUPS["projection_control"],
        },
    }


def _safe_pre_decision_fields(row: dict, never: list[str]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in row.items():
        if key in never:
            continue
        if key == "features_known_at_decision_time":
            continue
        safe[key] = value
    return safe


def apply_feature_control_to_row(row: dict, config: dict) -> dict:
    never = list(config.get("never_feature_fields", get_never_feature_fields()))
    row_copy = copy.deepcopy(row)

    existing = row_copy.get("features_known_at_decision_time")
    if existing is not None and isinstance(existing, dict):
        snapshot = dict(existing)
    else:
        snapshot = _safe_pre_decision_fields(row_copy, never)

    for nf in never:
        snapshot.pop(nf, None)

    groups_def = get_feature_group_definitions()

    include_groups = set(config.get("include_groups") or [])
    exclude_groups = set(config.get("exclude_groups") or [])

    if include_groups:
        allowed_fields: set[str] = set()
        for grp in include_groups:
            if grp in groups_def:
                allowed_fields.update(groups_def[grp]["fields"])
        snapshot = {k: v for k, v in snapshot.items() if k in allowed_fields}
    elif exclude_groups:
        blocked: set[str] = set()
        for grp in exclude_groups:
            if grp in groups_def:
                blocked.update(groups_def[grp]["fields"])
        snapshot = {k: v for k, v in snapshot.items() if k not in blocked}

    include_fields = set(config.get("include_fields") or [])
    exclude_fields = set(config.get("exclude_fields") or [])

    if include_fields:
        snapshot = {k: v for k, v in snapshot.items() if k in include_fields}
    else:
        for ex in exclude_fields:
            snapshot.pop(ex, None)

    row_copy["features_known_at_decision_time"] = snapshot
    return row_copy


def summarize_feature_control_impact(
    rows: list[dict],
    config: dict,
) -> dict[str, Any]:
    never = list(config.get("never_feature_fields", get_never_feature_fields()))
    groups_def = get_feature_group_definitions()

    available: set[str] = set()
    missing: set[str] = set()
    removed: set[str] = set()

    for row in rows:
        row_keys = set(row.keys())
        snapshot_keys = set(row.get("features_known_at_decision_time", {}).keys())
        available.update(snapshot_keys)
        missing.update(key for key in row_keys if key not in snapshot_keys and key not in never)

    removed.update(field for field in never if any(field in row for row in rows))

    include_groups = config.get("include_groups") or []
    exclude_groups = config.get("exclude_groups") or []
    include_fields = config.get("include_fields") or []
    exclude_fields = config.get("exclude_fields") or []

    warnings: list[str] = []
    if exclude_groups or exclude_fields:
        warnings.append("Some field groups or fields have been explicitly excluded.")
    if any(grp in exclude_groups for grp in ("line_movement",)):
        warnings.append("Line movement fields are missing or removed - CLV-style analysis will be limited.")
    if any(grp in exclude_groups for grp in ("player_stats",)):
        warnings.append("Player prop fields are missing - player prop projections are not ready.")

    profile_label = next(
        (p["label"] for p in get_feature_control_profiles() if p["value"] == config.get("profile")),
        config.get("profile", DEFAULT_FEATURE_CONTROL_PROFILE),
    )
    interpretation = f"Profile: {profile_label}. "
    if not include_groups and not exclude_groups and not include_fields and not exclude_fields:
        interpretation += "This profile can test a basic available-data baseline."
    else:
        interpretation += "Operator selected custom field controls."
    interpretation += " Settlement fields are top-level only and are not used as model features."

    return {
        "profile": config.get("profile", DEFAULT_FEATURE_CONTROL_PROFILE),
        "rows_seen": len(rows),
        "included_groups": include_groups,
        "excluded_groups": exclude_groups,
        "included_fields": include_fields,
        "excluded_fields": exclude_fields,
        "never_feature_fields": never,
        "available_feature_count": len(available),
        "missing_feature_count": len(missing),
        "removed_feature_count": len(removed),
        "warnings": warnings,
        "operator_interpretation": interpretation,
    }


def get_feature_ablation_lab_snapshot_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    market: str | None = None,
    mode: str = "single_sport",
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    limit: int = 2000,
) -> dict[str, Any]:
    from src.data.historical_odds import (
        connect_historical_odds_db,
        initialize_historical_odds_db,
        query_historical_odds_rows,
    )

    result: dict[str, Any] = {
        "ok": False,
        "version": "10H15",
        "mode": mode,
        "sport_key": "",
        "market_family": "",
        "field_groups": [],
        "all_selectable_fields": [],
        "active_fields": [],
        "removed_fields": [],
        "included_sports": [],
        "excluded_sports": [],
        "sport_readiness": {},
        "performance": {},
        "roi_by_sport": {},
        "warnings": [],
        "operator_interpretation": "",
    }
    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
        raw_rows = query_historical_odds_rows(conn, sport=sport, market=market, limit=limit)
        conn.close()
    except Exception as exc:
        result["warnings"].append(f"Cannot open database: {exc}")
        return result

    if not raw_rows:
        result["warnings"].append("No rows in database.")
        raw_rows = []

    ablation = run_feature_ablation_lab(
        rows=raw_rows,
        sport=sport,
        market=market,
        mode=mode,
        selected_fields=selected_fields,
        removed_fields=removed_fields,
        selected_groups=selected_groups,
    )

    result["ok"] = ablation.get("ok", False)
    result["version"] = ablation.get("version", "10H15")
    result["mode"] = ablation.get("mode", mode)
    result["sport_key"] = ablation.get("sport_key", "")
    result["market_family"] = ablation.get("market_family", "")
    result["field_groups"] = ablation.get("field_groups", [])
    result["all_selectable_fields"] = ablation.get("all_selectable_fields", [])
    result["active_fields"] = ablation.get("active_fields", [])
    result["removed_fields"] = ablation.get("removed_fields", [])
    result["included_sports"] = ablation.get("included_sports", [])
    result["excluded_sports"] = ablation.get("excluded_sports", [])
    result["sport_readiness"] = ablation.get("sport_readiness", {})
    result["performance"] = ablation.get("performance", {})
    result["roi_by_sport"] = ablation.get("roi_by_sport", {})
    result["warnings"] = ablation.get("warnings", []) + result["warnings"]
    result["operator_interpretation"] = ablation.get("operator_interpretation", "")
    return result


def get_calibration_strategy_filter_snapshot_for_dashboard(
    db_path: str | Path,
    filters: dict[str, Any] | None = None,
    mode: str = "single_sport",
    sport: str | None = None,
    market: str | None = None,
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    min_required_coverage_percent: float = 80.0,
    min_active_field_coverage_percent: float = 60.0,
    min_rows_per_sport: int = 25,
    min_rows_per_market: int = 10,
) -> dict[str, Any]:
    from src.data.historical_odds import (
        connect_historical_odds_db,
        initialize_historical_odds_db,
        query_historical_odds_rows,
    )

    result: dict[str, Any] = {
        "ok": False,
        "version": "10H16",
        "mode": mode,
        "sport_key": normalize_sport_key(sport) if sport else "general",
        "market_family": normalize_market_family(market, sport=sport) if market else "general_market",
        "included_sports": [],
        "excluded_sports": [],
        "included_market_families": [],
        "excluded_market_families": [],
        "readiness_snapshot": {},
        "performance": {},
        "exclusion_reason_counts": {},
        "warnings": [],
        "operator_interpretation": "",
    }
    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
        raw_rows = query_historical_odds_rows(
            conn,
            sport=sport,
            league=(filters or {}).get("league"),
            market=market,
            source_key=(filters or {}).get("source_key"),
            start_date=(filters or {}).get("start_date"),
            end_date=(filters or {}).get("end_date"),
            limit=(filters or {}).get("limit", 5000),
        )
        conn.close()
    except Exception as exc:
        result["warnings"].append(f"Cannot open database: {exc}")
        return result

    if not raw_rows:
        result["ok"] = True
        result["warnings"].append("No rows in database.")
        result["operator_interpretation"] = "No rows available for calibration filter."
        return result

    try:
        filtered = run_calibration_strategy_filter(
            rows=raw_rows,
            mode=mode,
            sport=sport,
            market=market,
            selected_fields=selected_fields,
            removed_fields=removed_fields,
            selected_groups=selected_groups,
            min_required_coverage_percent=min_required_coverage_percent,
            min_active_field_coverage_percent=min_active_field_coverage_percent,
            min_rows_per_sport=min_rows_per_sport,
            min_rows_per_market=min_rows_per_market,
        )
    except Exception as exc:
        result["warnings"].append(f"Calibration filter error: {exc}")
        result["ok"] = False
        return result

    result["ok"] = True
    result["version"] = filtered.get("version", "10H16")
    result["sport_key"] = filtered.get("sport_key", "general")
    result["market_family"] = filtered.get("market_family", "general_market")
    result["included_sports"] = filtered.get("included_sports", [])
    result["excluded_sports"] = filtered.get("excluded_sports", [])
    result["included_market_families"] = filtered.get("included_market_families", [])
    result["excluded_market_families"] = filtered.get("excluded_market_families", [])
    result["readiness_snapshot"] = filtered.get("readiness_snapshot", {})
    result["performance"] = filtered.get("performance", {})
    result["exclusion_reason_counts"] = filtered.get("exclusion_reason_counts", {})
    result["warnings"] = filtered.get("warnings", [])
    result["operator_interpretation"] = filtered.get("operator_interpretation", "")
    return result


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
    "apply_feature_control_to_row",
    "evaluate_market_feature_readiness",
    "evaluate_sport_feature_readiness",
    "build_feature_control_config",
    "get_calibration_strategy_filter_snapshot_for_dashboard",
    "get_feature_ablation_lab_snapshot_for_dashboard",
    "get_feature_control_profiles",
    "get_feature_group_definitions",
    "get_never_feature_fields",
    "get_market_feature_pack",
    "get_sport_feature_pack",
    "normalize_market_family",
    "normalize_sport_key",
    "run_calibration_strategy_filter",
    "run_feature_ablation_lab",
    "summarize_feature_control_impact",
]
