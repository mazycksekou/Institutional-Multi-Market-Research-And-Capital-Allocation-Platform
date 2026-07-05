from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from .contracts import DataSourceDescriptor


@dataclass(slots=True)
class LocalSourceRegistry:
    """In-memory registry for local-only data sources."""

    _sources: dict[str, DataSourceDescriptor] = field(default_factory=dict)

    def register(self, source: DataSourceDescriptor) -> DataSourceDescriptor:
        if not hasattr(source, "as_dict") or not hasattr(source, "is_local"):
            raise TypeError("source must behave like a DataSourceDescriptor")
        if not bool(getattr(source, "is_local")):
            raise ValueError("Only local sources can be registered.")
        name = str(getattr(source, "name", "")).strip()
        self._sources[name] = source  # type: ignore[assignment]
        return source

    def get(self, name: str) -> DataSourceDescriptor | None:
        return self._sources.get(str(name).strip())

    def list(self) -> tuple[DataSourceDescriptor, ...]:
        return tuple(self._sources[name] for name in sorted(self._sources))

    def clear(self) -> None:
        self._sources.clear()

    def extend(self, sources: Iterable[DataSourceDescriptor]) -> None:
        for source in sources:
            self.register(source)


DEFAULT_LOCAL_SOURCE_REGISTRY = LocalSourceRegistry()


def register_local_source(source: DataSourceDescriptor) -> DataSourceDescriptor:
    return DEFAULT_LOCAL_SOURCE_REGISTRY.register(source)


def list_local_sources() -> tuple[DataSourceDescriptor, ...]:
    return DEFAULT_LOCAL_SOURCE_REGISTRY.list()


def get_local_source(name: str) -> DataSourceDescriptor | None:
    return DEFAULT_LOCAL_SOURCE_REGISTRY.get(name)


def reset_local_source_registry() -> None:
    DEFAULT_LOCAL_SOURCE_REGISTRY.clear()
