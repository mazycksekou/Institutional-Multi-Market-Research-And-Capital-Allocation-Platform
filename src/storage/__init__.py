"""Storage boundaries for archive and future persistence adapters."""

from .local_store import (
    LOCAL_STORAGE_SCHEMA_VERSION,
    LocalStorageEngine,
    SUPPORTED_LOCAL_STORAGE_BACKENDS,
    backend_available,
    create_local_storage_engine,
)

__all__ = [
    "LOCAL_STORAGE_SCHEMA_VERSION",
    "LocalStorageEngine",
    "SUPPORTED_LOCAL_STORAGE_BACKENDS",
    "backend_available",
    "create_local_storage_engine",
]
