from __future__ import annotations

import math
from typing import Any, Iterable

from src.security.secret_safety import redact_sensitive, secret_safety_fields
from src.security.policy import detect_execution_authority_violations, locked_safety_flags


SUPPORTED_FOOTBALL_SPORTS = (
    "americanfootball_nfl",
    "americanfootball_ncaaf",
)

FOOTBALL_SPORT_ALIASES = {
    "nfl": "americanfootball_nfl",
    "americanfootball_nfl": "americanfootball_nfl",
    "football_nfl": "americanfootball_nfl",
    "pro_football": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "cfb": "americanfootball_ncaaf",
    "college_football": "americanfootball_ncaaf",
    "americanfootball_ncaaf": "americanfootball_ncaaf",
}

SUPPORTED_FOOTBALL_MARKET_TYPES = (
    "moneyline",
    "spread",
    "total",
    "team_total",
    "first_half_spread",
    "first_half_total",
    "player_passing_prop",
    "player_rushing_prop",
    "player_receiving_prop",
    "anytime_td",
    "sack_prop",
    "interception_prop",
    "defensive_prop",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_attempts",
    "receiving_yards",
    "receptions",
    "sacks",
    "tackles",
    "field_goals",
    "longest_reception",
    "longest_rush",
)

SUPPORTED_FOOTBALL_ROLES = (
    "QB",
    "RB",
    "WR",
    "TE",
    "OL",
    "DL",
    "EDGE",
    "LB",
    "CB",
    "S",
    "K",
    "P",
    "TEAM_OFFENSE",
    "TEAM_DEFENSE",
    "SPECIAL_TEAMS",
    "UNKNOWN",
)

TEAM_MARKETS = {"moneyline", "spread", "total", "team_total", "first_half_spread", "first_half_total"}
PLAYER_PROP_MARKETS = {
    "player_passing_prop",
    "player_rushing_prop",
    "player_receiving_prop",
    "anytime_td",
    "sack_prop",
    "interception_prop",
    "defensive_prop",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_attempts",
    "receiving_yards",
    "receptions",
    "sacks",
    "tackles",
    "field_goals",
    "longest_reception",
    "longest_rush",
}

ALLOWED_FOOTBALL_ACTIONS = (
    "ACTIVE_REVIEW",
    "WATCHLIST_REVIEW",
    "CALIBRATION_ONLY",
    "NO_BET",
    "DATA_INSUFFICIENT",
    "MARKET_REVIEW_ONLY",
    "PLAYER_PROP_REVIEW_ONLY",
    "TEAM_MARKET_REVIEW_ONLY",
)

FORBIDDEN_FOOTBALL_ACTIONS = (
    "EXECUTE",
    "PLACE_BET",
    "SUBMIT_ORDER",
    "AUTO_TRADE",
    "AUTO_BET",
    "PROVIDER_WRITE",
    "OWNER_APPROVED",
)

DATA_TIER_REQUIREMENTS = {
    0: {
        "tier_name": "no_reliable_football_impact_data",
        "capabilities": ["DATA_INSUFFICIENT"],
        "minimum_groups": [],
    },
    1: {
        "tier_name": "basic_game_team_context",
        "capabilities": ["team_context_limited", "unit_context_limited"],
        "minimum_groups": ["basic_game_context"],
    },
    2: {
        "tier_name": "play_drive_context",
        "capabilities": ["epa_success_rate", "drive_efficiency", "pace_game_script"],
        "minimum_groups": ["play_by_play", "drive_context"],
    },
    3: {
        "tier_name": "player_participation_role_context",
        "capabilities": ["snap_share", "route_target_carry_share", "role_adjusted_player_impact"],
        "minimum_groups": ["player_participation", "snap_share"],
    },
    4: {
        "tier_name": "tracking_context_optional",
        "capabilities": ["separation_pressure_coverage_shell_tracking", "expected_yac_ryoe"],
        "minimum_groups": ["tracking_context"],
    },
}


def normalize_football_sport(value: Any) -> str:
    raw = str(value or "americanfootball_nfl").strip().lower().replace("-", "_").replace(" ", "_")
    return FOOTBALL_SPORT_ALIASES.get(raw, raw if raw in SUPPORTED_FOOTBALL_SPORTS else "americanfootball_nfl")


def normalize_football_market(value: Any) -> str:
    raw = str(value or "spread").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "h2h": "moneyline",
        "ml": "moneyline",
        "spreads": "spread",
        "totals": "total",
        "passing": "player_passing_prop",
        "rushing": "player_rushing_prop",
        "receiving": "player_receiving_prop",
        "td": "anytime_td",
        "anytime_touchdown": "anytime_td",
        "interception": "interceptions",
        "int": "interceptions",
        "1h_spread": "first_half_spread",
        "1h_total": "first_half_total",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_FOOTBALL_MARKET_TYPES else raw)


def normalize_role(value: Any) -> str:
    raw = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "QB1": "QB",
        "QUARTERBACK": "QB",
        "RUNNING_BACK": "RB",
        "HALFBACK": "RB",
        "WIDE_RECEIVER": "WR",
        "TIGHT_END": "TE",
        "OFFENSIVE_LINE": "OL",
        "OT": "OL",
        "OG": "OL",
        "C": "OL",
        "CENTER": "OL",
        "DEFENSIVE_LINE": "DL",
        "DE": "EDGE",
        "OLB_EDGE": "EDGE",
        "LINEBACKER": "LB",
        "CORNER": "CB",
        "CORNERBACK": "CB",
        "SAFETY": "S",
        "PK": "K",
        "KICKER": "K",
        "PUNTER": "P",
        "OFFENSE": "TEAM_OFFENSE",
        "DEFENSE": "TEAM_DEFENSE",
        "ST": "SPECIAL_TEAMS",
    }
    role = aliases.get(raw, raw)
    return role if role in SUPPORTED_FOOTBALL_ROLES else "UNKNOWN"


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
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "active", "available", "healthy", "probable"}


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


def football_safety_flags() -> dict[str, Any]:
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
        }
    )
    return flags


def finalize_football_response(payload: dict[str, Any], *, source_payload: Any = None) -> dict[str, Any]:
    safe = redact_sensitive(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(football_safety_flags())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        safe.update(football_safety_flags())
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    return safe
