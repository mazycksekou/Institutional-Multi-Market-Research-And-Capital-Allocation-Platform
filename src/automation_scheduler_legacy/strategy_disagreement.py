from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .data_paths import resolve_base_data_dir
from .scheduler_config import hash_payload, safe_run_id, utc_now_iso
from .secret_safety import redact_sensitive, secret_safety_fields
from .security_policy import locked_safety_flags


SCHEMA_VERSION = "automation_scheduler.v1.strategy_disagreement.v1"


def _queue_path(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "strategy" / "disagreements" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = payload.get("items") if isinstance(payload, dict) else payload
    return [dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def build_strategy_disagreement_record(
    *,
    candidate: Mapping[str, Any] | None = None,
    candidate_id: str | None = None,
    asset_type: str | None = None,
    market_type: str | None = None,
    provider: str | None = None,
    strategy_a: str | None = None,
    strategy_b: str | None = None,
    core_model_action: str | None = None,
    strategy_action: str | None = None,
    disagreement_type: str = "strategy_conflict",
    disagreement_reasons: list[str] | None = None,
    calibration_bucket: str | None = None,
    manifold_cluster_id: str | None = None,
    strategy_ids: list[str] | None = None,
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    created_at = utc_now_iso()
    cid = candidate_id or safe_candidate.get("candidate_id") or safe_candidate.get("id") or safe_candidate.get("ticker") or "unknown"
    ids = [str(item) for item in (strategy_ids or [strategy_a, strategy_b]) if item]
    seed = "|".join([str(cid), ",".join(ids), str(disagreement_type), created_at, hash_payload(disagreement_reasons or [])[:16]])
    record = {
        "disagreement_id": f"strategy_disagreement_{safe_run_id('strategy_disagreement', seed)}",
        "candidate_id": cid,
        "asset_type": asset_type or safe_candidate.get("asset_type") or safe_candidate.get("asset_class"),
        "market_type": market_type or safe_candidate.get("market_type") or safe_candidate.get("source_type"),
        "provider": provider or safe_candidate.get("provider") or safe_candidate.get("provider_id"),
        "core_model_action": core_model_action,
        "strategy_action": strategy_action,
        "strategy_a": strategy_a,
        "strategy_b": strategy_b,
        "disagreement_type": disagreement_type,
        "disagreement_reasons": list(disagreement_reasons or [])[:20],
        "calibration_bucket": calibration_bucket or safe_candidate.get("calibration_bucket"),
        "manifold_cluster_id": manifold_cluster_id or safe_candidate.get("manifold_cluster_id"),
        "strategy_ids": ids[:20],
        "created_at": created_at,
        "redacted": True,
        **secret_safety_fields(source_payload=candidate, redacted_payload=safe_candidate),
        **locked_safety_flags(),
    }
    record["execution_allowed"] = False
    record["provider_write"] = False
    record["live_execution_enabled"] = False
    return record


def append_strategy_disagreement(record: Mapping[str, Any], *, base_data_dir: str | None = None, limit: int = 500) -> dict[str, Any]:
    safe_record = redact_sensitive(dict(record))
    safe_record.update(locked_safety_flags())
    safe_record["redacted"] = True
    path = _queue_path(base_data_dir)
    items = _read_items(path)
    items.append(safe_record)
    cap = max(1, min(int(limit or 500), 5000))
    items = sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)[:cap]
    wrapper = {
        "ok": True,
        "status": "ok",
        "schema_version": SCHEMA_VERSION,
        "count": len(items),
        "items": items,
        "redacted": True,
        **locked_safety_flags(),
    }
    _atomic_write(path, wrapper)
    return {
        "ok": True,
        "status": "strategy_disagreement_record_written",
        "disagreement_id": safe_record.get("disagreement_id"),
        "count": len(items),
        "record": safe_record,
        **locked_safety_flags(),
    }


def load_strategy_disagreements(*, base_data_dir: str | None = None, limit: int = 100) -> dict[str, Any]:
    items = _read_items(_queue_path(base_data_dir))
    cap = max(1, min(int(limit or 100), 500))
    return {
        "ok": True,
        "status": "ok",
        "schema_version": SCHEMA_VERSION,
        "count": min(len(items), cap),
        "total_count": len(items),
        "items": sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)[:cap],
        "redacted": True,
        **locked_safety_flags(),
    }
