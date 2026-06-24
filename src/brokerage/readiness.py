"""Disabled execution readiness helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from automation_scheduler.owner_approval_gate import evaluate_owner_approval
from automation_scheduler.provider_allowlist import classify_provider
from automation_scheduler.risk_limit_guard import evaluate_risk_limits
from automation_scheduler.secret_safety import redact_sensitive, secret_safety_fields
from automation_scheduler.security_event_types import EXECUTION_ATTEMPT_BLOCKED
from automation_scheduler.security_policy import locked_safety_flags
from src.services.ledger_service import append_security_event
from src.providers.policy.write_firewall import check_provider_write_attempt

from .contracts import ExecutionMode, ExecutionReadiness, ExecutionRequest, OrderRequest, PositionSnapshot
from .orders import build_execution_request, build_order_request
from .positions import build_position_snapshot


def _coerce_order_request(order_request: OrderRequest | Mapping[str, Any] | None) -> OrderRequest | None:
    if order_request is None:
        return None
    if isinstance(order_request, OrderRequest):
        return order_request
    if isinstance(order_request, Mapping):
        return build_order_request(order_request)
    return None


def _coerce_execution_request(
    execution_request: ExecutionRequest | Mapping[str, Any] | None,
    order_request: OrderRequest | None,
) -> ExecutionRequest | None:
    if execution_request is None:
        if order_request is None:
            return None
        return build_execution_request(order_request)
    if isinstance(execution_request, ExecutionRequest):
        return execution_request
    if isinstance(execution_request, Mapping):
        candidate_order = execution_request.get("order_request")
        if not isinstance(candidate_order, OrderRequest) and candidate_order is not None:
            candidate_order = _coerce_order_request(candidate_order)
        return build_execution_request(candidate_order or order_request, candidate=execution_request)
    return None


def _coerce_position_snapshot(position_snapshot: PositionSnapshot | Mapping[str, Any] | None) -> PositionSnapshot | None:
    if position_snapshot is None:
        return None
    if isinstance(position_snapshot, PositionSnapshot):
        return position_snapshot
    if isinstance(position_snapshot, Mapping):
        return build_position_snapshot(position_snapshot)
    return None


def get_execution_readiness(
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    position_snapshot: PositionSnapshot | Mapping[str, Any] | None = None,
    execution_mode: ExecutionMode | str = ExecutionMode.DISABLED,
    allow_live: bool = False,
    extra_blockers: Sequence[str] | None = None,
    extra_warnings: Sequence[str] | None = None,
) -> ExecutionReadiness:
    order = _coerce_order_request(order_request)
    execution = _coerce_execution_request(execution_request, order)
    position = _coerce_position_snapshot(position_snapshot)
    blockers = [
        "broker_boundary_disabled",
        "live_trading_deferred",
    ]
    warnings = [
        "disabled_execution_boundary_only",
    ]
    if order is None:
        blockers.append("missing_order_request")
    if execution is None:
        blockers.append("missing_execution_request")
    if position is None:
        warnings.append("position_snapshot_optional")
    if not allow_live:
        blockers.append("allow_live_false")
    if extra_blockers:
        blockers.extend(str(item) for item in extra_blockers if item)
    if extra_warnings:
        warnings.extend(str(item) for item in extra_warnings if item)
    if isinstance(execution_mode, ExecutionMode):
        mode = execution_mode
    else:
        mode_text = str(execution_mode or "").strip().lower()
        mode = ExecutionMode(mode_text) if mode_text in ExecutionMode._value2member_map_ else ExecutionMode.DISABLED
    return ExecutionReadiness(
        ready=False,
        status="disabled" if mode == ExecutionMode.DISABLED else "live_trading_deferred",
        execution_mode=mode,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        order_request=order,
        execution_request=execution,
        position_snapshot=position,
        brokerage_boundary_disabled=True,
        live_trading_allowed=False,
        account_required=True,
        credentials_required=True,
    )


def _as_score(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def _disabled_hard_gate_result() -> dict[str, Any]:
    return {
        "failed_hard_gates": True,
        "hard_gate_status": "locked",
        "kill_switch_inactive": False,
        "global_live_execution_enabled": False,
        "provider_specific_execution_enabled": False,
        "provider_write_allowed": False,
    }


def evaluate_future_execution_eligibility(
    candidate: Mapping[str, Any] | None = None,
    *,
    aggregate: Mapping[str, Any] | None = None,
    hard_gate_result: Mapping[str, Any] | None = None,
    actor_type: str = "system",
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    aggregate = redact_sensitive(dict(aggregate or {}))
    violations = []
    if bool(safe_candidate.get("execution_allowed")) or bool(aggregate.get("execution_allowed")):
        violations.append("execution_authority_requires_explicit_disable")
    blockers: list[str] = []
    warnings: list[str] = []

    if actor_type == "ai_provider":
        if bool(safe_candidate.get("future_execution_eligible")) or bool(aggregate.get("future_execution_eligible")):
            blockers.append("ai_cannot_set_future_execution_eligible")
        if bool(safe_candidate.get("execution_allowed")) or bool(aggregate.get("execution_allowed")):
            blockers.append("ai_cannot_set_execution_allowed")
    blockers.extend(violations)

    hard = dict(hard_gate_result or _disabled_hard_gate_result())
    if hard.get("failed_hard_gates"):
        blockers.append("hard_security_gate_locked")
    if bool(aggregate.get("fatal_safety_blocker")):
        blockers.append("fatal_safety_blocker")
    if _as_score(aggregate.get("weighted_score")) < 85:
        blockers.append("strategy_evidence_not_strong_enough")
    if _as_score(aggregate.get("calibration_support_score")) < 70:
        blockers.append("calibration_sample_not_sufficient")
    if _as_score(aggregate.get("liquidity_risk_score"), 100.0) > 30:
        blockers.append("liquidity_or_spread_risk_not_acceptable")
    if _as_score(aggregate.get("trap_risk_score"), 100.0) > 30:
        blockers.append("red_team_or_trap_risk_not_clear")

    future_eligible = not bool(blockers)
    if future_eligible:
        warnings.append("future_execution_eligible_is_not_current_execution_authority")

    return {
        "ok": True,
        "status": "future_execution_eligible_review_only" if future_eligible else "future_execution_blocked",
        "candidate_id": safe_candidate.get("candidate_id") or safe_candidate.get("id") or safe_candidate.get("ticker"),
        "future_execution_eligible": bool(future_eligible),
        "future_execution_blockers": sorted(set(blockers)),
        "future_execution_warnings": warnings,
        "hard_gate_status": hard.get("hard_gate_status", "locked"),
        "owner_approval_still_required": True,
        "execution_flags_still_need_explicit_enablement": True,
        **locked_safety_flags(),
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
    kill_switches = {"kill_switches_active": True}
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
