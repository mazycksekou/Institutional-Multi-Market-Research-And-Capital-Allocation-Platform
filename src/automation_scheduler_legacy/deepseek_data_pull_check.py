from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_runtime_data_path, get_storage_health, resolve_base_data_dir
from .data_source_registry import build_registry
from .kalshi_readonly_readiness import build_kalshi_readonly_readiness_report, load_project_env, resolve_project_root
from .prediction_market_outcome_candidates import build_candidate_report
from src.services.scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso


DEEPSEEK_DATA_PULL_CHECK_SCHEMA_VERSION = f"{SCHEMA_VERSION}.deepseek_data_pull_check.v1"
DEFAULT_APP_BASE_URL = "https://betting-stock-api-code-integration.onrender.com"
MAX_TINY_PROVIDER_CALLS = 3
MAX_TINY_PROVIDER_RECORDS = 5
DEFAULT_LOCAL_RECORD_SCAN_LIMIT = 250

COMPACT_REPORT_INPUTS = {
    "ops_check_latest": ("ops_checks", "latest.json"),
    "data_availability_tiers": ("data_sources", "data_availability", "latest.json"),
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _cap_nonnegative(value: Any, maximum: int) -> int:
    return max(0, min(_safe_int(value, 0), maximum))


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


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _relative(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _report_root(base_data_dir: str | Path | None = None) -> Path:
    if base_data_dir is None:
        return get_runtime_data_path("deepseek_data_checks")
    root = resolve_base_data_dir(base_data_dir) / "deepseek_data_checks"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _summarize_input_report(name: str, path: Path, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "name": name,
            "path": str(path),
            "exists": path.exists(),
            "read_ok": False,
            "status": "missing_or_malformed",
        }
    return {
        "name": name,
        "path": str(path),
        "exists": True,
        "read_ok": True,
        "status": payload.get("status") or payload.get("mode") or "ok",
        "ok": payload.get("ok"),
        "run_id": payload.get("run_id") or payload.get("latest_run_id"),
        "created_at": payload.get("created_at") or payload.get("started_at") or payload.get("last_updated_at"),
        "provider_write": bool(payload.get("provider_write", False)),
        "execution_allowed": bool(payload.get("execution_allowed", False)),
        "raw_payload_included": bool(payload.get("raw_payload_included", False)),
        "secrets_included": bool(payload.get("secrets_included", False)),
    }


def read_compact_input_reports(*, base_data_dir: str | Path = "data") -> list[dict[str, Any]]:
    root = resolve_base_data_dir(base_data_dir)
    reports: list[dict[str, Any]] = []
    for name, parts in COMPACT_REPORT_INPUTS.items():
        path = root.joinpath(*parts)
        payload = _read_json(path)
        reports.append(_summarize_input_report(name, path, payload))
    return reports


def _registry_budget_summary(*, module: str | None = None, source_id: str | None = None) -> dict[str, Any]:
    registry = build_registry(module=module or None)
    sources = [source for source in list(registry.get("sources") or []) if isinstance(source, dict)]
    if source_id:
        needle = str(source_id).strip().lower()
        sources = [
            source for source in sources
            if needle in {
                str(source.get("source_id") or "").lower(),
                str(source.get("provider") or "").lower(),
                str(source.get("name") or "").lower(),
            }
        ]
    enabled_sources = [source for source in sources if bool(source.get("enabled", False))]
    paid_or_budgeted = [
        source for source in sources
        if bool(source.get("requires_budget_approval", False))
        or bool(source.get("paid_upgrade_required", False))
        or str(source.get("source_access_type") or "").lower() in {"paid", "paid_api", "commercial"}
    ]
    paid_enabled = [
        source for source in enabled_sources
        if source in paid_or_budgeted or bool(source.get("paid_upgrade_allowed", False))
    ]
    return {
        "total_sources_checked": len(sources),
        "enabled_source_count": len(enabled_sources),
        "enabled_source_ids": [str(source.get("source_id") or source.get("id") or "unknown") for source in enabled_sources][:25],
        "paid_budget_gated_source_count": len(paid_or_budgeted),
        "paid_source_enabled_count": len(paid_enabled),
        "paid_budget_gated_sources_blocked": len(paid_enabled) == 0,
        "source_remains_enabled_false": len(enabled_sources) == 0,
        "paid_upgrade_allowed": False,
        "substantial_usage_allowed": False,
    }


def provider_call_gate(
    *,
    dry_run: bool = True,
    allow_tiny_provider_calls: bool = False,
    max_provider_calls: int = 0,
    max_records: int = 0,
) -> dict[str, Any]:
    requested_calls = max(0, _safe_int(max_provider_calls, 0))
    requested_records = max(0, _safe_int(max_records, 0))
    effective_calls = _cap_nonnegative(requested_calls, MAX_TINY_PROVIDER_CALLS)
    effective_records = _cap_nonnegative(requested_records, MAX_TINY_PROVIDER_RECORDS)
    allowed = bool(dry_run and allow_tiny_provider_calls and effective_calls > 0 and effective_records > 0)
    return {
        "dry_run": bool(dry_run),
        "provider_calls_requested": requested_calls,
        "provider_records_requested": requested_records,
        "allow_tiny_provider_calls": bool(allow_tiny_provider_calls),
        "max_provider_calls_effective": effective_calls if allow_tiny_provider_calls else 0,
        "max_records_effective": effective_records if allow_tiny_provider_calls else 0,
        "provider_calls_allowed": allowed,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "provider_records_returned": 0,
        "markets_checked_with_provider": 0,
        "explicit_outcomes_found": 0,
        "provider_call_execution_status": "tiny_provider_mode_armed" if allowed else "not_executed",
        "provider_call_block_reason": None if allowed else "provider_calls_disabled_by_default_or_missing_tiny_caps",
        "rate_limited": False,
        "rate_limit_stop_enabled": True,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _candidate_summary(candidate_report: dict[str, Any] | None) -> dict[str, Any]:
    if not candidate_report:
        return {
            "prediction_market_outcome_check_enabled": False,
            "candidates_count": 0,
            "rejected_count": 0,
        }
    keys = (
        "candidate_latest_json_path",
        "candidate_latest_markdown_path",
        "candidate_item_json_path",
        "candidate_item_markdown_path",
        "candidate_daily_json_path",
        "candidate_daily_markdown_path",
    )
    return {
        "prediction_market_outcome_check_enabled": True,
        "candidate_status": candidate_report.get("status"),
        "source_records_scanned": candidate_report.get("source_records_scanned"),
        "candidates_count": candidate_report.get("candidates_count"),
        "rejected_count": candidate_report.get("rejected_count"),
        "local_rejected_count": candidate_report.get("local_rejected_count"),
        "provider_rejected_count": candidate_report.get("provider_rejected_count"),
        "rejection_reason_counts": candidate_report.get("rejection_reason_counts"),
        "rejection_reasons": candidate_report.get("rejection_reasons"),
        "provider_settlement_check_enabled": candidate_report.get("provider_settlement_check_enabled"),
        "provider_settlement_check_status": candidate_report.get("provider_settlement_check_status"),
        "provider_call_block_reason": candidate_report.get("provider_call_block_reason"),
        "provider_calls_attempted": candidate_report.get("provider_calls_attempted"),
        "provider_calls_succeeded": candidate_report.get("provider_calls_succeeded"),
        "provider_calls_failed": candidate_report.get("provider_calls_failed"),
        "provider_records_returned": candidate_report.get("provider_records_returned"),
        "markets_checked_with_provider": candidate_report.get("markets_checked_with_provider"),
        "explicit_outcomes_found": candidate_report.get("explicit_outcomes_found"),
        "tiny_provider_mode_requested": candidate_report.get("tiny_provider_mode_requested"),
        "tiny_provider_mode_allowed": candidate_report.get("tiny_provider_mode_allowed"),
        "provider_readiness_status": candidate_report.get("provider_readiness_status"),
        "provider_readiness_blockers": candidate_report.get("provider_readiness_blockers"),
        "provider_config_present": candidate_report.get("provider_config_present"),
        "live_read_enabled": candidate_report.get("live_read_enabled"),
        "credentials_present": candidate_report.get("credentials_present"),
        "pending_records_seen": candidate_report.get("pending_records_seen"),
        "provider_eligible_records": candidate_report.get("provider_eligible_records"),
        "provider_ineligible_records": candidate_report.get("provider_ineligible_records"),
        "provider_ineligible_reason_counts": candidate_report.get("provider_ineligible_reason_counts"),
        "missing_identifier_count": candidate_report.get("missing_identifier_count"),
        "missing_ticker_count": candidate_report.get("missing_ticker_count"),
        "missing_market_id_count": candidate_report.get("missing_market_id_count"),
        "already_settled_or_closed_without_result_count": candidate_report.get("already_settled_or_closed_without_result_count"),
        "local_explicit_outcome_count": candidate_report.get("local_explicit_outcome_count"),
        "provider_selection_limit": candidate_report.get("provider_selection_limit"),
        "provider_selected_count": candidate_report.get("provider_selected_count"),
        "provider_selection_blocker": candidate_report.get("provider_selection_blocker"),
        "why_provider_calls_zero": candidate_report.get("why_provider_calls_zero"),
        "readiness_source": candidate_report.get("readiness_source"),
        "rate_limited": candidate_report.get("rate_limited"),
        "persisted": False,
        "would_persist_outcomes": False,
        **{key: candidate_report.get(key) for key in keys if candidate_report.get(key)},
    }


def _kalshi_env_and_readiness_context(project_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_project_root(project_root or Path(__file__).resolve())
    env_load = load_project_env(root)
    readiness = build_kalshi_readonly_readiness_report(project_root=root, load_env=False, tiny_connectivity_check=False)
    return {
        "env_file_present": bool(env_load.get("env_file_present")),
        "env_loaded": bool(env_load.get("env_loaded")),
        "env_loader": env_load.get("env_loader"),
        "readiness_source": "kalshi_readonly_readiness",
        "readiness_checker_provider_readiness_status": readiness.get("provider_readiness_status"),
        "readiness_checker_provider_readiness_blockers": readiness.get("provider_readiness_blockers", []),
        "readiness_checker_credentials_present": bool(readiness.get("credentials_present")),
        "readiness_checker_live_reads_enabled": bool(readiness.get("live_reads_enabled")),
        "readiness_checker_provider_config_present": bool(readiness.get("provider_config_present")),
        "missing_env_names": list(readiness.get("missing_env_names") or []),
    }


def _readiness_checker_consistent_with_wrapper(readiness_context: dict[str, Any], candidate: dict[str, Any]) -> bool:
    wrapper_status = candidate.get("provider_readiness_status")
    if wrapper_status is None:
        return True
    checker_blockers = sorted(str(item) for item in list(readiness_context.get("readiness_checker_provider_readiness_blockers") or []))
    wrapper_blockers = sorted(str(item) for item in list(candidate.get("provider_readiness_blockers") or []))
    return (
        str(readiness_context.get("readiness_checker_provider_readiness_status") or "") == str(wrapper_status or "")
        and checker_blockers == wrapper_blockers
    )


def render_deepseek_data_pull_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DeepSeek Data Pull Check",
        "",
        f"- created_at: {report.get('created_at')}",
        f"- run_id: {report.get('run_id')}",
        f"- dry_run: {str(report.get('dry_run')).lower()}",
        f"- provider_calls_attempted: {report.get('provider_calls_attempted')}",
        f"- max_provider_calls_effective: {report.get('max_provider_calls_effective')}",
        f"- max_records_effective: {report.get('max_records_effective')}",
        f"- prediction_market_outcome_check_enabled: {str(report.get('prediction_market_outcome_check_enabled')).lower()}",
        f"- candidates_count: {report.get('candidates_count')}",
        f"- env_file_present: {str(report.get('env_file_present')).lower()}",
        f"- env_loaded: {str(report.get('env_loaded')).lower()}",
        f"- env_loader: {report.get('env_loader')}",
        f"- readiness_source: {report.get('readiness_source')}",
        f"- readiness_checker_consistent_with_wrapper: {str(report.get('readiness_checker_consistent_with_wrapper')).lower()}",
        f"- provider_write: {str(report.get('provider_write')).lower()}",
        f"- execution_allowed: {str(report.get('execution_allowed')).lower()}",
        f"- raw_payload_included: {str(report.get('raw_payload_included')).lower()}",
        f"- secrets_included: {str(report.get('secrets_included')).lower()}",
        "",
        "## Input Reports",
    ]
    for item in list(report.get("input_reports") or []):
        lines.append(f"- {item.get('name')}: {item.get('status')} read_ok={item.get('read_ok')}")
    lines.extend(["", "## Recommended Next No-Spend Action", str(report.get("recommended_next_no_spend_action") or "")])
    return "\n".join(lines) + "\n"


def write_deepseek_data_pull_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    root = _report_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10] if created else datetime.now(timezone.utc).date().isoformat()
    run_id = str(report.get("run_id") or sanitize_filename(f"deepseek_data_check_{created}_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{sanitize_filename(run_id)}.json"
    item_md = root / "items" / f"{sanitize_filename(run_id)}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    safe_report = {
        **report,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    markdown = render_deepseek_data_pull_markdown(safe_report)
    for path in (latest_json, item_json, daily_json):
        _atomic_write_json(path, safe_report)
    for path in (latest_md, item_md, daily_md):
        _atomic_write_text(path, markdown)
    return {
        "latest_json_path": _relative(latest_json, base_data_dir),
        "latest_markdown_path": _relative(latest_md, base_data_dir),
        "item_json_path": _relative(item_json, base_data_dir),
        "item_markdown_path": _relative(item_md, base_data_dir),
        "daily_json_path": _relative(daily_json, base_data_dir),
        "daily_markdown_path": _relative(daily_md, base_data_dir),
    }


def build_deepseek_data_pull_check_report(
    *,
    dry_run: bool = True,
    prediction_market_outcome_check: bool = False,
    allow_tiny_provider_calls: bool = False,
    max_provider_calls: int = 0,
    max_records: int = 0,
    module: str | None = None,
    source_id: str | None = None,
    no_deepseek: bool = False,
    app_base_url: str | None = None,
    base_data_dir: str | Path = "data",
    persist: bool = False,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    safe_dry_run = True if dry_run is not False else True
    readiness_context = _kalshi_env_and_readiness_context(project_root)
    call_gate = provider_call_gate(
        dry_run=safe_dry_run,
        allow_tiny_provider_calls=allow_tiny_provider_calls,
        max_provider_calls=max_provider_calls,
        max_records=max_records,
    )
    local_record_limit = DEFAULT_LOCAL_RECORD_SCAN_LIMIT
    candidate_report = None
    if prediction_market_outcome_check:
        candidate_report = build_candidate_report(
            base_data_dir=base_data_dir,
            persist=persist,
            module=module,
            source_id=source_id,
            local_record_limit=local_record_limit,
            allow_tiny_provider_calls=allow_tiny_provider_calls,
            max_provider_calls=max_provider_calls,
            max_records=max_records,
        )
    budget = _registry_budget_summary(module=module, source_id=source_id)
    now = utc_now_iso()
    run_id = sanitize_filename(f"deepseek_data_check_{now.replace(':', '-')}_{uuid4().hex[:8]}")
    candidate = _candidate_summary(candidate_report)
    readiness_consistent = _readiness_checker_consistent_with_wrapper(readiness_context, candidate)
    report = {
        "ok": True,
        "status": "deepseek_data_pull_check_complete",
        "schema_version": DEEPSEEK_DATA_PULL_CHECK_SCHEMA_VERSION,
        "created_at": now,
        "run_id": run_id,
        "dry_run": safe_dry_run,
        "persistence_scope": "compact_reports_only",
        "app_base_url": app_base_url or DEFAULT_APP_BASE_URL,
        "module_filter": module,
        "source_id_filter": source_id,
        "deepseek_invocation_enabled": False,
        "no_deepseek": bool(no_deepseek),
        "import_endpoints_called": False,
        "migration_endpoints_called": False,
        "deploy_attempted": False,
        "source_enable_attempted": False,
        "paid_api_calls_attempted": 0,
        "paid_api_calls_allowed": False,
        "paid_sources_enabled": False,
        "input_reports": read_compact_input_reports(base_data_dir=base_data_dir),
        **budget,
        **call_gate,
        **candidate,
        **readiness_context,
        "readiness_checker_consistent_with_wrapper": readiness_consistent,
        "recommended_next_no_spend_action": "no-call audit of existing source reports",
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
        "storage_backend": "file",
        "storage_health": get_storage_health(),
    }
    if persist:
        report.update(write_deepseek_data_pull_report(report, base_data_dir=base_data_dir))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the safe DeepSeek data-pull/check report.")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--prediction-market-outcome-check", action="store_true")
    parser.add_argument("--allow-tiny-provider-calls", action="store_true")
    parser.add_argument("--max-provider-calls", type=int, default=0)
    parser.add_argument("--max-records", type=int, default=0)
    parser.add_argument("--module", default=None)
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--no-deepseek", action="store_true")
    parser.add_argument("--app-base-url", default=DEFAULT_APP_BASE_URL)
    parser.add_argument("--base-data-dir", default="data")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_deepseek_data_pull_check_report(
        dry_run=True,
        prediction_market_outcome_check=args.prediction_market_outcome_check,
        allow_tiny_provider_calls=args.allow_tiny_provider_calls,
        max_provider_calls=args.max_provider_calls,
        max_records=args.max_records,
        module=args.module,
        source_id=args.source_id,
        no_deepseek=args.no_deepseek,
        app_base_url=args.app_base_url,
        base_data_dir=args.base_data_dir,
        persist=args.persist,
        project_root=args.project_root,
    )
    print(json.dumps({
        "ok": report["ok"],
        "status": report["status"],
        "run_id": report["run_id"],
        "latest_json_path": report.get("latest_json_path"),
        "prediction_market_outcome_check_enabled": report.get("prediction_market_outcome_check_enabled"),
        "candidates_count": report.get("candidates_count"),
        "provider_calls_attempted": report["provider_calls_attempted"],
        "max_provider_calls_effective": report["max_provider_calls_effective"],
        "max_records_effective": report["max_records_effective"],
        "provider_calls_succeeded": report.get("provider_calls_succeeded", 0),
        "provider_calls_failed": report.get("provider_calls_failed", 0),
        "markets_checked_with_provider": report.get("markets_checked_with_provider", 0),
        "explicit_outcomes_found": report.get("explicit_outcomes_found", 0),
        "provider_readiness_status": report.get("provider_readiness_status"),
        "provider_readiness_blockers": report.get("provider_readiness_blockers", []),
        "env_file_present": report.get("env_file_present"),
        "env_loaded": report.get("env_loaded"),
        "env_loader": report.get("env_loader"),
        "readiness_source": report.get("readiness_source"),
        "readiness_checker_consistent_with_wrapper": report.get("readiness_checker_consistent_with_wrapper"),
        "missing_env_names": report.get("missing_env_names", []),
        "provider_eligible_records": report.get("provider_eligible_records"),
        "provider_selected_count": report.get("provider_selected_count"),
        "why_provider_calls_zero": report.get("why_provider_calls_zero"),
        "rejected_count": report.get("rejected_count", 0),
        "rate_limited": report.get("rate_limited", False),
        "persisted": False,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
