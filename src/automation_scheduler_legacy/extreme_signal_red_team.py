from __future__ import annotations

from typing import Any

from .extreme_randomness_diagnostics import diagnose_extreme_randomness
from .security_policy import locked_safety_flags


def run_extreme_signal_red_team(
    candidate: dict[str, Any] | None = None,
    *,
    baseline_values: list[Any] | None = None,
    matrix_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = diagnose_extreme_randomness(candidate, baseline_values=baseline_values, matrix_payload=matrix_payload)
    item = dict(result.get("sample_item") or {})
    adjustment = str(item.get("recommended_action_adjustment") or "none")
    allowed = adjustment in {"none", "downgrade_review", "no_bet", "no_trade", "request_more_data"}
    payload = {
        "ok": True,
        "status": "extreme_signal_red_team_complete",
        "red_team_only": True,
        "research_only": True,
        "diagnostics": result,
        "allowed_adjustment": adjustment if allowed else "request_more_data",
        "can_only_downgrade_or_request_more_data": True,
        "can_approve": False,
        "can_execute": False,
        "can_create_order": False,
        "can_create_bet": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def run_extreme_signal_batch_red_team(
    candidates: list[dict[str, Any]] | None = None,
    *,
    baseline_values: list[Any] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    cap = max(1, min(int(limit or 100), 250))
    diagnostics = [
        run_extreme_signal_red_team(candidate, baseline_values=baseline_values)
        for candidate in (candidates or [])[:cap]
        if isinstance(candidate, dict)
    ]
    payload = {
        "ok": True,
        "status": "extreme_signal_batch_red_team_complete",
        "red_team_only": True,
        "research_only": True,
        "items_received": len(candidates or []),
        "items_diagnosed": len(diagnostics),
        "diagnostics": diagnostics,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
