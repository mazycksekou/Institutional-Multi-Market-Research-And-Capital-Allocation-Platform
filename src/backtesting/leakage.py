from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def _parse_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def detect_future_timestamps(
    rows: Sequence[Mapping[str, Any]],
    *,
    timestamp_field: str = "timestamp",
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    future_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        parsed = _parse_timestamp(row.get(timestamp_field))
        if parsed is None:
            continue
        if parsed > current:
            future_rows.append(
                {
                    "index": index,
                    "timestamp": parsed.isoformat(),
                    "timestamp_field": timestamp_field,
                }
            )
    return {
        "ok": not future_rows,
        "status": "accepted" if not future_rows else "rejected",
        "timestamp_field": timestamp_field,
        "checked_rows": len(rows),
        "future_rows": future_rows,
    }


def assert_no_future_timestamps(
    rows: Sequence[Mapping[str, Any]],
    *,
    timestamp_field: str = "timestamp",
    now: datetime | None = None,
) -> None:
    report = detect_future_timestamps(rows, timestamp_field=timestamp_field, now=now)
    if not report["ok"]:
        raise ValueError("future timestamps are not allowed in backtest datasets")
