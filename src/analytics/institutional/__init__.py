from __future__ import annotations

import re
from typing import Any, Callable

ACTIVATION_TIERS = (
    "research_only",
    "backtest_ready",
    "paper_trade_ready",
    "review_queue_ready",
    "active_scoring_ready",
)

MODEL_CLASSIFICATIONS = (
    "alpha_model",
    "risk_model",
    "allocation_model",
    "execution_model",
    "liability_model",
    "regime_model",
    "validation_model",
    "reporting_model",
)

DEFAULT_ACTIVATION_STATUS = "research_only"

PROMOTION_RULES = {
    "research_only": "Promote to backtest_ready only when required inputs and tests exist.",
    "backtest_ready": "Promote to paper_trade_ready only after out-of-sample validation.",
    "paper_trade_ready": "Promote to review_queue_ready only after performance monitoring.",
    "review_queue_ready": "Promote to active_scoring_ready only after calibration, drawdown, and governance checks.",
}

REVIEW_QUEUE_FIELDS = (
    "institutional_model_family",
    "institutional_model_purpose",
    "institutional_model_status",
    "institutional_model_evidence_score",
    "institutional_model_risk_rating",
    "institutional_model_router_reason",
    "portfolio_construction_score",
    "risk_attribution_score",
    "execution_cost_score",
    "liability_alignment_score",
    "macro_regime_score",
    "tax_aware_score",
    "governance_score",
)


def make_model(
    name: str,
    classification: str,
    mathematical_purpose: str,
    required_inputs: list[str],
    output_fields: list[str],
    assumptions: list[str],
    limitations: list[str],
    evidence_standard: str,
    applicable_markets: list[str],
    review_queue_scoring_reason: str,
    activation_status: str = DEFAULT_ACTIVATION_STATUS,
) -> dict[str, Any]:
    if classification not in MODEL_CLASSIFICATIONS:
        raise ValueError(f"Unsupported institutional model classification: {classification}")
    if activation_status not in ACTIVATION_TIERS:
        raise ValueError(f"Unsupported activation tier: {activation_status}")
    return {
        "name": name,
        "classification": classification,
        "mathematical_purpose": mathematical_purpose,
        "required_inputs": required_inputs,
        "output_fields": output_fields,
        "assumptions": assumptions,
        "limitations": limitations,
        "evidence_standard": evidence_standard,
        "activation_status": activation_status,
        "applicable_markets": applicable_markets,
        "review_queue_scoring_reason": review_queue_scoring_reason,
    }


def normalize_weights(values: list[float]) -> list[float]:
    if not values:
        return []
    total = sum(max(value, 0.0) for value in values)
    if total <= 0:
        return [round(1.0 / len(values), 6) for _ in values]
    return [round(max(value, 0.0) / total, 6) for value in values]


def clamp_score(value: Any, minimum: float = 0.0, maximum: float = 100.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = minimum
    return max(minimum, min(maximum, numeric))


def build_output(output_fields: list[str], values: dict[str, Any]) -> dict[str, Any]:
    return {field: values.get(field) for field in output_fields}


def missing_inputs(available_inputs: dict[str, Any], required_inputs: list[str]) -> list[str]:
    missing: list[str] = []
    for field in required_inputs:
        value = available_inputs.get(field)
        if value is None:
            missing.append(field)
    return missing


def tier_allows_review_queue(activation_status: str) -> bool:
    return activation_status in {"review_queue_ready", "active_scoring_ready"}


def ensure_no_banned_language(payload: Any) -> bool:
    banned_words = ("lock", "guaranteed", "risk-free", "sure thing", "can't lose", "cant lose")
    rendered = repr(payload).lower()
    return not any(re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", rendered) for word in banned_words)


def combine_model_maps(*maps: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    for mapping in maps:
        combined.update(mapping)
    return combined


def evaluate_registry_entry(
    models: dict[str, dict[str, Any]],
    evaluator: Callable[[str, dict[str, Any]], dict[str, Any]],
    model_name: str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    if model_name not in models:
        raise KeyError(f"Unknown institutional model: {model_name}")
    missing = missing_inputs(inputs, models[model_name]["required_inputs"])
    if missing:
        return {"status": "inactive_missing_inputs", "missing_inputs": missing}
    result = evaluator(model_name, inputs)
    result["status"] = "ok"
    return result
