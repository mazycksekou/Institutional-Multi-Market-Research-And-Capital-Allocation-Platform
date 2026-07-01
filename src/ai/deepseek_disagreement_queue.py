from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.data.data_paths import get_storage_health, resolve_base_data_dir
from .deepseek_response_validator import compact_redacted_for_deepseek, profit_lab_safety_flags
from src.services.scheduler_config import SCHEMA_VERSION, safe_run_id, sanitize_filename, utc_now_iso


DISAGREEMENT_SCHEMA_VERSION = f"{SCHEMA_VERSION}.deepseek_profit_lab.disagreement_queue.v1"

REVIEW_ACTION_ALIASES = {
    "ACTIVE_REVIEW": {"ACTIVE_REVIEW", "URGENT_REVIEW", "REVIEW_REQUIRED", "NEEDS_HUMAN_REVIEW"},
    "WATCHLIST_REVIEW": {"WATCHLIST_REVIEW", "WATCH_RECHECK", "RECHECK_LATER"},
    "LOW_PRIORITY_REVIEW": {"LOW_PRIORITY_REVIEW", "CONTINUE_COLLECTING"},
    "DATA_INSUFFICIENT": {"DATA_INSUFFICIENT", "INSUFFICIENT_SAMPLE", "INSUFFICIENT_DATA"},
    "NO_BET": {"NO_BET", "NO_ACTION"},
    "NO_TRADE": {"NO_TRADE", "NO_ACTION"},
    "NO_REVIEW": {"NO_REVIEW", "NO_ACTION"},
}


def _queue_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "deepseek_profit_lab" / "disagreements"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _queue_dir(base_data_dir) / "latest.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _candidate_id(candidate: Mapping[str, Any]) -> str:
    return str(
        candidate.get("candidate_id")
        or candidate.get("id")
        or candidate.get("review_item_id")
        or candidate.get("contract_id")
        or candidate.get("ticker")
        or candidate.get("asset_symbol")
        or "unknown"
    )[:120]


def _core_action(candidate: Mapping[str, Any], explicit_action: str | None = None) -> str:
    return str(
        explicit_action
        or candidate.get("core_model_action")
        or candidate.get("recommended_action")
        or candidate.get("queue_status")
        or candidate.get("recommendation_status")
        or "unknown"
    ).strip().upper()


def _actions_equivalent(core_action: str, deepseek_action: str) -> bool:
    core = str(core_action or "").strip().upper()
    deepseek = str(deepseek_action or "").strip().upper()
    if not core or core == "UNKNOWN":
        return True
    if core == deepseek:
        return True
    return core in REVIEW_ACTION_ALIASES.get(deepseek, set())


def should_record_disagreement(
    candidate: Mapping[str, Any],
    review: Mapping[str, Any],
    *,
    core_model_action: str | None = None,
) -> bool:
    if review.get("agreement_with_core_model") is False:
        return True
    core = _core_action(candidate, core_model_action)
    deepseek = str(review.get("recommended_action") or "").strip().upper()
    return bool(deepseek and not _actions_equivalent(core, deepseek))


def build_disagreement_record(
    candidate: Mapping[str, Any],
    review: Mapping[str, Any],
    *,
    core_model_action: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    created = created_at or utc_now_iso()
    candidate_id = _candidate_id(candidate)
    core = _core_action(candidate, core_model_action)
    deepseek = str(review.get("recommended_action") or "UNKNOWN").strip().upper()
    reasons = list(review.get("disagreement_reasons") or [])
    if not reasons and not _actions_equivalent(core, deepseek):
        reasons = [f"core_model_action={core};deepseek_action={deepseek}"]
    record = {
        "schema_version": DISAGREEMENT_SCHEMA_VERSION,
        "disagreement_id": f"deepseek_disagreement_{safe_run_id('deepseek_disagreement', candidate_id + core + deepseek + created)}",
        "candidate_id": candidate_id,
        "asset_type": str(candidate.get("asset_type") or candidate.get("asset_class") or review.get("asset_type") or "unknown")[:80],
        "market_type": str(candidate.get("market_type") or review.get("market_type") or "unknown")[:120],
        "provider": str(candidate.get("provider") or candidate.get("provider_id") or "unknown")[:120],
        "core_model_action": core,
        "deepseek_action": deepseek,
        "disagreement_type": "action_disagreement" if not _actions_equivalent(core, deepseek) else "model_risk_disagreement",
        "disagreement_reasons": [str(item)[:240] for item in reasons[:25]],
        "calibration_bucket": candidate.get("calibration_bucket") or candidate.get("bucket"),
        "manifold_cluster_id": candidate.get("manifold_cluster_id"),
        "strategy_ids": list(candidate.get("strategy_ids") or candidate.get("strategy_id") or [])[:25]
        if isinstance(candidate.get("strategy_ids") or candidate.get("strategy_id"), list)
        else ([candidate.get("strategy_id")] if candidate.get("strategy_id") else []),
        "created_at": created,
        "redacted": True,
        **profit_lab_safety_flags(deepseek_used=True),
    }
    record["provider_write"] = False
    record["execution_allowed"] = False
    record["live_execution_enabled"] = False
    return compact_redacted_for_deepseek(record, list_limit=25)


def load_disagreement_queue(*, base_data_dir: str = "data", limit: int = 100) -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    if isinstance(payload, Mapping):
        items = [row for row in payload.get("items", []) if isinstance(row, Mapping)]
    else:
        items = []
    cap = max(1, min(int(limit or 100), 500))
    return {
        "ok": True,
        "status": "ok",
        "schema_version": DISAGREEMENT_SCHEMA_VERSION,
        "count": len(items),
        "items": [compact_redacted_for_deepseek(dict(row), list_limit=25) for row in items[-cap:]],
        "storage_backend": "file",
        "storage": get_storage_health(),
        **profit_lab_safety_flags(deepseek_used=False),
    }


def append_disagreement_record(
    record: Mapping[str, Any],
    *,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    items = [row for row in payload.get("items", []) if isinstance(row, Mapping)] if isinstance(payload, Mapping) else []
    safe_record = compact_redacted_for_deepseek(dict(record), list_limit=25)
    items.append(safe_record)
    wrapper = {
        "ok": True,
        "status": "ok",
        "schema_version": DISAGREEMENT_SCHEMA_VERSION,
        "updated_at": utc_now_iso(),
        "count": len(items),
        "items": items[-500:],
        "storage_backend": "file",
        **profit_lab_safety_flags(deepseek_used=False),
    }
    latest = _latest_path(base_data_dir)
    history = _queue_dir(base_data_dir) / f"{sanitize_filename(str(safe_record.get('disagreement_id') or utc_now_iso()))}.json"
    _atomic_write_json(latest, wrapper)
    _atomic_write_json(history, safe_record)
    return {
        "ok": True,
        "status": "disagreement_recorded",
        "disagreement_id": safe_record.get("disagreement_id"),
        "disagreement_path": _project_relative_path(base_data_dir, latest),
        "disagreement_item_path": _project_relative_path(base_data_dir, history),
        "record": safe_record,
        **profit_lab_safety_flags(deepseek_used=False),
    }
