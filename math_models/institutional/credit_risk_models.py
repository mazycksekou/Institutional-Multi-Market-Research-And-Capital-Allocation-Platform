from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "probability_of_default",
    "expected_loss",
    "credit_var",
    "spread_risk",
    "downgrade_risk",
    "recovery_assumption",
    "credit_score",
]

MODELS = {
    name: make_model(
        name=name,
        classification="risk_model",
        mathematical_purpose="Estimate default, loss, spread decomposition, and concentration risk across credit exposures.",
        required_inputs=["leverage_ratio", "interest_coverage", "spread", "recovery_rate", "exposure"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Credit ratios summarize issuer fragility reasonably well.",
            "Recovery assumptions are bounded and scenario-consistent.",
        ],
        limitations=[
            "Credit events are path-dependent and can gap beyond model assumptions.",
            "These outputs are portfolio risk diagnostics, not direct trade commands.",
        ],
        evidence_standard="Credit portfolio management practice, structural and reduced-form credit literature, and bank risk frameworks.",
        applicable_markets=["credit", "corporate_bonds", "loans", "private_credit"],
        review_queue_scoring_reason="Relevant to credit review items because expected loss and downgrade risk can override apparent spread attractiveness.",
    )
    for name in [
        "merton_structural_credit_model",
        "reduced_form_default_model",
        "credit_transition_matrix_model",
        "expected_default_frequency",
        "probability_of_default_model",
        "loss_given_default_model",
        "exposure_at_default_model",
        "credit_var_model",
        "spread_decomposition_model",
        "recovery_rate_model",
        "downgrade_risk_model",
        "credit_portfolio_concentration_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_credit_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    leverage_ratio = max(float(inputs["leverage_ratio"]), 0.0)
    interest_coverage = max(float(inputs["interest_coverage"]), 0.01)
    spread = max(float(inputs["spread"]), 0.0)
    recovery_rate = max(0.0, min(1.0, float(inputs["recovery_rate"])))
    exposure = max(float(inputs["exposure"]), 0.0)
    probability_of_default = round(min(1.0, leverage_ratio / (interest_coverage * 10.0) + spread * 0.1), 6)
    expected_loss = round(exposure * probability_of_default * (1.0 - recovery_rate), 6)
    credit_var = round(expected_loss * 1.65, 6)
    spread_risk = round(spread * exposure, 6)
    downgrade_risk = round(min(1.0, probability_of_default * 1.2), 6)
    credit_score = round(max(0.0, 100.0 - probability_of_default * 100.0 - leverage_ratio * 5.0 + interest_coverage * 3.0), 2)
    return build_output(
        OUTPUT_FIELDS,
        {
            "probability_of_default": probability_of_default,
            "expected_loss": expected_loss,
            "credit_var": credit_var,
            "spread_risk": spread_risk,
            "downgrade_risk": downgrade_risk,
            "recovery_assumption": recovery_rate,
            "credit_score": credit_score,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_credit_model, model_name, inputs)

