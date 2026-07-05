from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import DataSourceDescriptor, DatasetMetadata


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        return value.as_dict()
    raise TypeError("value must be a mapping or canonical descriptor")


def validate_dataset_metadata(
    metadata: DatasetMetadata | Mapping[str, Any],
    *,
    required_fields: Sequence[str] = ("dataset_name", "source_name", "source_type"),
) -> dict[str, Any]:
    payload = _mapping(metadata)
    missing_fields = [field for field in required_fields if not payload.get(field)]
    return {
        "ok": not missing_fields,
        "status": "accepted" if not missing_fields else "rejected",
        "missing_fields": missing_fields,
        "field_count": len(payload),
        "metadata": payload,
    }


def validate_local_source_descriptor(
    source: DataSourceDescriptor | Mapping[str, Any],
) -> dict[str, Any]:
    payload = _mapping(source)
    missing_fields = [field for field in ("name", "source_type") if not payload.get(field)]
    is_local = bool(payload.get("local_only", True)) and str(payload.get("source_type", "")).lower() not in {
        "http",
        "https",
        "ws",
        "wss",
        "ftp",
        "sftp",
        "live",
    }
    errors = list(missing_fields)
    if not is_local:
        errors.append("non_local_source")
    return {
        "ok": not errors,
        "status": "accepted" if not errors else "rejected",
        "errors": errors,
        "missing_fields": missing_fields,
        "is_local": is_local,
        "source": payload,
    }


def validate_dataset_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    required_fields: Sequence[str] = ("timestamp", "source_name"),
) -> dict[str, Any]:
    missing_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        payload = _mapping(row)
        missing_fields = [field for field in required_fields if not payload.get(field)]
        if missing_fields:
            missing_rows.append({"index": index, "missing_fields": missing_fields})
    return {
        "ok": not missing_rows,
        "status": "accepted" if not missing_rows else "rejected",
        "missing_rows": missing_rows,
        "row_count": len(rows),
    }
