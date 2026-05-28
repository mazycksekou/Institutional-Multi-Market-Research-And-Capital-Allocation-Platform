from __future__ import annotations

from typing import Any

_SECRET_KEYS = ("key", "secret", "token", "password", "auth", "credential")


def _redact(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for k, v in payload.items():
            lk = str(k).lower()
            if any(s in lk for s in _SECRET_KEYS):
                out[k] = "[redacted]"
            elif lk in {"provider_payload", "raw_payload", "external_payload"}:
                out[k] = "[omitted]"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(payload, list):
        return [_redact(v) for v in payload]
    return payload


def redact_and_limit_payload(payload: Any, limit: int = 10, verbose: bool = False) -> Any:
    safe = _redact(payload)
    max_items = 100 if verbose else 10
    cap = max(1, min(int(limit or max_items), max_items))
    if isinstance(safe, list):
        return safe[:cap]
    if isinstance(safe, dict):
        compact = dict(safe)
        for k in list(compact.keys()):
            if isinstance(compact[k], list):
                compact[k] = compact[k][:cap]
        return compact
    return safe


def compact_health_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok" if payload.get("ok", True) else "error",
        "timestamp": payload.get("checked_at") or payload.get("created_at"),
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "counts": {
            "review_queue_count": int(payload.get("review_queue_count", payload.get("count", 0))),
            "provider_count": int(payload.get("provider_count", 0)),
        },
        "blockers": list(payload.get("blockers", []))[:10],
        "top_reasons": list(payload.get("top_reasons", []))[:10],
    }


def compact_review_queue_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    items = list(payload.get("items", []))[: max(1, min(limit, 10))]
    top = []
    for it in items:
        top.append({
            "decision": it.get("recommended_action", "review_required"),
            "recommended_action": it.get("recommended_action"),
            "opportunity_score": it.get("opportunity_score"),
            "confidence": it.get("confidence"),
            "risk": it.get("risk"),
            "blockers": list(it.get("blockers", []))[:10],
            "next_check_seconds": it.get("recheck_after_seconds"),
        })
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": payload.get("updated_at") or payload.get("checked_at"),
        "dry_run": True,
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "counts": {"review_items": int(payload.get("count", len(top)))},
        "items": top,
    }


def compact_run_once_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok" if payload.get("ok", True) else "error",
        "run_id": payload.get("run_id"),
        "timestamp": payload.get("created_at") or payload.get("checked_at"),
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "counts": {
            "review_queue_size": int(payload.get("review_queue_size", 0)),
            "candidates_processed": int(payload.get("candidates_processed", 0)),
            "skipped_items": int(payload.get("skipped_count", len(payload.get("skipped_items", [])))),
        },
        "report_path": (payload.get("report") or {}).get("path") or payload.get("report_path"),
        "top_reasons": list(payload.get("monitor_errors", []))[:10],
        "blockers": list(payload.get("blockers", []))[:10],
    }


def compact_governance_inventory(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    items = list(payload.get("inventory", []))[: max(1, min(limit, 10))]
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": payload.get("checked_at"),
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "counts": {"inventory": int(len(payload.get("inventory", [])))},
        "items": [
            {
                "decision": i.get("status_reason", "review_required"),
                "recommended_action": "review_required",
                "opportunity_score": None,
                "confidence": None,
                "risk": None,
                "blockers": [],
            }
            for i in items
        ],
    }


def compact_governance_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": payload.get("created_at") or payload.get("checked_at"),
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "counts": {
            "blocked_model_count": int(payload.get("blocked_model_count", 0)),
            "eligible_model_count": int(payload.get("eligible_model_count", 0)),
        },
        "top_reasons": list(payload.get("recommended_next_actions", []))[:10],
    }


def compact_validation_response(payload: dict[str, Any]) -> dict[str, Any]:
    v = payload.get("validation", payload)
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": None,
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(v.get("human_approval_required", True)),
        "auto_execution_enabled": False,
        "decision": v.get("promotion_recommendation", "review_required"),
        "blockers": list(v.get("blocked_reasons", []))[:10],
        "top_reasons": list(v.get("blocked_reasons", []))[:10],
    }
