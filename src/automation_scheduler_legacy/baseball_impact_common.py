from __future__ import annotations

import math
from typing import Any, Iterable

from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import detect_execution_authority_violations, locked_safety_flags


SUPPORTED_BASEBALL_SPORTS = ("baseball_mlb",)

SUPPORTED_BASEBALL_MARKETS = (
    "moneyline",
    "runline",
    "total",
    "team_total",
    "first_five_moneyline",
    "first_five_runline",
    "first_five_total",
    "pitcher_strikeouts",
    "pitcher_outs_recorded",
    "pitcher_earned_runs",
    "pitcher_hits_allowed",
    "pitcher_walks_allowed",
    "pitcher_home_runs_allowed",
    "batter_hits",
    "batter_total_bases",
    "batter_home_runs",
    "batter_rbis",
    "batter_runs",
    "batter_stolen_bases",
    "batter_walks",
    "batter_strikeouts",
)

SUPPORTED_BASEBALL_ROLES = (
    "STARTING_PITCHER",
    "RELIEF_PITCHER",
    "CLOSER",
    "CATCHER",
    "BATTER",
    "BASE_RUNNER",
    "INFIELDER",
    "OUTFIELDER",
    "TEAM_OFFENSE",
    "TEAM_DEFENSE",
    "BULLPEN",
    "UNKNOWN",
)

TEAM_MARKETS = {
    "moneyline",
    "runline",
    "total",
    "team_total",
    "first_five_moneyline",
    "first_five_runline",
    "first_five_total",
}
PITCHER_PROP_MARKETS = {
    "pitcher_strikeouts",
    "pitcher_outs_recorded",
    "pitcher_earned_runs",
    "pitcher_hits_allowed",
    "pitcher_walks_allowed",
    "pitcher_home_runs_allowed",
}
BATTER_PROP_MARKETS = {
    "batter_hits",
    "batter_total_bases",
    "batter_home_runs",
    "batter_rbis",
    "batter_runs",
    "batter_stolen_bases",
    "batter_walks",
    "batter_strikeouts",
}
PLAYER_PROP_MARKETS = PITCHER_PROP_MARKETS | BATTER_PROP_MARKETS
FIRST_FIVE_MARKETS = {"first_five_moneyline", "first_five_runline", "first_five_total"}

ALLOWED_BASEBALL_REVIEW_STATUSES = (
    "DATA_INSUFFICIENT",
    "CALIBRATION_ONLY",
    "WATCHLIST_REVIEW",
    "ACTIVE_REVIEW",
    "NO_BET",
    "MARKET_REVIEW_ONLY",
    "PLAYER_PROP_REVIEW_ONLY",
    "TEAM_MARKET_REVIEW_ONLY",
    "PITCHER_PROP_REVIEW_ONLY",
    "BATTER_PROP_REVIEW_ONLY",
)

FORBIDDEN_BASEBALL_ACTIONS = (
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
    0: {"tier_name": "no_reliable_baseball_impact_data", "capabilities": ["DATA_INSUFFICIENT"]},
    1: {"tier_name": "basic_team_game_context", "capabilities": ["limited_team_context", "low_confidence_review_only"]},
    2: {"tier_name": "box_score_game_log_split_context", "capabilities": ["limited_pitcher_batter_props", "platoon_diagnostics"]},
    3: {"tier_name": "pitch_pa_batted_ball_context", "capabilities": ["run_value", "contact_quality", "pitch_mix_matchup"]},
    4: {"tier_name": "advanced_tracking_defense_catcher_umpire_context", "capabilities": ["tracking_optional", "richer_modifiers"]},
}


def normalize_baseball_sport(value: Any) -> str:
    raw = str(value or "baseball_mlb").strip().lower().replace("-", "_").replace(" ", "_")
    return "baseball_mlb" if raw in {"mlb", "baseball", "baseball_mlb", "major_league_baseball"} else "baseball_mlb"


def normalize_baseball_market(value: Any) -> str:
    raw = str(value or "moneyline").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "h2h": "moneyline",
        "ml": "moneyline",
        "spread": "runline",
        "first_5_moneyline": "first_five_moneyline",
        "first_5_runline": "first_five_runline",
        "first_5_total": "first_five_total",
        "pitcher_ks": "pitcher_strikeouts",
        "strikeouts": "pitcher_strikeouts",
        "outs": "pitcher_outs_recorded",
        "hits": "batter_hits",
        "total_bases": "batter_total_bases",
        "home_runs": "batter_home_runs",
        "stolen_bases": "batter_stolen_bases",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_BASEBALL_MARKETS else raw)


def normalize_baseball_role(value: Any) -> str:
    raw = str(value or "UNKNOWN").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "SP": "STARTING_PITCHER",
        "STARTER": "STARTING_PITCHER",
        "PITCHER": "STARTING_PITCHER",
        "RP": "RELIEF_PITCHER",
        "RELIEVER": "RELIEF_PITCHER",
        "CL": "CLOSER",
        "HITTER": "BATTER",
        "RUNNER": "BASE_RUNNER",
        "OF": "OUTFIELDER",
        "IF": "INFIELDER",
        "OFFENSE": "TEAM_OFFENSE",
        "DEFENSE": "TEAM_DEFENSE",
    }
    role = aliases.get(raw, raw)
    return role if role in SUPPORTED_BASEBALL_ROLES else "UNKNOWN"


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
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "confirmed", "active", "healthy", "closed"}


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


def confidence_from_sample(sample_size: Any, *, full_sample: float = 300.0, floor: float = 20.0, cap: float = 92.0) -> float:
    sample = safe_float(sample_size, 0.0) or 0.0
    return clamp(floor + min(sample / max(full_sample, 1.0), 1.0) * (cap - floor))


def baseball_safety_fields() -> dict[str, Any]:
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


def finalize_baseball_response(payload: dict[str, Any], *, source_payload: Any = None) -> dict[str, Any]:
    safe = redact_sensitive(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(baseball_safety_fields())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        safe.update(baseball_safety_fields())
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    safe["compact_response"] = True
    return safe
