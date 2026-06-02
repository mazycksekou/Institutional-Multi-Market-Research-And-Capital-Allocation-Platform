from __future__ import annotations

from typing import Any

from .balance_sheet_risk import evaluate_balance_sheet
from .candlestick_pattern_detector import detect_candlestick_patterns
from .liquidity_context_scoring import calculate_float_rotation, score_liquidity_context
from .scheduler_config import safe_run_id, utc_now_iso
from .session_risk_rules import evaluate_session_risk, score_time_of_day


SAFETY_FLAGS = {
    "provider_write": False,
    "execution_allowed": False,
    "live_execution_enabled": False,
    "auto_execution": False,
    "auto_execution_enabled": False,
    "human_approval_required": True,
    "broker_order_execution_enabled": False,
    "crypto_trade_execution_enabled": False,
    "stock_trade_execution_enabled": False,
    "actual_orders_submitted": 0,
    "actual_bets_submitted": 0,
    "actual_trades_submitted": 0,
    "raw_payload_included": False,
    "secrets_included": False,
    "review_only": True,
}


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def score_price_band(price: Any) -> dict[str, Any]:
    parsed = _num(price)
    reasons: list[str] = []
    if parsed is None or parsed <= 0:
        return {
            "price": parsed,
            "price_band": "data_insufficient",
            "price_range_quality_score": 0.0,
            "small_account_fit_score": 0.0,
            "overextension_risk": 100.0,
            "no_review_reasons": ["missing_or_invalid_price"],
        }
    if 3.0 <= parsed <= 12.0:
        band = "preferred_3_to_12"
        quality = 94.0
        overextension = 18.0
    elif 2.0 <= parsed <= 20.0:
        band = "acceptable_2_to_20"
        quality = 78.0
        overextension = 30.0
    elif parsed < 2.0:
        band = "below_2_caution"
        quality = 34.0
        overextension = 70.0
        reasons.append("sub_2_dollar_caution")
    elif parsed > 50.0:
        band = "above_50_caution"
        quality = 42.0
        overextension = 58.0
        reasons.append("above_50_requires_liquidity_options_or_context")
    else:
        band = "extended_20_to_50"
        quality = 58.0
        overextension = 45.0
        reasons.append("outside_small_account_preferred_range")
    return {
        "price": parsed,
        "price_band": band,
        "price_range_quality_score": quality,
        "small_account_fit_score": quality,
        "overextension_risk": overextension,
        "no_review_reasons": reasons,
    }


