from __future__ import annotations

from typing import Any

from .security_policy import ALLOWED_AI_PROVIDERS, DEFAULT_AI_PROVIDER, locked_safety_flags


FORBIDDEN_AI_PROVIDER_TYPES = {
    "broker",
    "stock_broker",
    "sportsbook",
    "kalshi_order",
    "kalshi_execution",
    "prediction_market_order",
    "crypto_exchange",
    "exchange",
    "execution_provider",
    "unknown",
}

BROKER_PROVIDER_HINTS = ("broker", "alpaca", "interactive_brokers", "ibkr", "schwab", "tradier", "robinhood")
SPORTSBOOK_PROVIDER_HINTS = ("sportsbook", "draftkings", "fanduel", "betmgm", "caesars", "espnbet", "bet365", "sharp")
KALSHI_ORDER_HINTS = ("kalshi_order", "kalshi_execution", "kalshi_trading", "kalshi_write")
CRYPTO_EXCHANGE_HINTS = ("crypto_exchange", "coinbase", "binance", "kraken", "bybit", "okx")


def normalize_provider_name(provider: str | None) -> str:
    return str(provider or "").strip().lower().replace(" ", "_").replace("-", "_")


def classify_provider(provider: str | None, *, provider_type: str | None = None) -> str:
    explicit_type = normalize_provider_name(provider_type)
    if explicit_type:
        if explicit_type in {"deepseek", "openai", "internal_diagnostics", "internal_deterministic"}:
            return explicit_type
        if explicit_type in FORBIDDEN_AI_PROVIDER_TYPES:
            return explicit_type
    name = normalize_provider_name(provider)
    if name in {"deepseek", "openai"}:
        return name
    if name in {"internal_diagnostics", "internal_deterministic", "python_diagnostics", "local_math"}:
        return "internal_deterministic"
    if any(hint in name for hint in BROKER_PROVIDER_HINTS):
        return "broker"
    if any(hint in name for hint in SPORTSBOOK_PROVIDER_HINTS):
        return "sportsbook"
    if any(hint in name for hint in KALSHI_ORDER_HINTS):
        return "kalshi_order"
    if name == "kalshi":
        return "kalshi_order"
    if any(hint in name for hint in CRYPTO_EXCHANGE_HINTS):
        return "crypto_exchange"
    return "unknown" if name else "unknown"


def is_internal_deterministic_provider(provider: str | None, *, provider_type: str | None = None) -> bool:
    return classify_provider(provider, provider_type=provider_type) == "internal_deterministic"


def is_allowed_ai_provider_name(provider: str | None, *, provider_type: str | None = None) -> bool:
    provider_class = classify_provider(provider, provider_type=provider_type)
    return provider_class in set(ALLOWED_AI_PROVIDERS) or provider_class == "internal_deterministic"


def provider_allowlist_response(provider: str | None, *, provider_type: str | None = None) -> dict[str, Any]:
    provider_class = classify_provider(provider, provider_type=provider_type)
    allowed = is_allowed_ai_provider_name(provider, provider_type=provider_type)
    return {
        "ok": allowed,
        "status": "provider_allowed_for_analysis" if allowed else "forbidden_provider_rejected",
        "provider_name": provider,
        "provider_type": provider_type,
        "provider_class": provider_class,
        "allowed_ai_providers": ALLOWED_AI_PROVIDERS,
        "default_provider": DEFAULT_AI_PROVIDER,
        "forbidden_provider_policy": "deny_by_default",
        **locked_safety_flags(),
    }
