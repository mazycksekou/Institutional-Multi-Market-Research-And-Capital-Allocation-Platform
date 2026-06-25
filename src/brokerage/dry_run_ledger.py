"""Local-only dry-run ledger."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import ExecutionRequest, LedgerEvent, OrderRequest
from .dry_run import DryRunLedgerEvent, build_dry_run_ledger_event
from .orders import build_execution_request, build_order_request


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
    for name in ("ledger_id", "ledger_path", "entries", "metadata", "entry_id", "order_request", "execution_request", "ledger_event"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class DryRunLedgerEntry:
    """A single dry-run ledger entry."""

    entry_id: str
    order_request: OrderRequest
    execution_request: ExecutionRequest
    ledger_event: DryRunLedgerEvent
    pipeline_status: str = "dry_run_only"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["order_request"] = self.order_request.as_dict()
        payload["execution_request"] = self.execution_request.as_dict()
        payload["ledger_event"] = self.ledger_event.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class DryRunLedger:
    """Local-only dry-run ledger container."""

    ledger_id: str
    entries: tuple[DryRunLedgerEntry, ...] = ()
    ledger_path: str | None = None
    status: str = "local_only"
    live_persistence_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entries"] = [item.as_dict() for item in self.entries]
        payload["metadata"] = dict(self.metadata)
        return payload


def build_dry_run_ledger(
    *,
    ledger_id: str = "dry_run_ledger",
    ledger_path: str | Path | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DryRunLedger:
    return DryRunLedger(
        ledger_id=ledger_id,
        entries=(),
        ledger_path=str(ledger_path) if ledger_path is not None else None,
        status="local_only",
        live_persistence_allowed=False,
        metadata=dict(metadata or {}),
    )


def _coerce_ledger(ledger: DryRunLedger | Mapping[str, Any] | None) -> DryRunLedger:
    if isinstance(ledger, DryRunLedger):
        return ledger
    payload = _to_payload(ledger)
    entries_payload = payload.get("entries") or ()
    entry_items: list[DryRunLedgerEntry] = []
    for item in entries_payload if isinstance(entries_payload, Sequence) and not isinstance(entries_payload, (str, bytes)) else ():
        entry_items.append(_coerce_entry(item))
    return DryRunLedger(
        ledger_id=str(payload.get("ledger_id") or "dry_run_ledger"),
        entries=tuple(entry_items),
        ledger_path=payload.get("ledger_path"),
        status=str(payload.get("status") or "local_only"),
        live_persistence_allowed=bool(payload.get("live_persistence_allowed", False)),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_entry(entry: DryRunLedgerEntry | Mapping[str, Any] | None, *, metadata: Mapping[str, Any] | None = None) -> DryRunLedgerEntry:
    if isinstance(entry, DryRunLedgerEntry):
        return entry
    payload = _to_payload(entry)
    order_payload = payload.get("order_request")
    execution_payload = payload.get("execution_request")
    ledger_event_payload = payload.get("ledger_event")
    order = order_payload if isinstance(order_payload, OrderRequest) else build_order_request(order_payload)
    execution = execution_payload if isinstance(execution_payload, ExecutionRequest) else build_execution_request(order, candidate=execution_payload if isinstance(execution_payload, Mapping) else None)
    ledger_event = ledger_event_payload if isinstance(ledger_event_payload, DryRunLedgerEvent) else build_dry_run_ledger_event(order, execution_request=execution, metadata=metadata)
    return DryRunLedgerEntry(
        entry_id=str(payload.get("entry_id") or ledger_event.event_id),
        order_request=order,
        execution_request=execution,
        ledger_event=ledger_event,
        pipeline_status=str(payload.get("pipeline_status") or "dry_run_only"),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def append_dry_run_event(
    ledger: DryRunLedger | Mapping[str, Any] | None,
    entry: DryRunLedgerEntry | Mapping[str, Any] | None = None,
    *,
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DryRunLedger:
    """Append a local dry-run event and optionally mirror it to a file."""

    state = _coerce_ledger(ledger)
    if entry is None:
        if order_request is None:
            order_request = build_order_request({})
        order = order_request if isinstance(order_request, OrderRequest) else build_order_request(order_request)
        execution = execution_request if isinstance(execution_request, ExecutionRequest) else build_execution_request(order, candidate=execution_request if isinstance(execution_request, Mapping) else None)
        dry_event = build_dry_run_ledger_event(order, execution_request=execution, metadata=metadata)
        entry_obj = DryRunLedgerEntry(
            entry_id=dry_event.event_id,
            order_request=order,
            execution_request=execution,
            ledger_event=dry_event,
            metadata=dict(metadata or {}),
        )
    else:
        entry_obj = _coerce_entry(entry, metadata=metadata)
    entries = (*state.entries, entry_obj)
    updated = DryRunLedger(
        ledger_id=state.ledger_id,
        entries=entries,
        ledger_path=state.ledger_path,
        status=state.status,
        live_persistence_allowed=False,
        metadata=dict(state.metadata),
    )
    if state.ledger_path:
        path = Path(state.ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(item.as_dict(), sort_keys=True) for item in entries), encoding="utf-8")
    return updated


def verify_dry_run_consistency(ledger: DryRunLedger | Mapping[str, Any] | None) -> dict[str, Any]:
    """Verify that a dry-run ledger remains local and internally consistent."""

    state = _coerce_ledger(ledger)
    blockers: list[str] = []
    previous_created_at: str | None = None
    for entry in state.entries:
        if entry.ledger_event.event_type != "dry_run_execution":
            blockers.append(f"unexpected_event_type:{entry.ledger_event.event_type}")
        if entry.ledger_event.payload.get("broker_adapter_reached"):
            blockers.append("broker_adapter_reached")
        if entry.ledger_event.payload.get("live_submit_allowed"):
            blockers.append("live_submit_allowed")
        if previous_created_at and entry.created_at < previous_created_at:
            blockers.append("non_monotonic_created_at")
        previous_created_at = entry.created_at
    return {
        "ledger_id": state.ledger_id,
        "entry_count": len(state.entries),
        "consistent": not blockers,
        "status": "local_only" if not blockers else "inconsistent",
        "blockers": tuple(dict.fromkeys(blockers)),
        "live_persistence_allowed": False,
        "ledger_path": state.ledger_path,
        "metadata": dict(state.metadata),
    }


__all__ = [
    "DryRunLedger",
    "DryRunLedgerEntry",
    "append_dry_run_event",
    "build_dry_run_ledger",
    "verify_dry_run_consistency",
]

