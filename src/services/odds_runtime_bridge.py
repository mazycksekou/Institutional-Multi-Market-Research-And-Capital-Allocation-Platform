from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.connectors.errors import ConnectorDisabledError
from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from src.providers.policy.secret_policy import assert_no_secret_leak
from src.providers.sportsbooks.adapters import normalize_sportsbook_quote as _normalize_sportsbook_quote
from src.providers.sportsbooks.contracts import validate_sportsbook_payload
from src.core.entity_resolver import normalize_ticket_fields


SCHEMA_VERSION = "src.services.odds_runtime_bridge.v1"

ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"bridge_module": "src.services.odds_runtime_bridge"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enrich_with_sharp(ticket: dict[str, Any]) -> dict[str, Any]:
    normalized_ticket = normalize_ticket_fields(ticket)
    return {
        "provider": "sharp",
        "provider_status": "disabled",
        "message": "Sharp live odds access has been retired in favor of the connector boundary.",
        "provider_notes": [
            "Sharp live odds access has been retired in favor of the connector boundary.",
            "Legacy compatibility shell returns metadata only.",
        ],
        "connector_configuration": dict(ODDS_DATA_CONNECTOR_CONFIGURATION.describe()),
        "connector_readiness": dict(ODDS_DATA_CONNECTOR_READINESS),
        "ticket_fields": normalized_ticket,
    }


@dataclass
class SharpSportsbookAdapter:
    contract: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.contract = dict(self.contract or {})
        self.provider_id = "sharp_sportsbook"
        self.provider_name = "Sharp Sportsbook"
        self.provider_type = "sportsbook_odds"
        self.connector_configuration = dict(ODDS_DATA_CONNECTOR_CONFIGURATION.describe())
        self.connector_readiness = dict(ODDS_DATA_CONNECTOR_READINESS)

    def build_sharp_url(self, path_name: str) -> dict[str, Any]:
        return {
            "provider": self.provider_id,
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
            "supports_polling": False,
            "supports_streaming": False,
            "required_credentials": ["ODDS_DATA_API_KEY", "ODDS_DATA_API_SECRET"],
            "supported_markets": ["h2h", "spreads", "totals"],
            "read_only_mode": True,
            "enabled": False,
            "live_calls_enabled": False,
            "provider_live_calls_enabled": False,
            "dry_run": True,
        }

    def validate_config(self) -> dict[str, Any]:
        dry_run = bool(self.contract.get("dry_run", True))
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
            "dry_run": dry_run,
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
            "timestamp": _utc_now_iso(),
            "connector_configuration": self.connector_configuration,
            "connector_readiness": self.connector_readiness,
        }

    def _disabled(self, message: str) -> None:
        raise ConnectorDisabledError(message)

    def fetch_events(self) -> dict[str, Any]:
        self._disabled("Sharp sportsbook access is disabled; use src.connectors.odds_data metadata only")

    def fetch_odds(self) -> dict[str, Any]:
        self._disabled("Sharp sportsbook access is disabled; use src.connectors.odds_data metadata only")

    def fetch_player_props(self) -> dict[str, Any]:
        self._disabled("Sharp sportsbook access is disabled; use src.connectors.odds_data metadata only")

    def fetch_sports(self) -> dict[str, Any]:
        self._disabled("Sharp sportsbook access is disabled; use src.connectors.odds_data metadata only")

    def normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _normalize_sportsbook_quote(payload, provider="sharp_sportsbook")

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_sportsbook_payload(payload)

    def fetch_snapshot(self) -> dict[str, Any]:
        cfg = self.validate_config()
        return {
            "ok": True,
            "status": "provider_disabled",
            "provider_id": self.provider_id,
            "provider_enabled": bool(cfg["provider_enabled"]),
            "live_calls_enabled": bool(cfg["live_calls_enabled"]),
            "credential_status": cfg["credential_status"],
            "dry_run": True,
            "records": [],
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "rejection_reason_counts": {},
            "http_status": None,
            "diagnostic": {
                "bridge_module": "src.services.odds_runtime_bridge",
                "connector_configuration": self.connector_configuration,
                "connector_readiness": self.connector_readiness,
            },
            "blockers": cfg["blockers"][:10],
            "timestamp": _utc_now_iso(),
            "connector_configuration": self.connector_configuration,
            "connector_readiness": self.connector_readiness,
        }


