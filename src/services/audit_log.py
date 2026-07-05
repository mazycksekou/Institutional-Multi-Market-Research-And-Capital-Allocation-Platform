from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.services.scheduler_config import SCHEMA_VERSION, redact_secrets, utc_now_iso


def _audit_log_path(config: dict[str, Any]) -> Path:
    path = Path(config["paths"]["audit_log"]) / "audit_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_audit_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    path = _audit_log_path(config)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append_audit_record(config: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    path = _audit_log_path(config)
    records = read_audit_records(config)
    wrapped = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        "record": redact_secrets(record),
    }
    records.append(wrapped)
    path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    return wrapped
