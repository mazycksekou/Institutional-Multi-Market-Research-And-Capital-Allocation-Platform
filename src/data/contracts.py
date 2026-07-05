from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: str | None) -> str:
    return (value or "").strip()


@dataclass(slots=True, frozen=True)
class DataSourceDescriptor:
    """Description of a local-only dataset source."""

    name: str
    source_type: str
    uri: str | None = None
    local_only: bool = True
    description: str = ""
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _normalize_text(self.name))
        object.__setattr__(self, "source_type", _normalize_text(self.source_type).lower())
        object.__setattr__(self, "description", _normalize_text(self.description))
        object.__setattr__(self, "tags", tuple(str(tag).strip() for tag in self.tags if str(tag).strip()))

    @property
    def is_local(self) -> bool:
        return bool(self.local_only) and self.source_type not in {"http", "https", "ws", "wss", "ftp", "sftp", "live"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "uri": self.uri,
            "local_only": self.local_only,
            "description": self.description,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class DatasetMetadata:
    """Canonical metadata for a local dataset."""

    dataset_name: str
    source_name: str
    source_type: str
    schema_version: str = "v1"
    record_count: int = 0
    local_only: bool = True
    created_at: str = field(default_factory=_utc_now_iso)
    path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_name", _normalize_text(self.dataset_name))
        object.__setattr__(self, "source_name", _normalize_text(self.source_name))
        object.__setattr__(self, "source_type", _normalize_text(self.source_type).lower())
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version) or "v1")
        object.__setattr__(self, "path", _normalize_text(self.path) or None)
        object.__setattr__(self, "record_count", max(0, int(self.record_count)))

    @property
    def is_local(self) -> bool:
        return bool(self.local_only) and self.source_type not in {"http", "https", "ws", "wss", "ftp", "sftp", "live"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "schema_version": self.schema_version,
            "record_count": self.record_count,
            "local_only": self.local_only,
            "created_at": self.created_at,
            "path": self.path,
            "metadata": dict(self.metadata),
        }


def coerce_path_text(value: str | Path | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
