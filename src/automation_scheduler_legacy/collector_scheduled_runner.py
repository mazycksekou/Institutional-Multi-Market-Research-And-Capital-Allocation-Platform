from __future__ import annotations

import os
import secrets
from typing import Any

from .calibration_collector import run_collector_cycle
from .data_paths import get_storage_health, resolve_base_data_dir


CRON_TOKEN_ENV = "COLLECTOR_CRON_TOKEN"

DEFAULT_SCHEDULED_COLLECTOR_CONFIG = {
    "dry_run": False,
    "persist_outcomes": True,
    "target_daily_new_contracts": 250,
    "hard_cap_daily_new_contracts": 500,
    "max_new_contracts_per_cycle": 50,
    "max_markets_scanned": 25000,
    "adaptive_throttle": True,
    "include_short_term": True,
    "include_medium_term": True,
    "include_long_term": True,
    "deepseek_review": False,
}

UNSAFE_TRUE_FIELDS = {
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "live_execution_requested",
    "auto_execution_enabled",
    "auto_bet_enabled",
    "auto_trade_enabled",
    "kalshi_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "broker_order_execution_enabled",
    "submit_live_order",
    "submit_live_bet",
    "submit_live_trade",
    "submit_order",
    "submit_bet",
    "submit_trade",
    "infer_outcomes",
    "inferred_outcomes",
    "allow_inferred_outcomes",
}


def _safe_response(status: str, *, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "errors": list(errors or [])[:10],
        "provider_write": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "storage_backend": "file",
        "storage_health": get_storage_health(),
        "raw_payload_included": False,
    }


def validate_cron_token(provided_token: str | None) -> tuple[bool, int, dict[str, Any] | None]:
    expected = os.getenv(CRON_TOKEN_ENV)
    if expected is None or not expected.strip():
        return False, 503, _safe_response("scheduled_endpoint_disabled", errors=["missing_COLLECTOR_CRON_TOKEN"])
    if provided_token is None or not provided_token.strip():
        return False, 401, _safe_response("unauthorized", errors=["missing_X_Collector_Token"])
    if not secrets.compare_digest(str(provided_token), str(expected)):
        return False, 403, _safe_response("forbidden", errors=["invalid_X_Collector_Token"])
    return True, 200, None


def _as_int(payload: dict[str, Any], key: str, default: int) -> int:
    value = payload.get(key, default)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _validate_overrides(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(UNSAFE_TRUE_FIELDS):
        if payload.get(field) is True:
            errors.append(f"{field}_rejected")
    for field in (
        "target_daily_new_contracts",
        "hard_cap_daily_new_contracts",
        "max_new_contracts_per_cycle",
        "max_new_contracts",
        "max_markets_scanned",
    ):
        if field in payload and payload.get(field) is not None:
            try:
                if int(payload[field]) < 0:
                    errors.append(f"{field}_must_be_non_negative")
            except (TypeError, ValueError):
                errors.append(f"{field}_must_be_integer")
    hard_cap = payload.get("hard_cap_daily_new_contracts")
    if isinstance(hard_cap, str) and hard_cap.strip().lower() in {"unlimited", "none", "infinite", "inf"}:
        errors.append("hard_cap_daily_new_contracts_unlimited_rejected")
    try:
        if hard_cap is not None and int(hard_cap) > 500:
            errors.append("hard_cap_daily_new_contracts_exceeds_scheduled_cap")
    except (TypeError, ValueError):
        pass
    return sorted(set(errors))


def build_scheduled_collector_config(payload: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str]]:
    payload = dict(payload or {})
    errors = _validate_overrides(payload)
    config = dict(DEFAULT_SCHEDULED_COLLECTOR_CONFIG)
    config.update(
        {
            "target_daily_new_contracts": _as_int(payload, "target_daily_new_contracts", config["target_daily_new_contracts"]),
            "hard_cap_daily_new_contracts": _as_int(payload, "hard_cap_daily_new_contracts", config["hard_cap_daily_new_contracts"]),
            "max_new_contracts_per_cycle": _as_int(payload, "max_new_contracts_per_cycle", config["max_new_contracts_per_cycle"]),
            "max_markets_scanned": _as_int(payload, "max_markets_scanned", config["max_markets_scanned"]),
            "adaptive_throttle": bool(payload.get("adaptive_throttle", config["adaptive_throttle"])),
            "include_short_term": bool(payload.get("include_short_term", config["include_short_term"])),
            "include_medium_term": bool(payload.get("include_medium_term", config["include_medium_term"])),
            "include_long_term": bool(payload.get("include_long_term", config["include_long_term"])),
            "deepseek_review": bool(payload.get("deepseek_review", False)),
            "trigger_type": str(payload.get("trigger_type") or "scheduled_endpoint"),
        }
    )
    return config, errors


def run_scheduled_collector_cycle(
    payload: dict[str, Any] | None = None,
    *,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config, errors = build_scheduled_collector_config(payload)
    if errors:
        return _safe_response("invalid_request", errors=errors)
    result = run_collector_cycle(
        dry_run=False,
        persist_outcomes=True,
        max_new_contracts=config["max_new_contracts_per_cycle"],
        target_daily_new_contracts=config["target_daily_new_contracts"],
        hard_cap_daily_new_contracts=config["hard_cap_daily_new_contracts"],
        max_markets_scanned=config["max_markets_scanned"],
        include_short_term=config["include_short_term"],
        include_medium_term=config["include_medium_term"],
        include_long_term=config["include_long_term"],
        adaptive_throttle=config["adaptive_throttle"],
        deepseek_review=config["deepseek_review"],
        base_data_dir=base,
    )
    result["trigger_type"] = config["trigger_type"]
    result["scheduled_run"] = True
    result["provider_write"] = False
    result["execution_allowed_count"] = 0
    result["live_execution_enabled"] = False
    result["auto_execution_enabled"] = False
    result["kalshi_order_execution_enabled"] = False
    result["sportsbook_bet_execution_enabled"] = False
    result["broker_order_execution_enabled"] = False
    result["actual_orders_submitted"] = 0
    result["actual_bets_submitted"] = 0
    result["actual_trades_submitted"] = 0
    result["storage_health"] = get_storage_health()
    result["raw_payload_included"] = False
    return result
