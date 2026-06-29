from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "duration",
    "convexity",
    "key_rate_exposure",
    "yield_curve_factors",
    "spread_risk",
    "rate_shock_pnl",
    "income_projection",
]

MODELS = {
    name: make_model(
        name=name,
        classification="risk_model",
        mathematical_purpose="Measure rates exposure, yield-curve shape, and income sensitivity for fixed-income portfolios.",
        required_inputs=["cash_flows", "yield_curve", "spread", "price"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Yield curve points are representative for the instrument set.",
            "Rate shocks and spread shifts are approximately local over the review horizon.",
        ],
        limitations=[
            "Large regime shifts can invalidate local duration and convexity approximations.",
            "Outputs inform rates risk review, not sportsbook-style trade recommendations.",
        ],
        evidence_standard="Institutional fixed-income analytics, risk management practice, and academic term-structure research.",
        applicable_markets=["bonds", "rates", "credit", "inflation_linked"],
        review_queue_scoring_reason="Relevant for rates and fixed-income candidates because it translates yield and spread moves into risk and carry impacts.",
    )
    for name in [
        "duration_convexity_model",
        "yield_curve_bootstrap_model",
        "nelson_siegel_yield_curve",
        "dynamic_nelson_siegel",
        "key_rate_duration_model",
        "spread_duration_model",
        "credit_spread_model",
        "term_premium_model",
        "curve_steepener_flattener_model",
        "bond_ladder_model",
        "carry_roll_down_model",
        "breakeven_inflation_model",
        "real_yield_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_rates_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    cash_flows = [float(value) for value in inputs["cash_flows"]]
    yield_curve = [float(value) for value in inputs["yield_curve"]]
    spread = float(inputs["spread"])
    price = float(inputs["price"])
    duration = round(sum((idx + 1) * cf for idx, cf in enumerate(cash_flows)) / max(sum(cash_flows), 0.0001), 6)
    convexity = round(sum(((idx + 1) ** 2) * cf for idx, cf in enumerate(cash_flows)) / max(sum(cash_flows), 0.0001), 6)
    key_rate_exposure = {f"{idx + 1}y": round(duration * (point / max(sum(yield_curve), 0.0001)), 6) for idx, point in enumerate(yield_curve)}
    yield_curve_factors = {
        "level": round(sum(yield_curve) / max(len(yield_curve), 1), 6),
        "slope": round((yield_curve[-1] - yield_curve[0]) if len(yield_curve) > 1 else 0.0, 6),
        "curvature": round((yield_curve[len(yield_curve) // 2] * 2 - yield_curve[0] - yield_curve[-1]) if len(yield_curve) > 2 else 0.0, 6),
    }
    spread_risk = round(abs(spread) * duration, 6)
    rate_shock_pnl = round(-duration * 0.01 * price + 0.5 * convexity * (0.01 ** 2) * price, 6)
    income_projection = round(price * max(yield_curve_factors["level"] + spread, 0.0), 6)
    return build_output(
        OUTPUT_FIELDS,
        {
            "duration": duration,
            "convexity": convexity,
            "key_rate_exposure": key_rate_exposure,
            "yield_curve_factors": yield_curve_factors,
            "spread_risk": spread_risk,
            "rate_shock_pnl": rate_shock_pnl,
            "income_projection": income_projection,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_rates_model, model_name, inputs)

