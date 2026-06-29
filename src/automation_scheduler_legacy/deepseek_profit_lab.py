from __future__ import annotations

import json
import os
from typing import Any, Mapping

import httpx

from .ai_provider_security import evaluate_ai_provider
from .calibration import build_calibration_report
from src.data.data_paths import get_storage_health, resolve_base_data_dir
from .deepseek_daily_report import build_local_daily_report, write_daily_report
from .deepseek_disagreement_queue import (
    append_disagreement_record,
    build_disagreement_record,
    load_disagreement_queue,
    should_record_disagreement,
)
from .deepseek_prompt_contracts import build_candidate_review_prompt, build_daily_report_prompt
from .deepseek_response_validator import (
    compact_redacted_for_deepseek,
    default_candidate_review,
    default_daily_report,
    extract_json_payload,
    profit_lab_safety_flags,
    validate_candidate_review,
    validate_daily_report,
)
from src.services.execution_service import compact_trap_report, load_trap_report
from .outcome_store import load_outcome_state, summarize_outcomes
from src.providers.health import summarize_provider_health
from .review_queue import load_review_queue_state, summarize_review_items
from src.services.scheduler_config import get_default_scheduler_config, utc_now_iso
from .security_readiness_report import build_security_readiness_report


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


def _timeout_seconds() -> float:
    raw = os.getenv("DEEPSEEK_TIMEOUT_SECONDS", os.getenv("DEEPSEEK_TIMEOUT", "20"))
    try:
        return max(1.0, min(120.0, float(raw or 20)))
    except (TypeError, ValueError):
        return 20.0


def get_deepseek_profit_lab_config() -> dict[str, Any]:
    return {
        "enabled": _env_bool("DEEPSEEK_ENABLED", False),
        "api_key_configured": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip().rstrip("/") or DEFAULT_DEEPSEEK_BASE_URL,
        "model": os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL,
        "timeout_seconds": _timeout_seconds(),
        "max_items_per_review": max(1, min(_env_int("DEEPSEEK_MAX_ITEMS_PER_REVIEW", 5), 25)),
        "daily_report_enabled": _env_bool("DEEPSEEK_DAILY_REPORT_ENABLED", True),
        "disagreement_queue_enabled": _env_bool("DEEPSEEK_DISAGREEMENT_QUEUE_ENABLED", True),
    }


def _chat_completion_url(base_url: str) -> str:
    url = str(base_url or DEFAULT_DEEPSEEK_BASE_URL).rstrip("/")
    if url.endswith("/chat/completions") or url.endswith("/api/generate"):
        return url
    return f"{url}/chat/completions"


def _call_deepseek_json(prompt: str, *, config: Mapping[str, Any]) -> Any:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": "Return strict compact JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=float(config["timeout_seconds"])) as client:
        response = client.post(_chat_completion_url(str(config["base_url"])), headers=headers, json=body)
    response.raise_for_status()
    return extract_json_payload(response.json())


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


def _base_response(*, status: str, enabled: bool, deepseek_used: bool = False, ok: bool = True) -> dict[str, Any]:
    return {
        "ok": bool(ok),
        "status": status,
        "enabled": bool(enabled),
        "local_server_reachable": False,
        "json_schema_valid": False,
        "reviewer_side_effects": "none",
        "created_at": utc_now_iso(),
        "storage": get_storage_health(),
        **profit_lab_safety_flags(deepseek_used=deepseek_used),
    }


