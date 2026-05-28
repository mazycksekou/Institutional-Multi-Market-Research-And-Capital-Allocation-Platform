from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "estimated_cost",
    "slippage_estimate",
    "market_impact",
    "execution_risk",
    "fill_probability",
    "optimal_execution_schedule",
    "cost_adjusted_edge",
]

MODELS = {
    name: make_model(
        name=name,
        classification="execution_model",
        mathematical_purpose="Estimate trading costs, impact, and schedule quality before implementation.",
        required_inputs=["order_size", "average_daily_volume", "bid_ask_spread", "volatility", "raw_edge"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Liquidity and spread conditions are representative.",
            "Execution schedule can be adjusted before order release.",
        ],
        limitations=[
            "Market impact can widen during stress or event-driven order flow.",
            "Outputs reduce implementation optimism but never create executable orders.",
        ],
        evidence_standard="Institutional trading cost analysis and execution research.",
        applicable_markets=["stocks", "etfs", "futures", "options", "prediction_markets"],
        review_queue_scoring_reason="Relevant because higher implementation cost should reduce apparent edge before human review.",
    )
    for name in [
        "transaction_cost_analysis",
        "implementation_shortfall_model",
        "almgren_chriss_optimal_execution",
        "market_impact_model",
        "slippage_forecast_model",
        "smart_order_routing_score",
        "liquidity_participation_model",
        "volume_weighted_execution_model",
        "time_weighted_execution_model",
        "arrival_price_model",
        "spread_cost_model",
        "fill_probability_model",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_execution_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    order_size = max(float(inputs["order_size"]), 0.0)
    average_daily_volume = max(float(inputs["average_daily_volume"]), 1.0)
    bid_ask_spread = max(float(inputs["bid_ask_spread"]), 0.0)
    volatility = max(float(inputs["volatility"]), 0.0)
    raw_edge = float(inputs["raw_edge"])
    participation = order_size / average_daily_volume
    estimated_cost = round(order_size * (bid_ask_spread + participation * 0.01 + volatility * 0.05), 6)
    slippage_estimate = round(bid_ask_spread * 0.5 + participation * volatility, 6)
    market_impact = round(participation * 100.0 * max(volatility, 0.01), 6)
    execution_risk = round(min(100.0, market_impact * 5.0 + bid_ask_spread * 100.0), 2)
    fill_probability = round(max(0.0, min(1.0, 1.0 - participation * 1.5 - volatility * 0.2)), 6)
    cost_adjusted_edge = round(raw_edge - (estimated_cost / max(order_size, 1.0)) * 100.0, 6)
    schedule = {
        "arrival": round(min(0.2, participation), 4),
        "vwap": round(min(0.5, max(0.2, participation * 2.0)), 4),
        "passive_remainder": round(max(0.0, 1.0 - min(0.2, participation) - min(0.5, max(0.2, participation * 2.0))), 4),
    }
    return build_output(
        OUTPUT_FIELDS,
        {
            "estimated_cost": estimated_cost,
            "slippage_estimate": slippage_estimate,
            "market_impact": market_impact,
            "execution_risk": execution_risk,
            "fill_probability": fill_probability,
            "optimal_execution_schedule": schedule,
            "cost_adjusted_edge": cost_adjusted_edge,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_execution_model, model_name, inputs)
