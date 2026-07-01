from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from src.services.scheduler_config import sanitize_filename, utc_now_iso


LOCAL_SPORTS_HISTORY_SCHEMA_VERSION = "local_sports_history_audit_v1"

SPORT_MODULES = {
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaaw",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "baseball_mlb",
    "icehockey_nhl",
    "soccer",
    "tennis",
    "ufc_mma",
    "boxing",
    "golf",
}

ALLOWED_BLOCKED_REASONS = {
    "available",
    "no_records_found",
    "missing_event_id",
    "missing_event_date",
    "missing_participants",
    "missing_scores_or_results",
    "unsupported_shape",
    "raw_payload_risk",
    "secret_risk",
    "not_sports_history",
    "unreadable_file",
    "malformed_json",
    "insufficient_fields",
}

RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
}
SECRET_FIELD_MARKERS = (
    "api_key",
    "api_secret",
    "secret",
    "token",
    "password",
    "auth_header",
    "authorization",
    "credential",
    "signature",
    "private_key",
)
SKIP_PATH_MARKERS = (
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "tokens",
    "private_key",
    "api_key",
)
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
SUPPORTED_SUFFIXES = {".json", ".jsonl", ".ndjson"}
RECORD_LIST_KEYS = (
    "items",
    "records",
    "rows",
    "games",
    "events",
    "normalized_records",
    "compact_records",
    "matches",
    "fixtures",
    "schedule",
    "results",
    "normalized_sample_records",
    "sample_records",
    "data",
)
PLACEHOLDER_VALUES = {"", "n/a", "na", "none", "null", "unknown", "tbd", "placeholder"}
PREVIEW_ROW_LIMIT = 250

MODULE_KEYWORDS = {
    "basketball_nba": ("basketball_nba", " nba ", "/nba", "\\nba", "league:nba"),
    "basketball_wnba": ("basketball_wnba", " wnba ", "/wnba", "\\wnba", "league:wnba"),
    "basketball_ncaab": ("basketball_ncaab", "ncaab", "college basketball", "mens basketball"),
    "basketball_ncaaw": ("basketball_ncaaw", "ncaaw", "womens basketball"),
    "americanfootball_nfl": ("americanfootball_nfl", " nfl ", "/nfl", "\\nfl", "league:nfl"),
    "americanfootball_ncaaf": ("americanfootball_ncaaf", "ncaaf", "collegefootball", "college football", "cfbd"),
    "baseball_mlb": ("baseball_mlb", " mlb ", "/mlb", "\\mlb", "baseball", "league:mlb"),
    "icehockey_nhl": ("icehockey_nhl", " nhl ", "/nhl", "\\nhl", "hockey"),
    "soccer": ("soccer", "football_soccer", "premier league", "epl", "fifa", "uefa"),
    "tennis": ("tennis", " atp ", " wta ", "/atp", "\\atp", "/wta", "\\wta"),
    "ufc_mma": ("ufc_mma", " ufc ", "sport:ufc", "league:ufc", "/ufc", "\\ufc", " mma ", "sport:mma", "mixed martial"),
    "boxing": ("boxing", " boxer ", "fight_card"),
    "golf": ("golf", " pga ", " lpga ", "masters", "tournament"),
}

EVENT_ID_KEYS = ("event_id", "game_id", "match_id", "fixture_id", "bout_id", "fight_id", "tournament_id", "id")
EVENT_DATE_KEYS = (
    "event_date",
    "start_date",
    "game_date",
    "match_date",
    "fixture_date",
    "scheduled_date",
    "date",
    "start_time",
    "commence_time",
    "scheduled_at",
    "event_time",
)
HOME_KEYS = ("home_participant", "home_team", "home", "home_name", "team", "fighter_a", "player_a", "golfer")
AWAY_KEYS = ("away_participant", "away_team", "away", "away_name", "opponent", "fighter_b", "player_b", "field")
HOME_SCORE_KEYS = ("home_score", "home_points", "home_runs", "home_goals", "home_sets", "player_a_score", "fighter_a_score")
AWAY_SCORE_KEYS = ("away_score", "away_points", "away_runs", "away_goals", "away_sets", "player_b_score", "fighter_b_score")
FINAL_RESULT_KEYS = ("final_result", "result", "game_result", "match_result", "winner", "outcome")
MARKET_PRICE_KEYS = (
    "market_price_or_odds",
    "implied_probability",
    "market_implied_probability",
    "odds",
    "price",
    "moneyline",
    "spread",
    "total",
    "best_odds",
    "closing_odds",
)
EXPLICIT_OUTCOME_KEYS = ("explicit_outcome", "settlement_result", "final_outcome")
PARENT_CONTEXT_KEYS = ("module", "sport", "league", "competition", "provider", "provider_id", "source_id", "season", "week")

