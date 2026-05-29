from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .scheduler_config import SCHEMA_VERSION, utc_now_iso

LEDGER_SCHEMA_VERSION = f"{SCHEMA_VERSION}.paper_decision_ledger.v1"


def _ledger_path(base_data_dir: str = "data") -> Path:
    folder = Path(base_data_dir) / "paper_ledger"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "paper_decisions.json"


def load_paper_decisions(base_data_dir: str = "data") -> list[dict[str, Any]]:
    path = _ledger_path(base_data_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_paper_decisions(items: list[dict[str, Any]], base_data_dir: str = "data") -> None:
    path = _ledger_path(base_data_dir)
    path.write_text(json.dumps(items, indent=2, sort_keys=True), encoding="utf-8")


def create_paper_decision_record(candidate: dict[str, Any], *, snapshot_id: str | None = None, report_path: str | None = None, base_data_dir: str = "data") -> dict[str, Any]:
    now = utc_now_iso()
    decision = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "decision_id": str(candidate.get("id") or candidate.get("decision_id") or f"decision_{hash(str(candidate)) & 0xFFFFFFFF:08x}"),
        "provider": candidate.get("provider_id", candidate.get("provider", "unknown")),
        "source_type": candidate.get("source_type", candidate.get("market_type", "unknown")),
        "market_type": candidate.get("market_type", "unknown"),
        "ticker": candidate.get("ticker"),
        "contract_id": candidate.get("contract_id"),
        "event": candidate.get("event_name") or candidate.get("event_title"),
        "title": candidate.get("contract_title"),
        "observed_price": candidate.get("yes_price"),
        "price_source": candidate.get("price_source"),
        "implied_probability": candidate.get("implied_probability"),
        "recommendation_status": candidate.get("recommendation_status", "review_only"),
        "review_priority_score": candidate.get("review_priority_score"),
        "confidence_score": candidate.get("confidence_score"),
        "risk_score": candidate.get("risk_score"),
        "reason_codes": list(candidate.get("reason_codes") or []),
        "created_at": now,
        "snapshot_id": snapshot_id,
        "report_path": report_path,
        "execution_allowed": False,
        "paper_only": True,
        "settled_at": None,
        "settlement_status": None,
        "final_outcome": None,
        "paper_result": None,
        "paper_roi_estimate": None,
        "calibration_bucket": None,
    }
    existing = load_paper_decisions(base_data_dir)
    existing.append(decision)
    _save_paper_decisions(existing, base_data_dir)
    return decision
