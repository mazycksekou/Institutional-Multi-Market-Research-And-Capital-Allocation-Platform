"""Monitoring readiness metadata scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


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
    for name in ("ready", "status", "blockers", "warnings", "metadata", "name", "required", "satisfied", "description", "endpoint", "severity"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class MonitoringRequirement:
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
class AlertingRequirement:
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
class HealthCheckRequirement:
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
class MonitoringReadiness:
    monitoring_id: str
    requirements: tuple[MonitoringRequirement, ...] = ()
    alerting_requirements: tuple[AlertingRequirement, ...] = ()
    health_check_requirements: tuple[HealthCheckRequirement, ...] = ()
    ready: bool = False
    status: str = "disabled"
    live_monitoring_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["alerting_requirements"] = [item.as_dict() for item in self.alerting_requirements]
        payload["health_check_requirements"] = [item.as_dict() for item in self.health_check_requirements]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_requirement(item: MonitoringRequirement | Mapping[str, Any] | str) -> MonitoringRequirement:
    if isinstance(item, MonitoringRequirement):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return MonitoringRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_alerting_requirement(item: AlertingRequirement | Mapping[str, Any] | str) -> AlertingRequirement:
    if isinstance(item, AlertingRequirement):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return AlertingRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_health_check_requirement(item: HealthCheckRequirement | Mapping[str, Any] | str) -> HealthCheckRequirement:
    if isinstance(item, HealthCheckRequirement):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return HealthCheckRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_monitoring_readiness(
    *,
    monitoring_id: str = "monitoring_readiness_default",
    requirements: Sequence[MonitoringRequirement | Mapping[str, Any] | str] | None = None,
    alerting_requirements: Sequence[AlertingRequirement | Mapping[str, Any] | str] | None = None,
    health_check_requirements: Sequence[HealthCheckRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> MonitoringReadiness:
    requirement_items = tuple(_coerce_requirement(item) for item in (requirements or ()))
    alerting_items = tuple(_coerce_alerting_requirement(item) for item in (alerting_requirements or ("order_submission_alerts",)))
    health_items = tuple(_coerce_health_check_requirement(item) for item in (health_check_requirements or ("broker_service_health",)))
    blockers = ["monitoring_readiness_disabled"]
    if not monitoring_id:
        blockers.append("missing_monitoring_id")
    if not requirement_items:
        blockers.append("missing_monitoring_requirements")
    return MonitoringReadiness(
        monitoring_id=str(monitoring_id),
        requirements=requirement_items,
        alerting_requirements=alerting_items,
        health_check_requirements=health_items,
        ready=False,
        status="disabled",
        live_monitoring_allowed=False,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=("monitoring_readiness_remains_disabled_in_this_phase",),
        metadata=dict(metadata or {}),
    )


def evaluate_monitoring_readiness(
    monitoring_readiness: MonitoringReadiness | Mapping[str, Any] | None = None,
    *,
    monitoring_id: str | None = None,
    requirements: Sequence[MonitoringRequirement | Mapping[str, Any] | str] | None = None,
    alerting_requirements: Sequence[AlertingRequirement | Mapping[str, Any] | str] | None = None,
    health_check_requirements: Sequence[HealthCheckRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> MonitoringReadiness:
    if isinstance(monitoring_readiness, MonitoringReadiness):
        state = monitoring_readiness
    else:
        payload = _to_payload(monitoring_readiness)
        state = MonitoringReadiness(
            monitoring_id=str(payload.get("monitoring_id") or monitoring_id or "monitoring_readiness_default"),
            requirements=tuple(
                _coerce_requirement(item)
                for item in (payload.get("requirements") or requirements or ())
            ),
            alerting_requirements=tuple(
                _coerce_alerting_requirement(item)
                for item in (payload.get("alerting_requirements") or alerting_requirements or ())
            ),
            health_check_requirements=tuple(
                _coerce_health_check_requirement(item)
                for item in (payload.get("health_check_requirements") or health_check_requirements or ())
            ),
            ready=bool(payload.get("ready", False)),
            status=str(payload.get("status") or "disabled"),
            live_monitoring_allowed=bool(payload.get("live_monitoring_allowed", False)),
            blockers=_coerce_text_tuple(payload.get("blockers")),
            warnings=_coerce_text_tuple(payload.get("warnings")),
            metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
        )
    requirement_ready = all(item.satisfied for item in state.requirements if item.required)
    alerting_ready = all(item.satisfied for item in state.alerting_requirements if item.required)
    health_ready = all(item.satisfied for item in state.health_check_requirements if item.required)
    ready = bool(state.ready and requirement_ready and alerting_ready and health_ready and not state.blockers)
    status = "ready_local_only" if ready else "disabled"
    blockers = tuple(
        dict.fromkeys(
            [
                *state.blockers,
                *[f"missing_{item.name}" for item in state.requirements if item.required and not item.satisfied],
                *[f"missing_{item.name}" for item in state.alerting_requirements if item.required and not item.satisfied],
                *[f"missing_{item.name}" for item in state.health_check_requirements if item.required and not item.satisfied],
                "monitoring_readiness_disabled",
            ]
        )
    )
    return MonitoringReadiness(
        monitoring_id=state.monitoring_id,
        requirements=state.requirements,
        alerting_requirements=state.alerting_requirements,
        health_check_requirements=state.health_check_requirements,
        ready=ready,
        status=status,
        live_monitoring_allowed=False,
        blockers=blockers,
        warnings=tuple(dict.fromkeys([*state.warnings, "monitoring_readiness_remains_disabled_in_this_phase"])),
        metadata=dict(metadata or {}),
    )


__all__ = [
    "AlertingRequirement",
    "HealthCheckRequirement",
    "MonitoringReadiness",
    "MonitoringRequirement",
    "build_monitoring_readiness",
    "evaluate_monitoring_readiness",
]
