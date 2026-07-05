from __future__ import annotations

from typing import Any, Mapping

from .contracts import DataSourceDescriptor, DatasetMetadata, coerce_path_text


def create_dataset_metadata(
    dataset_name: str,
    source: DataSourceDescriptor | Mapping[str, Any] | str,
    *,
    source_type: str | None = None,
    schema_version: str = "v1",
    record_count: int = 0,
    path: str | None = None,
    local_only: bool | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DatasetMetadata:
    if isinstance(source, DataSourceDescriptor):
        descriptor = source
    elif hasattr(source, "as_dict") and hasattr(source, "name") and hasattr(source, "source_type"):
        descriptor = DataSourceDescriptor(
            name=str(getattr(source, "name")),
            source_type=str(getattr(source, "source_type", source_type or "local")),
            uri=getattr(source, "uri", None),
            local_only=bool(getattr(source, "local_only", True if local_only is None else local_only)),
            description=str(getattr(source, "description", "")),
            tags=tuple(getattr(source, "tags", ())),
            metadata=dict(getattr(source, "metadata", {})),
        )
    elif isinstance(source, Mapping):
        descriptor = DataSourceDescriptor(
            name=str(source.get("name", "")),
            source_type=str(source.get("source_type", source_type or "local")),
            uri=source.get("uri") if source.get("uri") is not None else None,
            local_only=bool(source.get("local_only", True if local_only is None else local_only)),
            description=str(source.get("description", "")),
            tags=tuple(source.get("tags", ())),
            metadata=dict(source.get("metadata", {})),
        )
    else:
        descriptor = DataSourceDescriptor(
            name=str(source),
            source_type=source_type or "local",
            local_only=True if local_only is None else bool(local_only),
            metadata=dict(metadata or {}),
        )
    return DatasetMetadata(
        dataset_name=dataset_name,
        source_name=descriptor.name,
        source_type=source_type or descriptor.source_type,
        schema_version=schema_version,
        record_count=record_count,
        local_only=True if local_only is None else bool(local_only),
        path=coerce_path_text(path),
        metadata=metadata or descriptor.metadata,
    )


def describe_dataset_metadata(metadata: DatasetMetadata | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(metadata, DatasetMetadata):
        return metadata.as_dict()
    return dict(metadata)
