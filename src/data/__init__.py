"""Canonical local data foundation.

This package owns dataset contracts, metadata, source registry helpers,
validation helpers, and local-only loader scaffolds.
"""

from .contracts import DataSourceDescriptor, DatasetMetadata
from .local_loader import load_local_dataset
from .local_platform import (
    DEFAULT_LOCAL_PLATFORM_ASSET_CLASS,
    DEFAULT_LOCAL_PLATFORM_FEATURE_PACK,
    DEFAULT_LOCAL_PLATFORM_MARKET,
    DEFAULT_LOCAL_PLATFORM_MARKET_TYPE,
    DEFAULT_LOCAL_PLATFORM_OWNER,
    DEFAULT_LOCAL_PLATFORM_PROVIDER,
    DEFAULT_LOCAL_PLATFORM_READINESS,
    DEFAULT_LOCAL_PLATFORM_SOURCE_NAME,
    DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE,
    DEFAULT_LOCAL_PLATFORM_STORAGE_PATH,
    DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY,
    DatasetContract,
    LOCAL_DATA_PLATFORM_SCHEMA_VERSION,
    LocalDataPlatform,
    ValidationContract,
    backend_available,
    build_local_platform_dashboard_snapshot,
    build_synthetic_local_dataset,
    create_local_platform,
    load_rows_from_source,
    normalize_dataset_rows,
    validate_rows_against_contract,
)
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
from .market_profile_contracts import MarketProfileContract, build_market_profile_contract, validate_market_profile_contract
from .market_profile_registry import (
    DEFAULT_MARKET_PROFILE_REGISTRY,
    MarketProfileRegistry,
    get_market_profile,
    list_market_profiles,
    register_market_profile,
    reset_market_profile_registry,
)

__all__ = [
    "DataSourceDescriptor",
    "DatasetMetadata",
    "DEFAULT_LOCAL_PLATFORM_ASSET_CLASS",
    "DEFAULT_LOCAL_PLATFORM_FEATURE_PACK",
    "DEFAULT_LOCAL_PLATFORM_MARKET",
    "DEFAULT_LOCAL_PLATFORM_MARKET_TYPE",
    "DEFAULT_LOCAL_PLATFORM_OWNER",
    "DEFAULT_LOCAL_PLATFORM_PROVIDER",
    "DEFAULT_LOCAL_PLATFORM_READINESS",
    "DEFAULT_LOCAL_PLATFORM_SOURCE_NAME",
    "DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE",
    "DEFAULT_LOCAL_PLATFORM_STORAGE_PATH",
    "DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY",
    "LocalSourceRegistry",
    "DEFAULT_LOCAL_SOURCE_REGISTRY",
    "MarketProfileContract",
    "MarketProfileRegistry",
    "DEFAULT_MARKET_PROFILE_REGISTRY",
    "create_dataset_metadata",
    "describe_dataset_metadata",
    "DatasetContract",
    "LocalDataPlatform",
    "LOCAL_DATA_PLATFORM_SCHEMA_VERSION",
    "ValidationContract",
    "backend_available",
    "build_local_platform_dashboard_snapshot",
    "build_synthetic_local_dataset",
    "get_local_source",
    "get_market_profile",
    "list_local_sources",
    "list_market_profiles",
    "load_local_dataset",
    "load_rows_from_source",
    "normalize_dataset_rows",
    "register_local_source",
    "register_market_profile",
    "reset_local_source_registry",
    "reset_market_profile_registry",
    "create_local_platform",
    "validate_dataset_metadata",
    "validate_dataset_rows",
    "validate_local_source_descriptor",
    "build_market_profile_contract",
    "validate_market_profile_contract",
    "validate_rows_against_contract",
]
