from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .contracts import DataSourceDescriptor
from .validation import validate_local_source_descriptor


REMOTE_SCHEMES = {"http", "https", "ws", "wss", "ftp", "sftp"}
LOCAL_SUFFIXES = {".json", ".jsonl", ".ndjson", ".csv"}


def _coerce_source(source: DataSourceDescriptor | dict[str, Any]) -> DataSourceDescriptor:
    if isinstance(source, DataSourceDescriptor):
        return source
    if hasattr(source, "as_dict") and hasattr(source, "name") and hasattr(source, "source_type"):
        return DataSourceDescriptor(
            name=str(getattr(source, "name")),
            source_type=str(getattr(source, "source_type", "local")),
            uri=getattr(source, "uri", None),
            local_only=bool(getattr(source, "local_only", True)),
            description=str(getattr(source, "description", "")),
            tags=tuple(getattr(source, "tags", ())),
            metadata=dict(getattr(source, "metadata", {})),
        )
    if isinstance(source, dict):
        return DataSourceDescriptor(
            name=str(source.get("name", "")),
            source_type=str(source.get("source_type", "local")),
            uri=source.get("uri") if source.get("uri") is not None else None,
            local_only=bool(source.get("local_only", True)),
            description=str(source.get("description", "")),
            tags=tuple(source.get("tags", ())),
            metadata=dict(source.get("metadata", {})),
        )
    raise TypeError("source must be a DataSourceDescriptor or mapping")


def _is_remote_uri(value: str | None) -> bool:
    if not value:
        return False
    scheme = urlparse(value).scheme.lower()
    return scheme in REMOTE_SCHEMES


def _read_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        row = json.loads(text)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_local_dataset(
    source: DataSourceDescriptor | dict[str, Any],
    *,
    path: str | Path | None = None,
) -> list[dict[str, Any]]:
    descriptor = _coerce_source(source)
    verdict = validate_local_source_descriptor(descriptor)
    if not verdict["ok"]:
        raise ValueError("Only local sources are supported by src.data.local_loader")

    candidate = path if path is not None else descriptor.uri
    if candidate is None:
        return []

    candidate_text = str(candidate)
    if _is_remote_uri(candidate_text):
        raise ValueError("Remote sources are not supported by src.data.local_loader")

    resolved = Path(candidate_text).expanduser()
    if not resolved.exists():
        return []

    suffix = resolved.suffix.lower()
    if suffix == ".json":
        return _read_json(resolved)
    if suffix in {".jsonl", ".ndjson"}:
        return _read_jsonl(resolved)
    if suffix == ".csv":
        return _read_csv(resolved)
    if suffix in LOCAL_SUFFIXES:
        return _read_json(resolved)

    text = resolved.read_text(encoding="utf-8")
    return [{"value": line} for line in text.splitlines() if line.strip()]
