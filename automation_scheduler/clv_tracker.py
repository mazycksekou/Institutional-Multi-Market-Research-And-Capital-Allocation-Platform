from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .scheduler_config import SCHEMA_VERSION, redact_secrets, sanitize_filename, utc_now_iso


def calculate_clv(opening_odds: Any, current_odds: Any, closing_odds: Any | None = None) -> dict[str, float]:
    opening = float(opening_odds)
    current = float(current_odds)
    closing = float(closing_odds if closing_odds is not None else current_odds)
    return {
        "opening_to_current": round(current - opening, 4),
        "opening_to_closing": round(closing - opening, 4),
        "current_to_closing": round(closing - current, 4),
    }


def build_clv_record(payload: dict[str, Any]) -> dict[str, Any]:
    odds_delta = calculate_clv(payload.get("opening_odds"), payload.get("current_odds"), payload.get("closing_odds"))
    return {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        "candidate_type": "clv_watch",
        "event": payload.get("event"),
        "market": payload.get("market"),
        "selection": payload.get("selection"),
        "opening_odds": payload.get("opening_odds"),
        "current_odds": payload.get("current_odds"),
        "closing_odds": payload.get("closing_odds"),
        "clv": odds_delta,
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }


def write_clv_record(payload: dict[str, Any], *, base_dir: str = "data/reports") -> dict[str, Any]:
    record = build_clv_record(payload)
    directory = Path(base_dir)
    directory.mkdir(parents=True, exist_ok=True)
    name = sanitize_filename(f"clv_{payload.get('event', 'event')}_{payload.get('selection', 'selection')}")
    path = directory / f"{name}.json"
    path.write_text(json.dumps(redact_secrets(record), indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "record": record}
