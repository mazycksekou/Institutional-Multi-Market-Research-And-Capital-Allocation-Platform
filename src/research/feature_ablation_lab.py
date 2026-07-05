"""Feature Ablation Lab – Phase 10H15.

Start with all safe available fields, then let the operator remove fields
to test what actually improves model performance.

Architecture:
- Backend owns all ablation logic and calculations.
- Streamlit is display and controls only.
- No preset experiment profiles.
- No SQLite schema changes.
- No bankroll math.
- No backtesting_engine changes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from src.market_intelligence.feature_packs import (
    evaluate_market_feature_readiness,
    evaluate_sport_feature_readiness,
    get_market_feature_pack,
    get_sport_feature_pack,
    normalize_market_family,
    normalize_sport_key,
    summarize_market_feature_readiness,
    summarize_sport_feature_readiness,
)

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

FEATURE_ABLATION_LAB_VERSION: str = "10H15"

# ---------------------------------------------------------------------------
# Never‑feature fields (leakage / grading only)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Canonical field groups
# ---------------------------------------------------------------------------

_ODDS_FIELDS: list[str] = [
    "odds_at_decision_time",
    "market_implied_probability",
    "bookmaker",
    "opening_odds",
    "implied_probability",
]

_MARKET_FIELDS: list[str] = [
    "market",
    "market_family",
    "selection",
    "line_value",
    "team_name",
    "player_name",
]

_LINE_MOVEMENT_FIELDS: list[str] = [
    "opening_line",
    "current_line",
    "decision_line",
    "line_move_up",
    "line_move_down",
    "line_total_range",
    "odds_move_up",
    "odds_move_down",
    "odds_total_range",
]

_VOLATILITY_FIELDS: list[str] = [
    "volatility_level",
    "line_volatility_score",
    "odds_volatility_score",
]

_TEAM_CONTEXT_FIELDS: list[str] = [
    "home_team",
    "away_team",
    "opponent_team",
    "home_or_away",
]

_PLAYER_CONTEXT_FIELDS: list[str] = [
    "player_name",
    "minutes_projection",
    "usage_rate",
    "player_recent_form",
    "projected_lineup",
]

_INJURY_AVAILABILITY_FIELDS: list[str] = [
    "injury_status",
    "availability_status",
    "lineup_status",
    "starting_goalie",
    "starting_pitcher",
    "qb_status",
]

_REST_SCHEDULE_FIELDS: list[str] = [
    "rest_days",
    "travel",
    "schedule_spot",
    "back_to_back",
    "days_since_last_game",
]

_WEATHER_ENVIRONMENT_FIELDS: list[str] = [
    "weather",
    "wind",
    "temperature",
    "park_factor",
    "course_or_track",
    "surface",
    "venue_context",
]

_MATCHUP_FIELDS: list[str] = [
    "matchup_context",
    "head_to_head",
    "opponent_strength",
    "defensive_rating",
    "offensive_rating",
]

_FORM_FIELDS: list[str] = [
    "team_recent_form",
    "player_recent_form",
    "recent_form",
    "xg_for",
    "xg_against",
]

_SPORT_SPECIFIC_FIELDS: list[str] = [
    "starting_pitcher",
    "bullpen_strength",
    "pace",
    "strokes_gained_approach",
    "serve_rating",
    "return_rating",
    "map_pool",
    "patch_version",
    "fighter_recent_form",
]

BASE_FIELD_GROUPS: list[dict[str, Any]] = [
    {
        "group_key": "odds_fields",
        "display_name": "Odds Fields",
        "description": "Market odds, implied probability, bookmaker information",
        "fields": _ODDS_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Includes odds, implied probability, and bookmaker. Always available."
        ),
    },
    {
        "group_key": "market_fields",
        "display_name": "Market Fields",
        "description": "Market type, selection, line value, team/player",
        "fields": _MARKET_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Describes the market structure and selection details."
        ),
    },
    {
        "group_key": "line_movement_fields",
        "display_name": "Line Movement / Odds Movement Fields",
        "description": "Opening line, current line, closing line, CLV (grading only)",
        "fields": _LINE_MOVEMENT_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Track how lines and odds moved. Available when opening/closing snapshots exist."
        ),
    },
    {
        "group_key": "volatility_fields",
        "display_name": "Volatility Fields",
        "description": "Volatility level and scores",
        "fields": _VOLATILITY_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Measures how much the line or odds moved within the snapshots."
        ),
    },
    {
        "group_key": "team_context_fields",
        "display_name": "Team Context Fields",
        "description": "Home/away team names and orientation",
        "fields": _TEAM_CONTEXT_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Provides team identification and home/away context."
        ),
    },
    {
        "group_key": "player_context_fields",
        "display_name": "Player Context Fields",
        "description": "Player name, minutes projection, usage, recent form",
        "fields": _PLAYER_CONTEXT_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Player‑level data when players are identified."
        ),
    },
    {
        "group_key": "injury_availability_fields",
        "display_name": "Injury & Availability Fields",
        "description": "Injury status, starting lineup info",
        "fields": _INJURY_AVAILABILITY_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Indicates whether key players are available."
        ),
    },
    {
        "group_key": "rest_schedule_fields",
        "display_name": "Rest & Schedule Fields",
        "description": "Days of rest, back‑to‑back games, travel",
        "fields": _REST_SCHEDULE_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Captures how much rest each side has had."
        ),
    },
    {
        "group_key": "weather_environment_fields",
        "display_name": "Weather & Environment Fields",
        "description": "Weather conditions, venue, park factor",
        "fields": _WEATHER_ENVIRONMENT_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Outdoor conditions and venue that affect game outcomes."
        ),
    },
    {
        "group_key": "matchup_fields",
        "display_name": "Matchup Fields",
        "description": "Matchup context, head‑to‑head history, strength ratings",
        "fields": _MATCHUP_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Provides historical and matchup analysis."
        ),
    },
    {
        "group_key": "form_fields",
        "display_name": "Form Fields",
        "description": "Recent team/player form, expected goals (soccer)",
        "fields": _FORM_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "How well the team or player has performed recently."
        ),
    },
    {
        "group_key": "sport_specific_fields",
        "display_name": "Sport‑Specific Fields",
        "description": "Custom fields that vary by sport",
        "fields": _SPORT_SPECIFIC_FIELDS,
        "safe_for_pre_decision": True,
        "operator_interpretation": (
            "Sport‑dependent fields like pitcher name, map pool, etc."
        ),
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        f = float(value)
        if not (f != f):  # NaN check
            return f
        return default
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _rows_for_sport(rows: Sequence[Mapping[str, Any]], sport_key: str) -> list[dict]:
    sport_key_norm = normalize_sport_key(sport_key)
    out: list[dict] = []
    for r in rows:
        if normalize_sport_key(r.get("sport")) == sport_key_norm:
            out.append(dict(r))
    return out


def _rows_for_market(
    rows: Sequence[Mapping[str, Any]],
    market_key: str,
) -> list[dict]:
    mkt = normalize_market_family(market_key)
    out: list[dict] = []
    for r in rows:
        if normalize_market_family(r.get("market"), r.get("selection"), r.get("sport")) == mkt:
            out.append(dict(r))
    return out


def _all_safe_fields_for_combination(
    sport: Any,
    market: Any,
) -> list[str]:
    """Return the union of fields from base groups, plus sport‑specific recommended
    and market‑specific recommended, minus never fields."""
    # Collect base group fields
    base_fields: set[str] = set()
    for grp in BASE_FIELD_GROUPS:
        base_fields.update(grp["fields"])
    # Add sport‑specific recommended fields from sport feature packs
    sport_pack = get_sport_feature_pack(sport)
    base_fields.update(sport_pack.get("recommended_fields", []))
    # Add market‑specific recommended fields
    market_pack = get_market_feature_pack(market, sport=sport)
    base_fields.update(market_pack.get("recommended_fields", []))
    # Remove never fields
    never_set = set(ABLATION_NEVER_FEATURE_FIELDS)
    final = [f for f in base_fields if f not in never_set]
    return sorted(set(final))


# ---------------------------------------------------------------------------
# Part 3: get_ablation_field_groups_for_sport
# ---------------------------------------------------------------------------


def get_ablation_field_groups_for_sport(
    sport: object = None,
    market: object = None,
) -> dict[str, Any]:
    """Return all selectable field groups and fields for the given sport/market."""
    sport_key = normalize_sport_key(sport)
    market_family = normalize_market_family(market, sport=sport_key)

    all_fields = _all_safe_fields_for_combination(sport_key, market_family)
    never_set = set(ABLATION_NEVER_FEATURE_FIELDS)
    excluded = [f for f in ABLATION_NEVER_FEATURE_FIELDS if f in all_fields]
    all_selectable = [f for f in all_fields if f not in never_set]

    # Rebuild groups that contain only selectable fields
    groups_out: list[dict[str, Any]] = []
    for grp in BASE_FIELD_GROUPS:
        safe_fields = [f for f in grp["fields"] if f in all_selectable]
        if not safe_fields:
            continue
        grp_copy = dict(grp)
        grp_copy["fields"] = safe_fields
        groups_out.append(grp_copy)

    # Add market‑specific fields not already covered? We'll rely on base.

    warnings: list[str] = []
    if excluded:
        warnings.append(f"Excluded never‑feature fields: {', '.join(excluded)}")

    return {
        "ok": True,
        "version": FEATURE_ABLATION_LAB_VERSION,
        "sport_key": sport_key,
        "market_family": market_family,
        "groups": groups_out,
        "all_selectable_fields": all_selectable,
        "excluded_never_fields": excluded,
        "warnings": warnings,
        "operator_interpretation": (
            f"All safe pre‑decision fields for {sport_key} ({market_family}). "
            "Remove fields to test which matter."
        ),
    }


# ---------------------------------------------------------------------------
# Part 4: Readiness gating
# ---------------------------------------------------------------------------


def is_sport_calibration_ready(
    rows: Sequence[Mapping[str, Any]],
    sport: str,
    required_coverage_threshold: float = 80.0,
) -> dict[str, Any]:
    """Check whether a given sport has enough required fields to be useful for
    calibration (i.e. usable or strong readiness level)."""
    sport_rows = _rows_for_sport(rows, sport)
    if not sport_rows:
        return {
            "sport_key": normalize_sport_key(sport),
            "ready": False,
            "readiness_level": "no_data",
            "total_rows": 0,
            "required_coverage_percent": 0.0,
            "missing_required_fields": [],
            "reason": "No rows for this sport.",
        }
    eval_result = evaluate_sport_feature_readiness(sport_rows, sport)
    ready = eval_result.get("readiness_level") in ("usable", "strong")
    return {
        "sport_key": eval_result["sport_key"],
        "ready": ready,
        "readiness_level": eval_result["readiness_level"],
        "total_rows": eval_result["total_rows"],
        "required_coverage_percent": eval_result["required_coverage_percent"],
        "missing_required_fields": eval_result["missing_required_fields"],
        "reason": (
            "Calibration ready"
            if ready
            else f"Readiness level is {eval_result['readiness_level']} "
                 f"(required_coverage {eval_result['required_coverage_percent']}%)."
        ),
    }


def filter_calibration_ready_sports(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Group rows by normalised sport and return only those that are calibration‑ready."""
    # Get distinct normalized sport keys
    sport_keys: set[str] = set()
    for r in rows:
        sport_keys.add(normalize_sport_key(r.get("sport")))
    sport_keys.discard("general")

    included_rows: list[dict] = []
    excluded_rows: list[dict] = []
    included_sports: list[str] = []
    excluded_sports: list[dict[str, Any]] = []
    sport_readiness: dict[str, Any] = {}

    for sk in sport_keys:
        ready_info = is_sport_calibration_ready(rows, sk)
        sport_readiness[sk] = ready_info
        if ready_info.get("ready"):
            included_sports.append(sk)
            included_rows.extend(_rows_for_sport(rows, sk))
        else:
            excluded_sports.append(
                {
                    "sport_key": sk,
                    "readiness_level": ready_info.get("readiness_level", ""),
                    "missing_required_fields": ready_info.get("missing_required_fields", []),
                    "reason": ready_info.get("reason", "Not calibration ready"),
                }
            )
            excluded_rows.extend(_rows_for_sport(rows, sk))

    return {
        "included_rows": included_rows,
        "excluded_rows": excluded_rows,
        "included_sports": included_sports,
        "excluded_sports": excluded_sports,
        "sport_readiness": sport_readiness,
        "warnings": (
            [f"Excluded {len(excluded_sports)} sport(s): {', '.join(e['sport_key'] for e in excluded_sports)}"]
            if excluded_sports
            else []
        ),
    }


