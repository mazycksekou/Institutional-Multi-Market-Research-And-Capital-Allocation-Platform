"""Controlled live-activation readiness scaffold.

This module models the final approval/kill-switch/readiness gate for future
live activation. It is deterministic, local-only, and disabled in this phase.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalRequirement, ApprovalState, build_default_approval_requirements, evaluate_approval_gate
from .kill_switch import KillSwitchState, build_default_kill_switch_state


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
    for name in ("ready", "status", "blockers", "warnings", "metadata", "approval_id", "approval_scope", "approval_source", "approved", "denied", "kill_switch_id", "clear", "reason"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


def _coerce_approval_state(approval_state: ApprovalState | Mapping[str, Any] | None) -> ApprovalState:
    payload = _to_payload(approval_state)
    requirements = payload.get("requirements")
    if isinstance(requirements, Sequence) and not isinstance(requirements, (str, bytes)):
        requirements_payload = []
        for item in requirements:
            item_payload = _to_payload(item)
            requirements_payload.append(
                {
                    "name": str(item_payload.get("name") or item_payload.get("requirement_id") or "unknown"),
                    "required": bool(item_payload.get("required", True)),
                    "satisfied": bool(item_payload.get("satisfied", False)),
                    "description": str(item_payload.get("description") or ""),
                    "evidence": _coerce_text_tuple(item_payload.get("evidence")),
                    "metadata": dict(item_payload.get("metadata") or {k: v for k, v in item_payload.items() if v is not None}),
                }
            )
    else:
        requirements_payload = [item.as_dict() for item in build_default_approval_requirements()]
    requirement_items = tuple(
        ApprovalRequirement(
            name=str(item["name"]),
            required=bool(item["required"]),
            satisfied=bool(item["satisfied"]),
            description=str(item["description"]),
            evidence=tuple(item["evidence"]),
            metadata=dict(item["metadata"]),
        )
        for item in requirements_payload
    )
    return ApprovalState(
        approval_id=str(payload.get("approval_id") or payload.get("state_id") or "activation_state"),
        status=str(payload.get("status") or "disabled"),
        approved=bool(payload.get("approved", False)),
        denied=bool(payload.get("denied", False)),
        approval_scope=str(payload.get("approval_scope") or "live_activation"),
        approval_source=str(payload.get("approval_source") or "local"),
        requirements=requirement_items,
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_kill_switch_state(kill_switch_state: KillSwitchState | Mapping[str, Any] | None) -> KillSwitchState:
    payload = _to_payload(kill_switch_state)
    return KillSwitchState(
        kill_switch_id=str(payload.get("kill_switch_id") or "live_trading_kill_switch"),
        clear=bool(payload.get("clear", False)),
        status=str(payload.get("status") or ("clear" if bool(payload.get("clear", False)) else "blocked")),
        reason=str(payload.get("reason") or "live_trading_disabled"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_requirement_payload(requirement: ActivationRequirement | Mapping[str, Any]) -> ActivationRequirement:
    payload = _to_payload(requirement)
    return ActivationRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _component_payload(value: Any) -> dict[str, Any]:
    return _to_payload(value)


def _component_ready(value: Any, *, ready_statuses: Sequence[str] = ("ready", "ready_local_only", "approved_local_only", "approved", "clear", "enabled", "available", "passed", "ok")) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    payload = _component_payload(value)
    blockers = _coerce_text_tuple(payload.get("blockers"))
    warnings = _coerce_text_tuple(payload.get("warnings"))
    ready = bool(payload.get("ready", False))
    status = str(payload.get("status") or ("ready_local_only" if ready else "disabled"))
    if not ready and status.lower() in {item.lower() for item in ready_statuses} and not blockers:
        ready = True
    if blockers:
        ready = False
    return ready, status, blockers, warnings


@dataclass(frozen=True, slots=True)
class ActivationRequirement:
    """Local metadata describing a single activation requirement."""

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


def build_default_activation_requirements() -> tuple[ActivationRequirement, ...]:
    """Return the local approval checklist for controlled activation."""

    return (
        ActivationRequirement(name="approval_state_ready", description="Approval state must be satisfied locally."),
        ActivationRequirement(name="kill_switch_clear", description="Kill switch must be clear locally."),
        ActivationRequirement(name="credential_readiness_ready", description="Credential readiness metadata must be ready."),
        ActivationRequirement(name="broker_client_readiness_ready", description="Broker client readiness metadata must be ready."),
        ActivationRequirement(name="monitoring_readiness_ready", description="Monitoring readiness metadata must be ready."),
        ActivationRequirement(name="rollback_readiness_ready", description="Rollback readiness metadata must be ready."),
    )


@dataclass(frozen=True, slots=True)
class ActivationState:
    """Explicit local activation state for future live activation."""

    activation_id: str
    approval_state: ApprovalState
    kill_switch_state: KillSwitchState
    credential_readiness: Any | None = None
    broker_client_readiness: Any | None = None
    monitoring_readiness: Any | None = None
    rollback_readiness: Any | None = None
    activation_scope: str = "live_activation"
    status: str = "disabled"
    live_activation_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["kill_switch_state"] = self.kill_switch_state.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ActivationGateResult:
    """Evaluation result for controlled live activation readiness."""

    decision_id: str
    approved: bool
    status: str
    gate_status: str
    satisfied_requirements: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    message: str = ""
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["satisfied_requirements"] = list(self.satisfied_requirements)
        payload["missing_requirements"] = list(self.missing_requirements)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ActivationReadiness:
    """Structured readiness snapshot for controlled live activation."""

    ready: bool
    status: str
    activation_state: ActivationState
    gate_result: ActivationGateResult
    requirements: tuple[ActivationRequirement, ...]
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    approval_gate_status: str = "disabled"
    kill_switch_status: str = "blocked"
    credential_readiness_status: str = "disabled"
    broker_client_readiness_status: str = "disabled"
    monitoring_readiness_status: str = "disabled"
    rollback_readiness_status: str = "disabled"
    live_activation_allowed: bool = False
    approval_required: bool = True
    kill_switch_required: bool = True
    credentials_required: bool = True
    broker_required: bool = True
    monitoring_required: bool = True
    rollback_required: bool = True
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["activation_state"] = self.activation_state.as_dict()
        payload["gate_result"] = self.gate_result.as_dict()
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


class ActivationBlockedError(RuntimeError):
    """Raised when controlled activation readiness is not satisfied."""


def _coerce_state(state: ActivationState | Mapping[str, Any] | None) -> ActivationState:
    payload = _to_payload(state)
    approval_state = _coerce_approval_state(payload.get("approval_state"))
    kill_switch_state = _coerce_kill_switch_state(payload.get("kill_switch_state"))
    return ActivationState(
        activation_id=str(payload.get("activation_id") or payload.get("state_id") or "activation_state"),
        approval_state=approval_state,
        kill_switch_state=kill_switch_state,
        credential_readiness=payload.get("credential_readiness"),
        broker_client_readiness=payload.get("broker_client_readiness"),
        monitoring_readiness=payload.get("monitoring_readiness"),
        rollback_readiness=payload.get("rollback_readiness"),
        activation_scope=str(payload.get("activation_scope") or "live_activation"),
        status=str(payload.get("status") or "disabled"),
        live_activation_allowed=bool(payload.get("live_activation_allowed", False)),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_disabled_activation_state(
    *,
    approval_state: ApprovalState | Mapping[str, Any] | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    credential_readiness: Any | None = None,
    broker_client_readiness: Any | None = None,
    monitoring_readiness: Any | None = None,
    rollback_readiness: Any | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ActivationState:
    approval = _coerce_approval_state(approval_state or ApprovalState(approval_id="activation_disabled", requirements=build_default_approval_requirements()))
    kill_switch = _coerce_kill_switch_state(kill_switch_state or build_default_kill_switch_state())
    return ActivationState(
        activation_id="activation_disabled",
        approval_state=approval,
        kill_switch_state=kill_switch,
        credential_readiness=credential_readiness,
        broker_client_readiness=broker_client_readiness,
        monitoring_readiness=monitoring_readiness,
        rollback_readiness=rollback_readiness,
        activation_scope="live_activation",
        status="disabled",
        live_activation_allowed=False,
        metadata=dict(metadata or {}),
    )


def evaluate_activation_readiness(
    activation_state: ActivationState | Mapping[str, Any] | None = None,
    *,
    requirements: Sequence[ActivationRequirement | Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ActivationReadiness:
    state = _coerce_state(activation_state)
    requirement_items = tuple(_coerce_requirement_payload(item) for item in (requirements if requirements is not None else build_default_activation_requirements()))

    approval_gate = evaluate_approval_gate(state.approval_state)
    kill_ready = bool(state.kill_switch_state.clear)
    kill_status = "clear" if kill_ready else "blocked"
    credential_ready, credential_status, credential_blockers, credential_warnings = _component_ready(state.credential_readiness)
    broker_ready, broker_status, broker_blockers, broker_warnings = _component_ready(state.broker_client_readiness)
    monitoring_ready, monitoring_status, monitoring_blockers, monitoring_warnings = _component_ready(state.monitoring_readiness)
    rollback_ready, rollback_status, rollback_blockers, rollback_warnings = _component_ready(state.rollback_readiness)

    component_ready_map = {
        "approval_state_ready": approval_gate.ready,
        "kill_switch_clear": kill_ready,
        "credential_readiness_ready": credential_ready,
        "broker_client_readiness_ready": broker_ready,
        "monitoring_readiness_ready": monitoring_ready,
        "rollback_readiness_ready": rollback_ready,
    }
    component_status_map = {
        "approval_state_ready": approval_gate.status,
        "kill_switch_clear": kill_status,
        "credential_readiness_ready": credential_status,
        "broker_client_readiness_ready": broker_status,
        "monitoring_readiness_ready": monitoring_status,
        "rollback_readiness_ready": rollback_status,
    }
    component_blockers = [
        *approval_gate.blockers,
        *credential_blockers,
        *broker_blockers,
        *monitoring_blockers,
        *rollback_blockers,
    ]
    component_warnings = [
        *approval_gate.warnings,
        *credential_warnings,
        *broker_warnings,
        *monitoring_warnings,
        *rollback_warnings,
    ]

    satisfied = tuple(item.name for item in requirement_items if item.required and component_ready_map.get(item.name, False))
    missing = tuple(item.name for item in requirement_items if item.required and not component_ready_map.get(item.name, False))
    blockers = tuple(dict.fromkeys([*missing, *component_blockers]))
    warnings = tuple(dict.fromkeys([*component_warnings, "controlled_activation_remains_disabled_in_this_phase"]))
    ready = not blockers and not missing
    status = "ready_local_only" if ready else "activation_blocked"
    gate_result = ActivationGateResult(
        decision_id=f"{state.activation_id}:decision",
        approved=ready,
        status=status,
        gate_status=status,
        satisfied_requirements=satisfied,
        missing_requirements=missing,
        blocked_reasons=blockers,
        message="activation requirements satisfied for local evaluation only" if ready else "activation readiness requirements are not yet satisfied",
        metadata=dict(metadata or {}),
    )
    return ActivationReadiness(
        ready=ready,
        status=status,
        activation_state=state,
        gate_result=gate_result,
        requirements=tuple(
            ActivationRequirement(
                name=item.name,
                required=item.required,
                satisfied=component_ready_map.get(item.name, False),
                description=item.description,
                evidence=(component_status_map.get(item.name, "disabled"),),
                metadata=dict(item.metadata),
            )
            for item in requirement_items
        ),
        blockers=blockers,
        warnings=warnings,
        approval_gate_status=approval_gate.status,
        kill_switch_status=kill_status,
        credential_readiness_status=credential_status,
        broker_client_readiness_status=broker_status,
        monitoring_readiness_status=monitoring_status,
        rollback_readiness_status=rollback_status,
        live_activation_allowed=False,
        approval_required=True,
        kill_switch_required=True,
        credentials_required=True,
        broker_required=True,
        monitoring_required=True,
        rollback_required=True,
        metadata=dict(metadata or {}),
    )


def require_activation_ready(
    activation_state: ActivationState | Mapping[str, Any] | None = None,
    *,
    requirements: Sequence[ActivationRequirement | Mapping[str, Any]] | None = None,
) -> ActivationGateResult:
    readiness = evaluate_activation_readiness(activation_state, requirements=requirements)
    if readiness.ready:
        return readiness.gate_result
    raise ActivationBlockedError(readiness.gate_result.message)


__all__ = [
    "ActivationBlockedError",
    "ActivationGateResult",
    "ActivationReadiness",
    "ActivationRequirement",
    "ActivationState",
    "build_default_activation_requirements",
    "build_disabled_activation_state",
    "evaluate_activation_readiness",
    "require_activation_ready",
]
