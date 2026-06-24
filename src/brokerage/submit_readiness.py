"""Live-submit readiness verification scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalState, evaluate_approval_gate
from .client_factory import BrokerClientDescriptor
from .contracts import ExecutionRequest, LedgerEvent, OrderRequest
from .ledger import record_ledger_event
from .live_submit import LiveSubmitDisabledError, LiveSubmitRequest, build_live_submit_request, submit_live_order_disabled
from .orders import build_execution_request, build_order_request


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


def _to_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        candidate = value.as_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    payload: dict[str, Any] = {}
    for name in ("ready", "status", "blockers", "warnings", "metadata", "name", "required", "satisfied", "description", "submit_id", "approval_id", "broker_name", "client_name", "environment"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


def _coerce_approval_state(approval_state: ApprovalState | Mapping[str, Any] | None) -> ApprovalState:
    payload = _to_payload(approval_state)
    return ApprovalState(
        approval_id=str(payload.get("approval_id") or payload.get("state_id") or "submit_readiness_state"),
        status=str(payload.get("status") or "disabled"),
        approved=bool(payload.get("approved", False)),
        denied=bool(payload.get("denied", False)),
        approval_scope=str(payload.get("approval_scope") or "live_activation"),
        approval_source=str(payload.get("approval_source") or "local"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_descriptor(descriptor: BrokerClientDescriptor | Mapping[str, Any] | None) -> BrokerClientDescriptor:
    payload = _to_payload(descriptor)
    return BrokerClientDescriptor(
        broker_name=str(payload.get("broker_name") or payload.get("broker") or "unknown"),
        approval_state_id=payload.get("approval_state_id"),
        client_name=str(payload.get("client_name") or "disabled"),
        environment=str(payload.get("environment") or "disabled"),
        account_id=payload.get("account_id"),
        approval_required=bool(payload.get("approval_required", True)),
        live_trading_allowed=bool(payload.get("live_trading_allowed", False)),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


@dataclass(frozen=True, slots=True)
class SubmitRequirement:
    name: str
    required: bool = True
    satisfied: bool = False
    description: str = ""
    evidence: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = list(self.evidence)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SubmitReadinessState:
    order_request: OrderRequest
    execution_request: ExecutionRequest
    approval_state: ApprovalState
    broker_client_descriptor: BrokerClientDescriptor
    live_submit_request: LiveSubmitRequest
    ledger_event: LedgerEvent | None = None
    requirements: tuple[SubmitRequirement, ...] = ()
    status: str = "disabled"
    ready: bool = False
    submit_path_disabled: bool = True
    live_submit_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["order_request"] = self.order_request.as_dict()
        payload["execution_request"] = self.execution_request.as_dict()
        payload["approval_state"] = self.approval_state.as_dict()
        payload["broker_client_descriptor"] = self.broker_client_descriptor.as_dict()
        payload["live_submit_request"] = self.live_submit_request.as_dict()
        payload["ledger_event"] = self.ledger_event.as_dict() if self.ledger_event is not None else None
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SubmitReadinessResult:
    readiness_id: str
    state: SubmitReadinessState
    ready: bool
    status: str
    satisfied_requirements: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    submit_path_disabled: bool = True
    live_submit_allowed: bool = False
    ledger_event: LedgerEvent | None = None
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.as_dict()
        payload["satisfied_requirements"] = list(self.satisfied_requirements)
        payload["missing_requirements"] = list(self.missing_requirements)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["ledger_event"] = self.ledger_event.as_dict() if self.ledger_event is not None else None
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_requirement(requirement: SubmitRequirement | Mapping[str, Any] | str) -> SubmitRequirement:
    payload = _to_payload(requirement)
    if isinstance(requirement, str):
        payload.setdefault("name", requirement)
    return SubmitRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_submit_readiness_requirements(
    *,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[SubmitRequirement, ...]:
    return (
        SubmitRequirement(name="approval_state_ready", description="Approval state must be satisfied locally.", metadata=dict(metadata or {})),
        SubmitRequirement(name="kill_switch_clear", description="Kill switch must be clear locally.", metadata=dict(metadata or {})),
        SubmitRequirement(name="credential_readiness_ready", description="Credential readiness must be available locally.", metadata=dict(metadata or {})),
        SubmitRequirement(name="broker_client_readiness_ready", description="Broker client readiness must be available locally.", metadata=dict(metadata or {})),
        SubmitRequirement(name="monitoring_readiness_ready", description="Monitoring readiness must be available locally.", metadata=dict(metadata or {})),
        SubmitRequirement(name="rollback_readiness_ready", description="Rollback readiness must be available locally.", metadata=dict(metadata or {})),
        SubmitRequirement(name="live_submit_boundary_disabled", description="The live submit boundary must remain disabled.", metadata=dict(metadata or {})),
    )


def _component_ready(value: Any) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    payload = _to_payload(value)
    ready = bool(payload.get("ready", False))
    status = str(payload.get("status") or ("ready_local_only" if ready else "disabled"))
    blockers = _coerce_text_tuple(payload.get("blockers"))
    warnings = _coerce_text_tuple(payload.get("warnings"))
    if not ready and status.lower() in {"ready", "ready_local_only", "approved", "approved_local_only", "clear", "enabled", "available", "passed", "ok"} and not blockers:
        ready = True
    if blockers:
        ready = False
    return ready, status, blockers, warnings


def _coerce_order_request(order_request: OrderRequest | Mapping[str, Any] | None) -> OrderRequest:
    payload = _to_payload(order_request)
    return build_order_request(payload)


def _coerce_execution_request(
    execution_request: ExecutionRequest | Mapping[str, Any] | None,
    order_request: OrderRequest,
) -> ExecutionRequest:
    if execution_request is None:
        return build_execution_request(order_request)
    payload = _to_payload(execution_request)
    candidate_order = payload.get("order_request")
    if candidate_order is not None:
        candidate_order = _coerce_order_request(candidate_order)
    return build_execution_request(candidate_order or order_request, candidate=payload)


def build_disabled_submit_readiness(
    order_request: OrderRequest | Mapping[str, Any] | None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    approval_state: ApprovalState | Mapping[str, Any] | None = None,
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any] | None = None,
    credential_readiness: Any | None = None,
    monitoring_readiness: Any | None = None,
    rollback_readiness: Any | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SubmitReadinessState:
    order = _coerce_order_request(order_request)
    execution = _coerce_execution_request(execution_request, order)
    approval = _coerce_approval_state(approval_state)
    descriptor = _coerce_descriptor(broker_client_descriptor)
    live_submit_request = build_live_submit_request(order, execution_request=execution, approval_state=approval, broker_client_descriptor=descriptor, metadata=metadata)
    ledger_event = LedgerEvent(
        event_id=f"submit_readiness_{live_submit_request.submit_id}",
        event_type="submit_readiness_evaluated",
        subject_id=live_submit_request.submit_id,
        payload={"live_submit_allowed": False, "submit_path_disabled": True},
        metadata=dict(metadata or {}),
    )
    return SubmitReadinessState(
        order_request=order,
        execution_request=execution,
        approval_state=approval,
        broker_client_descriptor=descriptor,
        live_submit_request=live_submit_request,
        ledger_event=ledger_event,
        requirements=build_submit_readiness_requirements(metadata=metadata),
        status="disabled",
        ready=False,
        submit_path_disabled=True,
        live_submit_allowed=False,
        metadata=dict(metadata or {}),
    )


def evaluate_submit_readiness(
    order_request: OrderRequest | Mapping[str, Any] | None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    approval_state: ApprovalState | Mapping[str, Any] | None = None,
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any] | None = None,
    credential_readiness: Any | None = None,
    monitoring_readiness: Any | None = None,
    rollback_readiness: Any | None = None,
    requirements: Sequence[SubmitRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SubmitReadinessResult:
    state = build_disabled_submit_readiness(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
        credential_readiness=credential_readiness,
        monitoring_readiness=monitoring_readiness,
        rollback_readiness=rollback_readiness,
        metadata=metadata,
    )
    approval_gate = evaluate_approval_gate(state.approval_state)
    kill_ready = False
    kill_status = "disabled"
    if bool(getattr(state.approval_state, "approved", False)):
        kill_ready = True
    cred_ready, cred_status, cred_blockers, cred_warnings = _component_ready(credential_readiness)
    broker_ready, broker_status, broker_blockers, broker_warnings = _component_ready(broker_client_descriptor)
    mon_ready, mon_status, mon_blockers, mon_warnings = _component_ready(monitoring_readiness)
    roll_ready, roll_status, roll_blockers, roll_warnings = _component_ready(rollback_readiness)
    comp_ready = {
        "approval_state_ready": approval_gate.ready,
        "kill_switch_clear": kill_ready,
        "credential_readiness_ready": cred_ready,
        "broker_client_readiness_ready": broker_ready,
        "monitoring_readiness_ready": mon_ready,
        "rollback_readiness_ready": roll_ready,
        "live_submit_boundary_disabled": True,
    }
    comp_status = {
        "approval_state_ready": approval_gate.status,
        "kill_switch_clear": kill_status,
        "credential_readiness_ready": cred_status,
        "broker_client_readiness_ready": broker_status,
        "monitoring_readiness_ready": mon_status,
        "rollback_readiness_ready": roll_status,
        "live_submit_boundary_disabled": "disabled",
    }
    reqs = tuple(_coerce_requirement(item) for item in (requirements if requirements is not None else build_submit_readiness_requirements(metadata=metadata)))
    satisfied = tuple(item.name for item in reqs if item.required and comp_ready.get(item.name, False))
    missing = tuple(item.name for item in reqs if item.required and not comp_ready.get(item.name, False))
    blockers = tuple(
        dict.fromkeys(
            [
                *approval_gate.blockers,
                *cred_blockers,
                *broker_blockers,
                *mon_blockers,
                *roll_blockers,
                *missing,
                "live_submit_disabled",
            ]
        )
    )
    warnings = tuple(dict.fromkeys([*approval_gate.warnings, *cred_warnings, *broker_warnings, *mon_warnings, *roll_warnings, "submit_readiness_remains_disabled_in_this_phase"]))
    ready = not blockers and not missing
    status = "ready_local_only" if ready else "disabled"
    return SubmitReadinessResult(
        readiness_id=f"submit_readiness_{state.live_submit_request.submit_id}",
        state=state,
        ready=ready,
        status=status,
        satisfied_requirements=satisfied,
        missing_requirements=missing,
        blockers=blockers,
        warnings=warnings,
        submit_path_disabled=True,
        live_submit_allowed=False,
        ledger_event=state.ledger_event,
        metadata=dict(metadata or {}),
    )


def verify_submit_path_disabled(
    order_request: OrderRequest | Mapping[str, Any] | None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    approval_state: ApprovalState | Mapping[str, Any] | None = None,
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any] | None = None,
    credential_readiness: Any | None = None,
    monitoring_readiness: Any | None = None,
    rollback_readiness: Any | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SubmitReadinessResult:
    result = evaluate_submit_readiness(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
        credential_readiness=credential_readiness,
        monitoring_readiness=monitoring_readiness,
        rollback_readiness=rollback_readiness,
        metadata=metadata,
    )
    if result.live_submit_allowed:
        raise AssertionError("live submit must remain disabled in this phase")
    return result


__all__ = [
    "SubmitReadinessResult",
    "SubmitReadinessState",
    "SubmitRequirement",
    "build_disabled_submit_readiness",
    "build_submit_readiness_requirements",
    "evaluate_submit_readiness",
    "verify_submit_path_disabled",
]
