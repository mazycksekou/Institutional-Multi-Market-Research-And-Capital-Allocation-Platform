from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from typing import Any

import httpx

from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from src.providers.validation import validate_provider_payload
from src.providers.policy.secret_policy import credential_status_from_env, redact_http_diagnostic, redact_mapping
from .scheduler_config import utc_now_iso
from src.core.math_utils import (
    american_to_decimal,
    american_to_implied_probability,
    decimal_to_implied_probability,
)

PROVIDER_ID = "sharp_sportsbook"
PROVIDER_TYPE = "sportsbook_odds"
SCHEMA_VERSION = "automation_scheduler.v1.sharp_sportsbook.v1"
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_BASE_URL = "https://api.sharp.app"
DEFAULT_EVENTS_PATH = "v1/events"
DEFAULT_ODDS_PATH = "v1/odds"
DEFAULT_PLAYER_PROPS_PATH = "v1/player-props"
DEFAULT_SPORTS_PATH = "v1/sports"

# Canonical odds connector metadata for delete-proof redirection.
ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "automation_scheduler.sharp_sportsbook_adapter"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_path(path_value: str) -> str:
    segments = [segment for segment in str(path_value or "").strip().split("/") if segment]
    if not segments:
        return "/"
    return "/" + "/".join(segments)


def _blocker_from_http_status(http_status: int) -> str:
    if http_status == 404:
        return "http_404"
    if http_status == 401:
        return "http_401"
    if http_status == 403:
        return "http_403"
    if http_status == 429:
        return "http_429"
    if 500 <= int(http_status) <= 599:
        return "http_5xx"
    return f"http_{int(http_status)}"


def _american_to_decimal(american_odds: float | int | None) -> float | None:
    try:
        return round(american_to_decimal(float(american_odds)), 6)
    except (TypeError, ValueError):
        return None


def _implied_probability_from_american(american_odds: float | int | None) -> float | None:
    try:
        return round(american_to_implied_probability(float(american_odds)), 8)
    except (TypeError, ValueError):
        return None


def _implied_probability_from_decimal(decimal_odds: float | int | None) -> float | None:
    try:
        return round(decimal_to_implied_probability(float(decimal_odds)), 8)
    except (TypeError, ValueError):
        return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_american_int(value: Any) -> int | None:
    parsed = _to_float(value)
    if parsed is None or parsed == 0:
        return None
    return int(round(parsed))


def _to_decimal(value: Any) -> float | None:
    parsed = _to_float(value)
    if parsed is None or parsed <= 1.0:
        return None
    return round(parsed, 6)


