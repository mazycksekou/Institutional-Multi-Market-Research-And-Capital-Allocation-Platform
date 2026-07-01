from __future__ import annotations

from typing import Any, Mapping

from src.brokerage.readiness import evaluate_future_execution_eligibility
from src.security.secret_safety import redact_sensitive, secret_safety_fields
from src.security.policy import detect_execution_authority_violations, locked_safety_flags
from .strategy_disagreement import append_strategy_disagreement, build_strategy_disagreement_record
from .strategy_registry import get_strategy_registry
from .strategy_router import route_strategies


ALLOWED_REVIEW_STATUSES = {
    "NO_REVIEW",
    "LOW_PRIORITY_REVIEW",
    "WATCHLIST_REVIEW",
    "ACTIVE_REVIEW",
    "DATA_INSUFFICIENT",
    "NO_BET",
    "NO_TRADE",
    "NO_TRADE_SESSION_LOCK",
    "REVIEW_ONLY",
}

_NO_BET_MARKETS = {"sportsbook", "sports_player_props", "sports_totals", "sports_pregame_main", "prediction_market", "kalshi"}
_RED_TEAM_FAMILIES = {"deepseek_red_team", "openai_optional_red_team", "topological_red_team", "extreme_randomness_red_team"}


def _score(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def _norm_action(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text if text in ALLOWED_REVIEW_STATUSES else "NO_REVIEW"


def _output_for(strategy_id: str, strategy_outputs: Mapping[str, Any] | list[Mapping[str, Any]] | None) -> dict[str, Any]:
    if isinstance(strategy_outputs, Mapping):
        value = strategy_outputs.get(strategy_id, {})
        return redact_sensitive(dict(value)) if isinstance(value, Mapping) else {}
    if isinstance(strategy_outputs, list):
        for item in strategy_outputs:
            if isinstance(item, Mapping) and item.get("strategy_id") == strategy_id:
                return redact_sensitive(dict(item))
    return {}


def _strategy_weight(strategy: Mapping[str, Any]) -> float:
    maturity = str(strategy.get("maturity_status") or "")
    family = str(strategy.get("strategy_family") or strategy.get("strategy_id") or "")
    if family in _RED_TEAM_FAMILIES or "red_team" in family:
        return 0.0
    if maturity == "active_ranking":
        return 1.25
    if maturity == "active_review":
        return 1.0
    if maturity == "calibration_only":
        return 0.25
    return 0.0


def _review_status(weighted_score: float, confidence: float, red_team_penalty: float, safety_penalty: float, missing_required: bool) -> str:
    if safety_penalty >= 100:
        return "NO_TRADE"
    if missing_required:
        return "DATA_INSUFFICIENT"
    adjusted = weighted_score - safety_penalty
    if adjusted >= 80 and confidence >= 45:
        return "ACTIVE_REVIEW"
    if adjusted >= 65:
        return "WATCHLIST_REVIEW"
    if adjusted >= 45:
        return "LOW_PRIORITY_REVIEW"
    return "NO_REVIEW"


def aggregate_strategy_scores(
    candidate: Mapping[str, Any] | None = None,
    *,
    routed: Mapping[str, Any] | None = None,
    strategy_outputs: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    create_disagreements: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    routing = dict(routed or route_strategies(safe_candidate))
    registry = get_strategy_registry()
    selected = list(routing.get("selected_strategies") or [])
    blocked = list(routing.get("blocked_strategies") or [])
    skipped = list(routing.get("skipped_strategies") or [])
    strategy_scores: dict[str, float] = {}
    weights: dict[str, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0
    confidence_values: list[float] = []
    edge_values: list[float] = []
    liquidity_risks: list[float] = []
    trap_risks: list[float] = []
    calibration_values: list[float] = []
    red_team_penalty = 0.0
    safety_penalty = 0.0
    fatal_safety_blocker = bool(safe_candidate.get("fatal_safety_blocker"))
    positive_ids: list[str] = []
    negative_ids: list[str] = []
    disagreement_records: list[dict[str, Any]] = []
    missing_required = bool(blocked) and not selected

    for row in selected:
        strategy_id = str(row.get("strategy_id"))
        strategy = registry.get(strategy_id, {})
        out = _output_for(strategy_id, strategy_outputs)
        violations = detect_execution_authority_violations(out)
        if violations:
            safety_penalty = max(safety_penalty, 100.0)
            fatal_safety_blocker = True
            negative_ids.append(strategy_id)
        family = str(row.get("strategy_family") or strategy.get("strategy_family") or strategy_id)
        score = _score(
            out.get("score")
            if out.get("score") is not None
            else out.get("review_priority_score")
            if out.get("review_priority_score") is not None
            else out.get("edge_quality_score"),
            50.0 if row.get("can_affect_review") else 0.0,
        )
        weight = _strategy_weight({**strategy, **row})
        is_red_team = family in _RED_TEAM_FAMILIES or "red_team" in family
        if is_red_team:
            action = _norm_action(out.get("recommended_action"))
            warning = bool(out.get("red_team_warning")) or action in {"NO_BET", "NO_TRADE", "DATA_INSUFFICIENT"}
            penalty = _score(out.get("red_team_penalty"), 25.0 if warning else 0.0)
            red_team_penalty = max(red_team_penalty, penalty)
            if warning:
                negative_ids.append(strategy_id)
            if bool(out.get("fatal_safety_blocker")):
                safety_penalty = max(safety_penalty, 100.0)
                fatal_safety_blocker = True
            score = 0.0
            weight = 0.0
        else:
            if score >= 75 and weight > 0:
                positive_ids.append(strategy_id)
            if score <= 35 and weight > 0:
                negative_ids.append(strategy_id)
        strategy_scores[strategy_id] = score
        weights[strategy_id] = weight
        weighted_sum += score * weight
        total_weight += weight
        if weight > 0 and not is_red_team:
            confidence_values.append(_score(out.get("confidence_score"), score))
            edge_values.append(_score(out.get("edge_quality_score"), score))
            calibration_values.append(_score(out.get("calibration_support_score"), _score(strategy.get("outcome_coverage"), 0.0) * 100.0))
        liquidity_risks.append(_score(out.get("liquidity_risk_score"), _score(safe_candidate.get("liquidity_risk_score"), 50.0)))
        trap_risks.append(_score(out.get("trap_risk_score"), _score(safe_candidate.get("trap_risk_score"), 50.0)))

    weighted_score = weighted_sum / total_weight if total_weight else 0.0
    confidence = (sum(confidence_values) / len(confidence_values)) if confidence_values else 0.0
    edge_quality = (sum(edge_values) / len(edge_values)) if edge_values else weighted_score
    liquidity_risk = max(liquidity_risks) if liquidity_risks else _score(safe_candidate.get("liquidity_risk_score"), 50.0)
    trap_risk = max(trap_risks) if trap_risks else _score(safe_candidate.get("trap_risk_score"), 50.0)
    calibration_support = max(calibration_values) if calibration_values else 0.0
    uncertainty_penalty = max(0.0, 100.0 - confidence) * 0.2
    if fatal_safety_blocker:
        safety_penalty = max(safety_penalty, 100.0)

    recommended = _review_status(weighted_score, confidence, red_team_penalty, safety_penalty, missing_required)
    market_type = str(safe_candidate.get("market_type") or safe_candidate.get("source_type") or "").lower()
    if safety_penalty >= 100:
        recommended = "NO_BET" if market_type in _NO_BET_MARKETS else "NO_TRADE"
    elif red_team_penalty >= 50:
        recommended = "LOW_PRIORITY_REVIEW" if recommended in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"} else recommended
    elif red_team_penalty >= 25 and recommended == "ACTIVE_REVIEW":
        recommended = "WATCHLIST_REVIEW"

    if positive_ids and negative_ids:
        record = build_strategy_disagreement_record(
            candidate=safe_candidate,
            strategy_a=positive_ids[0],
            strategy_b=negative_ids[0],
            core_model_action=safe_candidate.get("recommended_action") or "ACTIVE_REVIEW",
            strategy_action=recommended,
            disagreement_type="strategy_score_conflict",
            disagreement_reasons=["positive_strategy_conflicts_with_negative_or_red_team_signal"],
            strategy_ids=positive_ids[:5] + negative_ids[:5],
        )
        if create_disagreements:
            append_strategy_disagreement(record, base_data_dir=base_data_dir)
        disagreement_records.append(record)

    future = evaluate_future_execution_eligibility(
        safe_candidate,
        aggregate={
            "weighted_score": weighted_score,
            "calibration_support_score": calibration_support,
            "liquidity_risk_score": liquidity_risk,
            "trap_risk_score": trap_risk,
            "fatal_safety_blocker": fatal_safety_blocker,
        },
    )
    return {
        "ok": True,
        "status": "strategy_scores_aggregated",
        "candidate_id": safe_candidate.get("candidate_id") or safe_candidate.get("id") or safe_candidate.get("ticker"),
        "selected_strategies": [row.get("strategy_id") for row in selected],
        "skipped_strategies": [row.get("strategy_id") for row in skipped],
        "blocked_strategies": [row.get("strategy_id") for row in blocked],
        "strategy_scores": strategy_scores,
        "strategy_weights": weights,
        "weighted_score": round(weighted_score, 4),
        "confidence_score": round(confidence, 4),
        "edge_quality_score": round(edge_quality, 4),
        "liquidity_risk_score": round(liquidity_risk, 4),
        "trap_risk_score": round(trap_risk, 4),
        "calibration_support_score": round(calibration_support, 4),
        "uncertainty_penalty": round(uncertainty_penalty, 4),
        "red_team_penalty": round(red_team_penalty, 4),
        "safety_penalty": round(safety_penalty, 4),
        "fatal_safety_blocker": bool(fatal_safety_blocker),
        "final_review_priority": recommended,
        "recommended_review_status": recommended,
        "future_execution_eligible": bool(future.get("future_execution_eligible", False)),
        "future_execution_blockers": list(future.get("future_execution_blockers") or [])[:20],
        "disagreement_records_created": len(disagreement_records),
        "disagreement_records": disagreement_records[:5],
        "universal_strategy_agreement_required": False,
        "missing_optional_strategy_blocks_review": False,
        **secret_safety_fields(source_payload=candidate, redacted_payload=safe_candidate),
        **locked_safety_flags(),
    }
