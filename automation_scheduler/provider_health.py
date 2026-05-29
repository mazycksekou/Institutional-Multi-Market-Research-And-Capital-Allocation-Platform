from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .provider_contracts import ensure_provider_runtime_directories
from .scheduler_config import utc_now_iso


def compact_provider_health(contract: dict[str, Any], blockers: list[str] | None = None) -> dict[str, Any]:
    blocked = list(blockers or [])
    if not contract.get("enabled", False):
        blocked.append("disabled_provider")
    if not contract.get("live_calls_enabled", False):
        blocked.append("live_calls_disabled")
    if contract.get("required_credentials") and contract.get("credential_status") != "ok":
        blocked.append("missing_credentials")
    if contract.get("dry_run", True):
        blocked.append("dry_run_placeholder")
    status = "ok" if len(blocked) == 0 else "blocked"
    return {
        "provider_id": contract.get("provider_id"),
        "provider_type": contract.get("provider_type"),
        "enabled": bool(contract.get("enabled", False)),
        "live_calls_enabled": bool(contract.get("live_calls_enabled", False)),
        "dry_run": bool(contract.get("dry_run", True)),
        "status": status,
        "last_checked_at": utc_now_iso(),
        "blockers": blocked[:10],
        "rate_limit_note": contract.get("rate_limit_note", "dry_run_only"),
    }


def summarize_provider_health(contracts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    entries = [compact_provider_health(contract) for contract in contracts.values()]
    blocked_count = sum(1 for entry in entries if entry["status"] != "ok")
    return {
        "ok": True,
        "status": "ok",
        "timestamp": utc_now_iso(),
        "provider_count": len(entries),
        "enabled_provider_count": sum(1 for entry in entries if entry["enabled"]),
        "live_calls_enabled_count": sum(1 for entry in entries if entry["live_calls_enabled"]),
        "blocked_count": blocked_count,
        "dry_run": True,
        "blockers": sorted({reason for entry in entries for reason in entry["blockers"]})[:10],
        "top_provider_statuses": entries[:10],
    }


def write_provider_health_snapshot(contracts: dict[str, dict[str, Any]], base_data_dir: str = "data") -> str:
    paths = ensure_provider_runtime_directories(base_data_dir)
    snapshot = summarize_provider_health(contracts)
    path = Path(paths["provider_health"]) / "provider_health.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)

