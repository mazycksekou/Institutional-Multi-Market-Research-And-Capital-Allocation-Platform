from __future__ import annotations

from typing import Any


def _index_rows(rows: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("contract_id") or row.get("ticker") or "").upper()
        if key:
            indexed[key] = row
    return indexed


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _change_category(previous: dict[str, Any], current: dict[str, Any], *, probability_move_threshold: float, price_move_threshold: float) -> list[str]:
    reasons: list[str] = []
    if not previous:
        reasons.append("new_market")
    prev_prob = _to_float(previous.get("implied_probability"))
    cur_prob = _to_float(current.get("implied_probability"))
    if prev_prob is not None and cur_prob is not None and abs(cur_prob - prev_prob) >= probability_move_threshold:
        reasons.append("probability_move")
    prev_yes = _to_float(previous.get("yes_price"))
    cur_yes = _to_float(current.get("yes_price"))
    if prev_yes is not None and cur_yes is not None and abs(cur_yes - prev_yes) >= price_move_threshold:
        reasons.append("price_move")
    prev_liq = _to_float(previous.get("liquidity_score"))
    cur_liq = _to_float(current.get("liquidity_score"))
    if prev_liq is not None and cur_liq is not None and abs(cur_liq - prev_liq) >= 0.1:
        reasons.append("liquidity_change")
    if bool(current.get("low_liquidity")):
        reasons.append("low_liquidity")
    if bool(current.get("close_time_approaching")):
        reasons.append("close_time_approaching")
    if bool(current.get("stale_market")):
        reasons.append("stale_market")
    if str(previous.get("status") or "") != str(current.get("status") or ""):
        reasons.append("status_change")
    if bool(current.get("partial_pricing")):
        reasons.append("partial_pricing")
    return reasons


def summarize_snapshot_health(snapshot_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "records_received": int(snapshot_summary.get("records_received", 0)),
        "records_valid": int(snapshot_summary.get("records_valid", 0)),
        "records_rejected": int(snapshot_summary.get("records_rejected", 0)),
        "blockers": list(snapshot_summary.get("blockers", []))[:10],
        "http_status": snapshot_summary.get("http_status"),
        "error_category": snapshot_summary.get("error_category"),
    }


def monitor_kalshi_market(
    *,
    previous_snapshot: list[dict[str, Any]] | None,
    current_snapshot: list[dict[str, Any]] | None,
    provider: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    thresholds = config.get("kalshi_monitor", {})
    probability_move_threshold = float(thresholds.get("probability_move_threshold", 0.03))
    price_move_threshold = float(thresholds.get("price_move_threshold", 0.03))
    previous_index = _index_rows(previous_snapshot)
    current_index = _index_rows(current_snapshot)
    candidates: list[dict[str, Any]] = []
    reason_counts: dict[str, int] = {}
    for key, current in current_index.items():
        previous = previous_index.get(key, {})
        reasons = _change_category(
            previous,
            current,
            probability_move_threshold=probability_move_threshold,
            price_move_threshold=price_move_threshold,
        )
        if not reasons:
            continue
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        candidates.append(
            {
                "source": "kalshi_monitor",
                "provider": provider,
                "provider_id": "kalshi_prediction_market",
                "source_type": "prediction_market",
                "market_type": "prediction_market",
                "recommendation_status": "review_only",
                "execution_allowed": False,
                "human_approval_required": True,
                "ticker": current.get("ticker"),
                "contract_id": current.get("contract_id"),
                "event_name": current.get("event_title"),
                "contract_title": current.get("contract_title"),
                "yes_bid": current.get("yes_bid"),
                "yes_ask": current.get("yes_ask"),
                "no_bid": current.get("no_bid"),
                "no_ask": current.get("no_ask"),
                "yes_price": current.get("yes_price"),
                "no_price": current.get("no_price"),
                "implied_probability": current.get("implied_probability"),
                "liquidity_score": current.get("liquidity_score"),
                "volume": current.get("volume"),
                "open_interest": current.get("open_interest"),
                "close_time": current.get("close_time"),
                "status": current.get("status"),
                "settlement_rule_status": "present" if current.get("settlement_rule") else "missing",
                "pricing_quality": current.get("pricing_quality", "missing"),
                "price_source": current.get("price_source", "missing"),
                "derived_price": bool(current.get("derived_price", False)),
                "partial_pricing": bool(current.get("partial_pricing", False)),
                "reason": reasons[0],
                "reason_codes": reasons,
            }
        )
    return {
        "snapshot": {
            "provider": provider,
            "previous_count": len(previous_index),
            "current_count": len(current_index),
        },
        "reason_counts": reason_counts,
        "candidates": candidates,
    }
