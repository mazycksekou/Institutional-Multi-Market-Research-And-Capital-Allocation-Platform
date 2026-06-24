from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .governance_config import default_governance_config
from .model_inventory import inventory_counts
from .model_inventory import get_model_inventory
from src.analytics.governance import build_governance_health
from src.analytics.reports import (
    build_model_validation_report,
    generate_governance_report as _generate_governance_report,
)


def get_governance_health():
    cfg = default_governance_config()
    counts = inventory_counts()
    audits_dir = Path("data/governance_audit")
    audits = list(audits_dir.glob("*.json")) if audits_dir.exists() else []
    report = _generate_governance_report(get_model_inventory(), counts, audit_records=audits)
    reports_dir = Path("data/performance_reports")
    return build_governance_health(
        counts,
        report,
        config=cfg,
        reports_dir=reports_dir,
        audit_dir=Path("data/governance_audit"),
    )


def generate_governance_report():
    audits = list(Path("data/governance_audit").glob("*.json")) if Path("data/governance_audit").exists() else []
    return _generate_governance_report(get_model_inventory(), inventory_counts(), audit_records=audits)

SCHEMA_VERSION = "model_governance.v1"
BANNED_OUTPUT_TERMS = ("lock", "guaranteed", "risk-free", "sure thing", "can't lose", "cant lose")


def contains_banned_language(value: Any) -> bool:
    rendered = repr(value).lower().replace("\u2019", "'")
    return any(re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", rendered) for term in BANNED_OUTPUT_TERMS)


def safe_decision_label(value: str) -> str:
    if contains_banned_language(value):
        return "blocked_by_governance"
    return value

__all__ = [
    "SCHEMA_VERSION",
    "contains_banned_language",
    "safe_decision_label",
    "default_governance_config",
    "get_model_inventory",
    "generate_governance_report",
    "get_governance_health",
    "build_model_validation_report",
]
