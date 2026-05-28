from __future__ import annotations

def evaluate_cross_book_gate(**kwargs):
    blocked = []
    if float(kwargs.get("market_identity_confidence", 100)) < 80: blocked.append("low_market_identity")
    if kwargs.get("stale_data", False): blocked.append("stale_data")
    if kwargs.get("odds_timestamp_mismatch", False): blocked.append("odds_timestamp_mismatch")
    if kwargs.get("false_arbitrage_risk", False): blocked.append("false_arbitrage_risk")
    if kwargs.get("settlement_mismatch", False): blocked.append("settlement_mismatch")
    if float(kwargs.get("liquidity_score", 100)) < 60: blocked.append("low_liquidity")
    return {**kwargs, "cross_book_gate_result": "approved" if not blocked else "blocked_by_governance", "blocked_reasons": blocked}
