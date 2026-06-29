from __future__ import annotations

import json
from typing import Any, Mapping

from .scheduler_config import utc_now_iso
from .secret_safety import RAW_PAYLOAD_KEYS, is_secret_key, redact_string
from .security_policy import (
    EXECUTION_TRUE_FIELDS,
    EXECUTABLE_PAYLOAD_KEYS,
    detect_execution_authority_violations,
    locked_safety_flags,
)


ALLOWED_RECOMMENDED_ACTIONS = {
    "ACTIVE_REVIEW",
    "WATCHLIST_REVIEW",
    "LOW_PRIORITY_REVIEW",
    "NO_BET",
    "NO_TRADE",
    "DATA_INSUFFICIENT",
    "NO_REVIEW",
}

CANDIDATE_REQUIRED_FIELDS = {
    "deepseek_status",
    "candidate_id",
    "asset_type",
    "market_type",
    "recommended_action",
    "confidence_score",
    "edge_quality_score",
    "liquidity_risk_score",
    "trap_risk_score",
    "calibration_support_score",
    "out_of_distribution_risk",
    "agreement_with_core_model",
    "disagreement_reasons",
    "missing_inputs",
    "review_reasons",
    "no_bet_reasons",
    "no_trade_reasons",
    "next_data_to_collect",
    "red_team_only",
    "deepseek_used",
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "auto_execution",
    "human_approval_required",
}

CANDIDATE_OPTIONAL_FIELDS = {
    "owner_approval_required",
}

DAILY_REPORT_REQUIRED_FIELDS = {
    "report_id",
    "date",
    "strongest_review_candidates",
    "strongest_no_bet_no_trade_traps",
    "calibration_improvements",
    "failing_clusters",
    "missing_data",
    "provider_issues",
    "disagreement_count",
    "repeated_model_mistakes",
    "recommended_next_data_to_collect",
    "recommended_next_codex_task",
    "safety_status",
    "red_team_only",
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
}

DAILY_REPORT_OPTIONAL_FIELDS = {
    "deepseek_used",
    "auto_execution",
    "auto_execution_enabled",
    "human_approval_required",
    "owner_approval_required",
}

FORBIDDEN_INPUT_KEYS = set(RAW_PAYLOAD_KEYS) | set(EXECUTABLE_PAYLOAD_KEYS) | {
    "headers",
    "auth_headers",
    "authorization",
    "signature",
    "signed_payload",
    "private_key",
    "api_key",
    "apikey",
    "secret",
    "token",
}


def profit_lab_safety_flags(*, deepseek_used: bool = False) -> dict[str, Any]:
    flags = locked_safety_flags()
    flags.update(
        {
            "red_team_only": True,
            "deepseek_used": bool(deepseek_used),
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "owner_approval_required": True,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    )
    return flags


def compact_redacted_for_deepseek(value: Any, *, list_limit: int = 25, depth: int = 0) -> Any:
    if depth > 8:
        return None
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lower = key_text.strip().lower()
            if lower in FORBIDDEN_INPUT_KEYS or is_secret_key(key_text):
                continue
            if lower in EXECUTION_TRUE_FIELDS:
                out[key_text] = False
                continue
            compact = compact_redacted_for_deepseek(item, list_limit=list_limit, depth=depth + 1)
            if compact is not None:
                out[key_text] = compact
        return out
    if isinstance(value, list):
        return [
            item
            for item in (
                compact_redacted_for_deepseek(row, list_limit=list_limit, depth=depth + 1)
                for row in value[: max(1, min(int(list_limit or 25), 100))]
            )
            if item is not None
        ]
    if isinstance(value, str):
        return redact_string(value)[:500]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:240]


def extract_json_payload(response_payload: Any) -> Any:
    if isinstance(response_payload, Mapping):
        choices = response_payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, Mapping):
                message = first.get("message")
                if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                    return extract_json_payload(message["content"])
                if isinstance(first.get("text"), str):
                    return extract_json_payload(first["text"])
        for key in ("candidate_review", "daily_report", "review", "report"):
            if isinstance(response_payload.get(key), Mapping):
                return response_payload[key]
        if isinstance(response_payload.get("response"), str):
            return extract_json_payload(response_payload["response"])
        return dict(response_payload)
    if isinstance(response_payload, str):
        text = response_payload.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise
    return response_payload


