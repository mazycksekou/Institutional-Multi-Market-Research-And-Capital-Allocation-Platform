from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.data.data_paths import get_storage_health, resolve_base_data_dir
from .deepseek_response_validator import (
    compact_redacted_for_deepseek,
    default_daily_report,
    profit_lab_safety_flags,
)
from src.services.scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso


DAILY_REPORT_SCHEMA_VERSION = f"{SCHEMA_VERSION}.deepseek_profit_lab.daily_report.v1"


def _reports_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "deepseek_profit_lab" / "daily_reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _reports_dir(base_data_dir) / "latest.json"


def _report_path(base_data_dir: str, report_date: str) -> Path:
    return _reports_dir(base_data_dir) / f"{sanitize_filename(report_date)}.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def build_local_daily_report(
    summaries: Mapping[str, Any] | None = None,
    *,
    report_date: str | None = None,
    status: str = "local_daily_report",
    reason: str | None = None,
    deepseek_used: bool = False,
) -> dict[str, Any]:
    summaries = summaries or {}
    report = default_daily_report(
        status=status,
        report_date=report_date,
        reason=reason,
        deepseek_used=deepseek_used,
    )
    review_queue = summaries.get("review_queue_summary") if isinstance(summaries.get("review_queue_summary"), Mapping) else {}
    trap_summary = summaries.get("trap_no_bet_summary") if isinstance(summaries.get("trap_no_bet_summary"), Mapping) else {}
    disagreement_summary = summaries.get("disagreement_summary") if isinstance(summaries.get("disagreement_summary"), Mapping) else {}
    provider_health = summaries.get("provider_health_summary") if isinstance(summaries.get("provider_health_summary"), Mapping) else {}

    report["strongest_review_candidates"] = compact_redacted_for_deepseek(
        summaries.get("review_queue_items") or summaries.get("candidates") or [],
        list_limit=10,
    )
    report["strongest_no_bet_no_trade_traps"] = compact_redacted_for_deepseek(
        trap_summary.get("items") if isinstance(trap_summary, Mapping) else [],
        list_limit=10,
    )
    report["missing_data"] = list(
        dict.fromkeys(
            [str(item) for item in (report.get("missing_data") or [])]
            + [str(item) for item in (summaries.get("missing_data") or [])]
        )
    )[:25]
    report["provider_issues"] = [
        str(item)[:240]
        for item in list(provider_health.get("blockers") or provider_health.get("provider_errors") or [])[:25]
    ]
    report["disagreement_count"] = int(disagreement_summary.get("count", 0) or 0)
    report["calibration_improvements"] = [
        str(item)[:240]
        for item in list(
            (summaries.get("calibration_summary") or {}).get("next_required_data")
            or (summaries.get("calibration_summary") or {}).get("warnings")
            or []
        )[:25]
        if str(item).strip()
    ]
    if isinstance(review_queue, Mapping) and int(review_queue.get("execution_allowed_count", 0) or 0) > 0:
        report["safety_status"]["status"] = "execution_flag_anomaly_detected"
    report["safety_status"].update(
        {
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        }
    )
    report.update(profit_lab_safety_flags(deepseek_used=deepseek_used))
    return compact_redacted_for_deepseek(report, list_limit=25)


def write_daily_report(report: Mapping[str, Any], *, base_data_dir: str = "data") -> dict[str, Any]:
    safe = compact_redacted_for_deepseek(dict(report), list_limit=50)
    if not isinstance(safe, dict):
        safe = default_daily_report(status="local_daily_report")
    safe["schema_version"] = DAILY_REPORT_SCHEMA_VERSION
    safe.update(profit_lab_safety_flags(deepseek_used=bool(safe.get("deepseek_used", False))))
    report_date = str(safe.get("date") or utc_now_iso()[:10])
    latest = _latest_path(base_data_dir)
    dated = _report_path(base_data_dir, report_date)
    _atomic_write_json(latest, safe)
    _atomic_write_json(dated, safe)
    return {
        "ok": True,
        "status": "daily_report_written",
        "report_id": safe.get("report_id"),
        "date": report_date,
        "daily_report_path": _project_relative_path(base_data_dir, dated),
        "latest_daily_report_path": _project_relative_path(base_data_dir, latest),
        **profit_lab_safety_flags(deepseek_used=False),
    }


def load_latest_daily_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    if isinstance(payload, Mapping):
        report = compact_redacted_for_deepseek(dict(payload), list_limit=50)
    else:
        report = build_local_daily_report(status="empty")
    return {
        "ok": True,
        "status": "ok",
        "report": report,
        "storage_backend": "file",
        "storage": get_storage_health(),
        **profit_lab_safety_flags(deepseek_used=bool(isinstance(report, Mapping) and report.get("deepseek_used"))),
    }
