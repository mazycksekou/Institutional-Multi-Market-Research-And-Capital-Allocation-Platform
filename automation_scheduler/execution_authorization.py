from __future__ import annotations

from typing import Any

from src.brokerage.readiness import evaluate_execution_authorization as _evaluate_execution_authorization


def kill_switch_state() -> dict[str, Any]:
    return {
        "status": "active",
        "kill_switches_active": True,
        "switches": {"GLOBAL_EXECUTION_KILL_SWITCH": True},
    }


def evaluate_execution_authorization(
    request: dict[str, Any] | None = None,
    *,
    owner_approval: dict[str, Any] | None = None,
    risk_limits: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
) -> dict[str, Any]:
    return _evaluate_execution_authorization(
        request,
        owner_approval=owner_approval,
        risk_limits=risk_limits,
        idempotency_key=idempotency_key,
        execution_mode=execution_mode,
        base_data_dir=base_data_dir,
        persist_audit=persist_audit,
    )
