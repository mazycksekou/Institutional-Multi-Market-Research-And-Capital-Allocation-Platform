from __future__ import annotations

import math
from typing import Any, Iterable

from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import detect_execution_authority_violations, locked_safety_flags


SUPPORTED_COMBAT_SPORTS = ("combat_sports", "ufc", "mma", "ufc_mma", "boxing")

SUPPORTED_COMBAT_MARKETS = (
    "moneyline",
    "fight_winner",
    "method_of_victory",
    "ko_tko",
    "submission",
    "decision",
    "draw",
    "fight_goes_distance",
    "fight_does_not_go_distance",
    "over_rounds",
    "under_rounds",
    "exact_round",
    "round_group",
    "winning_method_round",
    "inside_distance",
    "points_decision",
    "split_decision",
    "unanimous_decision",
    "fighter_significant_strikes",
    "fighter_total_strikes",
    "fighter_takedowns",
    "fighter_takedown_attempts",
    "fighter_submission_attempts",
    "fighter_control_time",
    "fighter_knockdowns",
    "fighter_round_1_finish",
    "fighter_round_2_finish",
    "fighter_round_3_finish",
    "fighter_round_4_5_finish",
    "performance_bonus_style_prop",
    "fighter_jabs_landed",
    "fighter_power_punches_landed",
    "fighter_total_punches_landed",
    "knockdowns",
    "stoppage",
)

SUPPORTED_COMBAT_PHASES = (
    "OPEN_SPACE_STRIKING",
    "POCKET_BOXING",
    "KICKING_RANGE",
    "CLINCH",
    "CAGE_WRESTLING",
    "TAKEDOWN_ENTRY",
    "TOP_CONTROL",
    "BOTTOM_SURVIVAL",
    "SCRAMBLE",
    "SUBMISSION_SEQUENCE",
    "GROUND_AND_POUND",
    "BOXING_OUTSIDE",
    "BOXING_INSIDE",
    "UNKNOWN",
)

MONEYLINE_MARKETS = {"moneyline", "fight_winner"}
METHOD_MARKETS = {
    "method_of_victory",
    "ko_tko",
    "submission",
    "decision",
    "inside_distance",
    "points_decision",
    "split_decision",
    "unanimous_decision",
    "stoppage",
}
ROUND_TOTAL_MARKETS = {
    "fight_goes_distance",
    "fight_does_not_go_distance",
    "over_rounds",
    "under_rounds",
    "exact_round",
    "round_group",
    "winning_method_round",
    "fighter_round_1_finish",
    "fighter_round_2_finish",
    "fighter_round_3_finish",
    "fighter_round_4_5_finish",
}
FIGHTER_PROP_MARKETS = {
    "fighter_significant_strikes",
    "fighter_total_strikes",
    "fighter_takedowns",
    "fighter_takedown_attempts",
    "fighter_submission_attempts",
    "fighter_control_time",
    "fighter_knockdowns",
    "performance_bonus_style_prop",
}
BOXING_PROP_MARKETS = {
    "fighter_jabs_landed",
    "fighter_power_punches_landed",
    "fighter_total_punches_landed",
    "knockdowns",
}

ALLOWED_COMBAT_REVIEW_STATUSES = (
    "DATA_INSUFFICIENT",
    "CALIBRATION_ONLY",
    "WATCHLIST_REVIEW",
    "ACTIVE_REVIEW",
    "NO_BET",
    "MARKET_REVIEW_ONLY",
    "FIGHTER_PROP_REVIEW_ONLY",
    "METHOD_MARKET_REVIEW_ONLY",
    "ROUND_TOTAL_REVIEW_ONLY",
    "DAMAGE_DURABILITY_REVIEW_ONLY",
    "PHASE_CONTROL_REVIEW_ONLY",
    "JUDGING_REFEREE_REVIEW_ONLY",
)

FORBIDDEN_COMBAT_ACTIONS = (
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
    0: {"tier_name": "no_reliable_combat_sports_impact_data", "capabilities": ["DATA_INSUFFICIENT"]},
    1: {"tier_name": "basic_fighter_bout_context", "capabilities": ["limited_bout_context", "low_confidence_review_only"]},
    2: {"tier_name": "summary_striking_grappling_finish_data", "capabilities": ["limited_striking_grappling", "method_total_prop_relevance"]},
    3: {"tier_name": "round_level_opponent_adjusted_phase_data", "capabilities": ["phase_control", "round_total_method_review", "cardio_durability_review"]},
    4: {"tier_name": "film_medical_camp_judging_microdata_optional", "capabilities": ["film_tracking_optional", "richer_tactical_and_context_review"]},
}


