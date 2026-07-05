from __future__ import annotations

import json
import os
from typing import Any

import httpx

from src.data.data_paths import resolve_base_data_dir
from src.services.ledger_service import append_audit_record
from src.providers.institutional_cross_asset_adapters import compact_redact


ALLOWED_RECOMMENDED_ACTIONS = {
    "continue_collecting",
    "recheck_later",
    "insufficient_sample",
    "provider_lag",
    "needs_human_review",
    "calibration_ready_for_review",
    "fix_data_contract",
    "keep_execution_disabled",
}

FORBIDDEN_RECOMMENDED_ACTIONS = {
    "place_bet",
    "place_trade",
    "execute_order",
    "submit_order",
    "persist_outcome",
    "enable_execution",
    "bypass_dry_run",
    "override_code_scores",
    "change_thresholds_automatically",
}


def default_review(summary: str = "DeepSeek sidecar review disabled.") -> dict[str, Any]:
    return {
        "summary": summary,
        "crosscheck_status": "pass",
        "asset_class_findings": {
            "prediction_market": [],
            "stock": [],
            "bond": [],
            "major_asset": [],
            "sportsbook": [],
        },
        "valuation_mismatches": [],
        "risk_flags": [],
        "execution_desk_warnings": [],
        "missing_inputs": [],
        "data_quality_notes": [],
        "recommended_action": "continue_collecting",
        "confidence": 0.0,
        "must_not_execute": True,
    }


def _validate_review(payload: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "malformed_json"
    review = dict(payload)
    action = str(review.get("recommended_action") or "").strip()
    if action in FORBIDDEN_RECOMMENDED_ACTIONS:
        return None, "forbidden_recommended_action"
    if action not in ALLOWED_RECOMMENDED_ACTIONS:
        return None, "unsupported_recommended_action"
    if review.get("must_not_execute") is not True:
        return None, "must_not_execute_missing"
    asset_findings = review.get("asset_class_findings")
    if not isinstance(asset_findings, dict):
        asset_findings = default_review()["asset_class_findings"]
    for asset_class in ("prediction_market", "stock", "bond", "major_asset", "sportsbook"):
        if not isinstance(asset_findings.get(asset_class), list):
            asset_findings[asset_class] = []
    review["asset_class_findings"] = asset_findings
    for list_key in ("valuation_mismatches", "risk_flags", "execution_desk_warnings", "missing_inputs", "data_quality_notes"):
        if not isinstance(review.get(list_key), list):
            review[list_key] = []
        review[list_key] = [str(item)[:300] for item in review[list_key]][:50]
    review["summary"] = str(review.get("summary") or "")[:1000]
    review["crosscheck_status"] = str(review.get("crosscheck_status") or "warning")
    if review["crosscheck_status"] not in {"pass", "warning", "fail"}:
        review["crosscheck_status"] = "warning"
    try:
        confidence = float(review.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    review["confidence"] = max(0.0, min(1.0, confidence))
    review["must_not_execute"] = True
    return review, None


def _extract_model_json(response_payload: Any) -> Any:
    if isinstance(response_payload, dict):
        if isinstance(response_payload.get("review"), dict):
            return response_payload["review"]
        if isinstance(response_payload.get("message"), dict) and isinstance(response_payload["message"].get("content"), str):
            return json.loads(response_payload["message"]["content"])
        if isinstance(response_payload.get("response"), str):
            return json.loads(response_payload["response"])
        return response_payload
    if isinstance(response_payload, str):
        return json.loads(response_payload)
    return response_payload


def run_deepseek_sidecar_review(
    *,
    report: dict[str, Any] | None = None,
    enabled: bool | None = None,
    local_url: str | None = None,
    base_data_dir: str = "data",
    persist_audit: bool = True,
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    is_enabled = bool(enabled) if enabled is not None else os.getenv("INSTITUTIONAL_DEEPSEEK_REVIEW_ENABLED", "false").lower() in {"1", "true", "yes"}
    compact_report = compact_redact(report or {})
    base = {
        "ok": True,
        "status": "disabled",
        "enabled": is_enabled,
        "local_server_reachable": False,
        "json_schema_valid": True,
        "forbidden_actions_rejected": False,
        "reviewer_side_effects": "none",
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "raw_payload_included": False,
        "review": default_review(),
    }
    if not is_enabled:
        if persist_audit:
            append_audit_record(
                action_type="deepseek_review",
                input_payload=compact_report,
                output_payload=base,
                base_data_dir=base_data_dir,
                compact_summary="DeepSeek disabled by default; no side effects.",
            )
        return base

    url = local_url or os.getenv("INSTITUTIONAL_DEEPSEEK_LOCAL_URL", "http://127.0.0.1:11434/api/generate")
    try:
        response = httpx.post(
            url,
            json={
                "model": os.getenv("INSTITUTIONAL_DEEPSEEK_MODEL", "deepseek-r1"),
                "stream": False,
                "prompt": (
                    "Review this compact institutional sidecar report as JSON only. "
                    "Do not recommend execution or state changes. Return the required schema.\n"
                    + json.dumps(compact_report, separators=(",", ":"), sort_keys=True)
                ),
            },
            timeout=10.0,
        )
        response.raise_for_status()
        model_payload = _extract_model_json(response.json())
        review, reason = _validate_review(model_payload)
    except Exception:
        out = {
            **base,
            "status": "unavailable",
            "enabled": True,
            "local_server_reachable": False,
            "json_schema_valid": False,
            "rejected_reason": "local_server_unavailable_or_malformed_json",
            "review": default_review("DeepSeek local reviewer unavailable or returned malformed JSON."),
        }
        if persist_audit:
            append_audit_record(
                action_type="deepseek_review",
                input_payload=compact_report,
                output_payload=out,
                base_data_dir=base_data_dir,
                compact_summary="DeepSeek unavailable; no side effects.",
            )
        return out

    if reason:
        out = {
            **base,
            "status": "rejected",
            "enabled": True,
            "local_server_reachable": True,
            "json_schema_valid": False,
            "forbidden_actions_rejected": reason == "forbidden_recommended_action",
            "rejected_reason": reason,
            "review": default_review(f"DeepSeek output rejected: {reason}."),
        }
        if persist_audit:
            append_audit_record(
                action_type="deepseek_review",
                input_payload=compact_report,
                output_payload=out,
                base_data_dir=base_data_dir,
                compact_summary="DeepSeek output rejected; no side effects.",
            )
        return out

    out = {
        **base,
        "status": "review_complete",
        "enabled": True,
        "local_server_reachable": True,
        "json_schema_valid": True,
        "review": review,
    }
    if persist_audit:
        append_audit_record(
            action_type="deepseek_review",
            input_payload=compact_report,
            output_payload=out,
            base_data_dir=base_data_dir,
            compact_summary="DeepSeek sidecar review completed without side effects.",
        )
    return out
