from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


def create_run_context(config: dict[str, Any], governance_status: str = "ok", approval_status: str = "pending") -> dict[str, Any]:
    return {
        "run_id": f"run_{uuid.uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": bool(config.get("dry_run", True)),
        "config_summary": {
            "paper_execution_only": bool(config.get("paper_execution_only", True)),
            "roi_target_is_filter_only": bool(config.get("roi_target_is_filter_only", True)),
        },
        "governance_status": governance_status,
        "human_approval_status": approval_status,
    }
