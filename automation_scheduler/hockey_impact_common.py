from __future__ import annotations

import math
from typing import Any, Iterable

from .secret_safety import (
    OMITTED,
    RAW_PAYLOAD_KEYS,
    REDACTED,
    SECRET_KEY_PARTS,
    looks_like_secret_value,
    redact_string,
    secret_safety_fields,
)
from .security_policy import detect_execution_authority_violations, locked_safety_flags


SUPPORTED_HOCKEY_SPORTS = ("icehockey_nhl",)

HOCKEY_SPORT_ALIASES = {
    "nhl": "icehockey_nhl",
    "hockey_nhl": "icehockey_nhl",
    "ice_hockey_nhl": "icehockey_nhl",
    "icehockey_nhl": "icehockey_nhl",
}

SUPPORTED_HOCKEY_MARKETS = (
    "moneyline",
    "three_way_moneyline",
    "regulation_moneyline",
    "puckline",
    "total",
    "team_total",
    "first_period_moneyline",
    "first_period_total",
    "first_period_team_total",
    "player_shots_on_goal",
    "player_points",
    "player_goals",
    "player_assists",
    "player_power_play_points",
    "player_blocked_shots",
    "anytime_goal",
    "goalie_saves",
    "goalie_goals_allowed",
    "goalie_win",
    "goalie_shutout",
)

SUPPORTED_HOCKEY_ROLES = (
    "CENTER",
    "WINGER",
    "DEFENSEMAN",
    "GOALIE",
    "POWER_PLAY_UNIT",
    "PENALTY_KILL_UNIT",
    "LINE",
    "DEFENSIVE_PAIR",
    "TEAM_OFFENSE",
    "TEAM_DEFENSE",
    "SPECIAL_TEAMS",
    "UNKNOWN",
)

TEAM_MARKETS = {
    "moneyline",
    "three_way_moneyline",
    "regulation_moneyline",
    "puckline",
    "total",
    "team_total",
    "first_period_moneyline",
    "first_period_total",
    "first_period_team_total",
}

SKATER_PROP_MARKETS = {
    "player_shots_on_goal",
    "player_points",
    "player_goals",
    "player_assists",
    "player_power_play_points",
    "player_blocked_shots",
    "anytime_goal",
}

GOALIE_PROP_MARKETS = {
    "goalie_saves",
    "goalie_goals_allowed",
    "goalie_win",
    "goalie_shutout",
}

SPECIAL_TEAMS_MARKETS = {
    "player_power_play_points",
    "team_total",
    "total",
    "anytime_goal",
    "first_period_total",
}

FIRST_PERIOD_MARKETS = {
    "first_period_moneyline",
    "first_period_total",
    "first_period_team_total",
}

ALLOWED_HOCKEY_ACTIONS = (
    "ACTIVE_REVIEW",
    "WATCHLIST_REVIEW",
    "CALIBRATION_ONLY",
    "NO_BET",
    "DATA_INSUFFICIENT",
    "MARKET_REVIEW_ONLY",
    "PLAYER_PROP_REVIEW_ONLY",
    "TEAM_MARKET_REVIEW_ONLY",
    "GOALIE_PROP_REVIEW_ONLY",
    "SPECIAL_TEAMS_REVIEW_ONLY",
)

FORBIDDEN_HOCKEY_ACTIONS = (
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
    0: {
        "tier_name": "no_reliable_hockey_impact_data",
        "capabilities": ["DATA_INSUFFICIENT"],
        "minimum_groups": [],
    },
    1: {
        "tier_name": "basic_team_game_context",
        "capabilities": ["limited_team_context", "low_confidence_review_only"],
        "minimum_groups": ["basic_game_context"],
    },
    2: {
        "tier_name": "shot_attempt_possession_special_teams_context",
        "capabilities": ["shot_volume", "possession_proxy", "special_teams_proxy", "first_period_proxy"],
        "minimum_groups": ["shot_volume_context", "shot_attempt_context"],
    },
    3: {
        "tier_name": "expected_goals_line_pair_goalie_quality_context",
        "capabilities": ["expected_goals", "line_pair_context", "goalie_quality_context", "skater_props"],
        "minimum_groups": ["expected_goal_context"],
    },
    4: {
        "tier_name": "tracking_transition_micro_event_context_optional",
        "capabilities": ["zone_entries_exits", "forecheck_rush_rebound_slot", "shift_workload", "deployment_matching"],
        "minimum_groups": ["tracking_context"],
    },
}


def normalize_hockey_sport(value: Any) -> str:
    raw = str(value or "icehockey_nhl").strip().lower().replace("-", "_").replace(" ", "_")
    return HOCKEY_SPORT_ALIASES.get(raw, raw if raw in SUPPORTED_HOCKEY_SPORTS else "icehockey_nhl")


