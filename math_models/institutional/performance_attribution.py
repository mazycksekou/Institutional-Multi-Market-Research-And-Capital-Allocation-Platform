from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "performance_summary",
    "risk_adjusted_metrics",
    "attribution_summary",
    "drawdown_summary",
    "reporting_disclosures",
]

MODELS = {
    name: make_model(
        name=name,
        classification="reporting_model",
        mathematical_purpose="Translate realized returns into transparent attribution, drawdown, and risk-adjusted reporting.",
        required_inputs=["period_returns", "benchmark_returns", "drawdowns", "capital_flows"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Return series and capital flows are complete enough for attribution.",
            "Reported metrics are interpreted with appropriate disclosure context.",
        ],
        limitations=[
            "Historical attribution does not prove forward alpha persistence.",
            "Reporting outputs should not directly activate review-queue scoring without relevance checks.",
        ],
        evidence_standard="Performance measurement, attribution, and institutional reporting practice.",
        applicable_markets=["stocks", "funds", "multi_asset", "retirement_portfolio", "alternatives"],
        review_queue_scoring_reason="Useful for transparency and validation, but should influence review scoring only when the candidate is tied to performance reporting.",
    )
    for name in [
        "time_weighted_return",
        "money_weighted_return",
        "internal_rate_of_return",
        "geometric_return",
        "performance_attribution",
        "factor_attribution",
        "sector_attribution",
        "risk_adjusted_return",
        "sharpe_sortino_calmar",
        "information_ratio",
        "hit_rate_profit_factor",
        "drawdown_attribution",
        "gips_style_reporting_placeholder",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_performance_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    period_returns = [float(value) for value in inputs["period_returns"]]
    benchmark_returns = [float(value) for value in inputs["benchmark_returns"]]
    drawdowns = [float(value) for value in inputs["drawdowns"]]
    capital_flows = [float(value) for value in inputs["capital_flows"]]
    average_return = sum(period_returns) / max(len(period_returns), 1)
    benchmark_return = sum(benchmark_returns) / max(len(benchmark_returns), 1)
    excess_return = average_return - benchmark_return
    volatility = (sum((value - average_return) ** 2 for value in period_returns) / max(len(period_returns), 1)) ** 0.5
    performance_summary = {"average_return": round(average_return, 6), "benchmark_return": round(benchmark_return, 6), "excess_return": round(excess_return, 6)}
    risk_adjusted_metrics = {
        "sharpe_like": round(excess_return / max(volatility, 0.0001), 6),
        "information_ratio": round(excess_return / max(volatility, 0.0001), 6),
        "profit_factor_like": round(sum(max(r, 0.0) for r in period_returns) / max(abs(sum(min(r, 0.0) for r in period_returns)), 0.0001), 6),
    }
    attribution_summary = {"selection": round(excess_return * 0.6, 6), "allocation": round(excess_return * 0.4, 6)}
    drawdown_summary = {"max_drawdown": round(min(drawdowns) if drawdowns else 0.0, 6), "recovery_need": round(abs(min(drawdowns)) / max(1.0 + min(drawdowns), 0.0001) if drawdowns else 0.0, 6)}
    reporting_disclosures = [
        "Past performance is not a guarantee of future results.",
        f"Net capital flow observed: {round(sum(capital_flows), 6)}",
    ]
    return build_output(
        OUTPUT_FIELDS,
        {
            "performance_summary": performance_summary,
            "risk_adjusted_metrics": risk_adjusted_metrics,
            "attribution_summary": attribution_summary,
            "drawdown_summary": drawdown_summary,
            "reporting_disclosures": reporting_disclosures,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_performance_model, model_name, inputs)

