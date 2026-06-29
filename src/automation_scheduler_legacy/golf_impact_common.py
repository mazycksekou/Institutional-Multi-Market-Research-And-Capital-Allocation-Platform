from __future__ import annotations

import math
from typing import Any, Iterable

from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import detect_execution_authority_violations, locked_safety_flags


SUPPORTED_GOLF_SPORTS = ("golf", "pga", "lpga")

SUPPORTED_GOLF_MARKETS = (
    "outright_winner",
    "top_5",
    "top_10",
    "top_20",
    "top_30",
    "top_40",
    "make_cut",
    "miss_cut",
    "tournament_matchup",
    "round_matchup",
    "first_round_leader",
    "top_nationality",
    "top_region",
    "round_score",
    "total_score",
    "birdies_or_better",
    "bogeys_or_worse",
    "fairways_hit",
    "greens_in_regulation",
    "driving_distance",
    "longest_drive",
    "putts",
    "three_putts",
    "eagles",
    "holes_in_one",
)

SUPPORTED_GOLF_SKILL_GROUPS = (
    "OFF_THE_TEE",
    "APPROACH",
    "AROUND_THE_GREEN",
    "PUTTING",
    "TEE_TO_GREEN",
    "SCORING",
    "COURSE_FIT",
    "WEATHER_WAVE",
    "CUT_MADE_PROFILE",
    "UNKNOWN",
)

OUTRIGHT_MARKETS = {"outright_winner", "top_nationality", "top_region"}
TOP_FINISH_MARKETS = {"top_5", "top_10", "top_20", "top_30", "top_40"}
CUT_MARKETS = {"make_cut", "miss_cut"}
MATCHUP_MARKETS = {"tournament_matchup", "round_matchup"}
ROUND_MARKETS = {"round_matchup", "first_round_leader", "round_score"}
SCORE_MARKETS = {"round_score", "total_score", "birdies_or_better", "bogeys_or_worse", "eagles", "holes_in_one"}
PLAYER_PROP_MARKETS = {
    "birdies_or_better",
    "bogeys_or_worse",
    "fairways_hit",
    "greens_in_regulation",
    "driving_distance",
    "longest_drive",
    "putts",
    "three_putts",
    "eagles",
    "holes_in_one",
}

ALLOWED_GOLF_REVIEW_STATUSES = (
    "DATA_INSUFFICIENT",
    "CALIBRATION_ONLY",
    "WATCHLIST_REVIEW",
    "ACTIVE_REVIEW",
    "NO_BET",
    "MARKET_REVIEW_ONLY",
    "PLAYER_PROP_REVIEW_ONLY",
    "OUTRIGHT_REVIEW_ONLY",
    "MATCHUP_REVIEW_ONLY",
    "CUT_MARKET_REVIEW_ONLY",
    "WEATHER_WAVE_REVIEW_ONLY",
    "COURSE_FIT_REVIEW_ONLY",
)

FORBIDDEN_GOLF_ACTIONS = (
    "EXECUTE",
    "PLACE_BET",
    "SUBMIT_ORDER",
    "AUTO_BET",
    "AUTO_TRADE",
    "PROVIDER_WRITE",
    "OWNER_APPROVED",
    "FIRE_ORDER",
    "SEND_TO_BROKER",
    "SEND_TO_SPORTSBOOK",
)

DATA_TIER_REQUIREMENTS = {
    0: {"tier_name": "no_reliable_golf_impact_data", "capabilities": ["DATA_INSUFFICIENT"]},
    1: {"tier_name": "basic_player_tournament_context", "capabilities": ["limited_player_context", "low_confidence_review_only"]},
    2: {"tier_name": "strokes_gained_summary_skill_splits", "capabilities": ["limited_sg_diagnostics", "cut_and_matchup_relevance"]},
    3: {"tier_name": "course_fit_weather_field_context", "capabilities": ["course_fit", "weather_wave", "top_finish_review", "player_props"]},
    4: {"tier_name": "shot_level_tracking_simulation_context", "capabilities": ["tracking_optional", "simulation_optional", "richer_diagnostics"]},
}


