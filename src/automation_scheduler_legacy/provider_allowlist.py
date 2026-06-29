from __future__ import annotations

from typing import Any

from src.providers.policy.allowlist import (
    ALLOWED_AI_PROVIDERS,
    BROKER_PROVIDER_HINTS,
    CRYPTO_EXCHANGE_HINTS,
    DEFAULT_AI_PROVIDER,
    FORBIDDEN_AI_PROVIDER_TYPES,
    MARKET_ORDER_PROVIDER_HINTS,
    SPORTSBOOK_PROVIDER_HINTS,
    classify_provider as _canonical_classify_provider,
    is_allowed_ai_provider_name,
    is_internal_deterministic_provider,
    normalize_provider_name,
    provider_allowlist_response as _canonical_provider_allowlist_response,
)

KALSHI_ORDER_HINTS = ("kalshi_order", "kalshi_execution", "kalshi_trading", "kalshi_write", "kalshi")


def classify_provider(provider: str | None, *, provider_type: str | None = None) -> str:
    name = normalize_provider_name(provider)
    if any(hint in name for hint in KALSHI_ORDER_HINTS):
        return "kalshi_order"
    return _canonical_classify_provider(provider, provider_type=provider_type)


def provider_allowlist_response(provider: str | None, *, provider_type: str | None = None) -> dict[str, Any]:
    response = dict(_canonical_provider_allowlist_response(provider, provider_type=provider_type))
    response["provider_class"] = classify_provider(provider, provider_type=provider_type)
    response["ok"] = is_allowed_ai_provider_name(provider, provider_type=provider_type)
    response["status"] = "provider_allowed_for_analysis" if response["ok"] else "forbidden_provider_rejected"
    return response


__all__ = [
    "ALLOWED_AI_PROVIDERS",
    "BROKER_PROVIDER_HINTS",
    "CRYPTO_EXCHANGE_HINTS",
    "DEFAULT_AI_PROVIDER",
    "FORBIDDEN_AI_PROVIDER_TYPES",
    "KALSHI_ORDER_HINTS",
    "MARKET_ORDER_PROVIDER_HINTS",
    "SPORTSBOOK_PROVIDER_HINTS",
    "classify_provider",
    "is_allowed_ai_provider_name",
    "is_internal_deterministic_provider",
    "normalize_provider_name",
    "provider_allowlist_response",
]