# ---------------------------------------------------------------------------
# Part 5: Ablation calculations
# ---------------------------------------------------------------------------


_REQUIRED_BASE_FIELDS: list[str] = [
    "sport",
    "event_date",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
]


def _row_has_requisite_fields(row: Mapping[str, Any], required: list[str]) -> bool:
    for f in required:
        v = row.get(f)
        if v is None or v == "":
            return False
    return True


def _row_has_sufficient_active_fields(
    row: Mapping[str, Any],
    active_fields: set[str],
    threshold_pct: float = 60.0,
) -> bool:
    if not active_fields:
        # No extra active fields required beyond base
        return True
    present = sum(1 for f in active_fields if row.get(f) is not None)
    needed = max(1, round(len(active_fields) * threshold_pct / 100))
    return present >= needed


def apply_field_ablation(
    rows: Sequence[Mapping[str, Any]],
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    sport: object = None,
    market: object = None,
    mode: str = "single_sport",
    user_row_threshold: int = 1,
) -> dict[str, Any]:
    """Determine which fields are active after ablation and which rows are eligible."""
    never_set = set(ABLATION_NEVER_FEATURE_FIELDS)
    # start with all safe fields
    all_selectable = _all_safe_fields_for_combination(sport, market)

    # apply group selection
    if selected_groups:
        selected_groups_set = set(selected_groups)
        group_fields: set[str] = set()
        for grp in BASE_FIELD_GROUPS:
            if grp["group_key"] in selected_groups_set:
                group_fields.update(grp["fields"])
        # intersect with all_selectable
        all_selectable = [f for f in all_selectable if f in group_fields]

    # apply selected_fields (overrides group selection)
    if selected_fields:
        allowed = set(selected_fields)
        all_selectable = [f for f in all_selectable if f in allowed]

    # apply removed_fields (subtract)
    removed = set(removed_fields or [])
    never_set_used = set(ABLATION_NEVER_FEATURE_FIELDS)
    # ensure removed never contains leakage fields? They shouldn't be selectable anyway.
    active_fields = set(all_selectable) - removed - never_set_used
    # Remove any remaining never fields
    active_fields -= never_set_used

    eligible_rows: list[dict] = []
    skipped_rows: list[dict] = []
    core_rows: list[dict] = []

    required = list(_REQUIRED_BASE_FIELDS)
    for raw in rows:
        r = dict(raw)
        if not _row_has_requisite_fields(r, required):
            skipped_rows.append(r)
            continue
        core_rows.append(r)
        # Base fields are always required; active_extra = active_fields - required
        active_extra = active_fields - set(required)
        if _row_has_sufficient_active_fields(r, active_extra, threshold_pct=60.0):
            eligible_rows.append(r)
        else:
            skipped_rows.append(r)

    total = len(rows) or 1
    eligibility_rate = round(len(eligible_rows) / total * 100, 1)

    rows_tested = len(core_rows)
    rows_needed_before_trust = user_row_threshold
    row_threshold_met = rows_tested >= rows_needed_before_trust
    if row_threshold_met:
        row_threshold_note = (
            f"Rows tested: {rows_tested} / {rows_needed_before_trust} selected by user."
        )
    else:
        row_threshold_note = (
            f"Rows tested: {rows_tested} / {rows_needed_before_trust} selected by user. "
            f"The run is allowed, but the row count is below your selected review threshold."
        )

    warnings: list[str] = []
    if removed - set(all_selectable):
        warnings.append("Some removed fields were not selectable.")
    # check for never fields in active (shouldn't)
    err = active_fields & never_set_used
    if err:
        warnings.append(f"Leakage fields accidentally included: {err}")
        active_fields -= err

    return {
        "ok": True,
        "version": FEATURE_ABLATION_LAB_VERSION,
        "mode": mode,
        "sport_key": normalize_sport_key(sport),
        "market_family": normalize_market_family(market, sport=sport),
        "selected_fields": selected_fields or [],
        "removed_fields": list(removed),
        "active_fields": sorted(active_fields),
        "excluded_never_fields": list(ABLATION_NEVER_FEATURE_FIELDS),
        "eligible_rows": eligible_rows,
        "skipped_rows": skipped_rows,
        "core_rows": core_rows,
        "eligibility_rate_percent": eligibility_rate,
        "warnings": warnings,
        "rows_tested": rows_tested,
        "rows_needed_before_trust": rows_needed_before_trust,
        "row_threshold_met": row_threshold_met,
        "row_threshold_note": row_threshold_note,
        "user_row_threshold": user_row_threshold,
        "operator_interpretation": (
            f"{len(eligible_rows)} of {len(rows)} rows ({eligibility_rate}%) have "
            f"sufficient active pre‑decision fields."
        ),
    }


