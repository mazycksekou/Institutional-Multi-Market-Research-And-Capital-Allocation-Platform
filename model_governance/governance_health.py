from __future__ import annotations

import json
from pathlib import Path

from .governance_config import default_governance_config
from .governance_report import generate_governance_report
from .model_inventory import inventory_counts


def get_governance_health():
    cfg = default_governance_config()
    counts = inventory_counts()
    report = generate_governance_report()
    reports_dir = Path("data/performance_reports")
    backtest_ready_count = 0
    blocked_by_performance_count = 0
    blocked_by_calibration_count = 0
    if reports_dir.exists():
        for report_path in reports_dir.glob("*.json"):
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if str(payload.get("performance_status")) == "backtest_complete":
                backtest_ready_count += 1
            blocked_reasons = set(payload.get("blocked_reasons", []))
            if "blocked_by_performance" in blocked_reasons:
                blocked_by_performance_count += 1
            if "blocked_by_calibration" in blocked_reasons:
                blocked_by_calibration_count += 1
    return {
        "governance_status": "ok",
        "inventory_count": counts["model_inventory_count"],
        "tier_counts": counts,
        "audit_log_writable": Path("data/governance_audit").exists() or Path("data").exists(),
        "blocked_models_count": report["blocked_model_count"],
        "active_scoring_ready_count": counts["active_scoring_ready_count"],
        "production_candidate_count": counts["production_candidate_count"],
        "human_approval_required": cfg["human_approval_required"],
        "auto_execution_enabled": cfg["auto_execution_enabled"],
        "kelly_risk_status_counts": {"full_kelly_auto_execution_allowed": 0, "review_only": counts["model_inventory_count"]},
        "last_governance_report_id": "governance_report_v1",
        "backtest_ready_count": backtest_ready_count,
        "blocked_by_performance_count": blocked_by_performance_count,
        "blocked_by_calibration_count": blocked_by_calibration_count,
    }
