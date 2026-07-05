from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "factor_exposures",
    "factor_risk_contribution",
    "idiosyncratic_risk",
    "tracking_error",
    "active_risk",
    "attribution_summary",
    "concentration_risk",
]

MODELS = {
    name: make_model(
        name=name,
        classification="risk_model",
        mathematical_purpose="Estimate factor exposures, common-factor risk, and concentration for multi-factor portfolios.",
        required_inputs=["factor_loadings", "factor_returns", "portfolio_weights", "benchmark_weights"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Factor definitions are stable enough for the review horizon.",
            "Benchmark exposures are comparable to portfolio exposures.",
        ],
        limitations=[
            "Factor mappings can drift across regimes.",
            "Short-term event markets should not be scored directly from long-horizon factor models.",
        ],
        evidence_standard="Institutional risk platform practice, academic factor research, and manager risk reporting standards.",
        applicable_markets=["stocks", "etfs", "funds", "multi_asset", "credit"],
        review_queue_scoring_reason="Useful for portfolio and risk review items because it identifies hidden concentration and active risk.",
    )
    for name in [
        "barra_style_factor_risk_model",
        "multi_asset_factor_risk_model",
        "fundamental_factor_model",
        "statistical_factor_model",
        "macro_factor_model",
        "covariance_matrix_forecast",
        "shrinkage_covariance_model",
        "principal_component_risk_model",
        "risk_attribution_model",
        "performance_attribution_model",
        "active_risk_tracking_error_model",
        "beta_exposure_model",
        "style_factor_exposure_model",
        "sector_industry_exposure_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_factor_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    factor_exposures = {factor: round(sum(float(x) for x in loadings) / max(len(loadings), 1), 6) for factor, loadings in inputs["factor_loadings"].items()}
    factor_risk_contribution = {factor: round(abs(exposure) * abs(float(inputs["factor_returns"].get(factor, 0.0))), 6) for factor, exposure in factor_exposures.items()}
    active_diffs = []
    for key, value in inputs["portfolio_weights"].items():
        active_diffs.append(abs(float(value) - float(inputs["benchmark_weights"].get(key, 0.0))))
    active_risk = round(sum(active_diffs), 6)
    tracking_error = round(active_risk / max(len(active_diffs), 1), 6)
    concentration_risk = round(max(abs(exposure) for exposure in factor_exposures.values()) * 100.0 if factor_exposures else 0.0, 2)
    idiosyncratic_risk = round(max(0.0, 1.0 - min(sum(abs(value) for value in factor_risk_contribution.values()), 1.0)), 6)
    attribution_summary = {
        "largest_factor": max(factor_risk_contribution, key=factor_risk_contribution.get) if factor_risk_contribution else None,
        "active_risk": active_risk,
        "tracking_error": tracking_error,
    }
    return build_output(
        OUTPUT_FIELDS,
        {
            "factor_exposures": factor_exposures,
            "factor_risk_contribution": factor_risk_contribution,
            "idiosyncratic_risk": idiosyncratic_risk,
            "tracking_error": tracking_error,
            "active_risk": active_risk,
            "attribution_summary": attribution_summary,
            "concentration_risk": concentration_risk,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_factor_model, model_name, inputs)

