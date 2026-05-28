from __future__ import annotations


def get_disabled_auto_execution_policy() -> dict[str, object]:
    return {
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "paper_execution_only": True,
        "human_approval_required": True,
        "status": "disabled_for_v1",
        "reason": "Future-only policy. Live execution is not enabled in automation_scheduler v1.",
    }
