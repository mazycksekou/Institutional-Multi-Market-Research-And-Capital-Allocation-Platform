from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from ._shared import clamp, compact_list, safe_float, weighted_average
from .report import build_market_intelligence_report


def _first_defined(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _is_active_contract(contract: Mapping[str, Any], *, floor_minutes: float = 1.0) -> bool:
    days_to_expiry = safe_float(_first_defined(contract.get("days_to_expiry"), contract.get("dte")))
    minutes_to_expiry = safe_float(_first_defined(contract.get("minutes_to_expiry"), contract.get("time_to_expiry_minutes")))
    if days_to_expiry is not None and days_to_expiry <= 0:
        return False
    if minutes_to_expiry is not None and minutes_to_expiry <= 0:
        return False
    if minutes_to_expiry is not None:
        floor_time_to_expiry(minutes_to_expiry, floor_minutes=floor_minutes)
    return True


def compute_gex(*, oi: Any, gamma: Any, price: Any, option_type: str = "call", contract_multiplier: float = 100.0) -> float:
    oi_value = safe_float(oi, 0.0) or 0.0
    gamma_value = safe_float(gamma, 0.0) or 0.0
    price_value = safe_float(price, 0.0) or 0.0
    base = oi_value * contract_multiplier * gamma_value * (price_value ** 2) * 0.01
    return float(base if str(option_type).lower() == "call" else -base)


def compute_net_gex(contracts: Sequence[Mapping[str, Any]] | None = None, *, default_price: Any = None) -> float:
    total = 0.0
    for contract in contracts or []:
        if not _is_active_contract(contract):
            continue
        price = contract.get("underlying_price") or contract.get("price") or default_price or contract.get("strike")
        total += compute_gex(
            oi=contract.get("open_interest"),
            gamma=contract.get("gamma"),
            price=price,
            option_type=str(contract.get("option_type") or contract.get("type") or "call"),
        )
    return float(total)


def compute_vanna(*, d2: Any, sigma: Any, gamma: Any) -> float:
    sigma_value = safe_float(sigma, 0.0) or 0.0
    gamma_value = safe_float(gamma, 0.0) or 0.0
    d2_value = safe_float(d2, 0.0) or 0.0
    if sigma_value == 0.0:
        return 0.0
    return float((-(d2_value / sigma_value)) * gamma_value)


def compute_vanna_exposure(*, oi: Any, d2: Any, sigma: Any, gamma: Any, price: Any) -> float:
    vanna = compute_vanna(d2=d2, sigma=sigma, gamma=gamma)
    oi_value = safe_float(oi, 0.0) or 0.0
    price_value = safe_float(price, 0.0) or 0.0
    return float(oi_value * 100.0 * vanna * price_value * 0.01)


def floor_time_to_expiry(minutes_to_expiry: Any, *, floor_minutes: float = 1.0) -> float:
    minutes = safe_float(minutes_to_expiry, 0.0) or 0.0
    if minutes <= 0.0:
        return 0.0
    return max(float(floor_minutes), minutes)


def classify_dte_bucket(days_to_expiry: Any) -> str:
    dte = safe_float(days_to_expiry, 0.0) or 0.0
    if dte <= 2:
        return "0-2 DTE"
    if dte <= 7:
        return "Weekly"
    if dte <= 45:
        return "Monthly"
    return "Long Dated"


def build_options_intelligence_report(
    payload: Mapping[str, Any] | None = None,
    /,
    **overrides: Any,
) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    contracts = [dict(contract) for contract in data.get("contracts") or [] if isinstance(contract, Mapping)]
    price = safe_float(data.get("underlying_price") or data.get("price") or data.get("current_price_or_odds")) or 0.0
    gex_by_tenor: dict[str, float] = defaultdict(float)
    call_wall = {"strike": None, "gex": None}
    put_wall = {"strike": None, "gex": None}
    gamma_flip = None
    trend_probability = 50.0
    pinning = 0.0
    for contract in contracts:
        if not _is_active_contract(contract):
            continue
        strike = safe_float(contract.get("strike"))
        days_to_expiry = safe_float(_first_defined(contract.get("days_to_expiry"), contract.get("dte")))
        minutes_to_expiry = safe_float(_first_defined(contract.get("minutes_to_expiry"), contract.get("time_to_expiry_minutes")))
        if minutes_to_expiry is not None:
            minutes_to_expiry = floor_time_to_expiry(minutes_to_expiry)
        if strike is not None and price and abs(strike - price) / max(price, 1.0) > 2.0:
            continue
        dte = classify_dte_bucket(_first_defined(days_to_expiry, contract.get("dte"), 0))
        gex = compute_gex(
            oi=contract.get("open_interest"),
            gamma=contract.get("gamma"),
            price=contract.get("underlying_price") or price,
            option_type=str(contract.get("option_type") or "call"),
        )
        gex_by_tenor[dte] += gex
        if str(contract.get("option_type") or "").lower() == "call":
            if call_wall["gex"] is None or gex > float(call_wall["gex"]):
                call_wall = {"strike": strike, "gex": round(gex, 4)}
        else:
            if put_wall["gex"] is None or gex < float(put_wall["gex"]):
                put_wall = {"strike": strike, "gex": round(gex, 4)}
        if gamma_flip is None and strike is not None and price and strike >= price:
            gamma_flip = strike
    net_gex = compute_net_gex(contracts, default_price=price)
    vanna_profile = sum(
        compute_vanna_exposure(
            oi=contract.get("open_interest"),
            d2=contract.get("d2") or contract.get("days_to_expiry"),
            sigma=contract.get("iv") or contract.get("implied_volatility"),
            gamma=contract.get("gamma"),
            price=contract.get("underlying_price") or price,
        )
        for contract in contracts
    )
    if price:
        pinning = clamp(50.0 + (net_gex / max(price * 1000.0, 1.0)) * 50.0)
        trend_probability = clamp(50.0 + (net_gex / max(abs(price) * 100.0, 1.0)) * 10.0)
    return build_market_intelligence_report(
        {
            "market": "options/stocks",
            "symbol_or_event": str(data.get("symbol") or data.get("underlying_symbol") or ""),
            "current_price_or_odds": price,
            "bias": "bullish" if net_gex > 0 else "bearish" if net_gex < 0 else "neutral",
            "confidence": clamp(weighted_average(((abs(net_gex), 0.5), (abs(vanna_profile), 0.35), (len(contracts), 0.15))) or 0.0),
            "primary_target": data.get("primary_target") or round(price * 1.02, 4),
            "secondary_target": data.get("secondary_target") or round(price * 1.05, 4),
            "stretch_target": data.get("stretch_target") or round(price * 1.08, 4),
            "expected_move": data.get("expected_move") or round(abs(net_gex) / max(price * 1000.0, 1.0), 4),
            "support": data.get("support") or round(price * 0.98, 4),
            "resistance": data.get("resistance") or round(price * 1.02, 4),
            "liquidity_zones": data.get("liquidity_zones") or [],
            "positioning_summary": "Dealer-positioning convention: call GEX positive, put GEX negative; net GEX sums signed exposures.",
            "flow_summary": f"gex={round(net_gex, 4)}; vanna_exposure={round(vanna_profile, 4)}; tenor={dict(gex_by_tenor)}",
            "catalysts": compact_list(data.get("catalysts") or data.get("news_catalysts"), limit=10),
            "trade_plan": "Use options positioning as a modeling convention only; no live trading.",
            "risk": "0DTE stale OI and far-OTM strikes filtered; treat intraday OI as stale.",
            "stop": data.get("stop") or round(price * 0.97, 4),
            "invalidation": data.get("invalidation") or "price breaks gamma-flip / support structure",
            "reasoning": [
                f"net_gex={round(net_gex, 4)}",
                f"vanna_exposure={round(vanna_profile, 4)}",
                f"call_wall={call_wall}",
                f"put_wall={put_wall}",
                f"gamma_flip={gamma_flip}",
            ],
            "no_trade_reason": data.get("no_trade_reason") or ("expired_contracts_ignored" if not contracts else "none"),
            "gex_profile": round(net_gex, 4),
            "vanna_profile": round(vanna_profile, 4),
            "call_wall": call_wall,
            "put_wall": put_wall,
            "gamma_flip": gamma_flip,
            "expected_pinning": round(pinning, 4),
            "trend_probability": round(trend_probability, 4),
            "gex_by_tenor": {key: round(value, 4) for key, value in gex_by_tenor.items()},
            "dte_bucket": classify_dte_bucket(data.get("days_to_expiry") or data.get("dte") or 0),
        },
    )
