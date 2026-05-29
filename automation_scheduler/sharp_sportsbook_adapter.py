from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from .provider_payload_validator import validate_provider_payload
from .provider_secret_policy import credential_status_from_env, redact_mapping
from .scheduler_config import utc_now_iso

PROVIDER_ID = "sharp_sportsbook"
PROVIDER_TYPE = "sportsbook_odds"
SCHEMA_VERSION = "automation_scheduler.v1.sharp_sportsbook.v1"
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_BASE_URL = "https://api.sharp.app"


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


def _american_to_decimal(american_odds: float | int | None) -> float | None:
    try:
        odds = float(american_odds)
    except (TypeError, ValueError):
        return None
    if odds == 0:
        return None
    if odds > 0:
        return round(1.0 + (odds / 100.0), 6)
    return round(1.0 + (100.0 / abs(odds)), 6)


def _implied_probability_from_american(american_odds: float | int | None) -> float | None:
    try:
        odds = float(american_odds)
    except (TypeError, ValueError):
        return None
    if odds == 0:
        return None
    if odds > 0:
        return round(100.0 / (odds + 100.0), 8)
    return round(abs(odds) / (abs(odds) + 100.0), 8)


class SharpSportsbookAdapter:
    def __init__(self, contract: dict[str, Any] | None = None):
        self.contract = dict(contract or {})
        self.provider_id = PROVIDER_ID
        self.provider_name = "Sharp Sportsbook"
        self.provider_type = PROVIDER_TYPE
        self.base_url = (os.getenv("SHARP_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout_seconds = max(1.0, _safe_float(os.getenv("SHARP_API_TIMEOUT_SECONDS"), DEFAULT_TIMEOUT_SECONDS))
        self.live_reads_enabled = _env_bool("SHARP_LIVE_READS_ENABLED", default=False)
        self.read_only_mode = True

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
        provider_enabled = bool(self.contract.get("enabled", False))
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

    def _safe_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        cfg = self.validate_config()
        if "blocked_missing_credentials" in cfg["blockers"]:
            return {"ok": False, "status": "blocked_missing_credentials", "records": [], "errors": ["missing_credentials"]}
        if "live_reads_disabled" in cfg["blockers"]:
            return {"ok": True, "status": "live_reads_disabled", "records": [], "errors": []}
        if "provider_disabled" in cfg["blockers"]:
            return {"ok": True, "status": "provider_disabled", "records": [], "errors": []}
        if not cfg["ok"]:
            return {"ok": True, "status": "blocked", "records": [], "errors": cfg["blockers"]}

        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, headers=self._build_headers(), params=params or {})
            if response.status_code == 429:
                return {"ok": False, "status": "rate_limited", "records": [], "errors": ["provider_rate_limited"]}
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "status": "provider_error",
                    "records": [],
                    "errors": [f"http_{response.status_code}"],
                }
            body = response.json()
        except httpx.TimeoutException:
            return {"ok": False, "status": "timeout", "records": [], "errors": ["provider_timeout"]}
        except Exception:
            return {"ok": False, "status": "provider_error", "records": [], "errors": ["provider_unreachable"]}

        records = body if isinstance(body, list) else body.get("data", [])
        if not isinstance(records, list):
            return {"ok": False, "status": "malformed_payload", "records": [], "errors": ["malformed_payload"]}
        return {"ok": True, "status": "ok", "records": records, "errors": []}

    def fetch_events(self) -> dict[str, Any]:
        return self._safe_get("v1/events")

    def fetch_odds(self) -> dict[str, Any]:
        return self._safe_get("v1/odds")

    def fetch_player_props(self) -> dict[str, Any]:
        return self._safe_get("v1/player-props")

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
                "blockers": fetch["errors"][:10],
                "timestamp": utc_now_iso(),
            }

        normalized: list[dict[str, Any]] = []
        rejected = 0
        for row in fetch["records"]:
            if not isinstance(row, dict):
                rejected += 1
                continue
            norm = self.normalize_payload(row)
            verdict = self.validate_payload(norm)
            if verdict["ok"]:
                normalized.append(norm)
            else:
                rejected += 1
        return {
            "ok": True,
            "status": "ok",
            "provider_id": self.provider_id,
            "provider_enabled": bool(config_state["provider_enabled"]),
            "live_calls_enabled": bool(config_state["live_calls_enabled"]),
            "credential_status": credential_status,
            "dry_run": False,
            "records": normalized,
            "records_received": len(fetch["records"]),
            "records_valid": len(normalized),
            "records_rejected": rejected,
            "blockers": [],
            "timestamp": utc_now_iso(),
        }
