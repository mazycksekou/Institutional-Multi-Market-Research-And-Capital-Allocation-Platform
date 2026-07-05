from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "after_tax_return",
    "tax_drag",
    "harvesting_candidate",
    "wash_sale_risk",
    "account_location_recommendation",
]

MODELS = {
    name: make_model(
        name=name,
        classification="allocation_model",
        mathematical_purpose="Optimize after-tax outcomes and account placement under tax and wash-sale constraints.",
        required_inputs=["pre_tax_return", "tax_rate", "unrealized_loss", "recent_sale_days", "account_type"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Tax rates and account rules are known for the evaluation context.",
            "Recent sale history is available for wash-sale checks.",
        ],
        limitations=[
            "Tax rules vary by jurisdiction and investor circumstance.",
            "Outputs are advisory and should not override explicit compliance controls.",
        ],
        evidence_standard="Tax-aware portfolio construction and wealth management practice.",
        applicable_markets=["stocks", "etfs", "funds", "retirement_portfolio", "taxable_account"],
        review_queue_scoring_reason="Relevant for taxable-account candidates because after-tax return can reverse pre-tax attractiveness.",
    )
    for name in [
        "tax_loss_harvesting_model",
        "asset_location_model",
        "after_tax_return_model",
        "wash_sale_risk_checker",
        "capital_gains_budget_model",
        "account_type_allocation_model",
        "taxable_vs_retirement_account_optimizer",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_tax_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    pre_tax_return = float(inputs["pre_tax_return"])
    tax_rate = max(0.0, min(1.0, float(inputs["tax_rate"])))
    unrealized_loss = float(inputs["unrealized_loss"])
    recent_sale_days = max(int(inputs["recent_sale_days"]), 0)
    account_type = str(inputs["account_type"])
    tax_drag = round(max(pre_tax_return, 0.0) * tax_rate, 6)
    after_tax_return = round(pre_tax_return - tax_drag, 6)
    harvesting_candidate = bool(unrealized_loss < 0)
    wash_sale_risk = round(1.0 if harvesting_candidate and recent_sale_days < 31 else 0.0, 6)
    account_location_recommendation = "retirement_account" if tax_drag > 0.03 else account_type
    return build_output(
        OUTPUT_FIELDS,
        {
            "after_tax_return": after_tax_return,
            "tax_drag": tax_drag,
            "harvesting_candidate": harvesting_candidate,
            "wash_sale_risk": wash_sale_risk,
            "account_location_recommendation": account_location_recommendation,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_tax_model, model_name, inputs)

