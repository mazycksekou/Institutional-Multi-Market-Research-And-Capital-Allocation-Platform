"""Credential readiness metadata scaffold."""

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
    for name in ("ready", "status", "blockers", "warnings", "metadata", "name", "required", "satisfied", "description", "source", "credential_name"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class CredentialRequirement:
    name: str
    required: bool = True
    satisfied: bool = False
    description: str = ""
    sources: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sources"] = list(self.sources)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class CredentialReadinessState:
    broker_name: str
    requirements: tuple[CredentialRequirement, ...] = ()
    status: str = "disabled"
    ready: bool = False
    credentials_required: bool = True
    live_trading_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class CredentialReadinessResult:
    readiness_id: str
    state: CredentialReadinessState
    ready: bool
    status: str
    satisfied_requirements: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    credentials_required: bool = True
    live_trading_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.as_dict()
        payload["satisfied_requirements"] = list(self.satisfied_requirements)
        payload["missing_requirements"] = list(self.missing_requirements)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_requirement(requirement: CredentialRequirement | Mapping[str, Any] | str) -> CredentialRequirement:
    if isinstance(requirement, CredentialRequirement):
        return requirement
    payload = _to_payload(requirement)
    if isinstance(requirement, str):
        payload.setdefault("name", requirement)
    return CredentialRequirement(
        name=str(payload.get("name") or payload.get("credential_name") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        sources=_coerce_text_tuple(payload.get("sources")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_credential_readiness_requirements(
    required_credentials: Sequence[CredentialRequirement | Mapping[str, Any] | str] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[CredentialRequirement, ...]:
    items = required_credentials or ("api_key", "api_secret")
    return tuple(
        _coerce_requirement(
            CredentialRequirement(
                name=str(item),
                required=True,
                satisfied=False,
                description="Credential readiness metadata only.",
                metadata=dict(metadata or {}),
            )
            if isinstance(item, str)
            else item
        )
        for item in items
    )


def build_disabled_credential_readiness(
    *,
    broker_name: str,
    requirements: Sequence[CredentialRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CredentialReadinessState:
    requirement_items = tuple(_coerce_requirement(item) for item in (requirements or build_credential_readiness_requirements()))
    blockers = ["credential_readiness_disabled"]
    if not broker_name:
        blockers.append("missing_broker_name")
    if not requirement_items:
        blockers.append("missing_credential_requirements")
    return CredentialReadinessState(
        broker_name=str(broker_name or "unknown"),
        requirements=requirement_items,
        status="disabled",
        ready=False,
        credentials_required=True,
        live_trading_allowed=False,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=("credential_readiness_remains_disabled_in_this_phase",),
        metadata=dict(metadata or {}),
    )


def evaluate_credential_readiness(
    credential_readiness: CredentialReadinessState | Mapping[str, Any] | None = None,
    *,
    broker_name: str | None = None,
    requirements: Sequence[CredentialRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CredentialReadinessResult:
    if isinstance(credential_readiness, CredentialReadinessState):
        state = credential_readiness
    else:
        payload = _to_payload(credential_readiness)
        state = CredentialReadinessState(
            broker_name=str(payload.get("broker_name") or broker_name or "unknown"),
            requirements=tuple(
                _coerce_requirement(item)
                for item in (payload.get("requirements") or requirements or build_credential_readiness_requirements())
            ),
            status=str(payload.get("status") or "disabled"),
            ready=bool(payload.get("ready", False)),
            credentials_required=bool(payload.get("credentials_required", True)),
            live_trading_allowed=bool(payload.get("live_trading_allowed", False)),
            blockers=_coerce_text_tuple(payload.get("blockers")),
            warnings=_coerce_text_tuple(payload.get("warnings")),
            metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
        )
    satisfied = tuple(item.name for item in state.requirements if item.required and item.satisfied)
    missing = tuple(item.name for item in state.requirements if item.required and not item.satisfied)
    blockers = tuple(dict.fromkeys([*state.blockers, *missing, "credential_readiness_disabled"]))
    ready = bool(state.ready and not missing and not state.blockers)
    status = "ready_local_only" if ready else "disabled"
    return CredentialReadinessResult(
        readiness_id=f"credential_readiness_{state.broker_name}",
        state=state,
        ready=ready,
        status=status,
        satisfied_requirements=satisfied,
        missing_requirements=missing,
        blockers=blockers,
        warnings=tuple(dict.fromkeys([*state.warnings, "credential_readiness_remains_disabled_in_this_phase"])),
        credentials_required=True,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "CredentialReadinessResult",
    "CredentialReadinessState",
    "CredentialRequirement",
    "build_credential_readiness_requirements",
    "build_disabled_credential_readiness",
    "evaluate_credential_readiness",
]
