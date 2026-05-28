from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..scheduler_config import SCHEMA_VERSION, redact_secrets, utc_now_iso


def _execution_audit_path(base_data_dir: str | None = None) -> Path:
    root = Path(base_data_dir or "data") / "audit_log"
    root.mkdir(parents=True, exist_ok=True)
    return root / "execution_audit_log.json"


def read_execution_audit_records(base_data_dir: str | None = None) -> list[dict[str, Any]]:
    path = _execution_audit_path(base_data_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append_execution_audit_record(record: dict[str, Any], *, base_data_dir: str | None = None) -> dict[str, Any]:
    records = read_execution_audit_records(base_data_dir)
    wrapped = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        "mode": "paper_or_dry_run_only",
        "record": redact_secrets(record),
    }
    records.append(wrapped)
    _execution_audit_path(base_data_dir).write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    return wrapped
