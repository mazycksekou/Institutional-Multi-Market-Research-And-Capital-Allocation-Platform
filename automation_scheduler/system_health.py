from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .review_queue import load_review_queue
from .scheduler_config import SCHEMA_VERSION, utc_now_iso


def get_system_health(config: dict[str, Any]) -> dict[str, Any]:
    review_items = load_review_queue(config)
    path_status = {name: Path(path).exists() for name, path in config["paths"].items()}
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "checked_at": utc_now_iso(),
        "dry_run": config["dry_run"],
        "human_approval_required": config["human_approval_required"],
        "auto_bet_enabled": config["auto_bet_enabled"],
        "auto_trade_enabled": config["auto_trade_enabled"],
        "auto_execution_enabled": config["auto_execution_enabled"],
        "paper_execution_only": config["paper_execution_only"],
        "alert_only_mode": config["alert_only_mode"],
        "paths_ready": path_status,
        "review_queue_count": len(review_items),
        "provider_count": len(config["providers"]),
    }


def write_system_health(config: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    health = get_system_health(config)
    if extra:
        health["extra"] = extra
    path = Path(config["paths"]["system_health"]) / "health.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(health, indent=2, sort_keys=True), encoding="utf-8")
    return health
