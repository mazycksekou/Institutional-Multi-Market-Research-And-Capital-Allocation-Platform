from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_governance_audit_record(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out.setdefault("schema_version", "model_governance.v1")
    out.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    path = Path("data/governance_audit")
    path.mkdir(parents=True, exist_ok=True)
    rid = out.get("id") or f"audit_{int(datetime.now(timezone.utc).timestamp())}"
    out["id"] = rid
    (path / f"{rid}.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    return out