def score_low_float_high_demand(row: dict[str, Any]) -> dict[str, Any]:
    price = _num(row.get("price"))
    float_shares = _num(row.get("float_shares"))
    daily_volume = _num(row.get("daily_volume", row.get("volume")))
    relative_volume = _num(row.get("relative_volume", row.get("volume_ratio")), 0.0) or 0.0
    intraday_change = _num(row.get("intraday_percent_change", row.get("price_change_percent")), 0.0) or 0.0
    catalyst_detected = bool(row.get("catalyst_detected", row.get("has_catalyst", False)))
    catalyst_type = row.get("catalyst_type") or ("unknown_catalyst" if catalyst_detected else None)
    catalyst_quality_score = _num(row.get("catalyst_quality_score"), 80.0 if catalyst_detected else 0.0) or 0.0
    dollar_volume = _num(row.get("dollar_volume"))
    if dollar_volume is None and price is not None and daily_volume is not None:
        dollar_volume = price * daily_volume
    float_rotation = calculate_float_rotation(daily_volume, float_shares)

    demand_score = 0.0
    demand_score += 25.0 if intraday_change >= 10.0 else max(0.0, intraday_change) * 1.5
    demand_score += 25.0 if relative_volume >= 5.0 else relative_volume * 4.0
    demand_score += 22.0 if catalyst_detected else 0.0
    demand_score += 18.0 if dollar_volume and dollar_volume >= 2_000_000 else (8.0 if dollar_volume and dollar_volume >= 500_000 else 0.0)
    if float_rotation is not None:
        demand_score += min(10.0, float_rotation * 4.0)
    demand_score = _clamp(demand_score)

    if float_shares is None or float_shares <= 0:
        supply_score = 0.0
    elif float_shares < 10_000_000:
        supply_score = 92.0
    elif float_shares < 30_000_000:
        supply_score = 68.0
    elif float_shares < 100_000_000:
        supply_score = 44.0
    else:
        supply_score = 24.0

    rotation_bonus = 0.0 if float_rotation is None else min(18.0, float_rotation * 6.0)
    rate_of_change_score = _clamp(intraday_change * 2.0 + relative_volume * 6.0 + rotation_bonus)
    halt_risk_score = _clamp(max(0.0, intraday_change - 20.0) * 1.2 + (float_rotation or 0.0) * 6.0)
    dilution_risk_score = _clamp(float(row.get("dilution_risk_score", 0.0) or 0.0))
    offering_risk_score = _clamp(float(row.get("offering_risk_score", 0.0) or 0.0))
    risk_penalty = halt_risk_score * 0.12 + dilution_risk_score * 0.15 + offering_risk_score * 0.15
    low_float_momentum_score = _clamp(demand_score * 0.42 + supply_score * 0.28 + rate_of_change_score * 0.30 - risk_penalty)

    blockers: list[str] = []
    if float_shares is None:
        blockers.append("missing_float")
    elif float_shares >= 10_000_000:
        blockers.append("float_above_low_float_threshold")
    if intraday_change < 10.0:
        blockers.append("intraday_change_below_10_percent")
    if relative_volume < 5.0:
        blockers.append("relative_volume_below_5x")
    if not catalyst_detected:
        blockers.append("missing_real_catalyst")
    price_band = score_price_band(price)
    if price_band["price_band"] not in {"preferred_3_to_12", "acceptable_2_to_20"}:
        blockers.extend(price_band["no_review_reasons"])
    if float_shares is not None and float_shares < 10_000_000 and not catalyst_detected:
        blockers.append("low_float_without_catalyst_is_risk")

    return {
        "float_shares": float_shares,
        "daily_volume": daily_volume,
        "relative_volume": relative_volume,
        "dollar_volume": round(dollar_volume, 2) if dollar_volume is not None else None,
        "float_rotation": float_rotation,
        "intraday_percent_change": intraday_change,
        "catalyst_detected": catalyst_detected,
        "catalyst_type": catalyst_type,
        "catalyst_quality_score": round(_clamp(catalyst_quality_score), 2),
        "demand_score": round(demand_score, 2),
        "supply_score": round(supply_score, 2),
        "rate_of_change_score": round(rate_of_change_score, 2),
        "halt_risk_score": round(halt_risk_score, 2),
        "dilution_risk_score": round(dilution_risk_score, 2),
        "offering_risk_score": round(offering_risk_score, 2),
        "low_float_momentum_score": round(low_float_momentum_score, 2),
        "low_float_blockers": sorted(set(blockers)),
    }


