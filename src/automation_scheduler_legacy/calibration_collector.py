from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from .calibration import build_calibration_report
from .data_paths import get_storage_health, resolve_base_data_dir
from .deepseek_reviewer import run_deepseek_review
from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter
from .outcome_store import ingest_outcome_records, load_outcome_records
from .paper_decision_ledger import LEDGER_SCHEMA_VERSION, create_paper_decision_record, load_paper_decisions
from .review_queue import build_review_item, load_review_queue_state, persist_review_queue_snapshot, summarize_review_items
from .scheduler_config import SCHEMA_VERSION, ensure_runtime_directories, get_default_scheduler_config, safe_run_id, sanitize_filename, utc_now_iso
from .scheduler_runner import _evaluate_kalshi_review_candidates
from src.services.settlement_service import classify_kalshi_settlement, discover_kalshi_settlements_for_pending_rows

COLLECTOR_SCHEMA_VERSION = f"{SCHEMA_VERSION}.kalshi_calibration_collector.v1"
DEFAULT_PUBLIC_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
KALSHI_PROVIDER = "kalshi_prediction_market"
WATCHLIST_BUCKETS = ("short_term", "medium_term", "long_term", "unresolved")
SAFE_STATUS_VALUES = {"active", "open", "initialized", "trading"}
SETTLED_CLASSIFICATIONS = {"settled_yes", "settled_no", "void_or_cancelled"}
DEFAULT_DAILY_NEW_CONTRACT_TARGET = 250
DEFAULT_DAILY_NEW_CONTRACT_HARD_CAP = 500
DEFAULT_MAX_NEW_CONTRACTS_PER_CYCLE = 50
DEFAULT_MAX_MARKETS_SCANNED_PER_CYCLE = 25000
DEFAULT_ACTIVE_UNRESOLVED_WATCHLIST_LIMIT = 1000
DEFAULT_CLOSED_UNKNOWN_BACKLOG_LIMIT = 500
LOWER_LIQUIDITY_TIERS = {"missing", "unknown", "very_low_liquidity", "low_liquidity", "very_low", "low"}
UNUSABLE_PRICING_VALUES = {"missing", "unusable", "invalid", "unknown"}
VALUATION_FIELDS = (
    "liquidity_score",
    "spread_score",
    "pricing_quality_score",
    "close_time_score",
    "market_structure_score",
    "risk_score",
    "confidence_score",
    "review_priority_score",
)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


