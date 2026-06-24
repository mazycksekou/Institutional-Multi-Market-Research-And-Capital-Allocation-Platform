from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .contracts import BacktestDatasetContract


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


def validate_backtest_dataset_order(
    rows: Sequence[Mapping[str, Any]],
    *,
    timestamp_field: str = "timestamp",
) -> dict[str, Any]:
    errors: list[str] = []
    ordered_timestamps: list[str] = []
    previous: datetime | None = None
    for index, row in enumerate(rows):
        if timestamp_field not in row or row[timestamp_field] in (None, ""):
            errors.append(f"missing_timestamp_row_{index}")
            continue
        parsed = _parse_timestamp(row[timestamp_field])
        if parsed is None:
            errors.append(f"invalid_timestamp_row_{index}")
            continue
        ordered_timestamps.append(parsed.isoformat())
        if previous is not None and parsed < previous:
            errors.append(f"non_chronological_row_{index}")
        previous = parsed
    return {
        "ok": not errors,
        "status": "accepted" if not errors else "rejected",
        "errors": errors,
        "row_count": len(rows),
        "timestamp_field": timestamp_field,
        "ordered_timestamps": ordered_timestamps,
    }


def build_backtest_dataset_contract(
    rows: Sequence[Mapping[str, Any]],
    *,
    dataset_name: str,
    source_name: str,
    timestamp_field: str = "timestamp",
    local_only: bool = True,
    metadata: dict[str, Any] | None = None,
) -> BacktestDatasetContract:
    return BacktestDatasetContract(
        dataset_name=dataset_name,
        source_name=source_name,
        rows=[dict(row) for row in rows],
        timestamp_field=timestamp_field,
        local_only=local_only,
        metadata=dict(metadata or {}),
    )


def sort_backtest_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    timestamp_field: str = "timestamp",
) -> list[dict[str, Any]]:
    return sorted(
        (dict(row) for row in rows),
        key=lambda row: _parse_timestamp(row.get(timestamp_field)) or datetime.min.replace(tzinfo=timezone.utc),
    )
