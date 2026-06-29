from __future__ import annotations

from typing import Any

from .basketball_incentive_context import evaluate_incentive_context
from .basketball_lineup_matchup_context import evaluate_lineup_matchup_context
from .basketball_market_relevance import evaluate_market_relevance
from .basketball_player_impact_calibration import evaluate_basketball_player_impact_calibration
from .basketball_player_impact_common import (
    clamp,
    compact_list,
    finalize_safe_response,
    normalize_basketball_sport,
    percent_score,
    safe_float,
    score_from_range,
    sport_contract,
    weighted_average,
)
from .basketball_player_impact_red_team import review_basketball_player_impact
from .basketball_possession_impact import evaluate_possession_impact
from .basketball_role_context import evaluate_role_context
from .basketball_tracking_opportunity import evaluate_tracking_opportunity
from src.security.policy import detect_execution_authority_violations


AVAILABILITY_INPUTS = (
    "games_played",
    "games_missed",
    "injury_status",
    "injury_designation",
    "minutes_last_5",
    "minutes_last_10",
    "projected_minutes",
    "minutes_volatility",
    "foul_trouble_rate",
    "rotation_status",
    "starter_status",
    "closing_lineup_status",
    "back_to_back_risk",
    "load_management_risk",
    "coach_rotation_volatility",
    "recent_overtime_minutes",
    "rest_days",
)

REVIEW_STATUSES = ("NO_REVIEW", "LOW_PRIORITY_REVIEW", "WATCHLIST_REVIEW", "ACTIVE_REVIEW", "DATA_INSUFFICIENT", "NO_BET")


def _merge_candidate_inputs(candidate: dict[str, Any] | None) -> dict[str, Any]:
    raw = candidate if isinstance(candidate, dict) else {}
    stats = raw.get("input_stats") if isinstance(raw.get("input_stats"), dict) else {}
    merged = dict(stats)
    for key, value in raw.items():
        if key != "input_stats":
            merged[key] = value
    return merged


def _list_average(value: Any) -> float | None:
    if isinstance(value, list):
        nums = [safe_float(item) for item in value]
        nums = [item for item in nums if item is not None]
        return sum(nums) / len(nums) if nums else None
    return safe_float(value)


def _injury_score(row: dict[str, Any]) -> tuple[float, float]:
    designation = str(row.get("injury_designation") or row.get("injury_status") or "").strip().lower()
    if designation in {"out", "inactive", "suspended"}:
        return 0.0, 100.0
    if designation in {"doubtful"}:
        return 22.0, 78.0
    if designation in {"questionable", "game_time_decision", "gtd"}:
        return 52.0, 48.0
    if designation in {"probable", "available", "active"}:
        return 84.0, 16.0
    games_played = safe_float(row.get("games_played"))
    games_missed = safe_float(row.get("games_missed"))
    if games_played is not None and games_missed is not None and (games_played + games_missed) > 0:
        availability = games_played / (games_played + games_missed) * 100.0
        return clamp(availability), clamp(100.0 - availability)
    return 62.0, 38.0


