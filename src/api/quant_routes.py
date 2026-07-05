from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import Depends

from src.api.schemas.quant import BetAnalysisRequest, MarketPricingRequest, StockAnalysisRequest


def register_quant_routes(
    app: Any,
    *,
    require_action_key: Any,
    american_to_decimal_fn: Any,
    american_to_implied_probability_fn: Any,
    build_market_pricing_row_fn: Any,
    capm_required_return_fn: Any,
    classify_bet_fn: Any,
    classify_edge_fn: Any,
    classify_stock_fn: Any,
    expected_value_dollars_fn: Any,
    expected_value_per_unit_fn: Any,
    exposure_check_fn: Any,
    implied_probability_from_american_fn: Any,
    kelly_fraction_fn: Any,
    probability_to_fair_american_fn: Any,
    stock_alpha_fn: Any,
    suggested_bet_size_fn: Any,
    suggested_stake_fn: Any,
) -> None:
    """
    Register quant analysis routes.

    Canonical owner: src/api/quant_routes.py
    """
    american_to_decimal = american_to_decimal_fn
    american_to_implied_probability = american_to_implied_probability_fn
    build_market_pricing_row = build_market_pricing_row_fn
    capm_required_return = capm_required_return_fn
    classify_bet = classify_bet_fn
    classify_edge = classify_edge_fn
    classify_stock = classify_stock_fn
    expected_value_dollars = expected_value_dollars_fn
    expected_value_per_unit = expected_value_per_unit_fn
    exposure_check = exposure_check_fn
    implied_probability_from_american = implied_probability_from_american_fn
    kelly_fraction = kelly_fraction_fn
    probability_to_fair_american = probability_to_fair_american_fn
    stock_alpha = stock_alpha_fn
    suggested_bet_size = suggested_bet_size_fn
    suggested_stake = suggested_stake_fn

    @app.post("/quant/bet-analysis", operation_id="quantBetAnalysis", dependencies=[Depends(require_action_key)])
    async def quant_bet_analysis(payload: BetAnalysisRequest):
        true_probability = payload.true_probability_pct / 100
        implied_probability = implied_probability_from_american(payload.odds)
        edge_pct = (true_probability - implied_probability) * 100
        ev_unit = expected_value_per_unit(payload.odds, true_probability)
        ev_dollars = expected_value_dollars(payload.odds, true_probability, payload.stake)
        kelly = kelly_fraction(payload.odds, true_probability)
        suggested = suggested_bet_size(payload.bankroll, kelly)
        exposure = exposure_check(payload.bankroll, suggested, payload.current_group_exposure)
        decision = classify_bet(edge_pct, ev_unit * 100, kelly * 100)
        analysis = {
            "implied_probability_pct": round(implied_probability * 100, 2),
            "true_probability_pct": round(payload.true_probability_pct, 2),
            "edge_pct": round(edge_pct, 2),
            "ev_per_100": round(ev_unit * 100, 2),
            "ev_dollars": round(ev_dollars, 2),
            "kelly_pct": round(kelly * 100, 2),
            "suggested_stake": round(suggested, 2),
            "decision": decision,
            "exposure": exposure,
        }
        logbook_row = {
            "date": date.today().isoformat(),
            "type": "bet",
            "sport": payload.sport,
            "event": payload.event,
            "pick": payload.pick,
            "market": payload.market,
            "odds": payload.odds,
            "stake": payload.stake,
            "bankroll": payload.bankroll,
            "true_probability_pct": analysis["true_probability_pct"],
            "implied_probability_pct": analysis["implied_probability_pct"],
            "edge_pct": analysis["edge_pct"],
            "ev_per_100": analysis["ev_per_100"],
            "ev_dollars": analysis["ev_dollars"],
            "kelly_pct": analysis["kelly_pct"],
            "suggested_stake": analysis["suggested_stake"],
            "correlation_group": payload.correlation_group,
            "exposure_status": exposure["message"],
            "decision": decision,
            "result": "pending",
            "profit_or_loss": 0,
            "notes": payload.notes,
        }
        return {"ok": True, "endpoint": "/quant/bet-analysis", "analysis": analysis, "logbook_row": logbook_row}


    @app.post("/quant/market-pricing", operation_id="priceMarket", dependencies=[Depends(require_action_key)])
    async def quant_market_pricing(payload: MarketPricingRequest):
        implied = american_to_implied_probability(payload.american_odds)
        implied_probability = implied["decimal"]
        edge = payload.true_probability - implied_probability
        ev_unit = expected_value_per_unit(payload.american_odds, payload.true_probability)
        kelly = kelly_fraction(payload.american_odds, payload.true_probability)
        suggested = suggested_stake(payload.bankroll, payload.american_odds, payload.true_probability)
        decision = classify_edge(edge * 100, ev_unit)
        risk_warning = "Stake is within the capped fractional Kelly risk limit."

        if suggested <= 0 and ev_unit <= 0:
            risk_warning = "This market has no positive expected value at the submitted probability."
        elif payload.bankroll and payload.stake > payload.bankroll * 0.05:
            decision = "OVEREXPOSED"
            risk_warning = "Submitted stake is above the correlation exposure guardrail."
        elif payload.stake > suggested and suggested >= 0:
            risk_warning = "Submitted stake is above the capped fractional Kelly recommendation."

        output = {
            "decimal_odds": round(american_to_decimal(payload.american_odds), 2),
            "implied_probability": round(implied_probability, 4),
            "implied_probability_percent": round(implied_probability * 100, 2),
            "true_probability_percent": round(payload.true_probability * 100, 2),
            "edge": round(edge, 4),
            "edge_percent": round(edge * 100, 2),
            "fair_american_odds": probability_to_fair_american(payload.true_probability),
            "ev_per_unit": round(ev_unit, 4),
            "ev_per_100": round(ev_unit * 100, 2),
            "kelly_fraction": round(kelly, 4),
            "kelly_percent": round(kelly * 100, 2),
            "suggested_stake": round(suggested, 2),
            "decision": decision,
            "risk_warning": risk_warning,
        }
        input_data = payload.model_dump()
        logbook_row = build_market_pricing_row(input_data, output)
        return {
            "ok": True,
            "event": payload.event,
            "provider": payload.provider,
            "sportsbook": payload.sportsbook,
            "league": payload.league,
            "market": payload.market,
            "selection": payload.selection,
            "american_odds": payload.american_odds,
            "decimal_odds": output["decimal_odds"],
            "implied_probability": output["implied_probability"],
            "implied_probability_percent": output["implied_probability_percent"],
            "true_probability": payload.true_probability,
            "true_probability_percent": output["true_probability_percent"],
            "edge": output["edge"],
            "edge_percent": output["edge_percent"],
            "fair_american_odds": output["fair_american_odds"],
            "ev_per_unit": output["ev_per_unit"],
            "ev_per_100": output["ev_per_100"],
            "kelly_fraction": output["kelly_fraction"],
            "kelly_percent": output["kelly_percent"],
            "suggested_stake": output["suggested_stake"],
            "decision": output["decision"],
            "risk_warning": output["risk_warning"],
            "logbook_row": logbook_row,
        }


    @app.post("/quant/stock-analysis", operation_id="quantStockAnalysis", dependencies=[Depends(require_action_key)])
    async def quant_stock_analysis(payload: StockAnalysisRequest):
        required = capm_required_return(payload.risk_free_rate_pct, payload.beta, payload.expected_market_return_pct)
        alpha = stock_alpha(payload.expected_stock_return_pct, required)
        position_pct = (payload.planned_position_size / payload.portfolio_value * 100) if payload.portfolio_value else 0
        decision = classify_stock(alpha)
        analysis = {
            "ticker": payload.ticker.upper(),
            "capm_required_return_pct": round(required, 2),
            "expected_stock_return_pct": round(payload.expected_stock_return_pct, 2),
            "alpha_pct": round(alpha, 2),
            "position_pct": round(position_pct, 2),
            "decision": decision,
        }
        logbook_row = {
            "date": date.today().isoformat(),
            "type": "stock",
            "ticker": payload.ticker.upper(),
            "current_price": payload.current_price,
            "expected_stock_return_pct": payload.expected_stock_return_pct,
            "beta": payload.beta,
            "risk_free_rate_pct": payload.risk_free_rate_pct,
            "expected_market_return_pct": payload.expected_market_return_pct,
            "capm_required_return_pct": analysis["capm_required_return_pct"],
            "alpha_pct": analysis["alpha_pct"],
            "planned_position_size": payload.planned_position_size,
            "portfolio_value": payload.portfolio_value,
            "position_pct": analysis["position_pct"],
            "decision": decision,
            "exit_plan": "",
            "result": "pending",
            "profit_or_loss": 0,
            "notes": payload.notes,
        }
        return {"ok": True, "endpoint": "/quant/stock-analysis", "analysis": analysis, "logbook_row": logbook_row}
