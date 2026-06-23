from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.connectors.prediction_market_data import (
    build_prediction_market_connector_configuration,
    build_prediction_market_disabled_live_client,
    describe_prediction_market_connector_readiness,
)
from src.connectors.errors import ConnectorDisabledError
from src.core.entity_resolver import normalize_ticket_fields
from src.providers.prediction_markets.adapters import PredictionMarketProviderAdapter, normalize_prediction_market_quote
from src.providers.policy.secret_policy import assert_no_secret_leak
from src.providers.registry import get_provider_registry
from src.providers.validation import validate_provider_payload


SCHEMA_VERSION = "src.services.prediction_market_runtime_bridge.v1"
PROVIDER_ID = "kalshi_prediction_market"

PREDICTION_MARKET_CONNECTOR_CONFIGURATION = build_prediction_market_connector_configuration(
    metadata={"bridge_module": "src.services.prediction_market_runtime_bridge"},
)
PREDICTION_MARKET_CONNECTOR_READINESS = describe_prediction_market_connector_readiness()
PREDICTION_MARKET_DISABLED_CLIENT = build_prediction_market_disabled_live_client()
PREDICTION_MARKET_PROVIDER_ADAPTER = PredictionMarketProviderAdapter()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_prediction_market_readonly_contract() -> dict[str, Any]:
    return dict(get_provider_registry(include_legacy_aliases=True).get(PROVIDER_ID, {}))


def build_prediction_market_readonly_adapter() -> "PredictionMarketReadonlyAdapter":
    return PredictionMarketReadonlyAdapter(build_prediction_market_readonly_contract())