class SharpSportsbookAdapter:
    def __init__(self, contract: dict[str, Any] | None = None):
        self.contract = dict(contract or {})
        self.provider_id = PROVIDER_ID
        self.provider_name = "Sharp Sportsbook"
        self.provider_type = PROVIDER_TYPE
        self.base_url = (os.getenv("SHARP_API_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
        self.base_url_present = bool(os.getenv("SHARP_API_BASE_URL", "").strip())
        self.timeout_seconds = max(1.0, _safe_float(os.getenv("SHARP_API_TIMEOUT_SECONDS"), DEFAULT_TIMEOUT_SECONDS))
        self.provider_enabled_env_set = os.getenv("SHARP_PROVIDER_ENABLED") is not None
        self.live_reads_env_set = os.getenv("SHARP_LIVE_READS_ENABLED") is not None
        self.provider_enabled_from_env = _env_bool("SHARP_PROVIDER_ENABLED", default=False) if self.provider_enabled_env_set else None
        self.live_reads_enabled = _env_bool("SHARP_LIVE_READS_ENABLED", default=bool(self.contract.get("live_calls_enabled", False)))
        self.path_config = {
            "events_path": os.getenv("SHARP_EVENTS_PATH", DEFAULT_EVENTS_PATH),
            "odds_path": os.getenv("SHARP_ODDS_PATH", DEFAULT_ODDS_PATH),
            "player_props_path": os.getenv("SHARP_PLAYER_PROPS_PATH", DEFAULT_PLAYER_PROPS_PATH),
            "sports_path": os.getenv("SHARP_SPORTS_PATH", DEFAULT_SPORTS_PATH),
        }
        self.read_only_mode = True

    def _resolve_url_and_diag(self, path_name: str) -> tuple[str, dict[str, Any]]:
        resolved_path = _normalize_path(self.path_config.get(path_name, ""))
        split = urlsplit(self.base_url or DEFAULT_BASE_URL)
        base_path = _normalize_path(split.path) if split.path else ""
        if base_path in {"", "/"}:
            joined_path = resolved_path
        else:
            joined_path = _normalize_path(f"{base_path}/{resolved_path}")
        safe_url = urlunsplit((split.scheme or "https", split.netloc, joined_path, "", ""))
        diagnostic = {
            "base_url_present": bool(self.base_url_present),
            "path_name": path_name,
            "resolved_path": resolved_path,
            "url_host": split.netloc,
            "url_path": joined_path,
            "query_redacted": True,
            "secret_redacted": True,
        }
        return safe_url, diagnostic

    def build_sharp_url(self, path_name: str) -> dict[str, Any]:
        _, diagnostic = self._resolve_url_and_diag(path_name)
        return diagnostic

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "supports_polling": True,
            "supports_streaming": False,
            "required_credentials": ["SHARP_API_KEY"],
            "supported_markets": ["moneyline", "spread", "total", "player_props"],
            "read_only_mode": True,
            "enabled": bool(self.contract.get("enabled", False)),
            "live_calls_enabled": bool(self.contract.get("live_calls_enabled", False)),
            "provider_live_calls_enabled": False,
            "dry_run": True,
        }

    def validate_config(self) -> dict[str, Any]:
        blockers: list[str] = []
        credential = credential_status_from_env(self.provider_id)
        provider_enabled = (
            bool(self.provider_enabled_from_env)
            if self.provider_enabled_from_env is not None
            else bool(self.contract.get("enabled", False))
        )
        live_call_contract_enabled = bool(self.contract.get("live_calls_enabled", False))
        dry_run = bool(self.contract.get("dry_run", True))

        if not provider_enabled:
            blockers.append("provider_disabled")
        if not self.live_reads_enabled or not live_call_contract_enabled:
            blockers.append("live_reads_disabled")
        if credential["status"] != "ok":
            blockers.append("blocked_missing_credentials")
        if not self.read_only_mode:
            blockers.append("read_only_required")

        ready = len(blockers) == 0
        return {
            "ok": ready,
            "status": "read_only_ready" if ready else "blocked",
            "blockers": blockers,
            "credential_status": credential["status"],
            "live_reads_enabled": self.live_reads_enabled,
            "provider_enabled": provider_enabled,
            "live_calls_enabled": bool(self.live_reads_enabled and live_call_contract_enabled),
            "provider_live_calls_enabled": bool(ready),
            "dry_run": dry_run,
            "read_only_mode": self.read_only_mode,
        }

    def health_check(self) -> dict[str, Any]:
        cfg = self.validate_config()
        return {
            "ok": True,
            "status": cfg["status"],
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "dry_run": cfg["dry_run"],
            "provider_enabled": bool(cfg["provider_enabled"]),
            "live_calls_enabled": bool(cfg["live_calls_enabled"]),
            "credential_status": cfg["credential_status"],
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "blockers": cfg["blockers"][:10],
            "timestamp": utc_now_iso(),
        }

    def _build_headers(self) -> dict[str, str]:
        api_key = os.getenv("SHARP_API_KEY", "").strip()
        return {"X-API-Key": api_key, "Accept": "application/json"}

    def _safe_get(self, path_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        cfg = self.validate_config()
        if "blocked_missing_credentials" in cfg["blockers"]:
            return {"ok": False, "status": "blocked_missing_credentials", "records": [], "errors": ["missing_credentials"]}
        if "live_reads_disabled" in cfg["blockers"]:
            return {"ok": True, "status": "live_reads_disabled", "records": [], "errors": []}
        if "provider_disabled" in cfg["blockers"]:
            return {"ok": True, "status": "provider_disabled", "records": [], "errors": []}
        if not cfg["ok"]:
            return {"ok": True, "status": "blocked", "records": [], "errors": cfg["blockers"]}

        url, diagnostic = self._resolve_url_and_diag(path_name)
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, headers=self._build_headers(), params=params or {})
            if response.status_code >= 400:
                blocker = _blocker_from_http_status(int(response.status_code))
                return {
                    "ok": False,
                    "status": "provider_error",
                    "http_status": int(response.status_code),
                    "blocker": blocker,
                    "diagnostic": redact_http_diagnostic({**diagnostic, "method": "GET"}),
                    "records": [],
                    "errors": [blocker],
                }
            try:
                body = response.json()
            except Exception:
                return {
                    "ok": False,
                    "status": "provider_error",
                    "http_status": int(response.status_code),
                    "blocker": "malformed_provider_response",
                    "diagnostic": redact_http_diagnostic({**diagnostic, "method": "GET"}),
                    "records": [],
                    "errors": ["malformed_provider_response"],
                }
        except httpx.TimeoutException:
            return {
                "ok": False,
                "status": "provider_error",
                "http_status": None,
                "blocker": "provider_timeout",
                "diagnostic": redact_http_diagnostic({**diagnostic, "method": "GET"}),
                "records": [],
                "errors": ["provider_timeout"],
            }
        except Exception:
            return {
                "ok": False,
                "status": "provider_error",
                "http_status": None,
                "blocker": "provider_unreachable",
                "diagnostic": redact_http_diagnostic({**diagnostic, "method": "GET"}),
                "records": [],
                "errors": ["provider_unreachable"],
            }

        records = self._extract_records(body)
        return {"ok": True, "status": "ok", "records": records, "errors": []}

    def fetch_events(self) -> dict[str, Any]:
        return self._safe_get("events_path")

    def fetch_odds(self) -> dict[str, Any]:
        return self._safe_get("odds_path")

    def fetch_player_props(self) -> dict[str, Any]:
        return self._safe_get("player_props_path")

    def fetch_sports(self) -> dict[str, Any]:
        return self._safe_get("sports_path")

    def normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        odds = payload.get("odds")
        ts = payload.get("timestamp") or payload.get("updated_at") or utc_now_iso()
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "received_at": utc_now_iso(),
            "event_id": payload.get("event_id") or payload.get("id"),
            "sport": payload.get("sport"),
            "league": payload.get("league"),
            "event_name": payload.get("event_name") or payload.get("name"),
            "start_time": payload.get("start_time"),
            "book": payload.get("book") or payload.get("sportsbook") or "sharp",
            "market": payload.get("market"),
            "selection": payload.get("selection"),
            "line": payload.get("line"),
            "odds": odds,
            "decimal_odds": _american_to_decimal(odds),
            "implied_probability": _implied_probability_from_american(odds),
            "timestamp": ts,
            "source_payload_redacted": redact_mapping(payload),
            "schema_version": SCHEMA_VERSION,
        }

    def _extract_records(self, body: Any) -> list[Any]:
        if isinstance(body, list):
            return body
        if not isinstance(body, dict):
            return []
        for key in ("data", "events", "eventBoards", "items", "results"):
            candidate = body.get(key)
            if isinstance(candidate, list):
                return candidate
        return []

    def _extract_nested_rows(self, row: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
        market_keys = ("markets", "market", "marketGroups", "lines")
        book_keys = ("books", "bookmakers", "sportsbooks", "prices")
        outcome_keys = ("outcomes", "selections", "participants", "runners", "options")

        markets: list[dict[str, Any]] = []
        for key in market_keys:
            value = row.get(key)
            if isinstance(value, list):
                markets = [item for item in value if isinstance(item, dict)]
                if markets:
                    break
        if not markets:
            markets = [_as_dict(_coalesce(row.get("market"), row))]

        counts = {"events": 1, "markets": len(markets), "books": 0, "outcomes": 0}
        flattened: list[dict[str, Any]] = []
        for market in markets:
            books: list[dict[str, Any]] = []
            for key in book_keys:
                value = market.get(key)
                if isinstance(value, list):
                    books = [item for item in value if isinstance(item, dict)]
                    if books:
                        break
            if not books:
                books = [_as_dict(_coalesce(market.get("book"), market))]
            counts["books"] += len(books)

            for book in books:
                outcomes: list[dict[str, Any]] = []
                for key in outcome_keys:
                    value = book.get(key)
                    if isinstance(value, list):
                        outcomes = [item for item in value if isinstance(item, dict)]
                        if outcomes:
                            break
                if not outcomes:
                    for key in outcome_keys:
                        value = market.get(key)
                        if isinstance(value, list):
                            outcomes = [item for item in value if isinstance(item, dict)]
                            if outcomes:
                                break
                if not outcomes:
                    outcomes = [_as_dict(_coalesce(book.get("outcome"), book.get("selection"), market.get("selection")))]
                counts["outcomes"] += len(outcomes)
                for outcome in outcomes:
                    flattened.append({"event": row, "market": market, "book": book, "outcome": outcome})
        return flattened, counts

    def _normalize_flattened_row(self, candidate: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str], str | None]:
        event = _as_dict(candidate.get("event"))
        market = _as_dict(candidate.get("market"))
        book = _as_dict(candidate.get("book"))
        outcome = _as_dict(candidate.get("outcome"))
        warnings: list[str] = []

        event_id = _coalesce(
            event.get("event_id"),
            event.get("eventId"),
            event.get("event_uuid"),
            event.get("external_event_id"),
            event.get("id"),
            event.get("game_id"),
            event.get("gameId"),
            market.get("event_id"),
            market.get("eventId"),
            market.get("gameId"),
            outcome.get("event_id"),
            outcome.get("eventId"),
        )
        if event_id is None:
            return None, warnings, "missing_event_id"

        market_name = _coalesce(
            market.get("market"),
            market.get("market_name"),
            market.get("marketName"),
            market.get("market_type"),
            market.get("market_segment"),
            market.get("stat_category"),
            market.get("market_ref"),
            market.get("name"),
            market.get("type"),
            outcome.get("market"),
            outcome.get("marketName"),
        )
        if market_name is None:
            return None, warnings, "missing_market_name"

        selection = _coalesce(
            outcome.get("selection"),
            outcome.get("name"),
            outcome.get("label"),
            outcome.get("outcome"),
            outcome.get("participant"),
            outcome.get("runner"),
            outcome.get("team"),
            outcome.get("side"),
            market.get("selection"),
            market.get("outcome"),
            market.get("participant"),
        )
        if selection is None:
            return None, warnings, "missing_selection"

        american_odds = _to_american_int(
            _coalesce(
                outcome.get("odds"),
                outcome.get("american_odds"),
                outcome.get("americanOdds"),
                outcome.get("price"),
                outcome.get("price_american"),
                outcome.get("priceAmerican"),
                outcome.get("odds_american"),
                market.get("odds"),
                market.get("american_odds"),
                market.get("americanOdds"),
                market.get("odds_american"),
            )
        )
        decimal_odds = _to_decimal(
            _coalesce(
                outcome.get("decimal_odds"),
                outcome.get("decimalOdds"),
                outcome.get("price_decimal"),
                outcome.get("priceDecimal"),
                outcome.get("decimal"),
                outcome.get("odds_decimal"),
                market.get("decimal_odds"),
                market.get("decimalOdds"),
                market.get("price_decimal"),
                market.get("priceDecimal"),
                market.get("odds_decimal"),
            )
        )

        odds = american_odds
        implied_probability = None
        if odds is not None:
            decimal_odds = decimal_odds or _american_to_decimal(odds)
            implied_probability = _implied_probability_from_american(odds)
        else:
            if decimal_odds is None:
                return None, warnings, "malformed_odds"
            odds = decimal_odds
            implied_probability = _implied_probability_from_decimal(decimal_odds)
            warnings.append("odds_format_decimal")

        sport = _coalesce(event.get("sport"), event.get("sport_name"), event.get("sportName"), event.get("sport_key"), event.get("sport_ref"))
        league = _coalesce(
            event.get("league"),
            event.get("league_name"),
            event.get("leagueName"),
            event.get("league_ref"),
            event.get("competition"),
            event.get("competitionName"),
            event.get("tournament"),
        )
        event_name = _coalesce(
            event.get("event_name"),
            event.get("eventName"),
            event.get("name"),
            event.get("title"),
            event.get("matchup"),
        )
        if event_name is None:
            home = _safe_str(_coalesce(event.get("home_team"), event.get("homeTeam"), event.get("team1")))
            away = _safe_str(_coalesce(event.get("away_team"), event.get("awayTeam"), event.get("team2")))
            if home and away:
                event_name = f"{away} @ {home}"
            else:
                event_name = f"event_{event_id}"
            warnings.append("fallback_event_name")

        start_time = _coalesce(
            event.get("start_time"),
            event.get("startTime"),
            event.get("starts_at"),
            event.get("startsAt"),
            event.get("commence_time"),
            event.get("scheduled"),
            event.get("event_start_time"),
        )
        if start_time is None:
            start_time = utc_now_iso()
            warnings.append("fallback_start_time")

        timestamp = _coalesce(
            outcome.get("timestamp"),
            outcome.get("updated_at"),
            outcome.get("updatedAt"),
            market.get("timestamp"),
            market.get("updated_at"),
            market.get("updatedAt"),
            book.get("timestamp"),
            book.get("updated_at"),
            book.get("updatedAt"),
            event.get("timestamp"),
            event.get("updated_at"),
            event.get("updatedAt"),
            event.get("wire_received_at"),
            event.get("last_seen_at"),
            event.get("odds_changed_at"),
            utc_now_iso(),
        )
        if not _safe_str(timestamp):
            timestamp = utc_now_iso()
            warnings.append("fallback_timestamp")

        normalized = {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "received_at": utc_now_iso(),
            "event_id": _safe_str(event_id),
            "sport": _safe_str(sport),
            "league": _safe_str(league),
            "event_name": _safe_str(event_name),
            "start_time": _safe_str(start_time),
            "book": _safe_str(
                _coalesce(
                    book.get("book"),
                    book.get("name"),
                    book.get("sportsbook"),
                    book.get("label"),
                    book.get("id"),
                    event.get("sportsbook"),
                    event.get("sportsbook_ref"),
                    "sharp",
                )
            ),
            "market": _safe_str(market_name),
            "selection": _safe_str(selection),
            "line": _coalesce(outcome.get("line"), outcome.get("point"), market.get("line"), market.get("point")),
            "odds": odds,
            "decimal_odds": decimal_odds,
            "implied_probability": implied_probability,
            "timestamp": _safe_str(timestamp),
            "source_payload_redacted": {
                "event_field_names": sorted(str(k) for k in event.keys())[:40],
                "market_field_names": sorted(str(k) for k in market.keys())[:40],
                "book_field_names": sorted(str(k) for k in book.keys())[:40],
                "outcome_field_names": sorted(str(k) for k in outcome.keys())[:40],
            },
            "schema_version": SCHEMA_VERSION,
        }
        return normalized, warnings, None

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_provider_payload(
            PROVIDER_TYPE,
            payload,
            max_staleness_seconds=3600 * 12,
        )

    def fetch_snapshot(self) -> dict[str, Any]:
        config_state = self.validate_config()
        credential_status = config_state["credential_status"]
        status = "blocked"
        if "provider_disabled" in config_state["blockers"]:
            status = "provider_disabled"
        elif "live_reads_disabled" in config_state["blockers"]:
            status = "live_reads_disabled"
        elif "blocked_missing_credentials" in config_state["blockers"]:
            status = "blocked_missing_credentials"
        elif "read_only_required" in config_state["blockers"]:
            status = "blocked"
        if not config_state["ok"]:
            return {
                "ok": True,
                "status": status,
                "provider_id": self.provider_id,
                "provider_enabled": bool(config_state["provider_enabled"]),
                "live_calls_enabled": bool(config_state["live_calls_enabled"]),
                "credential_status": credential_status,
                "dry_run": True,
                "records": [],
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "blockers": config_state["blockers"][:10],
                "timestamp": utc_now_iso(),
            }

        fetch = self.fetch_odds()
        if (not fetch["ok"]) and fetch.get("blocker") == "http_404":
            fetch = self.fetch_events()
        if not fetch["ok"]:
            return {
                "ok": True,
                "status": fetch["status"],
                "provider_id": self.provider_id,
                "provider_enabled": bool(config_state["provider_enabled"]),
                "live_calls_enabled": bool(config_state["live_calls_enabled"]),
                "credential_status": credential_status,
                "dry_run": False,
                "records": [],
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "http_status": fetch.get("http_status"),
                "diagnostic": fetch.get("diagnostic"),
                "blockers": fetch["errors"][:10],
                "timestamp": utc_now_iso(),
            }

        normalized: list[dict[str, Any]] = []
        rejection_reason_counts: Counter[str] = Counter()
        warning_reason_counts: Counter[str] = Counter()
        shape_top_level_keys: set[str] = set()
        first_level_nested_keys: set[str] = set()
        candidate_counts: Counter[str] = Counter()
        for row in fetch["records"]:
            if not isinstance(row, dict):
                rejection_reason_counts["malformed_record"] += 1
                continue
            shape_top_level_keys.update(str(k) for k in row.keys())
            for value in row.values():
                if isinstance(value, dict):
                    first_level_nested_keys.update(str(k) for k in value.keys())
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            first_level_nested_keys.update(str(k) for k in item.keys())
                            break
            flattened_rows, counts = self._extract_nested_rows(row)
            candidate_counts.update(counts)
            for flattened in flattened_rows:
                norm, warnings, reject_reason = self._normalize_flattened_row(flattened)
                for warning in warnings:
                    warning_reason_counts[warning] += 1
                if reject_reason:
                    rejection_reason_counts[reject_reason] += 1
                    continue
                verdict = self.validate_payload(norm or {})
                if verdict["ok"]:
                    normalized.append(norm or {})
                else:
                    if verdict["errors"]:
                        for reason in verdict["errors"]:
                            rejection_reason_counts[str(reason)] += 1
                    else:
                        rejection_reason_counts["validation_rejected"] += 1
        rejected = int(sum(rejection_reason_counts.values()))
        debug_summary = {
            "top_level_field_names_present": sorted(shape_top_level_keys)[:50],
            "first_level_nested_field_names": sorted(first_level_nested_keys)[:100],
            "candidate_event_count": int(candidate_counts.get("events", 0)),
            "candidate_market_count": int(candidate_counts.get("markets", 0)),
            "candidate_book_count": int(candidate_counts.get("books", 0)),
            "candidate_outcome_count": int(candidate_counts.get("outcomes", 0)),
            "rejection_reason_counts": dict(rejection_reason_counts),
            "validation_warning_counts": dict(warning_reason_counts),
            "secret_redacted": True,
        }
        return {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": self.provider_id,
            "provider_enabled": bool(config_state["provider_enabled"]),
            "live_calls_enabled": bool(config_state["live_calls_enabled"]),
            "credential_status": credential_status,
            "dry_run": False,
            "records": normalized,
            "records_received": len(fetch["records"]),
            "records_valid": len(normalized),
            "records_rejected": rejected,
            "rejection_reason_counts": dict(rejection_reason_counts),
            "internal_debug_summary": debug_summary,
            "blockers": [],
            "timestamp": utc_now_iso(),
        }
