from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def create_lineage_record(**kwargs: Any) -> dict[str, Any]:
    record = dict(kwargs)
    record.setdefault("received_at", datetime.now(timezone.utc).isoformat())
    record.setdefault("normalized_at", datetime.now(timezone.utc).isoformat())
    for key in list(record.keys()):
        if "secret" in key.lower() or "api_key" in key.lower() or "token" in key.lower():
            record[key] = "[REDACTED]"
    return record
