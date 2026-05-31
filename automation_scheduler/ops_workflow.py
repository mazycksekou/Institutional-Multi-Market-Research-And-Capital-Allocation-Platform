from __future__ import annotations

import importlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .data_paths import AUTOMATION_DATA_DIR_ENV, get_automation_data_dir, get_collector_scheduler_dir, get_runtime_data_path, get_storage_health


DEFAULT_APP_BASE_URL = "https://betting-stock-api-code-integration.onrender.com"
EXPECTED_CRON_SPACING_MINUTES = 30
READ_ONLY_RENDER_ENDPOINTS = (
    "/api/automation/health",
    "/api/automation/calibration",
    "/api/automation/outcomes",
    "/api/automation/review-queue",
    "/api/automation/data-sources/health",
    "/api/automation/data-sources/registry",
    "/api/automation/data-sources/coverage",
    "/api/automation/institutional-lab/health",
)
REQUIRED_COMMITS = {
    "persistent_storage": "65263202be90ed96f7b88d94edfd0d9115c932ee",
    "data_source_registry": "710697a499c0c2588a9ee2350b829ac3849c7f17",
    "collector_matching_fix": "b369e3f",
    "institutional_sidecar": "0c3ba30",
}
CRITICAL_IMPORTS = (
    "automation_scheduler.data_paths",
    "automation_scheduler.collector_scheduled_runner",
    "automation_scheduler.calibration_collector",
    "automation_scheduler.calibration",
    "automation_scheduler.response_compactor",
)
FALSE_SAFETY_FLAGS = (
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "auto_execution_enabled",
    "kalshi_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "broker_order_execution_enabled",
    "crypto_trade_execution_enabled",
    "stock_trade_execution_enabled",
    "raw_payload_included",
    "secrets_included",
)
ZERO_SAFETY_FLAGS = (
    "execution_allowed_count",
    "actual_orders_submitted",
    "actual_bets_submitted",
    "actual_trades_submitted",
    "actual_crypto_swaps_submitted",
)
TRUE_SAFETY_FLAGS = ("human_approval_required", "paper_only")
SECRET_KEY_FRAGMENTS = (
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
    "credential",
    "client_secret",
    "private_key",
    "api_key",
)
RAW_PAYLOAD_KEYS = {
    "raw_payload",
    "raw_provider_payload",
    "provider_payload",
    "authorization_header",
    "headers",
    "signed_url",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _safe_error(exc: BaseException) -> str:
    text = str(exc)
    if not text:
        text = exc.__class__.__name__
    return text[:240]


def _run_command(args: list[str], timeout: int = 8) -> tuple[int, str]:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return int(completed.returncode), (completed.stdout or completed.stderr or "").strip()
    except Exception as exc:
        return 127, _safe_error(exc)


def _git_value(args: list[str]) -> str | None:
    code, output = _run_command(["git", *args])
    return output if code == 0 and output else None


def _git_commit_exists(commit: str) -> bool:
    code, _ = _run_command(["git", "cat-file", "-e", f"{commit}^{{commit}}"])
    return code == 0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _is_render_runtime() -> bool:
    return any(os.getenv(name) for name in ("RENDER", "RENDER_EXTERNAL_HOSTNAME", "RENDER_INSTANCE_ID"))


def _safe_url(url: str) -> str:
    try:
        parts = urllib.parse.urlsplit(url)
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return str(url).split("?", 1)[0]


def _is_secret_key(key: str) -> bool:
    lower = key.lower()
    if lower in {
        "requires_api_key",
        "api_key_required",
        "secrets_included",
        "collector_cron_token_configured",
        "render_api_key_configured",
    }:
        return False
    if lower.endswith("_configured"):
        return False
    return any(fragment in lower for fragment in SECRET_KEY_FRAGMENTS)


def _is_raw_payload_key(key: str) -> bool:
    lower = key.lower()
    if lower in {"raw_payload_included"}:
        return False
    return lower in RAW_PAYLOAD_KEYS or "raw_provider_payload" in lower


def _sanitize_payload(value: Any, *, depth: int = 0, max_items: int = 50) -> Any:
    if depth > 8:
        return "[truncated]"
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= max_items:
                sanitized["truncated_item_count"] = max(0, len(value) - max_items)
                break
            key_text = str(key)
            if key_text.startswith("_") or _is_raw_payload_key(key_text):
                continue
            if _is_secret_key(key_text):
                sanitized[key_text] = "[redacted]"
            else:
                sanitized[key_text] = _sanitize_payload(item, depth=depth + 1, max_items=max_items)
        return sanitized
    if isinstance(value, list):
        items = [_sanitize_payload(item, depth=depth + 1, max_items=max_items) for item in value[:max_items]]
        if len(value) > max_items:
            items.append({"truncated_item_count": len(value) - max_items})
        return items
    if isinstance(value, tuple):
        return [_sanitize_payload(item, depth=depth + 1, max_items=max_items) for item in value[:max_items]]
    if isinstance(value, Path):
        return str(value)
    return value


def _extract_safety_fields(payload: Any) -> dict[str, Any]:
    wanted = set(FALSE_SAFETY_FLAGS) | set(ZERO_SAFETY_FLAGS) | set(TRUE_SAFETY_FLAGS)
    found: dict[str, Any] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                if key_text in wanted and key_text not in found:
                    found[key_text] = item
                elif not key_text.startswith("_") and not _is_raw_payload_key(key_text):
                    walk(item)
        elif isinstance(value, list):
            for item in value[:100]:
                walk(item)

    walk(payload)
    return _sanitize_payload(found)


def _string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            values.extend(_string_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_string_values(item))
    return values


def _contains_http_429(value: Any) -> bool:
    return any("http_429" in item or "429" == item for item in (text.lower() for text in _string_values(value)))


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool_is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return False


def _bool_is_false(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "no", "off", "disabled"}
    return False


def _progress(count: int, target: int) -> dict[str, Any]:
    target = max(1, int(target))
    count = max(0, int(count))
    return {
        "count": count,
        "target": target,
        "remaining": max(0, target - count),
        "pct": round(min(1.0, count / target), 4),
    }


def get_ops_config() -> dict[str, Any]:
    storage = get_storage_health()
    return {
        "app_base_url": (os.getenv("APP_BASE_URL") or "").strip() or None,
        "default_app_base_url": DEFAULT_APP_BASE_URL,
        "app_base_url_configured": bool((os.getenv("APP_BASE_URL") or "").strip()),
        "automation_data_dir_configured": bool((os.getenv(AUTOMATION_DATA_DIR_ENV) or "").strip()),
        "collector_cron_token_configured": bool((os.getenv("COLLECTOR_CRON_TOKEN") or "").strip()),
        "render_api_key_configured": bool((os.getenv("RENDER_API_KEY") or "").strip()),
        "storage": storage,
        "secrets_included": False,
        "raw_payload_included": False,
    }


def detect_runtime_context() -> dict[str, Any]:
    status_text = _git_value(["status", "--porcelain"]) or ""
    commits = {name: _git_commit_exists(commit) for name, commit in REQUIRED_COMMITS.items()}
    return {
        "cwd": str(Path.cwd()),
        "repo_root": str(_repo_root()),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "is_render": _is_render_runtime(),
        "is_windows": os.name == "nt",
        "git_branch": _git_value(["branch", "--show-current"]),
        "git_head": _git_value(["rev-parse", "--short", "HEAD"]),
        "dirty_worktree": bool(status_text),
        "required_commits_present": commits,
    }


def safe_get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    started = time.monotonic()
    safe_url = _safe_url(url)
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "betting-stock-api-ops-check/1.0"})
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
        try:
            status_code = int(getattr(response, "status", getattr(response, "code", 0)) or 0)
            body = response.read()
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
        elapsed_ms = round((time.monotonic() - started) * 1000, 2)
        try:
            data = json.loads(body.decode("utf-8-sig"))
        except Exception as exc:
            return {
                "ok": False,
                "status": "malformed_json",
                "error_category": "code_defect",
                "status_code": status_code,
                "url": safe_url,
                "elapsed_ms": elapsed_ms,
                "error": _safe_error(exc),
                "data": None,
            }
        return {
            "ok": 200 <= status_code < 300,
            "status": "ok" if 200 <= status_code < 300 else "render_endpoint_failure",
            "error_category": None if 200 <= status_code < 300 else "render_endpoint_failure",
            "status_code": status_code,
            "url": safe_url,
            "elapsed_ms": elapsed_ms,
            "data": _sanitize_payload(data),
        }
    except urllib.error.HTTPError as exc:
        status_code = int(getattr(exc, "code", 0) or 0)
        if status_code in {401, 403}:
            status = "render_auth_problem"
        elif status_code == 404:
            status = "missing_endpoint"
        else:
            status = "render_endpoint_failure"
        return {
            "ok": False,
            "status": status,
            "error_category": "render_auth_problem" if status_code in {401, 403} else "render_endpoint_failure",
            "status_code": status_code,
            "url": safe_url,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": _safe_error(exc),
            "data": None,
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        return {
            "ok": False,
            "status": "local_sandbox_network_unavailable",
            "error_category": "local_sandbox_network_unavailable",
            "status_code": None,
            "url": safe_url,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": _safe_error(exc),
            "data": None,
        }


def load_json_file_safe(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {"ok": False, "status": "missing_file", "path": str(file_path), "data": None}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"ok": False, "status": "malformed_json", "path": str(file_path), "error": _safe_error(exc), "data": None}
    return {"ok": True, "status": "ok", "path": str(file_path), "data": _sanitize_payload(payload)}


def check_local_environment() -> dict[str, Any]:
    import_results: dict[str, dict[str, Any]] = {}
    import_failures: list[str] = []
    for module_name in CRITICAL_IMPORTS:
        try:
            importlib.import_module(module_name)
            import_results[module_name] = {"ok": True, "status": "ok"}
        except Exception as exc:
            import_results[module_name] = {"ok": False, "status": "import_failed", "error": _safe_error(exc)}
            import_failures.append(module_name)

    storage = get_storage_health()
    context = detect_runtime_context()
    scripts = {
        "ops_check": Path("scripts/ops_check.py").exists(),
        "run_tests": Path("scripts/run_tests.ps1").exists(),
    }
    warnings: list[str] = []
    if not bool(storage.get("configured")):
        warnings.append("AUTOMATION_DATA_DIR_unset_using_local_data_fallback")
    missing_commits = [name for name, present in dict(context.get("required_commits_present", {})).items() if not present]
    if missing_commits:
        warnings.append("required_commits_missing")

    return {
        "ok": not import_failures and not missing_commits,
        "status": "ok" if not import_failures and not missing_commits else "code_defect",
        "imports": import_results,
        "import_failures": import_failures,
        "storage_status": storage,
        "runtime_context": context,
        "scripts": scripts,
        "warnings": warnings,
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
        "human_approval_required": True,
        "paper_only": True,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _endpoint_summary(path: str, payload: Any) -> dict[str, Any]:
    data = payload if isinstance(payload, dict) else {}
    summary: dict[str, Any] = {"path": path, "safety_flags": _extract_safety_fields(data)}
    for key in (
        "status",
        "ok",
        "storage_health",
        "paper_decisions_count",
        "outcome_records_count",
        "matched_outcomes_count",
        "unmatched_outcomes_count",
        "coverage_rate",
        "count",
        "total_count",
        "source_enabled_count",
        "enabled_source_count",
        "total_sources",
        "total_lanes",
        "provider_write",
        "execution_allowed",
        "execution_allowed_count",
        "raw_payload_included",
    ):
        if key in data:
            summary[key] = _sanitize_payload(data.get(key))
    if isinstance(data.get("warnings"), list):
        summary["warnings"] = list(data.get("warnings", []))[:10]
    if isinstance(data.get("provider_blockers"), list):
        summary["provider_blockers"] = list(data.get("provider_blockers", []))[:10]
    if path.endswith("/health") and isinstance(data.get("storage_health"), dict):
        summary["storage_health"] = data.get("storage_health")
    return summary


def check_render_health(base_url: str) -> dict[str, Any]:
    if not base_url:
        return {"ok": False, "status": "config_missing", "errors": ["APP_BASE_URL_missing"]}
    result = safe_get_json(_join_url(base_url, "/api/automation/health"))
    return {
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "status_code": result.get("status_code"),
        "endpoint": "/api/automation/health",
        "base_url": base_url.rstrip("/"),
        "summary": _endpoint_summary("/api/automation/health", result.get("data")),
        "error_category": result.get("error_category"),
        "error": result.get("error"),
    }


def check_render_endpoints(base_url: str, *, timeout: int = 20) -> dict[str, Any]:
    if not base_url:
        return {"ok": False, "status": "config_missing", "errors": ["APP_BASE_URL_missing"], "endpoints": {}}
    endpoint_results: dict[str, Any] = {}
    safety_payloads: list[dict[str, Any]] = []
    statuses: list[str] = []
    for path in READ_ONLY_RENDER_ENDPOINTS:
        result = safe_get_json(_join_url(base_url, path), timeout=timeout)
        status = str(result.get("status") or "unknown")
        statuses.append(status)
        summary = _endpoint_summary(path, result.get("data"))
        safety_payloads.append(dict(summary.get("safety_flags") or {}))
        endpoint_results[path] = {
            "ok": bool(result.get("ok")),
            "status": status,
            "status_code": result.get("status_code"),
            "error_category": result.get("error_category"),
            "error": result.get("error"),
            "summary": summary,
        }
    ok = all(item.get("ok") for item in endpoint_results.values())
    if any(status == "local_sandbox_network_unavailable" for status in statuses):
        overall_status = "local_sandbox_network_unavailable"
    elif any(status == "render_auth_problem" for status in statuses):
        overall_status = "render_auth_problem"
    elif any(status == "missing_endpoint" for status in statuses):
        overall_status = "missing_endpoint"
    elif ok:
        overall_status = "ok"
    else:
        overall_status = "render_endpoint_failure"
    return {
        "ok": ok,
        "status": overall_status,
        "base_url": base_url.rstrip("/"),
        "endpoints": endpoint_results,
        "endpoint_count": len(endpoint_results),
        "ok_endpoint_count": sum(1 for item in endpoint_results.values() if item.get("ok")),
        "safety_payloads": safety_payloads,
    }


def _cycle_time(cycle: dict[str, Any], fallback_path: Path | None = None) -> datetime | None:
    for key in ("completed_at", "created_at", "started_at", "latest_cycle_time"):
        parsed = _parse_time(cycle.get(key))
        if parsed is not None:
            return parsed
    if fallback_path is not None and fallback_path.exists():
        try:
            return datetime.fromtimestamp(fallback_path.stat().st_mtime, timezone.utc)
        except Exception:
            return None
    return None


def _latest_cycle_summary(cycle: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "cycle_id",
        "trigger_type",
        "status",
        "created_at",
        "started_at",
        "completed_at",
        "lock_acquired",
        "skipped_due_to_lock",
        "already_completed",
        "markets_scanned",
        "eligible_contracts_found",
        "effective_max_new_contracts",
        "new_contracts_added",
        "watchlist_size",
        "records_checked",
        "records_rechecked_today",
        "explicit_settlement_count",
        "outcomes_persisted",
        "provider_blockers",
        "adaptive_throttle_reasons",
        "errors",
        "next_suggested_recheck_time",
        "storage_health",
    )
    return {key: _sanitize_payload(cycle.get(key)) for key in keys if key in cycle}


def classify_cron_state(latest_cycle: dict[str, Any] | None, recent_cycles: list[dict[str, Any]] | None = None, *, storage: dict[str, Any] | None = None) -> dict[str, Any]:
    recent = list(recent_cycles or [])
    latest = dict(latest_cycle or (recent[0] if recent else {}))
    if storage and (not storage.get("read_ok") or not storage.get("write_ok") or (_is_render_runtime() and storage.get("persistence_warning"))):
        return {"status": "storage_problem", "recommended_action": "fix storage path or persistent disk before trusting cron reports"}
    if not latest:
        return {"status": "local_report_unavailable", "recommended_action": "check Render cron service, APP_BASE_URL, token, and report paths"}
    latest_status = str(latest.get("status") or "").lower()
    if latest_status in {"unauthorized", "forbidden", "scheduled_endpoint_disabled"}:
        return {"status": "endpoint_auth_problem", "recommended_action": "verify COLLECTOR_CRON_TOKEN is configured on cron and web service"}
    http_429_count = sum(1 for cycle in recent[:6] if _contains_http_429(cycle))
    if http_429_count >= 1:
        action = "keep schedule */30, keep or reduce payload, do not manually spam runs, and do not move to */15"
        return {"status": "running_but_provider_limited", "recommended_action": action, "repeated_http_429_count": http_429_count}
    watchlist_size = _as_int(latest.get("watchlist_size"), 0)
    outcomes_persisted = _as_int(latest.get("outcomes_persisted"), 0)
    explicit_settlement_count = _as_int(latest.get("explicit_settlement_count"), 0)
    if watchlist_size > 0 and outcomes_persisted == 0 and explicit_settlement_count == 0:
        return {"status": "running_but_no_settlements", "recommended_action": "wait for explicit settlements before judging calibration"}
    return {"status": "healthy", "recommended_action": "continue current schedule and monitor provider blockers"}


def check_cron_reports() -> dict[str, Any]:
    storage = get_storage_health()
    root = get_collector_scheduler_dir()
    latest_path = root / "latest_cycle.json"
    latest_loaded = load_json_file_safe(latest_path)
    latest_cycle = latest_loaded.get("data") if latest_loaded.get("ok") and isinstance(latest_loaded.get("data"), dict) else {}

    item_cycles: list[tuple[Path, dict[str, Any], datetime | None]] = []
    items_dir = root / "items"
    if items_dir.exists():
        for path in sorted(items_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:200]:
            loaded = load_json_file_safe(path)
            data = loaded.get("data") if loaded.get("ok") and isinstance(loaded.get("data"), dict) else None
            if data is not None:
                item_cycles.append((path, data, _cycle_time(data, path)))
    if latest_cycle and not any(cycle.get("cycle_id") == latest_cycle.get("cycle_id") for _, cycle, _ in item_cycles):
        item_cycles.insert(0, (latest_path, latest_cycle, _cycle_time(latest_cycle, latest_path)))

    now = datetime.now(timezone.utc)
    recent_24h = [(path, cycle, when) for path, cycle, when in item_cycles if when and now - when <= timedelta(hours=24)]
    recent_cycles = [cycle for _, cycle, _ in item_cycles[:6]]
    sorted_times = sorted([when for _, _, when in recent_24h if when])
    spacings: list[float] = []
    for left, right in zip(sorted_times, sorted_times[1:]):
        spacings.append(round((right - left).total_seconds() / 60.0, 2))
    average_spacing = round(sum(spacings) / len(spacings), 2) if spacings else None
    expected_cycles = int((24 * 60) / EXPECTED_CRON_SPACING_MINUTES)
    missed_cycles = max(0, expected_cycles - len(recent_24h))
    latest_time = _cycle_time(latest_cycle, latest_path) if latest_cycle else None
    latest_age = round((now - latest_time).total_seconds() / 60.0, 2) if latest_time else None
    daily_path = root / "daily" / f"{now.date().isoformat()}.json"
    daily_loaded = load_json_file_safe(daily_path)
    classification = classify_cron_state(latest_cycle, recent_cycles, storage=storage)
    latest_summary = _latest_cycle_summary(latest_cycle)
    repeated_429 = int(classification.get("repeated_http_429_count", 0) or sum(1 for cycle in recent_cycles if _contains_http_429(cycle)))

    return {
        "ok": bool(latest_cycle),
        "status": classification.get("status"),
        "cron_detected": bool(latest_cycle),
        "collector_scheduler_dir": str(root),
        "reports_written_under_data_dir": str(root).replace("\\", "/").endswith("collector_scheduler"),
        "latest_cycle_id": latest_cycle.get("cycle_id"),
        "latest_cycle_time": latest_time.isoformat().replace("+00:00", "Z") if latest_time else None,
        "latest_cycle_age_minutes": latest_age,
        "latest_status": latest_cycle.get("status"),
        "cycles_last_24h": len(recent_24h),
        "expected_cycles_last_24h": expected_cycles,
        "average_spacing_minutes": average_spacing,
        "expected_spacing_minutes": EXPECTED_CRON_SPACING_MINUTES,
        "missed_cycles": missed_cycles,
        "latest_provider_blockers": list(latest_cycle.get("provider_blockers") or [])[:10] if latest_cycle else [],
        "repeated_http_429_count": repeated_429,
        "effective_max_new_contracts": _as_int(latest_cycle.get("effective_max_new_contracts"), 0) if latest_cycle else 0,
        "new_contracts_added": _as_int(latest_cycle.get("new_contracts_added"), 0) if latest_cycle else 0,
        "watchlist_size": _as_int(latest_cycle.get("watchlist_size"), 0) if latest_cycle else 0,
        "records_checked": _as_int(latest_cycle.get("records_checked"), 0) if latest_cycle else 0,
        "explicit_settlement_count": _as_int(latest_cycle.get("explicit_settlement_count"), 0) if latest_cycle else 0,
        "outcomes_persisted": _as_int(latest_cycle.get("outcomes_persisted"), 0) if latest_cycle else 0,
        "next_suggested_recheck_time": latest_cycle.get("next_suggested_recheck_time") if latest_cycle else None,
        "latest_cycle": latest_summary,
        "daily_report_available": bool(daily_loaded.get("ok")),
        "daily_report_path": str(daily_path),
        "recent_cycle_ids": [cycle.get("cycle_id") for _, cycle, _ in item_cycles[:6]],
        "recommended_action": classification.get("recommended_action"),
        "storage_status": storage,
        "provider_write": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _summarize_calibration(payload: dict[str, Any]) -> dict[str, Any]:
    matched = _as_int(payload.get("matched_outcomes_count") or payload.get("matched_outcome_count"), 0)
    outcome_records = _as_int(payload.get("outcome_records_count") or payload.get("total_count"), 0)
    status = str(payload.get("status") or payload.get("calibration_status") or ("insufficient_data" if matched <= 0 else "unknown"))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": status,
        "paper_decisions_count": _as_int(payload.get("paper_decisions_count"), 0),
        "outcome_records_count": outcome_records,
        "matched_outcomes_count": matched,
        "unmatched_outcomes_count": _as_int(payload.get("unmatched_outcomes_count") or payload.get("unmatched_outcome_count"), 0),
        "coverage_rate": _as_float(payload.get("coverage_rate"), 0.0),
        "insufficient_sample": matched < 30 or status == "insufficient_data" or "insufficient_sample" in list(payload.get("warnings") or []),
        "next_required_data": list(payload.get("next_required_data") or (["settlement_results"] if matched <= 0 else [])),
        "progress_to_100": _progress(matched, 100),
        "progress_to_300": _progress(matched, 300),
        "progress_to_1000": _progress(matched, 1000),
        "safety_flags": _extract_safety_fields(payload),
        "raw_payload_included": False,
        "secrets_included": False,
    }


def check_calibration_status(base_url: str | None = None) -> dict[str, Any]:
    if base_url:
        result = safe_get_json(_join_url(base_url, "/api/automation/calibration"))
        if not result.get("ok"):
            return {
                "ok": False,
                "status": result.get("status"),
                "error_category": result.get("error_category"),
                "status_code": result.get("status_code"),
                "next_required_data": ["settlement_results"],
                "raw_payload_included": False,
                "secrets_included": False,
            }
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        return _summarize_calibration(data)
    try:
        from .calibration import build_calibration_report

        payload = build_calibration_report(base_data_dir=str(get_automation_data_dir()), write_report=False)
        return _summarize_calibration(_sanitize_payload(payload))
    except Exception as exc:
        return {"ok": False, "status": "code_defect", "error": _safe_error(exc), "next_required_data": ["settlement_results"], "raw_payload_included": False, "secrets_included": False}


def _summarize_datasources(payload: dict[str, Any]) -> dict[str, Any]:
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    enabled_count = sum(1 for source in sources if isinstance(source, dict) and source.get("enabled") is True)
    return {
        "ok": bool(payload.get("ok", True)),
        "status": str(payload.get("status") or "ok"),
        "total_lanes": _as_int(payload.get("total_lanes"), 0),
        "total_sources": _as_int(payload.get("total_sources"), len(sources)),
        "source_enabled_count": _as_int(payload.get("enabled_source_count") or payload.get("source_enabled_count"), enabled_count),
        "needs_terms_review_count": _as_int(payload.get("needs_terms_review_count"), 0),
        "future_source_candidate_count": _as_int(payload.get("future_source_candidate_count"), 0),
        "safety_flags": _extract_safety_fields(payload),
        "provider_write": False if payload.get("provider_write") is None else bool(payload.get("provider_write")),
        "execution_allowed": False if payload.get("execution_allowed") is None else bool(payload.get("execution_allowed")),
        "raw_payload_included": False,
        "secrets_included": False,
    }


def check_data_source_registry(base_url: str | None = None) -> dict[str, Any]:
    if base_url:
        health = safe_get_json(_join_url(base_url, "/api/automation/data-sources/health"))
        registry = safe_get_json(_join_url(base_url, "/api/automation/data-sources/registry"))
        coverage = safe_get_json(_join_url(base_url, "/api/automation/data-sources/coverage"))
        if not health.get("ok"):
            return {"ok": False, "status": health.get("status"), "error_category": health.get("error_category"), "raw_payload_included": False, "secrets_included": False}
        summary = _summarize_datasources(health.get("data") if isinstance(health.get("data"), dict) else {})
        summary["registry_endpoint_status"] = registry.get("status")
        summary["coverage_endpoint_status"] = coverage.get("status")
        summary["registry_endpoint_ok"] = bool(registry.get("ok"))
        summary["coverage_endpoint_ok"] = bool(coverage.get("ok"))
        return summary
    try:
        from . import get_data_source_coverage_snapshot, get_data_source_registry_health, get_data_source_registry_snapshot

        health = get_data_source_registry_health()
        registry = get_data_source_registry_snapshot()
        coverage = get_data_source_coverage_snapshot()
        summary = _summarize_datasources(_sanitize_payload({**registry, **health}))
        summary["coverage_status"] = "ok" if isinstance(coverage, dict) else "unknown"
        return summary
    except Exception as exc:
        return {"ok": False, "status": "code_defect", "error": _safe_error(exc), "raw_payload_included": False, "secrets_included": False}


def check_safety_flags(payloads: list[Any] | tuple[Any, ...] | Any) -> dict[str, Any]:
    payload_list = list(payloads) if isinstance(payloads, (list, tuple)) else [payloads]
    observed: dict[str, list[Any]] = {key: [] for key in (*FALSE_SAFETY_FLAGS, *ZERO_SAFETY_FLAGS, *TRUE_SAFETY_FLAGS)}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                if key_text in observed:
                    observed[key_text].append(item)
                if not key_text.startswith("_") and not _is_raw_payload_key(key_text):
                    walk(item)
        elif isinstance(value, list):
            for item in value[:100]:
                walk(item)

    for payload in payload_list:
        walk(payload)

    critical: list[str] = []
    warnings: list[str] = []
    for key in FALSE_SAFETY_FLAGS:
        values = observed[key]
        if not values:
            warnings.append(f"{key}_missing")
        elif any(_bool_is_true(value) for value in values):
            critical.append(f"{key}_enabled")
    for key in ZERO_SAFETY_FLAGS:
        values = observed[key]
        if not values:
            warnings.append(f"{key}_missing")
        elif any(_as_int(value, 0) != 0 for value in values):
            critical.append(f"{key}_nonzero")
    for key in TRUE_SAFETY_FLAGS:
        values = observed[key]
        if not values:
            warnings.append(f"{key}_missing")
        elif any(_bool_is_false(value) for value in values):
            critical.append(f"{key}_disabled")

    return {
        "ok": not critical,
        "status": "ok" if not critical else "safety_failure",
        "critical": sorted(set(critical)),
        "warnings": sorted(set(warnings)),
        "observed_flags": {key: bool(values) for key, values in observed.items()},
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
        "human_approval_required": True,
        "paper_only": True,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _storage_problem(storage: dict[str, Any] | None) -> bool:
    if not isinstance(storage, dict):
        return False
    if not storage.get("read_ok") or not storage.get("write_ok"):
        return True
    if _is_render_runtime():
        data_dir = str(storage.get("data_dir") or "").replace("\\", "/")
        if storage.get("configured") and not data_dir.startswith("/var/data"):
            return True
    return bool(storage.get("persistence_warning") and _is_render_runtime())


def classify_blockers(report: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    safety = report.get("safety_status") if isinstance(report.get("safety_status"), dict) else {}
    if safety and not safety.get("ok", True):
        blockers.append({"type": "safety_failure", "severity": "critical", "detail": ",".join(safety.get("critical") or [])})
    local = report.get("local_status") if isinstance(report.get("local_status"), dict) else {}
    if local and local.get("status") == "code_defect":
        blockers.append({"type": "code_defect", "severity": "critical", "detail": "local import or baseline check failed"})

    storage = report.get("storage_status") if isinstance(report.get("storage_status"), dict) else None
    if _storage_problem(storage):
        blockers.append({"type": "storage_problem", "severity": "critical", "detail": "storage read/write or Render /var/data configuration failed"})

    render = report.get("render_status") if isinstance(report.get("render_status"), dict) else {}
    render_status = str(render.get("status") or "")
    if render_status == "local_sandbox_network_unavailable":
        blockers.append({"type": "local_sandbox_network_unavailable", "severity": "warning", "detail": "network unavailable from this runtime"})
    elif render_status == "render_auth_problem":
        blockers.append({"type": "render_auth_problem", "severity": "critical", "detail": "Render endpoint authentication failed"})
    elif render_status in {"render_endpoint_failure", "missing_endpoint"}:
        blockers.append({"type": "render_endpoint_failure", "severity": "critical", "detail": render_status})

    cron = report.get("cron_status") if isinstance(report.get("cron_status"), dict) else {}
    if cron:
        cron_state = str(cron.get("status") or "")
        if cron_state == "running_but_provider_limited" or _as_int(cron.get("repeated_http_429_count"), 0) > 0:
            blockers.append({"type": "provider_rate_limit", "severity": "warning", "detail": "http_429 in collector reports"})
        elif cron_state in {"cron_not_detected", "endpoint_auth_problem"}:
            blockers.append({"type": cron_state, "severity": "critical", "detail": "cron reports unavailable or auth failed"})

    calibration = report.get("calibration_status") if isinstance(report.get("calibration_status"), dict) else {}
    calibration_state = str(calibration.get("status") or "")
    if calibration and calibration_state not in {"not_run", "skipped_config_missing"} and calibration.get("ok") is not None and _as_int(calibration.get("matched_outcomes_count"), 0) <= 0:
        blockers.append({"type": "insufficient_settlement_data", "severity": "warning", "detail": "no matched outcomes available"})

    if not blockers:
        primary = "verification_ok"
        action = "continue using ops workflow checks"
    else:
        critical = [item for item in blockers if item.get("severity") == "critical"]
        primary = critical[0]["type"] if critical else blockers[0]["type"]
        if primary == "provider_rate_limit":
            action = "keep schedule */30, keep or reduce payload, do not manually spam runs"
        elif primary == "insufficient_settlement_data":
            action = "wait for explicit settlement results before judging calibration"
        elif primary == "local_sandbox_network_unavailable":
            action = "rerun Render check from a network-enabled environment or use dashboard logs"
        elif primary == "storage_problem":
            action = "fix AUTOMATION_DATA_DIR and Render persistent disk configuration"
        elif primary == "safety_failure":
            action = "stop and fix enabled execution/provider-write flags"
        else:
            action = "inspect the classified failing check and fix the reported defect"
    return {
        "primary": primary,
        "blockers": blockers,
        "has_critical": any(item.get("severity") == "critical" for item in blockers),
        "recommended_action": action,
    }


def _markdown_report(report: dict[str, Any]) -> str:
    blocker = report.get("blocker_classification") or {}
    storage = report.get("storage_status") or {}
    cron = report.get("cron_status") or {}
    calibration = report.get("calibration_status") or {}
    lines = [
        f"# Ops Check {report.get('run_id')}",
        "",
        f"- mode: {report.get('mode')}",
        f"- started_at: {report.get('started_at')}",
        f"- completed_at: {report.get('completed_at')}",
        f"- blocker: {blocker.get('primary')}",
        f"- recommended_action: {blocker.get('recommended_action')}",
        f"- storage_data_dir: {storage.get('data_dir')}",
        f"- storage_read_ok: {storage.get('read_ok')}",
        f"- storage_write_ok: {storage.get('write_ok')}",
        f"- cron_status: {cron.get('status')}",
        f"- latest_cycle_id: {cron.get('latest_cycle_id')}",
        f"- matched_outcomes_count: {calibration.get('matched_outcomes_count')}",
        f"- raw_payload_included: {report.get('raw_payload_included')}",
        f"- secrets_included: {report.get('secrets_included')}",
        "",
    ]
    return "\n".join(lines)


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def write_ops_report(report: dict[str, Any]) -> dict[str, Any]:
    safe_report = _sanitize_payload({**report, "raw_payload_included": False, "secrets_included": False})
    run_id = str(safe_report.get("run_id") or f"ops_{uuid.uuid4().hex[:12]}")
    started = _parse_time(str(safe_report.get("started_at") or "")) or datetime.now(timezone.utc)
    day = started.date().isoformat()
    root = get_runtime_data_path("ops_checks")
    latest_path = root / "latest.json"
    item_path = root / "items" / f"{run_id}.json"
    daily_json_path = root / "daily" / f"{day}.json"
    daily_md_path = root / "daily" / f"{day}.md"
    paths = {
        "latest": str(latest_path),
        "item": str(item_path),
        "daily_json": str(daily_json_path),
        "daily_markdown": str(daily_md_path),
    }
    safe_report["report_paths"] = paths
    _atomic_write_json(item_path, safe_report)
    _atomic_write_json(latest_path, safe_report)
    _atomic_write_json(daily_json_path, safe_report)
    daily_md_path.parent.mkdir(parents=True, exist_ok=True)
    daily_md_path.write_text(_markdown_report(safe_report), encoding="utf-8")
    return {"ok": True, "status": "ok", "paths": paths, "raw_payload_included": False, "secrets_included": False}


def _base_safety_payload() -> dict[str, Any]:
    return {
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
        "human_approval_required": True,
        "paper_only": True,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def run_ops_check(
    *,
    mode: str = "local",
    base_url: str | None = None,
    timeout: int = 20,
    skip_network: bool = False,
    write_report: bool = False,
) -> dict[str, Any]:
    started_at = utc_now_iso()
    run_id = f"ops_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    mode = (mode or "local").strip().lower()
    config = get_ops_config()
    resolved_base_url = (base_url or config.get("app_base_url") or "").strip()
    context = detect_runtime_context()
    report: dict[str, Any] = {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": None,
        "mode": mode,
        "runtime_context": context,
        "git_branch": context.get("git_branch"),
        "git_head": context.get("git_head"),
        "dirty_worktree": context.get("dirty_worktree"),
        "python_version": context.get("python_version"),
        "platform": context.get("platform"),
        "app_base_url": resolved_base_url or None,
        "network_available": None if not skip_network else False,
        "storage_status": config.get("storage"),
        "render_status": {"ok": None, "status": "not_run"},
        "cron_status": {"ok": None, "status": "not_run"},
        "calibration_status": {"ok": None, "status": "not_run"},
        "datasource_status": {"ok": None, "status": "not_run"},
        "safety_status": {"ok": None, "status": "not_run"},
        "test_status": {"ok": None, "status": "not_run"},
        "raw_payload_included": False,
        "secrets_included": False,
    }
    safety_payloads: list[Any] = [_base_safety_payload()]

    if mode in {"local", "full"}:
        local_status = check_local_environment()
        report["local_status"] = local_status
        report["storage_status"] = local_status.get("storage_status") or report["storage_status"]
        safety_payloads.append(local_status)
    if mode in {"render", "full"}:
        if skip_network:
            report["render_status"] = {"ok": False, "status": "local_sandbox_network_unavailable", "skipped": True}
        elif not resolved_base_url:
            if mode == "render":
                report["render_status"] = {"ok": False, "status": "config_missing", "errors": ["APP_BASE_URL_missing"]}
            else:
                report["render_status"] = {"ok": None, "status": "skipped_config_missing", "errors": ["APP_BASE_URL_missing"]}
        else:
            render_status = check_render_endpoints(resolved_base_url, timeout=timeout)
            report["render_status"] = render_status
            report["network_available"] = render_status.get("status") != "local_sandbox_network_unavailable"
            safety_payloads.extend(render_status.get("safety_payloads") or [])
    if mode in {"cron", "full"}:
        cron_status = check_cron_reports()
        report["cron_status"] = cron_status
        safety_payloads.append(cron_status)
    if mode in {"calibration", "full"}:
        calibration_base = None if skip_network or not resolved_base_url else resolved_base_url
        calibration_status = check_calibration_status(calibration_base)
        report["calibration_status"] = calibration_status
        safety_payloads.append(calibration_status)
    if mode in {"datasources", "full"}:
        datasource_base = None if skip_network or not resolved_base_url else resolved_base_url
        datasource_status = check_data_source_registry(datasource_base)
        report["datasource_status"] = datasource_status
        safety_payloads.append(datasource_status)
    if mode in {"safety", "full", "local", "render", "cron", "calibration", "datasources"}:
        report["safety_status"] = check_safety_flags(safety_payloads)

    report["completed_at"] = utc_now_iso()
    report["blocker_classification"] = classify_blockers(report)
    report["recommended_action"] = report["blocker_classification"].get("recommended_action")
    if write_report:
        report["ops_report_write"] = write_ops_report(report)
    return _sanitize_payload(report)