def calculate_risk_reward(
    entry_price: Any,
    stop_loss: Any,
    target_price: Any,
    *,
    estimated_true_win_rate: Any = None,
    paper_account_equity: Any = None,
    paper_risk_fraction: float = 0.01,
    direction: str = "bullish",
) -> dict[str, Any]:
    entry = _num(entry_price)
    stop = _num(stop_loss)
    target = _num(target_price)
    direction = str(direction or "bullish").lower()
    blockers: list[str] = []
    if entry is None or stop is None or target is None or entry <= 0:
        blockers.append("missing_risk_reward_prices")
        risk = reward = ratio = breakeven = None
    elif direction == "bearish":
        risk = stop - entry
        reward = entry - target
        ratio = reward / risk if risk > 0 else None
        breakeven = risk / (reward + risk) if risk and reward and reward > 0 and risk > 0 else None
    else:
        risk = entry - stop
        reward = target - entry
        ratio = reward / risk if risk > 0 else None
        breakeven = risk / (reward + risk) if risk and reward and reward > 0 and risk > 0 else None
    if risk is not None and risk <= 0:
        blockers.append("invalid_stop_loss")
    if reward is not None and reward <= 0:
        blockers.append("invalid_target")
    if ratio is None:
        permission = "DATA_INSUFFICIENT"
        score = 0.0
    elif ratio < 1.0:
        permission = "BLOCKED"
        score = 25.0
        blockers.append("reward_risk_below_1_to_1")
    elif ratio < 1.5:
        permission = "WATCHLIST_ONLY"
        score = 55.0
    elif ratio < 2.0:
        permission = "REVIEW_ALLOWED_WITH_CAUTION"
        score = 72.0
    else:
        permission = "VALID"
        score = min(96.0, 70.0 + ratio * 8.0)
    estimated = _num(estimated_true_win_rate)
    if estimated is not None and estimated > 1.0:
        estimated = estimated / 100.0
    edge_over_breakeven = None
    if estimated is not None and breakeven is not None:
        edge_over_breakeven = round(estimated - breakeven, 6)
        if edge_over_breakeven < 0:
            blockers.append("estimated_win_rate_below_breakeven")
    account_equity = _num(paper_account_equity)
    max_loss = None
    position_size = None
    if account_equity is not None and account_equity > 0 and risk is not None and risk > 0:
        max_loss = account_equity * max(0.0, min(float(paper_risk_fraction), 0.05))
        position_size = max_loss / risk
    return {
        "entry_price": entry,
        "stop_loss": stop,
        "target_price": target,
        "risk_per_share": round(risk, 6) if risk is not None else None,
        "reward_per_share": round(reward, 6) if reward is not None else None,
        "reward_risk_ratio": round(ratio, 6) if ratio is not None else None,
        "breakeven_win_rate": round(breakeven, 6) if breakeven is not None else None,
        "estimated_true_win_rate": estimated,
        "edge_over_breakeven": edge_over_breakeven,
        "max_loss_if_wrong": round(max_loss, 2) if max_loss is not None else None,
        "position_size_paper_only": round(position_size, 6) if position_size is not None else None,
        "risk_reward_permission_status": permission,
        "risk_reward_score": round(score, 2),
        "risk_reward_blockers": sorted(set(blockers)),
        "paper_only": True,
        "execution_allowed": False,
    }


def score_a_quality_setup(
    *,
    catalyst_quality_score: Any = 0.0,
    liquidity_quality_score: Any = 0.0,
    setup_quality_score: Any = 0.0,
    spread_quality_score: Any = 0.0,
    risk_quality_score: Any = 0.0,
    repeatability_score: Any = 0.0,
    track_record_support_score: Any = 0.0,
) -> dict[str, Any]:
    values = {
        "catalyst_quality_score": _clamp(_num(catalyst_quality_score, 0.0) or 0.0),
        "liquidity_quality_score": _clamp(_num(liquidity_quality_score, 0.0) or 0.0),
        "setup_quality_score": _clamp(_num(setup_quality_score, 0.0) or 0.0),
        "spread_quality_score": _clamp(_num(spread_quality_score, 0.0) or 0.0),
        "risk_quality_score": _clamp(_num(risk_quality_score, 0.0) or 0.0),
        "repeatability_score": _clamp(_num(repeatability_score, 0.0) or 0.0),
        "track_record_support_score": _clamp(_num(track_record_support_score, 0.0) or 0.0),
    }
    stock_quality_score = (
        values["catalyst_quality_score"] * 0.18
        + values["liquidity_quality_score"] * 0.20
        + values["setup_quality_score"] * 0.20
        + values["spread_quality_score"] * 0.12
        + values["risk_quality_score"] * 0.14
        + values["repeatability_score"] * 0.10
        + values["track_record_support_score"] * 0.06
    )
    values["stock_quality_score"] = round(stock_quality_score, 2)
    values["a_quality_candidate"] = stock_quality_score >= 85.0
    return values


def build_detection_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_symbol": row.get("asset_symbol") or row.get("symbol") or row.get("ticker") or "UNKNOWN",
        "asset_type": row.get("asset_type") or "stock",
        "timeframe": row.get("timeframe") or "5m",
        "detected_at": row.get("detected_at") or utc_now_iso(),
        "vwap": row.get("vwap"),
        "opening_range_high": row.get("opening_range_high"),
        "previous_close": row.get("previous_close"),
        "pullback_high": row.get("pullback_high"),
        "prior_high": row.get("prior_high"),
        "breakout_confirmation_score": row.get("breakout_confirmation_score", 50.0),
    }


