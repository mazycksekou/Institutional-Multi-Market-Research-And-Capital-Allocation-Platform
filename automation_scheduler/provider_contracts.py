from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .scheduler_config import SCHEMA_VERSION, utc_now_iso

PROVIDER_CONTRACT_SCHEMA_VERSION = f"{SCHEMA_VERSION}.provider_contracts.v1"

PROVIDER_TYPES = (
    "sportsbook_odds",
    "player_props",
    "prediction_market",
    "stock_price",
    "stock_fundamentals",
    "news_events",
    "injury_weather",
)


def ensure_provider_runtime_directories(base_data_dir: str = "data") -> dict[str, str]:
    paths = {
        "provider_health": str(Path(base_data_dir) / "provider_health"),
        "provider_contracts": str(Path(base_data_dir) / "provider_contracts"),
        "provider_payload_samples": str(Path(base_data_dir) / "provider_payload_samples"),
    }
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)
    return paths


def build_provider_contract(
    *,
    provider_id: str,
    provider_name: str,
    provider_type: str,
    supports_streaming: bool = False,
    supports_polling: bool = True,
    min_poll_seconds: int = 60,
    rate_limit_note: str = "dry_run_only",
    required_credentials: list[str] | None = None,
    supported_markets: list[str] | None = None,
    enabled: bool = False,
    live_calls_enabled: bool = False,
) -> dict[str, Any]:
    if provider_type not in PROVIDER_TYPES:
        raise ValueError(f"unknown provider_type: {provider_type}")
    creds = list(required_credentials or [])
    return {
        "provider_id": provider_id,
        "provider_name": provider_name,
        "provider_type": provider_type,
        "enabled": bool(enabled),
        "dry_run": True,
        "supports_streaming": bool(supports_streaming),
        "supports_polling": bool(supports_polling),
        "min_poll_seconds": max(1, int(min_poll_seconds)),
        "rate_limit_note": rate_limit_note,
        "credential_status": "not_required" if not creds else "missing_credentials",
        "required_credentials": creds,
        "supported_markets": list(supported_markets or []),
        "output_schema_version": PROVIDER_CONTRACT_SCHEMA_VERSION,
        "last_health_status": "not_checked",
        "live_calls_enabled": bool(live_calls_enabled),
        "provider_live_calls_enabled": False,
        "provider_credentials_required": False,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "contract_status": "defined",
        "created_at": utc_now_iso(),
    }


def get_default_provider_contracts() -> dict[str, dict[str, Any]]:
    return {
        "sportsbook_placeholder": build_provider_contract(
            provider_id="sportsbook_placeholder",
            provider_name="Sportsbook Placeholder",
            provider_type="sportsbook_odds",
            min_poll_seconds=15,
            supported_markets=["h2h", "spreads", "totals"],
        ),
        "player_props_placeholder": build_provider_contract(
            provider_id="player_props_placeholder",
            provider_name="Player Props Placeholder",
            provider_type="player_props",
            min_poll_seconds=30,
            supported_markets=["points", "assists", "rebounds"],
        ),
        "kalshi_placeholder": build_provider_contract(
            provider_id="kalshi_placeholder",
            provider_name="Kalshi Placeholder",
            provider_type="prediction_market",
            supports_streaming=True,
            min_poll_seconds=15,
            supported_markets=["yes_no_contracts"],
        ),
        "stock_price_placeholder": build_provider_contract(
            provider_id="stock_price_placeholder",
            provider_name="Stock Price Placeholder",
            provider_type="stock_price",
            supports_streaming=True,
            min_poll_seconds=5,
            supported_markets=["equities"],
        ),
        "stock_fundamentals_placeholder": build_provider_contract(
            provider_id="stock_fundamentals_placeholder",
            provider_name="Stock Fundamentals Placeholder",
            provider_type="stock_fundamentals",
            min_poll_seconds=300,
            supported_markets=["fundamentals"],
        ),
        "news_events_placeholder": build_provider_contract(
            provider_id="news_events_placeholder",
            provider_name="News Events Placeholder",
            provider_type="news_events",
            min_poll_seconds=60,
            supported_markets=["macro", "injury_news", "team_news"],
        ),
        "injury_weather_placeholder": build_provider_contract(
            provider_id="injury_weather_placeholder",
            provider_name="Injury Weather Placeholder",
            provider_type="injury_weather",
            min_poll_seconds=60,
            supported_markets=["injuries", "lineups", "weather"],
        ),
    }


def write_provider_contract_snapshot(base_data_dir: str = "data") -> str:
    paths = ensure_provider_runtime_directories(base_data_dir)
    payload = {
        "schema_version": PROVIDER_CONTRACT_SCHEMA_VERSION,
        "written_at": utc_now_iso(),
        "providers": get_default_provider_contracts(),
        "dry_run": True,
    }
    path = Path(paths["provider_contracts"]) / "provider_contracts.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)

