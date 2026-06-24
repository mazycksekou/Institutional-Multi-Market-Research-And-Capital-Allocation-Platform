from __future__ import annotations

from pathlib import Path

from src.analytics.governance import build_governance_health as _build_governance_health
from src.analytics.reports import generate_governance_report as _generate_governance_report

from .governance_config import default_governance_config
from .model_inventory import inventory_counts
from .model_inventory import get_model_inventory


def get_governance_health():
    cfg = default_governance_config()
    counts = inventory_counts()
    audits_dir = Path("data/governance_audit")
    audits = list(audits_dir.glob("*.json")) if audits_dir.exists() else []
    report = _generate_governance_report(get_model_inventory(), counts, audit_records=audits)
    reports_dir = Path("data/performance_reports")
    return _build_governance_health(
        counts,
        report,
        config=cfg,
        reports_dir=reports_dir,
        audit_dir=Path("data/governance_audit"),
    )
