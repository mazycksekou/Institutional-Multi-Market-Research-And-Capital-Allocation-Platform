"""Sportsbook provider namespace for the future canonical provider package."""

from .contracts import (
    SPORTSBOOK_PROVIDER_TYPE,
    SAMPLE_DRY_RUN_PAYLOAD,
    SportsbookProviderContract,
    build_sportsbook_provider_contract,
    normalize_sportsbook_payload,
    validate_sportsbook_payload,
)
from .adapters import (
    SPORTSBOOK_PROVIDER_TYPE as ADAPTER_SPORTSBOOK_PROVIDER_TYPE,
    SportsbookEventQuote,
    SportsbookProviderAdapter,
    SportsbookQuote,
    build_sportsbook_event_quote,
    build_sportsbook_quote,
    normalize_sportsbook_event,
    normalize_sportsbook_odds,
    normalize_sportsbook_quote,
)

__all__ = [
    "ADAPTER_SPORTSBOOK_PROVIDER_TYPE",
    "SPORTSBOOK_PROVIDER_TYPE",
    "SportsbookEventQuote",
    "SportsbookProviderAdapter",
    "SportsbookProviderContract",
    "SportsbookQuote",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_sportsbook_event_quote",
    "build_sportsbook_provider_contract",
    "build_sportsbook_quote",
    "normalize_sportsbook_event",
    "normalize_sportsbook_payload",
    "normalize_sportsbook_odds",
    "normalize_sportsbook_quote",
    "validate_sportsbook_payload",
]