def collector_policy_from_env() -> dict[str, Any]:
    configured_hard_cap = max(1, _env_int("KALSHI_CALIBRATION_MAX_DAILY_NEW_CONTRACTS_HARD_CAP", DEFAULT_DAILY_NEW_CONTRACT_HARD_CAP))
    legacy_daily_target = _env_int("KALSHI_CALIBRATION_MAX_NEW_CONTRACTS_PER_DAY", DEFAULT_DAILY_NEW_CONTRACT_TARGET)
    target_daily = _env_int("KALSHI_CALIBRATION_TARGET_DAILY_NEW_CONTRACTS", legacy_daily_target)
    target_daily = max(0, min(target_daily, configured_hard_cap))
    per_cycle = max(1, min(_env_int("KALSHI_CALIBRATION_MAX_NEW_CONTRACTS_PER_CYCLE", DEFAULT_MAX_NEW_CONTRACTS_PER_CYCLE), configured_hard_cap))
    return {
        "collector_enabled": _env_bool("KALSHI_CALIBRATION_COLLECTOR_ENABLED", True),
        "max_markets_scanned_per_cycle": max(1, _env_int("KALSHI_CALIBRATION_MAX_MARKETS_SCANNED_PER_CYCLE", DEFAULT_MAX_MARKETS_SCANNED_PER_CYCLE)),
        "max_new_contracts_per_cycle": per_cycle,
        "target_daily_new_contracts": target_daily,
        "hard_cap_daily_new_contracts": configured_hard_cap,
        "max_new_contracts_per_day": target_daily,
        "recheck_interval_minutes": _env_int("KALSHI_CALIBRATION_RECHECK_INTERVAL_MINUTES", 15),
        "fast_recheck_interval_minutes": _env_int("KALSHI_CALIBRATION_FAST_RECHECK_INTERVAL_MINUTES", 5),
        "max_recheck_hours_after_close": _env_int("KALSHI_CALIBRATION_MAX_RECHECK_HOURS_AFTER_CLOSE", 72),
        "short_term_window_hours": _env_int("KALSHI_CALIBRATION_SHORT_TERM_WINDOW_HOURS", 48),
        "medium_term_window_days": _env_int("KALSHI_CALIBRATION_MEDIUM_TERM_WINDOW_DAYS", 14),
        "long_term_window_days": _env_int("KALSHI_CALIBRATION_LONG_TERM_WINDOW_DAYS", 60),
        "min_target_outcomes": _env_int("KALSHI_CALIBRATION_MIN_TARGET_OUTCOMES", 30),
        "good_target_outcomes": _env_int("KALSHI_CALIBRATION_GOOD_TARGET_OUTCOMES", 100),
        "strong_target_outcomes": _env_int("KALSHI_CALIBRATION_STRONG_TARGET_OUTCOMES", 300),
        "long_term_target_outcomes": _env_int("KALSHI_CALIBRATION_LONG_TERM_TARGET_OUTCOMES", 1000),
        "short_term_allocation": 0.80,
        "medium_term_allocation": 0.15,
        "long_term_allocation": 0.05,
        "exploration_sample_fraction": 0.10,
        "min_pricing_quality_score": float(_env_int("KALSHI_CALIBRATION_MIN_PRICING_QUALITY_SCORE", 1)),
        "max_active_unresolved_watchlist": _env_int("KALSHI_CALIBRATION_MAX_ACTIVE_UNRESOLVED_WATCHLIST", DEFAULT_ACTIVE_UNRESOLVED_WATCHLIST_LIMIT),
        "max_closed_unknown_backlog": _env_int("KALSHI_CALIBRATION_MAX_CLOSED_UNKNOWN_BACKLOG", DEFAULT_CLOSED_UNKNOWN_BACKLOG_LIMIT),
        "public_base_url": os.getenv("KALSHI_PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL).strip().rstrip("/"),
        "public_page_limit": min(1000, max(1, _env_int("KALSHI_CALIBRATION_PUBLIC_PAGE_LIMIT", 1000))),
        "request_timeout_seconds": max(1, _env_int("KALSHI_CALIBRATION_REQUEST_TIMEOUT_SECONDS", 12)),
        "lock_stale_minutes": max(5, _env_int("KALSHI_CALIBRATION_LOCK_STALE_MINUTES", 10)),
        "adaptive_throttle_enabled": _env_bool("KALSHI_CALIBRATION_ADAPTIVE_THROTTLE", True),
    }


def _insufficient_sample(calibration: dict[str, Any], policy: dict[str, Any]) -> bool:
    matched = int(calibration.get("matched_outcomes_count", 0) or 0)
    min_target = int(policy.get("min_target_outcomes", 30) or 30)
    warnings = set(str(item) for item in list(calibration.get("warnings", [])))
    return matched < min_target or "insufficient_sample" in warnings


def _collector_root(base_data_dir: str) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "collector_scheduler"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _watchlist_root(base_data_dir: str) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "collector_scheduler" / "watchlists"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _project_relative(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _market_key(row: dict[str, Any]) -> str | None:
    for field in ("ticker", "contract_id", "market_id"):
        value = row.get(field)
        if value:
            return str(value).strip()
    return None


def _score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _avg(values: list[float]) -> float:
    clean = [float(value) for value in values if value is not None]
    return round(sum(clean) / len(clean), 4) if clean else 0.0


def _progress(total: int, target: int) -> dict[str, Any]:
    target = max(1, int(target))
    total = max(0, int(total))
    return {
        "count": total,
        "target": target,
        "remaining": max(0, target - total),
        "pct": round(min(1.0, total / target), 4),
    }


def _safe_list(value: Any, limit: int = 25) -> list[Any]:
    return list(value or [])[:limit] if isinstance(value, list) else []


def _compact_contract(row: dict[str, Any], *, bucket: str | None = None) -> dict[str, Any]:
    compact = {
        "provider": row.get("provider") or row.get("provider_id") or KALSHI_PROVIDER,
        "market_type": row.get("market_type") or "prediction_market",
        "ticker": row.get("ticker"),
        "contract_id": row.get("contract_id"),
        "event_id": row.get("event_id"),
        "contract_title": row.get("contract_title") or row.get("selection"),
        "close_time": row.get("close_time") or row.get("market_close_at"),
        "collector_bucket": bucket or row.get("collector_bucket"),
        "liquidity_score": row.get("liquidity_score"),
        "spread_score": row.get("spread_score"),
        "pricing_quality_score": row.get("pricing_quality_score"),
        "close_time_score": row.get("close_time_score"),
        "market_structure_score": row.get("market_structure_score"),
        "risk_score": row.get("risk_score"),
        "confidence_score": row.get("confidence_score"),
        "review_priority_score": row.get("review_priority_score"),
        "liquidity_tier": row.get("liquidity_tier"),
        "exploration_sample": bool(row.get("exploration_sample", False)),
        "exploration_reason": row.get("exploration_reason"),
        "reason_codes": _safe_list(row.get("reason_codes"), 10),
        "implied_probability": row.get("implied_probability"),
        "observed_price": row.get("observed_price") if row.get("observed_price") is not None else row.get("yes_price"),
        "yes_price": row.get("yes_price"),
        "no_price": row.get("no_price"),
        "price_source": row.get("price_source"),
        "pricing_quality": row.get("pricing_quality"),
        "execution_allowed": False,
        "paper_only": True,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "human_approval_required": True,
    }
    return {key: value for key, value in compact.items() if value is not None}


def _watchlist_path(base_data_dir: str, bucket: str) -> Path:
    return _watchlist_root(base_data_dir) / f"{bucket}.latest.json"


def _load_watchlist(base_data_dir: str, bucket: str) -> list[dict[str, Any]]:
    payload = _read_json(_watchlist_path(base_data_dir, bucket))
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [row for row in payload["items"] if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def load_all_watchlists(base_data_dir: str = "data") -> dict[str, list[dict[str, Any]]]:
    return {bucket: _load_watchlist(base_data_dir, bucket) for bucket in WATCHLIST_BUCKETS}


def _write_watchlist(base_data_dir: str, bucket: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(items, key=lambda row: (str(row.get("close_time") or ""), str(_market_key(row) or "")))
    wrapper = {
        "schema_version": COLLECTOR_SCHEMA_VERSION,
        "storage_backend": "file",
        "last_updated_at": utc_now_iso(),
        "bucket": bucket,
        "count": len(ordered),
        "provider_write": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "items": ordered,
    }
    path = _watchlist_path(base_data_dir, bucket)
    _atomic_write_json(path, wrapper)
    return {"path": _project_relative(base_data_dir, path), "count": len(ordered)}


def _load_completed_index(base_data_dir: str) -> dict[str, Any]:
    path = _watchlist_root(base_data_dir) / "settled_completed.index.json"
    payload = _read_json(path)
    if isinstance(payload, dict):
        return payload
    return {
        "schema_version": COLLECTOR_SCHEMA_VERSION,
        "last_updated_at": None,
        "completed_tickers": [],
        "items": [],
    }


def _write_completed_index(base_data_dir: str, completed_items: list[dict[str, Any]]) -> dict[str, Any]:
    existing = _load_completed_index(base_data_dir)
    by_key: dict[str, dict[str, Any]] = {}
    for row in list(existing.get("items") or []):
        if isinstance(row, dict) and _market_key(row):
            by_key[str(_market_key(row))] = row
    for row in completed_items:
        key = _market_key(row)
        if key:
            by_key[str(key)] = row
    items = sorted(by_key.values(), key=lambda row: str(row.get("settled_at") or row.get("last_checked_at") or ""))
    payload = {
        "schema_version": COLLECTOR_SCHEMA_VERSION,
        "last_updated_at": utc_now_iso(),
        "count": len(items),
        "completed_tickers": sorted(by_key),
        "items": items,
        "provider_write": False,
    }
    path = _watchlist_root(base_data_dir) / "settled_completed.index.json"
    _atomic_write_json(path, payload)
    return {"path": _project_relative(base_data_dir, path), "count": len(items)}


def _daily_path(base_data_dir: str, day: str) -> Path:
    return _collector_root(base_data_dir) / "daily" / f"{day}.json"


def _load_daily_state(base_data_dir: str, day: str) -> dict[str, Any]:
    payload = _read_json(_daily_path(base_data_dir, day))
    if isinstance(payload, dict):
        payload.setdefault("sampled_tickers", [])
        policy = collector_policy_from_env()
        payload.setdefault("daily_new_contract_target", int(policy["target_daily_new_contracts"]))
        payload.setdefault("daily_new_contract_hard_cap", int(policy["hard_cap_daily_new_contracts"]))
        payload.setdefault("daily_new_contract_limit", int(policy["target_daily_new_contracts"]))
        payload.setdefault("new_contracts_added_today", int(payload.get("new_contracts_added", 0) or 0))
        payload.setdefault("daily_remaining_capacity", max(0, int(payload.get("daily_new_contract_target", 0) or 0) - len(payload.get("sampled_tickers") or [])))
        return payload
    policy = collector_policy_from_env()
    return {
        "schema_version": COLLECTOR_SCHEMA_VERSION,
        "date": day,
        "cycles_run": 0,
        "markets_scanned": 0,
        "eligible_contracts_found": 0,
        "selected_short_term": 0,
        "selected_medium_term": 0,
        "selected_long_term": 0,
        "new_contracts_added": 0,
        "daily_new_contract_target": int(policy["target_daily_new_contracts"]),
        "daily_new_contract_hard_cap": int(policy["hard_cap_daily_new_contracts"]),
        "daily_new_contract_limit": int(policy["target_daily_new_contracts"]),
        "daily_new_contracts_remaining": int(policy["target_daily_new_contracts"]),
        "new_contracts_added_today": 0,
        "daily_remaining_capacity": int(policy["target_daily_new_contracts"]),
        "sampled_tickers": [],
        "records_checked": 0,
        "records_rechecked_today": 0,
        "explicit_settlement_count": 0,
        "settled_yes_count": 0,
        "settled_no_count": 0,
        "void_cancelled_count": 0,
        "unknown_count": 0,
        "not_settled_count": 0,
        "outcomes_persisted": 0,
        "outcomes_persisted_today": 0,
        "duplicate_outcomes_skipped": 0,
        "exploration_sample_count": 0,
        "quality_gate_rejection_count": 0,
        "duplicate_contracts_skipped": 0,
        "liquidity_tier_counts": {},
        "liquidity_score_sum": 0.0,
        "pricing_quality_score_sum": 0.0,
        "quality_sample_count": 0,
        "average_liquidity_score": 0.0,
        "average_pricing_quality_score": 0.0,
        "provider_write": False,
        "execution_allowed_count": 0,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
    }


def _write_daily_markdown(base_data_dir: str, daily: dict[str, Any]) -> str:
    path = _collector_root(base_data_dir) / "daily" / f"{daily['date']}.md"
    lines = [
        f"# Kalshi Calibration Collector {daily['date']}",
        "",
        f"- cycles_run: {daily.get('cycles_run', 0)}",
        f"- markets_scanned: {daily.get('markets_scanned', 0)}",
        f"- eligible_contracts_found: {daily.get('eligible_contracts_found', 0)}",
        f"- daily_new_contract_target: {daily.get('daily_new_contract_target', daily.get('daily_new_contract_limit', 0))}",
        f"- daily_new_contract_hard_cap: {daily.get('daily_new_contract_hard_cap', 0)}",
        f"- new_contracts_added: {daily.get('new_contracts_added', 0)}",
        f"- daily_remaining_capacity: {daily.get('daily_remaining_capacity', daily.get('daily_new_contracts_remaining', 0))}",
        f"- selected_short_term: {daily.get('selected_short_term', 0)}",
        f"- selected_medium_term: {daily.get('selected_medium_term', 0)}",
        f"- selected_long_term: {daily.get('selected_long_term', 0)}",
        f"- unresolved_count: {daily.get('unresolved_count', 0)}",
        f"- closed_unknown: {daily.get('closed_unknown', 0)}",
        f"- stale_unknown: {daily.get('stale_unknown', 0)}",
        f"- recheck_due_now: {daily.get('recheck_due_now', 0)}",
        f"- next_suggested_recheck_time: {daily.get('next_suggested_recheck_time')}",
        f"- explicit_settlement_count: {daily.get('explicit_settlement_count', 0)}",
        f"- outcomes_persisted: {daily.get('outcomes_persisted', 0)}",
        f"- total_outcome_records_count: {daily.get('total_outcome_records_count', 0)}",
        f"- matched_outcomes_count: {daily.get('matched_outcomes_count', 0)}",
        f"- calibration_status: {daily.get('calibration_status')}",
        f"- coverage_rate: {daily.get('coverage_rate')}",
        f"- next_required_data: {', '.join(daily.get('next_required_data') or [])}",
        "",
        "Safety: provider_write=false, execution_allowed_count=0, auto_execution_enabled=false, kalshi_order_execution_enabled=false.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return _project_relative(base_data_dir, path)


def write_daily_report(base_data_dir: str = "data", *, day: str | None = None, calibration_report: dict[str, Any] | None = None) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    day = day or datetime.now(timezone.utc).date().isoformat()
    daily = _load_daily_state(base_data_dir, day)
    watchlists = load_all_watchlists(base_data_dir)
    unresolved = list(watchlists.get("unresolved", []))
    outcomes = load_outcome_records(base_data_dir)
    calibration = calibration_report or build_calibration_report(base_data_dir=base_data_dir, write_report=True)
    policy = collector_policy_from_env()
    backlog = _watchlist_backlog_summary(base_data_dir, policy)
    target = int(daily.get("daily_new_contract_target", policy["target_daily_new_contracts"]) or policy["target_daily_new_contracts"])
    hard_cap = int(daily.get("daily_new_contract_hard_cap", policy["hard_cap_daily_new_contracts"]) or policy["hard_cap_daily_new_contracts"])
    sampled_count = len(daily.get("sampled_tickers") or [])
    total_outcomes = len(outcomes)
    quality_count = int(daily.get("quality_sample_count", 0) or 0)
    average_liquidity = round(float(daily.get("liquidity_score_sum", 0.0) or 0.0) / quality_count, 4) if quality_count else float(daily.get("average_liquidity_score", 0.0) or 0.0)
    average_pricing = round(float(daily.get("pricing_quality_score_sum", 0.0) or 0.0) / quality_count, 4) if quality_count else float(daily.get("average_pricing_quality_score", 0.0) or 0.0)
    storage_health = get_storage_health()
    daily.update(
        {
            "watchlist_size": sum(len(watchlists.get(bucket, [])) for bucket in ("short_term", "medium_term", "long_term")),
            "short_term_watchlist_count": len(watchlists.get("short_term", [])),
            "medium_term_watchlist_count": len(watchlists.get("medium_term", [])),
            "long_term_watchlist_count": len(watchlists.get("long_term", [])),
            "unresolved_count": len(unresolved),
            "daily_new_contract_target": target,
            "daily_new_contract_hard_cap": hard_cap,
            "new_contracts_added_today": int(daily.get("new_contracts_added", 0) or 0),
            "daily_remaining_capacity": max(0, target - sampled_count),
            "records_rechecked_today": int(daily.get("records_checked", 0) or 0),
            "outcomes_persisted_today": int(daily.get("outcomes_persisted", 0) or 0),
            "total_outcome_records_count": total_outcomes,
            "matched_outcomes_count": int(calibration.get("matched_outcomes_count", 0)),
            "progress_to_100": _progress(total_outcomes, 100),
            "progress_to_300": _progress(total_outcomes, 300),
            "progress_to_1000": _progress(total_outcomes, 1000),
            "settlement_backlog": backlog,
            "unresolved_open": int(backlog.get("unresolved_open", 0)),
            "closed_unknown": int(backlog.get("closed_unknown", 0)),
            "not_settled": int(backlog.get("not_settled", 0)),
            "stale_unknown": int(backlog.get("stale_unknown", 0)),
            "recheck_due_now": int(backlog.get("recheck_due_now", 0)),
            "next_suggested_recheck_time": backlog.get("next_suggested_recheck_time"),
            "average_liquidity_score": average_liquidity,
            "average_pricing_quality_score": average_pricing,
            "liquidity_tier_counts": dict(daily.get("liquidity_tier_counts", {})),
            "exploration_sample_count": int(daily.get("exploration_sample_count", 0) or 0),
            "duplicate_skipped_count": int(daily.get("duplicate_contracts_skipped", 0) or 0),
            "quality_gate_rejection_count": int(daily.get("quality_gate_rejection_count", 0) or 0),
            "calibration_status": calibration.get("status"),
            "coverage_rate": float(calibration.get("coverage_rate", 0.0)),
            "insufficient_sample": _insufficient_sample(calibration, policy),
            "next_required_data": list(calibration.get("next_required_data", [])),
            "storage_backend": "file",
            "storage_health": storage_health,
            "persistence_warning_if_ephemeral": storage_health.get("persistence_warning"),
            "provider_write": False,
            "execution_allowed_count": 0,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
        }
    )
    json_path = _daily_path(base_data_dir, day)
    _atomic_write_json(json_path, daily)
    md_path = _write_daily_markdown(base_data_dir, daily)
    daily["daily_report_path"] = _project_relative(base_data_dir, json_path)
    daily["daily_markdown_path"] = md_path
    return daily


def _lock_path(base_data_dir: str) -> Path:
    return _collector_root(base_data_dir) / "collector.lock"


def _acquire_lock(base_data_dir: str, *, stale_minutes: int) -> dict[str, Any]:
    path = _lock_path(base_data_dir)
    now = datetime.now(timezone.utc)
    if path.exists():
        payload = _read_json(path)
        created = _parse_time((payload or {}).get("created_at")) if isinstance(payload, dict) else None
        if created and now - created <= timedelta(minutes=stale_minutes):
            return {"lock_acquired": False, "skipped_due_to_lock": True, "lock_path": _project_relative(base_data_dir, path)}
        try:
            path.unlink()
        except OSError:
            return {"lock_acquired": False, "skipped_due_to_lock": True, "lock_path": _project_relative(base_data_dir, path)}
    payload = {"created_at": utc_now_iso(), "pid": os.getpid()}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle)
    except FileExistsError:
        return {"lock_acquired": False, "skipped_due_to_lock": True, "lock_path": _project_relative(base_data_dir, path)}
    return {"lock_acquired": True, "skipped_due_to_lock": False, "lock_path": _project_relative(base_data_dir, path)}


def _release_lock(base_data_dir: str) -> None:
    try:
        _lock_path(base_data_dir).unlink()
    except OSError:
        pass


def _normalize_records(records: list[dict[str, Any]], adapter: KalshiReadonlyAdapter) -> list[dict[str, Any]]:
    normalized = []
    for row in records:
        if not isinstance(row, dict):
            continue
        if row.get("provider_id") == KALSHI_PROVIDER and row.get("schema_version"):
            normalized.append(dict(row))
        else:
            normalized.append(adapter.normalize_payload(row))
    return normalized


def _fetch_public_markets(policy: dict[str, Any], *, adapter: KalshiReadonlyAdapter) -> dict[str, Any]:
    base_url = str(policy["public_base_url"]).rstrip("/")
    max_scanned = max(0, int(policy["max_markets_scanned_per_cycle"]))
    page_limit = max(1, min(int(policy["public_page_limit"]), max_scanned or int(policy["public_page_limit"])))
    records: list[dict[str, Any]] = []
    cursor = None
    blockers: list[str] = []
    try:
        with httpx.Client(timeout=float(policy["request_timeout_seconds"])) as client:
            while len(records) < max_scanned:
                params: dict[str, Any] = {"limit": min(page_limit, max_scanned - len(records))}
                if cursor:
                    params["cursor"] = cursor
                response = client.get(f"{base_url}/markets", params=params)
                if response.status_code >= 400:
                    blockers.append(f"http_{response.status_code}")
                    break
                body = response.json()
                markets = body.get("markets") if isinstance(body, dict) else None
                if not isinstance(markets, list) or not markets:
                    break
                records.extend([row for row in markets if isinstance(row, dict)])
                next_cursor = body.get("cursor")
                if not next_cursor or next_cursor == cursor:
                    break
                cursor = str(next_cursor)
    except httpx.TimeoutException:
        blockers.append("read_timeout")
    except Exception:
        blockers.append("provider_unreachable")
    normalized = _normalize_records(records[:max_scanned], adapter)
    return {
        "status": "ok" if not blockers else "provider_error",
        "markets_scanned": len(records[:max_scanned]),
        "records": normalized,
        "blockers": blockers[:10],
    }


def _fetch_public_market_by_ticker(ticker: str, policy: dict[str, Any]) -> dict[str, Any]:
    base_url = str(policy["public_base_url"]).rstrip("/")
    try:
        with httpx.Client(timeout=float(policy["request_timeout_seconds"])) as client:
            response = client.get(f"{base_url}/markets/{ticker}")
        if response.status_code == 404:
            return {"ok": False, "status": "no_match", "ticker": ticker}
        if response.status_code >= 400:
            return {"ok": False, "status": f"http_{response.status_code}", "ticker": ticker}
        body = response.json()
        market = body.get("market") if isinstance(body, dict) else None
        if not isinstance(market, dict):
            return {"ok": False, "status": "no_match", "ticker": ticker}
        result = market.get("settlement_result") or market.get("settlementResult") or market.get("result")
        settlement_status = market.get("settlement_status") or market.get("settlementStatus")
        settlement_time = market.get("settlement_ts") or market.get("settlement_time") or market.get("settled_at")
        safe_payload = {
            key: market.get(key)
            for key in (
                "result",
                "settlement_result",
                "settlementResult",
                "settlement_status",
                "settlementStatus",
                "status",
                "market_status",
                "marketStatus",
                "settlement_ts",
                "settlement_time",
                "settled_at",
                "expiration_time",
                "close_time",
            )
            if market.get(key) not in (None, "")
        }
        return {
            "ok": True,
            "status": "ok",
            "ticker": ticker,
            "record": {
                "ticker": market.get("ticker") or ticker,
                "contract_id": market.get("ticker") or ticker,
                "settlement_result": result,
                "result": result,
                "settlement_status": settlement_status,
                "status": market.get("status"),
                "market_status": market.get("market_status") or market.get("marketStatus"),
                "settlement_time": settlement_time,
                "settled_at": settlement_time,
                "expiration_time": market.get("expiration_time"),
                "close_time": market.get("close_time"),
                "source_payload_redacted": safe_payload,
            },
        }
    except httpx.TimeoutException:
        return {"ok": False, "status": "read_timeout", "ticker": ticker}
    except Exception:
        return {"ok": False, "status": "provider_unreachable", "ticker": ticker}


def _invalid_request_response(errors: list[str], *, dry_run: bool, persist_outcomes: bool) -> dict[str, Any]:
    storage_health = get_storage_health()
    return {
        "ok": False,
        "status": "invalid_request",
        "errors": errors[:10],
        "dry_run": bool(dry_run),
        "persist_outcomes": bool(persist_outcomes),
        "provider_write": False,
        "execution_allowed_count": 0,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "human_approval_required": True,
        "paper_only": True,
        "storage_backend": "file",
        "storage_health": storage_health,
        "persistence_warning_if_ephemeral": storage_health.get("persistence_warning"),
        "raw_payload_included": False,
    }


def _apply_request_policy(
    policy: dict[str, Any],
    *,
    max_new_contracts: int | None,
    target_daily_new_contracts: int | None,
    hard_cap_daily_new_contracts: int | None,
    max_markets_scanned: int | None,
    adaptive_throttle: bool | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    configured_hard_cap = int(policy["hard_cap_daily_new_contracts"])
    requested_hard_cap = configured_hard_cap if hard_cap_daily_new_contracts is None else int(hard_cap_daily_new_contracts)
    if requested_hard_cap <= 0:
        errors.append("hard_cap_daily_new_contracts_must_be_positive")
    if requested_hard_cap > configured_hard_cap:
        errors.append("hard_cap_daily_new_contracts_exceeds_configured_cap")

    requested_target = int(target_daily_new_contracts if target_daily_new_contracts is not None else policy["target_daily_new_contracts"])
    if requested_target < 0:
        errors.append("target_daily_new_contracts_must_not_be_negative")

    requested_cycle = int(max_new_contracts if max_new_contracts is not None else policy["max_new_contracts_per_cycle"])
    if requested_cycle < 0:
        errors.append("max_new_contracts_must_not_be_negative")

    requested_scan = int(max_markets_scanned if max_markets_scanned is not None else policy["max_markets_scanned_per_cycle"])
    configured_scan = int(policy["max_markets_scanned_per_cycle"])
    if requested_scan <= 0:
        errors.append("max_markets_scanned_must_be_positive")
    if requested_scan > configured_scan:
        errors.append("max_markets_scanned_exceeds_configured_cap")

    if errors:
        return None, errors

    effective_hard_cap = min(requested_hard_cap, configured_hard_cap)
    effective_target = min(max(0, requested_target), effective_hard_cap)
    effective_cycle = min(max(0, requested_cycle), int(policy["max_new_contracts_per_cycle"]), effective_hard_cap)
    effective_policy = dict(policy)
    effective_policy.update(
        {
            "requested_daily_new_contract_target": requested_target,
            "requested_daily_new_contract_hard_cap": requested_hard_cap,
            "requested_max_new_contracts_per_cycle": requested_cycle,
            "requested_max_markets_scanned_per_cycle": requested_scan,
            "target_daily_new_contracts": effective_target,
            "max_new_contracts_per_day": effective_target,
            "hard_cap_daily_new_contracts": effective_hard_cap,
            "max_new_contracts_per_cycle": effective_cycle,
            "max_markets_scanned_per_cycle": min(requested_scan, configured_scan),
            "adaptive_throttle_enabled": bool(policy.get("adaptive_throttle_enabled", True) if adaptive_throttle is None else adaptive_throttle),
        }
    )
    return effective_policy, []


def _bucket_for_close(close_time: datetime, now: datetime, policy: dict[str, Any]) -> str | None:
    hours = (close_time - now).total_seconds() / 3600.0
    if hours < 0:
        return None
    if hours <= float(policy["short_term_window_hours"]):
        return "short_term"
    days = hours / 24.0
    if days <= float(policy["medium_term_window_days"]):
        return "medium_term"
    if days <= float(policy["long_term_window_days"]):
        return "long_term"
    return None


def _has_price_signal(row: dict[str, Any]) -> bool:
    return any(row.get(field) is not None for field in ("implied_probability", "yes_price", "no_price", "yes_bid", "yes_ask", "no_bid", "no_ask"))


def _is_selectable(row: dict[str, Any], now: datetime, policy: dict[str, Any]) -> tuple[bool, str | None]:
    if not _market_key(row):
        return False, "missing_ticker"
    close_time = _parse_time(row.get("close_time") or row.get("market_close_at"))
    if close_time is None:
        return False, "missing_close_time"
    if _bucket_for_close(close_time, now, policy) is None:
        return False, "outside_collection_windows"
    status = str(row.get("status_reason") or row.get("status") or "").strip().lower()
    if status and status not in SAFE_STATUS_VALUES:
        return False, "status_not_eligible"
    if not _has_price_signal(row):
        return False, "missing_price_signal"
    return True, None


def _quality_gate(row: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    market_type = str(row.get("market_type") or row.get("source_type") or "prediction_market").strip().lower()
    if market_type and market_type != "prediction_market":
        return False, "unsupported_market_type", None

    pricing_quality = str(row.get("pricing_quality") or "").strip().lower()
    pricing_score = _score(row.get("pricing_quality_score"))
    if pricing_quality in UNUSABLE_PRICING_VALUES or pricing_score < float(policy.get("min_pricing_quality_score", 1)):
        return False, "unusable_pricing_quality", None

    settlement_quality = row.get("settlement_quality_score")
    if isinstance(settlement_quality, str) and settlement_quality.strip().lower() in {"unknown", "unusable"}:
        return False, "settlement_quality_unknown", None
    settlement_status = str(row.get("settlement_rule_status") or row.get("settlement_rule_status_gate") or "").strip().lower()
    if settlement_status in {"unknown", "ambiguous", "unsupported"}:
        return False, "settlement_quality_unknown", None

    tier = str(row.get("liquidity_tier") or "").strip().lower()
    missing_liquidity = bool(row.get("missing_liquidity") or row.get("missing_liquidity_flag"))
    low_liquidity = bool(row.get("low_liquidity") or row.get("low_liquidity_flag"))
    if missing_liquidity or tier in LOWER_LIQUIDITY_TIERS or not tier:
        return True, None, "missing_or_low_liquidity"
    if low_liquidity:
        return True, None, "low_liquidity"
    return True, None, None


def _existing_sampled_keys(base_data_dir: str, day_state: dict[str, Any]) -> set[str]:
    keys = {str(value) for value in list(day_state.get("sampled_tickers") or []) if value}
    for rows in load_all_watchlists(base_data_dir).values():
        for row in rows:
            key = _market_key(row)
            if key:
                keys.add(str(key))
    for row in load_outcome_records(base_data_dir):
        key = _market_key(row)
        if key:
            keys.add(str(key))
    return keys


def _select_candidates(
    candidates: list[dict[str, Any]],
    *,
    base_data_dir: str,
    day_state: dict[str, Any],
    policy: dict[str, Any],
    max_new_contracts: int,
    target_daily_new_contracts: int,
    include_short_term: bool,
    include_medium_term: bool,
    include_long_term: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    existing_keys = _existing_sampled_keys(base_data_dir, day_state)
    daily_sampled = {str(value) for value in list(day_state.get("sampled_tickers") or []) if value}
    daily_remaining = max(0, int(target_daily_new_contracts) - len(daily_sampled))
    cap = max(0, min(int(max_new_contracts), daily_remaining, int(policy["hard_cap_daily_new_contracts"])))
    buckets: dict[str, list[dict[str, Any]]] = {"short_term": [], "medium_term": [], "long_term": []}
    exploration_buckets: dict[str, list[dict[str, Any]]] = {"short_term": [], "medium_term": [], "long_term": []}
    rejected = Counter()
    duplicate_contracts_skipped = 0
    seen_this_cycle: set[str] = set()
    for row in candidates:
        ok, reason = _is_selectable(row, now, policy)
        if not ok:
            rejected[str(reason or "invalid")] += 1
            continue
        key = str(_market_key(row))
        if key in existing_keys or key in seen_this_cycle:
            duplicate_contracts_skipped += 1
            rejected["duplicate_contract"] += 1
            continue
        quality_ok, quality_reason, exploration_reason = _quality_gate(row, policy)
        if not quality_ok:
            rejected[str(quality_reason or "quality_gate_rejected")] += 1
            continue
        close_time = _parse_time(row.get("close_time") or row.get("market_close_at"))
        bucket = _bucket_for_close(close_time or now, now, policy)
        if bucket == "short_term" and not include_short_term:
            rejected["short_term_disabled"] += 1
            continue
        if bucket == "medium_term" and not include_medium_term:
            rejected["medium_term_disabled"] += 1
            continue
        if bucket == "long_term" and not include_long_term:
            rejected["long_term_disabled"] += 1
            continue
        if bucket in buckets:
            copy = dict(row)
            copy["collector_bucket"] = bucket
            if exploration_reason:
                copy["exploration_sample"] = True
                copy["exploration_reason"] = exploration_reason
                exploration_buckets[bucket].append(copy)
            else:
                copy["exploration_sample"] = False
                buckets[bucket].append(copy)
            seen_this_cycle.add(key)

    for bucket_map in (buckets, exploration_buckets):
        for bucket in bucket_map:
            bucket_map[bucket] = sorted(
                bucket_map[bucket],
                key=lambda item: (-_score(item.get("review_priority_score")), str(item.get("close_time") or ""), str(_market_key(item) or "")),
            )

    selected: dict[str, list[dict[str, Any]]] = {"short_term": [], "medium_term": [], "long_term": []}
    if cap > 0:
        targets = {
            "short_term": int(round(cap * float(policy["short_term_allocation"]))),
            "medium_term": int(round(cap * float(policy["medium_term_allocation"]))),
        }
        targets["long_term"] = max(0, cap - targets["short_term"] - targets["medium_term"])
        for bucket in ("short_term", "medium_term", "long_term"):
            take = min(targets.get(bucket, 0), len(buckets[bucket]), cap - sum(len(rows) for rows in selected.values()))
            selected[bucket].extend(buckets[bucket][:take])
        remaining = cap - sum(len(rows) for rows in selected.values())
        selected_keys = {str(_market_key(row)) for rows in selected.values() for row in rows}
        for bucket in ("short_term", "medium_term", "long_term"):
            if remaining <= 0:
                break
            for row in buckets[bucket]:
                if remaining <= 0:
                    break
                key = str(_market_key(row))
                if key in selected_keys:
                    continue
                selected[bucket].append(row)
                selected_keys.add(key)
                remaining -= 1
        exploration_cap = int(cap * float(policy.get("exploration_sample_fraction", 0.10)))
        exploration_added = 0
        for bucket in ("short_term", "medium_term", "long_term"):
            if remaining <= 0 or exploration_added >= exploration_cap:
                break
            for row in exploration_buckets[bucket]:
                if remaining <= 0 or exploration_added >= exploration_cap:
                    break
                key = str(_market_key(row))
                if key in selected_keys:
                    continue
                selected[bucket].append(row)
                selected_keys.add(key)
                remaining -= 1
                exploration_added += 1

    flat = [row for bucket in ("short_term", "medium_term", "long_term") for row in selected[bucket]]
    liquidity_scores = [_score(row.get("liquidity_score")) for row in flat if row.get("liquidity_score") is not None]
    pricing_scores = [_score(row.get("pricing_quality_score")) for row in flat if row.get("pricing_quality_score") is not None]
    liquidity_tiers = Counter(str(row.get("liquidity_tier") or "missing") for row in flat)
    return {
        "eligible_contracts_found": sum(len(rows) for rows in buckets.values()) + sum(len(rows) for rows in exploration_buckets.values()),
        "selected": selected,
        "selected_flat": flat,
        "rejected_reason_counts": dict(rejected),
        "duplicate_contracts_skipped": duplicate_contracts_skipped,
        "daily_new_contracts_remaining": max(0, daily_remaining - len(flat)),
        "daily_new_contract_limit": int(target_daily_new_contracts),
        "daily_new_contract_hard_cap": int(policy["hard_cap_daily_new_contracts"]),
        "exploration_sample_count": len([row for row in flat if row.get("exploration_sample")]),
        "exploration_candidates_found": sum(len(rows) for rows in exploration_buckets.values()),
        "quality_gate_rejection_count": sum(count for reason, count in rejected.items() if reason in {"unusable_pricing_quality", "settlement_quality_unknown", "unsupported_market_type"}),
        "average_liquidity_score": _avg(liquidity_scores),
        "average_pricing_quality_score": _avg(pricing_scores),
        "liquidity_tier_counts": dict(liquidity_tiers),
    }


def _merge_review_queue(config: dict[str, Any], items: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    state = load_review_queue_state(config)
    by_id: dict[str, dict[str, Any]] = {
        str(row.get("id")): row
        for row in list(state.get("items", []))
        if isinstance(row, dict) and row.get("id")
    }
    for item in items:
        if item.get("id"):
            by_id[str(item["id"])] = item
    merged = sorted(by_id.values(), key=lambda row: (-_score(row.get("review_priority_score")), str(row.get("id") or "")))
    return persist_review_queue_snapshot(config, merged, run_id=run_id, summary=summarize_review_items(merged))


def _persist_paper_decisions(base_data_dir: str, items: list[dict[str, Any]], *, run_id: str, report_path: str | None) -> dict[str, Any]:
    existing = load_paper_decisions(base_data_dir)
    decisions = [
        create_paper_decision_record(
            item,
            run_id=run_id,
            snapshot_id=run_id,
            report_path=report_path,
            base_data_dir=base_data_dir,
            persist=False,
        )
        for item in items
    ]
    by_id = {str(row.get("decision_id")): row for row in existing if isinstance(row, dict) and row.get("decision_id")}
    written = 0
    for row in decisions:
        key = str(row.get("decision_id"))
        if key not in by_id:
            written += 1
        by_id[key] = row
    all_decisions = sorted(by_id.values(), key=lambda row: (str(row.get("created_at") or ""), str(row.get("decision_id") or "")))
    now = utc_now_iso()
    latest_path = Path(base_data_dir) / "paper_ledger" / "latest.json"
    run_path = Path(base_data_dir) / "paper_ledger" / "items" / f"{sanitize_filename(run_id)}.json"
    legacy_path = Path(base_data_dir) / "paper_ledger" / "paper_decisions.json"
    wrapper = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "storage_backend": "file",
        "latest_run_id": run_id,
        "last_updated_at": now,
        "items_written_count": len(all_decisions),
        "items": all_decisions,
    }
    run_wrapper = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "storage_backend": "file",
        "latest_run_id": run_id,
        "last_updated_at": now,
        "items_written_count": len(decisions),
        "items": decisions,
    }
    _atomic_write_json(latest_path, wrapper)
    _atomic_write_json(run_path, run_wrapper)
    _atomic_write_json(legacy_path, all_decisions)
    return {
        "storage_backend": "file",
        "latest_run_id": run_id,
        "last_updated_at": now,
        "paper_ledger_write_path": _project_relative(base_data_dir, latest_path),
        "paper_ledger_items_run_path": _project_relative(base_data_dir, run_path),
        "paper_decisions_written": written,
        "paper_decisions_total_count": len(all_decisions),
        "decisions": decisions,
    }


def _selected_to_review_items(config: dict[str, Any], selected_rows: list[dict[str, Any]], *, run_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in selected_rows:
        item = build_review_item(row, config)
        if item is None:
            continue
        item["run_id"] = run_id
        item["paper_only"] = True
        item["execution_allowed"] = False
        item["auto_execution_enabled"] = False
        item["kalshi_order_execution_enabled"] = False
        item["human_approval_required"] = True
        item["collector_bucket"] = row.get("collector_bucket")
        item["exploration_sample"] = bool(row.get("exploration_sample", False))
        item["exploration_reason"] = row.get("exploration_reason")
        items.append(item)
    return items


def _watchlist_item(item: dict[str, Any], decision: dict[str, Any] | None, *, run_id: str) -> dict[str, Any]:
    close_time = _parse_time(item.get("close_time") or item.get("market_close_at"))
    first_recheck = _iso(close_time + timedelta(seconds=5)) if close_time else None
    compact = _compact_contract(item, bucket=str(item.get("collector_bucket") or "unresolved"))
    compact.update(
        {
            "schema_version": COLLECTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "review_item_id": item.get("id") or item.get("review_item_id"),
            "decision_id": (decision or {}).get("decision_id"),
            "added_at": utc_now_iso(),
            "last_checked_at": None,
            "next_recheck_time": first_recheck,
            "recheck_count": 0,
            "outcome_status": "pending",
            "settlement_discovery_classification": None,
            "completion_candidate_ready": False,
            "provider_write": False,
            "execution_allowed": False,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "human_approval_required": True,
            "paper_only": True,
        }
    )
    return compact


def _recheck_delay_minutes(close_time: datetime, now: datetime, policy: dict[str, Any]) -> int:
    age_minutes = max(0.0, (now - close_time).total_seconds() / 60.0)
    if age_minutes < 30:
        return int(policy.get("fast_recheck_interval_minutes", 5))
    if age_minutes < 6 * 60:
        return int(policy.get("recheck_interval_minutes", 15))
    if age_minutes < 24 * 60:
        return 30
    return 120


def _next_recheck_time_for(row: dict[str, Any], now: datetime, policy: dict[str, Any]) -> datetime | None:
    close_time = _parse_time(row.get("close_time") or row.get("market_close_at"))
    if close_time is None:
        return None
    if now < close_time + timedelta(seconds=5):
        return close_time + timedelta(seconds=5)
    last_checked = _parse_time(row.get("last_checked_at"))
    if last_checked:
        return last_checked + timedelta(minutes=_recheck_delay_minutes(close_time, now, policy))
    return close_time + timedelta(seconds=5)


def _due_for_recheck(row: dict[str, Any], now: datetime, policy: dict[str, Any]) -> tuple[bool, str | None]:
    close_time = _parse_time(row.get("close_time") or row.get("market_close_at"))
    if close_time is None:
        return False, "missing_close_time"
    if now < close_time + timedelta(seconds=5):
        return False, "before_first_recheck"
    if now > close_time + timedelta(hours=int(policy["max_recheck_hours_after_close"])):
        return False, "stale_unknown"
    next_recheck = _parse_time(row.get("next_recheck_time"))
    if next_recheck and now < next_recheck:
        return False, "before_next_recheck"
    last_checked = _parse_time(row.get("last_checked_at"))
    if last_checked and now < last_checked + timedelta(minutes=_recheck_delay_minutes(close_time, now, policy)):
        return False, "interval_not_elapsed"
    return True, None


def _watchlist_backlog_summary(base_data_dir: str, policy: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    watchlists = load_all_watchlists(base_data_dir)
    by_key: dict[str, dict[str, Any]] = {}
    for bucket in WATCHLIST_BUCKETS:
        for row in watchlists.get(bucket, []):
            key = _market_key(row)
            if key:
                by_key[str(key)] = row
    completed_keys = {str(_market_key(row)) for row in load_outcome_records(base_data_dir) if _market_key(row)}
    unresolved_open = 0
    closed_unknown = 0
    not_settled = 0
    stale_unknown = 0
    recheck_due_now = 0
    next_times: list[datetime] = []
    bucket_counts = Counter()
    for key, row in by_key.items():
        if key in completed_keys:
            continue
        bucket_counts[str(row.get("collector_bucket") or "unresolved")] += 1
        close_time = _parse_time(row.get("close_time") or row.get("market_close_at"))
        classification = str(row.get("settlement_discovery_classification") or "").lower()
        if classification == "not_settled":
            not_settled += 1
        if close_time is None or now < close_time:
            unresolved_open += 1
        elif now > close_time + timedelta(hours=int(policy["max_recheck_hours_after_close"])):
            stale_unknown += 1
        else:
            closed_unknown += 1
        due, reason = _due_for_recheck(row, now, policy)
        if due:
            recheck_due_now += 1
            next_times.append(now)
        elif reason != "stale_unknown":
            next_time = _next_recheck_time_for(row, now, policy)
            if next_time:
                next_times.append(next_time)
    active_unresolved = len([key for key in by_key if key not in completed_keys])
    next_time = min(next_times) if next_times else None
    return {
        "watchlist_size": active_unresolved,
        "active_unresolved_watchlist": active_unresolved,
        "short_term_watchlist_count": int(bucket_counts.get("short_term", 0)),
        "medium_term_watchlist_count": int(bucket_counts.get("medium_term", 0)),
        "long_term_watchlist_count": int(bucket_counts.get("long_term", 0)),
        "unresolved_open": unresolved_open,
        "closed_unknown": closed_unknown,
        "not_settled": not_settled,
        "stale_unknown": stale_unknown,
        "recheck_due_now": recheck_due_now,
        "next_suggested_recheck_time": _iso(next_time) if next_time else None,
        "new_collection_blocked_by_backlog": bool(
            active_unresolved >= int(policy["max_active_unresolved_watchlist"])
            or closed_unknown >= int(policy["max_closed_unknown_backlog"])
        ),
    }


def _recheck_unresolved(
    base_data_dir: str,
    policy: dict[str, Any],
    *,
    persist_outcomes: bool,
    dry_run: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    watchlists = load_all_watchlists(base_data_dir)
    unresolved_by_key: dict[str, dict[str, Any]] = {}
    for bucket in ("short_term", "medium_term", "long_term", "unresolved"):
        for row in watchlists.get(bucket, []):
            key = _market_key(row)
            if key:
                unresolved_by_key[str(key)] = dict(row)

    completed_keys = {_market_key(row) for row in load_outcome_records(base_data_dir)}
    due: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    for row in unresolved_by_key.values():
        key = _market_key(row)
        if key in completed_keys:
            continue
        is_due, reason = _due_for_recheck(row, now, policy)
        if reason == "stale_unknown":
            row["settlement_discovery_classification"] = "stale_unknown"
            row["outcome_status"] = "unknown"
            stale.append(row)
            continue
        if is_due:
            due.append(row)

    read_only_records: list[dict[str, Any]] = []
    no_match_count = 0
    fetch_status_counts: Counter[str] = Counter()
    for row in due:
        key = str(_market_key(row))
        fetched = _fetch_public_market_by_ticker(key, policy)
        fetch_status_counts[str(fetched.get("status"))] += 1
        if fetched.get("ok") and isinstance(fetched.get("record"), dict):
            read_only_records.append(fetched["record"])
        else:
            no_match_count += 1

    discovery = discover_kalshi_settlements_for_pending_rows(due, read_only_records=read_only_records)
    explicit_candidates = [
        row
        for row in discovery.get("completion_candidates", [])
        if row.get("source") == "read_only_settlement" and row.get("evidence_type") == "explicit_settlement_field"
    ]
    dry_run_ingest = ingest_outcome_records(
        explicit_candidates,
        source="read_only_settlement",
        dry_run=True,
        persist=True,
        base_data_dir=base_data_dir,
    )
    persist_result = {
        "records_valid": 0,
        "records_rejected": 0,
        "rejected_reason_counts": {},
        "duplicate_count": 0,
        "outcome_records_written": 0,
        "total_count": len(load_outcome_records(base_data_dir)),
        "provider_write": False,
    }
    if bool(persist_outcomes) and not bool(dry_run) and int(dry_run_ingest.get("records_valid", 0)) > 0:
        persist_result = ingest_outcome_records(
            explicit_candidates,
            source="read_only_settlement",
            dry_run=False,
            persist=True,
            base_data_dir=base_data_dir,
        )

    record_lookup = {str(_market_key(record)): record for record in read_only_records if _market_key(record)}
    completed_items: list[dict[str, Any]] = []
    completed_candidate_keys = {str(_market_key(row)) for row in explicit_candidates if _market_key(row)}
    for row in due:
        key = str(_market_key(row))
        record = record_lookup.get(key)
        classification = {"classification": "no_match"}
        if record:
            classification = classify_kalshi_settlement(record)
        row["last_checked_at"] = utc_now_iso()
        row["recheck_count"] = int(row.get("recheck_count", 0) or 0) + 1
        row["settlement_discovery_classification"] = classification.get("classification")
        row["completion_candidate_ready"] = key in completed_candidate_keys
        row["next_recheck_time"] = _iso(now + timedelta(minutes=_recheck_delay_minutes(_parse_time(row.get("close_time") or row.get("market_close_at")) or now, now, policy)))
        if key in completed_candidate_keys and (not dry_run) and (int(persist_result.get("outcome_records_written", 0)) > 0 or int(persist_result.get("duplicate_count", 0)) > 0):
            completed = dict(row)
            completed["outcome_status"] = classification.get("outcome_status")
            completed["final_outcome"] = classification.get("final_outcome")
            completed["settled_at"] = (record or {}).get("settlement_time") or (record or {}).get("settled_at")
            completed_items.append(completed)
            unresolved_by_key.pop(key, None)
        else:
            unresolved_by_key[key] = row
    for row in stale:
        key = str(_market_key(row))
        unresolved_by_key[key] = row

    return {
        "records_checked": len(due),
        "read_only_records_matched": int(discovery.get("read_only_records_matched", 0)),
        "no_match_count": no_match_count,
        "stale_count": len(stale),
        "fetch_status_counts": dict(fetch_status_counts),
        "settled_yes_count": int(discovery.get("settled_yes_count", 0)),
        "settled_no_count": int(discovery.get("settled_no_count", 0)),
        "void_cancelled_count": int(discovery.get("void_cancelled_count", 0)),
        "not_settled_count": int(discovery.get("not_settled_count", 0)),
        "unknown_count": int(discovery.get("unknown_count", 0)),
        "explicit_settlement_count": len(explicit_candidates),
        "dry_run_ingest": dry_run_ingest,
        "persist_result": persist_result,
        "outcomes_persisted": int(persist_result.get("outcome_records_written", 0)),
        "duplicate_outcomes_skipped": int(persist_result.get("duplicate_count", 0)),
        "updated_unresolved_items": list(unresolved_by_key.values()),
        "completed_items": completed_items,
        "provider_write": False,
    }


def run_collector_cycle(
    *,
    dry_run: bool = True,
    persist_outcomes: bool = False,
    max_new_contracts: int | None = None,
    target_daily_new_contracts: int | None = None,
    hard_cap_daily_new_contracts: int | None = None,
    max_markets_scanned: int | None = None,
    include_short_term: bool = True,
    include_medium_term: bool = True,
    include_long_term: bool = True,
    adaptive_throttle: bool | None = None,
    deepseek_review: bool = False,
    base_data_dir: str = "data",
    read_only_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    base_policy = collector_policy_from_env()
    policy, policy_errors = _apply_request_policy(
        base_policy,
        max_new_contracts=max_new_contracts,
        target_daily_new_contracts=target_daily_new_contracts,
        hard_cap_daily_new_contracts=hard_cap_daily_new_contracts,
        max_markets_scanned=max_markets_scanned,
        adaptive_throttle=adaptive_throttle,
    )
    if policy_errors or policy is None:
        return _invalid_request_response(policy_errors, dry_run=dry_run, persist_outcomes=persist_outcomes)
    max_new_contracts = int(policy["max_new_contracts_per_cycle"])
    target_daily_new_contracts = int(policy["target_daily_new_contracts"])
    storage_health = get_storage_health()
    if not bool(policy["collector_enabled"]):
        return {
            "ok": True,
            "status": "disabled",
            "dry_run": bool(dry_run),
            "provider_write": False,
            "execution_allowed_count": 0,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "human_approval_required": True,
            "storage_backend": "file",
            "storage_health": storage_health,
            "persistence_warning_if_ephemeral": storage_health.get("persistence_warning"),
        }
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    lock = _acquire_lock(base_data_dir, stale_minutes=int(policy["lock_stale_minutes"]))
    cycle_id = f"kalshi_calibration_{safe_run_id('kalshi_calibration_cycle', utc_now_iso())}"
    if not lock["lock_acquired"]:
        return {
            "ok": True,
            "status": "skipped_due_to_lock",
            "cycle_id": cycle_id,
            **lock,
            "provider_write": False,
            "execution_allowed_count": 0,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "storage_backend": "file",
            "storage_health": storage_health,
            "persistence_warning_if_ephemeral": storage_health.get("persistence_warning"),
        }

    try:
        day = datetime.now(timezone.utc).date().isoformat()
        day_state = _load_daily_state(base_data_dir, day)
        adapter = KalshiReadonlyAdapter(dict(config["providers"].get(KALSHI_PROVIDER, {})))
        recheck = _recheck_unresolved(base_data_dir, policy, persist_outcomes=persist_outcomes, dry_run=dry_run)
        pre_backlog = _watchlist_backlog_summary(base_data_dir, policy)
        daily_sampled = {str(value) for value in list(day_state.get("sampled_tickers") or []) if value}
        daily_remaining_capacity = max(0, min(target_daily_new_contracts, int(policy["hard_cap_daily_new_contracts"])) - len(daily_sampled))
        adaptive_throttle_reasons: list[str] = []
        effective_max_new_contracts = min(max_new_contracts, daily_remaining_capacity)
        if pre_backlog.get("new_collection_blocked_by_backlog"):
            adaptive_throttle_reasons.append("settlement_backlog_limit_reached")
            effective_max_new_contracts = 0
        if daily_remaining_capacity <= 0:
            adaptive_throttle_reasons.append("daily_target_reached")
            effective_max_new_contracts = 0

        if effective_max_new_contracts <= 0 and read_only_records is None:
            scan = {"status": "new_collection_paused", "markets_scanned": 0, "records": [], "blockers": []}
        elif read_only_records is not None:
            normalized_records = _normalize_records(read_only_records, adapter)
            scan = {"status": "injected_records", "markets_scanned": len(normalized_records), "records": normalized_records, "blockers": []}
        else:
            scan = _fetch_public_markets(policy, adapter=adapter)
        provider_blockers = list(scan.get("blockers", []))[:10]
        if bool(policy.get("adaptive_throttle_enabled", True)) and provider_blockers:
            if any(str(blocker) == "http_429" for blocker in provider_blockers):
                adaptive_throttle_reasons.append("provider_rate_or_availability_limit")
                effective_max_new_contracts = 0
            elif int(scan.get("markets_scanned", 0) or 0) <= 0 and any(str(blocker) in {"read_timeout", "provider_unreachable"} for blocker in provider_blockers):
                adaptive_throttle_reasons.append("provider_rate_or_availability_limit")
                effective_max_new_contracts = 0
            else:
                adaptive_throttle_reasons.append("provider_error_throttle")
                effective_max_new_contracts = min(effective_max_new_contracts, max(1, effective_max_new_contracts // 2))

        evaluation = _evaluate_kalshi_review_candidates(
            config,
            {
                "records": list(scan.get("records", [])),
                "records_received": int(scan.get("markets_scanned", 0)),
                "records_valid": len(scan.get("records", [])),
            },
        )
        selection = _select_candidates(
            list(evaluation.get("candidates", [])),
            base_data_dir=base_data_dir,
            day_state=day_state,
            policy=policy,
            max_new_contracts=effective_max_new_contracts,
            target_daily_new_contracts=target_daily_new_contracts,
            include_short_term=include_short_term,
            include_medium_term=include_medium_term,
            include_long_term=include_long_term,
        )
        duplicate_denominator = int(selection.get("eligible_contracts_found", 0)) + int(selection.get("duplicate_contracts_skipped", 0))
        if duplicate_denominator > 0 and int(selection.get("duplicate_contracts_skipped", 0)) / duplicate_denominator > 0.30:
            adaptive_throttle_reasons.append("high_duplicate_rate")
        selected_rows = list(selection["selected_flat"])
        selected_items = _selected_to_review_items(config, selected_rows, run_id=cycle_id)
        paper_storage: dict[str, Any] = {"paper_decisions_written": 0, "paper_decisions_total_count": len(load_paper_decisions(base_data_dir)), "decisions": []}
        queue_storage: dict[str, Any] = {"items_written_count": 0}
        watchlist_storage: dict[str, Any] = {}
        completed_storage: dict[str, Any] = {}

        decisions_by_review: dict[str, dict[str, Any]] = {}
        if not dry_run and selected_items:
            report_path = f"outcomes/collector/items/{cycle_id}.json"
            queue_storage = _merge_review_queue(config, selected_items, cycle_id)
            paper_storage = _persist_paper_decisions(base_data_dir, selected_items, run_id=cycle_id, report_path=report_path)
            decisions_by_review = {
                str(row.get("review_item_id")): row
                for row in list(paper_storage.get("decisions", []))
                if row.get("review_item_id")
            }

        new_watchlist_items = []
        for item in selected_items:
            decision = decisions_by_review.get(str(item.get("id") or item.get("review_item_id")))
            new_watchlist_items.append(_watchlist_item(item, decision, run_id=cycle_id))

        if not dry_run:
            unresolved_by_key = {str(_market_key(row)): row for row in list(recheck.get("updated_unresolved_items", [])) if _market_key(row)}
            for item in new_watchlist_items:
                key = _market_key(item)
                if key:
                    unresolved_by_key[str(key)] = item
            all_unresolved = list(unresolved_by_key.values())
            for bucket in ("short_term", "medium_term", "long_term"):
                watchlist_storage[bucket] = _write_watchlist(
                    base_data_dir,
                    bucket,
                    [row for row in all_unresolved if row.get("collector_bucket") == bucket],
                )
            watchlist_storage["unresolved"] = _write_watchlist(base_data_dir, "unresolved", all_unresolved)
            if recheck.get("completed_items"):
                completed_storage = _write_completed_index(base_data_dir, list(recheck.get("completed_items", [])))

        calibration = build_calibration_report(base_data_dir=base_data_dir, write_report=not dry_run)
        outcomes = load_outcome_records(base_data_dir)
        post_backlog = _watchlist_backlog_summary(base_data_dir, policy) if not dry_run else pre_backlog
        total_outcomes = len(outcomes)
        selected_counts = {bucket: len(selection["selected"][bucket]) for bucket in ("short_term", "medium_term", "long_term")}
        selection_rejections = Counter(selection["rejected_reason_counts"])
        for reason, count in dict(evaluation.get("rejected_reason_counts", {})).items():
            mapped_reason = "missing_price_signal" if reason == "missing_prices" else str(reason)
            selection_rejections[mapped_reason] += int(count or 0)
        cycle_report = {
            "schema_version": COLLECTOR_SCHEMA_VERSION,
            "ok": True,
            "status": "collector_cycle_complete",
            "cycle_id": cycle_id,
            "created_at": utc_now_iso(),
            "dry_run": bool(dry_run),
            "persist_outcomes": bool(persist_outcomes),
            "lock_acquired": True,
            "skipped_due_to_lock": False,
            "collector_enabled": bool(policy["collector_enabled"]),
            "markets_scanned": int(scan.get("markets_scanned", 0)),
            "eligible_contracts_found": int(selection.get("eligible_contracts_found", 0)),
            "selected_short_term": selected_counts["short_term"],
            "selected_medium_term": selected_counts["medium_term"],
            "selected_long_term": selected_counts["long_term"],
            "new_contracts_added": len(selected_items) if not dry_run else 0,
            "new_contracts_selected": len(selected_items),
            "daily_new_contract_target": int(selection["daily_new_contract_limit"]),
            "daily_new_contract_hard_cap": int(selection["daily_new_contract_hard_cap"]),
            "daily_new_contract_limit": int(selection["daily_new_contract_limit"]),
            "daily_new_contracts_remaining": int(selection["daily_new_contracts_remaining"]),
            "daily_remaining_capacity": int(selection["daily_new_contracts_remaining"]),
            "effective_max_new_contracts": int(effective_max_new_contracts),
            "adaptive_throttle_enabled": bool(policy.get("adaptive_throttle_enabled", True)),
            "adaptive_throttle_reasons": adaptive_throttle_reasons,
            "duplicate_contracts_skipped": int(selection["duplicate_contracts_skipped"]),
            "selection_rejected_reason_counts": dict(selection_rejections),
            "quality_gate_rejection_count": int(selection.get("quality_gate_rejection_count", 0)),
            "exploration_sample_count": int(selection.get("exploration_sample_count", 0)),
            "exploration_candidates_found": int(selection.get("exploration_candidates_found", 0)),
            "average_liquidity_score": float(selection.get("average_liquidity_score", 0.0)),
            "average_pricing_quality_score": float(selection.get("average_pricing_quality_score", 0.0)),
            "liquidity_tier_counts": dict(selection.get("liquidity_tier_counts", {})),
            "records_checked": int(recheck["records_checked"]),
            "records_rechecked_today": int(recheck["records_checked"]),
            "read_only_records_matched": int(recheck["read_only_records_matched"]),
            "explicit_settlement_count": int(recheck["explicit_settlement_count"]),
            "settled_yes_count": int(recheck["settled_yes_count"]),
            "settled_no_count": int(recheck["settled_no_count"]),
            "void_cancelled_count": int(recheck["void_cancelled_count"]),
            "unknown_count": int(recheck["unknown_count"]),
            "not_settled_count": int(recheck["not_settled_count"]),
            "no_match_count": int(recheck["no_match_count"]),
            "stale_count": int(recheck["stale_count"]),
            "dry_run_ingest": {
                "records_received": int(recheck["dry_run_ingest"].get("records_received", 0)),
                "records_valid": int(recheck["dry_run_ingest"].get("records_valid", 0)),
                "records_rejected": int(recheck["dry_run_ingest"].get("records_rejected", 0)),
                "rejected_reason_counts": dict(recheck["dry_run_ingest"].get("rejected_reason_counts", {})),
                "duplicate_count": int(recheck["dry_run_ingest"].get("duplicate_count", 0)),
            },
            "outcomes_persisted": int(recheck["outcomes_persisted"]),
            "outcomes_persisted_today": int(recheck["outcomes_persisted"]),
            "duplicate_outcomes_skipped": int(recheck["duplicate_outcomes_skipped"]),
            "total_outcome_records_count": total_outcomes,
            "matched_outcomes_count": int(calibration.get("matched_outcomes_count", 0)),
            "progress_to_100": _progress(total_outcomes, 100),
            "progress_to_300": _progress(total_outcomes, 300),
            "progress_to_1000": _progress(total_outcomes, 1000),
            "calibration_status": calibration.get("status"),
            "coverage_rate": float(calibration.get("coverage_rate", 0.0)),
            "insufficient_sample": _insufficient_sample(calibration, policy),
            "next_required_data": list(calibration.get("next_required_data", [])),
            "sample_targets": {
                "min_target_outcomes": int(policy["min_target_outcomes"]),
                "good_target_outcomes": int(policy["good_target_outcomes"]),
                "strong_target_outcomes": int(policy["strong_target_outcomes"]),
                "long_term_target_outcomes": int(policy["long_term_target_outcomes"]),
            },
            "settlement_backlog": post_backlog,
            "watchlist_size": int(post_backlog.get("watchlist_size", 0)),
            "unresolved_open": int(post_backlog.get("unresolved_open", 0)),
            "closed_unknown": int(post_backlog.get("closed_unknown", 0)),
            "stale_unknown": int(post_backlog.get("stale_unknown", 0)),
            "recheck_due_now": int(post_backlog.get("recheck_due_now", 0)),
            "next_suggested_recheck_time": post_backlog.get("next_suggested_recheck_time"),
            "storage_backend": "file",
            "storage_health": storage_health,
            "persistence_warning_if_ephemeral": storage_health.get("persistence_warning"),
            "collector_policy": {
                "max_markets_scanned_per_cycle": int(policy["max_markets_scanned_per_cycle"]),
                "max_new_contracts_per_cycle": int(policy["max_new_contracts_per_cycle"]),
                "target_daily_new_contracts": int(policy["target_daily_new_contracts"]),
                "hard_cap_daily_new_contracts": int(policy["hard_cap_daily_new_contracts"]),
                "max_new_contracts_per_day": int(policy["max_new_contracts_per_day"]),
                "recheck_interval_minutes": int(policy["recheck_interval_minutes"]),
                "fast_recheck_interval_minutes": int(policy["fast_recheck_interval_minutes"]),
                "max_recheck_hours_after_close": int(policy["max_recheck_hours_after_close"]),
                "short_medium_long_allocation": "80/15/5",
                "max_active_unresolved_watchlist": int(policy["max_active_unresolved_watchlist"]),
                "max_closed_unknown_backlog": int(policy["max_closed_unknown_backlog"]),
            },
            "provider_write": False,
            "execution_allowed_count": 0,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "human_approval_required": True,
            "paper_only": True,
            "selected_contracts": [_compact_contract(row, bucket=row.get("collector_bucket")) for row in selected_items],
            "paper_ledger": {k: v for k, v in paper_storage.items() if k != "decisions"},
            "review_queue": queue_storage,
            "watchlists": watchlist_storage,
            "completed_index": completed_storage,
            "provider_blockers": list(scan.get("blockers", []))[:10],
            "deepseek_review_status": "not_requested",
        }

        daily_report = None
        if not dry_run:
            sampled = set(str(value) for value in list(day_state.get("sampled_tickers") or []) if value)
            for row in selected_items:
                key = _market_key(row)
                if key:
                    sampled.add(str(key))
            day_state["sampled_tickers"] = sorted(sampled)
            day_state["cycles_run"] = int(day_state.get("cycles_run", 0) or 0) + 1
            day_state["markets_scanned"] = int(day_state.get("markets_scanned", 0) or 0) + cycle_report["markets_scanned"]
            day_state["eligible_contracts_found"] = int(day_state.get("eligible_contracts_found", 0) or 0) + cycle_report["eligible_contracts_found"]
            day_state["selected_short_term"] = int(day_state.get("selected_short_term", 0) or 0) + cycle_report["selected_short_term"]
            day_state["selected_medium_term"] = int(day_state.get("selected_medium_term", 0) or 0) + cycle_report["selected_medium_term"]
            day_state["selected_long_term"] = int(day_state.get("selected_long_term", 0) or 0) + cycle_report["selected_long_term"]
            day_state["new_contracts_added"] = int(day_state.get("new_contracts_added", 0) or 0) + cycle_report["new_contracts_added"]
            day_state["new_contracts_added_today"] = day_state["new_contracts_added"]
            day_state["daily_new_contract_limit"] = int(target_daily_new_contracts)
            day_state["daily_new_contract_target"] = int(target_daily_new_contracts)
            day_state["daily_new_contract_hard_cap"] = int(policy["hard_cap_daily_new_contracts"])
            day_state["daily_new_contracts_remaining"] = max(0, int(target_daily_new_contracts) - len(sampled))
            day_state["daily_remaining_capacity"] = day_state["daily_new_contracts_remaining"]
            day_state["duplicate_contracts_skipped"] = int(day_state.get("duplicate_contracts_skipped", 0) or 0) + cycle_report["duplicate_contracts_skipped"]
            day_state["quality_gate_rejection_count"] = int(day_state.get("quality_gate_rejection_count", 0) or 0) + cycle_report["quality_gate_rejection_count"]
            day_state["exploration_sample_count"] = int(day_state.get("exploration_sample_count", 0) or 0) + cycle_report["exploration_sample_count"]
            tier_counts = Counter(dict(day_state.get("liquidity_tier_counts", {})))
            tier_counts.update(dict(cycle_report.get("liquidity_tier_counts", {})))
            day_state["liquidity_tier_counts"] = dict(tier_counts)
            selected_quality_rows = list(selected_items)
            day_state["liquidity_score_sum"] = float(day_state.get("liquidity_score_sum", 0.0) or 0.0) + sum(_score(row.get("liquidity_score")) for row in selected_quality_rows)
            day_state["pricing_quality_score_sum"] = float(day_state.get("pricing_quality_score_sum", 0.0) or 0.0) + sum(_score(row.get("pricing_quality_score")) for row in selected_quality_rows)
            day_state["quality_sample_count"] = int(day_state.get("quality_sample_count", 0) or 0) + len(selected_quality_rows)
            if int(day_state["quality_sample_count"]) > 0:
                day_state["average_liquidity_score"] = round(float(day_state["liquidity_score_sum"]) / int(day_state["quality_sample_count"]), 4)
                day_state["average_pricing_quality_score"] = round(float(day_state["pricing_quality_score_sum"]) / int(day_state["quality_sample_count"]), 4)
            for field in ("records_checked", "explicit_settlement_count", "settled_yes_count", "settled_no_count", "void_cancelled_count", "unknown_count", "not_settled_count", "outcomes_persisted", "duplicate_outcomes_skipped"):
                day_state[field] = int(day_state.get(field, 0) or 0) + int(cycle_report[field])
            day_state["records_rechecked_today"] = day_state["records_checked"]
            day_state["outcomes_persisted_today"] = day_state["outcomes_persisted"]
            day_state["deepseek_review_status"] = cycle_report["deepseek_review_status"]
            _atomic_write_json(_daily_path(base_data_dir, day), day_state)
            daily_report = write_daily_report(base_data_dir, day=day, calibration_report=calibration)
            cycle_report["daily_report_path"] = daily_report.get("daily_report_path")
            cycle_report["daily_markdown_path"] = daily_report.get("daily_markdown_path")
            cycle_path = _collector_root(base_data_dir) / "items" / f"{sanitize_filename(cycle_id)}.json"
            latest_path = _collector_root(base_data_dir) / "latest_cycle.json"
            _atomic_write_json(cycle_path, cycle_report)
            _atomic_write_json(latest_path, cycle_report)
            cycle_report["cycle_report_path"] = _project_relative(base_data_dir, cycle_path)
            cycle_report["latest_cycle_path"] = _project_relative(base_data_dir, latest_path)

        if deepseek_review:
            review = run_deepseek_review(
                collector_cycle_report=cycle_report,
                daily_report=daily_report or {},
                calibration_report=calibration,
                sampled_contracts=list(cycle_report.get("selected_contracts", [])),
            )
            cycle_report["deepseek_review_status"] = review.get("status")
            cycle_report["deepseek_review"] = review
            if not dry_run:
                daily_after_review = _load_daily_state(base_data_dir, day)
                daily_after_review["deepseek_review_status"] = review.get("status")
                _atomic_write_json(_daily_path(base_data_dir, day), daily_after_review)
                write_daily_report(base_data_dir, day=day, calibration_report=calibration)
        return cycle_report
    finally:
        _release_lock(base_data_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Kalshi calibration collector.")
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--persist-outcomes", action="store_true")
    parser.add_argument("--daily-report", action="store_true")
    parser.add_argument("--max-new-contracts", type=int, default=None)
    parser.add_argument("--target-daily-new-contracts", type=int, default=None)
    parser.add_argument("--hard-cap-daily-new-contracts", type=int, default=None)
    parser.add_argument("--max-markets-scanned", type=int, default=None)
    parser.add_argument("--disable-adaptive-throttle", action="store_true")
    parser.add_argument("--base-data-dir", default="data")
    args = parser.parse_args(argv)
    if args.daily_report and not args.run_once:
        print(json.dumps(write_daily_report(args.base_data_dir), indent=2, sort_keys=True))
        return 0
    if not args.run_once:
        parser.error("one of --run-once or --daily-report is required")
    dry_run = bool(args.dry_run) or not bool(args.persist_outcomes)
    result = run_collector_cycle(
        dry_run=dry_run,
        persist_outcomes=bool(args.persist_outcomes),
        max_new_contracts=args.max_new_contracts,
        target_daily_new_contracts=args.target_daily_new_contracts,
        hard_cap_daily_new_contracts=args.hard_cap_daily_new_contracts,
        max_markets_scanned=args.max_markets_scanned,
        adaptive_throttle=not bool(args.disable_adaptive_throttle),
        base_data_dir=args.base_data_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
