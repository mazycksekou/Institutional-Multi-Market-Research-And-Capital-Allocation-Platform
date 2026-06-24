"""Canonical local data foundation.

This package owns dataset contracts, metadata, source registry helpers,
validation helpers, and local-only loader scaffolds.
"""

from .contracts import DataSourceDescriptor, DatasetMetadata
from .local_loader import load_local_dataset
from .metadata import create_dataset_metadata, describe_dataset_metadata
from .source_registry import (
    LocalSourceRegistry,
    DEFAULT_LOCAL_SOURCE_REGISTRY,
    get_local_source,
    list_local_sources,
    register_local_source,
    reset_local_source_registry,
)
from .validation import (
    validate_dataset_metadata,
    validate_dataset_rows,
    validate_local_source_descriptor,
)

__all__ = [
    "DataSourceDescriptor",
    "DatasetMetadata",
    "LocalSourceRegistry",
    "DEFAULT_LOCAL_SOURCE_REGISTRY",
    "create_dataset_metadata",
    "describe_dataset_metadata",
    "get_local_source",
    "list_local_sources",
    "load_local_dataset",
    "register_local_source",
    "reset_local_source_registry",
    "validate_dataset_metadata",
    "validate_dataset_rows",
    "validate_local_source_descriptor",
]
