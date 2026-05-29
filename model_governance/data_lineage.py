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
    record.setdefault("redaction_status", "applied")
    for key in list(record.keys()):
        if "secret" in key.lower() or "api_key" in key.lower() or "token" in key.lower():
            record[key] = "[REDACTED]"
    return record