def _coerce_score(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = 0.0
    return round(max(0.0, min(100.0, parsed)), 4)


def _coerce_list(value: Any, *, limit: int = 25) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    return [redact_string(str(item))[:240] for item in value[:limit] if str(item).strip()]


def _candidate_id(candidate: Mapping[str, Any] | None) -> str:
    candidate = candidate or {}
    return str(
        candidate.get("candidate_id")
        or candidate.get("id")
        or candidate.get("review_item_id")
        or candidate.get("contract_id")
        or candidate.get("ticker")
        or candidate.get("asset_symbol")
        or "unknown"
    )[:120]


def default_candidate_review(
    *,
    status: str,
    candidate: Mapping[str, Any] | None = None,
    reason: str | None = None,
    deepseek_used: bool = False,
) -> dict[str, Any]:
    candidate = candidate or {}
    missing_inputs = [reason] if reason else []
    action = "NO_REVIEW" if status == "disabled" else "DATA_INSUFFICIENT"
    return {
        "deepseek_status": status,
        "candidate_id": _candidate_id(candidate),
        "asset_type": str(candidate.get("asset_type") or candidate.get("asset_class") or "unknown")[:80],
        "market_type": str(candidate.get("market_type") or candidate.get("source_type") or "unknown")[:120],
        "recommended_action": action,
        "confidence_score": 0.0,
        "edge_quality_score": 0.0,
        "liquidity_risk_score": 0.0,
        "trap_risk_score": 0.0,
        "calibration_support_score": 0.0,
        "out_of_distribution_risk": 0.0,
        "agreement_with_core_model": False,
        "disagreement_reasons": [],
        "missing_inputs": missing_inputs,
        "review_reasons": ["deepseek_not_used"] if not deepseek_used else [],
        "no_bet_reasons": [],
        "no_trade_reasons": [],
        "next_data_to_collect": ["compact_redacted_calibration_and_outcome_evidence"],
        **profit_lab_safety_flags(deepseek_used=deepseek_used),
    }


def validate_candidate_review(
    payload: Any,
    *,
    candidate: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(payload, Mapping):
        return None, "invalid_json_object"
    raw = dict(payload)
    violations = detect_execution_authority_violations(raw)
    if violations:
        return None, "execution_authority_violation"
    allowed = CANDIDATE_REQUIRED_FIELDS | CANDIDATE_OPTIONAL_FIELDS
    unsupported = sorted(set(raw) - allowed)
    if unsupported:
        return None, "unsupported_keys"
    missing = sorted(CANDIDATE_REQUIRED_FIELDS - set(raw))
    if missing:
        return None, "missing_required_keys"
    action = str(raw.get("recommended_action") or "").strip().upper()
    if action not in ALLOWED_RECOMMENDED_ACTIONS:
        return None, "unsupported_recommended_action"
    if raw.get("red_team_only") is not True:
        return None, "red_team_only_not_true"
    if raw.get("provider_write") is not False:
        return None, "provider_write_not_false"
    if raw.get("execution_allowed") is not False:
        return None, "execution_allowed_not_false"
    if raw.get("live_execution_enabled") is not False:
        return None, "live_execution_enabled_not_false"
    if raw.get("auto_execution") is not False:
        return None, "auto_execution_not_false"
    if raw.get("human_approval_required") is not True:
        return None, "human_approval_required_not_true"

    clean = {
        "deepseek_status": str(raw.get("deepseek_status") or "review_complete")[:80],
        "candidate_id": str(raw.get("candidate_id") or _candidate_id(candidate))[:120],
        "asset_type": str(raw.get("asset_type") or (candidate or {}).get("asset_type") or "unknown")[:80],
        "market_type": str(raw.get("market_type") or (candidate or {}).get("market_type") or "unknown")[:120],
        "recommended_action": action,
        "confidence_score": _coerce_score(raw.get("confidence_score")),
        "edge_quality_score": _coerce_score(raw.get("edge_quality_score")),
        "liquidity_risk_score": _coerce_score(raw.get("liquidity_risk_score")),
        "trap_risk_score": _coerce_score(raw.get("trap_risk_score")),
        "calibration_support_score": _coerce_score(raw.get("calibration_support_score")),
        "out_of_distribution_risk": _coerce_score(raw.get("out_of_distribution_risk")),
        "agreement_with_core_model": bool(raw.get("agreement_with_core_model")),
        "disagreement_reasons": _coerce_list(raw.get("disagreement_reasons")),
        "missing_inputs": _coerce_list(raw.get("missing_inputs")),
        "review_reasons": _coerce_list(raw.get("review_reasons")),
        "no_bet_reasons": _coerce_list(raw.get("no_bet_reasons")),
        "no_trade_reasons": _coerce_list(raw.get("no_trade_reasons")),
        "next_data_to_collect": _coerce_list(raw.get("next_data_to_collect")),
        **profit_lab_safety_flags(deepseek_used=True),
    }
    clean["deepseek_status"] = "review_complete" if clean["deepseek_status"] == "ok" else clean["deepseek_status"]
    return clean, None


def default_daily_report(
    *,
    status: str,
    report_date: str | None = None,
    reason: str | None = None,
    deepseek_used: bool = False,
) -> dict[str, Any]:
    day = report_date or utc_now_iso()[:10]
    return {
        "report_id": f"deepseek_profit_lab_{day}",
        "date": day,
        "strongest_review_candidates": [],
        "strongest_no_bet_no_trade_traps": [],
        "calibration_improvements": [],
        "failing_clusters": [],
        "missing_data": [reason] if reason else [],
        "provider_issues": [],
        "disagreement_count": 0,
        "repeated_model_mistakes": [],
        "recommended_next_data_to_collect": ["compact_outcome_and_calibration_evidence"],
        "recommended_next_codex_task": "review DeepSeek Profit Lab input coverage",
        "safety_status": {
            "status": status,
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        },
        **profit_lab_safety_flags(deepseek_used=deepseek_used),
    }


def validate_daily_report(
    payload: Any,
    *,
    report_date: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(payload, Mapping):
        return None, "invalid_json_object"
    raw = dict(payload)
    violations = detect_execution_authority_violations(raw)
    if violations:
        return None, "execution_authority_violation"
    allowed = DAILY_REPORT_REQUIRED_FIELDS | DAILY_REPORT_OPTIONAL_FIELDS
    unsupported = sorted(set(raw) - allowed)
    if unsupported:
        return None, "unsupported_keys"
    missing = sorted(DAILY_REPORT_REQUIRED_FIELDS - set(raw))
    if missing:
        return None, "missing_required_keys"
    if raw.get("red_team_only") is not True:
        return None, "red_team_only_not_true"
    if raw.get("provider_write") is not False:
        return None, "provider_write_not_false"
    if raw.get("execution_allowed") is not False:
        return None, "execution_allowed_not_false"
    if raw.get("live_execution_enabled") is not False:
        return None, "live_execution_enabled_not_false"

    day = str(raw.get("date") or report_date or utc_now_iso()[:10])[:40]
    safety = compact_redacted_for_deepseek(raw.get("safety_status") or {}, list_limit=25)
    if not isinstance(safety, dict):
        safety = {}
    safety.update(
        {
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        }
    )
    clean = {
        "report_id": str(raw.get("report_id") or f"deepseek_profit_lab_{day}")[:120],
        "date": day,
        "strongest_review_candidates": compact_redacted_for_deepseek(raw.get("strongest_review_candidates") or [], list_limit=10),
        "strongest_no_bet_no_trade_traps": compact_redacted_for_deepseek(raw.get("strongest_no_bet_no_trade_traps") or [], list_limit=10),
        "calibration_improvements": _coerce_list(raw.get("calibration_improvements"), limit=20),
        "failing_clusters": compact_redacted_for_deepseek(raw.get("failing_clusters") or [], list_limit=10),
        "missing_data": _coerce_list(raw.get("missing_data"), limit=25),
        "provider_issues": _coerce_list(raw.get("provider_issues"), limit=25),
        "disagreement_count": int(raw.get("disagreement_count") or 0),
        "repeated_model_mistakes": _coerce_list(raw.get("repeated_model_mistakes"), limit=25),
        "recommended_next_data_to_collect": _coerce_list(raw.get("recommended_next_data_to_collect"), limit=25),
        "recommended_next_codex_task": str(raw.get("recommended_next_codex_task") or "")[:240],
        "safety_status": safety,
        **profit_lab_safety_flags(deepseek_used=True),
    }
    return clean, None
