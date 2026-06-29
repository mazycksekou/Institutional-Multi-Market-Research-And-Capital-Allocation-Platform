from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def create_lineage_record(**kwargs: Any) -> dict[str, Any]:
    record = dict(kwargs)
    record.setdefault("received_at", datetime.now(timezone.utc).isoformat())
    record.setdefault("normalized_at", datetime.now(timezone.utc).isoformat())
    record.setdefault("provider_id", "unknown_provider")
    record.setdefault("provider_type", "unknown_provider_type")
    record.setdefault("payload_schema_version", "unknown")
    record.setdefault("stale_status", "unknown")
    record.setdefault("validation_status", "unknown")
    record.setdefault("settlement_rule_status", "unknown")
    record.setdefault("redaction_status", "applied")
    record.setdefault("snapshot_id", "unknown_snapshot")
    record.setdefault("source_type", record.get("provider_type", "unknown_provider_type"))
    record.setdefault("schema_version", "model_governance.data_lineage.v1")
    if record.get("provider_id") == "sharp_sportsbook":
        if record.get("provider_type") in {"unknown_provider_type", "", None}:
            record["provider_type"] = "sportsbook_odds"
    if record.get("provider_id") == "kalshi_prediction_market":
        if record.get("provider_type") in {"unknown_provider_type", "", None}:
            record["provider_type"] = "prediction_market"
        record["source_type"] = "prediction_market"
    for key in list(record.keys()):
        if "secret" in key.lower() or "api_key" in key.lower() or "token" in key.lower():
            record[key] = "[REDACTED]"
    return record
