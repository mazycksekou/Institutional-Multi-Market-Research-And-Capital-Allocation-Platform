"""Approval-gated live activation scaffold.

This module models explicit approval requirements for future live activation
without enabling any live behavior in the current phase.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


@dataclass(frozen=True, slots=True)
class ApprovalRequirement:
    """Local metadata describing a single approval requirement."""

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


def build_default_approval_requirements() -> tuple[ApprovalRequirement, ...]:
    """Return the fixed approval checklist for future live activation."""

    return (
        ApprovalRequirement(
            name="owner_approval",
            description="Explicit owner approval is required before live activation.",
        ),
        ApprovalRequirement(
            name="broker_approval",
            description="Broker approval must be granted before live activation.",
        ),
        ApprovalRequirement(
            name="risk_approval",
            description="Risk approval must be recorded before live activation.",
        ),
        ApprovalRequirement(
            name="security_review",
            description="Security review must be complete before live activation.",
        ),
        ApprovalRequirement(
            name="rollback_plan_ready",
            description="A rollback plan must be ready before live activation.",
        ),
        ApprovalRequirement(
            name="kill_switch_clear",
            description="The kill switch must be clear before live activation.",
        ),
    )


@dataclass(frozen=True, slots=True)
class ApprovalState:
    """Explicit local state describing the current approval posture."""

    approval_id: str
    status: str = "disabled"
    approved: bool = False
    denied: bool = False
    approval_scope: str = "live_activation"
    approval_source: str = "local"
    requirements: tuple[ApprovalRequirement, ...] = field(default_factory=build_default_approval_requirements)
    approver: str | None = None
    reviewed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """Evaluation result for a live-activation approval state."""

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
class ApprovalGateStatus:
    """Structured approval-gate status for future live activation."""

    ready: bool
    status: str
    approval_state: ApprovalState
    decision: ApprovalDecision
    requirements: tuple[ApprovalRequirement, ...]
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    live_activation_allowed: bool = False
    approval_required: bool = True
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["decision"] = self.decision.as_dict()
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


class ApprovalRejectedError(RuntimeError):
    """Raised when live activation approval is explicitly rejected."""


class ApprovalMissingError(RuntimeError):
    """Raised when required approval evidence is missing."""


def _coerce_requirement(requirement: ApprovalRequirement | Mapping[str, Any]) -> ApprovalRequirement:
    if isinstance(requirement, ApprovalRequirement):
        return requirement
    payload = dict(requirement)
    return ApprovalRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_state(state: ApprovalState | Mapping[str, Any] | None) -> ApprovalState:
    if isinstance(state, ApprovalState):
        return state
    if state is None:
        return ApprovalState(approval_id="live_activation_default", requirements=build_default_approval_requirements())
    payload = dict(state)
    requirements = payload.get("requirements")
    if isinstance(requirements, Sequence) and not isinstance(requirements, (str, bytes)):
        requirement_items = tuple(_coerce_requirement(item) for item in requirements)
    else:
        requirement_items = build_default_approval_requirements()
    return ApprovalState(
        approval_id=str(payload.get("approval_id") or payload.get("state_id") or "live_activation_state"),
        status=str(payload.get("status") or "disabled"),
        approved=bool(payload.get("approved", False)),
        denied=bool(payload.get("denied", False)),
        approval_scope=str(payload.get("approval_scope") or "live_activation"),
        approval_source=str(payload.get("approval_source") or "local"),
        requirements=requirement_items,
        approver=payload.get("approver"),
        reviewed_at=payload.get("reviewed_at"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _approval_blockers(state: ApprovalState, requirements: tuple[ApprovalRequirement, ...]) -> tuple[str, ...]:
    blockers: list[str] = []
    missing = [item.name for item in requirements if item.required and not item.satisfied]
    if missing:
        blockers.append("missing_required_approvals")
        blockers.extend(f"missing_{item}" for item in missing)
    if state.denied or state.status in {"denied", "rejected"}:
        blockers.append("approval_explicitly_denied")
    if not state.approved:
        blockers.append("approval_not_granted")
    return tuple(dict.fromkeys(blockers))


def evaluate_approval_gate(
    approval_state: ApprovalState | Mapping[str, Any] | None = None,
    *,
    requirements: Sequence[ApprovalRequirement | Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ApprovalGateStatus:
    """Evaluate a local approval state without enabling live behavior."""

    state = _coerce_state(approval_state)
    requirement_items = tuple(_coerce_requirement(item) for item in requirements) if requirements is not None else state.requirements
    satisfied_requirements = tuple(item.name for item in requirement_items if item.required and item.satisfied)
    missing_requirements = tuple(item.name for item in requirement_items if item.required and not item.satisfied)
    blockers = _approval_blockers(state, requirement_items)
    warnings = ("live_activation_still_disabled_in_this_phase",)
    ready = bool(state.approved and not blockers and not missing_requirements)
    if ready:
        status = "approved_local_only"
        message = "approval requirements satisfied for local evaluation only"
    elif "approval_explicitly_denied" in blockers:
        status = "approval_rejected"
        message = "approval was explicitly denied"
    elif missing_requirements:
        status = "approval_missing"
        message = "required approval evidence is missing"
    else:
        status = "approval_pending"
        message = "approval is not yet granted"
    decision = ApprovalDecision(
        decision_id=f"{state.approval_id}:decision",
        approved=ready,
        status=status,
        gate_status=status,
        satisfied_requirements=satisfied_requirements,
        missing_requirements=missing_requirements,
        blocked_reasons=blockers,
        message=message,
        metadata=dict(metadata or {}),
    )
    return ApprovalGateStatus(
        ready=ready,
        status=status,
        approval_state=state,
        decision=decision,
        requirements=requirement_items,
        blockers=blockers,
        warnings=warnings,
        live_activation_allowed=False,
        approval_required=True,
        metadata=dict(metadata or {}),
    )


def require_live_approval(
    approval_state: ApprovalState | Mapping[str, Any] | None = None,
    *,
    requirements: Sequence[ApprovalRequirement | Mapping[str, Any]] | None = None,
) -> ApprovalDecision:
    """Require an approved local state before future live activation.

    The check is deterministic and local-only. It does not activate live
    behavior in this phase.
    """

    gate = evaluate_approval_gate(approval_state, requirements=requirements)
    if gate.ready:
        return gate.decision
    if "approval_explicitly_denied" in gate.blockers:
        raise ApprovalRejectedError(gate.decision.message)
    raise ApprovalMissingError(gate.decision.message)


__all__ = [
    "ApprovalDecision",
    "ApprovalGateStatus",
    "ApprovalMissingError",
    "ApprovalRejectedError",
    "ApprovalRequirement",
    "ApprovalState",
    "build_default_approval_requirements",
    "evaluate_approval_gate",
    "require_live_approval",
]