def normalize_golf_sport(value: Any) -> str:
    raw = str(value or "golf").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "golf_pga": "pga",
        "pga_tour": "pga",
        "liv": "pga",
        "liv_golf": "pga",
        "dp_world_tour": "pga",
        "european_tour": "pga",
        "women_golf": "lpga",
        "womens_golf": "lpga",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in SUPPORTED_GOLF_SPORTS else "golf"


def normalize_golf_market(value: Any) -> str:
    raw = str(value or "top_20").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "winner": "outright_winner",
        "outright": "outright_winner",
        "make_the_cut": "make_cut",
        "miss_the_cut": "miss_cut",
        "h2h": "tournament_matchup",
        "matchup": "tournament_matchup",
        "frl": "first_round_leader",
        "first_round": "first_round_leader",
        "score": "round_score",
        "gir": "greens_in_regulation",
        "fairways": "fairways_hit",
        "driving_dist": "driving_distance",
        "birdies": "birdies_or_better",
        "bogeys": "bogeys_or_worse",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in SUPPORTED_GOLF_MARKETS else normalized


def normalize_golf_skill_group(value: Any) -> str:
    raw = str(value or "UNKNOWN").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "OTT": "OFF_THE_TEE",
        "ARG": "AROUND_THE_GREEN",
        "ATG": "AROUND_THE_GREEN",
        "T2G": "TEE_TO_GREEN",
        "TEE_TO_GREEN": "TEE_TO_GREEN",
        "COURSE": "COURSE_FIT",
        "CUT": "CUT_MADE_PROFILE",
    }
    group = aliases.get(raw, raw)
    return group if group in SUPPORTED_GOLF_SKILL_GROUPS else "UNKNOWN"


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "confirmed", "active", "healthy"}


def clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    number = safe_float(value, low)
    if number is None:
        number = low
    return max(low, min(high, float(number)))


def score_from_range(value: Any, *, low: float, high: float, inverse: bool = False) -> float | None:
    number = safe_float(value)
    if number is None or high == low:
        return None
    score = (number - low) / (high - low) * 100.0
    if inverse:
        score = 100.0 - score
    return clamp(score)


def score_centered(value: Any, *, center: float, span: float) -> float | None:
    number = safe_float(value)
    if number is None or span <= 0:
        return None
    return clamp(50.0 + ((number - center) / span) * 50.0)


def percent_score(value: Any) -> float | None:
    number = safe_float(value)
    if number is None:
        return None
    if 0.0 <= number <= 1.0:
        return clamp(number * 100.0)
    return clamp(number)


def categorical_score(value: Any, mapping: dict[str, float], default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return mapping.get(raw, default)


def weighted_average(parts: Iterable[tuple[Any, float]]) -> float | None:
    total = 0.0
    weight = 0.0
    for value, part_weight in parts:
        number = safe_float(value)
        if number is None or part_weight <= 0:
            continue
        total += number * part_weight
        weight += part_weight
    return total / weight if weight > 0 else None


def present_fields(row: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [field for field in fields if row.get(field) not in (None, "", [])]


def missing_fields(row: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [field for field in fields if row.get(field) in (None, "", [])]


def compact_list(values: Iterable[Any], limit: int = 20) -> list[Any]:
    out: list[Any] = []
    for value in values:
        if value in (None, "", []):
            continue
        if value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def confidence_from_sample(sample_size: Any, *, full_sample: float = 80.0, floor: float = 20.0, cap: float = 90.0) -> float:
    sample = safe_float(sample_size, 0.0) or 0.0
    return clamp(floor + min(sample / max(full_sample, 1.0), 1.0) * (cap - floor))


def golf_safety_fields() -> dict[str, Any]:
    flags = locked_safety_flags()
    flags.update(
        {
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "owner_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
            "raw_payload_included": False,
            "raw_payload_exposed": False,
            "secrets_included": False,
            "compact_response": True,
            "sportsbook_bet_execution_enabled": False,
        }
    )
    return flags


def finalize_golf_response(payload: dict[str, Any], *, source_payload: Any = None) -> dict[str, Any]:
    safe = redact_sensitive(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(golf_safety_fields())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        safe.update(golf_safety_fields())
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    safe["compact_response"] = True
    return safe