def evaluate_availability_minutes(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = [key for key in AVAILABILITY_INPUTS if source.get(key) not in (None, "", [])]
    missing = [key for key in AVAILABILITY_INPUTS if source.get(key) in (None, "", [])]
    injury_availability, injury_risk = _injury_score(source)
    projected_minutes = score_from_range(source.get("projected_minutes"), low=8.0, high=38.0)
    minutes_5 = _list_average(source.get("minutes_last_5"))
    minutes_10 = _list_average(source.get("minutes_last_10"))
    if minutes_5 is not None and minutes_10 is not None:
        drift = abs(minutes_5 - minutes_10)
        recent_minutes_score = clamp(score_from_range(minutes_5, low=8.0, high=38.0) or 0.0)
        stability_from_recent = clamp(100.0 - drift * 6.0)
    else:
        recent_minutes_score = projected_minutes or 0.0
        stability_from_recent = 55.0 if projected_minutes is not None else 25.0
    minutes_volatility = score_from_range(source.get("minutes_volatility"), low=0.0, high=14.0, inverse=True)
    coach_stability = score_from_range(source.get("coach_rotation_volatility"), low=0.0, high=1.0, inverse=True)
    rotation_status = str(source.get("rotation_status") or source.get("starter_status") or "").strip().lower()
    if rotation_status in {"starter", "locked_starter", "closing", "core_rotation"}:
        rotation_trust = 82.0
    elif rotation_status in {"bench", "rotation", "sixth_man"}:
        rotation_trust = 62.0
    elif rotation_status in {"fringe", "two_way", "spot_minutes"}:
        rotation_trust = 32.0
    else:
        rotation_trust = 48.0
    if str(source.get("closing_lineup_status") or "").strip().lower() in {"closing", "likely", "yes"}:
        rotation_trust = max(rotation_trust, 78.0)
    load_management = percent_score(source.get("load_management_risk"))
    if load_management is None:
        load_management = 55.0 if str(source.get("injury_status") or "").lower() in {"probable", "questionable"} else 20.0
    back_to_back_risk = percent_score(source.get("back_to_back_risk")) or (35.0 if str(source.get("back_to_back") or "").lower() in {"true", "yes", "1"} else 0.0)
    overtime_risk = score_from_range(source.get("recent_overtime_minutes"), low=0.0, high=20.0) or 0.0
    load_management = clamp(max(load_management, (back_to_back_risk * 0.6) + (overtime_risk * 0.35)))
    foul_trouble = score_from_range(source.get("foul_trouble_rate"), low=0.0, high=0.20) or score_from_range(source.get("foul_trouble_rate"), low=0.0, high=20.0) or 0.0
    minutes_stability = weighted_average(
        (
            (stability_from_recent, 0.8),
            (minutes_volatility, 1.0),
            (coach_stability, 0.55),
            (rotation_trust, 0.7),
            (100.0 - load_management, 0.55),
            (100.0 - foul_trouble, 0.3),
        )
    ) or 0.0
    projected_confidence = weighted_average(
        (
            (projected_minutes, 0.8),
            (recent_minutes_score, 0.5),
            (minutes_stability, 0.9),
            (injury_availability, 0.6),
            (rotation_trust, 0.55),
        )
    ) or 0.0
    availability = weighted_average(
        (
            (injury_availability, 1.1),
            (100.0 - load_management, 0.75),
            (100.0 - back_to_back_risk, 0.35),
            (minutes_stability, 0.65),
            (rotation_trust, 0.35),
        )
    ) or 0.0
    status = "missing" if not present else ("partial" if len(present) < 6 else "ok")
    return finalize_safe_response(
        {
            "availability_score": round(clamp(availability), 2),
            "minutes_stability_score": round(clamp(minutes_stability), 2),
            "projected_minutes_confidence": round(clamp(projected_confidence), 2),
            "rotation_trust_score": round(clamp(rotation_trust), 2),
            "load_management_risk": round(clamp(load_management), 2),
            "foul_trouble_risk": round(clamp(foul_trouble), 2),
            "injury_risk_score": round(clamp(injury_risk), 2),
            "availability_status": status,
            "availability_missing_inputs": compact_list(missing, limit=25),
        },
        source_payload=source,
    )


def _downgrade_status(status: str, downgrade: float) -> str:
    order = ["NO_REVIEW", "LOW_PRIORITY_REVIEW", "WATCHLIST_REVIEW", "ACTIVE_REVIEW"]
    if status in {"NO_BET", "DATA_INSUFFICIENT"} or downgrade <= 0:
        return status
    steps = 2 if downgrade >= 24 else 1
    idx = order.index(status) if status in order else 0
    return order[max(0, idx - steps)]


def _recommend_status(*, top_market_score: float, missing_major_count: int, insufficient_sample: bool, fatal_safety: bool, incentive_only: bool) -> str:
    if fatal_safety:
        return "NO_BET"
    if incentive_only:
        return "DATA_INSUFFICIENT"
    if missing_major_count >= 3:
        return "DATA_INSUFFICIENT"
    if top_market_score >= 72.0 and missing_major_count <= 1:
        return "ACTIVE_REVIEW"
    if top_market_score >= 62.0:
        return "WATCHLIST_REVIEW" if insufficient_sample else "ACTIVE_REVIEW"
    if top_market_score >= 45.0:
        return "LOW_PRIORITY_REVIEW" if insufficient_sample else "WATCHLIST_REVIEW"
    return "NO_REVIEW"


def run_basketball_player_impact(
    candidate: dict[str, Any] | None = None,
    *,
    outcome_records: list[dict[str, Any]] | None = None,
    red_team_provider: str | None = None,
) -> dict[str, Any]:
    source = _merge_candidate_inputs(candidate)
    sport = normalize_basketball_sport(source.get("sport") or source.get("league"))
    contract = sport_contract(sport)
    source["sport"] = sport
    source.setdefault("league", contract["league"])

    fatal_violations = detect_execution_authority_violations(candidate or {})
    possession = evaluate_possession_impact(source)
    tracking = evaluate_tracking_opportunity(source)
    role = evaluate_role_context(source)
    lineup = evaluate_lineup_matchup_context(source)
    availability = evaluate_availability_minutes(source)
    incentive = evaluate_incentive_context(source)
    market = evaluate_market_relevance(
        source,
        possession=possession,
        tracking=tracking,
        role=role,
        lineup=lineup,
        availability=availability,
        incentive=incentive,
    )
    calibration = evaluate_basketball_player_impact_calibration(source, outcome_records or [], market_type=source.get("market_type") or source.get("market"))

    top_market_score = max((safe_float(value, 0.0) or 0.0 for value in (market.get("market_relevance_scores") or {}).values()), default=0.0)
    missing_major = sum(
        1
        for status in (
            possession.get("possession_impact_status"),
            tracking.get("tracking_status"),
            lineup.get("lineup_matchup_status"),
            availability.get("availability_status"),
        )
        if status == "missing"
    )
    non_incentive_signal = max(
        safe_float(possession.get("possession_impact_score"), 0.0) or 0.0,
        safe_float(tracking.get("tracking_opportunity_score"), 0.0) or 0.0,
        safe_float(role.get("role_adjusted_efficiency_score"), 0.0) or 0.0,
        safe_float(lineup.get("lineup_fit_score"), 0.0) or 0.0,
        safe_float(availability.get("availability_score"), 0.0) or 0.0,
    )
    incentive_only = non_incentive_signal < 35.0 and (safe_float(incentive.get("incentive_context_score"), 0.0) or 0.0) >= 55.0
    base_status = _recommend_status(
        top_market_score=top_market_score,
        missing_major_count=missing_major,
        insufficient_sample=bool(calibration.get("insufficient_sample", True)),
        fatal_safety=bool(fatal_violations),
        incentive_only=incentive_only,
    )
    player_impact_score = weighted_average(
        (
            (possession.get("possession_impact_score"), 1.1 if possession.get("possession_impact_status") != "missing" else 0.0),
            (tracking.get("tracking_opportunity_score"), 0.8 if tracking.get("tracking_status") != "missing" else 0.0),
            (role.get("role_adjusted_efficiency_score"), 0.9),
            (lineup.get("lineup_fit_score"), 0.7 if lineup.get("lineup_matchup_status") != "missing" else 0.0),
            (lineup.get("matchup_fit_score"), 0.55 if lineup.get("lineup_matchup_status") != "missing" else 0.0),
            (availability.get("availability_score"), 1.0 if availability.get("availability_status") != "missing" else 0.0),
            (top_market_score, 0.75),
            (incentive.get("incentive_context_score"), 0.15 if not incentive_only else 0.0),
        )
    ) or 0.0

    prelim = {
        "possession_impact": possession,
        "tracking_opportunity": tracking,
        "role_context": role,
        "lineup_matchup_context": lineup,
        "availability_minutes": availability,
        "incentive_context": incentive,
        "market_relevance": market,
        "calibration": calibration,
        "recommended_review_status": base_status,
    }
    red_team = review_basketball_player_impact(source, prelim, provider=red_team_provider)
    recommended_status = _downgrade_status(base_status, safe_float(red_team.get("red_team_downgrade"), 0.0) or 0.0)
    if fatal_violations:
        recommended_status = "NO_BET"

    missing_inputs = compact_list(
        [
            *possession.get("possession_impact_missing_inputs", []),
            *tracking.get("tracking_missing_inputs", []),
            *role.get("role_missing_inputs", []),
            *lineup.get("lineup_matchup_missing_inputs", []),
            *availability.get("availability_missing_inputs", []),
            *incentive.get("incentive_missing_inputs", []),
            *market.get("market_relevance_missing_inputs", []),
            *calibration.get("calibration_missing_inputs", []),
            *red_team.get("missing_data_requested", []),
        ],
        limit=45,
    )
    markets_to_review = list(market.get("recommended_market_focus") or [])
    if recommended_status in {"NO_REVIEW", "DATA_INSUFFICIENT", "NO_BET"}:
        markets_to_review = []

    payload = {
        "ok": True,
        "status": "basketball_player_impact_complete",
        "sport": sport,
        "league": contract["league"],
        "sport_contract_id": contract["sport_contract_id"],
        "calibration_bucket_prefix": contract["calibration_bucket_prefix"],
        "legacy_sport_alias": contract.get("legacy_sport_alias"),
        "player_id": source.get("player_id") or source.get("athlete_id"),
        "player_name_optional_redacted": source.get("player_name") or source.get("player") or source.get("athlete_name"),
        "team_id": source.get("team_id") or source.get("team"),
        "opponent_id": source.get("opponent_id") or source.get("opponent"),
        "player_impact_score": round(clamp(player_impact_score), 2),
        "possession_impact_score": possession.get("possession_impact_score", 0.0),
        "tracking_opportunity_score": tracking.get("tracking_opportunity_score", 0.0),
        "role_adjusted_efficiency_score": role.get("role_adjusted_efficiency_score", 0.0),
        "lineup_fit_score": lineup.get("lineup_fit_score", 0.0),
        "matchup_fit_score": lineup.get("matchup_fit_score", 0.0),
        "availability_score": availability.get("availability_score", 0.0),
        "minutes_stability_score": availability.get("minutes_stability_score", 0.0),
        "incentive_context_score": incentive.get("incentive_context_score", 0.0),
        "market_relevance_scores": market.get("market_relevance_scores", {}),
        "calibration_status": calibration.get("calibration_status", "insufficient_sample"),
        "insufficient_sample": bool(calibration.get("insufficient_sample", True)),
        "recommended_review_status": recommended_status,
        "markets_to_review": compact_list(markets_to_review, limit=8),
        "markets_to_avoid": compact_list(market.get("markets_to_avoid") or [], limit=8),
        "missing_inputs": missing_inputs,
        "fatal_safety_violations": fatal_violations,
        "possession_impact": possession,
        "tracking_opportunity": tracking,
        "role_context": role,
        "lineup_matchup_context": lineup,
        "availability_minutes": availability,
        "incentive_context": incentive,
        "market_relevance": market,
        "calibration": calibration,
        "red_team": red_team,
        "review_status_values": list(REVIEW_STATUSES),
    }
    return finalize_safe_response(payload, source_payload=candidate or {})
