from __future__ import annotations

import json
import os
from typing import Any

import httpx

from src.services.scheduler_config import utc_now_iso

FORBIDDEN_RECOMMENDED_ACTIONS = {
    "place_bet",
    "execute_trade",
    "persist_outcome",
    "enable_execution",
    "bypass_dry_run",
    "change_thresholds",
    "override_code_scores",
}
ALLOWED_RECOMMENDED_ACTIONS = {
    "continue_collecting",
    "recheck_later",
    "insufficient_sample",
    "provider_lag",
    "needs_human_review",
    "calibration_ready_for_review",
}
REQUIRED_REVIEW_KEYS = {
    "summary",
    "crosscheck_status",
    "risk_flags",
    "valuation_mismatches",
    "missing_inputs",
    "data_quality_notes",
    "recommended_action",
    "confidence",
    "must_not_execute",
}
VALUATION_FIELDS = (
    "liquidity_score",
    "spread_score",
    "pricing_quality_score",
    "close_time_score",
    "market_structure_score",
    "risk_score",
    "confidence_score",
    "review_priority_score",
)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_deepseek_config() -> dict[str, Any]:
    try:
        timeout = float(os.getenv("DEEPSEEK_TIMEOUT", "20") or 20)
    except (TypeError, ValueError):
        timeout = 20.0
    return {
        "enabled": _env_bool("DEEPSEEK_ENABLED", False),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/"),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-r1").strip() or "deepseek-r1",
        "timeout": max(1.0, timeout),
    }


def _compact_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _redact_compact(value: Any, *, list_limit: int = 25) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            lower = str(key).lower()
            if any(part in lower for part in ("key", "secret", "token", "password", "auth", "credential", "signature", "header")):
                continue
            if lower in {"provider_payload", "raw_payload", "external_payload", "source_payload", "source_payload_redacted", "raw_provider_payload", "raw_kalshi_payload"}:
                continue
            redacted = _redact_compact(item, list_limit=list_limit)
            if redacted is not None:
                out[str(key)] = redacted
        return out
    if isinstance(value, list):
        return [_redact_compact(item, list_limit=list_limit) for item in value[:list_limit]]
    return _compact_scalar(value)


def compact_review_input(
    *,
    collector_cycle_report: dict[str, Any] | None = None,
    daily_report: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    sampled_contracts: list[dict[str, Any]] | None = None,
    top_n: int = 20,
) -> dict[str, Any]:
    contracts = []
    for row in list(sampled_contracts or [])[: max(0, int(top_n))]:
        contracts.append(
            {
                "ticker": row.get("ticker"),
                "contract_id": row.get("contract_id"),
                "close_time": row.get("close_time"),
                "bucket": row.get("collector_bucket") or row.get("bucket"),
                "liquidity_score": row.get("liquidity_score"),
                "spread_score": row.get("spread_score"),
                "pricing_quality_score": row.get("pricing_quality_score"),
                "close_time_score": row.get("close_time_score"),
                "market_structure_score": row.get("market_structure_score"),
                "risk_score": row.get("risk_score"),
                "confidence_score": row.get("confidence_score"),
                "review_priority_score": row.get("review_priority_score"),
                "liquidity_tier": row.get("liquidity_tier"),
                "reason_codes": list(row.get("reason_codes") or [])[:10],
                "implied_probability": row.get("implied_probability"),
                "observed_price": row.get("observed_price") if row.get("observed_price") is not None else row.get("yes_price"),
                "outcome_status": row.get("outcome_status"),
                "final_outcome": row.get("final_outcome"),
            }
        )
    return _redact_compact(
        {
            "created_at": utc_now_iso(),
            "collector_cycle_report": collector_cycle_report or {},
            "daily_report": daily_report or {},
            "calibration_report": calibration_report or {},
            "sampled_contracts": contracts,
            "safety_contract": {
                "provider_write": False,
                "execution_allowed_count": 0,
                "auto_execution_enabled": False,
                "kalshi_order_execution_enabled": False,
                "must_not_execute": True,
            },
        }
    )


