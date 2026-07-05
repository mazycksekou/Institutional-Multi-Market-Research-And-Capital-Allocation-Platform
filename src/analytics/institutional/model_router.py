from __future__ import annotations

from typing import Any

from . import REVIEW_QUEUE_FIELDS, combine_model_maps, tier_allows_review_queue
from .alternative_investments import get_models as get_alternative_models
from .credit_risk_models import get_models as get_credit_models
from .derivatives_hedging import get_models as get_derivatives_models
from .execution_cost_models import get_models as get_execution_models
from .factor_risk_models import get_models as get_factor_models
from .fixed_income_rates import get_models as get_fixed_income_models
from .liability_retirement_models import get_models as get_liability_models
from .macro_regime_models import get_models as get_macro_models
from .model_governance import get_models as get_governance_models
from .performance_attribution import get_models as get_performance_models
from .portfolio_construction import get_models as get_portfolio_models
from .tax_aware_models import get_models as get_tax_models

SPORTSBOOK_MARKETS = {"sportsbook", "sports", "betting", "moneyline", "spread", "total"}
SHORT_HORIZONS = {"intraday", "same_day", "short_term"}
LONG_HORIZONS = {"multi_month", "annual", "strategic", "long_term", "retirement"}


def get_model_library() -> dict[str, dict[str, Any]]:
    return combine_model_maps(
        get_portfolio_models(),
        get_factor_models(),
        get_liability_models(),
        get_fixed_income_models(),
        get_credit_models(),
        get_derivatives_models(),
        get_execution_models(),
        get_alternative_models(),
        get_macro_models(),
        get_tax_models(),
        get_performance_models(),
        get_governance_models(),
    )


def _purpose_matches(model: dict[str, Any], requested_purpose: str) -> bool:
    requested = requested_purpose.lower()
    return requested in model["classification"] or requested in model["name"] or requested in model["mathematical_purpose"].lower()


def _market_matches(model: dict[str, Any], market_type: str) -> bool:
    market = market_type.lower()
    return "all" in model["applicable_markets"] or market in {value.lower() for value in model["applicable_markets"]}


def _blocked_for_context(model: dict[str, Any], market_type: str, horizon: str, risk_constraints_ok: bool) -> str | None:
    market = market_type.lower()
    horizon_name = horizon.lower()
    classification = model["classification"]
    if market in SPORTSBOOK_MARKETS:
        return "institutional_models_do_not_create_sportsbook_recommendations"
    if classification == "allocation_model" and horizon_name in SHORT_HORIZONS:
        return "allocation_model_blocked_for_short_horizon"
    if classification == "liability_model" and horizon_name in SHORT_HORIZONS:
        return "liability_model_blocked_for_short_horizon"
    if classification == "reporting_model" and horizon_name in SHORT_HORIZONS:
        return "reporting_model_blocked_for_short_horizon"
    if classification == "alpha_model" and not risk_constraints_ok:
        return "alpha_model_cannot_override_risk_or_liability_constraints"
    return None


def route_models(
    market_type: str,
    horizon: str,
    purpose: str,
    available_inputs: dict[str, Any],
    risk_constraints_ok: bool = True,
) -> dict[str, Any]:
    if market_type.lower() in SPORTSBOOK_MARKETS:
        return {
            "eligible_models": [],
            "blocked_models": [{"name": "institutional_library", "reason": "institutional_models_do_not_create_sportsbook_recommendations"}],
            "missing_inputs": [],
            "routing_reason": "institutional_models_do_not_create_sportsbook_recommendations",
        }
    library = get_model_library()
    eligible_models: list[dict[str, Any]] = []
    blocked_models: list[dict[str, Any]] = []
    missing: set[str] = set()
    reasons: list[str] = []

    for model in library.values():
        if not _market_matches(model, market_type):
            continue
        if purpose and not _purpose_matches(model, purpose):
            continue
        block_reason = _blocked_for_context(model, market_type, horizon, risk_constraints_ok)
        if block_reason:
            blocked_models.append({"name": model["name"], "reason": block_reason})
            reasons.append(block_reason)
            continue
        missing_inputs = [field for field in model["required_inputs"] if available_inputs.get(field) is None]
        if missing_inputs:
            missing.update(missing_inputs)
            blocked_models.append({"name": model["name"], "reason": "missing_inputs", "missing_inputs": missing_inputs})
            continue
        eligible_models.append(model)

    routing_reason = "; ".join(sorted(set(reasons))) if reasons else "eligible_models_identified_for_context"
    return {
        "eligible_models": eligible_models,
        "blocked_models": blocked_models,
        "missing_inputs": sorted(missing),
        "routing_reason": routing_reason,
    }


def institutional_review_fields(
    model: dict[str, Any],
    *,
    evidence_score: float,
    input_quality_score: float,
    model_risk_rating: str,
    router_reason: str,
    relevant_to_market: bool,
) -> dict[str, Any]:
    if not tier_allows_review_queue(model["activation_status"]):
        return {}
    if evidence_score < 70 or input_quality_score < 75:
        return {}
    if model_risk_rating.lower() not in {"low", "moderate"}:
        return {}
    if not relevant_to_market:
        return {}
    payload = {
        "institutional_model_family": model["name"],
        "institutional_model_purpose": model["classification"],
        "institutional_model_status": model["activation_status"],
        "institutional_model_evidence_score": evidence_score,
        "institutional_model_risk_rating": model_risk_rating,
        "institutional_model_router_reason": router_reason,
        "portfolio_construction_score": 0,
        "risk_attribution_score": 0,
        "execution_cost_score": 0,
        "liability_alignment_score": 0,
        "macro_regime_score": 0,
        "tax_aware_score": 0,
        "governance_score": 0,
    }
    if model["classification"] == "allocation_model":
        payload["portfolio_construction_score"] = evidence_score
    elif model["classification"] == "risk_model":
        payload["risk_attribution_score"] = evidence_score
    elif model["classification"] == "execution_model":
        payload["execution_cost_score"] = evidence_score
    elif model["classification"] == "liability_model":
        payload["liability_alignment_score"] = evidence_score
    elif model["classification"] == "regime_model":
        payload["macro_regime_score"] = evidence_score
    elif "tax" in model["name"]:
        payload["tax_aware_score"] = evidence_score
    elif model["classification"] == "validation_model":
        payload["governance_score"] = evidence_score
    return {field: payload[field] for field in REVIEW_QUEUE_FIELDS}
