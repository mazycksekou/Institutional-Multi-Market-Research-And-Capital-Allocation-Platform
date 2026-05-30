from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import get_runtime_data_path
from .scheduler_config import sanitize_filename, utc_now_iso


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_historical_rows(path: str) -> list[dict[str, Any]]:
    if "://" in str(path):
        raise ValueError("historical replay supports local JSON rows only")
    file_path = Path(path)
    if not file_path.exists():
        return []
    if file_path.suffix.lower() != ".json":
        raise ValueError("historical replay expects a local JSON file")
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("historical replay JSON must be a list of rows")
    return payload


def replay_rows(rows: list[dict[str, Any]], model_id: str = "unknown_model") -> dict[str, Any]:
    replay_items: list[dict[str, Any]] = []
    for row in rows:
        replay_items.append(
            {
                "event_id": row.get("event_id"),
                "market_type": row.get("market_type"),
                "event_name": row.get("event_name"),
                "market_name": row.get("market_name"),
                "selection_name": row.get("selection_name"),
                "recommended_odds": row.get("odds"),
                "closing_odds": row.get("closing_odds"),
                "model_probability": _to_float(row.get("model_probability")),
                "result_status": row.get("result_status", "pending"),
                "timestamp": row.get("timestamp") or utc_now_iso(),
                "model_id": model_id,
            }
        )
    return {
        "model_id": model_id,
        "replayed_at": utc_now_iso(),
        "sample_size": len(replay_items),
        "rows": replay_items,
    }


def write_replay_result(result: dict[str, Any], base_dir: str = "data/backtests") -> str:
    normalized = str(base_dir).replace("\\", "/").rstrip("/")
    directory = get_runtime_data_path("backtests") if normalized == "data/backtests" else Path(base_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model_id = sanitize_filename(str(result.get("model_id") or "unknown_model"))
    replay_id = sanitize_filename(str(result.get("replayed_at") or utc_now_iso()))
    path = directory / f"replay_{model_id}_{replay_id}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)


def summarize_replay_result(result: dict[str, Any]) -> dict[str, Any]:
    rows = list(result.get("rows") or [])
    settled = [row for row in rows if str(row.get("result_status")).lower() in {"win", "loss", "push"}]
    return {
        "model_id": result.get("model_id"),
        "sample_size": len(rows),
        "settled_count": len(settled),
        "status": "backtest_complete" if rows else "needs_more_sample",
    }
