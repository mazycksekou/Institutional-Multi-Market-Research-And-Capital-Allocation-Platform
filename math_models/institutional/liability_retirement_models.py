from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "glide_path_allocation",
    "funding_ratio",
    "liability_match_score",
    "retirement_survival_score",
    "sequence_risk_score",
    "contribution_required",
    "rebalance_action",
]

MODELS = {
    name: make_model(
        name=name,
        classification="liability_model",
        mathematical_purpose="Match assets to future liabilities, retirement spending needs, and glide-path objectives.",
        required_inputs=["asset_value", "liability_value", "duration_gap", "contribution_rate", "withdrawal_rate"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Liability cash flows are approximately estimable.",
            "Retirement spending assumptions are realistic for the planning horizon.",
        ],
        limitations=[
            "Outputs are unsuitable for short-horizon trading decisions.",
            "Funding and longevity assumptions can change materially through time.",
        ],
        evidence_standard="Pension, retirement income, and asset-liability management research and institutional plan practice.",
        applicable_markets=["retirement_portfolio", "pension", "liability_management", "multi_asset"],
        review_queue_scoring_reason="Relevant only when a candidate is tied to funding, duration, or retirement sustainability decisions.",
    )
    for name in [
        "target_date_lifecycle_glide_path",
        "major_institution_retirement_scale_alias",
        "liability_driven_investing",
        "asset_liability_management",
        "cash_flow_matching",
        "duration_matching",
        "immunization_strategy",
        "surplus_optimization",
        "sequence_of_returns_risk",
        "retirement_income_sustainability",
        "stochastic_retirement_projection",
        "pension_funding_ratio_model",
        "contribution_policy_model",
        "longevity_risk_model",
        "annuity_income_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_liability_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    asset_value = float(inputs["asset_value"])
    liability_value = max(float(inputs["liability_value"]), 0.0001)
    duration_gap = abs(float(inputs["duration_gap"]))
    contribution_rate = float(inputs["contribution_rate"])
    withdrawal_rate = float(inputs["withdrawal_rate"])
    funding_ratio = round(asset_value / liability_value, 6)
    liability_match_score = round(max(0.0, 100.0 - duration_gap * 20.0), 2)
    retirement_survival_score = round(max(0.0, min(100.0, funding_ratio * 60.0 + contribution_rate * 100.0 - withdrawal_rate * 80.0)), 2)
    sequence_risk_score = round(min(100.0, duration_gap * 25.0 + withdrawal_rate * 100.0), 2)
    contribution_required = round(max(0.0, liability_value - asset_value) * 0.05, 2)
    equity_weight = round(max(0.1, min(0.9, 0.75 - withdrawal_rate)), 4)
    glide_path = {"equity": equity_weight, "fixed_income": round(1.0 - equity_weight, 4)}
    rebalance_action = "increase_hedging" if duration_gap > 1 else "maintain_glide_path"
    return build_output(
        OUTPUT_FIELDS,
        {
            "glide_path_allocation": glide_path,
            "funding_ratio": funding_ratio,
            "liability_match_score": liability_match_score,
            "retirement_survival_score": retirement_survival_score,
            "sequence_risk_score": sequence_risk_score,
            "contribution_required": contribution_required,
            "rebalance_action": rebalance_action,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_liability_model, model_name, inputs)
