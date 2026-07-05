"""Sandbox activation composition scaffold.

This module assembles the production-shaped activation inputs under explicit
local approval while keeping live activation disabled.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval_evidence import ApprovalEvidence, ApprovalValidationResult, build_default_approval_evidence, validate_approval_evidence
from .approval import ApprovalRequirement
from .adapter_readiness import BrokerAdapterReadiness, build_broker_adapter_readiness, validate_broker_adapter_readiness
from .credential_readiness import CredentialReadinessState, build_disabled_credential_readiness, evaluate_credential_readiness
from .deployment_readiness import DeploymentReadiness, build_disabled_deployment_readiness, evaluate_deployment_readiness
from .kill_switch import KillSwitchState, build_default_kill_switch_state
from .monitoring import MonitoringReadiness, build_monitoring_readiness, evaluate_monitoring_readiness
from .rollback import RollbackPlan, build_rollback_plan


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    for name in (
        "ready",
        "status",
        "blockers",
        "warnings",
        "metadata",
        "approval_evidence",
        "activation_metadata",
        "broker_readiness",
        "credential_readiness",
        "kill_switch_state",
        "rollback_metadata",
        "monitoring_readiness",
        "deployment_readiness",
    ):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


def _component_status(value: Any, *, default_status: str = "disabled") -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    payload = _to_payload(value)
    ready = bool(payload.get("ready", False))
    status = str(payload.get("status") or (default_status if not ready else "ready_local_only"))
    blockers = _coerce_text_tuple(payload.get("blockers"))
    warnings = _coerce_text_tuple(payload.get("warnings"))
    if not ready and status.lower() in {"ready", "ready_local_only", "approved", "approved_local_only", "clear", "enabled", "available", "passed", "ok", "metadata_only"} and not blockers:
        ready = True
    if blockers:
        ready = False
    return ready, status, blockers, warnings


def _coerce_approval_evidence(value: ApprovalEvidence | Mapping[str, Any] | None) -> ApprovalEvidence:
    if isinstance(value, ApprovalEvidence):
        return value
    if value is None:
        return build_default_approval_evidence()
    return validate_approval_evidence(value).evidence


@dataclass(frozen=True, slots=True)
class SandboxActivationRequest:
    """Local sandbox activation request."""

    sandbox_id: str
    approval_evidence: ApprovalEvidence
    activation_metadata: dict[str, Any] = field(default_factory=dict)
    broker_readiness: Any | None = None
    credential_readiness: Any | None = None
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None
    rollback_metadata: RollbackPlan | Mapping[str, Any] | None = None
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None
    deployment_readiness: DeploymentReadiness | Mapping[str, Any] | None = None
    status: str = "disabled"
    live_activation_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_evidence"] = self.approval_evidence.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxActivationState:
    """Evaluated sandbox activation state."""

    sandbox_id: str
    request: SandboxActivationRequest
    approval_validation: ApprovalValidationResult
    broker_readiness_ready: bool
    credential_readiness_ready: bool
    kill_switch_ready: bool
    rollback_ready: bool
    monitoring_ready: bool
    deployment_ready: bool
    ready: bool = False
    status: str = "disabled"
    live_activation_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    approval_status: str = "not_approved"
    broker_status: str = "disabled"
    credential_status: str = "disabled"
    kill_switch_status: str = "blocked"
    rollback_status: str = "metadata_only"
    monitoring_status: str = "disabled"
    deployment_status: str = "disabled"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["approval_validation"] = self.approval_validation.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxActivationResult:
    """Final sandbox activation proof result."""

    proof_id: str
    state: SandboxActivationState
    proof_passed: bool
    status: str
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    live_activation_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def build_disabled_sandbox_activation(
    *,
    approval_evidence: ApprovalEvidence | Mapping[str, Any] | None = None,
    activation_metadata: Mapping[str, Any] | None = None,
    broker_readiness: Any | None = None,
    credential_readiness: Any | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    rollback_metadata: RollbackPlan | Mapping[str, Any] | None = None,
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    deployment_readiness: DeploymentReadiness | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxActivationRequest:
    evidence = _coerce_approval_evidence(approval_evidence)
    return SandboxActivationRequest(
        sandbox_id="sandbox_activation_disabled",
        approval_evidence=evidence,
        activation_metadata=dict(activation_metadata or {}),
        broker_readiness=broker_readiness,
        credential_readiness=credential_readiness,
        kill_switch_state=kill_switch_state or build_default_kill_switch_state(),
        rollback_metadata=rollback_metadata or build_rollback_plan(),
        monitoring_readiness=monitoring_readiness or build_monitoring_readiness(),
        deployment_readiness=deployment_readiness or build_disabled_deployment_readiness(),
        status="disabled",
        live_activation_allowed=False,
        metadata=dict(metadata or {}),
    )


def _coerce_request(request: SandboxActivationRequest | Mapping[str, Any] | None) -> SandboxActivationRequest:
    if isinstance(request, SandboxActivationRequest):
        return request
    payload = _to_payload(request)
    approval_evidence = payload.get("approval_evidence")
    approval_evidence = _coerce_approval_evidence(approval_evidence)
    return SandboxActivationRequest(
        sandbox_id=str(payload.get("sandbox_id") or "sandbox_activation_disabled"),
        approval_evidence=approval_evidence,
        activation_metadata=dict(payload.get("activation_metadata") or {}),
        broker_readiness=payload.get("broker_readiness"),
        credential_readiness=payload.get("credential_readiness"),
        kill_switch_state=payload.get("kill_switch_state") or build_default_kill_switch_state(),
        rollback_metadata=payload.get("rollback_metadata") or build_rollback_plan(),
        monitoring_readiness=payload.get("monitoring_readiness") or build_monitoring_readiness(),
        deployment_readiness=payload.get("deployment_readiness") or build_disabled_deployment_readiness(),
        status=str(payload.get("status") or "disabled"),
        live_activation_allowed=bool(payload.get("live_activation_allowed", False)),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def evaluate_sandbox_activation(
    sandbox_activation: SandboxActivationRequest | SandboxActivationState | Mapping[str, Any] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxActivationResult:
    request = _coerce_request(sandbox_activation)
    approval_validation = validate_approval_evidence(request.approval_evidence)
    broker_ready, broker_status, broker_blockers, broker_warnings = _component_status(request.broker_readiness)
    credential_ready, credential_status, credential_blockers, credential_warnings = _component_status(request.credential_readiness)
    kill_ready, kill_status, kill_blockers, kill_warnings = _component_status(request.kill_switch_state)
    rollback_ready, rollback_status, rollback_blockers, rollback_warnings = _component_status(request.rollback_metadata)
    monitoring_ready, monitoring_status, monitoring_blockers, monitoring_warnings = _component_status(request.monitoring_readiness)
    deployment_ready, deployment_status, deployment_blockers, deployment_warnings = _component_status(request.deployment_readiness)

    blockers = tuple(
        dict.fromkeys(
            [
                *approval_validation.blocked_reasons,
                *broker_blockers,
                *credential_blockers,
                *kill_blockers,
                *rollback_blockers,
                *monitoring_blockers,
                *deployment_blockers,
            ]
        )
    )
    warnings = tuple(
        dict.fromkeys(
            [
                *approval_validation.warnings,
                *broker_warnings,
                *credential_warnings,
                *kill_warnings,
                *rollback_warnings,
                *monitoring_warnings,
                *deployment_warnings,
                "sandbox_activation_remains_disabled_in_this_phase",
            ]
        )
    )
    ready = bool(
        approval_validation.valid
        and broker_ready
        and credential_ready
        and kill_ready
        and rollback_ready
        and monitoring_ready
        and deployment_ready
    )
    status = "ready_local_only" if ready else "sandbox_activation_blocked"
    state = SandboxActivationState(
        sandbox_id=request.sandbox_id,
        request=request,
        approval_validation=approval_validation,
        broker_readiness_ready=broker_ready,
        credential_readiness_ready=credential_ready,
        kill_switch_ready=kill_ready,
        rollback_ready=rollback_ready,
        monitoring_ready=monitoring_ready,
        deployment_ready=deployment_ready,
        ready=ready,
        status=status,
        live_activation_allowed=False,
        blockers=blockers,
        warnings=warnings,
        approval_status=approval_validation.status,
        broker_status=broker_status,
        credential_status=credential_status,
        kill_switch_status=kill_status,
        rollback_status=rollback_status,
        monitoring_status=monitoring_status,
        deployment_status=deployment_status,
        metadata=dict(metadata or {}),
    )
    proof_passed = bool(approval_validation.approved or approval_validation.valid)
    return SandboxActivationResult(
        proof_id=f"{request.sandbox_id}:proof",
        state=state,
        proof_passed=proof_passed and not state.live_activation_allowed,
        status="sandbox_proof_passed" if proof_passed and not state.live_activation_allowed else "sandbox_proof_blocked",
        blockers=blockers,
        warnings=warnings,
        live_activation_allowed=False,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "SandboxActivationRequest",
    "SandboxActivationResult",
    "SandboxActivationState",
    "build_disabled_sandbox_activation",
    "evaluate_sandbox_activation",
]
