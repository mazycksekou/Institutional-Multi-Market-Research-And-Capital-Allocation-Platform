from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import resolve_base_data_dir
from .kalshi_readonly_adapter import SCHEMA_VERSION, KalshiReadonlyAdapter
from .provider_payload_validator import validate_provider_payload
from .provider_secret_policy import assert_no_secret_leak
from .scheduler_config import utc_now_iso


def get_kalshi_snapshot(adapter: KalshiReadonlyAdapter | None = None) -> dict[str, Any]:
    instance = adapter or KalshiReadonlyAdapter()
    return instance.fetch_snapshot()


def normalize_kalshi_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    records = list(snapshot.get("records", []))
    return {
        "ok": bool(snapshot.get("ok", True)),
        "status": snapshot.get("status", "dry_run_placeholder"),
        "provider_id": snapshot.get("provider_id", "kalshi_prediction_market"),
        "provider_name": "Kalshi Prediction Market",
        "received_at": snapshot.get("timestamp") or utc_now_iso(),
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


def validate_kalshi_snapshot(snapshot: dict[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
    normalized = normalize_kalshi_snapshot(snapshot)
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


def write_kalshi_snapshot(snapshot: dict[str, Any], base_data_dir: str = "data") -> str:
    base_root = resolve_base_data_dir(base_data_dir)
    normalized = normalize_kalshi_snapshot(snapshot)
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


def summarize_kalshi_snapshot(snapshot: dict[str, Any], snapshot_path: str | None = None) -> dict[str, Any]:
    normalized = normalize_kalshi_snapshot(snapshot)
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
