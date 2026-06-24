"""Deployment readiness metadata scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .kill_switch import KillSwitchState, build_default_kill_switch_state
from .monitoring import MonitoringReadiness, build_monitoring_readiness, evaluate_monitoring_readiness
from .rollback import RollbackPlan, build_rollback_plan


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
    for name in ("ready", "status", "blockers", "warnings", "metadata", "name", "required", "satisfied", "description", "deployment_id", "reason"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class DeploymentRequirement:
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
class DeploymentReadiness:
    deployment_id: str
    monitoring_readiness: MonitoringReadiness
    rollback_plan: RollbackPlan
    kill_switch_state: KillSwitchState
    requirements: tuple[DeploymentRequirement, ...] = ()
    ready: bool = False
    status: str = "disabled"
    live_deployment_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["monitoring_readiness"] = self.monitoring_readiness.as_dict()
        payload["rollback_plan"] = self.rollback_plan.as_dict()
        payload["kill_switch_state"] = self.kill_switch_state.as_dict()
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


class ProductionDeploymentBlockedError(RuntimeError):
    """Raised when a production deployment is requested while blocked."""


def _coerce_requirement(item: DeploymentRequirement | Mapping[str, Any] | str) -> DeploymentRequirement:
    if isinstance(item, DeploymentRequirement):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return DeploymentRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_kill_switch_state(kill_switch_state: KillSwitchState | Mapping[str, Any] | None) -> KillSwitchState:
    if isinstance(kill_switch_state, KillSwitchState):
        return kill_switch_state
    payload = _to_payload(kill_switch_state)
    return KillSwitchState(
        kill_switch_id=str(payload.get("kill_switch_id") or "live_trading_kill_switch"),
        clear=bool(payload.get("clear", False)),
        status=str(payload.get("status") or ("clear" if bool(payload.get("clear", False)) else "blocked")),
        reason=str(payload.get("reason") or "live_trading_disabled"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_rollback_plan(rollback_plan: RollbackPlan | Mapping[str, Any] | None) -> RollbackPlan:
    if isinstance(rollback_plan, RollbackPlan):
        return rollback_plan
    payload = _to_payload(rollback_plan)
    return RollbackPlan(
        rollback_id=str(payload.get("rollback_id") or "rollback_plan_default"),
        reason=str(payload.get("reason") or "live_trading_deferred"),
        steps=tuple(str(step) for step in payload.get("steps") or ()),
        status=str(payload.get("status") or "metadata_only"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_monitoring_readiness(monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None) -> MonitoringReadiness:
    if isinstance(monitoring_readiness, MonitoringReadiness):
        return monitoring_readiness
    if monitoring_readiness is None:
        return build_monitoring_readiness()
    return evaluate_monitoring_readiness(monitoring_readiness)


def build_disabled_deployment_readiness(
    *,
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    rollback_plan: RollbackPlan | Mapping[str, Any] | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    requirements: Sequence[DeploymentRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DeploymentReadiness:
    monitoring = _coerce_monitoring_readiness(monitoring_readiness)
    rollback = _coerce_rollback_plan(rollback_plan or build_rollback_plan())
    kill_switch = _coerce_kill_switch_state(kill_switch_state or build_default_kill_switch_state())
    requirement_items = tuple(_coerce_requirement(item) for item in (requirements or ()))
    return DeploymentReadiness(
        deployment_id="deployment_disabled",
        monitoring_readiness=monitoring,
        rollback_plan=rollback,
        kill_switch_state=kill_switch,
        requirements=requirement_items,
        ready=False,
        status="disabled",
        live_deployment_allowed=False,
        blockers=(
            "deployment_readiness_disabled",
            "rollback_plan_required",
            "monitoring_readiness_required",
            "kill_switch_clear_required",
        ),
        warnings=("deployment_readiness_remains_disabled_in_this_phase",),
        metadata=dict(metadata or {}),
    )


def evaluate_deployment_readiness(
    deployment_readiness: DeploymentReadiness | Mapping[str, Any] | None = None,
    *,
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    rollback_plan: RollbackPlan | Mapping[str, Any] | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    requirements: Sequence[DeploymentRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DeploymentReadiness:
    if isinstance(deployment_readiness, DeploymentReadiness):
        state = deployment_readiness
    else:
        payload = _to_payload(deployment_readiness)
        state = DeploymentReadiness(
            deployment_id=str(payload.get("deployment_id") or "deployment_disabled"),
            monitoring_readiness=evaluate_monitoring_readiness(payload.get("monitoring_readiness") or monitoring_readiness),
            rollback_plan=_coerce_rollback_plan(payload.get("rollback_plan") or rollback_plan),
            kill_switch_state=_coerce_kill_switch_state(payload.get("kill_switch_state") or kill_switch_state),
            requirements=tuple(
                _coerce_requirement(item)
                for item in (payload.get("requirements") or requirements or ())
            ),
            ready=bool(payload.get("ready", False)),
            status=str(payload.get("status") or "disabled"),
            live_deployment_allowed=bool(payload.get("live_deployment_allowed", False)),
            blockers=_coerce_text_tuple(payload.get("blockers")),
            warnings=_coerce_text_tuple(payload.get("warnings")),
            metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
        )
    monitoring_ready = bool(state.monitoring_readiness.ready)
    rollback_ready = bool(state.rollback_plan.steps or state.rollback_plan.status == "metadata_only")
    kill_ready = bool(state.kill_switch_state.clear)
    ready = bool(state.ready and monitoring_ready and rollback_ready and kill_ready)
    blockers = tuple(
        dict.fromkeys(
            [
                *state.blockers,
                *(["monitoring_readiness_required"] if not monitoring_ready else []),
                *(["rollback_plan_required"] if not rollback_ready else []),
                *(["kill_switch_clear_required"] if not kill_ready else []),
                "deployment_readiness_disabled",
            ]
        )
    )
    missing = tuple(item.name for item in state.requirements if item.required and not item.satisfied)
    if missing:
        blockers = tuple(dict.fromkeys([*blockers, *missing]))
    status = "ready_local_only" if ready and not missing else "disabled"
    return DeploymentReadiness(
        deployment_id=state.deployment_id,
        monitoring_readiness=state.monitoring_readiness,
        rollback_plan=state.rollback_plan,
        kill_switch_state=state.kill_switch_state,
        requirements=state.requirements,
        ready=ready and not missing,
        status=status,
        live_deployment_allowed=False,
        blockers=blockers,
        warnings=tuple(dict.fromkeys([*state.warnings, "deployment_readiness_remains_disabled_in_this_phase"])),
        metadata=dict(metadata or {}),
    )


def require_deployment_ready(
    deployment_readiness: DeploymentReadiness | Mapping[str, Any] | None = None,
    *,
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    rollback_plan: RollbackPlan | Mapping[str, Any] | None = None,
    kill_switch_state: KillSwitchState | Mapping[str, Any] | None = None,
    requirements: Sequence[DeploymentRequirement | Mapping[str, Any] | str] | None = None,
) -> DeploymentReadiness:
    readiness = evaluate_deployment_readiness(
        deployment_readiness,
        monitoring_readiness=monitoring_readiness,
        rollback_plan=rollback_plan,
        kill_switch_state=kill_switch_state,
        requirements=requirements,
    )
    if readiness.ready:
        return readiness
    raise ProductionDeploymentBlockedError("production deployment remains blocked in this phase")


__all__ = [
    "DeploymentReadiness",
    "DeploymentRequirement",
    "ProductionDeploymentBlockedError",
    "build_disabled_deployment_readiness",
    "evaluate_deployment_readiness",
    "require_deployment_ready",
]
