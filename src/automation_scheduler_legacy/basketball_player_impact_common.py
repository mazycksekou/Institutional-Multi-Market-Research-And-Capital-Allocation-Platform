from __future__ import annotations

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


SUPPORTED_BASKETBALL_SPORTS = (
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaaw",
)

BASKETBALL_SPORT_ALIASES = {
    "nba": "basketball_nba",
    "basketball_nba": "basketball_nba",
    "wnba": "basketball_wnba",
    "basketball_wnba": "basketball_wnba",
    "ncaab": "basketball_ncaab",
    "mens_college_basketball": "basketball_ncaab",
    "basketball_ncaab": "basketball_ncaab",
    "ncaaw": "basketball_ncaaw",
    "ncaawb": "basketball_ncaaw",
    "womens_college_basketball": "basketball_ncaaw",
    "basketball_ncaaw": "basketball_ncaaw",
    "basketball_ncaawb": "basketball_ncaaw",
}

SPORT_CONTRACTS: dict[str, dict[str, Any]] = {
    "basketball_nba": {
        "league": "NBA",
        "sport_contract_id": "basketball_nba_player_impact_2026",
        "calibration_bucket_prefix": "basketball_nba.player_impact",
        "contract_context": "nba_cba_contract_awards_bonus_minutes",
        "screenshot_analysis_parity_key": "basketball_nba",
    },
    "basketball_wnba": {
        "league": "WNBA",
        "sport_contract_id": "basketball_wnba_player_impact_2026",
        "calibration_bucket_prefix": "basketball_wnba.player_impact",
        "contract_context": "wnba_contract_playoff_awards_minutes",
        "screenshot_analysis_parity_key": "basketball_wnba",
    },
    "basketball_ncaab": {
        "league": "NCAAB",
        "sport_contract_id": "basketball_ncaab_player_impact_2026",
        "calibration_bucket_prefix": "basketball_ncaab.player_impact",
        "contract_context": "mens_college_nil_portal_seeding_role",
        "screenshot_analysis_parity_key": "basketball_ncaab",
    },
    "basketball_ncaaw": {
        "league": "NCAAW",
        "sport_contract_id": "basketball_ncaaw_player_impact_2026",
        "calibration_bucket_prefix": "basketball_ncaaw.player_impact",
        "legacy_sport_alias": "basketball_ncaawb",
        "contract_context": "womens_college_nil_portal_seeding_role",
        "screenshot_analysis_parity_key": "basketball_ncaawb",
    },
}


def normalize_basketball_sport(value: Any, league: Any = None) -> str:
    raw = str(value or league or "basketball_nba").strip().lower().replace("-", "_").replace(" ", "_")
    return BASKETBALL_SPORT_ALIASES.get(raw, raw if raw in SUPPORTED_BASKETBALL_SPORTS else "basketball_nba")


def sport_contract(sport: str) -> dict[str, Any]:
    return dict(SPORT_CONTRACTS.get(normalize_basketball_sport(sport), SPORT_CONTRACTS["basketball_nba"]))


def safe_flags(*, red_team_only: bool = False) -> dict[str, Any]:
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
            "sportsbook_bet_execution_enabled": False,
        }
    )
    if red_team_only:
        flags["red_team_only"] = True
    return flags


def _sensitive_key_for_basketball_output(key: Any) -> bool:
    lower = str(key or "").strip().lower()
    if lower in {
        "secrets_included",
        "secrets_detected",
        "source_secret_like_content_redacted",
        "redacted_payload_contains_secret",
        "auth_header_exposed",
        "signature_exposed",
        "redaction_applied",
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


def redact_basketball_output(payload: Any, *, list_limit: int = 100) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            lower = str(key).strip().lower()
            if lower in RAW_PAYLOAD_KEYS:
                out[str(key)] = OMITTED
            elif _sensitive_key_for_basketball_output(key):
                out[str(key)] = REDACTED
            else:
                out[str(key)] = redact_basketball_output(value, list_limit=list_limit)
        return out
    if isinstance(payload, list):
        return [redact_basketball_output(value, list_limit=list_limit) for value in payload[: max(1, int(list_limit or 100))]]
    if isinstance(payload, str) and looks_like_secret_value(payload):
        return redact_string(payload)
    return payload


def finalize_safe_response(payload: dict[str, Any], *, source_payload: Any = None, red_team_only: bool = False) -> dict[str, Any]:
    safe = redact_basketball_output(payload)
    if not isinstance(safe, dict):
        safe = {"payload": safe}
    safe.update(safe_flags(red_team_only=red_team_only))
    violations = detect_execution_authority_violations(safe)
    if violations:
        safe["execution_authority_violations_blocked"] = violations
        for key, value in safe_flags(red_team_only=red_team_only).items():
            safe[key] = value
    safe.update(secret_safety_fields(source_payload=source_payload, redacted_payload=safe))
    safe["raw_payload_included"] = False
    safe["raw_payload_exposed"] = False
    safe["secrets_included"] = False
    return safe


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if out != out:
        return default
    return out


def clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    number = safe_float(value, low)
    if number is None:
        number = low
    return max(low, min(high, float(number)))


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "active", "out", "probable", "questionable"}


def present_fields(row: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [field for field in fields if row.get(field) not in (None, "", [])]


def missing_fields(row: dict[str, Any], fields: Iterable[str]) -> list[str]:
    return [field for field in fields if row.get(field) in (None, "", [])]


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


def percent_score(value: Any, *, already_score_ok: bool = True) -> float | None:
    number = safe_float(value)
    if number is None:
        return None
    if already_score_ok and 0.0 <= number <= 100.0:
        return clamp(number)
    if 0.0 <= number <= 1.0:
        return clamp(number * 100.0)
    return clamp(number)


def confidence_from_sample(sample_size: Any, *, full_sample: float = 500.0, floor: float = 20.0, cap: float = 95.0) -> float:
    sample = safe_float(sample_size, 0.0) or 0.0
    return clamp(floor + min(sample / max(full_sample, 1.0), 1.0) * (cap - floor))


def compact_list(values: Iterable[Any], limit: int = 20) -> list[Any]:
    out = []
    for value in values:
        if value in (None, "", []):
            continue
        if value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out
