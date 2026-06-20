from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROVIDER_SCHEMA_VERSION = "src.providers.skeleton.v1"
PROVIDER_CONTRACT_SCHEMA_VERSION = "src.providers.contracts.v1"

PROVIDER_TYPES = (
    "sportsbook_odds",
    "player_props",
    "prediction_market",
    "stock_price",
    "stock_fundamentals",
    "news_events",
    "injury_weather",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (list, tuple, set)):
        return tuple(str(value) for value in values)
    if isinstance(values, str):
        return (values,)
    return (str(values),)


def _resolve_base_data_dir(base_data_dir: str = "data") -> Path:
    return Path(base_data_dir).resolve()


@dataclass(slots=True)
class ProviderContract:
    provider_id: str
    provider_name: str = ""
    provider_type: str = "unknown"
    enabled: bool = False
    dry_run: bool = True
    supports_streaming: bool = False
    supports_polling: bool = True
    min_poll_seconds: int = 60
    rate_limit_note: str = "dry_run_only"
    credential_status: str = "not_required"
    required_credentials: tuple[str, ...] = ()
    supported_markets: tuple[str, ...] = ()
    live_calls_enabled: bool = False
    contract_status: str = "scaffold_only"
    output_schema_version: str = PROVIDER_CONTRACT_SCHEMA_VERSION
    last_health_status: str = "not_checked"
    provider_live_calls_enabled: bool = False
    provider_credentials_required: bool = False
    human_approval_required: bool = True
    auto_execution_enabled: bool = False
    auto_bet_enabled: bool = False
    auto_trade_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = PROVIDER_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ProviderContract":
        return cls(
            provider_id=str(data.get("provider_id") or ""),
            provider_name=str(data.get("provider_name") or ""),
            provider_type=str(data.get("provider_type") or "unknown"),
            enabled=bool(data.get("enabled", False)),
            dry_run=bool(data.get("dry_run", True)),
            supports_streaming=bool(data.get("supports_streaming", False)),
            supports_polling=bool(data.get("supports_polling", True)),
            min_poll_seconds=max(1, int(data.get("min_poll_seconds", 60))),
            rate_limit_note=str(data.get("rate_limit_note") or "dry_run_only"),
            credential_status=str(
                data.get("credential_status")
                or ("missing_credentials" if data.get("required_credentials") else "not_required")
            ),
            required_credentials=_as_tuple(data.get("required_credentials")),
            supported_markets=_as_tuple(data.get("supported_markets")),
            live_calls_enabled=bool(data.get("live_calls_enabled", False)),
            contract_status=str(data.get("contract_status") or "scaffold_only"),
            output_schema_version=str(data.get("output_schema_version") or PROVIDER_CONTRACT_SCHEMA_VERSION),
            last_health_status=str(data.get("last_health_status") or "not_checked"),
            provider_live_calls_enabled=bool(data.get("provider_live_calls_enabled", False)),
            provider_credentials_required=bool(data.get("provider_credentials_required", False)),
            human_approval_required=bool(data.get("human_approval_required", True)),
            auto_execution_enabled=bool(data.get("auto_execution_enabled", False)),
            auto_bet_enabled=bool(data.get("auto_bet_enabled", False)),
            auto_trade_enabled=bool(data.get("auto_trade_enabled", False)),
            metadata=dict(data.get("metadata") or {}),
            schema_version=str(data.get("schema_version") or PROVIDER_SCHEMA_VERSION),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "supports_streaming": self.supports_streaming,
            "supports_polling": self.supports_polling,
            "min_poll_seconds": self.min_poll_seconds,
            "rate_limit_note": self.rate_limit_note,
            "credential_status": self.credential_status,
            "required_credentials": list(self.required_credentials),
            "supported_markets": list(self.supported_markets),
            "live_calls_enabled": self.live_calls_enabled,
            "contract_status": self.contract_status,
            "output_schema_version": self.output_schema_version,
            "last_health_status": self.last_health_status,
            "provider_live_calls_enabled": self.provider_live_calls_enabled,
            "provider_credentials_required": self.provider_credentials_required,
            "human_approval_required": self.human_approval_required,
            "auto_execution_enabled": self.auto_execution_enabled,
            "auto_bet_enabled": self.auto_bet_enabled,
            "auto_trade_enabled": self.auto_trade_enabled,
            "metadata": dict(self.metadata),
            "schema_version": self.schema_version,
        }


def build_scaffold_provider_contract(
    provider_id: str,
    provider_name: str = "",
    provider_type: str = "unknown",
) -> ProviderContract:
    return ProviderContract(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_type=provider_type,
        contract_status="scaffold_only",
    )


def ensure_provider_runtime_directories(base_data_dir: str = "data") -> dict[str, str]:
    root = _resolve_base_data_dir(base_data_dir)
    data_sources = root / "data_sources"
    paths = {
        "provider_health": str(data_sources / "provider_health"),
        "provider_contracts": str(data_sources / "provider_contracts"),
        "provider_payload_samples": str(data_sources / "provider_payload_samples"),
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
        "created_at": _utc_now_iso(),
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
        "prediction_market_placeholder": build_provider_contract(
            provider_id="prediction_market_placeholder",
            provider_name="Prediction Market Placeholder",
            provider_type="prediction_market",
            supports_streaming=False,
            min_poll_seconds=30,
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
        "written_at": _utc_now_iso(),
        "providers": get_default_provider_contracts(),
        "dry_run": True,
    }
    path = Path(paths["provider_contracts"]) / "provider_contracts.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)
