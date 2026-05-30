from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .institutional_cross_asset_adapters import compact_redact
from .scheduler_config import sanitize_filename, utc_now_iso


def _lab_root(base_data_dir: str = "data") -> Path:
    path = Path(base_data_dir) / "institutional_lab"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(path, json.dumps(compact_redact(payload), separators=(",", ":"), sort_keys=True))


def _rel(base_data_dir: str, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path(base_data_dir).resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _asset_status(calibration: dict[str, Any], asset_class: str) -> str:
    return str(((calibration.get("asset_classes") or {}).get(asset_class) or {}).get("status") or "insufficient_data")


def _top_counts(records: list[dict[str, Any]], field: str, limit: int = 10) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in records:
        values = row.get(field)
        if not isinstance(values, list):
            values = [values] if values else []
        for value in values:
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
    return [{"key": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _value_counts(records: list[dict[str, Any]], field: str, limit: int = 10) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in records:
        value = row.get(field)
        if value:
            counts[str(value)] = counts.get(str(value), 0) + 1
    return [{"key": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def build_daily_report_payload(run_result: dict[str, Any]) -> dict[str, Any]:
    records = [row for row in run_result.get("records", []) if isinstance(row, dict)]
    calibration = dict(run_result.get("calibration") or {})
    asset_reports = calibration.get("asset_classes") or {}
    deepseek = dict(run_result.get("deepseek_review") or {})
    execution = dict(run_result.get("execution_simulation") or {})
    source_counts = dict(run_result.get("source_counts") or {})
    matched_by_asset = {
        asset: int((asset_reports.get(asset) or {}).get("matched_outcomes_count", 0))
        for asset in ("prediction_market", "stock", "bond", "major_asset", "sportsbook")
    }
    insufficient_by_asset = {
        asset: bool((asset_reports.get(asset) or {}).get("insufficient_sample", True))
        for asset in ("prediction_market", "stock", "bond", "major_asset", "sportsbook")
    }
    return {
        "ok": True,
        "date": str(run_result.get("created_at") or utc_now_iso())[:10],
        "run_id": run_result.get("run_id"),
        "asset_classes_available": [asset for asset, count in source_counts.items() if int(count or 0) > 0],
        "records_read": int(run_result.get("records_read", len(records))),
        "records_normalized": int(run_result.get("records_normalized", len(records))),
        "records_with_outcomes": len([row for row in records if row.get("final_outcome") is not None or row.get("final_price") is not None]),
        "prediction_market_status": _asset_status(calibration, "prediction_market"),
        "stock_status": _asset_status(calibration, "stock"),
        "bond_major_asset_status": {
            "bond": _asset_status(calibration, "bond"),
            "major_asset": _asset_status(calibration, "major_asset"),
        },
        "sportsbook_status": _asset_status(calibration, "sportsbook"),
        "calibration_status_by_asset_class": {asset: str((asset_reports.get(asset) or {}).get("status") or "insufficient_data") for asset in ("prediction_market", "stock", "bond", "major_asset", "sportsbook")},
        "matched_outcomes_by_asset_class": matched_by_asset,
        "insufficient_sample_by_asset_class": insufficient_by_asset,
        "top_data_quality_issues": _top_counts(records, "missing_fields"),
        "top_liquidity_issues": _value_counts(records, "liquidity_tier"),
        "top_valuation_mismatches": _top_counts(records, "valuation_mismatches"),
        "top_risk_flags": _top_counts(records, "reason_codes"),
        "execution_desk_status": execution.get("execution_desk_status", "simulation_only"),
        "simulated_tickets_created": int(bool(execution.get("simulated_ticket_created", False))),
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "DeepSeek review status": deepseek.get("status", "disabled"),
        "deepseek_review_status": deepseek.get("status", "disabled"),
        "next_required_data": list(calibration.get("next_required_data") or [])[:25],
        "next_recheck_time": run_result.get("next_recheck_time"),
        "raw_payload_included": False,
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# Institutional Cross-Asset Daily Report - {report.get('date')}",
        "",
        f"- run_id: {report.get('run_id')}",
        f"- records_read: {report.get('records_read')}",
        f"- records_normalized: {report.get('records_normalized')}",
        f"- records_with_outcomes: {report.get('records_with_outcomes')}",
        f"- prediction_market_status: {report.get('prediction_market_status')}",
        f"- stock_status: {report.get('stock_status')}",
        f"- bond_status: {(report.get('bond_major_asset_status') or {}).get('bond')}",
        f"- major_asset_status: {(report.get('bond_major_asset_status') or {}).get('major_asset')}",
        f"- sportsbook_status: {report.get('sportsbook_status')}",
        f"- execution_desk_status: {report.get('execution_desk_status')}",
        f"- simulated_tickets_created: {report.get('simulated_tickets_created')}",
        "- actual_orders_submitted: 0",
        "- actual_bets_submitted: 0",
        "- actual_trades_submitted: 0",
        "- provider_write: false",
        "- execution_allowed: false",
        "- live_execution_enabled: false",
        f"- deepseek_review_status: {report.get('deepseek_review_status')}",
        "",
        "## Next Required Data",
    ]
    for item in report.get("next_required_data") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_run_artifacts(
    run_result: dict[str, Any],
    *,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    root = _lab_root(base_data_dir)
    run_id = str(run_result.get("run_id") or sanitize_filename(utc_now_iso()))
    latest_path = root / "latest.json"
    item_path = root / "items" / f"{sanitize_filename(run_id)}.json"
    report_path = root / "reports" / f"{sanitize_filename(run_id)}.md"
    _atomic_write_json(latest_path, run_result)
    _atomic_write_json(item_path, run_result)
    _atomic_write_text(report_path, render_markdown_report(build_daily_report_payload(run_result)))
    return {
        "latest_path": _rel(base_data_dir, latest_path),
        "item_path": _rel(base_data_dir, item_path),
        "report_path": _rel(base_data_dir, report_path),
    }


def write_daily_report(
    run_result: dict[str, Any],
    *,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    daily = build_daily_report_payload(run_result)
    root = _lab_root(base_data_dir) / "daily"
    json_path = root / f"{sanitize_filename(str(daily['date']))}.json"
    md_path = root / f"{sanitize_filename(str(daily['date']))}.md"
    _atomic_write_json(json_path, daily)
    _atomic_write_text(md_path, render_markdown_report(daily))
    return {
        **daily,
        "daily_report_path": _rel(base_data_dir, json_path),
        "daily_markdown_path": _rel(base_data_dir, md_path),
    }


def load_latest_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    path = _lab_root(base_data_dir) / "latest.json"
    if not path.exists():
        return {
            "ok": True,
            "status": "not_run",
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "raw_payload_included": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "ok": False,
            "status": "malformed_latest_report",
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "raw_payload_included": False,
        }
    payload = compact_redact(payload)
    if isinstance(payload, dict):
        payload["provider_write"] = False
        payload["execution_allowed"] = False
        payload["live_execution_enabled"] = False
        payload["raw_payload_included"] = False
        return payload
    return {"ok": False, "status": "malformed_latest_report", "raw_payload_included": False}


def load_daily_report(*, base_data_dir: str = "data", report_date: str | None = None) -> dict[str, Any]:
    root = _lab_root(base_data_dir) / "daily"
    if report_date:
        path = root / f"{sanitize_filename(report_date)}.json"
    else:
        paths = sorted(root.glob("*.json"))
        path = paths[-1] if paths else root / "missing.json"
    if not path.exists():
        return {
            "ok": True,
            "status": "not_run",
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "raw_payload_included": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "status": "malformed_daily_report", "raw_payload_included": False}
    payload = compact_redact(payload)
    if isinstance(payload, dict):
        payload["provider_write"] = False
        payload["execution_allowed"] = False
        payload["live_execution_enabled"] = False
        payload["raw_payload_included"] = False
        return payload
    return {"ok": False, "status": "malformed_daily_report", "raw_payload_included": False}
