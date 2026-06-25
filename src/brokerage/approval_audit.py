"""Local-only approval audit history scaffold."""

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
    for name in ("event_id", "event_type", "approval_id", "operator_id", "status", "message", "metadata", "entries"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class ApprovalAuditEvent:
    """Local approval audit event."""

    event_id: str
    event_type: str = "approval_decision"
    approval_id: str = "approval_audit_default"
    operator_id: str = "operator_default"
    status: str = "blocked"
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalAuditRecord:
    """Local audit record containing approval events."""

    audit_id: str
    events: tuple[ApprovalAuditEvent, ...] = ()
    status: str = "disabled"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["events"] = [item.as_dict() for item in self.events]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalAuditStatus:
    """Status summary for the local approval audit trail."""

    ready: bool
    status: str
    audit_record: ApprovalAuditRecord
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    live_audit_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["audit_record"] = self.audit_record.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class ApprovalAuditSummary:
    """Deterministic local summary of the approval audit history."""

    total_events: int
    approved_events: int
    denied_events: int
    blocked_events: int
    status: str = "disabled"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_event(event: ApprovalAuditEvent | Mapping[str, Any] | None = None, **kwargs: Any) -> ApprovalAuditEvent:
    if isinstance(event, ApprovalAuditEvent):
        return event
    payload = _to_payload(event)
    payload.update(kwargs)
    return ApprovalAuditEvent(
        event_id=str(payload.get("event_id") or payload.get("audit_event_id") or "approval_audit_event"),
        event_type=str(payload.get("event_type") or "approval_decision"),
        approval_id=str(payload.get("approval_id") or "approval_audit_default"),
        operator_id=str(payload.get("operator_id") or "operator_default"),
        status=str(payload.get("status") or "blocked"),
        message=str(payload.get("message") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_record(record: ApprovalAuditRecord | Mapping[str, Any] | None = None) -> ApprovalAuditRecord:
    if isinstance(record, ApprovalAuditRecord):
        return record
    payload = _to_payload(record)
    events = payload.get("events")
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
        event_items = tuple(_coerce_event(item) for item in events)
    else:
        event_items = ()
    return ApprovalAuditRecord(
        audit_id=str(payload.get("audit_id") or "approval_audit_default"),
        events=event_items,
        status=str(payload.get("status") or ("recorded_local_only" if event_items else "disabled")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_approval_audit(
    *,
    audit_id: str = "approval_audit_default",
    events: Sequence[ApprovalAuditEvent | Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ApprovalAuditRecord:
    """Build a local-only approval audit record."""

    event_items = tuple(_coerce_event(item) for item in (events or ()))
    return ApprovalAuditRecord(
        audit_id=audit_id,
        events=event_items,
        status="recorded_local_only" if event_items else "disabled",
        metadata=dict(metadata or {}),
    )


def append_approval_event(
    audit_record: ApprovalAuditRecord | Mapping[str, Any] | None = None,
    event: ApprovalAuditEvent | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ApprovalAuditRecord:
    """Append an approval audit event locally."""

    record = _coerce_record(audit_record)
    entry = _coerce_event(event, **kwargs)
    return ApprovalAuditRecord(
        audit_id=record.audit_id,
        events=tuple((*record.events, entry)),
        status="recorded_local_only",
        metadata=dict(record.metadata),
    )


def summarize_approval_history(
    audit_record: ApprovalAuditRecord | Mapping[str, Any] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> ApprovalAuditSummary:
    """Summarize the local approval audit history deterministically."""

    record = _coerce_record(audit_record)
    approved_events = sum(1 for item in record.events if item.status in {"approved", "approved_local_only"})
    denied_events = sum(1 for item in record.events if item.status in {"denied", "rejected"})
    blocked_events = sum(1 for item in record.events if item.status not in {"approved", "approved_local_only"})
    return ApprovalAuditSummary(
        total_events=len(record.events),
        approved_events=approved_events,
        denied_events=denied_events,
        blocked_events=blocked_events,
        status="recorded_local_only" if record.events else "disabled",
        metadata=dict(metadata or {}),
    )


__all__ = [
    "ApprovalAuditEvent",
    "ApprovalAuditRecord",
    "ApprovalAuditStatus",
    "ApprovalAuditSummary",
    "append_approval_event",
    "build_approval_audit",
    "summarize_approval_history",
]
