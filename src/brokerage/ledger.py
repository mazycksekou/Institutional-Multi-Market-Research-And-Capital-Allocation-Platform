"""Local-only brokerage ledger events."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import LedgerEvent


_LEDGER_EVENTS: list[LedgerEvent] = []


def _coerce_event(event: LedgerEvent | Mapping[str, Any] | None = None, **kwargs: Any) -> LedgerEvent:
    if isinstance(event, LedgerEvent):
        return event
    payload = dict(event or {})
    payload.update(kwargs)
    if "event_type" not in payload:
        payload["event_type"] = "brokerage_event"
    if "subject_id" not in payload:
        payload["subject_id"] = str(payload.get("order_id") or payload.get("execution_id") or payload.get("position_id") or "unknown")
    if "event_id" not in payload:
        payload["event_id"] = str(payload.get("ledger_event_id") or payload["subject_id"])
    return LedgerEvent(
        event_id=str(payload["event_id"]),
        event_type=str(payload["event_type"]),
        subject_id=str(payload["subject_id"]),
        created_at=str(payload.get("created_at") or ""),
        payload=dict(payload.get("payload") or {}),
        metadata=dict(payload.get("metadata") or {}),
    )


def record_ledger_event(
    event: LedgerEvent | Mapping[str, Any] | None = None,
    *,
    ledger: list[LedgerEvent] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    item = _coerce_event(event, **kwargs)
    target = ledger if ledger is not None else _LEDGER_EVENTS
    target.append(item)
    return item.as_dict()


def get_ledger_events(*, ledger: list[LedgerEvent] | None = None) -> list[dict[str, Any]]:
    rows = ledger if ledger is not None else _LEDGER_EVENTS
    return [event.as_dict() for event in rows]


def clear_ledger_events(*, ledger: list[LedgerEvent] | None = None) -> None:
    rows = ledger if ledger is not None else _LEDGER_EVENTS
    rows.clear()
