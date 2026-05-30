from __future__ import annotations

from typing import Any


CURRENT_PHASE_ACCESS_TYPES = {
    "open_public",
    "free_key",
    "free_tier",
    "open_dataset",
    "public_wrapper_with_terms_review",
    "manual_import",
}

FUTURE_ONLY_ACCESS_TYPES = {
    "paid_candidate",
    "partner_candidate",
    "institutional_vendor_candidate",
    "broker_data_candidate",
    "sportsbook_account_candidate",
    "internal_proprietary_candidate",
}

BLOCKING_FLAGS = {
    "requires_provider_write",
    "requires_execution_account",
    "requires_brokerage_account",
    "requires_sportsbook_account",
    "requires_paid_subscription",
    "trial_only",
    "credit_card_required",
}

QUALITY_TIERS = ("unusable", "candidate", "usable", "strong", "institutional")


def _clamp(value: float | int | None) -> int:
    if value is None:
        return 0
    return int(max(0, min(100, round(float(value)))))


def _bool_count(values: dict[str, Any]) -> tuple[int, int]:
    total = len(values)
    if total <= 0:
        return 0, 0
    return sum(1 for value in values.values() if bool(value)), total


def _cadence_score(cadence: str | None) -> int:
    return {
        "live": 100,
        "near_live": 88,
        "daily": 72,
        "weekly": 48,
        "seasonal": 30,
        "historical_only": 35,
        "unknown": 10,
    }.get(str(cadence or "unknown"), 10)


def score_source(source: dict[str, Any], required_inputs: list[str] | None = None) -> dict[str, Any]:
    access_type = str(source.get("source_access_type") or "unknown")
    coverage = dict(source.get("coverage") or {})
    freshness = dict(source.get("freshness") or {})
    limits = dict(source.get("limits") or {})
    legal_terms = dict(source.get("legal_terms") or {})
    mapping = dict(source.get("model_mapping") or {})
    required = list(required_inputs or [])
    supported_inputs = set(mapping.get("model_inputs_supported") or [])
    missing_required = [item for item in required if item not in supported_inputs]
    present, total = _bool_count(coverage)
    completeness_score = _clamp((present / total) * 100 if total else 0)
    coverage_score = _clamp(((len(required) - len(missing_required)) / len(required)) * 100 if required else completeness_score)
    outcome_fields = list(mapping.get("outcome_fields_available") or [])
    historical_fields = list(mapping.get("historical_backfill_fields_available") or [])
    join_keys = list(mapping.get("join_keys") or [])

    terms_risk = 20
    if bool(source.get("requires_terms_review", False)) or bool(legal_terms.get("requires_manual_review", False)):
        terms_risk = 82
    if bool(legal_terms.get("commercial_use_unclear", False)):
        terms_risk = max(terms_risk, 72)
    if access_type == "unknown":
        terms_risk = max(terms_risk, 88)
    if access_type in FUTURE_ONLY_ACCESS_TYPES:
        terms_risk = max(terms_risk, 65)

    rate_limit_risk = 35 if bool(limits.get("rate_limit_known", False)) else 65
    if bool(limits.get("throttle_required", True)):
        rate_limit_risk = max(rate_limit_risk, 55)
    if access_type in {"open_dataset", "manual_import"}:
        rate_limit_risk = min(rate_limit_risk, 25)

    blocked = access_type in FUTURE_ONLY_ACCESS_TYPES or any(bool(source.get(flag, False)) for flag in BLOCKING_FLAGS)
    unknown_terms = terms_risk >= 70
    current_phase_allowed = (
        bool(source.get("current_phase_allowed", False))
        and access_type in CURRENT_PHASE_ACCESS_TYPES
        and not blocked
        and not bool(source.get("requires_provider_write", False))
    )
    approved = str(source.get("approval_status") or "candidate") == "approved_for_research"
    current_usability = 0
    if current_phase_allowed and approved and not unknown_terms:
        current_usability = _clamp((coverage_score * 0.35) + (_cadence_score(freshness.get("expected_update_cadence")) * 0.2) + ((100 - terms_risk) * 0.25) + ((100 - rate_limit_risk) * 0.2))
    elif current_phase_allowed and not blocked:
        current_usability = _clamp(min(45, (coverage_score * 0.25) + ((100 - terms_risk) * 0.25)))

    future_value = _clamp((coverage_score * 0.35) + (completeness_score * 0.2) + (len(historical_fields) * 6) + (len(outcome_fields) * 8) + (len(join_keys) * 5))
    if access_type in FUTURE_ONLY_ACCESS_TYPES:
        future_value = max(future_value, 45)

    quality = {
        "source_reliability_score": _clamp(70 if approved else 45 if access_type != "unknown" else 15),
        "freshness_score": _cadence_score(freshness.get("expected_update_cadence")),
        "coverage_score": coverage_score,
        "completeness_score": completeness_score,
        "join_quality_score": _clamp(25 + len(join_keys) * 25 if join_keys else 10),
        "model_input_fill_rate": coverage_score,
        "terms_risk_score": _clamp(terms_risk),
        "rate_limit_risk_score": _clamp(rate_limit_risk),
        "historical_depth_score": _clamp(70 if coverage.get("historical") or historical_fields else 10),
        "outcome_availability_score": _clamp(80 if coverage.get("final_results") or coverage.get("settlements") or outcome_fields else 10),
        "external_research_priority_score": 0,
        "current_phase_usability_score": current_usability,
        "future_value_score": future_value,
    }
    quality["quality_tier"] = quality_tier(quality, source)
    return quality


def quality_tier(quality: dict[str, Any], source: dict[str, Any] | None = None) -> str:
    source = source or {}
    if any(bool(source.get(flag, False)) for flag in BLOCKING_FLAGS) or str(source.get("source_access_type") or "") in {"unknown"}:
        return "unusable"
    if int(quality.get("terms_risk_score") or 0) >= 70:
        return "candidate"
    usability = int(quality.get("current_phase_usability_score") or 0)
    if usability >= 90:
        return "institutional"
    if usability >= 75:
        return "strong"
    if usability >= 55:
        return "usable"
    return "candidate"


def score_lane(lane: dict[str, Any]) -> dict[str, int]:
    candidates = list(lane.get("source_candidates") or [])
    verified = list(lane.get("verified_sources") or [])
    sources = verified + candidates + list(lane.get("future_source_candidates") or [])
    if not sources:
        return {
            "coverage_score": 0,
            "freshness_score": 0,
            "outcome_availability_score": 0,
            "terms_risk_score": 100,
            "external_research_priority_score": 95,
        }
    qualities = [dict(src.get("quality") or score_source(src, lane.get("required_model_inputs") or [])) for src in sources]
    def avg(field: str) -> int:
        values = [int(q.get(field) or 0) for q in qualities]
        return _clamp(sum(values) / len(values) if values else 0)

    has_verified = bool(verified)
    has_terms_block = any(int(q.get("terms_risk_score") or 0) >= 70 for q in qualities)
    return {
        "coverage_score": max(int(q.get("coverage_score") or 0) for q in qualities),
        "freshness_score": max(int(q.get("freshness_score") or 0) for q in qualities),
        "outcome_availability_score": max(int(q.get("outcome_availability_score") or 0) for q in qualities),
        "terms_risk_score": avg("terms_risk_score"),
        "external_research_priority_score": _clamp(85 if not has_verified else 35 if has_terms_block else 15),
    }