CANONICAL_ALIAS_GROUPS = {
    "event_id": EVENT_ID_KEYS,
    "event_date": EVENT_DATE_KEYS,
    "home_participant": HOME_KEYS,
    "away_participant": AWAY_KEYS,
    "home_score": HOME_SCORE_KEYS,
    "away_score": AWAY_SCORE_KEYS,
    "final_result": FINAL_RESULT_KEYS + ("home_win", "away_win"),
    "market_price_or_odds": MARKET_PRICE_KEYS,
    "explicit_outcome": EXPLICIT_OUTCOME_KEYS,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _real_value(value: Any) -> bool:
    if value in (None, [], {}):
        return False
    if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_VALUES:
        return False
    return True


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _safe_number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_value(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and _real_value(row.get(key)):
            return _safe_scalar(row.get(key))
    return None


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return ""


def _safe_record_slice(row: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in row.items():
        lower_key = str(key).lower()
        if lower_key in RAW_PAYLOAD_KEYS or any(marker in lower_key for marker in SECRET_FIELD_MARKERS):
            continue
        scalar = _safe_scalar(value)
        if scalar is not None:
            safe[str(key)] = scalar
    return safe


def _secret_key_is_status(lower_key: str) -> bool:
    return (
        lower_key.startswith("missing_")
        or lower_key.endswith("_configured")
        or lower_key.endswith("_present")
        or lower_key.startswith("requires_")
        or lower_key in {"credential_status", "approval_status"}
    )


def _secret_value_risky(lower_key: str, value: Any) -> bool:
    if _secret_key_is_status(lower_key):
        return False
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return False
    if isinstance(value, str):
        text = value.strip().lower()
        if text in PLACEHOLDER_VALUES or text in {"false", "true", "configured", "missing", "not_configured", "[redacted]", "redacted"}:
            return False
        return True
    return True


def _has_raw_payload_risk(value: Any, *, depth: int = 0) -> bool:
    if depth > 6:
        return False
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            if lower_key in RAW_PAYLOAD_KEYS and _real_value(item):
                return True
            if _has_raw_payload_risk(item, depth=depth + 1):
                return True
    elif isinstance(value, list):
        return any(_has_raw_payload_risk(item, depth=depth + 1) for item in value[:100])
    return False


def _has_secret_risk(value: Any, *, depth: int = 0) -> bool:
    if depth > 6:
        return False
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            if any(marker in lower_key for marker in SECRET_FIELD_MARKERS) and _secret_value_risky(lower_key, item):
                return True
            if _has_secret_risk(item, depth=depth + 1):
                return True
    elif isinstance(value, list):
        return any(_has_secret_risk(item, depth=depth + 1) for item in value[:100])
    return False


def _diagnostics_template() -> dict[str, Counter[str]]:
    return {
        "alias_mapping_hits": Counter(),
        "nested_container_hits": Counter(),
        "fields_present_counts": Counter(),
    }


def _record_alias_hit(counters: dict[str, Counter[str]] | None, alias: str, canonical: str) -> None:
    if counters is None:
        return
    counters["alias_mapping_hits"][f"{alias}->{canonical}"] += 1


def _record_field_present(counters: dict[str, Counter[str]] | None, canonical: str, value: Any) -> None:
    if counters is not None and _real_value(value):
        counters["fields_present_counts"][canonical] += 1


def _should_skip_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    if any(part in SKIP_DIRS for part in parts):
        return True
    if "local_sports_history" in parts:
        return True
    name = path.name.lower()
    if name == ".env" or name.startswith(".env."):
        return True
    return any(marker in part for part in parts for marker in SKIP_PATH_MARKERS)


def _default_scan_roots(base_data_dir: str | Path | None = None) -> list[Path]:
    base = resolve_base_data_dir(base_data_dir)
    repo = _repo_root()
    candidates = [
        base,
        base / "data_sources",
        base / "data_sources" / "adapters",
        base / "review_queue",
        base / "paper_ledger",
        base / "outcomes",
        base / "automation",
        repo / "tests" / "fixtures",
        repo / "docs",
    ]
    roots: list[Path] = []
    seen: set[Path] = set()
    for root in candidates:
        if not root.exists():
            continue
        resolved = root.resolve()
        if any(resolved == existing or resolved.is_relative_to(existing) for existing in seen):
            continue
        seen.add(resolved)
        roots.append(resolved)
    return roots


def _iter_scan_files(scan_roots: list[str | Path]) -> tuple[list[Path], int]:
    files: list[Path] = []
    skipped = 0
    seen: set[Path] = set()
    for rootish in scan_roots:
        root = Path(rootish).expanduser().resolve()
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else root.rglob("*")
        for path in candidates:
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            if _should_skip_path(path):
                skipped += 1
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(resolved)
    return sorted(files), skipped


def _read_json_records(path: Path) -> tuple[Any | None, str | None]:
    try:
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            rows: list[Any] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
            return rows, None
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError:
        return None, "malformed_json"
    except UnicodeDecodeError:
        return None, "unreadable_file"
    except OSError:
        return None, "unreadable_file"


def _looks_like_record(row: dict[str, Any]) -> bool:
    keys = set(row)
    interesting = set(EVENT_ID_KEYS + EVENT_DATE_KEYS + HOME_KEYS + AWAY_KEYS + HOME_SCORE_KEYS + AWAY_SCORE_KEYS + FINAL_RESULT_KEYS)
    interesting.update({"sport", "league", "module", "event_name", "event_title", "market_type"})
    return bool(keys & interesting)


def _parent_context(payload: dict[str, Any], inherited_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = dict(inherited_context or {})
    safe = _safe_record_slice(payload)
    for key in PARENT_CONTEXT_KEYS:
        if key in safe and _real_value(safe.get(key)):
            context[key] = safe[key]
    return context


def _merge_context(row: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    if not context:
        return row
    merged = dict(row)
    for key, value in context.items():
        if key not in merged and _real_value(value):
            merged[key] = value
    return merged


def _extract_records(
    payload: Any,
    *,
    depth: int = 0,
    counters: dict[str, Counter[str]] | None = None,
    inherited_context: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    if depth > 4:
        return [], "unsupported_shape"
    if isinstance(payload, list):
        rows = [_merge_context(row, inherited_context) for row in payload if isinstance(row, dict)]
        return rows, None if rows or not payload else "no_records_found"
    if not isinstance(payload, dict):
        return [], "unsupported_shape"
    context = _parent_context(payload, inherited_context)
    records: list[dict[str, Any]] = []
    for key in RECORD_LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            rows = [_merge_context(row, context) for row in value if isinstance(row, dict)]
            if rows and counters is not None:
                counters["nested_container_hits"][key] += 1
            records.extend(rows)
        elif isinstance(value, dict):
            if counters is not None:
                counters["nested_container_hits"][key] += 1
            nested, _ = _extract_records(value, depth=depth + 1, counters=counters, inherited_context=context)
            records.extend(nested)
    if records:
        return records, None
    if _looks_like_record(payload):
        return [_merge_context(payload, context)], None
    return [], "no_records_found" if any(key in payload for key in RECORD_LIST_KEYS) else "unsupported_shape"


def _path_for_text(path: Path) -> str:
    text = str(path).lower().replace("\\", "/")
    return f" {text} "


def _module_guess(path: Path, row: dict[str, Any]) -> str | None:
    safe = _safe_record_slice(row)
    module_value = str(safe.get("module") or "").strip()
    if module_value in SPORT_MODULES:
        return module_value
    text_bits = [
        _path_for_text(path),
        f" sport:{_safe_text(safe.get('sport')).lower()} ",
        f" league:{_safe_text(safe.get('league')).lower()} ",
        f" competition:{_safe_text(safe.get('competition')).lower()} ",
        f" source:{_safe_text(safe.get('source')).lower()} ",
        f" provider:{_safe_text(safe.get('provider')).lower()} ",
    ]
    text = " ".join(text_bits)
    for module, keywords in MODULE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return module
    if any(_real_value(safe.get(key)) for key in HOME_KEYS) and any(_real_value(safe.get(key)) for key in AWAY_KEYS):
        return "unknown_sports"
    return None


def _split_event_name(row: dict[str, Any]) -> tuple[str | None, str | None]:
    text = _safe_text(row.get("event_name") or row.get("event_title") or row.get("matchup") or row.get("name")).strip()
    for marker in (" vs. ", " vs ", " v. ", " v ", " @ "):
        if marker in text:
            left, right = text.split(marker, 1)
            left = left.strip()
            right = right.strip()
            if left and right:
                return left, right
    return None, None


def _first_alias_value(
    row: dict[str, Any],
    keys: tuple[str, ...],
    canonical: str,
    counters: dict[str, Counter[str]] | None,
) -> Any:
    for key in keys:
        if key in row and _real_value(row.get(key)):
            _record_alias_hit(counters, key, canonical)
            return _safe_scalar(row.get(key))
    return None


def _explicit_home_away_result(
    row: dict[str, Any],
    home: Any,
    away: Any,
    counters: dict[str, Counter[str]] | None,
) -> tuple[Any, Any]:
    home_win = row.get("home_win")
    away_win = row.get("away_win")
    if home_win is True:
        _record_alias_hit(counters, "home_win", "final_result")
        return "home_win", home
    if away_win is True:
        _record_alias_hit(counters, "away_win", "final_result")
        return "away_win", away
    return None, None


def _normalize_preview_row(
    path: Path,
    row: dict[str, Any],
    *,
    counters: dict[str, Counter[str]] | None = None,
) -> dict[str, Any]:
    safe = _safe_record_slice(row)
    module = _module_guess(path, safe) or "unknown"
    home = _first_alias_value(safe, HOME_KEYS, "home_participant", counters)
    away = _first_alias_value(safe, AWAY_KEYS, "away_participant", counters)
    if not home or not away:
        parsed_home, parsed_away = _split_event_name(safe)
        if parsed_home and not home:
            _record_alias_hit(counters, "event_name", "home_participant")
            home = parsed_home
        if parsed_away and not away:
            _record_alias_hit(counters, "event_name", "away_participant")
            away = parsed_away
    home_score = _first_alias_value(safe, HOME_SCORE_KEYS, "home_score", counters)
    away_score = _first_alias_value(safe, AWAY_SCORE_KEYS, "away_score", counters)
    home_n = _safe_number(home_score)
    away_n = _safe_number(away_score)
    final_margin = None
    total_score = None
    winner = _first_alias_value(safe, ("winner", "winning_team", "winning_participant"), "winner", counters)
    if home_n is not None and away_n is not None:
        final_margin = home_n - away_n
        total_score = home_n + away_n
        if winner is None:
            if home_n > away_n:
                winner = home
            elif away_n > home_n:
                winner = away
            else:
                winner = "draw"
    final_result = _first_alias_value(safe, FINAL_RESULT_KEYS, "final_result", counters)
    explicit_result, explicit_winner = _explicit_home_away_result(safe, home, away, counters)
    final_result = final_result or explicit_result
    winner = winner or explicit_winner
    event_id = _first_alias_value(safe, EVENT_ID_KEYS, "event_id", counters)
    event_date = _first_alias_value(safe, EVENT_DATE_KEYS, "event_date", counters)
    has_participants = _real_value(home) and _real_value(away)
    has_scores_or_result = (home_n is not None and away_n is not None) or _real_value(final_result) or _real_value(winner)
    if module not in SPORT_MODULES:
        blocked_reason = "unsupported_shape"
    elif not _real_value(event_id):
        blocked_reason = "missing_event_id"
    elif not _real_value(event_date):
        blocked_reason = "missing_event_date"
    elif not has_participants:
        blocked_reason = "missing_participants"
    elif not has_scores_or_result:
        blocked_reason = "missing_scores_or_results"
    else:
        blocked_reason = "available"
    market_price_or_odds = _first_alias_value(safe, MARKET_PRICE_KEYS, "market_price_or_odds", counters)
    explicit_outcome = _first_alias_value(safe, EXPLICIT_OUTCOME_KEYS, "explicit_outcome", counters)
    for canonical in CANONICAL_ALIAS_GROUPS:
        _record_field_present(counters, canonical, {
            "event_id": event_id,
            "event_date": event_date,
            "home_participant": home,
            "away_participant": away,
            "home_score": home_score,
            "away_score": away_score,
            "final_result": final_result,
            "market_price_or_odds": market_price_or_odds,
            "explicit_outcome": explicit_outcome,
        }.get(canonical))
    return {
        "module": module,
        "event_id": event_id,
        "source_path": str(path),
        "event_date": event_date,
        "home_participant": home,
        "away_participant": away,
        "neutral_site": _first_value(safe, ("neutral_site", "neutral")),
        "home_score": home_score,
        "away_score": away_score,
        "final_result": final_result,
        "winner": winner,
        "final_margin": final_margin,
        "total_score": total_score,
        "market_price_or_odds": market_price_or_odds,
        "explicit_outcome": explicit_outcome,
        "normalization_status": "available" if blocked_reason == "available" else "blocked",
        "blocked_reason": blocked_reason,
        "raw_payload_included": False,
    }


def _file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "unknown"


def _file_report(
    path: Path,
    *,
    base: Path,
    counters: dict[str, Counter[str]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload, read_error = _read_json_records(path)
    rel = _relative_path(path, base)
    if read_error:
        return (
            {
                "path": rel,
                "file_type": _file_type(path),
                "module_guess": None,
                "records_seen": 0,
                "records_with_event_id": 0,
                "records_with_event_date": 0,
                "records_with_home_away": 0,
                "records_with_scores": 0,
                "records_with_final_result": 0,
                "records_with_market_price_or_odds": 0,
                "records_with_explicit_outcome": 0,
                "raw_payload_included": False,
                "secrets_included": False,
                "usable_for_tier0_preview": False,
                "blocked_reason": read_error,
            },
            [],
        )
    if _has_raw_payload_risk(payload):
        return (_blocked_file_report(path, base=base, reason="raw_payload_risk"), [])
    if _has_secret_risk(payload):
        return (_blocked_file_report(path, base=base, reason="secret_risk"), [])
    records, shape_error = _extract_records(payload, counters=counters)
    if not records:
        return (_blocked_file_report(path, base=base, reason=shape_error or "no_records_found"), [])

    preview_rows = [_normalize_preview_row(path, row, counters=counters) for row in records if isinstance(row, dict)]
    sport_rows = [row for row in preview_rows if row["module"] in SPORT_MODULES or row["module"] == "unknown_sports"]
    if not sport_rows:
        return (_blocked_file_report(path, base=base, reason="not_sports_history", records_seen=len(records)), [])

    modules = sorted({row["module"] for row in sport_rows if row["module"] in SPORT_MODULES})
    usable_rows = [row for row in sport_rows if row["blocked_reason"] == "available"]
    reason = "available" if usable_rows else _first_blocked_reason(sport_rows)
    return (
        {
            "path": rel,
            "file_type": _file_type(path),
            "module_guess": modules[0] if len(modules) == 1 else ("multiple" if len(modules) > 1 else "unknown_sports"),
            "records_seen": len(records),
            "records_with_event_id": sum(1 for row in sport_rows if _real_value(row.get("event_id"))),
            "records_with_event_date": sum(1 for row in sport_rows if _real_value(row.get("event_date"))),
            "records_with_home_away": sum(1 for row in sport_rows if _real_value(row.get("home_participant")) and _real_value(row.get("away_participant"))),
            "records_with_scores": sum(1 for row in sport_rows if _safe_number(row.get("home_score")) is not None and _safe_number(row.get("away_score")) is not None),
            "records_with_final_result": sum(1 for row in sport_rows if _real_value(row.get("final_result")) or _real_value(row.get("winner"))),
            "records_with_market_price_or_odds": sum(1 for row in sport_rows if _real_value(row.get("market_price_or_odds"))),
            "records_with_explicit_outcome": sum(1 for row in sport_rows if _real_value(row.get("explicit_outcome"))),
            "raw_payload_included": False,
            "secrets_included": False,
            "usable_for_tier0_preview": bool(usable_rows),
            "blocked_reason": reason,
        },
        usable_rows,
    )


def _blocked_file_report(path: Path, *, base: Path, reason: str, records_seen: int = 0) -> dict[str, Any]:
    if reason not in ALLOWED_BLOCKED_REASONS:
        reason = "insufficient_fields"
    return {
        "path": _relative_path(path, base),
        "file_type": _file_type(path),
        "module_guess": None,
        "records_seen": records_seen,
        "records_with_event_id": 0,
        "records_with_event_date": 0,
        "records_with_home_away": 0,
        "records_with_scores": 0,
        "records_with_final_result": 0,
        "records_with_market_price_or_odds": 0,
        "records_with_explicit_outcome": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "usable_for_tier0_preview": False,
        "blocked_reason": reason,
    }


def _first_blocked_reason(rows: list[dict[str, Any]]) -> str:
    priority = [
        "missing_event_id",
        "missing_event_date",
        "missing_participants",
        "missing_scores_or_results",
        "unsupported_shape",
        "insufficient_fields",
    ]
    reasons = {str(row.get("blocked_reason")) for row in rows}
    for reason in priority:
        if reason in reasons:
            return reason
    return "insufficient_fields"


def _relative_path(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(_repo_root().resolve())).replace("\\", "/")
    except Exception:
        try:
            return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
        except Exception:
            return path.name


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    path = base / "local_sports_history"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rel_report_path(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build_local_sports_history_audit_report(
    *,
    base_data_dir: str | Path | None = None,
    scan_roots: list[str | Path] | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    roots = [Path(root).expanduser().resolve() for root in (scan_roots or _default_scan_roots(base))]
    files, skipped = _iter_scan_files(roots)
    counters = _diagnostics_template()
    file_reports: list[dict[str, Any]] = []
    preview_rows: list[dict[str, Any]] = []
    for path in files:
        report, rows = _file_report(path, base=base, counters=counters)
        file_reports.append(report)
        for row in rows:
            if len(preview_rows) < PREVIEW_ROW_LIMIT:
                preview_rows.append({**row, "source_path": _relative_path(Path(str(row["source_path"])), base)})

    usable_files = [row for row in file_reports if row.get("usable_for_tier0_preview")]
    modules_with_rows = sorted({row["module"] for row in preview_rows if row.get("module") in SPORT_MODULES})
    modules_still_blocked = sorted(SPORT_MODULES - set(modules_with_rows))
    reason_counts = Counter(str(row.get("blocked_reason")) for row in file_reports)
    top_missing_fields = _top_missing_fields(reason_counts)
    near_miss_examples = _near_miss_examples(file_reports)
    return {
        "ok": True,
        "status": "ok",
        "schema_version": LOCAL_SPORTS_HISTORY_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "runtime_data_dir": str(base),
        "scan_roots": [str(root) for root in roots],
        "files_scanned": len(files),
        "files_skipped_secret_like_path_count": skipped,
        "candidate_files_found": len(file_reports),
        "usable_tier0_preview_files": len(usable_files),
        "modules_with_preview_rows": modules_with_rows,
        "modules_still_blocked": modules_still_blocked,
        "top_missing_fields": top_missing_fields,
        "near_miss_file_count": sum(
            1
            for row in file_reports
            if row.get("blocked_reason") in {"missing_event_id", "missing_event_date", "missing_participants", "missing_scores_or_results"}
        ),
        "near_miss_examples_redacted": near_miss_examples,
        "fields_present_counts": dict(sorted(counters["fields_present_counts"].items())),
        "alias_mapping_hits": dict(sorted(counters["alias_mapping_hits"].items())),
        "nested_container_hits": dict(sorted(counters["nested_container_hits"].items())),
        "blocked_reason_counts": dict(sorted(reason_counts.items())),
        "candidate_files": file_reports,
        "preview_rows": preview_rows,
        "preview_rows_returned": len(preview_rows),
        "preview_row_limit": PREVIEW_ROW_LIMIT,
        "derived_feature_backfill_report_can_consume_preview_rows_later": True,
        "recommended_next_no_spend_action": _recommended_next_action(modules_with_rows, top_missing_fields),
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
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
        "storage_health": get_storage_health(),
    }


def _top_missing_fields(reason_counts: Counter[str]) -> list[dict[str, Any]]:
    mapping = {
        "missing_event_id": "event_id",
        "missing_event_date": "event_date",
        "missing_participants": "home_away_participants",
        "missing_scores_or_results": "scores_or_final_result",
        "insufficient_fields": "minimum_sports_history_fields",
        "unsupported_shape": "record_container_or_sports_aliases",
    }
    rows = [
        {"field": field, "count": count, "blocked_reason": reason}
        for reason, count in reason_counts.items()
        if count and (field := mapping.get(reason))
    ]
    return sorted(rows, key=lambda row: (-int(row["count"]), str(row["field"])))[:10]


def _near_miss_examples(file_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    near_miss_reasons = {"missing_event_id", "missing_event_date", "missing_participants", "missing_scores_or_results"}
    for row in file_reports:
        if row.get("blocked_reason") not in near_miss_reasons:
            continue
        examples.append(
            {
                "path": row.get("path"),
                "module_guess": row.get("module_guess"),
                "blocked_reason": row.get("blocked_reason"),
                "records_seen": row.get("records_seen"),
                "records_with_event_id": row.get("records_with_event_id"),
                "records_with_event_date": row.get("records_with_event_date"),
                "records_with_home_away": row.get("records_with_home_away"),
                "records_with_scores": row.get("records_with_scores"),
                "records_with_final_result": row.get("records_with_final_result"),
            }
        )
        if len(examples) >= 10:
            break
    return examples


def _recommended_next_action(modules_with_rows: list[str], top_missing_fields: list[dict[str, Any]]) -> str:
    if modules_with_rows:
        return "wire preview rows into derived_feature_backfill_report as a no-call local input"
    if top_missing_fields:
        field = top_missing_fields[0]["field"]
        return f"no-call audit existing files for missing {field} fields"
    return "add mocked schedule/result fixtures for each sport before local backfill integration"


def render_local_sports_history_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Local Sports History Audit",
        "",
        f"1. files_scanned: {report.get('files_scanned')}",
        f"2. candidate_files_found: {report.get('candidate_files_found')}",
        f"3. usable_tier0_preview_files: {report.get('usable_tier0_preview_files')}",
        f"4. modules_with_preview_rows: {', '.join(report.get('modules_with_preview_rows') or []) if report.get('modules_with_preview_rows') else 'none'}",
        f"5. modules_still_blocked: {', '.join(list(report.get('modules_still_blocked') or [])[:13]) if report.get('modules_still_blocked') else 'none'}",
        f"6. top_missing_fields: {json.dumps(report.get('top_missing_fields') or [], sort_keys=True)}",
        f"7. alias_mapping_hits: {json.dumps(report.get('alias_mapping_hits') or {}, sort_keys=True)}; nested_container_hits: {json.dumps(report.get('nested_container_hits') or {}, sort_keys=True)}",
        f"8. recommended_next_no_spend_action: {report.get('recommended_next_no_spend_action')}; safety provider_calls_attempted=0 provider_write=false execution_allowed=false raw_payload_included=false secrets_included=false",
        "",
    ]
    return "\n".join(lines)


def write_local_sports_history_audit_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    run_id = sanitize_filename(f"local_sports_history_{created.replace(':', '-')}_{uuid4().hex[:8]}")
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    paths = {
        "latest_json_path": _rel_report_path(latest_json, base_data_dir),
        "latest_markdown_path": _rel_report_path(latest_md, base_data_dir),
        "item_json_path": _rel_report_path(item_json, base_data_dir),
        "item_markdown_path": _rel_report_path(item_md, base_data_dir),
        "daily_json_path": _rel_report_path(daily_json, base_data_dir),
        "daily_markdown_path": _rel_report_path(daily_md, base_data_dir),
    }
    payload = {**report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_local_sports_history_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--scan-root", action="append", default=[])
    args = parser.parse_args(argv)
    report = build_local_sports_history_audit_report(scan_roots=args.scan_root or None)
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_local_sports_history_audit_report(report)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "status": report["status"],
                "files_scanned": report["files_scanned"],
                "candidate_files_found": report["candidate_files_found"],
                "usable_tier0_preview_files": report["usable_tier0_preview_files"],
                "modules_with_preview_rows": report["modules_with_preview_rows"],
                "latest_json_path": paths.get("latest_json_path"),
                "latest_markdown_path": paths.get("latest_markdown_path"),
                "provider_calls_attempted": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
