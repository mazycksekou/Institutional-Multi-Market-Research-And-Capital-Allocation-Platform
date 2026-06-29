from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model, normalize_weights

OUTPUT_FIELDS = [
    "portfolio_weights",
    "expected_return",
    "expected_volatility",
    "risk_contribution",
    "diversification_score",
    "constraint_violations",
    "drawdown_estimate",
    "suitability_score",
]

MODELS = {
    name: make_model(
        name=name,
        classification="allocation_model",
        mathematical_purpose="Construct strategic or tactical portfolio weights under risk and allocation constraints.",
        required_inputs=["expected_returns", "volatility_estimates", "constraints", "asset_universe"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Expected return and volatility estimates are directionally informative.",
            "Constraints are explicitly provided and enforceable.",
        ],
        limitations=[
            "Optimization is sensitive to estimation error.",
            "Long-horizon allocation outputs should not be used for sportsbook-style recommendations.",
        ],
        evidence_standard="Institutional asset allocation research, manager practice, and portfolio theory validation.",
        applicable_markets=["stocks", "etfs", "funds", "multi_asset", "retirement_portfolio"],
        review_queue_scoring_reason="Relevant only for long-horizon portfolio review items and should not affect short-term market scoring.",
    )
    for name in [
        "mean_variance_optimization",
        "efficient_frontier_optimizer",
        "minimum_variance_portfolio",
        "maximum_sharpe_portfolio",
        "risk_parity_all_weather",
        "equal_risk_contribution",
        "hierarchical_risk_parity",
        "robust_portfolio_optimization",
        "resampled_efficient_frontier",
        "core_satellite_allocation",
        "strategic_asset_allocation",
        "tactical_asset_allocation",
        "factor_tilt_portfolio",
        "multi_objective_portfolio_optimization",
        "constrained_portfolio_optimizer",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_portfolio_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    returns = [float(value) for value in inputs["expected_returns"]]
    volatilities = [max(float(value), 0.0001) for value in inputs["volatility_estimates"]]
    raw_weights = [1.0 / value for value in volatilities]
    weights = normalize_weights(raw_weights)
    expected_return = sum(weight * ret for weight, ret in zip(weights, returns))
    expected_volatility = sum(weight * vol for weight, vol in zip(weights, volatilities))
    risk_contribution = {asset: round(weight * vol, 6) for asset, weight, vol in zip(inputs["asset_universe"], weights, volatilities)}
    diversification_score = round(min(100.0, len([w for w in weights if w > 0.05]) * 10.0), 2)
    violations = [rule for rule in inputs.get("constraints", []) if str(rule).startswith("violation:")]
    drawdown_estimate = round(expected_volatility * 2.5, 4)
    suitability_score = round(max(0.0, 100.0 - len(violations) * 15.0 - drawdown_estimate * 100.0), 2)
    return build_output(
        OUTPUT_FIELDS,
        {
            "portfolio_weights": dict(zip(inputs["asset_universe"], weights)),
            "expected_return": round(expected_return, 6),
            "expected_volatility": round(expected_volatility, 6),
            "risk_contribution": risk_contribution,
            "diversification_score": diversification_score,
            "constraint_violations": violations,
            "drawdown_estimate": drawdown_estimate,
            "suitability_score": suitability_score,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_portfolio_model, model_name, inputs)

