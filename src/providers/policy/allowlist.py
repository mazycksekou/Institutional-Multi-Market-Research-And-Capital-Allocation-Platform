from __future__ import annotations

from typing import Any


ALLOWED_AI_PROVIDERS = ["deepseek", "openai"]
DEFAULT_AI_PROVIDER = "deepseek"

FORBIDDEN_AI_PROVIDER_TYPES = {
    "broker",
    "stock_broker",
    "sportsbook",
    "market_order",
    "market_execution",
    "crypto_exchange",
    "exchange",
    "execution_provider",
    "unknown",
}

BROKER_PROVIDER_HINTS = ("broker", "alpaca", "interactive_brokers", "ibkr", "schwab", "tradier", "robinhood")
SPORTSBOOK_PROVIDER_HINTS = ("sportsbook", "draftkings", "fanduel", "betmgm", "caesars", "espnbet", "bet365")
MARKET_ORDER_PROVIDER_HINTS = ("order", "execution", "trading", "write")
CRYPTO_EXCHANGE_HINTS = ("crypto_exchange", "coinbase", "binance", "kraken", "bybit", "okx")
KALSHI_ORDER_HINTS = ("kalshi_order", "kalshi_execution", "kalshi_trading", "kalshi_write", "kalshi")


def _locked_safety_flags() -> dict[str, Any]:
    return {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "dry_run": True,
        "simulation_only": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "market_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "secrets_detected": False,
    }


def normalize_provider_name(provider: str | None) -> str:
    return str(provider or "").strip().lower().replace(" ", "_").replace("-", "_")


def classify_provider(provider: str | None, *, provider_type: str | None = None) -> str:
    explicit_type = normalize_provider_name(provider_type)
    if explicit_type:
        if explicit_type == "kalshi_order":
            return "kalshi_order"
        if explicit_type in {"deepseek", "openai", "internal_diagnostics", "internal_deterministic"}:
            return explicit_type
        if explicit_type in FORBIDDEN_AI_PROVIDER_TYPES:
            return explicit_type
    name = normalize_provider_name(provider)
    if name in {"deepseek", "openai"}:
        return name
    if name in {"internal_diagnostics", "internal_deterministic", "python_diagnostics", "local_math", "internal_math"}:
        return "internal_deterministic"
    if any(hint in name for hint in KALSHI_ORDER_HINTS):
        return "kalshi_order"
    if any(hint in name for hint in BROKER_PROVIDER_HINTS):
        return "broker"
    if any(hint in name for hint in SPORTSBOOK_PROVIDER_HINTS):
        return "sportsbook"
    if any(hint in name for hint in MARKET_ORDER_PROVIDER_HINTS):
        return "market_order"
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
        **_locked_safety_flags(),
    }