def local_crosscheck(review_input: dict[str, Any]) -> dict[str, list[str]]:
    mismatches: list[str] = []
    risk_flags: list[str] = []
    missing_inputs: list[str] = []
    cycle = review_input.get("collector_cycle_report") if isinstance(review_input.get("collector_cycle_report"), dict) else {}
    calibration = review_input.get("calibration_report") if isinstance(review_input.get("calibration_report"), dict) else {}
    contracts = review_input.get("sampled_contracts") if isinstance(review_input.get("sampled_contracts"), list) else []

    seen: set[str] = set()
    for row in contracts:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or row.get("contract_id") or "").strip()
        if ticker:
            if ticker in seen:
                risk_flags.append(f"duplicate_ticker:{ticker}")
            seen.add(ticker)
        else:
            missing_inputs.append("missing_ticker")
        if row.get("implied_probability") is None:
            missing_inputs.append(f"missing_implied_probability:{ticker or 'unknown'}")
        for field in VALUATION_FIELDS:
            value = row.get(field)
            if value is None:
                missing_inputs.append(f"missing_{field}:{ticker or 'unknown'}")
                continue
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                mismatches.append(f"{field}_not_numeric:{ticker or 'unknown'}")
                continue
            if parsed < 0.0 or parsed > 100.0:
                mismatches.append(f"{field}_outside_0_100:{ticker or 'unknown'}")
        liquidity_score = row.get("liquidity_score")
        tier = str(row.get("liquidity_tier") or "")
        try:
            liq = float(liquidity_score)
        except (TypeError, ValueError):
            liq = None
        if liq is not None:
            if liq < 20 and tier not in {"very_low_liquidity", "missing_liquidity"}:
                mismatches.append(f"liquidity_tier_inconsistent:{ticker or 'unknown'}")
            if 20 <= liq < 45 and tier != "low_liquidity":
                mismatches.append(f"liquidity_tier_inconsistent:{ticker or 'unknown'}")
        if row.get("final_outcome") and row.get("outcome_status") not in {"settled", "void", "cancelled"}:
            risk_flags.append(f"explicit_outcome_without_persisted_status:{ticker or 'unknown'}")

    unknown_persisted = int(cycle.get("unknown_persisted_count", 0) or 0)
    if unknown_persisted:
        risk_flags.append("unknown_rows_persisted")
    if int(cycle.get("execution_allowed_count", 0) or 0) != 0:
        risk_flags.append("execution_allowed_nonzero")
    if bool(cycle.get("provider_write", False)):
        risk_flags.append("provider_write_true")
    if calibration.get("status") in {"insufficient_data", "partial_calibration"}:
        if int(calibration.get("matched_outcomes_count", 0) or 0) < 30:
            risk_flags.append("calibration_sample_too_small")
    return {
        "risk_flags": risk_flags,
        "valuation_mismatches": mismatches,
        "missing_inputs": missing_inputs,
    }


def _default_review_payload(review_input: dict[str, Any], *, status: str = "warning", summary: str | None = None) -> dict[str, Any]:
    checks = local_crosscheck(review_input)
    has_warnings = bool(checks["risk_flags"] or checks["valuation_mismatches"] or checks["missing_inputs"])
    return {
        "summary": summary or ("Local compact crosscheck completed." if not has_warnings else "Local compact crosscheck found warnings."),
        "crosscheck_status": status if has_warnings else "pass",
        "risk_flags": checks["risk_flags"],
        "valuation_mismatches": checks["valuation_mismatches"],
        "missing_inputs": checks["missing_inputs"],
        "data_quality_notes": [],
        "recommended_action": "insufficient_sample" if "calibration_sample_too_small" in checks["risk_flags"] else "continue_collecting",
        "confidence": 0.0,
        "must_not_execute": True,
    }


