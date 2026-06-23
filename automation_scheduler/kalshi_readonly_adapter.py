from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from src.connectors.errors import ConnectorDisabledError
from src.connectors.prediction_market_data import (
    build_prediction_market_connector_configuration,
    describe_prediction_market_connector_readiness,
)
from src.providers.prediction_markets.adapters import normalize_prediction_market_quote
from src.providers.validation import validate_provider_payload

httpx = SimpleNamespace(Client=object)

PROVIDER_ID = "kalshi_prediction_market"
PROVIDER_TYPE = "prediction_market"
SCHEMA_VERSION = "automation_scheduler.v1.kalshi_prediction_market.v1"

KALSHI_CONNECTOR_CONFIGURATION = build_prediction_market_connector_configuration(
    metadata={"legacy_module": "automation_scheduler.kalshi_readonly_adapter"},
)
KALSHI_CONNECTOR_READINESS = describe_prediction_market_connector_readiness()


class KalshiReadonlyAdapter:
    def __init__(self, contract: dict[str, Any] | None = None):
        self.contract = dict(contract or {})
        self.provider_id = PROVIDER_ID
        self.provider_name = "Kalshi Prediction Market"
        self.provider_type = PROVIDER_TYPE
        self.read_only_mode = True
        self.connector_configuration = dict(KALSHI_CONNECTOR_CONFIGURATION.describe())
        self.connector_readiness = dict(KALSHI_CONNECTOR_READINESS)

    def build_kalshi_url(self, path_name: str) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "path_name": path_name,
            "read_only": True,
            "live_access_enabled": False,
            "connector_configuration": self.connector_configuration,
            "connector_readiness": self.connector_readiness,
            "blockers": [
                "provider_disabled",
                "live_reads_disabled",
                "blocked_missing_credentials",
                "read_only_required",
            ],
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "supports_polling": True,
            "supports_streaming": False,
            "required_credentials": ["KALSHI_API_KEY", "KALSHI_API_SECRET"],
            "supported_markets": ["event_contracts", "yes_no_contracts", "binary_markets"],
            "supports_prediction_markets": True,
            "read_only_mode": True,
            "enabled": False,
            "live_calls_enabled": False,
            "provider_live_calls_enabled": False,
            "dry_run": True,
        }

    def validate_config(self) -> dict[str, Any]:
        blockers = [
            "provider_disabled",
            "live_reads_disabled",
            "blocked_missing_credentials",
            "read_only_required",
        ]
        return {
            "ok": False,
            "status": "provider_disabled",
            "blockers": blockers,
            "credential_status": "missing_credentials",
            "live_reads_enabled": False,
            "provider_enabled": bool(self.contract.get("enabled", False)),
            "live_calls_enabled": False,
            "provider_live_calls_enabled": False,
            "dry_run": bool(self.contract.get("dry_run", True)),
            "read_only_mode": True,
            "connector_configuration": self.connector_configuration,
            "connector_readiness": self.connector_readiness,
        }

    def health_check(self) -> dict[str, Any]:
        cfg = self.validate_config()
        return {
            "ok": True,
            "status": cfg["status"],
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "dry_run": cfg["dry_run"],
            "provider_enabled": bool(cfg["provider_enabled"]),
            "live_calls_enabled": bool(cfg["live_calls_enabled"]),
            "credential_status": cfg["credential_status"],
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "blockers": cfg["blockers"][:10],
            "connector_configuration": self.connector_configuration,
            "connector_readiness": self.connector_readiness,
        }

    def _disabled(self, message: str) -> None:
        raise ConnectorDisabledError(message)

    def fetch_markets(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self._disabled("legacy Kalshi readonly adapter is disabled; use src.connectors.prediction_market_data")

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self._disabled("legacy Kalshi readonly adapter is disabled; use src.connectors.prediction_market_data")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self._disabled("legacy Kalshi readonly adapter is disabled; use src.connectors.prediction_market_data")

    def normalize_payload(self, payload: dict[str, Any], *, event_lookup: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        return normalize_prediction_market_quote(payload, provider="kalshi", market_type="prediction_market")

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_provider_payload(PROVIDER_TYPE, payload, max_staleness_seconds=3600 * 12)


__all__ = [
    "PROVIDER_ID",
    "PROVIDER_TYPE",
    "SCHEMA_VERSION",
    "KalshiReadonlyAdapter",
    "KALSHI_CONNECTOR_CONFIGURATION",
    "KALSHI_CONNECTOR_READINESS",
]
