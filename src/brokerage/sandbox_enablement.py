"""Sandbox enablement composition scaffold.

This module assembles the metadata needed to reason about sandbox enablement
without ever enabling live broker behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .activation import ActivationReadiness, build_disabled_activation_state, evaluate_activation_readiness
from .adapter_readiness import BrokerAdapterReadiness, build_broker_adapter_readiness, validate_broker_adapter_readiness
from .approval_evidence import ApprovalEvidence, ApprovalValidationResult, build_default_approval_evidence, validate_approval_evidence
from .credential_readiness import CredentialReadinessState, build_disabled_credential_readiness, evaluate_credential_readiness
from .deployment_readiness import DeploymentReadiness, build_disabled_deployment_readiness, evaluate_deployment_readiness
from .kill_switch import KillSwitchState, build_default_kill_switch_state, require_kill_switch_clear
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
        "activation_readiness",
        "credential_readiness",
        "broker_readiness",
        "kill_switch_state",
        "monitoring_readiness",
        "rollback_readiness",
        "deployment_readiness",
    ):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


def _text_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (list, tuple, set)):
        return tuple(str(item) for item in values if item not in (None, ""))
    return (str(values),)


def _component_ready(value: Any, *, disabled_statuses: tuple[str, ...] = ("disabled",)) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    payload = _to_payload(value)
    ready = bool(payload.get("ready", False))
    status = str(payload.get("status") or ("ready_local_only" if ready else "disabled"))
    blockers = _text_tuple(payload.get("blockers"))
    warnings = _text_tuple(payload.get("warnings"))
    if not ready and status.lower() in {"ready", "ready_local_only", "approved", "approved_local_only", "clear", "enabled", "available", "passed", "ok", "metadata_only"} and not blockers:
        ready = True
    if blockers:
        ready = False
    if status.lower() in disabled_statuses:
        ready = False
    return ready, status, blockers, warnings


def _coerce_approval_evidence(value: ApprovalEvidence | Mapping[str, Any] | None) -> ApprovalEvidence:
    if isinstance(value, ApprovalEvidence):
        return value
    if value is None:
        return build_default_approval_evidence()
    return validate_approval_evidence(value).evidence


@dataclass(frozen=True, slots=True)
class SandboxEnablementRequest:
    """Local sandbox enablement request."""

    enablement_id: str
    approval_evidence: ApprovalEvidence
    activation_readiness: ActivationReadiness | Mapping[str, Any] | None = None
    credential_readiness: CredentialReadinessState | Mapping[str, Any] | None = None
    broker_readiness: BrokerAdapterReadiness | Mapping[str, Any] | None = None
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None
    rollback_readiness: RollbackPlan | Mapping[str, Any] | None = None
    deployment_readiness: DeploymentReadiness | Mapping[str, Any] | None = None
    status: str = "disabled"
    live_enablement_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_evidence"] = self.approval_evidence.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxEnablementState:
    """Evaluated sandbox enablement state."""

    enablement_id: str
    request: SandboxEnablementRequest
    approval_validation: ApprovalValidationResult
    activation_ready: bool
    credential_ready: bool
    broker_ready: bool
    kill_switch_ready: bool
    monitoring_ready: bool
    rollback_ready: bool
    deployment_ready: bool
    ready: bool = False
    status: str = "disabled"
    live_enablement_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["approval_validation"] = self.approval_validation.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxEnablementResult:
    """Final sandbox enablement result."""

    enablement_id: str
    state: SandboxEnablementState
    ready: bool
    status: str
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    live_enablement_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_activation_ready(value: ActivationReadiness | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, ActivationReadiness):
        return bool(value.ready), value.status, tuple(value.blockers), tuple(value.warnings)
    if value is None:
        readiness = evaluate_activation_readiness(build_disabled_activation_state())
        return bool(readiness.ready), readiness.status, tuple(readiness.blockers), tuple(readiness.warnings)
    readiness = evaluate_activation_readiness(value)
    return bool(readiness.ready), readiness.status, tuple(readiness.blockers), tuple(readiness.warnings)


def _coerce_credential_ready(value: CredentialReadinessState | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, CredentialReadinessState):
        readiness = evaluate_credential_readiness(value)
    elif value is None:
        readiness = evaluate_credential_readiness(build_disabled_credential_readiness(broker_name="sandbox-broker"))
    else:
        readiness = evaluate_credential_readiness(value)
    return bool(readiness.ready), readiness.status, tuple(readiness.blockers), tuple(readiness.warnings)


def _coerce_broker_ready(value: BrokerAdapterReadiness | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, BrokerAdapterReadiness):
        readiness = validate_broker_adapter_readiness(value)
    elif value is None:
        readiness = validate_broker_adapter_readiness(
            build_broker_adapter_readiness(
                broker_name="sandbox-broker",
                supported_asset_classes=[{"asset_class": "equity", "supported": False}],
                supported_order_types=[{"order_type": "market", "supported": False}],
                account_capabilities=[{"capability_name": "sandbox_account", "supported": False}],
                reconciliation_capabilities=[{"capability_name": "position_reconciliation", "supported": False}],
            )
        )
    else:
        readiness = validate_broker_adapter_readiness(value)
    return bool(readiness.ready), readiness.status, tuple(readiness.blockers), tuple(readiness.warnings)


def _coerce_kill_switch_ready(value: KillSwitchState | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    try:
        state = require_kill_switch_clear(value)
        return True, state.status, (), ()
    except Exception as exc:  # pragma: no cover - local disabled path
        payload = _to_payload(value)
        status = str(payload.get("status") or "blocked")
        blockers = _text_tuple(payload.get("blockers")) or (str(exc),)
        warnings = _text_tuple(payload.get("warnings"))
        return False, status, blockers, warnings


def _coerce_monitoring_ready(value: MonitoringReadiness | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, MonitoringReadiness):
        readiness = evaluate_monitoring_readiness(value)
    elif value is None:
        readiness = evaluate_monitoring_readiness(build_monitoring_readiness())
    else:
        readiness = evaluate_monitoring_readiness(value)
    return bool(readiness.ready), readiness.status, tuple(readiness.blockers), tuple(readiness.warnings)


def _coerce_rollback_ready(value: RollbackPlan | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, RollbackPlan):
        payload = value.as_dict()
    else:
        payload = _to_payload(value) or build_rollback_plan().as_dict()
    ready = bool(payload.get("steps") or payload.get("status") == "metadata_only")
    status = str(payload.get("status") or "metadata_only")
    blockers = _text_tuple(payload.get("blockers"))
    warnings = _text_tuple(payload.get("warnings"))
    if not ready:
        blockers = tuple(dict.fromkeys([*blockers, "rollback_readiness_disabled"]))
    return ready, status, blockers, warnings


def _coerce_deployment_ready(value: DeploymentReadiness | Mapping[str, Any] | None) -> tuple[bool, str, tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, DeploymentReadiness):
        readiness = evaluate_deployment_readiness(value)
    elif value is None:
        readiness = evaluate_deployment_readiness(build_disabled_deployment_readiness())
    else:
        readiness = evaluate_deployment_readiness(value)
    return bool(readiness.ready), readiness.status, tuple(readiness.blockers), tuple(readiness.warnings)


def build_disabled_enablement(
    *,
    approval_evidence: ApprovalEvidence | Mapping[str, Any] | None = None,
    activation_readiness: ActivationReadiness | Mapping[str, Any] | None = None,
    credential_readiness: CredentialReadinessState | Mapping[str, Any] | None = None,
    broker_readiness: BrokerAdapterReadiness | Mapping[str, Any] | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    rollback_readiness: RollbackPlan | Mapping[str, Any] | None = None,
    deployment_readiness: DeploymentReadiness | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxEnablementRequest:
    """Build a disabled sandbox enablement request."""

    evidence = _coerce_approval_evidence(approval_evidence)
    if activation_readiness is None:
        activation_readiness = evaluate_activation_readiness(build_disabled_activation_state())
    if credential_readiness is None:
        credential_readiness = build_disabled_credential_readiness(broker_name="sandbox-broker")
    if broker_readiness is None:
        broker_readiness = build_broker_adapter_readiness(
            broker_name="sandbox-broker",
            supported_asset_classes=[{"asset_class": "equity", "supported": False}],
            supported_order_types=[{"order_type": "market", "supported": False}],
            account_capabilities=[{"capability_name": "sandbox_account", "supported": False}],
            reconciliation_capabilities=[{"capability_name": "position_reconciliation", "supported": False}],
        )
    if kill_switch_state is None:
        kill_switch_state = build_default_kill_switch_state()
    if monitoring_readiness is None:
        monitoring_readiness = build_monitoring_readiness()
    if rollback_readiness is None:
        rollback_readiness = build_rollback_plan()
    if deployment_readiness is None:
        deployment_readiness = build_disabled_deployment_readiness()
    return SandboxEnablementRequest(
        enablement_id="sandbox_enablement_disabled",
        approval_evidence=evidence,
        activation_readiness=activation_readiness,
        credential_readiness=credential_readiness,
        broker_readiness=broker_readiness,
        kill_switch_state=kill_switch_state,
        monitoring_readiness=monitoring_readiness,
        rollback_readiness=rollback_readiness,
        deployment_readiness=deployment_readiness,
        status="disabled",
        live_enablement_allowed=False,
        metadata=dict(metadata or {}),
    )


def evaluate_enablement(
    sandbox_enablement: SandboxEnablementRequest | Mapping[str, Any] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxEnablementResult:
    """Evaluate sandbox enablement metadata without enabling live behavior."""

    if isinstance(sandbox_enablement, SandboxEnablementRequest):
        request = sandbox_enablement
    else:
        payload = _to_payload(sandbox_enablement)
        request = build_disabled_enablement(
            approval_evidence=payload.get("approval_evidence"),
            activation_readiness=payload.get("activation_readiness"),
            credential_readiness=payload.get("credential_readiness"),
            broker_readiness=payload.get("broker_readiness"),
            kill_switch_state=payload.get("kill_switch_state"),
            monitoring_readiness=payload.get("monitoring_readiness"),
            rollback_readiness=payload.get("rollback_readiness"),
            deployment_readiness=payload.get("deployment_readiness"),
            metadata=payload.get("metadata"),
        )

    approval_validation = validate_approval_evidence(request.approval_evidence)
    activation_ready, activation_status, activation_blockers, activation_warnings = _coerce_activation_ready(request.activation_readiness)
    credential_ready, credential_status, credential_blockers, credential_warnings = _coerce_credential_ready(request.credential_readiness)
    broker_ready, broker_status, broker_blockers, broker_warnings = _coerce_broker_ready(request.broker_readiness)
    kill_ready, kill_status, kill_blockers, kill_warnings = _coerce_kill_switch_ready(request.kill_switch_state)
    monitoring_ready, monitoring_status, monitoring_blockers, monitoring_warnings = _coerce_monitoring_ready(request.monitoring_readiness)
    rollback_ready, rollback_status, rollback_blockers, rollback_warnings = _coerce_rollback_ready(request.rollback_readiness)
    deployment_ready, deployment_status, deployment_blockers, deployment_warnings = _coerce_deployment_ready(request.deployment_readiness)

    blockers = tuple(
        dict.fromkeys(
            [
                *approval_validation.blocked_reasons,
                *activation_blockers,
                *credential_blockers,
                *broker_blockers,
                *kill_blockers,
                *monitoring_blockers,
                *rollback_blockers,
                *deployment_blockers,
            ]
        )
    )
    warnings = tuple(
        dict.fromkeys(
            [
                *approval_validation.warnings,
                *activation_warnings,
                *credential_warnings,
                *broker_warnings,
                *kill_warnings,
                *monitoring_warnings,
                *rollback_warnings,
                *deployment_warnings,
                "sandbox_enablement_remains_disabled_in_this_phase",
            ]
        )
    )
    ready = bool(
        approval_validation.valid
        and activation_ready
        and credential_ready
        and broker_ready
        and kill_ready
        and monitoring_ready
        and rollback_ready
        and deployment_ready
    )
    state = SandboxEnablementState(
        enablement_id=request.enablement_id,
        request=request,
        approval_validation=approval_validation,
        activation_ready=activation_ready,
        credential_ready=credential_ready,
        broker_ready=broker_ready,
        kill_switch_ready=kill_ready,
        monitoring_ready=monitoring_ready,
        rollback_ready=rollback_ready,
        deployment_ready=deployment_ready,
        ready=ready,
        status="ready_local_only" if ready else "sandbox_enablement_blocked",
        live_enablement_allowed=False,
        blockers=blockers,
        warnings=warnings,
        metadata=dict(metadata or {}),
    )
    return SandboxEnablementResult(
        enablement_id=request.enablement_id,
        state=state,
        ready=ready,
        status=state.status,
        blockers=blockers,
        warnings=warnings,
        live_enablement_allowed=False,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "SandboxEnablementRequest",
    "SandboxEnablementResult",
    "SandboxEnablementState",
    "build_disabled_enablement",
    "evaluate_enablement",
]
