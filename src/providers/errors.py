from __future__ import annotations


class ProviderError(Exception):
    """Base error for canonical provider code."""


class ProviderConfigurationError(ProviderError):
    """Raised when a provider contract or registry entry is invalid."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot satisfy a request in scaffold mode."""


class ProviderResponseError(ProviderError):
    """Raised when a provider response is malformed or incomplete."""