def normalize_hockey_market(value: Any) -> str:
    raw = str(value or "moneyline").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "ml": "moneyline",
        "h2h": "moneyline",
        "3_way_moneyline": "three_way_moneyline",
        "three_way_ml": "three_way_moneyline",
        "regulation_ml": "regulation_moneyline",
        "puck_line": "puckline",
        "totals": "total",
        "sog": "player_shots_on_goal",
        "shots_on_goal": "player_shots_on_goal",
        "player_sog": "player_shots_on_goal",
        "ppp": "player_power_play_points",
        "power_play_points": "player_power_play_points",
        "blocked_shots": "player_blocked_shots",
        "anytime_goal_scorer": "anytime_goal",
        "saves": "goalie_saves",
        "goals_allowed": "goalie_goals_allowed",
        "goalie_goal_allowed": "goalie_goals_allowed",
        "1p_total": "first_period_total",
        "first_period_totals": "first_period_total",
        "1p_team_total": "first_period_team_total",
        "1p_moneyline": "first_period_moneyline",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_HOCKEY_MARKETS else raw)


def normalize_hockey_role(value: Any) -> str:
    raw = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "C": "CENTER",
        "CENTRE": "CENTER",
        "LW": "WINGER",
        "RW": "WINGER",
        "W": "WINGER",
        "D": "DEFENSEMAN",
        "DEFENDER": "DEFENSEMAN",
        "DEFENCEMAN": "DEFENSEMAN",
        "G": "GOALIE",
        "GK": "GOALIE",
        "PP": "POWER_PLAY_UNIT",
        "PK": "PENALTY_KILL_UNIT",
        "PAIR": "DEFENSIVE_PAIR",
        "OFFENSE": "TEAM_OFFENSE",
        "DEFENSE": "TEAM_DEFENSE",
        "ST": "SPECIAL_TEAMS",
    }
    role = aliases.get(raw, raw)
    return role if role in SUPPORTED_HOCKEY_ROLES else "UNKNOWN"


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
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "active", "available", "healthy", "confirmed", "probable"}


def clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    number = safe_float(value, low)
    if number is None:
        number = low
    return max(low, min(high, float(number)))


def percent_score(value: Any, *, already_score_ok: bool = True) -> float | None:
    number = safe_float(value)
    if number is None:
        return None
    if already_score_ok and 0.0 <= number <= 100.0:
        return clamp(number)
    if 0.0 <= number <= 1.0:
        return clamp(number * 100.0)
    return clamp(number)


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


def weighted_average(parts: Iterable[tuple[Any, float]]) -> float | None:
    total = 0.0
    weight = 0.0
    for value, part_weight in parts:
        number = safe_float(value)
        if number is None or part_weight <= 0:
            continue
        total += number * part_weight
        weight += part_weight
    if weight <= 0:
        return None
    return total / weight


def average_present(values: Iterable[Any]) -> float | None:
    numbers = [safe_float(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


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


def confidence_from_sample(sample_size: Any, *, full_sample: float = 500.0, floor: float = 20.0, cap: float = 95.0) -> float:
    sample = safe_float(sample_size, 0.0) or 0.0
    return clamp(floor + min(sample / max(full_sample, 1.0), 1.0) * (cap - floor))


def hockey_safety_flags() -> dict[str, Any]:
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
            "sportsbook_bet_execution_enabled": False,
            "compact_response": True,
        }
    )
    return flags


def _sensitive_key_for_hockey_output(key: Any) -> bool:
    lower = str(key or "").strip().lower()
    if lower in {
        "secrets_included",
        "secrets_detected",
        "source_secret_like_content_redacted",
        "redacted_payload_contains_secret",
        "auth_header_exposed",
        "signature_exposed",
        "redaction_applied",
        "new_api_keys_required",
        "api_keys_required",
        "paid_provider_required",
    }:
        return False
    if "possession" in lower:
        return False
    for part in SECRET_KEY_PARTS:
        if part == "session":
            if lower in {"session", "session_id", "session_token", "session_cookie"}:
                return True
            continue
        if part in lower:
            return True
    return False


def redact_hockey_output(payload: Any, *, list_limit: int = 100) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            lower = str(key).strip().lower()
            if lower in RAW_PAYLOAD_KEYS or lower in {
                "order_payload",
                "broker_order",
                "sportsbook_ticket",
                "bet_slip",
                "wager_payload",
                "ticket_payload",
                "slip_payload",
                "provider_write_payload",
                "execution_payload",
            }:
                out[str(key)] = OMITTED
            elif _sensitive_key_for_hockey_output(key):
                out[str(key)] = REDACTED
            else:
                out[str(key)] = redact_hockey_output(value, list_limit=list_limit)
        return out
    if isinstance(payload, list):
        return [redact_hockey_output(value, list_limit=list_limit) for value in payload[: max(1, int(list_limit or 100))]]
    if isinstance(payload, str) and looks_like_secret_value(payload):
        return redact_string(payload)
    return payload


def finalize_hockey_response(payload: dict[str, Any], *, source_payload: Any = None) -> dict[str, Any]:
    safe = redact_hockey_output(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(hockey_safety_flags())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        safe.update(hockey_safety_flags())
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    safe["compact_response"] = True
    return safe
