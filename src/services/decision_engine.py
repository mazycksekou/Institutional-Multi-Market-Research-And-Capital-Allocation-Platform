"""Canonical decision-engine orchestration helpers.

This module is intentionally thin. It combines core pricing, probability,
portfolio, execution, market-impact, and game-theory helpers without touching
connectors, providers, or live execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.brokerage.orders import build_execution_request, build_order_request
from src.brokerage.readiness import get_execution_readiness
from src.core.execution import liquidity_adjusted_size, split_order
from src.core.game_theory import position_accumulation_plan, thesis_break_triggered
from src.core.market_impact import adverse_selection_score, estimate_market_impact, signaling_risk_score
from src.core.portfolio import portfolio_summary
from src.core.pricing import (
    edge_percentage,
    expected_value_per_unit,
    fair_odds_american_from_probability,
    implied_probability_from_american,
    normalize_probability,
)
from src.core.risk import exposure_summary, risk_profile_settings


def build_decision_context(candidate: Mapping[str, Any]) -> dict[str, Any]:
    american_odds = candidate.get("american_odds", candidate.get("odds_american"))
    market_probability = candidate.get("market_probability")
    model_probability = candidate.get("model_probability")
    bankroll = float(candidate.get("bankroll", 0.0))
    exposure = candidate.get("exposure", {}) or {}

    implied_probability = (
        implied_probability_from_american(american_odds)
        if american_odds is not None
        else None
    )
    normalized_market_probability = (
        normalize_probability(market_probability)
        if market_probability is not None
        else implied_probability
    )
    normalized_model_probability = (
        normalize_probability(model_probability)
        if model_probability is not None
        else normalized_market_probability
    )

    edge = None
    ev_per_unit = None
    fair_odds = None
    if implied_probability is not None and normalized_model_probability is not None:
        edge = edge_percentage(normalized_model_probability, implied_probability)
        ev_per_unit = expected_value_per_unit(american_odds, normalized_model_probability)
        fair_odds = fair_odds_american_from_probability(normalized_model_probability)

    portfolio = portfolio_summary(exposure) if isinstance(exposure, Mapping) else {}
    exposure_report = exposure_summary(exposure) if isinstance(exposure, Mapping) else {}
    risk_profile = risk_profile_settings(candidate.get("risk_profile", "standard"))
    tranche_count = int(candidate.get("tranches", 3) or 3)
    avg_volume = candidate.get("average_daily_volume")
    order_size = float(candidate.get("order_size", candidate.get("stake", 0.0)) or 0.0)

    return {
        "bankroll": bankroll,
        "american_odds": american_odds,
        "implied_probability": implied_probability,
        "market_probability": normalized_market_probability,
        "model_probability": normalized_model_probability,
        "edge_percent": edge,
        "ev_per_unit": ev_per_unit,
        "fair_odds_american": fair_odds,
        "risk_profile": risk_profile,
        "portfolio_summary": portfolio,
        "exposure_summary": exposure_report,
        "order_plan": position_accumulation_plan(
            order_size,
            tranches=tranche_count,
            average_daily_volume=avg_volume,
        ),
        "liquidity_adjusted_size": (
            liquidity_adjusted_size(order_size, float(avg_volume), max_participation_rate=0.1)
            if avg_volume is not None
            else order_size
        ),
        "estimated_market_impact": (
            estimate_market_impact(order_size, float(avg_volume), spread_bps=float(candidate.get("spread_bps", 0.0)), volatility=float(candidate.get("volatility", 0.0)))
            if avg_volume is not None
            else 0.0
        ),
        "signaling_risk_score": (
            signaling_risk_score(order_size, float(avg_volume), order_count=tranche_count)
            if avg_volume is not None
            else 0.0
        ),
        "adverse_selection_score": (
            adverse_selection_score(
                float(candidate.get("spread_bps", 0.0)),
                float(candidate.get("volatility", 0.0)),
                order_size,
                float(avg_volume),
            )
            if avg_volume is not None
            else 0.0
        ),
        "thesis_break_triggered": thesis_break_triggered(
            normalized_model_probability or 0.0,
            float(candidate.get("thesis_probability", normalized_market_probability or 0.0)),
            tolerance=float(candidate.get("thesis_tolerance", 0.05)),
            min_edge=float(candidate.get("min_edge", -0.03)),
        ),
        "split_order": split_order(order_size, float(candidate.get("max_chunk_size", max(1.0, order_size or 1.0)))),
    }


def evaluate_decision(candidate: Mapping[str, Any]) -> dict[str, Any]:
    context = build_decision_context(candidate)
    decision = "watch"
    if context["model_probability"] is not None and context["edge_percent"] is not None:
        if context["edge_percent"] >= 2.5 and (context["ev_per_unit"] or 0.0) > 0:
            decision = "bet"
        elif context["edge_percent"] > 0 and (context["ev_per_unit"] or 0.0) > 0:
            decision = "lean"
    return {
        "decision": decision,
        "execution_enabled": False,
        "live_connector_enabled": False,
        "context": context,
    }


def build_decision_summary(candidate: Mapping[str, Any]) -> dict[str, Any]:
    result = evaluate_decision(candidate)
    return {
        "decision": result["decision"],
        "summary": result["context"],
        "risk_profile": result["context"]["risk_profile"],
        "execution_enabled": result["execution_enabled"],
        "live_connector_enabled": result["live_connector_enabled"],
    }


def build_brokerage_execution_plan(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Build a live-shaped execution plan while keeping the broker boundary disabled."""

    order_request = build_order_request(candidate)
    execution_request = build_execution_request(order_request, candidate=candidate)
    readiness = get_execution_readiness(
        order_request,
        execution_request=execution_request,
        execution_mode=execution_request.execution_mode,
    )
    return {
        "order_request": order_request.as_dict(),
        "execution_request": execution_request.as_dict(),
        "readiness": readiness.as_dict(),
    }


__all__ = [
    "build_brokerage_execution_plan",
    "build_decision_context",
    "build_decision_summary",
    "evaluate_decision",
]
