from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.data_paths import get_runtime_data_path
from src.services.scheduler_config import sanitize_filename, utc_now_iso


def _report_directory(base_dir: str = "data/performance_reports") -> Path:
    normalized = str(base_dir).replace("\\", "/").rstrip("/")
    path = get_runtime_data_path("performance_reports") if normalized == "data/performance_reports" else Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_model_performance_report(report: dict[str, Any], base_dir: str = "data/performance_reports") -> dict[str, Any]:
    report_id = sanitize_filename(report.get("report_id") or f"perf_{report.get('model_id', 'model')}_{utc_now_iso()}")
    full_report = {
        "report_id": report_id,
        "created_at": utc_now_iso(),
        **report,
    }
    path = _report_directory(base_dir) / f"{report_id}.json"
    path.write_text(json.dumps(full_report, indent=2, sort_keys=True), encoding="utf-8")
    compact = build_compact_performance_report(full_report, str(path))
    return {"full_report": full_report, "compact_report": compact, "report_path": str(path)}


def build_compact_performance_report(report: dict[str, Any], report_path: str) -> dict[str, Any]:
    return {
        "ok": True,
        "status": str(report.get("status") or "backtest_complete"),
        "report_id": report.get("report_id"),
        "model_id": report.get("model_id"),
        "sample_size": int(report.get("sample_size", 0)),
        "realized_roi_percent": float(report.get("realized_roi_percent", 0.0)),
        "average_clv_percent": float(report.get("average_clv_percent", 0.0)),
        "positive_clv_rate": float(report.get("positive_clv_rate", 0.0)),
        "max_drawdown_percent": float(report.get("max_drawdown_percent", 0.0)),
        "brier_score": float(report.get("brier_score", 0.0)),
        "calibration_status": report.get("calibration_status"),
        "performance_status": report.get("performance_status"),
        "blocked_reasons": list(report.get("blocked_reasons", []))[:10],
        "recommended_next_action": report.get("recommended_next_action", "watch_recheck"),
        "report_path": report_path,
    }
