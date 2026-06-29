from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "regime_probabilities",
    "risk_regime",
    "recession_probability",
    "inflation_risk",
    "rates_risk",
    "model_trust_adjustment",
]

MODELS = {
    name: make_model(
        name=name,
        classification="regime_model",
        mathematical_purpose="Classify macro and market regimes to scale trust in cyclical or directional models.",
        required_inputs=["growth_score", "inflation_score", "liquidity_score", "volatility_score"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Macro inputs summarize the current regime with tolerable lag.",
            "Regime signals should scale trust rather than override hard risk constraints.",
        ],
        limitations=[
            "Macro classifications can lag turning points.",
            "Regime models should not directly create sportsbook or order-routing actions.",
        ],
        evidence_standard="Macro research, business-cycle models, and institutional top-down allocation practice.",
        applicable_markets=["macro", "stocks", "rates", "credit", "multi_asset"],
        review_queue_scoring_reason="Useful for scaling confidence because adverse macro regimes should lower trust in other models.",
    )
    for name in [
        "macro_regime_classifier",
        "business_cycle_model",
        "inflation_regime_model",
        "rates_regime_model",
        "volatility_regime_model",
        "recession_probability_model",
        "global_macro_factor_model",
        "nowcasting_model",
        "leading_indicator_model",
        "risk_on_risk_off_model",
        "liquidity_regime_model",
        "monetary_policy_regime_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_macro_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    growth_score = max(0.0, min(1.0, float(inputs["growth_score"])))
    inflation_score = max(0.0, min(1.0, float(inputs["inflation_score"])))
    liquidity_score = max(0.0, min(1.0, float(inputs["liquidity_score"])))
    volatility_score = max(0.0, min(1.0, float(inputs["volatility_score"])))
    regime_probabilities = {
        "risk_on": round(max(0.0, growth_score * liquidity_score * (1.0 - volatility_score)), 6),
        "risk_off": round(max(0.0, (1.0 - growth_score) * (1.0 - liquidity_score) + volatility_score * 0.5), 6),
        "inflationary": round(max(0.0, inflation_score), 6),
    }
    recession_probability = round(max(0.0, min(1.0, (1.0 - growth_score) * 0.7 + volatility_score * 0.3)), 6)
    inflation_risk = round(inflation_score, 6)
    rates_risk = round((inflation_score + (1.0 - liquidity_score)) / 2.0, 6)
    risk_regime = "risk_off" if regime_probabilities["risk_off"] >= regime_probabilities["risk_on"] else "risk_on"
    model_trust_adjustment = round(max(0.2, 1.0 - recession_probability * 0.5 - volatility_score * 0.3), 6)
    return build_output(
        OUTPUT_FIELDS,
        {
            "regime_probabilities": regime_probabilities,
            "risk_regime": risk_regime,
            "recession_probability": recession_probability,
            "inflation_risk": inflation_risk,
            "rates_risk": rates_risk,
            "model_trust_adjustment": model_trust_adjustment,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_macro_model, model_name, inputs)