def build_profit_lab_input(
    *,
    candidate: Mapping[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    review_queue_summary: Mapping[str, Any] | None = None,
    calibration_summary: Mapping[str, Any] | None = None,
    outcome_summary: Mapping[str, Any] | None = None,
    provider_health_summary: Mapping[str, Any] | None = None,
    manifold_cluster_summary: Mapping[str, Any] | None = None,
    markov_hmm_summary: Mapping[str, Any] | None = None,
    sportsbook_full_board_summary: Mapping[str, Any] | None = None,
    stock_crypto_pattern_summary: Mapping[str, Any] | None = None,
    kalshi_prediction_market_summary: Mapping[str, Any] | None = None,
    small_account_summary: Mapping[str, Any] | None = None,
    security_readiness_summary: Mapping[str, Any] | None = None,
    strategy_readiness_summary: Mapping[str, Any] | None = None,
    trap_no_bet_summary: Mapping[str, Any] | None = None,
    disagreement_summary: Mapping[str, Any] | None = None,
    core_model_action: str | None = None,
) -> dict[str, Any]:
    payload = {
        "created_at": utc_now_iso(),
        "candidate": dict(candidate or {}),
        "candidates": list(candidates or ([] if candidate is None else [dict(candidate)])),
        "core_model_action": core_model_action,
        "review_queue_summary": dict(review_queue_summary or {}),
        "calibration_summary": dict(calibration_summary or {}),
        "outcome_summary": dict(outcome_summary or {}),
        "provider_health_summary": dict(provider_health_summary or {}),
        "manifold_cluster_summary": dict(manifold_cluster_summary or {}),
        "markov_hmm_summary": dict(markov_hmm_summary or {}),
        "sportsbook_full_board_summary": dict(sportsbook_full_board_summary or {}),
        "stock_crypto_pattern_summary": dict(stock_crypto_pattern_summary or {}),
        "kalshi_prediction_market_summary": dict(kalshi_prediction_market_summary or {}),
        "small_account_summary": dict(small_account_summary or {}),
        "security_readiness_summary": dict(security_readiness_summary or {}),
        "strategy_readiness_summary": dict(strategy_readiness_summary or {}),
        "trap_no_bet_summary": dict(trap_no_bet_summary or {}),
        "disagreement_summary": dict(disagreement_summary or {}),
        "safety_contract": {
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
            "raw_payloads_forbidden": True,
            "secrets_forbidden": True,
            "executable_payloads_forbidden": True,
        },
    }
    return compact_redacted_for_deepseek(payload, list_limit=25)


def collect_latest_profit_lab_summaries(*, base_data_dir: str = "data", limit: int = 10) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    queue_state = load_review_queue_state(config)
    review_items = [row for row in queue_state.get("items", []) if isinstance(row, dict)]
    cap = max(1, min(int(limit or 10), 100))
    calibration = build_calibration_report(base_data_dir=base, write_report=False)
    outcomes = load_outcome_state(base)
    outcome_records = list(outcomes.get("items", []))
    traps = compact_trap_report(load_trap_report(base_data_dir=base), limit=cap)
    disagreements = load_disagreement_queue(base_data_dir=base, limit=cap)
    return compact_redacted_for_deepseek(
        {
            "review_queue_summary": summarize_review_items(review_items),
            "review_queue_items": review_items[:cap],
            "calibration_summary": calibration,
            "outcome_summary": summarize_outcomes(outcome_records),
            "provider_health_summary": summarize_provider_health(config["providers"]),
            "trap_no_bet_summary": traps,
            "security_readiness_summary": build_security_readiness_report(base_data_dir=base),
            "disagreement_summary": {"count": disagreements.get("count", 0), "items": disagreements.get("items", [])[:cap]},
        },
        list_limit=cap,
    )


def _disabled_or_config_response(
    *,
    config: Mapping[str, Any],
    candidate: Mapping[str, Any] | None = None,
    status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    response = _base_response(status=status, enabled=bool(config.get("enabled")), deepseek_used=False, ok=True)
    response["json_schema_valid"] = True
    response["review"] = default_candidate_review(status=status, candidate=candidate, reason=reason, deepseek_used=False)
    response["candidate_review"] = response["review"]
    response["deepseek_status"] = status
    response["candidate_id"] = _candidate_id(candidate)
    if reason:
        response["rejected_reason"] = reason
    return response


def run_candidate_review(
    *,
    candidate: Mapping[str, Any] | None = None,
    core_model_action: str | None = None,
    enabled: bool | None = None,
    base_data_dir: str = "data",
    persist_disagreement: bool = True,
    summaries: Mapping[str, Any] | None = None,
    **summary_inputs: Any,
) -> dict[str, Any]:
    config = get_deepseek_profit_lab_config()
    if enabled is not None:
        config["enabled"] = bool(enabled)
    candidate = compact_redacted_for_deepseek(dict(candidate or {}), list_limit=25)
    summaries = dict(summaries or {})
    summaries.update({key: value for key, value in summary_inputs.items() if value not in (None, {}, [])})

    if not config["enabled"]:
        return _disabled_or_config_response(config=config, candidate=candidate, status="disabled")
    if not config["api_key_configured"]:
        return _disabled_or_config_response(
            config=config,
            candidate=candidate,
            status="config_missing",
            reason="missing_DEEPSEEK_API_KEY",
        )

    policy = evaluate_ai_provider("deepseek", base_data_dir=str(resolve_base_data_dir(base_data_dir)), persist_audit=False)
    if not bool(policy.get("ok")):
        return _disabled_or_config_response(
            config=config,
            candidate=candidate,
            status="provider_not_allowed",
            reason=str(policy.get("denial_reason") or "ai_provider_not_allowed"),
        )

    compact_input = build_profit_lab_input(
        candidate=candidate,
        core_model_action=core_model_action,
        **summaries,
    )
    prompt = build_candidate_review_prompt(compact_input)
    local_review = default_candidate_review(status="provider_unavailable", candidate=candidate, reason="deepseek_provider_unavailable")
    try:
        parsed = _call_deepseek_json(prompt, config=config)
        review, reason = validate_candidate_review(parsed, candidate=candidate)
    except httpx.TimeoutException:
        out = _base_response(status="provider_timeout", enabled=True, ok=False)
        out["review"] = default_candidate_review(status="provider_timeout", candidate=candidate, reason="deepseek_timeout")
        out["candidate_review"] = out["review"]
        out["rejected_reason"] = "provider_timeout"
        return out
    except (json.JSONDecodeError, ValueError):
        out = _base_response(status="invalid_json", enabled=True, ok=False)
        out["review"] = default_candidate_review(status="invalid_json", candidate=candidate, reason="invalid_deepseek_json")
        out["candidate_review"] = out["review"]
        out["rejected_reason"] = "invalid_deepseek_json"
        return out
    except Exception:
        out = _base_response(status="provider_error", enabled=True, ok=False)
        out["review"] = local_review
        out["candidate_review"] = local_review
        out["rejected_reason"] = "provider_error"
        return out

    if reason:
        out = _base_response(status="review_rejected", enabled=True, ok=False)
        out["local_server_reachable"] = True
        out["json_schema_valid"] = False
        out["rejected_reason"] = reason
        out["forbidden_actions_rejected"] = reason in {
            "execution_authority_violation",
            "provider_write_not_false",
            "execution_allowed_not_false",
            "live_execution_enabled_not_false",
            "auto_execution_not_false",
        }
        out["review"] = default_candidate_review(status="review_rejected", candidate=candidate, reason=reason)
        out["candidate_review"] = out["review"]
        return out

    out = _base_response(status="review_complete", enabled=True, deepseek_used=True, ok=True)
    out["local_server_reachable"] = True
    out["json_schema_valid"] = True
    out["review"] = review
    out["candidate_review"] = review
    out["deepseek_status"] = review["deepseek_status"]
    out["candidate_id"] = review["candidate_id"]
    if (
        persist_disagreement
        and bool(config.get("disagreement_queue_enabled", True))
        and should_record_disagreement(candidate, review, core_model_action=core_model_action)
    ):
        record = build_disagreement_record(candidate, review, core_model_action=core_model_action)
        out["disagreement"] = append_disagreement_record(record, base_data_dir=str(resolve_base_data_dir(base_data_dir)))
    return out


def run_red_team_review(
    *,
    candidates: list[dict[str, Any]] | None = None,
    candidate: Mapping[str, Any] | None = None,
    enabled: bool | None = None,
    base_data_dir: str = "data",
    **summary_inputs: Any,
) -> dict[str, Any]:
    config = get_deepseek_profit_lab_config()
    max_items = int(config["max_items_per_review"])
    rows = [row for row in (candidates or []) if isinstance(row, dict)]
    if candidate:
        rows = [dict(candidate)] + rows
    summaries = dict(summary_inputs)
    if not rows:
        latest = collect_latest_profit_lab_summaries(base_data_dir=base_data_dir, limit=max_items)
        summaries = {**latest, **summaries}
        rows = [row for row in latest.get("review_queue_items", []) if isinstance(row, dict)]
    rows = rows[:max_items]
    if not rows:
        out = _base_response(status="no_candidates", enabled=bool(enabled if enabled is not None else config["enabled"]), ok=True)
        out["reviews"] = []
        out["review_count"] = 0
        return out

    reviews = []
    disagreements = []
    for row in rows:
        review = run_candidate_review(
            candidate=row,
            core_model_action=str(row.get("core_model_action") or row.get("recommended_action") or ""),
            enabled=enabled,
            base_data_dir=base_data_dir,
            summaries=summaries,
        )
        reviews.append(review.get("candidate_review") or review.get("review"))
        if isinstance(review.get("disagreement"), Mapping):
            disagreements.append(review["disagreement"].get("record") or review["disagreement"])
    status = "red_team_complete" if any(bool(item.get("deepseek_used")) for item in reviews if isinstance(item, Mapping)) else "red_team_local_only"
    out = _base_response(status=status, enabled=bool(enabled if enabled is not None else config["enabled"]), deepseek_used=status == "red_team_complete", ok=True)
    out["reviews"] = reviews
    out["review_count"] = len(reviews)
    out["disagreements_recorded"] = len(disagreements)
    if disagreements:
        out["disagreements"] = disagreements[:10]
    return out


def run_daily_report(
    *,
    report_date: str | None = None,
    enabled: bool | None = None,
    persist_report: bool = True,
    base_data_dir: str = "data",
    summaries: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = get_deepseek_profit_lab_config()
    if enabled is not None:
        config["enabled"] = bool(enabled)
    day = report_date or utc_now_iso()[:10]
    compact_summaries = compact_redacted_for_deepseek(
        dict(summaries or collect_latest_profit_lab_summaries(base_data_dir=base_data_dir, limit=10)),
        list_limit=25,
    )

    if not config.get("daily_report_enabled", True):
        report = build_local_daily_report(compact_summaries, report_date=day, status="daily_report_disabled", reason="DEEPSEEK_DAILY_REPORT_ENABLED=false")
        out = _base_response(status="daily_report_disabled", enabled=bool(config["enabled"]), ok=True)
        out["report"] = report
        return out
    if not config["enabled"]:
        report = build_local_daily_report(compact_summaries, report_date=day, status="disabled")
        out = _base_response(status="disabled", enabled=False, ok=True)
        out["json_schema_valid"] = True
        out["report"] = report
        if persist_report:
            out["persistence"] = write_daily_report(report, base_data_dir=str(resolve_base_data_dir(base_data_dir)))
        return out
    if not config["api_key_configured"]:
        report = build_local_daily_report(compact_summaries, report_date=day, status="config_missing", reason="missing_DEEPSEEK_API_KEY")
        out = _base_response(status="config_missing", enabled=True, ok=True)
        out["json_schema_valid"] = True
        out["rejected_reason"] = "missing_DEEPSEEK_API_KEY"
        out["report"] = report
        if persist_report:
            out["persistence"] = write_daily_report(report, base_data_dir=str(resolve_base_data_dir(base_data_dir)))
        return out

    policy = evaluate_ai_provider("deepseek", base_data_dir=str(resolve_base_data_dir(base_data_dir)), persist_audit=False)
    if not bool(policy.get("ok")):
        report = build_local_daily_report(compact_summaries, report_date=day, status="provider_not_allowed", reason=str(policy.get("denial_reason")))
        out = _base_response(status="provider_not_allowed", enabled=True, ok=True)
        out["rejected_reason"] = str(policy.get("denial_reason") or "ai_provider_not_allowed")
        out["report"] = report
        return out

    prompt = build_daily_report_prompt({"date": day, **compact_summaries})
    try:
        parsed = _call_deepseek_json(prompt, config=config)
        report, reason = validate_daily_report(parsed, report_date=day)
    except httpx.TimeoutException:
        report = default_daily_report(status="provider_timeout", report_date=day, reason="deepseek_timeout")
        out = _base_response(status="provider_timeout", enabled=True, ok=False)
        out["rejected_reason"] = "provider_timeout"
        out["report"] = report
        return out
    except (json.JSONDecodeError, ValueError):
        report = default_daily_report(status="invalid_json", report_date=day, reason="invalid_deepseek_json")
        out = _base_response(status="invalid_json", enabled=True, ok=False)
        out["rejected_reason"] = "invalid_deepseek_json"
        out["report"] = report
        return out
    except Exception:
        report = default_daily_report(status="provider_error", report_date=day, reason="provider_error")
        out = _base_response(status="provider_error", enabled=True, ok=False)
        out["rejected_reason"] = "provider_error"
        out["report"] = report
        return out

    if reason:
        report = default_daily_report(status="review_rejected", report_date=day, reason=reason)
        out = _base_response(status="review_rejected", enabled=True, ok=False)
        out["local_server_reachable"] = True
        out["rejected_reason"] = reason
        out["report"] = report
        return out

    out = _base_response(status="daily_report_complete", enabled=True, deepseek_used=True, ok=True)
    out["local_server_reachable"] = True
    out["json_schema_valid"] = True
    out["report"] = report
    if persist_report:
        out["persistence"] = write_daily_report(report, base_data_dir=str(resolve_base_data_dir(base_data_dir)))
    return out
