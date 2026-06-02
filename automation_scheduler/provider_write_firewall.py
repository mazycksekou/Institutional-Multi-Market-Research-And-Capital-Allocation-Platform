from __future__ import annotations

from typing import Any

from .audit_ledger import append_security_event
from .owner_approval_gate import evaluate_owner_approval
from .provider_allowlist import classify_provider
from .risk_limit_guard import evaluate_risk_limits
from .security_event_types import PROVIDER_WRITE_BLOCKED
from .security_policy import kill_switch_state, locked_safety_flags


WRITE_ALLOWLIST: dict[str, set[str]] = {}


def check_provider_write_attempt(
    *,
    provider: str | None,
    action: str | None,
    request_payload: dict[str, Any] | None = None,
    owner_approval: dict[str, Any] | None = None,
    risk_limits: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
) -> dict[str, Any]:
    request_payload = request_payload if isinstance(request_payload, dict) else {}
    provider_name = str(provider or request_payload.get("provider") or "unknown")
    action_name = str(action or request_payload.get("action") or "unknown")
    provider_class = classify_provider(provider_name)
    allowed_actions = WRITE_ALLOWLIST.get(provider_name, set())
    kill_switches = kill_switch_state()
    owner = evaluate_owner_approval(
        owner_approval,
        requested_scope={
            "action": action_name,
            "asset_type": request_payload.get("asset_type"),
            "market_type": request_payload.get("market_type"),
            "provider": provider_name,
            "max_size": request_payload.get("max_size"),
            "max_notional": request_payload.get("max_notional"),
        },
        persist_audit=False,
        base_data_dir=base_data_dir,
    )
    risk = evaluate_risk_limits(request_payload, risk_limits=risk_limits, persist_audit=False, base_data_dir=base_data_dir)
    blockers = []
    if provider_name not in WRITE_ALLOWLIST:
        blockers.append("provider_not_write_allowlisted")
    if action_name not in allowed_actions:
        blockers.append("action_not_write_allowlisted")
    if execution_mode not in {"sandbox_owner_approved", "live_owner_approved"}:
        blockers.append("execution_mode_not_enabled")
    if not owner["ok"]:
        blockers.append(owner["approval_denial_reason"] or "owner_approval_invalid")
    if not risk["ok"]:
        blockers.extend(risk["risk_blockers"])
    if kill_switches["kill_switches_active"]:
        blockers.append("kill_switch_active")
    if not idempotency_key:
        blockers.append("idempotency_key_missing")
    blockers.append("global_execution_locked")
    blockers.append("provider_write_default_false")

    result = {
        "ok": False,
        "status": "provider_write_blocked",
        "provider_name": provider_name,
        "provider_class": provider_class,
        "action_requested": action_name,
        "write_blockers": sorted(set(blockers)),
        "owner_approval_status": owner["approval_status"],
        "risk_limit_status": risk["risk_limit_status"],
        "kill_switches_active": kill_switches["kill_switches_active"],
        "idempotency_key_present": bool(idempotency_key),
        "replay_protection_required": True,
        "audit_ledger_required": True,
        **locked_safety_flags(),
    }
    if persist_audit:
        append_security_event(
            event_type=PROVIDER_WRITE_BLOCKED,
            actor_type=str(request_payload.get("actor_type") or "system"),
            actor_provider=str(request_payload.get("actor_provider") or ""),
            action_requested=action_name,
            denial_reason=";".join(result["write_blockers"]),
            asset_type=request_payload.get("asset_type"),
            market_type=request_payload.get("market_type"),
            provider_name=provider_name,
            request_payload={
                "provider": provider_name,
                "action": action_name,
                "request_payload": request_payload,
                "idempotency_key_present": bool(idempotency_key),
                "execution_mode": execution_mode,
            },
            response_payload=result,
            base_data_dir=base_data_dir,
        )
    return result
