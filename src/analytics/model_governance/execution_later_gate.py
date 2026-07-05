from __future__ import annotations

from .governance_config import default_governance_config


def evaluate_execution_later_gate():
    c = default_governance_config()
    return {**{k: c[k] for k in ["auto_execution_enabled", "auto_bet_enabled", "auto_trade_enabled", "paper_execution_only", "human_approval_required"]}, "result": "not_ready"}
