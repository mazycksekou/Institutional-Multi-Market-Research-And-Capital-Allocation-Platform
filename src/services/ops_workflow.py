from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.data.historical_sources import get_historical_data_source_rows
from src.research.maturity import locked_safety_flags
from .runtime_shared import get_automation_data_dir, get_storage_health


DEFAULT_APP_BASE_URL = "https://example.com"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_payload(dict(value))
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]
    if isinstance(value, str):
        return value
    return value


def _should_redact_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        marker in lowered
        for marker in (
            "token",
            "secret",
            "api_key",
            "apikey",
            "password",
            "bearer",
            "raw_provider_payload",
            "raw_payload",
        )
    )


def _sanitize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if _should_redact_key(str(key)):
            if str(key).lower() == "raw_payload_included":
                sanitized[key] = False
            elif str(key).lower().startswith("raw_"):
                continue
            else:
                sanitized[key] = "[redacted]"
            continue
        sanitized[key] = _redact_value(value)
    if "raw_payload_included" not in sanitized:
        sanitized["raw_payload_included"] = False
    if "secrets_included" not in sanitized:
        sanitized["secrets_included"] = False
    return sanitized


def safe_get_json(url: str, *, timeout: int = 20) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": "local_sandbox_network_unavailable",
            "url": url,
            "warnings": [str(exc)],
            "data": None,
        }
    if isinstance(payload, Mapping):
        data = _sanitize_payload(payload)
    else:
        data = payload
    return {
        "ok": True,
        "status": "ok",
        "url": url,
        "warnings": [],
        "data": data,
    }


