from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "allocation_target",
    "liquidity_need",
    "capital_call_projection",
    "illiquidity_risk",
    "manager_score",
    "vintage_diversification_score",
]

MODELS = {
    name: make_model(
        name=name,
        classification="allocation_model",
        mathematical_purpose="Assess pacing, liquidity, manager quality, and vintage diversification for alternative assets.",
        required_inputs=["target_allocation", "available_liquidity", "commitment_base", "manager_quality_score", "vintage_count"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Capital calls and liquidity needs are approximable from planning data.",
            "Manager selection inputs summarize underwriting quality.",
        ],
        limitations=[
            "Private asset marks and capital calls are lumpy and uncertain.",
            "Outputs inform planning and review, not near-term trading actions.",
        ],
        evidence_standard="Endowment, private markets, and institutional alternative allocation practice.",
        applicable_markets=["private_equity", "private_credit", "real_assets", "hedge_funds", "endowment"],
        review_queue_scoring_reason="Useful for long-horizon allocation review items because illiquidity can dominate apparent alpha.",
    )
    for name in [
        "endowment_model_allocation",
        "private_equity_pacing_model",
        "private_credit_allocation_model",
        "real_assets_inflation_hedge_model",
        "hedge_fund_replication_model",
        "manager_selection_scorecard",
        "illiquidity_premium_model",
        "capital_call_forecast_model",
        "commitment_pacing_model",
        "vintage_year_diversification_model",
        "liquidity_waterfall_model",
        "j_curve_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_alternative_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    target_allocation = max(float(inputs["target_allocation"]), 0.0)
    available_liquidity = max(float(inputs["available_liquidity"]), 0.0)
    commitment_base = max(float(inputs["commitment_base"]), 0.0)
    manager_quality_score = max(0.0, min(100.0, float(inputs["manager_quality_score"])))
    vintage_count = max(int(inputs["vintage_count"]), 1)
    liquidity_need = round(max(0.0, target_allocation * commitment_base - available_liquidity), 6)
    capital_call_projection = round(commitment_base * 0.2, 6)
    illiquidity_risk = round(min(100.0, (target_allocation * 100.0) + liquidity_need / max(commitment_base, 1.0) * 100.0), 2)
    vintage_diversification_score = round(min(100.0, vintage_count * 12.5), 2)
    return build_output(
        OUTPUT_FIELDS,
        {
            "allocation_target": round(target_allocation, 6),
            "liquidity_need": liquidity_need,
            "capital_call_projection": capital_call_projection,
            "illiquidity_risk": illiquidity_risk,
            "manager_score": manager_quality_score,
            "vintage_diversification_score": vintage_diversification_score,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_alternative_model, model_name, inputs)