def summarize_ablation_performance(
    rows: Sequence[Mapping[str, Any]],
    active_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Compute performance metrics for eligible rows."""
    total_rows = len(rows)
    if total_rows == 0:
        return {
            "total_rows": 0,
            "eligible_rows": 0,
            "skipped_rows": 0,
            "decisions": 0,
            "skipped_decisions": 0,
            "settled_count": 0,
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "net_result": 0.0,
            "roi_percent": 0.0,
            "win_rate_percent": 0.0,
            "sports": [],
            "market_families": [],
            "warnings": ["No rows to summarize."],
            "operator_interpretation": "No data available.",
        }
    decisions = 0
    skipped_decisions = 0
    settled = 0
    wins = 0
    losses = 0
    pushes = 0
    net = 0.0
    rois: list[float] = []
    sports_set: set[str] = set()
    mkts_set: set[str] = set()
    for r in rows:
        sports_set.add(_safe_str(r.get("sport")))
        mkt = normalize_market_family(r.get("market"), r.get("selection"), r.get("sport"))
        mkts_set.add(mkt)
        # check decision
        no_bet = r.get("no_bet") or r.get("reason") is not None
        if no_bet:
            skipped_decisions += 1
            continue
        decisions += 1
        # net result
        net += _safe_float(r.get("profit_loss") or r.get("pnl"))
        roi = _safe_float(r.get("roi_percent"))
        rois.append(roi)
        # settlement
        final = _safe_str(r.get("final_result") or r.get("result") or r.get("outcome")).upper()
        if final in ("W", "WIN", "H", "HOME", "YES", "Y"):
            wins += 1
            settled += 1
        elif final in ("L", "LOSS", "A", "AWAY", "NO", "N"):
            losses += 1
            settled += 1
        elif final in ("P", "PUSH", "D", "DRAW", "T", "TIE"):
            pushes += 1
            settled += 1
        # else not settled

    roi_avg = sum(rois) / len(rois) if rois else 0.0
    win_rate = (wins / settled * 100) if settled > 0 else 0.0

    warnings: list[str] = []
    if settled == 0:
        warnings.append(
            "Ablation coverage is available, but settled performance is limited "
            "until row-level outcomes are available."
        )

    return {
        "total_rows": total_rows,
        "eligible_rows": total_rows,
        "skipped_rows": 0,
        "decisions": decisions,
        "skipped_decisions": skipped_decisions,
        "settled_count": settled,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "net_result": round(net, 2),
        "roi_percent": round(roi_avg, 2),
        "win_rate_percent": round(win_rate, 2),
        "sports": sorted(sports_set),
        "market_families": sorted(mkts_set),
        "warnings": warnings,
        "operator_interpretation": (
            f"{settled} settled outcomes of {decisions} decisions. "
            f"ROI: {roi_avg:.2f}%, win rate {win_rate:.2f}%."
        ),
    }


def calculate_roi_by_sport(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Group eligible settled rows by sport and compute per‑sport ROI."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        sk = normalize_sport_key(r.get("sport"))
        groups[sk].append(r)
    result: dict[str, dict] = {}
    for sk, grp in groups.items():
        perf = summarize_ablation_performance(grp)
        result[sk] = {
            "sport_key": sk,
            "rows": perf["total_rows"],
            "settled_count": perf["settled_count"],
            "wins": perf["wins"],
            "losses": perf["losses"],
            "pushes": perf["pushes"],
            "net_result": perf["net_result"],
            "roi_percent": perf["roi_percent"],
            "win_rate_percent": perf["win_rate_percent"],
        }
    return result


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def run_feature_ablation_lab(
    rows: Sequence[Mapping[str, Any]],
    sport: object = None,
    market: object = None,
    mode: str = "single_sport",
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    user_row_threshold: int = 1,
) -> dict[str, Any]:
    """Run the ablation lab: filter rows by mode, apply field ablation,
    and summarise performance."""
    # Step 1 – handle mode
    if mode == "all_sports":
        filter_result = filter_calibration_ready_sports(rows)
        working_rows = filter_result["included_rows"]
        excluded_rows = filter_result["excluded_rows"]  # not used for performance
        included_sports = filter_result["included_sports"]
        excluded_sports = filter_result["excluded_sports"]
        sport_readiness = filter_result["sport_readiness"]
        mode_sport_key = "all_sports"
        mode_market_family = "mixed"
    else:
        # single_sport
        sport_key = normalize_sport_key(sport) if sport else "general"
        working_rows = _rows_for_sport(rows, sport_key) if sport else list(rows)
        if market:
            working_rows = _rows_for_market(working_rows, market)
        if working_rows:
            included_sports = [sport_key]
            excluded_sports = []
        else:
            included_sports = []
            excluded_sports = [
                {
                    "sport_key": sport_key,
                    "readiness_level": "no_data",
                    "missing_required_fields": [],
                    "reason": "No rows found for this sport.",
                }
            ]
        sport_readiness = {}
        mode_sport_key = sport_key
        mode_market_family = normalize_market_family(market, sport=sport_key) if market else "mixed"

    # Step 2 – apply field ablation
    ablation_result = apply_field_ablation(
        working_rows,
        selected_fields=selected_fields,
        removed_fields=removed_fields,
        selected_groups=selected_groups,
        sport=mode_sport_key,
        market=mode_market_family,
        mode=mode,
        user_row_threshold=user_row_threshold,
    )
    eligible = ablation_result["eligible_rows"]

    # Step 3 – summarise performance (only eligible rows)
    perf = summarize_ablation_performance(eligible, ablation_result["active_fields"])

    # Step 4 – per‑sport ROI (eligible rows only)
    roi_by_sport = calculate_roi_by_sport(eligible)

    warnings: list[str] = list(ablation_result.get("warnings", []))
    if mode == "all_sports" and excluded_sports:
        warnings.append(
            f"Excluded {len(excluded_sports)} sport(s) from ROI: "
            + ", ".join(e["sport_key"] for e in excluded_sports)
        )

    included_sport_count = len(included_sports)
    excluded_sport_count = len(excluded_sports)
    sport_population_note: str | None = None
    no_sports_reason: str | None = None
    if not included_sports and not excluded_sports:
        no_sports_reason = "No sports were included because no rows passed the readiness filter."
    elif not included_sports and excluded_sports:
        # Check if any excluded sport is due to no rows.
        any_no_rows = any(
            e.get("reason", "").lower().startswith("no rows") for e in excluded_sports
        )
        if any_no_rows:
            no_sports_reason = "No sports were included because no rows passed the readiness filter."
        else:
            no_sports_reason = "No sports were included because all sports failed the readiness filter."
    else:
        sport_population_note = f"{included_sport_count} sport(s) included, {excluded_sport_count} excluded."

    result = {
        "ok": True,
        "version": FEATURE_ABLATION_LAB_VERSION,
        "mode": mode,
        "sport_key": mode_sport_key,
        "market_family": mode_market_family,
        "field_groups": get_ablation_field_groups_for_sport(mode_sport_key, mode_market_family)["groups"],
        "all_selectable_fields": ablation_result.get("active_fields", []),
        "active_fields": ablation_result.get("active_fields", []),
        "removed_fields": ablation_result.get("removed_fields", []),
        "included_sports": included_sports,
        "excluded_sports": excluded_sports,
        "included_sport_count": included_sport_count,
        "excluded_sport_count": excluded_sport_count,
        "sport_population_note": sport_population_note,
        "no_sports_reason": no_sports_reason,
        "sport_readiness": sport_readiness,
        "performance": perf,
        "roi_by_sport": roi_by_sport,
        "warnings": warnings,
        "operator_interpretation": (
            f"Feature Ablation Lab for {mode_sport_key} ({mode}). "
            f"{eligible} eligible rows, {perf['settled_count']} settled outcomes."
        ),
    }

    # Phase 10H23E metadata fields (defaults, caller may override)
    result["run_type"] = "ablation_test"
    result["baseline_type"] = None
    result["risk_preset_used"] = None
    result["regression_tactic_used"] = None
    result["chance_override_used"] = False
    result["custom_weights_used"] = False
    result["true_baseline_mode"] = False
    result["baseline_warning"] = None
    # Phase 10H23I row‑count threshold metadata (not blocking)
    rows_tested = len(ablation_result.get("core_rows", []))
    result["rows_tested"] = rows_tested
    result["rows_needed_before_trust"] = user_row_threshold
    result["user_row_threshold"] = user_row_threshold
    result["row_threshold_met"] = rows_tested >= user_row_threshold
    if result["row_threshold_met"]:
        result["row_threshold_note"] = (
            f"Rows tested: {rows_tested} / {user_row_threshold} selected by user."
        )
    else:
        result["row_threshold_note"] = (
            f"Rows tested: {rows_tested} / {user_row_threshold} selected by user. "
            f"The run is allowed, but the row count is below your selected review threshold."
        )

    # detect baseline automatically
    if (
        not result["removed_fields"]
        and not result.get("custom_feature_weights")
        and result.get("regression_tactic_used") is None
        and result.get("risk_preset_used") is None
    ):
        result["run_type"] = "true_code_baseline"
        result["true_baseline_mode"] = True
        result["baseline_warning"] = (
            "True Code Baseline is the current model exactly as coded "
            "before removing fields, applying custom weights, or using regression overrides. "
            "It may be unstable, but it is the reference point."
        )

    return result
