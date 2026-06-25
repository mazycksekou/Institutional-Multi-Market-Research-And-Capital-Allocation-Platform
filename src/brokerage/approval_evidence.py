"""Explicit approval evidence scaffold for controlled sandbox activation.

This module keeps approval data local and deterministic. It models approval
evidence but never reads secrets, signs requests, or activates live behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
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
    for name in ("evidence_id", "source", "approved", "status", "notes", "approval_scope", "metadata", "requirements"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


class ApprovalSource(str, Enum):
    LOCAL = "local"
    MANUAL = "manual"
    OWNER = "owner"
    RISK = "risk"
    SECURITY = "security"
    BROKER = "broker"
    ROLLBACK = "rollback"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"


@dataclass(frozen=True, slots=True)
class ApprovalEvidence:
    """Metadata-only approval evidence."""

    evidence_id: str
    source: ApprovalSource = ApprovalSource.LOCAL
    requirements: tuple[ApprovalRequirement, ...] = field(default_factory=build_default_approval_requirements)
    approved: bool = False
    status: str = "not_approved"
    approval_scope: str = "live_activation"
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source"] = self.source.value
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalValidationResult:
    """Local-only result for approval evidence validation."""

    validation_id: str
    evidence: ApprovalEvidence
    valid: bool
    status: str
    approved: bool
    blocked_reasons: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = self.evidence.as_dict()
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["missing_requirements"] = list(self.missing_requirements)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
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


def _coerce_source(source: ApprovalSource | str | None) -> ApprovalSource:
    if isinstance(source, ApprovalSource):
        return source
    text = str(source or "local").strip().lower()
    return ApprovalSource(text) if text in ApprovalSource._value2member_map_ else ApprovalSource.LOCAL


def _coerce_evidence(evidence: ApprovalEvidence | Mapping[str, Any] | None) -> ApprovalEvidence:
    if isinstance(evidence, ApprovalEvidence):
        return evidence
    payload = _to_payload(evidence)
    requirements = payload.get("requirements")
    if isinstance(requirements, Sequence) and not isinstance(requirements, (str, bytes)):
        requirement_items = tuple(_coerce_requirement(item) for item in requirements)
    else:
        requirement_items = build_default_approval_requirements()
    return ApprovalEvidence(
        evidence_id=str(payload.get("evidence_id") or payload.get("approval_id") or "approval_evidence_default"),
        source=_coerce_source(payload.get("source")),
        requirements=requirement_items,
        approved=bool(payload.get("approved", False)),
        status=str(payload.get("status") or "not_approved"),
        approval_scope=str(payload.get("approval_scope") or "live_activation"),
        notes=str(payload.get("notes") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_default_approval_evidence(
    *,
    source: ApprovalSource | str = ApprovalSource.LOCAL,
    metadata: Mapping[str, Any] | None = None,
) -> ApprovalEvidence:
    """Return the default not-approved evidence object."""

    return ApprovalEvidence(
        evidence_id="approval_evidence_default",
        source=_coerce_source(source),
        requirements=tuple(
            ApprovalRequirement(
                name=item.name,
                required=item.required,
                satisfied=False,
                description=item.description,
                evidence=item.evidence,
                metadata=dict(metadata or item.metadata),
            )
            for item in build_default_approval_requirements()
        ),
        approved=False,
        status="not_approved",
        approval_scope="live_activation",
        notes="default approval evidence remains not approved",
        metadata=dict(metadata or {}),
    )


def validate_approval_evidence(
    approval_evidence: ApprovalEvidence | Mapping[str, Any] | None = None,
    *,
    requirements: Sequence[ApprovalRequirement | Mapping[str, Any] | str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ApprovalValidationResult:
    """Validate approval evidence without enabling live behavior."""

    evidence = _coerce_evidence(approval_evidence)
    requirement_items = tuple(_coerce_requirement(item) for item in (requirements if requirements is not None else evidence.requirements))
    satisfied = tuple(item.name for item in requirement_items if item.required and item.satisfied)
    missing = tuple(item.name for item in requirement_items if item.required and not item.satisfied)
    blockers = []
    if not evidence.approved:
        blockers.append("approval_not_granted")
    if evidence.status in {"denied", "rejected"}:
        blockers.append("approval_explicitly_denied")
    if missing:
        blockers.append("missing_required_approvals")
        blockers.extend(f"missing_{item}" for item in missing)
    valid = bool(evidence.approved and not blockers and not missing)
    status = "approved_local_only" if valid else "not_approved"
    warnings = ("approval_evidence_is_local_only",)
    return ApprovalValidationResult(
        validation_id=f"{evidence.evidence_id}:validation",
        evidence=ApprovalEvidence(
            evidence_id=evidence.evidence_id,
            source=evidence.source,
            requirements=requirement_items,
            approved=evidence.approved,
            status=status,
            approval_scope=evidence.approval_scope,
            notes=evidence.notes,
            metadata=dict(evidence.metadata),
        ),
        valid=valid,
        status=status,
        approved=bool(valid),
        blocked_reasons=tuple(dict.fromkeys(blockers)),
        missing_requirements=missing,
        warnings=warnings,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "ApprovalEvidence",
    "ApprovalRequirement",
    "ApprovalSource",
    "ApprovalValidationResult",
    "build_default_approval_evidence",
    "validate_approval_evidence",
]

