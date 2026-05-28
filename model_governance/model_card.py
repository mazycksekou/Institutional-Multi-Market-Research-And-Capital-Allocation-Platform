from __future__ import annotations

from typing import Any

from . import contains_banned_language
from .activation_tiers import default_activation_tier

REQUIRED_FIELDS = (
    "model_id",
    "model_name",
    "version",
    "purpose",
    "market_type",
    "time_horizon",
    "research_basis",
    "mathematical_summary",
    "inputs",
    "outputs",
    "assumptions",
    "limitations",
    "known_failure_modes",
    "data_quality_requirements",
    "calibration_requirements",
    "backtest_requirements",
    "risk_controls",
    "human_review_requirements",
    "activation_tier",
    "last_validated_at",
    "validation_status",
)


def create_model_card(**kwargs: Any) -> dict[str, Any]:
    card = {
        "model_id": kwargs["model_id"],
        "model_name": kwargs["model_name"],
        "version": kwargs.get("version", "1.0"),
        "purpose": kwargs["purpose"],
        "market_type": kwargs["market_type"],
        "time_horizon": kwargs["time_horizon"],
        "research_basis": kwargs["research_basis"],
        "mathematical_summary": kwargs["mathematical_summary"],
        "inputs": list(kwargs["inputs"]),
        "outputs": list(kwargs["outputs"]),
        "assumptions": list(kwargs["assumptions"]),
        "limitations": list(kwargs["limitations"]),
        "known_failure_modes": list(kwargs.get("known_failure_modes", [])),
        "data_quality_requirements": kwargs.get("data_quality_requirements", "Documented required inputs and freshness thresholds."),
        "calibration_requirements": kwargs.get("calibration_requirements", "Calibration evidence must be available before promotion."),
        "backtest_requirements": kwargs.get("backtest_requirements", "Backtests must include realistic costs."),
        "risk_controls": kwargs.get("risk_controls", "Human review and risk gates remain mandatory."),
        "human_review_requirements": kwargs.get("human_review_requirements", "Human approval is required for all actionable usage."),
        "activation_tier": kwargs.get("activation_tier", default_activation_tier()),
        "last_validated_at": kwargs.get("last_validated_at", ""),
        "validation_status": kwargs.get("validation_status", "research_pending"),
    }
    return card


def validate_model_card(card: dict[str, Any]) -> dict[str, Any]:
    missing_fields = [field for field in REQUIRED_FIELDS if field not in card or card[field] in (None, "", [])]
    prohibited_claim_language = contains_banned_language(card)
    valid = not missing_fields and not prohibited_claim_language
    return {
        "valid": valid,
        "missing_fields": missing_fields,
        "prohibited_claim_language": prohibited_claim_language,
    }


def build_card_from_inventory_item(item: dict[str, Any]) -> dict[str, Any]:
    return create_model_card(
        model_id=item["model_id"],
        model_name=item["model_name"],
        purpose=item["model_purpose"],
        market_type=item["market_type"],
        time_horizon=item["time_horizon"],
        research_basis=f"Registered governance basis for {item['model_family']}.",
        mathematical_summary=f"Governed model family for {item['model_purpose']}.",
        inputs=item["inputs_required"],
        outputs=item["outputs_produced"],
        assumptions=item["assumptions"],
        limitations=item["limitations"],
        known_failure_modes=["Missing or stale inputs can block activation."],
        activation_tier=item["activation_tier"],
        validation_status="validated" if item["governance_score"] >= 80 else "research_pending",
        last_validated_at="2026-05-28",
    )