def candidate_from_row(row: dict[str, Any], *, session_state: dict[str, Any] | None = None) -> dict[str, Any]:
    from .pattern_review_queue import build_pattern_review_item

    asset_symbol = str(row.get("asset_symbol") or row.get("symbol") or row.get("ticker") or "UNKNOWN").upper()
    asset_type = str(row.get("asset_type") or "stock").lower()
    context = build_detection_context(row)
    detections = list(row.get("detections") or [])
    if not detections:
        detections = detect_candlestick_patterns(row.get("candles") or [], context)
    if not detections and row.get("pattern_id"):
        detected_at = row.get("detected_at") or utc_now_iso()
        trigger = _num(row.get("trigger_price", row.get("entry_price", row.get("price"))), 0.0) or 0.0
        stop = _num(row.get("stop_loss", row.get("stop_loss_level")), trigger * 0.97 if trigger else 0.0) or 0.0
        target = _num(row.get("target_price"), trigger + (trigger - stop) * 2.0 if trigger and stop else 0.0) or 0.0
        detections = [
            {
                "detection_id": safe_run_id("manual_pattern_detection", f"{asset_symbol}|{row.get('pattern_id')}|{detected_at}|{trigger}"),
                "asset_symbol": asset_symbol,
                "asset_type": asset_type,
                "timeframe": row.get("timeframe") or "unknown",
                "pattern_id": row.get("pattern_id"),
                "pattern_name": row.get("pattern_name") or row.get("pattern_id"),
                "pattern_family": row.get("pattern_family") or "manual",
                "direction": row.get("direction") or "bullish",
                "detected_at": detected_at,
                "trigger_price": trigger,
                "invalidation_price": stop,
                "target_price": target,
                "pattern_quality_score": _num(row.get("pattern_quality_score"), 60.0) or 60.0,
                "pattern_base_priority_score": _num(row.get("pattern_base_priority_score"), 60.0) or 60.0,
                "volume_confirmation_score": _num(row.get("volume_confirmation_score"), 50.0) or 50.0,
                "breakout_confirmation_score": _num(row.get("breakout_confirmation_score"), 50.0) or 50.0,
                "failed_pattern_risk": _num(row.get("failed_pattern_risk"), 40.0) or 40.0,
                "entry_trigger_price": trigger,
                "stop_loss_level": stop,
                "reward_risk_ratio": None,
            }
        ]

    liquidity = score_liquidity_context(row, asset_type=asset_type)
    price_band = score_price_band(row.get("price"))
    low_float = score_low_float_high_demand(row) if asset_type == "stock" else {}
    time_score = score_time_of_day(row.get("detected_at"), minutes_since_midnight=row.get("minutes_since_midnight"))
    balance = evaluate_balance_sheet(row.get("balance_sheet") if isinstance(row.get("balance_sheet"), dict) else row)
    session = evaluate_session_risk(session_state or row.get("session") or {})
    items = []
    for detection in detections:
        rr = calculate_risk_reward(
            detection.get("entry_trigger_price") or detection.get("trigger_price") or row.get("entry_price") or row.get("price"),
            detection.get("stop_loss_level") or detection.get("invalidation_price") or row.get("stop_loss"),
            detection.get("target_price") or row.get("target_price"),
            estimated_true_win_rate=row.get("estimated_true_win_rate"),
            paper_account_equity=row.get("paper_account_equity"),
            direction=str(detection.get("direction") or "bullish"),
        )
        quality = score_a_quality_setup(
            catalyst_quality_score=low_float.get("catalyst_quality_score", row.get("catalyst_quality_score", 0.0)),
            liquidity_quality_score=liquidity.get("liquidity_score", 0.0),
            setup_quality_score=detection.get("pattern_quality_score", 0.0),
            spread_quality_score=liquidity.get("spread_slippage_score", 0.0),
            risk_quality_score=rr.get("risk_reward_score", 0.0),
            repeatability_score=row.get("repeatability_score", 50.0),
            track_record_support_score=row.get("track_record_support_score", 50.0),
        )
        item = build_pattern_review_item(
            detection=detection,
            liquidity=liquidity,
            catalyst=low_float or {"catalyst_quality_score": row.get("catalyst_quality_score", 0.0), "catalyst_detected": bool(row.get("catalyst_detected", False)), "catalyst_type": row.get("catalyst_type")},
            time_context=time_score,
            risk_reward=rr,
            balance_sheet=balance,
            price_band=price_band,
            session_risk=session,
            quality=quality,
            historical_calibration_score=row.get("historical_calibration_score"),
            micro_calibration_score=row.get("micro_calibration_score"),
            trade_window_calibration_score=row.get("trade_window_calibration_score"),
            special_catalyst=bool(row.get("special_catalyst", False)),
        )
        items.append(item)
    return {
        "asset_symbol": asset_symbol,
        "asset_type": asset_type,
        "detections": detections,
        "review_items": items,
        "liquidity": liquidity,
        "price_band": price_band,
        "low_float_momentum": low_float,
        "time_context": time_score,
        "balance_sheet": balance,
        "session_risk": session,
        **SAFETY_FLAGS,
    }


