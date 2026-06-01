from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_storage_health, resolve_base_data_dir
from .data_source_registry import SPORT_REQUIRED_INPUTS, build_registry
from .source_quality_scoring import score_source

CFBD_API_BASE_URL = "https://api.collegefootballdata.com"
CFBD_API_KEY_ENV = "CFBD_API_KEY"
SOURCE_ID = "collegefootballdata"
PROVIDER_ID = "collegefootballdata"
MODULE = "americanfootball_ncaaf"
REPORT_RELATIVE_DIR = ("data_sources", "adapters", "ncaaf_cfbd")
DEFAULT_MAX_RECORDS = 5
MAX_RECORDS_HARD_CAP = 25

_SAFE_BOOL_KEY_FIELDS = {
    "api_key_configured",
    "missing_api_key",
    "requires_api_key",
    "key_is_configured",
}
_SAFE_LIST_KEY_FIELDS = {"join_keys", "env_var_names"}
_RAW_KEYS = {
    "provider_payload",
    "raw_payload",
    "raw_provider_payload",
    "raw_record",
    "raw_records",
    "external_payload",
    "source_payload",
    "response_body",
    "raw_body",
}
_SECRET_KEY_EXACT = {
    "api_key",
    "apikey",
    "authorization",
    "auth_header",
    "headers",
    "token",
    "secret",
    "password",
    "credential",
    "signature",
    "cfbd_api_key",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_id() -> str:
    return f"ncaaf_cfbd_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"


def _effective_max_records(max_records: int | None) -> int:
    try:
        requested = int(max_records if max_records is not None else DEFAULT_MAX_RECORDS)
    except (TypeError, ValueError):
        requested = DEFAULT_MAX_RECORDS
    return max(1, min(requested, MAX_RECORDS_HARD_CAP))


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _first(raw: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in raw and _present(raw.get(name)):
            return raw.get(name)
    return None


def _safe_str(value: Any, *, max_len: int = 240) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_len]


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return float(int(value))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _append_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


def _compact_number(value: Any) -> int | float | None:
    number = _safe_float(value)
    if number is None:
        return None
    if number.is_integer():
        return int(number)
    return round(number, 6)


def _safe_report_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _sanitize_for_report(value)
    if isinstance(value, list):
        return [_safe_report_value(item) for item in value[:100]]
    if isinstance(value, tuple):
        return [_safe_report_value(item) for item in list(value)[:100]]
    if isinstance(value, str):
        return value[:1000]
    return value


def _unsafe_key(key: str) -> bool:
    lowered = str(key).lower()
    if lowered in _SAFE_BOOL_KEY_FIELDS or lowered in _SAFE_LIST_KEY_FIELDS:
        return False
    if lowered in _RAW_KEYS or lowered in _SECRET_KEY_EXACT:
        return True
    if lowered.endswith("_api_key") or lowered.endswith("_token") or lowered.endswith("_secret"):
        return True
    if "authorization" in lowered or "credential" in lowered or "signature" in lowered:
        return True
    return False


def _sanitize_for_report(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).startswith("_") or _unsafe_key(str(key)):
            continue
        safe[key] = _safe_report_value(value)
    safe["raw_payload_included"] = False
    safe["secrets_included"] = False
    return safe


def _safe_source_config(source: dict[str, Any]) -> dict[str, Any]:
    mapping = dict(source.get("model_mapping") or {})
    return {
        "source_id": SOURCE_ID,
        "source_name": source.get("source_name") or "CollegeFootballData free-key candidate",
        "module": MODULE,
        "module_lane": MODULE,
        "provider_id": PROVIDER_ID,
        "source_access_type": source.get("source_access_type") or "free_key",
        "auth_type": source.get("auth_type") or "api_key",
        "env_var_name": CFBD_API_KEY_ENV,
        "requires_account": bool(source.get("requires_account", True)),
        "requires_api_key": True,
        "approval_status": source.get("approval_status") or "needs_review",
        "current_phase_allowed": bool(source.get("current_phase_allowed", False)),
        "verification_phase_allowed": True,
        "terms_review_required": bool(source.get("requires_terms_review", True)),
        "enabled": False,
        "adapter_status": "verification_only",
        "adapter_scope": "read_only_verification_only",
        "registry_adapter_status": source.get("adapter_status"),
        "coverage": dict(source.get("coverage") or {}),
        "freshness": dict(source.get("freshness") or {}),
        "limits": dict(source.get("limits") or {}),
        "legal_terms": dict(source.get("legal_terms") or {}),
        "model_mapping": {
            "model_inputs_supported": list(mapping.get("model_inputs_supported") or []),
            "join_keys": list(mapping.get("join_keys") or []),
            "outcome_fields_available": list(mapping.get("outcome_fields_available") or []),
            "historical_backfill_fields_available": list(mapping.get("historical_backfill_fields_available") or []),
        },
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def get_cfbd_config() -> dict[str, Any]:
    registry = build_registry(module=MODULE)
    source = {}
    for row in list(registry.get("sources") or []):
        if row.get("source_id") == SOURCE_ID:
            source = dict(row)
            break
    return _safe_source_config(source)


def get_cfbd_headers() -> dict[str, str]:
    api_key = os.getenv(CFBD_API_KEY_ENV, "").strip()
    if not api_key:
        return {"Accept": "application/json"}
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


def verify_cfbd_access_config() -> dict[str, Any]:
    config = get_cfbd_config()
    api_key_configured = bool(os.getenv(CFBD_API_KEY_ENV, "").strip())
    return {
        "ok": True,
        "status": "metadata_verified",
        **config,
        "api_key_configured": api_key_configured,
        "missing_api_key": not api_key_configured,
        "metadata_only_supported": True,
        "live_sample_supported": api_key_configured,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def fetch_cfbd_tiny_sample(
    season: int | None = None,
    week: int | None = None,
    max_records: int = DEFAULT_MAX_RECORDS,
    dry_run: bool = True,
) -> dict[str, Any]:
    max_records_effective = _effective_max_records(max_records)
    api_key = os.getenv(CFBD_API_KEY_ENV, "").strip()
    if not api_key:
        return {
            "ok": True,
            "status": "missing_api_key",
            "records": [],
            "records_received": 0,
            "max_records_effective": max_records_effective,
            "dry_run": bool(dry_run),
            "missing_api_key": True,
            "fetch_live_sample_performed": False,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    query = {
        "year": str(season or datetime.now(timezone.utc).year),
        "seasonType": "regular",
    }
    if week is not None:
        query["week"] = str(week)
    url = f"{CFBD_API_BASE_URL}/games?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(url, headers=get_cfbd_headers(), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": "http_error",
            "http_status": int(getattr(exc, "code", 0) or 0),
            "records": [],
            "records_received": 0,
            "max_records_effective": max_records_effective,
            "dry_run": bool(dry_run),
            "missing_api_key": False,
            "fetch_live_sample_performed": False,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": "network_error",
            "error_class": type(exc).__name__,
            "records": [],
            "records_received": 0,
            "max_records_effective": max_records_effective,
            "dry_run": bool(dry_run),
            "missing_api_key": False,
            "fetch_live_sample_performed": False,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = []
    if isinstance(parsed, dict):
        records = parsed.get("games") or parsed.get("data") or parsed.get("items") or []
    else:
        records = parsed
    if not isinstance(records, list):
        records = []
    records = [row for row in records if isinstance(row, dict)][:max_records_effective]
    return {
        "ok": True,
        "status": "sample_fetched",
        "records": records,
        "records_received": len(records),
        "max_records_effective": max_records_effective,
        "dry_run": bool(dry_run),
        "missing_api_key": False,
        "fetch_live_sample_performed": True,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def normalize_cfbd_game_record(raw_record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_record, dict):
        return {}
    game_id = _safe_str(_first(raw_record, "id", "game_id", "gameId"))
    season = _safe_int(_first(raw_record, "season", "year"))
    week = _safe_int(_first(raw_record, "week"))
    home_points = _safe_int(_first(raw_record, "home_points", "homePoints"))
    away_points = _safe_int(_first(raw_record, "away_points", "awayPoints"))
    completed = _safe_bool(_first(raw_record, "completed", "isCompleted"))
    outcome_fields: list[str] = []
    final_result: dict[str, Any] | None = None
    if home_points is not None and away_points is not None:
        winner = "home" if home_points > away_points else "away" if away_points > home_points else "tie"
        final_result = {
            "home_points": home_points,
            "away_points": away_points,
            "winner": winner,
            "margin": home_points - away_points,
        }
        outcome_fields.extend(["final_score", "home_points", "away_points", "winner"])

    join_keys: list[str] = []
    if game_id:
        join_keys.extend(["game_id", "event_id"])
    if season is not None:
        join_keys.append("season")
    if week is not None:
        join_keys.append("week")

    normalized = {
        "provider_record_type": "game",
        "source_id": SOURCE_ID,
        "provider_id": PROVIDER_ID,
        "game_id": game_id,
        "event_id": game_id,
        "season": season,
        "week": week,
        "season_type": _safe_str(_first(raw_record, "season_type", "seasonType")),
        "start_date": _safe_str(_first(raw_record, "start_date", "startDate", "startTime")),
        "completed": completed,
        "home_team": _safe_str(_first(raw_record, "home_team", "homeTeam")),
        "away_team": _safe_str(_first(raw_record, "away_team", "awayTeam")),
        "home_conference": _safe_str(_first(raw_record, "home_conference", "homeConference")),
        "away_conference": _safe_str(_first(raw_record, "away_conference", "awayConference")),
        "venue": _safe_str(_first(raw_record, "venue", "venueName")),
        "neutral_site": _safe_bool(_first(raw_record, "neutral_site", "neutralSite")),
        "home_points": home_points,
        "away_points": away_points,
        "final_result": final_result,
        "join_keys": join_keys,
        "outcome_fields_available": outcome_fields,
    }
    conferences = [value for value in (normalized["home_conference"], normalized["away_conference"]) if value]
    if conferences:
        normalized["conference"] = list(dict.fromkeys(conferences))
    return {key: value for key, value in normalized.items() if value is not None}


def normalize_cfbd_team_record(raw_record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_record, dict):
        return {}
    normalized = {
        "provider_record_type": "team",
        "source_id": SOURCE_ID,
        "provider_id": PROVIDER_ID,
        "team": _safe_str(_first(raw_record, "school", "team", "name")),
        "team_id": _safe_str(_first(raw_record, "id", "team_id", "teamId")),
        "abbreviation": _safe_str(_first(raw_record, "abbreviation", "abbr")),
        "mascot": _safe_str(_first(raw_record, "mascot")),
        "conference": _safe_str(_first(raw_record, "conference")),
        "division": _safe_str(_first(raw_record, "division")),
        "color": _safe_str(_first(raw_record, "color"), max_len=40),
        "alt_color": _safe_str(_first(raw_record, "alt_color", "altColor"), max_len=40),
    }
    return {key: value for key, value in normalized.items() if value is not None}


def normalize_cfbd_advanced_record(raw_record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_record, dict):
        return {}
    offense = raw_record.get("offense") if isinstance(raw_record.get("offense"), dict) else {}
    defense = raw_record.get("defense") if isinstance(raw_record.get("defense"), dict) else {}
    offensive_epa = _compact_number(_first(offense, "ppa", "epa", "epaPerPlay", "epa_per_play") or _first(raw_record, "offensive_epa_per_play", "offensiveEpaPerPlay"))
    defensive_epa = _compact_number(_first(defense, "ppa", "epa", "epaPerPlay", "epa_per_play") or _first(raw_record, "defensive_epa_per_play", "defensiveEpaPerPlay"))
    offensive_success = _compact_number(_first(offense, "successRate", "success_rate") or _first(raw_record, "offensive_success_rate"))
    defensive_success_allowed = _compact_number(_first(defense, "successRate", "success_rate") or _first(raw_record, "defensive_success_rate_allowed"))
    offensive_explosiveness = _compact_number(_first(offense, "explosiveness") or _first(raw_record, "offensive_explosiveness"))
    defensive_explosiveness_allowed = _compact_number(_first(defense, "explosiveness") or _first(raw_record, "defensive_explosiveness_allowed"))
    side = _safe_str(_first(raw_record, "side", "homeAway", "home_away"))
    side_key = str(side or "").lower().strip()

    normalized = {
        "provider_record_type": "advanced",
        "source_id": SOURCE_ID,
        "provider_id": PROVIDER_ID,
        "game_id": _safe_str(_first(raw_record, "game_id", "gameId", "id")),
        "event_id": _safe_str(_first(raw_record, "game_id", "gameId", "id")),
        "season": _safe_int(_first(raw_record, "season", "year")),
        "week": _safe_int(_first(raw_record, "week")),
        "team": _safe_str(_first(raw_record, "team", "school")),
        "opponent": _safe_str(_first(raw_record, "opponent")),
        "home_away": side,
        "offensive_epa_per_play": offensive_epa,
        "defensive_epa_per_play": defensive_epa,
        "offensive_success_rate": offensive_success,
        "defensive_success_rate_allowed": defensive_success_allowed,
        "offensive_explosiveness": offensive_explosiveness,
        "defensive_explosiveness_allowed": defensive_explosiveness_allowed,
    }
    if side_key in {"home", "away"}:
        prefix = side_key
        direct_fields = {
            f"{prefix}_offensive_epa_per_play": offensive_epa,
            f"{prefix}_defensive_epa_per_play": defensive_epa,
            f"{prefix}_success_rate": offensive_success,
            f"{prefix}_defensive_success_rate_allowed": defensive_success_allowed,
            f"{prefix}_explosiveness": offensive_explosiveness,
            f"{prefix}_explosiveness_allowed": defensive_explosiveness_allowed,
        }
        normalized.update({key: value for key, value in direct_fields.items() if value is not None})
    return {key: value for key, value in normalized.items() if value is not None}


def _contract_fields() -> tuple[list[str], list[str]]:
    from multi_sport_model_registry import (
        COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS,
        COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS,
    )

    return list(COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS), list(COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS)


def _record_has(records: list[dict[str, Any]], field: str) -> bool:
    return any(_present(row.get(field)) for row in records if isinstance(row, dict))


def map_cfbd_to_ncaaf_model_inputs(records: list[dict[str, Any]]) -> dict[str, Any]:
    records = [dict(row) for row in records if isinstance(row, dict)]
    required_core, optional_inputs = _contract_fields()
    covered: list[str] = []
    auxiliary_supported: list[str] = []
    join_keys: list[str] = []
    outcome_fields: list[str] = []
    backfill_fields: list[str] = []

    for field in required_core:
        if _record_has(records, field):
            _append_unique(covered, field)
    for field in optional_inputs:
        if _record_has(records, field):
            _append_unique(covered, field)
    for field in ("game_id", "event_id", "season", "week", "start_date", "venue", "home_points", "away_points", "final_result"):
        if _record_has(records, field):
            _append_unique(auxiliary_supported, field)
    for row in records:
        for key in list(row.get("join_keys") or []):
            _append_unique(join_keys, str(key))
        for key in list(row.get("outcome_fields_available") or []):
            _append_unique(outcome_fields, str(key))
    if _record_has(records, "final_result"):
        _append_unique(outcome_fields, "final_result")
        _append_unique(backfill_fields, "final_result")
    for field in ("game_id", "event_id", "season", "week", "start_date", "home_team", "away_team", "home_points", "away_points"):
        if _record_has(records, field):
            _append_unique(backfill_fields, field)
    if _record_has(records, "game_id"):
        _append_unique(join_keys, "game_id")
    if _record_has(records, "event_id"):
        _append_unique(join_keys, "event_id")
    if _record_has(records, "season"):
        _append_unique(join_keys, "season")
    if _record_has(records, "week"):
        _append_unique(join_keys, "week")

    missing_required = [field for field in required_core if field not in covered]
    missing_optional = [field for field in optional_inputs if field not in covered]
    coverage_score = round((len(covered) / len(required_core)) * 100, 2) if required_core else 0.0
    required_backfill = {"game_id", "season", "week", "home_team", "away_team", "final_result"}
    backfill_score = round((len(required_backfill.intersection(backfill_fields)) / len(required_backfill)) * 100, 2)
    calibration_readiness = 0.0
    if "game_id" in join_keys or "event_id" in join_keys:
        calibration_readiness += 20
    if {"season", "week"}.issubset(set(backfill_fields)):
        calibration_readiness += 15
    if outcome_fields:
        calibration_readiness += 35
    calibration_readiness += min(30, coverage_score * 0.3)

    return {
        "covered_model_inputs": covered,
        "model_inputs_supported": list(dict.fromkeys(covered + auxiliary_supported)),
        "missing_model_inputs": missing_required,
        "missing_required_inputs": missing_required,
        "missing_optional_inputs": missing_optional,
        "outcome_fields_available": outcome_fields,
        "historical_backfill_fields_available": backfill_fields,
        "backfill_fields_available": backfill_fields,
        "join_keys": join_keys,
        "coverage_score": coverage_score,
        "calibration_readiness_score": round(min(100.0, calibration_readiness), 2),
        "record_count": len(records),
    }


def score_cfbd_sample_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    records = [dict(row) for row in records if isinstance(row, dict)]
    mapping = map_cfbd_to_ncaaf_model_inputs(records)
    config = get_cfbd_config()
    source_for_score = {
        **config,
        "coverage": {
            **dict(config.get("coverage") or {}),
            "historical": bool(records),
            "live": bool(records),
            "schedules": bool(_record_has(records, "home_team") and _record_has(records, "away_team")),
            "team_stats": any(row.get("provider_record_type") == "advanced" for row in records),
            "final_results": bool(mapping["outcome_fields_available"]),
        },
        "model_mapping": {
            "model_inputs_supported": list(mapping["covered_model_inputs"]),
            "missing_model_inputs": list(mapping["missing_required_inputs"]),
            "join_keys": list(mapping["join_keys"]),
            "outcome_fields_available": list(mapping["outcome_fields_available"]),
            "historical_backfill_fields_available": list(mapping["historical_backfill_fields_available"]),
        },
    }
    required_core, _ = _contract_fields()
    quality = score_source(source_for_score, required_inputs=required_core)
    if not records:
        quality.update(
            {
                "source_reliability_score": min(int(quality.get("source_reliability_score") or 0), 45),
                "coverage_score": 0,
                "completeness_score": 0,
                "join_quality_score": 10,
                "model_input_fill_rate": 0,
                "historical_depth_score": 10,
                "outcome_availability_score": 10,
                "current_phase_usability_score": min(int(quality.get("current_phase_usability_score") or 0), 15),
                "calibration_value_score": min(int(quality.get("calibration_value_score") or 0), 15),
            }
        )
    else:
        fill_rate = int(round(float(mapping["coverage_score"])))
        quality.update(
            {
                "coverage_score": fill_rate,
                "model_input_fill_rate": fill_rate,
                "join_quality_score": 85 if {"game_id", "event_id"}.intersection(mapping["join_keys"]) else 25,
                "outcome_availability_score": 85 if mapping["outcome_fields_available"] else 20,
                "historical_depth_score": 70 if {"season", "week"}.issubset(set(mapping["historical_backfill_fields_available"])) else 30,
                "completeness_score": min(100, max(fill_rate, 35 if records else 0)),
            }
        )
    quality["calibration_readiness_score"] = float(mapping["calibration_readiness_score"])
    quality["live_sample_required"] = not bool(records)
    quality["metadata_only"] = not bool(records)
    return quality


def _report_root(base_data_dir: str | Path | None = None) -> Path:
    root = resolve_base_data_dir(base_data_dir)
    path = root
    for part in REPORT_RELATIVE_DIR:
        path = path / part
    path.mkdir(parents=True, exist_ok=True)
    return path


def _markdown_report(report: dict[str, Any]) -> str:
    quality = dict(report.get("quality_scores") or {})
    lines = [
        "# NCAAF CFBD Adapter Verification",
        "",
        f"- run_id: {report.get('run_id')}",
        f"- status: {report.get('adapter_status')}",
        f"- source_id: {report.get('source_id')}",
        f"- module: {report.get('module')}",
        f"- enabled: {str(bool(report.get('enabled'))).lower()}",
        f"- fetch_live_sample_requested: {str(bool(report.get('fetch_live_sample_requested'))).lower()}",
        f"- fetch_live_sample_performed: {str(bool(report.get('fetch_live_sample_performed'))).lower()}",
        f"- sample_records_received: {report.get('sample_records_received')}",
        f"- sample_records_normalized: {report.get('sample_records_normalized')}",
        f"- coverage_score: {report.get('coverage_score')}",
        f"- calibration_readiness_score: {quality.get('calibration_readiness_score')}",
        "- provider_write: false",
        "- execution_allowed: false",
        "- raw_payload_included: false",
        "- secrets_included: false",
    ]
    return "\n".join(lines) + "\n"


def write_cfbd_sample_report(report: dict[str, Any]) -> dict[str, Any]:
    safe = _sanitize_for_report(dict(report or {}))
    run_id = str(safe.get("run_id") or _run_id())
    safe["run_id"] = run_id
    created_at = safe.get("created_at") or _utc_now()
    safe["created_at"] = created_at
    day = str(created_at)[:10]
    root = _report_root(report.get("_base_data_dir") if isinstance(report, dict) else None)
    items = root / "items"
    daily = root / "daily"
    items.mkdir(parents=True, exist_ok=True)
    daily.mkdir(parents=True, exist_ok=True)

    latest_path = root / "latest.json"
    item_path = items / f"{run_id}.json"
    daily_json_path = daily / f"{day}.json"
    daily_markdown_path = daily / f"{day}.md"
    paths = {
        "latest_path": str(latest_path),
        "item_path": str(item_path),
        "daily_json_path": str(daily_json_path),
        "daily_markdown_path": str(daily_markdown_path),
    }
    safe["report_paths"] = dict(paths)
    encoded = json.dumps(safe, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    for path in (latest_path, item_path, daily_json_path):
        path.write_text(encoded, encoding="utf-8")
    daily_markdown_path.write_text(_markdown_report(safe), encoding="utf-8")
    return {
        **paths,
        "report_paths": paths,
        "storage_health": get_storage_health(),
        "raw_payload_included": False,
        "secrets_included": False,
    }


def verify_ncaaf_cfbd_adapter(
    *,
    dry_run: bool = True,
    season: int | None = None,
    week: int | None = None,
    max_records: int = DEFAULT_MAX_RECORDS,
    fetch_live_sample: bool = False,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    max_records_effective = _effective_max_records(max_records)
    config_status = verify_cfbd_access_config()
    raw_records: list[dict[str, Any]] = []
    fetch_status = "not_requested"
    fetch_performed = False
    fetch_ok = True
    if fetch_live_sample:
        sample = fetch_cfbd_tiny_sample(
            season=season,
            week=week,
            max_records=max_records_effective,
            dry_run=dry_run,
        )
        fetch_status = str(sample.get("status") or "unknown")
        fetch_performed = bool(sample.get("fetch_live_sample_performed", False))
        fetch_ok = bool(sample.get("ok", True))
        raw_records = list(sample.get("records") or [])

    normalized_records = [normalize_cfbd_game_record(row) for row in raw_records]
    normalized_records = [row for row in normalized_records if row]
    mapping = map_cfbd_to_ncaaf_model_inputs(normalized_records)
    quality = score_cfbd_sample_quality(normalized_records)
    missing_api_key = bool(config_status.get("missing_api_key", True))
    if fetch_live_sample and missing_api_key:
        adapter_status = "missing_api_key"
    elif fetch_live_sample and not fetch_ok:
        adapter_status = fetch_status
    elif fetch_performed:
        adapter_status = "live_sample_verified"
    else:
        adapter_status = "metadata_only_verified"

    report = {
        "ok": True if adapter_status in {"metadata_only_verified", "missing_api_key", "live_sample_verified"} else False,
        "status": adapter_status,
        "adapter_status": adapter_status,
        "run_id": _run_id(),
        "created_at": _utc_now(),
        "source_id": SOURCE_ID,
        "module": MODULE,
        "provider_id": PROVIDER_ID,
        "source_access_type": config_status.get("source_access_type"),
        "current_phase_allowed": bool(config_status.get("current_phase_allowed", False)),
        "verification_phase_allowed": True,
        "approval_status": config_status.get("approval_status"),
        "enabled": False,
        "dry_run": bool(dry_run),
        "season": season,
        "week": week,
        "max_records_requested": max_records,
        "max_records_effective": max_records_effective,
        "fetch_live_sample_requested": bool(fetch_live_sample),
        "fetch_live_sample_performed": fetch_performed,
        "missing_api_key": missing_api_key,
        "api_key_configured": bool(config_status.get("api_key_configured", False)),
        "sample_records_received": len(raw_records),
        "sample_records_normalized": len(normalized_records),
        "normalized_sample_records": normalized_records[:max_records_effective],
        "model_inputs_supported": mapping["model_inputs_supported"],
        "covered_model_inputs": mapping["covered_model_inputs"],
        "missing_model_inputs": mapping["missing_model_inputs"],
        "missing_required_inputs": mapping["missing_required_inputs"],
        "missing_optional_inputs": mapping["missing_optional_inputs"],
        "outcome_fields_available": mapping["outcome_fields_available"],
        "historical_backfill_fields_available": mapping["historical_backfill_fields_available"],
        "backfill_fields_available": mapping["backfill_fields_available"],
        "join_keys": mapping["join_keys"],
        "coverage_score": mapping["coverage_score"],
        "calibration_readiness_score": mapping["calibration_readiness_score"],
        "quality_scores": quality,
        "terms_review_required": bool(config_status.get("terms_review_required", True)),
        "live_sample_required": bool(quality.get("live_sample_required", True)),
        "metadata_only_supported": True,
        "production_ingestion_enabled": False,
        "bulk_ingest_enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "_base_data_dir": base_data_dir,
    }
    report.update(write_cfbd_sample_report(report))
    report.pop("_base_data_dir", None)
    return report
