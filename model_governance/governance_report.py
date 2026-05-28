from __future__ import annotations

from pathlib import Path

from .model_inventory import get_model_inventory, inventory_counts


def generate_governance_report():
    inv = get_model_inventory()
    counts = inventory_counts()
    blocked = [i for i in inv if i["activation_tier"] in {"research_only", "backtest_ready", "paper_trade_ready"}]
    audits = list(Path("data/governance_audit").glob("*.json")) if Path("data/governance_audit").exists() else []
    return {"inventory_summary": {"total": len(inv)}, "tier_counts": counts, "blocked_model_count": len(blocked), "eligible_model_count": len(inv) - len(blocked), "models_needing_validation": [i["model_id"] for i in blocked], "models_with_drift": [], "models_blocked_by_input_quality": [], "models_blocked_by_risk": [], "models_blocked_by_settlement": [], "models_blocked_by_Kelly": [], "audit_summary": {"records": len(audits)}, "recommended_next_actions": ["review_required"]}
