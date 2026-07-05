from __future__ import annotations

from typing import Any, Mapping

from src.data.data_paths import get_storage_health
from src.providers.policy.allowlist import classify_provider

from .owner_approval_gate import evaluate_owner_approval
from .policy import kill_switch_state, locked_safety_flags
from .risk_limit_guard import evaluate_risk_limits
from .secret_safety import redact_sensitive, secret_safety_fields


HARD_GATE_NAMES = (
    "global_execution_enabled",
    "provider_execution_enabled",
    "provider_write_allowed",
    "owner_approval_valid",
    "human_approval_required",
    "kill_switch_inactive",
    "provider_allowlist_passed",
    "risk_limits_passed",
    "market_valid",
    "data_integrity_passed",
    "secret_safety_passed",
    "audit_ledger_write_ok",
    "idempotency_key_present",
    "replay_protection_passed",
    "dry_run_promotion_allowed",
    "execution_mode_valid",
)

VALID_EXECUTION_MODES = {"sandbox_owner_approved", "live_owner_approved"}
ANALYSIS_PROVIDER_CLASSES = {"deepseek", "openai", "internal_deterministic"}

__all__ = [
    "HARD_GATE_NAMES",
    "VALID_EXECUTION_MODES",
    "ANALYSIS_PROVIDER_CLASSES",
    "evaluate_hard_gates",
]


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "pass", "passed", "active", "valid"}
    return bool(value)


def _provider_allowlist_passed(request: Mapping[str, Any]) -> bool:
    provider = str(request.get("provider") or request.get("provider_id") or "")
    provider_type = request.get("provider_type")
    provider_class = classify_provider(provider, provider_type=provider_type)
    if provider_class in {"broker", "sportsbook", "kalshi_order", "crypto_exchange", "exchange", "execution_provider"}:
        return False
    return provider_class in ANALYSIS_PROVIDER_CLASSES


def evaluate_hard_gates(
    request: Mapping[str, Any] | None = None,
    *,
    owner_approval: Mapping[str, Any] | None = None,
    risk_limits: Mapping[str, Any] | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    required_gates: list[str] | tuple[str, ...] | None = None,
    gate_overrides: Mapping[str, Any] | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = False,
) -> dict[str, Any]:
    safe_request = redact_sensitive(dict(request or {}))
    provider = str(safe_request.get("provider") or safe_request.get("provider_id") or "unknown")
    action = str(safe_request.get("action") or safe_request.get("order_action") or "future_execution_review")
    mode = execution_mode or safe_request.get("execution_mode")
    idem = idempotency_key or safe_request.get("idempotency_key")
    requested_scope = {
        "action": action,
        "asset_type": safe_request.get("asset_type"),
        "market_type": safe_request.get("market_type"),
        "provider": provider,
        "max_size": safe_request.get("max_size"),
        "max_notional": safe_request.get("max_notional"),
        "time_window": safe_request.get("time_window"),
    }
    owner = evaluate_owner_approval(
        dict(owner_approval or {}),
        requested_scope=requested_scope,
        actor_type=str(safe_request.get("actor_type") or "system"),
        base_data_dir=base_data_dir,
        persist_audit=persist_audit,
    )
    risk = evaluate_risk_limits(dict(safe_request), risk_limits=dict(risk_limits or {}), base_data_dir=base_data_dir, persist_audit=persist_audit)
    kill = kill_switch_state()
    storage = get_storage_health()
    secret = secret_safety_fields(source_payload=request, redacted_payload=safe_request)
    replay_detected = _truthy(safe_request.get("replay_detected")) or bool(owner.get("approval_replay_detected"))
    gates = {
        "global_execution_enabled": False,
        "provider_execution_enabled": False,
        "provider_write_allowed": False,
        "owner_approval_valid": bool(owner.get("ok")),
        "human_approval_required": True,
        "kill_switch_inactive": not bool(kill.get("kill_switches_active")),
        "provider_allowlist_passed": _provider_allowlist_passed(safe_request),
        "risk_limits_passed": bool(risk.get("ok")),
        "market_valid": _truthy(safe_request.get("market_valid") or safe_request.get("market_open_valid")),
        "data_integrity_passed": _truthy(safe_request.get("data_integrity_passed") or safe_request.get("data_integrity_pass")),
        "secret_safety_passed": not bool(secret.get("redacted_payload_contains_secret")),
        "audit_ledger_write_ok": bool(storage.get("write_ok")),
        "idempotency_key_present": bool(idem),
        "replay_protection_passed": bool(idem) and not replay_detected,
        "dry_run_promotion_allowed": _truthy(safe_request.get("dry_run_promotion_allowed")),
        "execution_mode_valid": str(mode or "") in VALID_EXECUTION_MODES,
    }
    for key, value in dict(gate_overrides or {}).items():
        if key in gates:
            gates[key] = _truthy(value)

    required = list(required_gates or HARD_GATE_NAMES)
    failed = [name for name in required if not bool(gates.get(name))]
    return {
        "ok": not bool(failed),
        "status": "hard_gates_passed_future_only" if not failed else "execution_blocked_by_hard_gates",
        "hard_gate_status": "passed_future_only" if not failed else "locked",
        "hard_gates": gates,
        "required_hard_gates": required,
        "failed_hard_gates": failed,
        "execution_blocked": bool(failed),
        "at_least_one_required_hard_gate_false": bool(failed),
        "future_execution_review_only": True,
        "provider": provider,
        "provider_class": classify_provider(provider, provider_type=safe_request.get("provider_type")),
        "action_requested": action,
        "owner_approval_status": owner.get("approval_status"),
        "risk_limit_status": risk.get("risk_limit_status"),
        "risk_blockers": list(risk.get("risk_blockers") or [])[:20],
        "kill_switch_status": kill.get("status"),
        "storage": storage,
        **secret,
        **locked_safety_flags(),
    }