class PredictionMarketReadonlyAdapter:
    def __init__(self, contract: dict[str, Any] | None = None):
        self.contract = dict(contract or {})
        self.provider_id = PROVIDER_ID
        self.provider_name = "Kalshi Prediction Market"
        self.provider_type = "prediction_market"
        self.read_only_mode = True
        self.connector_configuration = dict(PREDICTION_MARKET_CONNECTOR_CONFIGURATION.describe())
        self.connector_readiness = dict(PREDICTION_MARKET_CONNECTOR_READINESS)

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
        self._disabled("prediction market runtime bridge is disabled; use src.connectors.prediction_market_data")

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self._disabled("prediction market runtime bridge is disabled; use src.connectors.prediction_market_data")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self._disabled("prediction market runtime bridge is disabled; use src.connectors.prediction_market_data")

    def normalize_payload(self, payload: dict[str, Any], *, event_lookup: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        return normalize_prediction_market_quote(payload, provider="kalshi", market_type="kalshi_prediction_market")

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_provider_payload("prediction_market", payload, max_staleness_seconds=3600 * 12)
KalshiReadonlyAdapter = PredictionMarketReadonlyAdapter


def enrich_with_kalshi(ticket: dict[str, Any]) -> dict[str, Any]:
    normalized_ticket = normalize_ticket_fields(ticket)
    return {
        "provider": "kalshi",
        "canonical_provider": "prediction_market",
        "provider_status": "unavailable",
        "reason": "prediction_market_connector_boundary_disabled",
        "data": [],
        "provider_notes": [
            "Prediction-market runtime access is routed through the canonical connector boundary.",
            "Legacy Kalshi provider shells are no longer runtime dependencies.",
        ],
        "normalized_ticket": normalized_ticket,
        "connector_configuration": dict(PREDICTION_MARKET_CONNECTOR_CONFIGURATION.describe()),
        "connector_readiness": dict(PREDICTION_MARKET_CONNECTOR_READINESS),
        "disabled_client": PREDICTION_MARKET_DISABLED_CLIENT.describe(),
        "provider_contract": PREDICTION_MARKET_PROVIDER_ADAPTER.contract.as_dict(),
        "provider_health": PREDICTION_MARKET_PROVIDER_ADAPTER.health_check(),
        "schema_version": SCHEMA_VERSION,
    }


def enrich_with_prediction_market(ticket: dict[str, Any]) -> dict[str, Any]:
    return enrich_with_kalshi(ticket)


def _resolve_base_data_dir(base_data_dir: str = "data") -> Path:
    candidate = Path(base_data_dir)
    return candidate if candidate.is_absolute() else Path.cwd() / candidate


def _disabled_snapshot(adapter: PredictionMarketReadonlyAdapter | None = None) -> dict[str, Any]:
    instance = adapter or PredictionMarketReadonlyAdapter()
    cfg = instance.validate_config()
    return {
        "ok": True,
        "status": cfg["status"],
        "provider_id": instance.provider_id,
        "provider_name": instance.provider_name,
        "received_at": _utc_now_iso(),
        "dry_run": True,
        "records_received": 0,
        "records_valid": 0,
        "records_rejected": 0,
        "rejection_reason_counts": {},
        "http_status": None,
        "diagnostic": {
            "bridge_module": "src.services.prediction_market_runtime_bridge",
            "connector_configuration": instance.connector_configuration,
            "connector_readiness": instance.connector_readiness,
        },
        "blockers": list(cfg["blockers"])[:10],
        "records": [],
        "schema_version": SCHEMA_VERSION,
        "connector_configuration": instance.connector_configuration,
        "connector_readiness": instance.connector_readiness,
    }


def get_prediction_market_snapshot(adapter: PredictionMarketReadonlyAdapter | None = None) -> dict[str, Any]:
    instance = adapter or PredictionMarketReadonlyAdapter()
    try:
        return instance.fetch_snapshot()
    except ConnectorDisabledError:
        return _disabled_snapshot(instance)


def normalize_prediction_market_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    records = list(snapshot.get("records", []))
    return {
        "ok": bool(snapshot.get("ok", True)),
        "status": snapshot.get("status", "dry_run_placeholder"),
        "provider_id": snapshot.get("provider_id", "kalshi_prediction_market"),
        "provider_name": "Kalshi Prediction Market",
        "received_at": snapshot.get("timestamp") or _utc_now_iso(),
        "dry_run": bool(snapshot.get("dry_run", True)),
        "records_received": int(snapshot.get("records_received", len(records))),
        "records_valid": int(snapshot.get("records_valid", 0)),
        "records_rejected": int(snapshot.get("records_rejected", 0)),
        "rejection_reason_counts": dict(snapshot.get("rejection_reason_counts", {})),
        "http_status": snapshot.get("http_status"),
        "diagnostic": snapshot.get("diagnostic"),
        "blockers": list(snapshot.get("blockers", []))[:10],
        "records": records,
        "schema_version": SCHEMA_VERSION,
    }


def validate_prediction_market_snapshot(snapshot: dict[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
    normalized = normalize_prediction_market_snapshot(snapshot)
    errors: list[str] = []
    valid = 0
    rejected = 0
    for row in normalized.get("records", []):
        if not isinstance(row, dict):
            rejected += 1
            errors.append("malformed_record")
            continue
        verdict = validate_provider_payload(
            "prediction_market",
            row,
            max_staleness_seconds=max_staleness_seconds,
        )
        if verdict["ok"]:
            valid += 1
        else:
            rejected += 1
            errors.extend(verdict["errors"])
    return {
        "ok": len(errors) == 0,
        "status": "accepted" if len(errors) == 0 else "rejected",
        "records_valid": valid,
        "records_rejected": rejected,
        "errors": sorted(set(errors)),
    }


def write_prediction_market_snapshot(snapshot: dict[str, Any], base_data_dir: str = "data") -> str:
    base_root = _resolve_base_data_dir(base_data_dir)
    normalized = normalize_prediction_market_snapshot(snapshot)
    assert_no_secret_leak(
        {
            "source_payload_redacted": [
                row.get("source_payload_redacted")
                for row in normalized.get("records", [])
                if isinstance(row, dict)
            ]
        }
    )
    folder = base_root / "data_sources" / "provider_payload_samples"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "kalshi_prediction_market_snapshot.json"
    path.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)


def summarize_prediction_market_snapshot(snapshot: dict[str, Any], snapshot_path: str | None = None) -> dict[str, Any]:
    normalized = normalize_prediction_market_snapshot(snapshot)
    return {
        "ok": bool(normalized.get("ok", True)),
        "status": normalized.get("status", "dry_run_placeholder"),
        "provider_id": normalized.get("provider_id", "kalshi_prediction_market"),
        "provider_enabled": bool(snapshot.get("provider_enabled", False)),
        "dry_run": bool(normalized.get("dry_run", True)),
        "live_calls_enabled": bool(snapshot.get("live_calls_enabled", not bool(normalized.get("dry_run", True)))),
        "credential_status": snapshot.get("credential_status", "missing_credentials"),
        "records_received": int(normalized.get("records_received", 0)),
        "records_valid": int(normalized.get("records_valid", 0)),
        "records_rejected": int(normalized.get("records_rejected", 0)),
        "rejection_reason_counts": dict(normalized.get("rejection_reason_counts", {})),
        "http_status": normalized.get("http_status"),
        "diagnostic": normalized.get("diagnostic"),
        "blockers": list(normalized.get("blockers", []))[:10],
        "snapshot_path": snapshot_path,
    }


build_kalshi_readonly_contract = build_prediction_market_readonly_contract
build_kalshi_readonly_adapter = build_prediction_market_readonly_adapter
get_kalshi_snapshot = get_prediction_market_snapshot
normalize_kalshi_snapshot = normalize_prediction_market_snapshot
validate_kalshi_snapshot = validate_prediction_market_snapshot
write_kalshi_snapshot = write_prediction_market_snapshot
summarize_kalshi_snapshot = summarize_prediction_market_snapshot


__all__ = [
    "SCHEMA_VERSION",
    "PredictionMarketReadonlyAdapter",
    "KalshiReadonlyAdapter",
    "PREDICTION_MARKET_CONNECTOR_CONFIGURATION",
    "PREDICTION_MARKET_CONNECTOR_READINESS",
    "PREDICTION_MARKET_DISABLED_CLIENT",
    "PREDICTION_MARKET_PROVIDER_ADAPTER",
    "build_prediction_market_readonly_contract",
    "build_prediction_market_readonly_adapter",
    "get_prediction_market_snapshot",
    "normalize_prediction_market_snapshot",
    "validate_prediction_market_snapshot",
    "write_prediction_market_snapshot",
    "summarize_prediction_market_snapshot",
    "build_kalshi_readonly_contract",
    "build_kalshi_readonly_adapter",
    "get_kalshi_snapshot",
    "normalize_kalshi_snapshot",
    "validate_kalshi_snapshot",
    "write_kalshi_snapshot",
    "summarize_kalshi_snapshot",
    "enrich_with_kalshi",
    "enrich_with_prediction_market",
]
