from __future__ import annotations

from math import erf, exp, log, sqrt
from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "option_value",
    "implied_volatility",
    "delta",
    "gamma",
    "vega",
    "theta",
    "rho",
    "hedge_ratio",
    "tail_protection_score",
    "max_loss_estimate",
]

MODELS = {
    name: make_model(
        name=name,
        classification="risk_model",
        mathematical_purpose="Price option overlays and hedge sensitivities for institutional derivatives programs.",
        required_inputs=["spot", "strike", "volatility", "time_to_expiry", "risk_free_rate"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Volatility and rate inputs are coherent for the pricing horizon.",
            "Greeks provide local risk approximations around the current state.",
        ],
        limitations=[
            "Model error rises during jumps, illiquidity, or smile distortions.",
            "Outputs support hedging review and should not create auto-execution instructions.",
        ],
        evidence_standard="Institutional derivatives risk management and standard option pricing literature.",
        applicable_markets=["options", "equity_derivatives", "rates_derivatives", "volatility"],
        review_queue_scoring_reason="Relevant when option overlays, hedge ratios, or tail protection costs matter for the candidate decision.",
    )
    for name in [
        "black_scholes_merton",
        "binomial_option_pricing",
        "monte_carlo_option_pricing",
        "heston_stochastic_volatility",
        "local_volatility_model",
        "implied_volatility_surface",
        "options_greeks_risk_model",
        "delta_gamma_vega_hedging",
        "tail_risk_hedging",
        "protective_put_overlay",
        "covered_call_overlay",
        "collar_strategy_model",
        "volatility_risk_premium_model",
        "dispersion_trade_model",
    ]
}


def _cdf(value: float) -> float:
    return 0.5 * (1.0 + erf(value / sqrt(2.0)))


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_derivatives_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    spot = max(float(inputs["spot"]), 0.0001)
    strike = max(float(inputs["strike"]), 0.0001)
    volatility = max(float(inputs["volatility"]), 0.0001)
    time_to_expiry = max(float(inputs["time_to_expiry"]), 1e-6)
    risk_free_rate = float(inputs["risk_free_rate"])
    d1 = (log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * sqrt(time_to_expiry))
    d2 = d1 - volatility * sqrt(time_to_expiry)
    option_value = spot * _cdf(d1) - strike * exp(-risk_free_rate * time_to_expiry) * _cdf(d2)
    delta = _cdf(d1)
    gamma = exp(-(d1**2) / 2.0) / (spot * volatility * sqrt(2.0 * 3.1415926535 * time_to_expiry))
    vega = spot * sqrt(time_to_expiry) * exp(-(d1**2) / 2.0) / sqrt(2.0 * 3.1415926535)
    theta = -(spot * exp(-(d1**2) / 2.0) * volatility) / (2.0 * sqrt(2.0 * 3.1415926535 * time_to_expiry))
    rho = strike * time_to_expiry * exp(-risk_free_rate * time_to_expiry) * _cdf(d2)
    hedge_ratio = round(delta, 6)
    tail_protection_score = round(max(0.0, min(100.0, volatility * 100.0 + (1.0 - delta) * 25.0)), 2)
    max_loss_estimate = round(option_value, 6)
    return build_output(
        OUTPUT_FIELDS,
        {
            "option_value": round(option_value, 6),
            "implied_volatility": round(volatility, 6),
            "delta": round(delta, 6),
            "gamma": round(gamma, 6),
            "vega": round(vega, 6),
            "theta": round(theta, 6),
            "rho": round(rho, 6),
            "hedge_ratio": hedge_ratio,
            "tail_protection_score": tail_protection_score,
            "max_loss_estimate": max_loss_estimate,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_derivatives_model, model_name, inputs)

