from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_governance.model_inventory import inventory_counts
from .review_queue import load_review_queue
from .scheduler_config import SCHEMA_VERSION, utc_now_iso


def get_system_health(config: dict[str, Any]) -> dict[str, Any]:
    review_items = load_review_queue(config)
    path_status = {name: Path(path).exists() for name, path in config["paths"].items()}
    governance_path = Path("data") / "governance_audit"
    inventory = inventory_counts()
    models_blocked_due_to_missing_inputs = 0
    models_blocked_due_to_stale_data = 0
    models_blocked_due_to_calibration = 0
    models_blocked_due_to_risk = 0
    models_blocked_due_to_settlement = 0
    models_blocked_due_to_Kelly = 0
    for item in review_items:
        input_gate = item.get("input_quality_gate_result") or {}
        calibration_gate = item.get("calibration_gate_result") or {}
        risk_gate = item.get("risk_gate_result") or {}
        blockers = set(item.get("blockers") or [])
        if input_gate.get("missing_inputs") or "missing_inputs" in blockers:
            models_blocked_due_to_missing_inputs += 1
        if item.get("stale_data_risk") or "stale_data" in blockers:
            models_blocked_due_to_stale_data += 1
        if calibration_gate and not calibration_gate.get("passes_gate", True):
            models_blocked_due_to_calibration += 1
        if risk_gate and not risk_gate.get("passes_gate", True):
            models_blocked_due_to_risk += 1
        if str(item.get("settlement_liquidity_gate_result", "")).startswith("blocked"):
            models_blocked_due_to_settlement += 1
        if str(item.get("kelly_gate_result", "")).startswith("blocked"):
            models_blocked_due_to_Kelly += 1
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
        "cross_book_engine_enabled": True,
        "paths_ready": path_status,
        "review_queue_count": len(review_items),
        "provider_count": len(config["providers"]),
        **inventory,
        "governance_audit_status": "ready" if governance_path.exists() else "not_written",
        "models_blocked_due_to_missing_inputs": models_blocked_due_to_missing_inputs,
        "models_blocked_due_to_stale_data": models_blocked_due_to_stale_data,
        "models_blocked_due_to_calibration": models_blocked_due_to_calibration,
        "models_blocked_due_to_risk": models_blocked_due_to_risk,
        "models_blocked_due_to_settlement": models_blocked_due_to_settlement,
        "models_blocked_due_to_Kelly": models_blocked_due_to_Kelly,
    }


def write_system_health(config: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    health = get_system_health(config)
    if extra:
        health["extra"] = extra
    path = Path(config["paths"]["system_health"]) / "health.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(health, indent=2, sort_keys=True), encoding="utf-8")
    return health
