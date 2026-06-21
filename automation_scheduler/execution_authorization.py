from __future__ import annotations

from typing import Any

from .audit_ledger import append_security_event
from .owner_approval_gate import evaluate_owner_approval
from .provider_allowlist import classify_provider
from src.providers.policy.write_firewall import check_provider_write_attempt
from .risk_limit_guard import evaluate_risk_limits
from .secret_safety import secret_safety_fields
from .security_event_types import EXECUTION_ATTEMPT_BLOCKED
from .security_policy import kill_switch_state, locked_safety_flags


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
    request = request if isinstance(request, dict) else {}
    provider = str(request.get("provider") or "unknown")
    action = str(request.get("action") or request.get("order_action") or "unknown")
    provider_class = classify_provider(provider)
    requested_scope = {
        "action": action,
        "asset_type": request.get("asset_type"),
        "market_type": request.get("market_type"),
        "provider": provider,
        "max_size": request.get("max_size"),
        "max_notional": request.get("max_notional"),
        "time_window": request.get("time_window"),
    }
    owner = evaluate_owner_approval(owner_approval, requested_scope=requested_scope, persist_audit=False, base_data_dir=base_data_dir)
    risk = evaluate_risk_limits(request, risk_limits=risk_limits, persist_audit=False, base_data_dir=base_data_dir)
    write = check_provider_write_attempt(
        provider=provider,
        action=action,
        request_payload=request,
        owner_approval=owner_approval,
        risk_limits=risk_limits,
        idempotency_key=idempotency_key,
        execution_mode=execution_mode,
        persist_audit=False,
        base_data_dir=base_data_dir,
    )
    kill_switches = kill_switch_state()
    hard_gates = {
        "global_live_execution_enabled": False,
        "provider_specific_execution_enabled": False,
        "provider_write_allowed": False,
        "owner_approval_valid": bool(owner["ok"]),
        "risk_limits_pass": bool(risk["ok"]),
        "kill_switch_inactive": not bool(kill_switches["kill_switches_active"]),
        "provider_allowlist_pass": False,
        "market_open_valid": bool(request.get("market_open_valid", False)),
        "data_integrity_pass": bool(request.get("data_integrity_pass", False)),
        "secret_safety_pass": True,
        "audit_ledger_write_required": True,
        "idempotency_key_present": bool(idempotency_key),
        "replay_protection_pass": False,
        "execution_mode_valid": execution_mode in {"sandbox_owner_approved", "live_owner_approved"},
        "dry_run_sandbox_promotion_approved": False,
    }
    blockers = [name for name, passed in hard_gates.items() if not passed]
    blockers.extend(write.get("write_blockers", []))
    result = {
        "ok": False,
        "status": "execution_attempt_blocked",
        "provider_name": provider,
        "provider_class": provider_class,
        "action_requested": action,
        "hard_gates": hard_gates,
        "execution_blockers": sorted(set(blockers)),
        "owner_approval_status": owner["approval_status"],
        "risk_limit_status": risk["risk_limit_status"],
        "provider_write_firewall_status": write["status"],
        "execution_mode": execution_mode,
        "execution_considered_for_future_only": True,
        "at_least_one_required_hard_gate_false": any(not value for value in hard_gates.values()),
        **secret_safety_fields(source_payload=request),
        **locked_safety_flags(),
    }
    if persist_audit:
        append_security_event(
            event_type=EXECUTION_ATTEMPT_BLOCKED,
            actor_type=str(request.get("actor_type") or "system"),
            actor_provider=str(request.get("actor_provider") or ""),
            action_requested=action,
            denial_reason=";".join(result["execution_blockers"]),
            asset_type=request.get("asset_type"),
            market_type=request.get("market_type"),
            provider_name=provider,
            request_payload=request,
            response_payload=result,
            base_data_dir=base_data_dir,
        )
    return result