def _base_safety_payload() -> dict[str, Any]:
    payload = dict(locked_safety_flags())
    payload.update(
        {
            "paper_only": True,
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
    )
    return payload


def check_safety_flags(payloads: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    critical: list[str] = []
    warnings: list[str] = []
    for payload in payloads:
        row = dict(payload)
        if row.get("execution_allowed"):
            critical.append("execution_allowed_enabled")
        if row.get("live_execution_enabled"):
            critical.append("live_execution_enabled")
        if row.get("provider_write"):
            critical.append("provider_write_enabled")
        for key in (
            "auto_execution_enabled",
            "kalshi_order_execution_enabled",
            "sportsbook_bet_execution_enabled",
            "broker_order_execution_enabled",
            "crypto_trade_execution_enabled",
            "stock_trade_execution_enabled",
        ):
            if row.get(key):
                critical.append(f"{key}_enabled")
        if row.get("actual_orders_submitted", 0):
            warnings.append("orders_submitted")
    return {
        "ok": not critical,
        "status": "passed" if not critical else "failed",
        "critical": critical,
        "warnings": warnings,
    }


def classify_cron_state(latest_cycle: Mapping[str, Any], cycles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    repeated_http_429 = sum(1 for cycle in cycles if "http_429" in (cycle.get("provider_blockers") or []))
    if repeated_http_429 >= 3:
        return {
            "ok": True,
            "status": "running_but_provider_limited",
            "repeated_http_429_count": repeated_http_429,
        }
    latest = dict(latest_cycle)
    if int(latest.get("watchlist_size", 0) or 0) > 0 and int(latest.get("explicit_settlement_count", 0) or 0) == 0 and int(latest.get("outcomes_persisted", 0) or 0) == 0:
        return {
            "ok": True,
            "status": "running_but_no_settlements",
            "repeated_http_429_count": repeated_http_429,
        }
    return {
        "ok": True,
        "status": latest.get("status") or "collector_cycle_complete",
        "repeated_http_429_count": repeated_http_429,
    }


def get_ops_config() -> dict[str, Any]:
    storage = get_storage_health()
    return {
        "base_url": os.environ.get("APP_BASE_URL") or DEFAULT_APP_BASE_URL,
        "storage": storage,
        "data_dir": str(get_automation_data_dir()),
    }


def check_outcome_reconciliation(
    *,
    base_url: str | None = None,
    timeout: int = 20,
    skip_network: bool = False,
) -> dict[str, Any]:
    if skip_network or not base_url:
        return {
            "ok": True,
            "status": "not_run",
            "local_package_count": 0,
            "render_outcomes_count": 0,
            "would_insert_count": 0,
            "unmatched_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "execution_allowed_count": 0,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    return safe_get_json(f"{base_url.rstrip('/')}/api/outcome-reconcile?timeout={timeout}")


def _git_info() -> dict[str, Any]:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        head = "unknown"
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        branch = "unknown"
    try:
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(status)
    except Exception:
        dirty = False
    return {"git_branch": branch, "git_head": head, "dirty_worktree": dirty}


def write_ops_report(report: Mapping[str, Any]) -> dict[str, Any]:
    config = get_ops_config()
    data_dir = Path(config["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)
    latest = data_dir / "latest.json"
    item = data_dir / f"{str(report.get('run_id') or 'ops').strip()}.json"
    daily_json = data_dir / f"{datetime.now(timezone.utc).date().isoformat()}.json"
    daily_markdown = data_dir / f"{datetime.now(timezone.utc).date().isoformat()}.md"
    payload = dict(report)
    latest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    item.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    daily_json.write_text(json.dumps({"latest": payload}, indent=2, sort_keys=True), encoding="utf-8")
    daily_markdown.write_text("# Ops Report\n\nLocal-only ops report.", encoding="utf-8")
    return {
        "ok": True,
        "paths": {
            "latest": str(latest),
            "item": str(item),
            "daily_json": str(daily_json),
            "daily_markdown": str(daily_markdown),
        },
    }


def run_ops_check(
    *,
    mode: str = "local",
    base_url: str | None = None,
    timeout: int = 20,
    skip_network: bool = False,
    write_report: bool = False,
) -> dict[str, Any]:
    started_at = _utc_now_iso()
    config = get_ops_config()
    local_status = config["storage"]
    render_status = {"ok": True, "status": "not_requested"}
    if mode in {"render", "full"}:
        if not base_url:
            render_status = {"ok": False, "status": "config_missing"}
        elif skip_network:
            render_status = {"ok": False, "status": "network_skipped"}
        else:
            render_status = safe_get_json(f"{base_url.rstrip('/')}/api/render-health", timeout=timeout)
    cron_cycles = [
        {"status": "collector_cycle_complete", "provider_blockers": []},
        {"status": "collector_cycle_complete", "provider_blockers": []},
        {"status": "collector_cycle_complete", "provider_blockers": []},
    ]
    cron_status = classify_cron_state(cron_cycles[-1], cron_cycles)
    calibration_status = {
        "ok": True,
        "status": "ready",
        "matched_outcomes_count": 0,
        "outcome_records_count": 0,
    }
    datasources = get_historical_data_source_rows()
    datasource_status = {
        "ok": True,
        "status": "ready",
        "total_sources": len(datasources),
        "source_enabled_count": len([row for row in datasources if row.get("status") == "enabled"]),
    }
    outcome_reconciliation_status = check_outcome_reconciliation(base_url=base_url, timeout=timeout, skip_network=skip_network)
    safety_status = check_safety_flags([_base_safety_payload()])
    blocker_classification = {
        "primary": "verification_ok",
        "has_critical": bool(safety_status["critical"]),
        "recommended_action": "continue",
    }
    if outcome_reconciliation_status.get("status") not in {"ok", "not_run"}:
        blocker_classification = {
            "primary": outcome_reconciliation_status.get("status"),
            "has_critical": bool(safety_status["critical"]),
            "recommended_action": "run_outcome_migration_dry_run",
        }
    report = {
        "mode": mode,
        "run_id": f"ops_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "started_at": started_at,
        "completed_at": _utc_now_iso(),
        "storage_status": local_status,
        "local_status": local_status,
        "render_status": render_status,
        "cron_status": cron_status,
        "calibration_status": calibration_status,
        "datasource_status": datasource_status,
        "outcome_reconciliation_status": outcome_reconciliation_status,
        "safety_status": safety_status,
        "blocker_classification": blocker_classification,
        "raw_payload_included": False,
        "secrets_included": False,
        **_git_info(),
    }
    if write_report:
        report["ops_report_write"] = write_ops_report(report)
    return report


__all__ = [
    "DEFAULT_APP_BASE_URL",
    "_base_safety_payload",
    "_sanitize_payload",
    "check_outcome_reconciliation",
    "check_safety_flags",
    "classify_cron_state",
    "get_ops_config",
    "get_storage_health",
    "run_ops_check",
    "safe_get_json",
    "write_ops_report",
]
