from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .data_paths import resolve_base_data_dir
from .scheduler_config import hash_payload, safe_run_id, utc_now_iso
from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import locked_safety_flags
from .strategy_context_buckets import build_context_bucket


SCHEMA_VERSION = "automation_scheduler.v1.strategy_performance_ledger.v1"


def _ledger_path(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "strategy" / "performance_ledger.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = payload.get("items") if isinstance(payload, dict) else payload
    return [dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def append_strategy_performance_record(record: Mapping[str, Any], *, base_data_dir: str | None = None, limit: int = 5000) -> dict[str, Any]:
    safe = redact_sensitive(dict(record))
    now = utc_now_iso()
    strategy_id = str(safe.get("strategy_id") or "unknown")
    candidate_id = str(safe.get("candidate_id") or safe.get("ticker") or "unknown")
    item = {
        "ledger_id": safe.get("ledger_id") or f"strategy_perf_{safe_run_id('strategy_perf', strategy_id + candidate_id + now + hash_payload(safe)[:16])}",
        "strategy_id": strategy_id,
        "candidate_id": candidate_id,
        "asset_type": safe.get("asset_type"),
        "market_type": safe.get("market_type"),
        "provider": safe.get("provider"),
        "context_bucket": build_context_bucket(safe),
        "outcome_status": safe.get("outcome_status"),
        "expected_value": safe.get("expected_value"),
        "average_return": safe.get("average_return") or safe.get("return"),
        "average_closing_line_value": safe.get("average_closing_line_value") or safe.get("clv"),
        "false_positive": bool(safe.get("false_positive", False)),
        "false_negative": bool(safe.get("false_negative", False)),
        "settled_at": safe.get("settled_at"),
        "created_at": now,
        "redacted": True,
        **secret_safety_fields(source_payload=record, redacted_payload=safe),
        **locked_safety_flags(),
    }
    path = _ledger_path(base_data_dir)
    items = _read_records(path)
    items.append(item)
    cap = max(1, min(int(limit or 5000), 20000))
    items = sorted(items, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:cap]
    wrapper = {"ok": True, "status": "ok", "schema_version": SCHEMA_VERSION, "count": len(items), "items": items, **locked_safety_flags()}
    _write(path, wrapper)
    return {"ok": True, "status": "strategy_performance_record_written", "ledger_id": item["ledger_id"], "record": item, **locked_safety_flags()}


def load_strategy_performance_ledger(*, base_data_dir: str | None = None, limit: int = 500) -> dict[str, Any]:
    items = _read_records(_ledger_path(base_data_dir))
    cap = max(1, min(int(limit or 500), 5000))
    return {
        "ok": True,
        "status": "ok",
        "schema_version": SCHEMA_VERSION,
        "total_count": len(items),
        "count": min(len(items), cap),
        "items": items[:cap],
        "redacted": True,
        **locked_safety_flags(),
    }


def summarize_strategy_performance(records: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    rows = [dict(row) for row in (records or []) if isinstance(row, Mapping)]
    by_strategy: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = str(row.get("strategy_id") or "unknown")
        bucket = by_strategy.setdefault(sid, {"strategy_id": sid, "sample_size": 0, "false_positive_count": 0, "expected_value_sum": 0.0})
        bucket["sample_size"] += 1
        bucket["false_positive_count"] += 1 if bool(row.get("false_positive")) else 0
        try:
            bucket["expected_value_sum"] += float(row.get("expected_value") or 0.0)
        except (TypeError, ValueError):
            pass
    summaries = []
    for item in by_strategy.values():
        sample = max(1, int(item["sample_size"]))
        summaries.append(
            {
                "strategy_id": item["strategy_id"],
                "sample_size": item["sample_size"],
                "false_positive_rate": item["false_positive_count"] / sample,
                "expected_value": item["expected_value_sum"] / sample,
            }
        )
    return {"ok": True, "status": "strategy_performance_summary", "total_records": len(rows), "strategies": summaries, **locked_safety_flags()}
