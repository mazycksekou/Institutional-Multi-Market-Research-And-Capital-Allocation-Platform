"""Canonical provider landing zone for future migration batches.

This package is intentionally scaffold-only for now. It defines stable
provider contracts, registry, health, and normalization interfaces without
depending on legacy provider ownership.
"""

from .base import ProviderAdapterBase, ProviderAdapterProtocol
from .contracts import PROVIDER_SCHEMA_VERSION, ProviderContract, build_scaffold_provider_contract
from .errors import (
    ProviderConfigurationError,
    ProviderError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from .health import ProviderHealthStatus, build_scaffold_health_status
from .normalization import normalize_provider_payload
from .registry import ProviderRegistry, create_provider_registry

__all__ = [
    "PROVIDER_SCHEMA_VERSION",
    "ProviderAdapterBase",
    "ProviderAdapterProtocol",
    "ProviderConfigurationError",
    "ProviderContract",
    "ProviderError",
    "ProviderHealthStatus",
    "ProviderRegistry",
    "ProviderResponseError",
    "ProviderUnavailableError",
    "build_scaffold_health_status",
    "build_scaffold_provider_contract",
    "create_provider_registry",
    "normalize_provider_payload",
]