def validate_reviewer_output(payload: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "invalid_json_object"
    missing = sorted(REQUIRED_REVIEW_KEYS - set(payload))
    if missing:
        return None, "missing_required_keys"
    action = str(payload.get("recommended_action") or "").strip()
    if action in FORBIDDEN_RECOMMENDED_ACTIONS:
        return None, "forbidden_recommended_action"
    if action not in ALLOWED_RECOMMENDED_ACTIONS:
        return None, "unsupported_recommended_action"
    if payload.get("must_not_execute") is not True:
        return None, "must_not_execute_not_true"
    status = str(payload.get("crosscheck_status") or "").strip()
    if status not in {"pass", "warning", "fail"}:
        return None, "unsupported_crosscheck_status"
    try:
        confidence = float(payload.get("confidence"))
    except (TypeError, ValueError):
        return None, "invalid_confidence"
    clean = {
        "summary": str(payload.get("summary") or "")[:1000],
        "crosscheck_status": status,
        "risk_flags": [str(item)[:240] for item in list(payload.get("risk_flags") or [])[:50]],
        "valuation_mismatches": [str(item)[:240] for item in list(payload.get("valuation_mismatches") or [])[:50]],
        "missing_inputs": [str(item)[:240] for item in list(payload.get("missing_inputs") or [])[:50]],
        "data_quality_notes": [str(item)[:240] for item in list(payload.get("data_quality_notes") or [])[:50]],
        "recommended_action": action,
        "confidence": max(0.0, min(1.0, confidence)),
        "must_not_execute": True,
    }
    return clean, None


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty_response")
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


def run_deepseek_review(
    *,
    collector_cycle_report: dict[str, Any] | None = None,
    daily_report: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    sampled_contracts: list[dict[str, Any]] | None = None,
    enabled: bool | None = None,
) -> dict[str, Any]:
    config = get_deepseek_config()
    if enabled is not None:
        config["enabled"] = bool(enabled)
    review_input = compact_review_input(
        collector_cycle_report=collector_cycle_report,
        daily_report=daily_report,
        calibration_report=calibration_report,
        sampled_contracts=sampled_contracts,
    )
    local_review = _default_review_payload(review_input)
    if not config["enabled"]:
        return {
            "ok": True,
            "status": "disabled",
            "enabled": False,
            "local_server_reachable": False,
            "json_schema_valid": True,
            "forbidden_actions_rejected": False,
            "reviewer_side_effects": "none",
            "provider_write": False,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "review": local_review,
        }

    prompt = (
        "Review this compact Kalshi calibration collector report. Return strict JSON only with keys "
        "summary, crosscheck_status, risk_flags, valuation_mismatches, missing_inputs, "
        "data_quality_notes, recommended_action, confidence, must_not_execute. "
        "Do not recommend execution, trading, order placement, threshold changes, or outcome persistence. "
        f"Compact input:\n{json.dumps(review_input, sort_keys=True)}"
    )
    try:
        with httpx.Client(timeout=float(config["timeout"])) as client:
            response = client.post(
                f"{config['base_url']}/api/generate",
                json={"model": config["model"], "prompt": prompt, "stream": False},
            )
        response.raise_for_status()
        body = response.json()
        raw_text = body.get("response") if isinstance(body, dict) else None
        parsed = _extract_json_object(str(raw_text or ""))
        validated, reason = validate_reviewer_output(parsed)
        if reason:
            return {
                "ok": False,
                "status": "review_rejected",
                "enabled": True,
                "local_server_reachable": True,
                "json_schema_valid": False,
                "rejected_reason": reason,
                "forbidden_actions_rejected": reason == "forbidden_recommended_action",
                "reviewer_side_effects": "none",
                "provider_write": False,
                "auto_execution_enabled": False,
                "kalshi_order_execution_enabled": False,
                "review": local_review,
            }
        local_checks = local_crosscheck(review_input)
        merged = dict(validated or {})
        for key in ("risk_flags", "valuation_mismatches", "missing_inputs"):
            merged[key] = list(dict.fromkeys(list(merged.get(key) or []) + local_checks[key]))[:50]
        if merged["risk_flags"] or merged["valuation_mismatches"] or merged["missing_inputs"]:
            merged["crosscheck_status"] = "warning" if merged["crosscheck_status"] == "pass" else merged["crosscheck_status"]
        return {
            "ok": True,
            "status": "review_complete",
            "enabled": True,
            "local_server_reachable": True,
            "json_schema_valid": True,
            "forbidden_actions_rejected": False,
            "reviewer_side_effects": "none",
            "provider_write": False,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "review": merged,
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "ok": False,
            "status": "invalid_json",
            "enabled": True,
            "local_server_reachable": True,
            "json_schema_valid": False,
            "forbidden_actions_rejected": False,
            "reviewer_side_effects": "none",
            "provider_write": False,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "review": local_review,
        }
    except httpx.TimeoutException:
        return {
            "ok": False,
            "status": "timeout",
            "enabled": True,
            "local_server_reachable": False,
            "json_schema_valid": False,
            "forbidden_actions_rejected": False,
            "reviewer_side_effects": "none",
            "provider_write": False,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "review": local_review,
        }
    except Exception:
        return {
            "ok": False,
            "status": "provider_error",
            "enabled": True,
            "local_server_reachable": False,
            "json_schema_valid": False,
            "forbidden_actions_rejected": False,
            "reviewer_side_effects": "none",
            "provider_write": False,
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
            "review": local_review,
        }
