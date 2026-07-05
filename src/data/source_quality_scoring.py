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

QUALITY_TIERS = (
    "unusable",
    "research_only",
    "candidate",
    "usable_after_review",
    "high_priority_adapter",
    "institutional_priority",
)


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
    source_category = str(source.get("source_category") or source.get("category") or "")
    module = str(source.get("module") or source.get("module_lane") or source.get("lane_id") or "")
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

    forbidden_actions = list(source.get("forbidden_actions") or [])
    trading_capable = bool(source.get("requires_execution_account") or source.get("requires_brokerage_account") or source.get("requires_sportsbook_account") or forbidden_actions)
    blocked = access_type in FUTURE_ONLY_ACCESS_TYPES or any(bool(source.get(flag, False)) for flag in BLOCKING_FLAGS)
    unknown_terms = terms_risk >= 70
    current_phase_allowed = (
        bool(source.get("current_phase_allowed", False))
        and access_type in CURRENT_PHASE_ACCESS_TYPES
        and not blocked
        and not bool(source.get("requires_provider_write", False))
        and not bool(source.get("execution_allowed", False))
        and not trading_capable
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
    if access_type in {"open_public", "free_key", "free_tier", "open_dataset"} and not trading_capable:
        future_value = max(future_value, 60)

    adapter_complexity = 45
    if access_type in {"open_dataset", "open_public"}:
        adapter_complexity = 25
    if bool(source.get("requires_oauth", False)):
        adapter_complexity = max(adapter_complexity, 70)
    if access_type in FUTURE_ONLY_ACCESS_TYPES:
        adapter_complexity = max(adapter_complexity, 80)
    calibration_value = _clamp((quality_signal := (len(outcome_fields) * 12 + len(historical_fields) * 7 + len(join_keys) * 8)) + (30 if coverage.get("historical") else 0) + (25 if coverage.get("final_results") or coverage.get("settlements") else 0))
    stock_signal = 0
    if source_category in {"finance", "stock/fundamentals", "macro/rates/bonds"} or module in {"stocks", "ETFs", "institutional_stock_pro_analyst"}:
        stock_signal = _clamp(
            (25 if coverage.get("fundamentals") else 0)
            + (20 if coverage.get("historical") else 0)
            + (15 if coverage.get("live") else 0)
            + (20 if "fundamentals" in supported_inputs else 0)
            + (20 if "sec_filings" in supported_inputs or "earnings" in supported_inputs else 0)
        )
    crypto_signal = 0
    if source_category == "crypto" or module == "cryptocurrency_edge_lab":
        crypto_signal = _clamp(
            (25 if coverage.get("historical") else 0)
            + (20 if coverage.get("live") else 0)
            + (20 if "ohlcv" in supported_inputs else 0)
            + (15 if "order_book_depth" in supported_inputs else 0)
            + (15 if "onchain_signals" in supported_inputs or "tvl" in supported_inputs else 0)
            + (15 if not trading_capable else 0)
        )

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
        "adapter_complexity_score": _clamp(adapter_complexity),
        "calibration_value_score": calibration_value,
        "stock_signal_value_score": stock_signal,
        "fundamental_depth_score": _clamp(80 if coverage.get("fundamentals") or "fundamentals" in supported_inputs else 15),
        "valuation_coverage_score": _clamp(75 if "valuation" in supported_inputs or coverage.get("fundamentals") else 10),
        "earnings_event_score": _clamp(75 if "earnings" in supported_inputs else 10),
        "SEC_mapping_score": _clamp(85 if "sec_filings" in supported_inputs or "cik" in join_keys else 10),
        "liquidity_market_depth_score": _clamp(75 if coverage.get("live") and ("volume" in supported_inputs or "order_book_depth" in supported_inputs) else 25),
        "crypto_signal_value_score": crypto_signal,
        "exchange_depth_score": _clamp(80 if "exchange_volume" in supported_inputs or "order_book_depth" in supported_inputs else 15),
        "onchain_depth_score": _clamp(80 if "onchain_signals" in supported_inputs else 15),
        "order_book_depth_score": _clamp(80 if "order_book_depth" in supported_inputs else 15),
        "funding_open_interest_score": _clamp(80 if "funding_rates" in supported_inputs or "open_interest" in supported_inputs else 10),
        "dex_liquidity_score": _clamp(80 if "dex_liquidity" in supported_inputs or "tvl" in supported_inputs else 10),
        "stablecoin_flow_score": _clamp(80 if "stablecoin_flows" in supported_inputs else 10),
    }
    quality["quality_tier"] = quality_tier(quality, source)
    return quality


def quality_tier(quality: dict[str, Any], source: dict[str, Any] | None = None) -> str:
    source = source or {}
    access_type = str(source.get("source_access_type") or "")
    if any(bool(source.get(flag, False)) for flag in BLOCKING_FLAGS) or access_type in {"unknown"}:
        return "unusable"
    if int(quality.get("terms_risk_score") or 0) >= 70:
        return "candidate"
    usability = int(quality.get("current_phase_usability_score") or 0)
    future_value = int(quality.get("future_value_score") or 0)
    calibration_value = int(quality.get("calibration_value_score") or 0)
    signal_value = max(int(quality.get("stock_signal_value_score") or 0), int(quality.get("crypto_signal_value_score") or 0))
    if usability >= 90 or (future_value >= 85 and calibration_value >= 75 and signal_value >= 70):
        return "institutional_priority"
    if usability >= 75 or (future_value >= 75 and signal_value >= 60):
        return "high_priority_adapter"
    if usability >= 55:
        return "usable_after_review"
    if future_value >= 35:
        return "research_only"
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
