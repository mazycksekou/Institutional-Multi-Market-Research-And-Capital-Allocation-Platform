from __future__ import annotations

from pathlib import Path

from .model_inventory import get_model_inventory, inventory_counts
from src.analytics.reports import generate_governance_report as _generate_governance_report


def generate_governance_report():
    audits = list(Path("data/governance_audit").glob("*.json")) if Path("data/governance_audit").exists() else []
    return _generate_governance_report(get_model_inventory(), inventory_counts(), audit_records=audits)


__all__ = ["generate_governance_report"]
