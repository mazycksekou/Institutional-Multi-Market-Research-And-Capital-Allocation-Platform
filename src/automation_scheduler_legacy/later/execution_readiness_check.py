from __future__ import annotations

from typing import Any


def check_execution_readiness(flags: dict[str, Any]) -> dict[str, object]:
    required_enabled = (
        bool(flags.get("auto_execution_enabled")),
        bool(flags.get("auto_bet_enabled")),
        bool(flags.get("auto_trade_enabled")),
        not bool(flags.get("paper_execution_only", True)),
        not bool(flags.get("human_approval_required", True)),
    )
    ready = all(required_enabled)
    return {
        "ready": ready,
        "status": "ready" if ready else "not_ready",
        "auto_execution_enabled": bool(flags.get("auto_execution_enabled", False)),
        "auto_bet_enabled": bool(flags.get("auto_bet_enabled", False)),
        "auto_trade_enabled": bool(flags.get("auto_trade_enabled", False)),
        "paper_execution_only": bool(flags.get("paper_execution_only", True)),
        "human_approval_required": bool(flags.get("human_approval_required", True)),
    }