def run_small_account_review(
    items: list[dict[str, Any]] | None = None,
    *,
    session_state: dict[str, Any] | None = None,
    persist_queue: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from .pattern_review_queue import persist_pattern_review_queue, summarize_pattern_review_queue

    rows = [row for row in (items or []) if isinstance(row, dict)]
    candidate_results = [candidate_from_row(row, session_state=session_state) for row in rows]
    review_items = [item for result in candidate_results for item in result.get("review_items", [])]
    ordered = sorted(review_items, key=lambda row: (-float(row.get("review_priority_score", 0.0)), str(row.get("asset_symbol", ""))))
    persistence = {}
    if persist_queue:
        persistence = persist_pattern_review_queue(ordered, base_data_dir=base_data_dir)
    summary = summarize_pattern_review_queue(ordered)
    return {
        "ok": True,
        "status": "review_candidates_created",
        "items_scanned": len(rows),
        "detections_created": sum(len(result.get("detections", [])) for result in candidate_results),
        "review_queue_count": len(ordered),
        "active_review_count": summary.get("active_review_count", 0),
        "watchlist_review_count": summary.get("watchlist_review_count", 0),
        "no_review_count": summary.get("no_review_count", 0),
        "items": ordered,
        "summary": summary,
        "local_analyst_review": build_local_analyst_review(ordered, summary),
        "persisted": bool(persistence),
        **persistence,
        **SAFETY_FLAGS,
    }


def build_local_analyst_review(review_items: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    risk_flags: list[str] = []
    missing_inputs: list[str] = []
    for item in review_items:
        if item.get("queue_status") in {"NO_TRADE", "NO_TRADE_SESSION_LOCK", "NO_REVIEW"}:
            risk_flags.extend(item.get("no_trade_reasons") or [])
        if item.get("balance_sheet_risk_bucket") == "data_insufficient":
            missing_inputs.append(f"balance_sheet:{item.get('asset_symbol')}")
        if item.get("micro_calibration_score") is None:
            missing_inputs.append(f"micro_calibration:{item.get('asset_symbol')}")
        if item.get("trade_window_calibration_score") is None:
            missing_inputs.append(f"trade_window_calibration:{item.get('asset_symbol')}")
    action = "needs_human_review" if int(summary.get("active_review_count", 0) or 0) or int(summary.get("watchlist_review_count", 0) or 0) else "continue_collecting"
    return {
        "status": "local_review_complete",
        "enabled": True,
        "external_model_called": False,
        "recommended_action": action,
        "risk_flags": sorted(set(str(flag) for flag in risk_flags if flag))[:25],
        "missing_inputs": sorted(set(str(item) for item in missing_inputs if item))[:25],
        "must_not_execute": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "reviewer_side_effects": "none",
    }
