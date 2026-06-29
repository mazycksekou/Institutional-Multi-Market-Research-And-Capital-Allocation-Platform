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


SUPPORTED_SOCCER_SPORTS = ("soccer", "football", "association_football")

SOCCER_SPORT_ALIASES = {
    "soccer": "soccer",
    "football": "football",
    "association_football": "association_football",
    "association football": "association_football",
    "epl": "soccer",
    "premier_league": "soccer",
    "uefa": "soccer",
    "fifa": "soccer",
}

SUPPORTED_SOCCER_MARKETS = (
    "three_way_moneyline",
    "moneyline",
    "draw_no_bet",
    "double_chance",
    "asian_handicap",
    "spread",
    "total",
    "team_total",
    "both_teams_to_score",
    "correct_score",
    "first_half_moneyline",
    "first_half_total",
    "first_half_team_total",
    "first_half_asian_handicap",
    "anytime_goal",
    "shots",
    "shots_on_target",
    "assists",
    "passes",
    "tackles",
    "cards",
    "fouls_committed",
    "fouls_drawn",
    "saves",
    "goalkeeper_saves",
)

SUPPORTED_SOCCER_ROLES = (
    "GOALKEEPER",
    "CENTER_BACK",
    "FULLBACK",
    "WINGBACK",
    "DEFENSIVE_MIDFIELDER",
    "CENTRAL_MIDFIELDER",
    "ATTACKING_MIDFIELDER",
    "WINGER",
    "FORWARD",
    "STRIKER",
    "SET_PIECE_TAKER",
    "PENALTY_TAKER",
    "TEAM_ATTACK",
    "TEAM_DEFENSE",
    "UNKNOWN",
)

TEAM_MARKETS = {
    "three_way_moneyline",
    "moneyline",
    "draw_no_bet",
    "double_chance",
    "asian_handicap",
    "spread",
    "total",
    "team_total",
    "both_teams_to_score",
    "correct_score",
    "first_half_moneyline",
    "first_half_total",
    "first_half_team_total",
    "first_half_asian_handicap",
}

PLAYER_PROP_MARKETS = {
    "anytime_goal",
    "shots",
    "shots_on_target",
    "assists",
    "passes",
    "tackles",
    "cards",
    "fouls_committed",
    "fouls_drawn",
    "saves",
    "goalkeeper_saves",
}

TOTAL_MARKETS = {"total", "team_total", "both_teams_to_score", "first_half_total", "first_half_team_total"}
TACTICAL_MARKETS = {"three_way_moneyline", "asian_handicap", "spread", "draw_no_bet", "double_chance"}
REFEREE_MARKETS = {"cards", "fouls_committed", "fouls_drawn", "total", "both_teams_to_score"}
SET_PIECE_MARKETS = {"anytime_goal", "assists", "shots", "team_total", "total"}
FIRST_HALF_MARKETS = {"first_half_moneyline", "first_half_total", "first_half_team_total", "first_half_asian_handicap"}

ALLOWED_SOCCER_ACTIONS = (
    "ACTIVE_REVIEW",
    "WATCHLIST_REVIEW",
    "CALIBRATION_ONLY",
    "NO_BET",
    "DATA_INSUFFICIENT",
    "MARKET_REVIEW_ONLY",
    "PLAYER_PROP_REVIEW_ONLY",
    "TEAM_MARKET_REVIEW_ONLY",
    "TOTALS_REVIEW_ONLY",
    "TACTICAL_REVIEW_ONLY",
    "SET_PIECE_REVIEW_ONLY",
    "REFEREE_CONTEXT_REVIEW_ONLY",
)

FORBIDDEN_SOCCER_ACTIONS = (
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
        "tier_name": "no_reliable_soccer_impact_data",
        "capabilities": ["DATA_INSUFFICIENT"],
        "minimum_groups": [],
    },
    1: {
        "tier_name": "basic_team_game_context",
        "capabilities": ["limited_team_context", "low_confidence_review_only"],
        "minimum_groups": ["basic_game_context"],
    },
    2: {
        "tier_name": "shot_xg_set_piece_referee_context",
        "capabilities": ["chance_quality", "team_total_btts_first_half", "limited_referee_context"],
        "minimum_groups": ["shot_context", "xg_context"],
    },
    3: {
        "tier_name": "event_possession_value_player_role_context",
        "capabilities": ["expected_threat", "possession_value", "pressing_transition", "player_role_props"],
        "minimum_groups": ["possession_value_context", "player_role_context"],
    },
    4: {
        "tier_name": "tracking_360_tactical_micro_event_context_optional",
        "capabilities": ["pitch_control", "formation_phase_shape", "off_ball_and_marking_context"],
        "minimum_groups": ["tracking_context"],
    },
}


