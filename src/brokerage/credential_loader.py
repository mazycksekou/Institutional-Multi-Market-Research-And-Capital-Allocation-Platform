"""Credential activation boundary scaffold.

The activation boundary is explicit, approval-gated, and disabled in this
phase. No environment variables or secrets are read here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .approval import ApprovalState, evaluate_approval_gate
from .kill_switch import KillSwitchState, build_default_kill_switch_state


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_approval_state(approval_state: ApprovalState | Mapping[str, Any]) -> ApprovalState:
    if isinstance(approval_state, ApprovalState):
        return approval_state
    if isinstance(approval_state, Mapping):
        payload = dict(approval_state)
    elif all(hasattr(approval_state, attr) for attr in ("approval_id", "status", "approved", "denied", "approval_scope", "approval_source")):
        payload = {
            "approval_id": getattr(approval_state, "approval_id"),
            "status": getattr(approval_state, "status"),
            "approved": getattr(approval_state, "approved"),
            "denied": getattr(approval_state, "denied"),
            "approval_scope": getattr(approval_state, "approval_scope"),
            "approval_source": getattr(approval_state, "approval_source"),
            "metadata": getattr(approval_state, "metadata", {}),
        }
    else:
        raise TypeError("approval_state must be an ApprovalState or mapping")
    return ApprovalState(
        approval_id=str(payload.get("approval_id") or payload.get("state_id") or "live_activation_state"),
        status=str(payload.get("status") or "disabled"),
        approved=bool(payload.get("approved", False)),
        denied=bool(payload.get("denied", False)),
        approval_scope=str(payload.get("approval_scope") or "live_activation"),
        approval_source=str(payload.get("approval_source") or "local"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_kill_switch_state(kill_switch_state: KillSwitchState | Mapping[str, Any] | None) -> KillSwitchState:
    if isinstance(kill_switch_state, KillSwitchState):
        return kill_switch_state
    if kill_switch_state is None:
        return build_default_kill_switch_state()
    if isinstance(kill_switch_state, Mapping):
        payload = dict(kill_switch_state)
    elif all(hasattr(kill_switch_state, attr) for attr in ("kill_switch_id", "clear", "status", "reason")):
        payload = {
            "kill_switch_id": getattr(kill_switch_state, "kill_switch_id"),
            "clear": getattr(kill_switch_state, "clear"),
            "status": getattr(kill_switch_state, "status"),
            "reason": getattr(kill_switch_state, "reason"),
            "metadata": getattr(kill_switch_state, "metadata", {}),
        }
    else:
        raise TypeError("kill_switch_state must be a KillSwitchState or mapping")
    return KillSwitchState(
        kill_switch_id=str(payload.get("kill_switch_id") or "live_trading_kill_switch"),
        clear=bool(payload.get("clear", False)),
        status=str(payload.get("status") or ("clear" if bool(payload.get("clear", False)) else "blocked")),
        reason=str(payload.get("reason") or "live_trading_disabled"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


@dataclass(frozen=True, slots=True)
class CredentialActivationRequirements:
    """Local metadata describing the requirements for credential activation."""

    broker_name: str
    approval_state: ApprovalState
    kill_switch_state: KillSwitchState
    required_credentials: tuple[str, ...] = ()
    credential_sources: tuple[str, ...] = ()
    approval_gate_status: str = "disabled"
    kill_switch_status: str = "blocked"
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    approval_required: bool = True
    kill_switch_required: bool = True
    credentials_required: bool = True
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["kill_switch_state"] = self.kill_switch_state.as_dict()
        payload["required_credentials"] = list(self.required_credentials)
        payload["credential_sources"] = list(self.credential_sources)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class CredentialActivationState:
    """Disabled credential activation state snapshot."""

    ready: bool
    status: str
    requirements: CredentialActivationRequirements
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    credentials_loading_allowed: bool = False
    live_trading_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["requirements"] = self.requirements.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class CredentialLoadRequest:
    """Production-shaped credential load request metadata."""

    request_id: str
    broker_name: str
    approval_state: ApprovalState
    kill_switch_state: KillSwitchState
    requirements: CredentialActivationRequirements
    credential_names: tuple[str, ...] = ()
    credential_sources: tuple[str, ...] = ()
    live_trading_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["kill_switch_state"] = self.kill_switch_state.as_dict()
        payload["requirements"] = self.requirements.as_dict()
        payload["credential_names"] = list(self.credential_names)
        payload["credential_sources"] = list(self.credential_sources)
        payload["metadata"] = dict(self.metadata)
        return payload


class DisabledCredentialLoadError(RuntimeError):
    """Raised when credentials are requested while the activation boundary is disabled."""


def build_credential_activation_requirements(
    approval_state: ApprovalState | Mapping[str, Any],
    kill_switch_state: KillSwitchState | Mapping[str, Any],
    *,
    broker_name: str,
    required_credentials: Sequence[str] | None = None,
    credential_sources: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CredentialActivationRequirements:
    approval = _coerce_approval_state(approval_state)
    kill_switch = _coerce_kill_switch_state(kill_switch_state)
    approval_gate = evaluate_approval_gate(approval)
    blockers: list[str] = []
    if not approval_gate.ready:
        blockers.extend(f"approval_{item}" for item in approval_gate.blockers or ("pending",))
    if not kill_switch.clear:
        blockers.append("kill_switch_not_clear")
    if not required_credentials:
        blockers.append("missing_required_credentials")
    warnings = ["credential_loading_disabled_in_this_phase"]
    return CredentialActivationRequirements(
        broker_name=str(broker_name),
        approval_state=approval,
        kill_switch_state=kill_switch,
        required_credentials=tuple(str(item) for item in required_credentials or () if item),
        credential_sources=tuple(str(item) for item in credential_sources or () if item),
        approval_gate_status=approval_gate.status,
        kill_switch_status=kill_switch.status,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        approval_required=True,
        kill_switch_required=True,
        credentials_required=True,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


def build_credential_load_request(
    approval_state: ApprovalState | Mapping[str, Any],
    kill_switch_state: KillSwitchState | Mapping[str, Any],
    *,
    broker_name: str,
    required_credentials: Sequence[str] | None = None,
    credential_sources: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CredentialLoadRequest:
    requirements = build_credential_activation_requirements(
        approval_state,
        kill_switch_state,
        broker_name=broker_name,
        required_credentials=required_credentials,
        credential_sources=credential_sources,
        metadata=metadata,
    )
    approval = _coerce_approval_state(approval_state)
    kill_switch = _coerce_kill_switch_state(kill_switch_state)
    credential_names = tuple(str(item) for item in required_credentials or ())
    credential_sources_tuple = tuple(str(item) for item in credential_sources or ())
    return CredentialLoadRequest(
        request_id=f"credential_load_{uuid4().hex[:16]}",
        broker_name=str(broker_name),
        approval_state=approval,
        kill_switch_state=kill_switch,
        requirements=requirements,
        credential_names=credential_names,
        credential_sources=credential_sources_tuple,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


def load_credentials_disabled(
    approval_state: ApprovalState | Mapping[str, Any],
    kill_switch_state: KillSwitchState | Mapping[str, Any],
    *,
    broker_name: str,
    required_credentials: Sequence[str] | None = None,
    credential_sources: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = build_credential_load_request(
        approval_state,
        kill_switch_state,
        broker_name=broker_name,
        required_credentials=required_credentials,
        credential_sources=credential_sources,
        metadata=metadata,
    )
    raise DisabledCredentialLoadError(
        f"credential loading is disabled in this phase; request_id={request.request_id}; approval_gate_status={request.requirements.approval_gate_status}; kill_switch_status={request.requirements.kill_switch_status}"
    )


__all__ = [
    "CredentialActivationRequirements",
    "CredentialActivationState",
    "CredentialLoadRequest",
    "DisabledCredentialLoadError",
    "build_credential_activation_requirements",
    "build_credential_load_request",
    "load_credentials_disabled",
]
