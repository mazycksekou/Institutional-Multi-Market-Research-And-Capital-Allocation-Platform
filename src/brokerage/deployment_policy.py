"""Deployment governance policy scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval_evidence import ApprovalEvidence, build_default_approval_evidence, validate_approval_evidence
from .adapter_readiness import BrokerAdapterReadiness, build_broker_adapter_readiness, validate_broker_adapter_readiness
from .credential_readiness import CredentialReadinessState, build_disabled_credential_readiness, evaluate_credential_readiness
from .kill_switch import KillSwitchState, build_default_kill_switch_state, require_kill_switch_clear
from .monitoring import MonitoringReadiness, build_monitoring_readiness, evaluate_monitoring_readiness
from .rollback import RollbackPlan, build_rollback_plan


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _text_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (list, tuple, set)):
        return tuple(str(item) for item in values if item not in (None, ""))
    return (str(values),)


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
        "name",
        "required",
        "satisfied",
        "description",
        "metadata",
        "checklist_id",
        "policy_id",
        "approval_evidence",
        "monitoring_readiness",
        "rollback_plan",
        "broker_readiness",
        "credential_readiness",
        "kill_switch_state",
    ):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class DeploymentBlocker:
    """Individual deployment blocker metadata."""

    name: str
    required: bool = True
    satisfied: bool = False
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class DeploymentChecklist:
    """Checklist describing deployment prerequisites."""

    checklist_id: str
    approval_required: bool = True
    monitoring_required: bool = True
    rollback_required: bool = True
    broker_required: bool = True
    credential_required: bool = True
    kill_switch_required: bool = True
    blockers: tuple[DeploymentBlocker, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = [item.as_dict() for item in self.blockers]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class DeploymentPolicy:
    """Policy metadata describing deployment prerequisites."""

    policy_id: str
    checklist: DeploymentChecklist
    status: str = "blocked"
    deployment_allowed: bool = False
    live_deployment_allowed: bool = False
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checklist"] = self.checklist.as_dict()
        payload["warnings"] = list(self.warnings)
        payload["blockers"] = list(self.blockers)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class DeploymentApproval:
    """Local deployment readiness evaluation result."""

    approval_id: str
    policy: DeploymentPolicy
    approval_evidence: ApprovalEvidence
    monitoring_readiness: MonitoringReadiness
    rollback_plan: RollbackPlan
    broker_readiness: BrokerAdapterReadiness
    credential_readiness: CredentialReadinessState
    kill_switch_state: KillSwitchState
    ready: bool = False
    status: str = "blocked"
    approved: bool = False
    live_deployment_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["policy"] = self.policy.as_dict()
        payload["approval_evidence"] = self.approval_evidence.as_dict()
        payload["monitoring_readiness"] = self.monitoring_readiness.as_dict()
        payload["rollback_plan"] = self.rollback_plan.as_dict()
        payload["broker_readiness"] = self.broker_readiness.as_dict()
        payload["credential_readiness"] = self.credential_readiness.as_dict()
        payload["kill_switch_state"] = self.kill_switch_state.as_dict()
        payload["warnings"] = list(self.warnings)
        payload["blockers"] = list(self.blockers)
        payload["metadata"] = dict(self.metadata)
        return payload


class ProductionDeploymentBlockedError(RuntimeError):
    """Raised when production deployment remains blocked."""


def _coerce_blocker(item: DeploymentBlocker | Mapping[str, Any] | str) -> DeploymentBlocker:
    if isinstance(item, DeploymentBlocker):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return DeploymentBlocker(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_approval(value: ApprovalEvidence | Mapping[str, Any] | None) -> ApprovalEvidence:
    if isinstance(value, ApprovalEvidence):
        return value
    if value is None:
        return build_default_approval_evidence()
    return validate_approval_evidence(value).evidence


def _coerce_monitoring(value: MonitoringReadiness | Mapping[str, Any] | None) -> MonitoringReadiness:
    if isinstance(value, MonitoringReadiness):
        return evaluate_monitoring_readiness(value)
    if value is None:
        return evaluate_monitoring_readiness(build_monitoring_readiness())
    return evaluate_monitoring_readiness(value)


def _coerce_rollback(value: RollbackPlan | Mapping[str, Any] | None) -> RollbackPlan:
    if isinstance(value, RollbackPlan):
        return value
    payload = _to_payload(value)
    return RollbackPlan(
        rollback_id=str(payload.get("rollback_id") or "rollback_plan_default"),
        reason=str(payload.get("reason") or "live_trading_deferred"),
        steps=tuple(str(step) for step in payload.get("steps") or ()),
        status=str(payload.get("status") or "metadata_only"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_broker(value: BrokerAdapterReadiness | Mapping[str, Any] | None) -> BrokerAdapterReadiness:
    if isinstance(value, BrokerAdapterReadiness):
        return validate_broker_adapter_readiness(value)
    if value is None:
        return validate_broker_adapter_readiness(
            build_broker_adapter_readiness(
                broker_name="sandbox-broker",
                supported_asset_classes=[{"asset_class": "equity", "supported": False}],
                supported_order_types=[{"order_type": "market", "supported": False}],
                account_capabilities=[{"capability_name": "sandbox_account", "supported": False}],
                reconciliation_capabilities=[{"capability_name": "position_reconciliation", "supported": False}],
            )
        )
    return validate_broker_adapter_readiness(value)


def _coerce_credentials(value: CredentialReadinessState | Mapping[str, Any] | None) -> CredentialReadinessState:
    if isinstance(value, CredentialReadinessState):
        return evaluate_credential_readiness(value)
    if value is None:
        return evaluate_credential_readiness(build_disabled_credential_readiness(broker_name="sandbox-broker"))
    return evaluate_credential_readiness(value)


def _coerce_kill_switch(value: KillSwitchState | Mapping[str, Any] | None) -> KillSwitchState:
    try:
        return require_kill_switch_clear(value)
    except Exception:
        payload = _to_payload(value)
        return KillSwitchState(
            kill_switch_id=str(payload.get("kill_switch_id") or "live_trading_kill_switch"),
            clear=bool(payload.get("clear", False)),
            status=str(payload.get("status") or ("clear" if bool(payload.get("clear", False)) else "blocked")),
            reason=str(payload.get("reason") or "live_trading_disabled"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_checklist(checklist: DeploymentChecklist | Mapping[str, Any] | None) -> DeploymentChecklist:
    if isinstance(checklist, DeploymentChecklist):
        return checklist
    payload = _to_payload(checklist)
    blockers = payload.get("blockers")
    blocker_items = tuple(_coerce_blocker(item) for item in blockers) if isinstance(blockers, Sequence) and not isinstance(blockers, (str, bytes)) else ()
    return DeploymentChecklist(
        checklist_id=str(payload.get("checklist_id") or "deployment_checklist_default"),
        approval_required=bool(payload.get("approval_required", True)),
        monitoring_required=bool(payload.get("monitoring_required", True)),
        rollback_required=bool(payload.get("rollback_required", True)),
        broker_required=bool(payload.get("broker_required", True)),
        credential_required=bool(payload.get("credential_required", True)),
        kill_switch_required=bool(payload.get("kill_switch_required", True)),
        blockers=blocker_items,
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_policy(policy: DeploymentPolicy | Mapping[str, Any] | None) -> DeploymentPolicy:
    if isinstance(policy, DeploymentPolicy):
        return policy
    payload = _to_payload(policy)
    checklist = _coerce_checklist(payload.get("checklist"))
    if checklist.blockers:
        blocker_items = checklist.blockers
    else:
        blocker_items = (
            DeploymentBlocker(name="approval_required", description="Approval is required before production deployment."),
            DeploymentBlocker(name="monitoring_required", description="Monitoring readiness is required before production deployment."),
            DeploymentBlocker(name="rollback_required", description="Rollback readiness is required before production deployment."),
            DeploymentBlocker(name="broker_required", description="Broker readiness is required before production deployment."),
            DeploymentBlocker(name="credential_required", description="Credential readiness is required before production deployment."),
            DeploymentBlocker(name="kill_switch_required", description="Kill switch clearance is required before production deployment."),
        )
        checklist = DeploymentChecklist(
            checklist_id=checklist.checklist_id,
            approval_required=checklist.approval_required,
            monitoring_required=checklist.monitoring_required,
            rollback_required=checklist.rollback_required,
            broker_required=checklist.broker_required,
            credential_required=checklist.credential_required,
            kill_switch_required=checklist.kill_switch_required,
            blockers=blocker_items,
            metadata=dict(checklist.metadata),
        )
    return DeploymentPolicy(
        policy_id=str(payload.get("policy_id") or "deployment_policy_default"),
        checklist=checklist,
        status=str(payload.get("status") or "blocked"),
        deployment_allowed=bool(payload.get("deployment_allowed", False)),
        live_deployment_allowed=bool(payload.get("live_deployment_allowed", False)),
        warnings=_text_tuple(payload.get("warnings")),
        blockers=_text_tuple(payload.get("blockers")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_default_policy(*, metadata: Mapping[str, Any] | None = None) -> DeploymentPolicy:
    """Return the default deployment-blocking policy."""

    checklist = DeploymentChecklist(
        checklist_id="deployment_checklist_default",
        approval_required=True,
        monitoring_required=True,
        rollback_required=True,
        broker_required=True,
        credential_required=True,
        kill_switch_required=True,
        blockers=(
            DeploymentBlocker(name="approval_required", description="Approval is required before production deployment."),
            DeploymentBlocker(name="monitoring_required", description="Monitoring readiness is required before production deployment."),
            DeploymentBlocker(name="rollback_required", description="Rollback readiness is required before production deployment."),
            DeploymentBlocker(name="broker_required", description="Broker readiness is required before production deployment."),
            DeploymentBlocker(name="credential_required", description="Credential readiness is required before production deployment."),
            DeploymentBlocker(name="kill_switch_required", description="Kill switch clearance is required before production deployment."),
        ),
        metadata=dict(metadata or {}),
    )
    return DeploymentPolicy(
        policy_id="deployment_policy_default",
        checklist=checklist,
        status="blocked",
        deployment_allowed=False,
        live_deployment_allowed=False,
        warnings=("deployment_policy_remains_blocked_in_this_phase",),
        blockers=("deployment_blocked",),
        metadata=dict(metadata or {}),
    )


def evaluate_deployment_policy(
    deployment_policy: DeploymentPolicy | Mapping[str, Any] | None = None,
    *,
    approval_evidence: ApprovalEvidence | Mapping[str, Any] | None = None,
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    rollback_plan: RollbackPlan | Mapping[str, Any] | None = None,
    broker_readiness: BrokerAdapterReadiness | Mapping[str, Any] | None = None,
    credential_readiness: CredentialReadinessState | Mapping[str, Any] | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DeploymentApproval:
    """Evaluate deployment policy metadata without enabling deployment."""

    policy = _coerce_policy(deployment_policy)
    approval = _coerce_approval(approval_evidence)
    monitoring = _coerce_monitoring(monitoring_readiness)
    rollback = _coerce_rollback(rollback_plan)
    broker = _coerce_broker(broker_readiness)
    credentials = _coerce_credentials(credential_readiness)
    kill_switch = _coerce_kill_switch(kill_switch_state)

    ready = bool(
        approval.approved
        and monitoring.ready
        and (rollback.status == "metadata_only" or bool(rollback.steps))
        and broker.ready
        and credentials.ready
        and kill_switch.clear
    )
    checklist = policy.checklist
    blockers = tuple(
        dict.fromkeys(
            [
                *policy.blockers,
                *(["approval_required"] if not approval.approved else []),
                *(["monitoring_required"] if not monitoring.ready else []),
                *(["rollback_required"] if not (rollback.status == "metadata_only" or rollback.steps) else []),
                *(["broker_required"] if not broker.ready else []),
                *(["credential_required"] if not credentials.ready else []),
                *(["kill_switch_required"] if not kill_switch.clear else []),
                "deployment_blocked",
            ]
        )
    )
    status = "ready_local_only" if ready else "blocked"
    return DeploymentApproval(
        approval_id=f"{policy.policy_id}:approval",
        policy=policy,
        approval_evidence=approval,
        monitoring_readiness=monitoring,
        rollback_plan=rollback,
        broker_readiness=broker,
        credential_readiness=credentials,
        kill_switch_state=kill_switch,
        ready=ready,
        status=status,
        approved=ready,
        live_deployment_allowed=False,
        blockers=blockers,
        warnings=tuple(dict.fromkeys([*policy.warnings, "deployment_policy_remains_blocked_in_this_phase"])),
        metadata=dict(metadata or {}),
    )


__all__ = [
    "DeploymentApproval",
    "DeploymentBlocker",
    "DeploymentChecklist",
    "DeploymentPolicy",
    "ProductionDeploymentBlockedError",
    "build_default_policy",
    "evaluate_deployment_policy",
]
