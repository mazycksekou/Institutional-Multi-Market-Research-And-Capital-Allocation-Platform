from __future__ import annotations

import math
from typing import Any, Iterable

from src.security.secret_safety import redact_sensitive, secret_safety_fields
from src.security.policy import detect_execution_authority_violations, locked_safety_flags


SUPPORTED_TENNIS_SPORTS = ("tennis", "atp", "wta")

SUPPORTED_TENNIS_MARKETS = (
    "moneyline",
    "match_winner",
    "set_handicap",
    "game_handicap",
    "total_games",
    "total_sets",
    "correct_score",
    "set_betting",
    "first_set_winner",
    "first_set_total_games",
    "first_set_handicap",
    "first_set_correct_score",
    "player_to_win_a_set",
    "player_to_win_2_0",
    "player_to_win_2_1",
    "player_to_win_3_0",
    "player_to_win_3_1",
    "player_to_win_3_2",
    "match_tiebreak_yes_no",
    "first_set_tiebreak_yes_no",
    "aces",
    "double_faults",
    "first_serve_percentage",
    "first_serve_points_won",
    "second_serve_points_won",
    "service_games_won",
    "return_games_won",
    "break_points_created",
    "break_points_converted",
    "break_points_saved",
    "total_points_won",
    "games_won",
    "sets_won",
)

SUPPORTED_TENNIS_CONTEXTS = (
    "SERVE",
    "RETURN",
    "SURFACE",
    "FORMAT",
    "TIEBREAK",
    "PRESSURE",
    "FATIGUE",
    "INJURY_RETIREMENT",
    "CONDITIONS",
    "MATCHUP",
    "UNKNOWN",
)

MATCH_MARKETS = {"moneyline", "match_winner"}
HANDICAP_MARKETS = {"set_handicap", "game_handicap", "first_set_handicap"}
TOTAL_MARKETS = {"total_games", "total_sets", "first_set_total_games"}
CORRECT_SCORE_MARKETS = {"correct_score", "first_set_correct_score", "player_to_win_2_0", "player_to_win_2_1", "player_to_win_3_0", "player_to_win_3_1", "player_to_win_3_2"}
SET_MARKETS = {"set_betting", "first_set_winner", "first_set_total_games", "first_set_handicap", "first_set_correct_score", "player_to_win_a_set", "sets_won"}
TIEBREAK_MARKETS = {"match_tiebreak_yes_no", "first_set_tiebreak_yes_no"}
PLAYER_PROP_MARKETS = {
    "aces",
    "double_faults",
    "first_serve_percentage",
    "first_serve_points_won",
    "second_serve_points_won",
    "service_games_won",
    "return_games_won",
    "break_points_created",
    "break_points_converted",
    "break_points_saved",
    "total_points_won",
    "games_won",
    "sets_won",
}

ALLOWED_TENNIS_REVIEW_STATUSES = (
    "DATA_INSUFFICIENT",
    "CALIBRATION_ONLY",
    "WATCHLIST_REVIEW",
    "ACTIVE_REVIEW",
    "NO_BET",
    "MARKET_REVIEW_ONLY",
    "PLAYER_PROP_REVIEW_ONLY",
    "SERVE_RETURN_REVIEW_ONLY",
    "SURFACE_MATCHUP_REVIEW_ONLY",
    "TIEBREAK_REVIEW_ONLY",
    "INJURY_RETIREMENT_REVIEW_ONLY",
)

FORBIDDEN_TENNIS_ACTIONS = (
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
    0: {"tier_name": "no_reliable_tennis_impact_data", "capabilities": ["DATA_INSUFFICIENT"]},
    1: {"tier_name": "basic_player_match_context", "capabilities": ["limited_player_match_context", "low_confidence_review_only"]},
    2: {"tier_name": "serve_return_summary_context", "capabilities": ["limited_serve_return_diagnostics", "totals_handicap_tiebreak_relevance"]},
    3: {"tier_name": "surface_point_pressure_context", "capabilities": ["surface_matchup", "format_relevance", "set_game_market_review", "player_props"]},
    4: {"tier_name": "tracking_shot_pattern_conditions_context", "capabilities": ["tracking_optional", "shot_pattern_optional", "richer_tactical_diagnostics"]},
}


def normalize_tennis_sport(value: Any) -> str:
    raw = str(value or "tennis").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "tennis_atp": "atp",
        "mens_tennis": "atp",
        "men_tennis": "atp",
        "tennis_wta": "wta",
        "womens_tennis": "wta",
        "women_tennis": "wta",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in SUPPORTED_TENNIS_SPORTS else "tennis"


def normalize_tennis_market(value: Any) -> str:
    raw = str(value or "moneyline").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "winner": "match_winner",
        "match": "match_winner",
        "ml": "moneyline",
        "spread": "game_handicap",
        "games_spread": "game_handicap",
        "sets_spread": "set_handicap",
        "games_total": "total_games",
        "sets_total": "total_sets",
        "tb": "match_tiebreak_yes_no",
        "tiebreak": "match_tiebreak_yes_no",
        "first_set_tiebreak": "first_set_tiebreak_yes_no",
        "dfs": "double_faults",
        "break_points": "break_points_created",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in SUPPORTED_TENNIS_MARKETS else normalized


def normalize_tennis_context(value: Any) -> str:
    raw = str(value or "UNKNOWN").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "SERVE_RETURN": "SERVE",
        "RET": "RETURN",
        "TB": "TIEBREAK",
        "INJURY": "INJURY_RETIREMENT",
        "RETIREMENT": "INJURY_RETIREMENT",
        "WEATHER": "CONDITIONS",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in SUPPORTED_TENNIS_CONTEXTS else "UNKNOWN"


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
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "confirmed", "active", "healthy", "indoor", "outdoor"}


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


def avg_prefixed(row: dict[str, Any], base_name: str) -> float | None:
    values = [
        safe_float(row.get(base_name)),
        safe_float(row.get(f"player_a_{base_name}")),
        safe_float(row.get(f"player_b_{base_name}")),
    ]
    numbers = [value for value in values if value is not None]
    return sum(numbers) / len(numbers) if numbers else None


def diff_prefixed(row: dict[str, Any], base_name: str) -> float | None:
    a = safe_float(row.get(f"player_a_{base_name}"))
    b = safe_float(row.get(f"player_b_{base_name}"))
    if a is None or b is None:
        return None
    return a - b


def tennis_safety_fields() -> dict[str, Any]:
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


def finalize_tennis_response(payload: dict[str, Any], *, source_payload: Any = None) -> dict[str, Any]:
    safe = redact_sensitive(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(tennis_safety_fields())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        safe.update(tennis_safety_fields())
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    safe["compact_response"] = True
    return safe
