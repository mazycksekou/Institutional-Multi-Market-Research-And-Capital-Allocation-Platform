from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from . import SCHEMA_VERSION
from automation_scheduler.scheduler_config import utc_now_iso


def write_governance_audit_record(
    *,
    model_id: str,
    action: str,
    previous_tier: str,
    new_tier: str,
    gate_results: dict[str, Any],
    decision: str,
    reason: str,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    record = {
        "id": uuid4().hex[:16],
        "created_at": utc_now_iso(),
        "model_id": model_id,
        "action": action,
        "previous_tier": previous_tier,
        "new_tier": new_tier,
        "gate_results": gate_results,
        "decision": decision,
        "reason": reason,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "schema_version": SCHEMA_VERSION,
    }
    path = Path(base_data_dir) / "governance_audit"
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{record['id']}.json"
    file_path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    record["path"] = str(file_path)
    return record