def normalize_combat_sport(value: Any) -> str:
    raw = str(value or "combat_sports").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "mixed_martial_arts": "mma",
        "ufc/mma": "ufc_mma",
        "ufc_mixed_martial_arts": "ufc_mma",
        "mma_mixed_martial_arts": "mma",
        "combat": "combat_sports",
        "combat_sport": "combat_sports",
    }
    sport = aliases.get(raw, raw)
    return sport if sport in SUPPORTED_COMBAT_SPORTS else "combat_sports"


def normalize_combat_market(value: Any) -> str:
    raw = str(value or "moneyline").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "h2h": "moneyline",
        "winner": "fight_winner",
        "fight_winner_2way": "fight_winner",
        "mov": "method_of_victory",
        "method": "method_of_victory",
        "ko": "ko_tko",
        "tko": "ko_tko",
        "sub": "submission",
        "goes_distance": "fight_goes_distance",
        "does_not_go_distance": "fight_does_not_go_distance",
        "inside_the_distance": "inside_distance",
        "points": "points_decision",
        "sig_strikes": "fighter_significant_strikes",
        "total_strikes": "fighter_total_strikes",
        "takedowns": "fighter_takedowns",
        "submission_attempts": "fighter_submission_attempts",
        "control_time": "fighter_control_time",
        "jabs": "fighter_jabs_landed",
        "power_punches": "fighter_power_punches_landed",
        "total_punches": "fighter_total_punches_landed",
    }
    market = aliases.get(raw, raw)
    return market if market in SUPPORTED_COMBAT_MARKETS else market


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
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "confirmed", "supplied", "active"}


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


def weighted_average(items: Iterable[tuple[Any, float]]) -> float | None:
    total = 0.0
    weight_total = 0.0
    for value, weight in items:
        number = safe_float(value)
        if number is None or weight <= 0:
            continue
        total += number * weight
        weight_total += weight
    if weight_total <= 0:
        return None
    return clamp(total / weight_total)


def compact_list(values: Iterable[Any] | None, limit: int = 20) -> list[Any]:
    if not values:
        return []
    out: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if value in (None, "", [], {}):
            continue
        key = str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
        if len(out) >= limit:
            break
    return out


def present_fields(row: dict[str, Any] | None, fields: Iterable[str]) -> list[str]:
    if not isinstance(row, dict):
        return []
    return [field for field in fields if row.get(field) not in (None, "", [], {})]


def missing_fields(row: dict[str, Any] | None, fields: Iterable[str]) -> list[str]:
    if not isinstance(row, dict):
        return list(fields)
    return [field for field in fields if row.get(field) in (None, "", [], {})]


def get_metric(row: dict[str, Any], base: str, *, prefix: str = "fighter_a") -> Any:
    prefixed = f"{prefix}_{base}"
    if prefixed in row:
        return row.get(prefixed)
    return row.get(base)


def score_metric(row: dict[str, Any], base: str, *, low: float, high: float, prefix: str = "fighter_a", inverse: bool = False) -> float | None:
    return score_from_range(get_metric(row, base, prefix=prefix), low=low, high=high, inverse=inverse)


def diff_score(row: dict[str, Any], base: str, *, low: float, high: float, inverse_b: bool = False) -> float | None:
    a = safe_float(get_metric(row, base, prefix="fighter_a"))
    b = safe_float(get_metric(row, base, prefix="fighter_b"))
    if a is None and b is None:
        return None
    if a is not None and b is not None:
        diff = a - b
        if inverse_b:
            diff = b - a
        return clamp(50.0 + (diff / (high - low)) * 50.0)
    return score_from_range(a, low=low, high=high)


def _redact_combat_payload(payload: Any) -> Any:
    return redact_sensitive(payload)


def combat_safety_fields() -> dict[str, Any]:
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
            "dry_run": True,
            "simulation_only": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
            "actual_crypto_swaps_submitted": 0,
            "kalshi_order_execution_enabled": False,
            "sportsbook_bet_execution_enabled": False,
            "broker_order_execution_enabled": False,
            "crypto_trade_execution_enabled": False,
            "stock_trade_execution_enabled": False,
            "raw_payload_included": False,
            "raw_payload_exposed": False,
            "secrets_included": False,
            "compact_response": True,
        }
    )
    return flags


def finalize_combat_response(payload: dict[str, Any], *, source_payload: Any | None = None) -> dict[str, Any]:
    safe = _redact_combat_payload(payload)
    if not isinstance(safe, dict):
        safe = {"value": safe}
    safe.update(combat_safety_fields())
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    safe["provider_write"] = False
    safe["execution_allowed"] = False
    safe["live_execution_enabled"] = False
    safe["auto_execution"] = False
    return safe

