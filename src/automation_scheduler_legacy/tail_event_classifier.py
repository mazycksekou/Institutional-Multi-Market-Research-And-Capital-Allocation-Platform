from __future__ import annotations

from typing import Any

from .security_policy import locked_safety_flags


TAIL_EVENT_TYPES = {
    "normal_noise",
    "elevated_noise",
    "random_extreme",
    "liquidity_tail_event",
    "volatility_tail_event",
    "correlation_tail_event",
    "market_structure_break",
    "possible_regime_change",
    "data_error_or_stale_feed",
    "fake_edge_tail_event",
}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if abs(parsed) <= 1.0:
        return parsed * 100.0
    return parsed


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _asset_type(row: dict[str, Any]) -> str:
    text = str(row.get("asset_type") or row.get("asset_class") or "").strip().lower()
    aliases = {
        "prediction": "prediction_market",
        "kalshi": "prediction_market",
        "sports": "sportsbook",
        "sport": "sportsbook",
        "equity": "stock",
        "bond": "bond_rate",
        "rate": "bond_rate",
        "rates": "bond_rate",
        "fixed_income": "bond_rate",
    }
    if text in aliases:
        return aliases[text]
    if text:
        return text
    if row.get("sport") or row.get("league") or row.get("line_move") is not None:
        return "sportsbook"
    if row.get("funding_rate") is not None or row.get("liquidation_cluster_risk") is not None:
        return "crypto"
    if row.get("yield_change") is not None or row.get("curve_steepening_score") is not None:
        return "bond_rate"
    return "stock"


def _risk_label(score: float) -> str:
    if score >= 80:
        return "extreme"
    if score >= 60:
        return "high"
    if score >= 35:
        return "moderate"
    return "low"


def classify_tail_event(candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    row = dict(candidate or {})
    asset_type = _asset_type(row)
    edge = abs(_num(row.get("estimated_edge")))
    price_move = abs(_num(row.get("price_move")))
    odds_move = abs(_num(row.get("odds_move")))
    line_move = abs(_num(row.get("line_move")))
    volume_spike = max(_num(row.get("volume_spike")), _num(row.get("relative_volume")))
    volatility = _num(row.get("volatility_score"))
    liquidity = _num(row.get("liquidity_score"), 50.0)
    spread_quality = _num(row.get("spread_score"), 50.0)
    correlation = _num(row.get("correlation_shock_score") or row.get("correlation_score"))
    stale = max(_num(row.get("stale_data_risk")), _num(row.get("stale_market_score")))
    settlement_uncertainty = _num(row.get("settlement_uncertainty_score"))
    macro_event = _num(row.get("macro_event_score"))
    funding_extreme = abs(_num(row.get("funding_rate"))) if row.get("funding_rate") is not None else 0.0
    liquidation = _num(row.get("liquidation_cluster_risk"))
    exchange_dislocation = _num(row.get("exchange_dislocation_score"))
    low_liquidity_risk = _clamp(100.0 - liquidity)
    wide_spread_risk = _clamp(100.0 - spread_quality)

    tail_type = "normal_noise"
    no_bet_no_trade_reason = None
    if stale >= 65:
        tail_type = "data_error_or_stale_feed"
        no_bet_no_trade_reason = "stale_or_data_error_risk"
    elif asset_type == "prediction_market" and (wide_spread_risk >= 60 or low_liquidity_risk >= 60) and edge >= 6:
        tail_type = "fake_edge_tail_event"
        no_bet_no_trade_reason = "prediction_market_wide_spread_or_low_liquidity_fake_edge"
    elif asset_type == "sportsbook" and (line_move >= 65 or odds_move >= 65):
        tail_type = "market_structure_break" if stale >= 35 else "random_extreme"
        no_bet_no_trade_reason = "sportsbook_line_shock_requires_recheck"
    elif asset_type in {"stock", "etf"} and (volatility >= 75 or volume_spike >= 8 or price_move >= 12):
        tail_type = "volatility_tail_event"
        no_bet_no_trade_reason = "stock_etf_volatility_expansion"
    elif asset_type == "crypto" and (liquidation >= 65 or funding_extreme >= 5 or exchange_dislocation >= 60):
        tail_type = "liquidity_tail_event"
        no_bet_no_trade_reason = "crypto_liquidation_or_exchange_dislocation"
    elif asset_type in {"bond_rate", "bond", "rate", "major_asset"} and (macro_event >= 65 or abs(_num(row.get("yield_change"))) >= 40):
        tail_type = "possible_regime_change"
        no_bet_no_trade_reason = "rates_macro_shock_requires_regime_review"
    elif correlation >= 70:
        tail_type = "correlation_tail_event"
        no_bet_no_trade_reason = "systemwide_correlation_shock"
    elif max(edge, price_move, odds_move, line_move, volatility) >= 70:
        tail_type = "random_extreme"
        no_bet_no_trade_reason = "large_signal_may_be_random_system_extreme"
    elif max(edge, price_move, odds_move, line_move, volatility) >= 35:
        tail_type = "elevated_noise"

    raw_score = max(edge, price_move, odds_move, line_move, volatility, volume_spike * 10.0, correlation)
    liquidity_adjusted = _clamp(raw_score + low_liquidity_risk * 0.25 + wide_spread_risk * 0.20)
    volatility_adjusted = _clamp(raw_score + volatility * 0.20)
    correlation_adjusted = _clamp(raw_score + correlation * 0.25)
    data_error_risk = _clamp(stale * 0.75 + (100.0 if row.get("data_quality_status") == "failed" else 0.0))
    risk_score = _clamp(max(liquidity_adjusted, volatility_adjusted, correlation_adjusted, data_error_risk))
    confidence = 0.35
    if tail_type not in {"normal_noise", "elevated_noise"}:
        confidence = 0.70 if risk_score >= 60 else 0.55
    if data_error_risk >= 65:
        confidence = max(confidence, 0.80)
    payload = {
        "tail_event_type": tail_type,
        "tail_event_confidence": round(confidence, 6),
        "tail_event_risk_score": round(risk_score, 2),
        "volatility_adjusted_signal": round(volatility_adjusted, 2),
        "liquidity_adjusted_signal": round(liquidity_adjusted, 2),
        "correlation_adjusted_signal": round(correlation_adjusted, 2),
        "random_extreme_probability": round(min(0.99, risk_score / 120.0), 6),
        "data_error_risk": round(data_error_risk, 2),
        "fake_edge_risk": _risk_label(max(low_liquidity_risk, wide_spread_risk) if tail_type == "fake_edge_tail_event" else max(edge, wide_spread_risk * 0.5)),
        "no_trade_no_bet_reason": no_bet_no_trade_reason,
        "no_bet_reasons": [no_bet_no_trade_reason] if no_bet_no_trade_reason and asset_type in {"sportsbook", "prediction_market"} else [],
        "no_trade_reasons": [no_bet_no_trade_reason] if no_bet_no_trade_reason and asset_type not in {"sportsbook", "prediction_market"} else [],
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
