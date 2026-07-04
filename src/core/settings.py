from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return default


def get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value.strip())
    except (TypeError, ValueError):
        return default


def redact_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if value == "":
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}***{value[-3:]}"


THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")

USE_MOCK_PROVIDERS = get_bool_env("USE_MOCK_PROVIDERS", True)
DRY_RUN = get_bool_env("DRY_RUN", True)
BACKGROUND_AGENT_ENABLED = get_bool_env("BACKGROUND_AGENT_ENABLED", False)

LIVE_AGENT_INTERVAL_SECONDS = get_int_env("LIVE_AGENT_INTERVAL_SECONDS", 60)
ODDS_STALE_SECONDS = get_int_env("ODDS_STALE_SECONDS", 90)
LIVE_FEATURE_STALE_SECONDS = get_int_env("LIVE_FEATURE_STALE_SECONDS", 300)
PROVIDER_CACHE_TTL_SECONDS = get_int_env("PROVIDER_CACHE_TTL_SECONDS", 15)
ALERT_DEDUPE_COOLDOWN_SECONDS = get_int_env("ALERT_DEDUPE_COOLDOWN_SECONDS", 1800)
MIN_PROVIDER_REQUESTS_REMAINING = get_int_env("MIN_PROVIDER_REQUESTS_REMAINING", 25)

BANKROLL_UNITS = get_float_env("BANKROLL_UNITS", 100.0)
KELLY_FRACTION = get_float_env("KELLY_FRACTION", 0.25)
MAX_STAKE_UNITS = get_float_env("MAX_STAKE_UNITS", 1.0)
MAX_DAILY_RISK_UNITS = get_float_env("MAX_DAILY_RISK_UNITS", 5.0)
MAX_EVENT_RISK_UNITS = get_float_env("MAX_EVENT_RISK_UNITS", 2.0)
MAX_CORRELATED_RISK_UNITS = get_float_env("MAX_CORRELATED_RISK_UNITS", 2.0)

AGENT_STATE_PATH = Path("data/agent_state.json")
PROVIDER_CACHE_PATH = Path("data/provider_cache.json")
ALERT_LEDGER_PATH = Path("data/alert_ledger.jsonl")
LIVE_AGENT_LOG_PATH = Path("data/live_agent.log")
EXPOSURE_LEDGER_PATH = Path("data/exposure_ledger.jsonl")
MODEL_REGISTRY_PATH = Path("src") / "sports" / "models" / "compressed" / "model_registry.json"


def get_redacted_config() -> dict[str, Any]:
    return {
        "THE_ODDS_API_KEY": redact_secret(THE_ODDS_API_KEY),
        "ALERT_WEBHOOK_URL": redact_secret(ALERT_WEBHOOK_URL),
        "USE_MOCK_PROVIDERS": USE_MOCK_PROVIDERS,
        "DRY_RUN": DRY_RUN,
        "BACKGROUND_AGENT_ENABLED": BACKGROUND_AGENT_ENABLED,
        "LIVE_AGENT_INTERVAL_SECONDS": LIVE_AGENT_INTERVAL_SECONDS,
        "ODDS_STALE_SECONDS": ODDS_STALE_SECONDS,
        "LIVE_FEATURE_STALE_SECONDS": LIVE_FEATURE_STALE_SECONDS,
        "PROVIDER_CACHE_TTL_SECONDS": PROVIDER_CACHE_TTL_SECONDS,
        "ALERT_DEDUPE_COOLDOWN_SECONDS": ALERT_DEDUPE_COOLDOWN_SECONDS,
        "MIN_PROVIDER_REQUESTS_REMAINING": MIN_PROVIDER_REQUESTS_REMAINING,
        "BANKROLL_UNITS": BANKROLL_UNITS,
        "KELLY_FRACTION": KELLY_FRACTION,
        "MAX_STAKE_UNITS": MAX_STAKE_UNITS,
        "MAX_DAILY_RISK_UNITS": MAX_DAILY_RISK_UNITS,
        "MAX_EVENT_RISK_UNITS": MAX_EVENT_RISK_UNITS,
        "MAX_CORRELATED_RISK_UNITS": MAX_CORRELATED_RISK_UNITS,
        "AGENT_STATE_PATH": str(AGENT_STATE_PATH),
        "PROVIDER_CACHE_PATH": str(PROVIDER_CACHE_PATH),
        "ALERT_LEDGER_PATH": str(ALERT_LEDGER_PATH),
        "LIVE_AGENT_LOG_PATH": str(LIVE_AGENT_LOG_PATH),
        "EXPOSURE_LEDGER_PATH": str(EXPOSURE_LEDGER_PATH),
        "MODEL_REGISTRY_PATH": str(MODEL_REGISTRY_PATH),
    }