def get_sportsbook_snapshot(adapter: SharpSportsbookAdapter | None = None) -> dict[str, Any]:
    instance = adapter or SharpSportsbookAdapter()
    return instance.fetch_snapshot()


def normalize_sportsbook_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    records = [row for row in snapshot.get("records", []) if isinstance(row, dict)]
    normalized_records = [_normalize_sportsbook_quote(row, provider="sharp_sportsbook") for row in records]
    return {
        "ok": bool(snapshot.get("ok", True)),
        "status": snapshot.get("status", "dry_run_placeholder"),
        "provider_id": snapshot.get("provider_id", "sharp_sportsbook"),
        "provider_name": "Sharp Sportsbook",
        "received_at": snapshot.get("timestamp") or _utc_now_iso(),
        "dry_run": bool(snapshot.get("dry_run", True)),
        "records_received": int(snapshot.get("records_received", len(normalized_records))),
        "records_valid": int(snapshot.get("records_valid", len(normalized_records))),
        "records_rejected": int(snapshot.get("records_rejected", 0)),
        "rejection_reason_counts": dict(snapshot.get("rejection_reason_counts", {})),
        "http_status": snapshot.get("http_status"),
        "diagnostic": snapshot.get("diagnostic"),
        "blockers": list(snapshot.get("blockers", []))[:10],
        "records": normalized_records,
        "internal_debug_summary": snapshot.get("internal_debug_summary"),
        "schema_version": SCHEMA_VERSION,
        "connector_configuration": snapshot.get("connector_configuration", ODDS_DATA_CONNECTOR_CONFIGURATION.describe()),
        "connector_readiness": snapshot.get("connector_readiness", ODDS_DATA_CONNECTOR_READINESS),
    }


def validate_sportsbook_snapshot(snapshot: dict[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
    normalized = normalize_sportsbook_snapshot(snapshot)
    errors: list[str] = []
    valid = 0
    rejected = 0
    for row in normalized.get("records", []):
        if not isinstance(row, dict):
            rejected += 1
            errors.append("malformed_record")
            continue
        verdict = validate_sportsbook_payload(row, max_staleness_seconds=max_staleness_seconds)
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


def get_valid_normalized_records(snapshot: dict[str, Any], max_staleness_seconds: int = 3600 * 12) -> list[dict[str, Any]]:
    normalized = normalize_sportsbook_snapshot(snapshot)
    valid_rows: list[dict[str, Any]] = []
    for row in normalized.get("records", []):
        if not isinstance(row, dict):
            continue
        verdict = validate_sportsbook_payload(row, max_staleness_seconds=max_staleness_seconds)
        if verdict["ok"]:
            valid_rows.append(row)
    return valid_rows


def write_sportsbook_snapshot(snapshot: dict[str, Any], base_data_dir: str = "data") -> str:
    base_root = Path(base_data_dir)
    normalized = normalize_sportsbook_snapshot(snapshot)
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
    path = folder / "sharp_sportsbook_snapshot.json"
    path.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)


def summarize_sportsbook_snapshot(snapshot: dict[str, Any], snapshot_path: str | None = None) -> dict[str, Any]:
    normalized = normalize_sportsbook_snapshot(snapshot)
    return {
        "ok": bool(normalized.get("ok", True)),
        "status": normalized.get("status", "dry_run_placeholder"),
        "provider_id": normalized.get("provider_id", "sharp_sportsbook"),
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
        "internal_debug_summary": normalized.get("internal_debug_summary"),
        "connector_configuration": normalized.get("connector_configuration"),
        "connector_readiness": normalized.get("connector_readiness"),
    }


__all__ = [
    "SCHEMA_VERSION",
    "SharpSportsbookAdapter",
    "ODDS_DATA_CONNECTOR_CONFIGURATION",
    "ODDS_DATA_CONNECTOR_READINESS",
    "enrich_with_sharp",
    "get_sportsbook_snapshot",
    "get_valid_normalized_records",
    "normalize_sportsbook_snapshot",
    "summarize_sportsbook_snapshot",
    "validate_sportsbook_snapshot",
    "write_sportsbook_snapshot",
]
