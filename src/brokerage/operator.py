"""Operator-facing approval interface for controlled sandbox activation.

This module is metadata-only and deterministic. It never authenticates,
persists externally, loads secrets, or activates live behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalRequirement, build_default_approval_requirements


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
    for name in (
        "operator_id",
        "display_name",
        "role",
        "environment",
        "approval_scope",
        "approval_metadata",
        "requirements",
        "status",
        "approved",
        "blockers",
        "warnings",
        "metadata",
    ):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


def _coerce_requirement(item: ApprovalRequirement | Mapping[str, Any] | str) -> ApprovalRequirement:
    if isinstance(item, ApprovalRequirement):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return ApprovalRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_identity(identity: "OperatorIdentity | Mapping[str, Any] | None") -> "OperatorIdentity":
    if isinstance(identity, OperatorIdentity):
        return identity
    payload = _to_payload(identity)
    return OperatorIdentity(
        operator_id=str(payload.get("operator_id") or "operator_default"),
        display_name=str(payload.get("display_name") or "default_operator"),
        role=str(payload.get("role") or "operator"),
        environment=str(payload.get("environment") or "disabled"),
        approval_scope=str(payload.get("approval_scope") or "sandbox_activation"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _approval_metadata_to_bool(approval_metadata: Mapping[str, Any] | None) -> bool:
    payload = dict(approval_metadata or {})
    return bool(payload.get("approved", False)) and bool(
        payload.get("approval_reference")
        or payload.get("approval_reason")
        or payload.get("operator_ack")
        or payload.get("operator_acknowledged")
    )


@dataclass(frozen=True, slots=True)
class OperatorIdentity:
    """Local metadata describing an operator identity."""

    operator_id: str
    display_name: str
    role: str = "operator"
    environment: str = "disabled"
    approval_scope: str = "sandbox_activation"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class OperatorApprovalRequest:
    """Deterministic local approval request."""

    request_id: str
    operator_identity: OperatorIdentity
    approval_scope: str = "sandbox_activation"
    approval_metadata: dict[str, Any] = field(default_factory=dict)
    requirements: tuple[ApprovalRequirement, ...] = field(default_factory=build_default_approval_requirements)
    status: str = "denied"
    approval_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operator_identity"] = self.operator_identity.as_dict()
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["metadata"] = dict(self.metadata)
        payload["approval_metadata"] = dict(self.approval_metadata)
        return payload


@dataclass(frozen=True, slots=True)
class OperatorApprovalDecision:
    """Local approval decision for operator control-plane actions."""

    decision_id: str
    request: OperatorApprovalRequest
    approved: bool = False
    status: str = "denied"
    approval_allowed: bool = False
    blocked_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class OperatorApprovalStatus:
    """Local-only operator approval status."""

    ready: bool
    status: str
    operator_request: OperatorApprovalRequest
    operator_decision: OperatorApprovalDecision
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    approval_required: bool = True
    live_activation_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operator_request"] = self.operator_request.as_dict()
        payload["operator_decision"] = self.operator_decision.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalAuditEntry:
    """Local audit entry for operator approval decisions."""

    entry_id: str
    request_id: str
    decision_id: str
    operator_id: str
    event_type: str = "operator_approval_decision"
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalAuditTrail:
    """Local-only trail of operator approval events."""

    trail_id: str
    entries: tuple[ApprovalAuditEntry, ...] = ()
    status: str = "blocked"
    live_audit_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entries"] = [item.as_dict() for item in self.entries]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class OperatorApprovalRecord:
    """Record tying an approval request, decision, and audit trail together."""

    record_id: str
    request: OperatorApprovalRequest
    decision: OperatorApprovalDecision
    audit_trail: ApprovalAuditTrail
    status: str = "denied"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["decision"] = self.decision.as_dict()
        payload["audit_trail"] = self.audit_trail.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


def build_default_operator(*, metadata: Mapping[str, Any] | None = None) -> OperatorIdentity:
    """Return the default disabled operator identity."""

    return OperatorIdentity(
        operator_id="operator_default",
        display_name="default_operator",
        role="operator",
        environment="disabled",
        approval_scope="sandbox_activation",
        metadata=dict(metadata or {}),
    )


def build_operator_request(
    operator_identity: OperatorIdentity | Mapping[str, Any] | None = None,
    *,
    approval_scope: str = "sandbox_activation",
    approval_metadata: Mapping[str, Any] | None = None,
    requirements: Sequence[ApprovalRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> OperatorApprovalRequest:
    """Build a metadata-only operator approval request."""

    identity = _coerce_identity(operator_identity)
    requirement_items = tuple(_coerce_requirement(item) for item in (requirements or build_default_approval_requirements()))
    approval_payload = dict(approval_metadata or {})
    satisfied_requirements = _coerce_text_tuple(approval_payload.get("satisfied_requirements"))
    all_requirements_satisfied = not any(item.required and not item.satisfied for item in requirement_items) or set(satisfied_requirements) >= {item.name for item in requirement_items if item.required}
    explicit_override = bool(approval_payload.get("override_requirements", False))
    approval_allowed = _approval_metadata_to_bool(approval_payload) and (all_requirements_satisfied or explicit_override)
    request = OperatorApprovalRequest(
        request_id=str(metadata.get("request_id") if isinstance(metadata, Mapping) and metadata.get("request_id") else "operator_approval_request"),
        operator_identity=identity,
        approval_scope=str(approval_scope or identity.approval_scope),
        approval_metadata=approval_payload,
        requirements=requirement_items,
        status="approved_local_only" if approval_allowed else "denied",
        approval_allowed=approval_allowed,
        metadata=dict(metadata or {}),
    )
    return request


def evaluate_operator_approval(
    operator_request: OperatorApprovalRequest | Mapping[str, Any] | None = None,
    *,
    approval_metadata: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> OperatorApprovalDecision:
    """Evaluate operator approval metadata without enabling live behavior."""

    request = operator_request if isinstance(operator_request, OperatorApprovalRequest) else build_operator_request(operator_request)
    approval_payload = dict(approval_metadata or request.approval_metadata)
    requirements = request.requirements
    missing_requirements = tuple(item.name for item in requirements if item.required and not item.satisfied)
    satisfied_requirements = _coerce_text_tuple(approval_payload.get("satisfied_requirements"))
    all_requirements_satisfied = not missing_requirements or set(satisfied_requirements) >= {item.name for item in requirements if item.required}
    explicit_override = bool(approval_payload.get("override_requirements", False))
    approved = _approval_metadata_to_bool(approval_payload) and (all_requirements_satisfied or explicit_override)
    blockers = []
    if not approved:
        blockers.append("operator_approval_denied")
    if missing_requirements and not all_requirements_satisfied and not explicit_override:
        blockers.append("missing_required_operator_requirements")
        blockers.extend(f"missing_{item}" for item in missing_requirements)
    status = "approved_local_only" if approved else "denied"
    warnings = ("operator_approval_remains_metadata_only",)
    return OperatorApprovalDecision(
        decision_id=f"{request.request_id}:decision",
        request=request,
        approved=approved,
        status=status,
        approval_allowed=approved,
        blocked_reasons=tuple(dict.fromkeys(blockers)),
        warnings=warnings,
        metadata=dict(metadata or {}),
    )


def record_operator_decision(
    operator_request: OperatorApprovalRequest | Mapping[str, Any] | None = None,
    *,
    operator_decision: OperatorApprovalDecision | Mapping[str, Any] | None = None,
    audit_trail: ApprovalAuditTrail | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> OperatorApprovalRecord:
    """Assemble a local approval record and audit trail without persistence."""

    request = operator_request if isinstance(operator_request, OperatorApprovalRequest) else build_operator_request(operator_request)
    decision = (
        operator_decision
        if isinstance(operator_decision, OperatorApprovalDecision)
        else evaluate_operator_approval(request, metadata=metadata)
    )
    if isinstance(audit_trail, ApprovalAuditTrail):
        trail = audit_trail
        entries = trail.entries
    else:
        trail = ApprovalAuditTrail(
            trail_id=f"{request.request_id}:trail",
            entries=(),
            status="recorded_local_only",
            live_audit_allowed=False,
            metadata=dict(metadata or {}),
        )
        entries = ()
    entry = ApprovalAuditEntry(
        entry_id=f"{request.request_id}:entry",
        request_id=request.request_id,
        decision_id=decision.decision_id,
        operator_id=request.operator_identity.operator_id,
        notes="operator decision recorded locally only",
        metadata=dict(metadata or {}),
    )
    updated_trail = ApprovalAuditTrail(
        trail_id=trail.trail_id,
        entries=tuple((*entries, entry)),
        status="recorded_local_only",
        live_audit_allowed=False,
        metadata=dict(trail.metadata),
    )
    return OperatorApprovalRecord(
        record_id=f"{request.request_id}:record",
        request=request,
        decision=decision,
        audit_trail=updated_trail,
        status=decision.status,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "ApprovalAuditEntry",
    "ApprovalAuditTrail",
    "OperatorApprovalDecision",
    "OperatorApprovalRecord",
    "OperatorApprovalRequest",
    "OperatorApprovalStatus",
    "OperatorIdentity",
    "build_default_operator",
    "build_operator_request",
    "evaluate_operator_approval",
    "record_operator_decision",
]
