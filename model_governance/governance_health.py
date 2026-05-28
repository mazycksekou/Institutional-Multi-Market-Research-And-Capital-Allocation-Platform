from __future__ import annotations

from pathlib import Path

from .governance_config import default_governance_config
from .governance_report import generate_governance_report
from .model_inventory import inventory_counts


def get_governance_health():
    cfg = default_governance_config()
    counts = inventory_counts()
    report = generate_governance_report()
    return {"governance_status": "ok", "inventory_count": counts["model_inventory_count"], "tier_counts": counts, "audit_log_writable": Path("data/governance_audit").exists() or Path("data").exists(), "blocked_models_count": report["blocked_model_count"], "active_scoring_ready_count": counts["active_scoring_ready_count"], "production_candidate_count": counts["production_candidate_count"], "human_approval_required": cfg["human_approval_required"], "auto_execution_enabled": cfg["auto_execution_enabled"], "kelly_risk_status_counts": {"full_kelly_auto_execution_allowed": 0, "review_only": counts["model_inventory_count"]}, "last_governance_report_id": "governance_report_v1"}
