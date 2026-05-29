from __future__ import annotations

import os
from collections import Counter
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from .provider_payload_validator import validate_provider_payload
from .provider_secret_policy import credential_status_from_env, redact_http_diagnostic, redact_mapping
from .scheduler_config import utc_now_iso

PROVIDER_ID = "kalshi_prediction_market"
PROVIDER_TYPE = "prediction_market"
SCHEMA_VERSION = "automation_scheduler.v1.kalshi_prediction_market.v1"
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_BASE_URL = "https://api.kalshi.com/trade-api/v2"
DEFAULT_MARKETS_PATH = "markets"
DEFAULT_EVENTS_PATH = "events"


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


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_path(path_value: str) -> str:
    segments = [segment for segment in str(path_value or "").strip().split("/") if segment]
    if not segments:
        return "/"
    return "/" + "/".join(segments)


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


def _to_probability(value: Any) -> float | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    if 0.0 <= parsed <= 1.0:
        return round(parsed, 8)
    if 1.0 < parsed <= 100.0:
        return round(parsed / 100.0, 8)
    return None


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


class KalshiReadonlyAdapter:
    def __init__(self, contract: dict[str, Any] | None = None):
        self.contract = dict(contract or {})
        self.provider_id = PROVIDER_ID
        self.provider_name = "Kalshi Prediction Market"
        self.provider_type = PROVIDER_TYPE
        self.base_url = (os.getenv("KALSHI_API_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
        self.base_url_present = bool(os.getenv("KALSHI_API_BASE_URL", "").strip())
        self.timeout_seconds = max(1.0, _safe_float(os.getenv("KALSHI_API_TIMEOUT_SECONDS"), DEFAULT_TIMEOUT_SECONDS))
        self.retry_count = max(0, int(_safe_float(os.getenv("KALSHI_API_RETRY_COUNT"), 0)))
        self.provider_enabled_from_env = _env_bool("KALSHI_PROVIDER_ENABLED", default=False) if os.getenv("KALSHI_PROVIDER_ENABLED") is not None else None
        self.live_reads_enabled = _env_bool("KALSHI_LIVE_READS_ENABLED", default=bool(self.contract.get("live_calls_enabled", False)))
        self.path_config = {
            "markets_path": os.getenv("KALSHI_MARKETS_PATH", DEFAULT_MARKETS_PATH),
            "events_path": os.getenv("KALSHI_EVENTS_PATH", DEFAULT_EVENTS_PATH),
        }
        self.read_only_mode = True

    def _classify_request_error(self, exc: Exception) -> tuple[str, str]:
        text = str(exc).lower()
        error_class = exc.__class__.__name__
        if isinstance(exc, httpx.InvalidURL):
            return "invalid_url", error_class
        if isinstance(exc, httpx.ConnectTimeout):
            return "connect_timeout", error_class
        if isinstance(exc, httpx.ReadTimeout):
            return "read_timeout", error_class
        if isinstance(exc, httpx.TimeoutException):
            return "read_timeout", error_class
        if isinstance(exc, httpx.ConnectError):
            if any(marker in text for marker in ("name or service not known", "getaddrinfo", "nodename nor servname", "temporary failure in name resolution", "no such host", "name does not resolve")):
                return "dns_error", error_class
            if any(marker in text for marker in ("ssl", "tls", "certificate", "cert verify", "wrong version number", "handshake")):
                return "tls_error", error_class
            return "connection_error", error_class
        if isinstance(exc, httpx.LocalProtocolError):
            return "request_build_error", error_class
        if isinstance(exc, httpx.RequestError):
            if any(marker in text for marker in ("invalid url", "unsupported url", "unknown url type")):
                return "invalid_url", error_class
            return "provider_unreachable", error_class
        return "unknown_client_error", error_class

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

    def build_kalshi_url(self, path_name: str) -> dict[str, Any]:
        _, diagnostic = self._resolve_url_and_diag(path_name)
        return diagnostic

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "supports_polling": True,
            "supports_streaming": False,
            "required_credentials": ["KALSHI_API_KEY", "KALSHI_API_SECRET"],
            "supported_markets": ["event_contracts", "yes_no_contracts", "binary_markets"],
            "read_only_mode": True,
            "enabled": bool(self.contract.get("enabled", False)),
            "live_calls_enabled": bool(self.contract.get("live_calls_enabled", False)),
            "provider_live_calls_enabled": False,
            "dry_run": True,
        }

    def validate_config(self) -> dict[str, Any]:
        blockers: list[str] = []
        credential = credential_status_from_env(self.provider_id)
        provider_enabled = bool(self.provider_enabled_from_env) if self.provider_enabled_from_env is not None else bool(self.contract.get("enabled", False))
        live_call_contract_enabled = bool(self.contract.get("live_calls_enabled", False))
        dry_run = bool(self.contract.get("dry_run", True))
        auto_execution_enabled = bool(self.contract.get("auto_execution_enabled", False))
        kalshi_order_execution_enabled = bool(self.contract.get("kalshi_order_execution_enabled", False))

        if not provider_enabled:
            blockers.append("provider_disabled")
        if not self.live_reads_enabled or not live_call_contract_enabled:
            blockers.append("live_reads_disabled")
        if credential["status"] != "ok":
            blockers.append("blocked_missing_credentials")
        if not dry_run:
            blockers.append("dry_run_required")
        if auto_execution_enabled or kalshi_order_execution_enabled:
            blockers.append("auto_execution_not_allowed")
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
        api_key = os.getenv("KALSHI_API_KEY", "").strip()
        api_secret = os.getenv("KALSHI_API_SECRET", "").strip()
        return {
            "KALSHI-ACCESS-KEY": api_key,
            "KALSHI-ACCESS-SECRET": api_secret,
            "Accept": "application/json",
        }

    def _safe_get(self, path_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        cfg = self.validate_config()
        if "blocked_missing_credentials" in cfg["blockers"]:
            return {"ok": False, "status": "blocked_missing_credentials", "records": [], "errors": ["missing_credentials"]}
        if "live_reads_disabled" in cfg["blockers"]:
            return {"ok": True, "status": "live_reads_disabled", "records": [], "errors": []}
        if "provider_disabled" in cfg["blockers"]:
            return {"ok": True, "status": "provider_disabled", "records": [], "errors": []}
        if "dry_run_required" in cfg["blockers"]:
            return {"ok": True, "status": "dry_run_placeholder", "records": [], "errors": ["dry_run_required"]}
        if "auto_execution_not_allowed" in cfg["blockers"]:
            return {"ok": True, "status": "dry_run_placeholder", "records": [], "errors": ["auto_execution_not_allowed"]}
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
        except httpx.TimeoutException as exc:
            category, error_class = self._classify_request_error(exc)
            return {
                "ok": False,
                "status": "provider_error",
                "http_status": None,
                "blocker": category,
                "diagnostic": redact_http_diagnostic(
                    {
                        **diagnostic,
                        "method": "GET",
                        "error_class": error_class,
                        "error_category": category,
                        "timeout_seconds": self.timeout_seconds,
                        "retry_count": self.retry_count,
                    }
                ),
                "records": [],
                "errors": [category],
            }
        except Exception as exc:
            category, error_class = self._classify_request_error(exc)
            blocker = category if category in {
                "dns_error",
                "tls_error",
                "connect_timeout",
                "read_timeout",
                "connection_error",
                "invalid_url",
                "request_build_error",
                "provider_unreachable",
                "unknown_client_error",
            } else "provider_unreachable"
            return {
                "ok": False,
                "status": "provider_error",
                "http_status": None,
                "blocker": blocker,
                "diagnostic": redact_http_diagnostic(
                    {
                        **diagnostic,
                        "method": "GET",
                        "error_class": error_class,
                        "error_category": blocker,
                        "timeout_seconds": self.timeout_seconds,
                        "retry_count": self.retry_count,
                    }
                ),
                "records": [],
                "errors": [blocker],
            }
        return {"ok": True, "status": "ok", "records": self._extract_records(body), "errors": []}

    def fetch_markets(self) -> dict[str, Any]:
        return self._safe_get("markets_path")

    def fetch_events(self) -> dict[str, Any]:
        return self._safe_get("events_path")

    def _extract_records(self, body: Any) -> list[dict[str, Any]]:
        if isinstance(body, list):
            return [row for row in body if isinstance(row, dict)]
        if not isinstance(body, dict):
            return []
        for key in ("data", "markets", "events", "items", "results"):
            candidate = body.get(key)
            if isinstance(candidate, list):
                return [row for row in candidate if isinstance(row, dict)]
        return []

    def normalize_payload(self, payload: dict[str, Any], *, event_lookup: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        event_lookup = event_lookup or {}
        event_id = _safe_str(_coalesce(payload.get("event_id"), payload.get("eventId"), payload.get("event_ticker"), payload.get("eventTicker")))
        event_row = event_lookup.get(event_id or "", {})

        yes_bid = _to_probability(_coalesce(payload.get("yes_bid"), payload.get("yesBid"), payload.get("best_bid_yes")))
        yes_ask = _to_probability(_coalesce(payload.get("yes_ask"), payload.get("yesAsk"), payload.get("best_ask_yes")))
        no_bid = _to_probability(_coalesce(payload.get("no_bid"), payload.get("noBid"), payload.get("best_bid_no")))
        no_ask = _to_probability(_coalesce(payload.get("no_ask"), payload.get("noAsk"), payload.get("best_ask_no")))

        raw_yes_price = _coalesce(payload.get("yes_price"), payload.get("yesPrice"), payload.get("last_price_yes"), payload.get("lastPriceYes"))
        raw_no_price = _coalesce(payload.get("no_price"), payload.get("noPrice"), payload.get("last_price_no"), payload.get("lastPriceNo"))
        yes_price: Any = _to_probability(raw_yes_price)
        no_price: Any = _to_probability(raw_no_price)
        if yes_price is None and yes_bid is not None and yes_ask is not None:
            yes_price = round((yes_bid + yes_ask) / 2.0, 8)
        if no_price is None and no_bid is not None and no_ask is not None:
            no_price = round((no_bid + no_ask) / 2.0, 8)
        if yes_price is not None and no_price is None:
            no_price = round(max(0.0, min(1.0, 1.0 - yes_price)), 8)
        if no_price is not None and yes_price is None:
            yes_price = round(max(0.0, min(1.0, 1.0 - no_price)), 8)
        if yes_price is None and raw_yes_price is not None:
            yes_price = raw_yes_price
        if no_price is None and raw_no_price is not None:
            no_price = raw_no_price

        implied_probability = yes_price
        close_time = _safe_str(_coalesce(payload.get("close_time"), payload.get("closeTime"), payload.get("expiration_time"), event_row.get("close_time"), event_row.get("closeTime")))
        timestamp = _safe_str(_coalesce(payload.get("timestamp"), payload.get("updated_at"), payload.get("updatedAt"), payload.get("last_updated_ts"), event_row.get("timestamp"), event_row.get("updated_at"), utc_now_iso()))

        spread = None
        if yes_bid is not None and yes_ask is not None:
            spread = max(0.0, yes_ask - yes_bid)
        liquidity_score = 0.0
        if spread is not None:
            liquidity_score = round(max(0.0, min(1.0, 1.0 - spread)), 8)

        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "received_at": utc_now_iso(),
            "market_id": _safe_str(_coalesce(payload.get("market_id"), payload.get("marketId"), payload.get("ticker"))),
            "event_id": event_id,
            "event_title": _safe_str(_coalesce(payload.get("event_title"), payload.get("eventTitle"), event_row.get("title"), event_row.get("event_title"))),
            "contract_id": _safe_str(_coalesce(payload.get("contract_id"), payload.get("contractId"), payload.get("series_ticker"), payload.get("seriesTicker"))),
            "contract_title": _safe_str(_coalesce(payload.get("contract_title"), payload.get("contractTitle"), payload.get("subtitle"), payload.get("title"))),
            "ticker": _safe_str(_coalesce(payload.get("ticker"), payload.get("market_ticker"), payload.get("marketTicker"))),
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "no_bid": no_bid,
            "no_ask": no_ask,
            "yes_price": yes_price,
            "no_price": no_price,
            "implied_probability": implied_probability,
            "volume": _to_float(_coalesce(payload.get("volume"), payload.get("trade_volume"), payload.get("tradeVolume"))),
            "open_interest": _to_float(_coalesce(payload.get("open_interest"), payload.get("openInterest"))),
            "liquidity_score": liquidity_score,
            "close_time": close_time,
            "status": _safe_str(_coalesce(payload.get("status"), payload.get("market_status"), payload.get("marketStatus"))),
            "settlement_rule": _safe_str(_coalesce(payload.get("settlement_rule"), payload.get("settlementRule"), payload.get("rules_primary"), payload.get("rulesPrimary"), payload.get("resolution_criteria"))),
            "timestamp": timestamp,
            "source_payload_redacted": redact_mapping(payload),
            "schema_version": SCHEMA_VERSION,
        }

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_provider_payload(PROVIDER_TYPE, payload, max_staleness_seconds=3600 * 12)

    def fetch_snapshot(self) -> dict[str, Any]:
        config_state = self.validate_config()
        credential_status = config_state["credential_status"]
        status = "dry_run_placeholder"
        if "provider_disabled" in config_state["blockers"]:
            status = "provider_disabled"
        elif "live_reads_disabled" in config_state["blockers"]:
            status = "live_reads_disabled"
        elif "blocked_missing_credentials" in config_state["blockers"]:
            status = "blocked_missing_credentials"

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

        events_fetch = self.fetch_events()
        markets_fetch = self.fetch_markets()
        if not events_fetch["ok"] and not markets_fetch["ok"]:
            blockers = list(dict.fromkeys(list(events_fetch.get("errors", [])) + list(markets_fetch.get("errors", []))))
            return {
                "ok": True,
                "status": "provider_error",
                "provider_id": self.provider_id,
                "provider_enabled": bool(config_state["provider_enabled"]),
                "live_calls_enabled": bool(config_state["live_calls_enabled"]),
                "credential_status": credential_status,
                "dry_run": False,
                "records": [],
                "records_received": 0,
                "records_valid": 0,
                "records_rejected": 0,
                "http_status": markets_fetch.get("http_status") or events_fetch.get("http_status"),
                "diagnostic": markets_fetch.get("diagnostic") or events_fetch.get("diagnostic"),
                "blockers": blockers[:10],
                "timestamp": utc_now_iso(),
            }

        event_lookup: dict[str, dict[str, Any]] = {}
        if events_fetch["ok"]:
            for row in events_fetch.get("records", []):
                event_id = _safe_str(_coalesce(row.get("event_id"), row.get("eventId"), row.get("ticker"), row.get("event_ticker")))
                if event_id:
                    event_lookup[event_id] = row

        normalized: list[dict[str, Any]] = []
        rejection_reason_counts: Counter[str] = Counter()
        source_records = list(markets_fetch.get("records", [])) if markets_fetch["ok"] else []
        for row in source_records:
            normalized_row = self.normalize_payload(row, event_lookup=event_lookup)
            verdict = self.validate_payload(normalized_row)
            if verdict["ok"]:
                normalized.append(normalized_row)
            else:
                for reason in verdict.get("errors", []):
                    rejection_reason_counts[str(reason)] += 1

        return {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": self.provider_id,
            "provider_enabled": bool(config_state["provider_enabled"]),
            "live_calls_enabled": bool(config_state["live_calls_enabled"]),
            "credential_status": credential_status,
            "dry_run": False,
            "records": normalized,
            "records_received": len(source_records),
            "records_valid": len(normalized),
            "records_rejected": int(sum(rejection_reason_counts.values())),
            "rejection_reason_counts": dict(rejection_reason_counts),
            "http_status": markets_fetch.get("http_status"),
            "diagnostic": markets_fetch.get("diagnostic"),
            "blockers": [],
            "timestamp": utc_now_iso(),
        }