def normalize_soccer_sport(value: Any) -> str:
    raw = str(value or "soccer").strip().lower().replace("-", "_")
    raw = raw.replace(" ", "_")
    return SOCCER_SPORT_ALIASES.get(raw, raw if raw in SUPPORTED_SOCCER_SPORTS else "soccer")


def normalize_soccer_market(value: Any) -> str:
    raw = str(value or "three_way_moneyline").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "ml": "moneyline",
        "h2h": "moneyline",
        "1x2": "three_way_moneyline",
        "three_way_ml": "three_way_moneyline",
        "3_way_moneyline": "three_way_moneyline",
        "dnb": "draw_no_bet",
        "ah": "asian_handicap",
        "asian_spread": "asian_handicap",
        "handicap": "asian_handicap",
        "btts": "both_teams_to_score",
        "both_teams_score": "both_teams_to_score",
        "cs": "correct_score",
        "sot": "shots_on_target",
        "goalkeeper_save": "goalkeeper_saves",
        "keeper_saves": "goalkeeper_saves",
        "first_half_ah": "first_half_asian_handicap",
        "1h_total": "first_half_total",
        "1h_team_total": "first_half_team_total",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_SOCCER_MARKETS else raw)


def normalize_soccer_role(value: Any) -> str:
    raw = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "GK": "GOALKEEPER",
        "KEEPER": "GOALKEEPER",
        "CB": "CENTER_BACK",
        "CENTERBACK": "CENTER_BACK",
        "CENTRE_BACK": "CENTER_BACK",
        "RB": "FULLBACK",
        "LB": "FULLBACK",
        "FB": "FULLBACK",
        "WB": "WINGBACK",
        "RWB": "WINGBACK",
        "LWB": "WINGBACK",
        "DM": "DEFENSIVE_MIDFIELDER",
        "CDM": "DEFENSIVE_MIDFIELDER",
        "CM": "CENTRAL_MIDFIELDER",
        "AM": "ATTACKING_MIDFIELDER",
        "CAM": "ATTACKING_MIDFIELDER",
        "RW": "WINGER",
        "LW": "WINGER",
        "FW": "FORWARD",
        "ST": "STRIKER",
        "CF": "STRIKER",
        "PENALTY": "PENALTY_TAKER",
        "SET_PIECE": "SET_PIECE_TAKER",
        "TEAM_OFFENSE": "TEAM_ATTACK",
        "TEAM_ATTACKING": "TEAM_ATTACK",
        "TEAM_DEFENSIVE": "TEAM_DEFENSE",
    }
    role = aliases.get(raw, raw)
    return role if role in SUPPORTED_SOCCER_ROLES else "UNKNOWN"


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


def soccer_safety_flags() -> dict[str, Any]:
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


def _sensitive_key_for_soccer_output(key: Any) -> bool:
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
    if "possession" in lower or "key_pass" in lower:
        return False
    for part in SECRET_KEY_PARTS:
        if part == "session":
            if lower in {"session", "session_id", "session_token", "session_cookie"}:
                return True
            continue
        if part in lower:
            return True
    return False


def redact_soccer_output(payload: Any, *, list_limit: int = 100) -> Any:
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
            elif _sensitive_key_for_soccer_output(key):
                out[str(key)] = REDACTED
            else:
                out[str(key)] = redact_soccer_output(value, list_limit=list_limit)
        return out
    if isinstance(payload, list):
        return [redact_soccer_output(value, list_limit=list_limit) for value in payload[: max(1, int(list_limit or 100))]]
    if isinstance(payload, str) and looks_like_secret_value(payload):
        return redact_string(payload)
    return payload


def finalize_soccer_response(payload: dict[str, Any], *, source_payload: Any = None) -> dict[str, Any]:
    safe = redact_soccer_output(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(soccer_safety_flags())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        safe.update(soccer_safety_flags())
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    safe["compact_response"] = True
    return safe
