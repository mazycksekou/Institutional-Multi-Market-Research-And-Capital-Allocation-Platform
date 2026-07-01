from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.services.scheduler_config import ROI_TARGET_DISCLAIMER, SCHEMA_VERSION, redact_secrets, sanitize_filename, utc_now_iso


def write_report(config: dict[str, Any], *, report_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    report_dir = Path(config["paths"]["reports"])
    report_dir.mkdir(parents=True, exist_ok=True)
    wrapper = {
        "schema_version": SCHEMA_VERSION,
        "written_at": utc_now_iso(),
        "report_name": report_name,
        "dry_run": config["dry_run"],
        "human_approval_required": config["human_approval_required"],
        "paper_execution_only": config["paper_execution_only"],
        "roi_target_percent": config["roi_target_percent"],
        "roi_target_disclaimer": ROI_TARGET_DISCLAIMER,
        "auto_execution_enabled": config["auto_execution_enabled"],
        "auto_bet_enabled": config["auto_bet_enabled"],
        "auto_trade_enabled": config["auto_trade_enabled"],
        "governance_layer": "model_governance.v1",
        "payload": redact_secrets(payload),
    }
    path = report_dir / f"{sanitize_filename(report_name)}.json"
    path.write_text(json.dumps(wrapper, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "report_name": report_name, "schema_version": SCHEMA_VERSION}


def write_compact_report(config: dict[str, Any], *, report_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    compact = redact_secrets(payload)
    path_meta = write_report(config, report_name=report_name, payload=compact)
    return {"path": path_meta["path"], "report_name": report_name, "schema_version": SCHEMA_VERSION}
