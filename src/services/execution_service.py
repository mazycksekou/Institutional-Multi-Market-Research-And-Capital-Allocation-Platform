"""Canonical execution helper service for disabled live-shaped execution flows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automation_scheduler.balance_sheet_risk import evaluate_balance_sheet
from automation_scheduler.candlestick_pattern_detector import detect_candlestick_patterns
from automation_scheduler.data_paths import get_storage_health, resolve_base_data_dir
from automation_scheduler.liquidity_context_scoring import calculate_float_rotation, score_liquidity_context
from automation_scheduler.scheduler_config import safe_run_id, sanitize_filename, utc_now_iso
from automation_scheduler.session_risk_rules import evaluate_session_risk, score_time_of_day
from automation_scheduler.institutional_cross_asset_adapters import compact_redact, read_existing_outputs
from automation_scheduler.institutional_cross_asset_calibration import build_calibration_by_asset_class
from automation_scheduler.institutional_risk_engine import assess_institutional_risk
from automation_scheduler.strategy_context_buckets import build_context_bucket
from src.services.ledger_service import append_audit_record


BROKER_STATUSES = {"RESEARCH_ONLY", "PAPER_SUPPORTED", "SANDBOX_READY", "NOT_APPROVED"}

MANIFOLD_TRAP_SCHEMA_VERSION = "automation_scheduler.v1.market_state_manifold.no_bet_traps.v1"
MIN_TRAP_STATS_SAMPLE = 30

EXECUTION_SAFETY_FLAGS = {
    "dry_run": True,
    "simulation_only": True,
    "live_execution_enabled": False,
    "provider_write": False,
    "execution_allowed": False,
    "auto_execution": False,
    "auto_execution_enabled": False,
    "human_approval_required": True,
    "owner_approval_required": True,
    "requires_human_command": True,
    "actual_order_submitted": False,
    "actual_bet_submitted": False,
    "actual_trade_submitted": False,
    "actual_orders_submitted": 0,
    "actual_bets_submitted": 0,
    "actual_trades_submitted": 0,
    "actual_crypto_swaps_submitted": 0,
    "kalshi_order_execution_enabled": False,
    "sportsbook_bet_execution_enabled": False,
    "broker_order_execution_enabled": False,
    "crypto_trade_execution_enabled": False,
    "stock_trade_execution_enabled": False,
}

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

LIVE_FLAG_FIELDS = (
    "live_execution_requested",
    "submit_live_order",
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "auto_execution_enabled",
    "auto_bet_enabled",
    "auto_trade_enabled",
    "kalshi_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "broker_order_execution_enabled",
    "crypto_trade_execution_enabled",
    "stock_trade_execution_enabled",
    "owner_approval_present",
)


class ExecutionDeskRejected(ValueError):
    pass


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _unit(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if 0.0 <= parsed <= 1.0:
        return parsed
    return _clamp(parsed, 0.0, 100.0) / 100.0


def _score(value: Any, default: float = 0.0) -> float:
    return _unit(value, default=default) * 100.0


def score_broker_provider(row: dict[str, Any]) -> dict[str, Any]:
    reliability = _clamp(_num(row.get("api_reliability_score"), 50.0))
    uptime = _clamp(_num(row.get("uptime_score"), 50.0))
    latency = _clamp(_num(row.get("latency_score"), 50.0))
    order_types = _clamp(_num(row.get("order_type_support_score"), 50.0))
    fees = _clamp(_num(row.get("fee_score"), 50.0))
    spread_quality = _clamp(_num(row.get("spread_quality_score"), 50.0))
    slippage_risk = _clamp(_num(row.get("slippage_risk_score"), 50.0))
    execution_restriction_risk = _clamp(_num(row.get("execution_restriction_risk"), 50.0))
    compliance_risk = _clamp(_num(row.get("compliance_risk_score"), 50.0))
    paper_or_sandbox_support = bool(row.get("paper_or_sandbox_support", False))
    asset_types = list(row.get("asset_types_supported") or [])
    broker_quality_score = (
        reliability * 0.18
        + uptime * 0.16
        + latency * 0.12
        + order_types * 0.12
        + fees * 0.10
        + spread_quality * 0.14
        + (100.0 - slippage_risk) * 0.08
        + (100.0 - execution_restriction_risk) * 0.05
        + (100.0 - compliance_risk) * 0.05
    )
    broker_quality_score = round(_clamp(broker_quality_score), 2)
    if compliance_risk >= 80 or execution_restriction_risk >= 85:
        broker_status = "NOT_APPROVED"
    elif paper_or_sandbox_support and broker_quality_score >= 80 and reliability >= 75:
        broker_status = "SANDBOX_READY"
    elif paper_or_sandbox_support:
        broker_status = "PAPER_SUPPORTED"
    else:
        broker_status = "RESEARCH_ONLY"
    return {
        "broker_name": str(row.get("broker_name") or row.get("provider_name") or "unknown"),
        "provider_type": str(row.get("provider_type") or "broker_research"),
        "asset_types_supported": asset_types,
        "api_reliability_score": reliability,
        "uptime_score": uptime,
        "latency_score": latency,
        "order_type_support_score": order_types,
        "fee_score": fees,
        "spread_quality_score": spread_quality,
        "slippage_risk_score": slippage_risk,
        "paper_or_sandbox_support": paper_or_sandbox_support,
        "execution_restriction_risk": execution_restriction_risk,
        "compliance_risk_score": compliance_risk,
        "broker_quality_score": broker_quality_score,
        "broker_status": broker_status,
        "source_access_type": row.get("source_access_type", "research_metadata"),
        "current_phase_allowed": bool(row.get("current_phase_allowed", True)),
        "future_paid_candidate": bool(row.get("future_paid_candidate", False)),
        "requires_budget_approval": bool(row.get("requires_budget_approval", False)),
        "approval_status": row.get("approval_status", "needs_review"),
        "enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
    }


def default_broker_quality_rows() -> list[dict[str, Any]]:
    return [
        score_broker_provider(
            {
                "broker_name": "research_only_equity_broker_template",
                "provider_type": "broker_research",
                "asset_types_supported": ["stock", "etf"],
                "api_reliability_score": 70,
                "uptime_score": 70,
                "latency_score": 60,
                "order_type_support_score": 65,
                "fee_score": 70,
                "spread_quality_score": 60,
                "slippage_risk_score": 45,
                "paper_or_sandbox_support": True,
                "execution_restriction_risk": 45,
                "compliance_risk_score": 35,
                "approval_status": "needs_review",
            }
        ),
        score_broker_provider(
            {
                "broker_name": "research_only_crypto_exchange_template",
                "provider_type": "exchange_research",
                "asset_types_supported": ["crypto"],
                "api_reliability_score": 65,
                "uptime_score": 68,
                "latency_score": 62,
                "order_type_support_score": 58,
                "fee_score": 55,
                "spread_quality_score": 55,
                "slippage_risk_score": 55,
                "paper_or_sandbox_support": False,
                "execution_restriction_risk": 60,
                "compliance_risk_score": 60,
                "approval_status": "not_approved",
            }
        ),
    ]


def build_broker_quality_report(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    brokers = [score_broker_provider(row) for row in rows] if rows is not None else default_broker_quality_rows()
    status_counts: dict[str, int] = {}
    for broker in brokers:
        status = str(broker.get("broker_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "ok": True,
        "status": "ok",
        "broker_count": len(brokers),
        "status_counts": status_counts,
        "brokers": brokers,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
    }


def _score_price_band(price: Any) -> dict[str, Any]:
    parsed = _num(price, default=None)
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


score_price_band = _score_price_band


def _score_low_float_high_demand(row: dict[str, Any]) -> dict[str, Any]:
    price = _num(row.get("price"), default=None)
    float_shares = _num(row.get("float_shares"), default=None)
    daily_volume = _num(row.get("daily_volume", row.get("volume")), default=None)
    relative_volume = _num(row.get("relative_volume", row.get("volume_ratio")), 0.0) or 0.0
    intraday_change = _num(row.get("intraday_percent_change", row.get("price_change_percent")), 0.0) or 0.0
    catalyst_detected = bool(row.get("catalyst_detected", row.get("has_catalyst", False)))
    catalyst_type = row.get("catalyst_type") or ("unknown_catalyst" if catalyst_detected else None)
    catalyst_quality_score = _num(row.get("catalyst_quality_score"), 80.0 if catalyst_detected else 0.0) or 0.0
    dollar_volume = _num(row.get("dollar_volume"), default=None)
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
    price_band = _score_price_band(price)
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


score_low_float_high_demand = _score_low_float_high_demand


def _calculate_risk_reward(
    entry_price: Any,
    stop_loss: Any,
    target_price: Any,
    *,
    estimated_true_win_rate: Any = None,
    paper_account_equity: Any = None,
    paper_risk_fraction: float = 0.01,
    direction: str = "bullish",
) -> dict[str, Any]:
    entry = _num(entry_price, default=None)
    stop = _num(stop_loss, default=None)
    target = _num(target_price, default=None)
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
    estimated = _num(estimated_true_win_rate, default=None)
    if estimated is not None and estimated > 1.0:
        estimated = estimated / 100.0
    edge_over_breakeven = None
    if estimated is not None and breakeven is not None:
        edge_over_breakeven = round(estimated - breakeven, 6)
        if edge_over_breakeven < 0:
            blockers.append("estimated_win_rate_below_breakeven")
    account_equity = _num(paper_account_equity, default=None)
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


calculate_risk_reward = _calculate_risk_reward


def _score_a_quality_setup(
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


score_a_quality_setup = _score_a_quality_setup


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
    from automation_scheduler.pattern_review_queue import build_pattern_review_item

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
    price_band = _score_price_band(row.get("price"))
    low_float = _score_low_float_high_demand(row) if asset_type == "stock" else {}
    time_score = score_time_of_day(row.get("detected_at"), minutes_since_midnight=row.get("minutes_since_midnight"))
    balance = evaluate_balance_sheet(row.get("balance_sheet") if isinstance(row.get("balance_sheet"), dict) else row)
    session = evaluate_session_risk(session_state or row.get("session") or {})
    items = []
    for detection in detections:
        rr = _calculate_risk_reward(
            detection.get("entry_trigger_price") or detection.get("trigger_price") or row.get("entry_price") or row.get("price"),
            detection.get("stop_loss_level") or detection.get("invalidation_price") or row.get("stop_loss"),
            detection.get("target_price") or row.get("target_price"),
            estimated_true_win_rate=row.get("estimated_true_win_rate"),
            paper_account_equity=row.get("paper_account_equity"),
            direction=str(detection.get("direction") or "bullish"),
        )
        quality = _score_a_quality_setup(
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
    from automation_scheduler.pattern_review_queue import persist_pattern_review_queue, summarize_pattern_review_queue

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


def detect_manifold_trap(
    *,
    asset_type: str,
    cluster_id: str | None,
    cluster_name: str | None,
    normalized_features: dict[str, float] | None = None,
    cluster_stats: dict[str, Any] | None = None,
    source_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    features = normalized_features or {}
    stats = cluster_stats or {}
    item = source_item or {}
    reasons: list[str] = []
    score = 0.0

    confidence = _score(features.get("confidence_score", item.get("confidence_score")), default=0.0)
    edge = _score(features.get("estimated_edge", item.get("estimated_edge")), default=50.0)
    liquidity = _score(features.get("liquidity_score", item.get("liquidity_score")), default=50.0)
    spread_quality = _score(features.get("spread_score", item.get("spread_score")), default=50.0)
    stale = _score(features.get("stale_data_risk", item.get("stale_data_risk")), default=0.0)
    settlement_uncertainty = _score(features.get("settlement_uncertainty_score", item.get("settlement_uncertainty_score")), default=0.0)
    pricing_quality = _score(features.get("pricing_quality_score", item.get("pricing_quality_score")), default=50.0)
    pattern_failure = _score(features.get("breakout_failure_score", item.get("breakout_failure_score")), default=0.0)
    dilution = _score(features.get("dilution_risk_score", item.get("dilution_risk_score")), default=0.0)
    liquidation = _score(features.get("liquidation_cluster_risk", item.get("liquidation_cluster_risk")), default=0.0)
    correlation = _score(features.get("correlation_score", item.get("correlation_score")), default=0.0)
    live_latency = _score(features.get("live_latency_score", item.get("live_latency_score")), default=0.0)

    stats_sample = int(stats.get("sample_size", 0) or 0)
    stats_usable = stats_sample >= MIN_TRAP_STATS_SAMPLE and not bool(stats.get("insufficient_sample", True))
    win_rate = stats.get("win_rate") if stats_usable else None
    roi = stats.get("historical_roi", stats.get("average_return")) if stats_usable else None
    false_positive_rate = stats.get("false_positive_rate") if stats_usable else None
    false_breakout_rate = stats.get("false_breakout_rate") if stats_usable else None
    negative_ev_rate = stats.get("historical_negative_ev_rate") if stats_usable else None

    if confidence >= 70.0 and (win_rate is not None and float(win_rate) < 0.48 or _negative_metric(roi)):
        score += 28.0
        reasons.append("high_confidence_poor_realized_outcomes")
    if edge >= 70.0 and liquidity < 40.0:
        score += 20.0
        reasons.append("high_estimated_edge_low_liquidity")
    if edge >= 65.0 and spread_quality < 35.0:
        score += 20.0
        reasons.append("wide_spread_fake_edge")
    if stale >= 65.0:
        score += 16.0
        reasons.append("stale_line_or_price")
    if settlement_uncertainty >= 65.0:
        score += 16.0
        reasons.append("settlement_uncertainty_high")
    if pricing_quality < 35.0:
        score += 10.0
        reasons.append("poor_pricing_quality")
    if false_positive_rate is not None and float(false_positive_rate) >= 0.45:
        score += 20.0
        reasons.append("historical_false_positive_cluster")
    if negative_ev_rate is not None and float(negative_ev_rate) >= 0.55:
        score += 18.0
        reasons.append("historical_negative_ev_cluster")
    if false_breakout_rate is not None and float(false_breakout_rate) >= 0.35:
        score += 16.0
        reasons.append("historical_false_breakout_cluster")
    if pattern_failure >= 70.0:
        score += 14.0
        reasons.append("breakout_failure_context")
    if dilution >= 70.0:
        score += 16.0
        reasons.append("dilution_risk_momentum_trap")
    if liquidation >= 70.0:
        score += 14.0
        reasons.append("liquidation_cluster_risk")
    if asset_type == "sportsbook" and correlation >= 80.0 and live_latency >= 70.0:
        score += 12.0
        reasons.append("sports_correlation_latency_trap")
    if bool(item.get("stale_market")):
        score += 10.0
        if "stale_line_or_price" not in reasons:
            reasons.append("stale_line_or_price")

    score = round(_clamp(score), 2)
    action = _execution_action(asset_type) if score >= 80.0 else "LOW_PRIORITY_REVIEW" if score >= 65.0 else "WATCHLIST_REVIEW"
    no_bet_score = score if asset_type in {"prediction_market", "sportsbook"} else min(score, 35.0)
    no_trade_score = score if asset_type in {"stock", "crypto", "etf", "bond_rate", "major_asset"} else min(score, 35.0)
    return {
        "trap_cluster_detected": score >= 65.0,
        "trap_cluster_id": cluster_id if score >= 65.0 else None,
        "trap_cluster_name": cluster_name if score >= 65.0 else None,
        "no_bet_trap_score": round(no_bet_score, 2),
        "no_trade_trap_score": round(no_trade_score, 2),
        "historical_false_positive_rate": false_positive_rate,
        "historical_negative_ev_rate": negative_ev_rate,
        "trap_reasons": reasons[:10],
        "recommended_action": action,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _negative_metric(value: Any) -> bool:
    try:
        if value is None:
            return False
        return float(value) < 0.0
    except (TypeError, ValueError):
        return False


def _execution_action(asset_type: str) -> str:
    if asset_type in {"stock", "crypto", "etf", "bond_rate", "major_asset"}:
        return "NO_TRADE"
    return "NO_BET"


def _traps_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "manifold" / "no_bet_traps"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _traps_dir(base_data_dir) / "latest.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def write_trap_report(traps: list[dict[str, Any]], *, base_data_dir: str = "data") -> dict[str, Any]:
    safe_traps = [
        {
            "trap_cluster_detected": bool(row.get("trap_cluster_detected")),
            "trap_cluster_id": row.get("trap_cluster_id"),
            "trap_cluster_name": row.get("trap_cluster_name"),
            "no_bet_trap_score": row.get("no_bet_trap_score"),
            "no_trade_trap_score": row.get("no_trade_trap_score"),
            "historical_false_positive_rate": row.get("historical_false_positive_rate"),
            "historical_negative_ev_rate": row.get("historical_negative_ev_rate"),
            "trap_reasons": list(row.get("trap_reasons") or [])[:10],
            "recommended_action": row.get("recommended_action"),
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
            "raw_payload_included": False,
            "secrets_included": False,
        }
        for row in traps
        if isinstance(row, dict)
    ]
    payload = {
        "ok": True,
        "schema_version": MANIFOLD_TRAP_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "trap_count": len([row for row in safe_traps if row.get("trap_cluster_detected")]),
        "items": safe_traps,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_backend": "file",
    }
    latest = _latest_path(base_data_dir)
    history = _traps_dir(base_data_dir) / f"{sanitize_filename(utc_now_iso()[:10])}.json"
    _atomic_write_json(latest, payload)
    _atomic_write_json(history, payload)
    return {
        "storage_backend": "file",
        "trap_report_path": _project_relative_path(base_data_dir, latest),
        "trap_report_history_path": _project_relative_path(base_data_dir, history),
        "trap_count": payload["trap_count"],
    }


def load_trap_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    if isinstance(payload, dict):
        payload["storage_health"] = get_storage_health()
        return payload
    return {
        "ok": True,
        "schema_version": MANIFOLD_TRAP_SCHEMA_VERSION,
        "status": "empty",
        "trap_count": 0,
        "items": [],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_backend": "file",
        "storage_health": get_storage_health(),
    }


def compact_trap_report(report: dict[str, Any], *, limit: int = 25) -> dict[str, Any]:
    cap = max(1, min(int(limit or 25), 100))
    items = []
    for row in [item for item in report.get("items", []) if isinstance(item, dict)][:cap]:
        items.append(
            {
                "trap_cluster_detected": bool(row.get("trap_cluster_detected")),
                "trap_cluster_id": row.get("trap_cluster_id"),
                "no_bet_trap_score": row.get("no_bet_trap_score"),
                "no_trade_trap_score": row.get("no_trade_trap_score"),
                "historical_false_positive_rate": row.get("historical_false_positive_rate"),
                "historical_negative_ev_rate": row.get("historical_negative_ev_rate"),
                "trap_reasons": list(row.get("trap_reasons") or [])[:5],
                "recommended_action": row.get("recommended_action"),
                "execution_allowed": False,
                "provider_write": False,
                "live_execution_enabled": False,
                "auto_execution": False,
                "auto_execution_enabled": False,
                "human_approval_required": True,
                "actual_orders_submitted": 0,
                "actual_bets_submitted": 0,
                "actual_trades_submitted": 0,
                "raw_payload_included": False,
                "secrets_included": False,
            }
        )
    return {
        "ok": bool(report.get("ok", True)),
        "status": report.get("status", "ok"),
        "schema_version": report.get("schema_version", MANIFOLD_TRAP_SCHEMA_VERSION),
        "trap_count": int(report.get("trap_count", len(items))),
        "items": items,
        "storage_backend": report.get("storage_backend", "file"),
        "storage": report.get("storage_health"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def validate_simulation_request(payload: dict[str, Any]) -> None:
    if payload.get("simulation_only") is not True:
        raise ExecutionDeskRejected("execution desk requires simulation_only=true")
    for field in LIVE_FLAG_FIELDS:
        if payload.get(field) is True:
            raise ExecutionDeskRejected(f"execution desk rejects {field}=true")
    if payload.get("human_command") not in (None, "simulate_only"):
        raise ExecutionDeskRejected("execution desk only accepts human_command=simulate_only")


def _find_candidate(records: list[dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any] | None:
    candidate_id = str(payload.get("candidate_id") or "")
    if not candidate_id:
        return None
    for row in records:
        if candidate_id in {str(row.get("sidecar_id")), str(row.get("source_record_id")), str(row.get("contract_id")), str(row.get("symbol_or_ticker"))}:
            return row
    return None


def _theoretical_size(payload: dict[str, Any], record: dict[str, Any], risk_result: dict[str, Any]) -> float | None:
    max_risk = payload.get("max_theoretical_risk")
    try:
        max_risk_float = float(max_risk)
    except (TypeError, ValueError):
        max_risk_float = 0.0
    if max_risk_float <= 0:
        return None
    if risk_result.get("risk_blocks"):
        return None
    confidence = float(record.get("confidence_score") or 0.0) / 100.0
    liquidity = float(record.get("liquidity_score") or 0.0) / 100.0
    return round(max_risk_float * min(0.25, confidence * liquidity * 0.25), 6)


def simulate_execution(
    payload: dict[str, Any],
    *,
    records: list[dict[str, Any]] | None = None,
    calibration_report: dict[str, Any] | None = None,
    base_data_dir: str = "data",
    persist: bool = True,
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    validate_simulation_request(payload)
    available_records = records if records is not None else read_existing_outputs(
        base_data_dir=base_data_dir,
        asset_classes=[payload.get("asset_class") or "prediction_market"],
    ).get("records", [])
    candidate = _find_candidate(available_records, payload) if available_records else None
    if candidate is None:
        candidate = {
            "sidecar_id": payload.get("candidate_id"),
            "source_record_id": payload.get("candidate_id"),
            "asset_class": payload.get("asset_class"),
            "provider": payload.get("provider"),
            "reason_codes": ["missing_candidate"],
            "execution_allowed": False,
            "paper_only": True,
            "review_only": True,
            "simulation_only": True,
        }
    if calibration_report is None and available_records:
        calibration_report = build_calibration_by_asset_class(available_records)
    risk_result = assess_institutional_risk(candidate, calibration_report=calibration_report)
    if candidate.get("reason_codes") and "missing_candidate" in candidate.get("reason_codes"):
        risk_result["risk_blocks"] = sorted(set(list(risk_result.get("risk_blocks", [])) + ["missing_candidate"]))
    run_id = f"execution_sim_{safe_run_id('institutional_execution_sim', utc_now_iso() + str(payload.get('candidate_id')))}"
    audit = append_audit_record(
        action_type="execution_simulation",
        run_id=run_id,
        asset_class=str(candidate.get("asset_class") or payload.get("asset_class") or "unknown"),
        provider=str(candidate.get("provider") or payload.get("provider") or "unknown"),
        source_record_id=str(candidate.get("source_record_id") or payload.get("candidate_id") or ""),
        input_payload=payload,
        output_payload=risk_result,
        safety_flags={**EXECUTION_SAFETY_FLAGS, "simulated_ticket_created": True},
        compact_summary="Execution desk simulation only; no provider write.",
        base_data_dir=base_data_dir,
    )
    result = {
        "ok": True,
        "status": "simulated",
        "execution_desk_status": "simulation_only",
        "run_id": run_id,
        "live_execution_enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "asset_class": candidate.get("asset_class") or payload.get("asset_class"),
        "provider": candidate.get("provider") or payload.get("provider"),
        "candidate_id": payload.get("candidate_id"),
        "pre_trade_checks_passed": False,
        "risk_blocks": sorted(set(risk_result.get("risk_blocks", []))),
        "warnings": sorted(set(risk_result.get("warnings", []))),
        "risk_score": risk_result.get("risk_score"),
        "risk_tier": risk_result.get("risk_tier"),
        "theoretical_size": _theoretical_size(payload, candidate, risk_result),
        "simulated_ticket_created": True,
        "actual_order_submitted": False,
        "actual_bet_submitted": False,
        "actual_trade_submitted": False,
        "human_command_required": True,
        "requires_human_command": True,
        "audit_id": audit["audit_id"],
        "simulation_only": True,
        "actual_provider_destination": None,
        "broker_order_id": None,
        "sportsbook_bet_id": None,
        "kalshi_order_id": None,
        "raw_payload_included": False,
    }
    result.update(EXECUTION_SAFETY_FLAGS)
    if persist:
        path = _execution_dir(base_data_dir) / f"{sanitize_filename(run_id)}.json"
        _atomic_write_json(path, compact_redact(result))
        latest = _execution_dir(base_data_dir) / "latest.json"
        _atomic_write_json(latest, compact_redact(result))
        result["execution_sim_path"] = str(path.relative_to(resolve_base_data_dir(base_data_dir))).replace("\\", "/")
    return result


def rejection_response(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "rejected",
        "rejected_reason": reason,
        "execution_desk_status": "simulation_only",
        **EXECUTION_SAFETY_FLAGS,
        "simulated_ticket_created": False,
        "pre_trade_checks_passed": False,
        "risk_blocks": ["live_execution_flags_rejected"],
        "human_command_required": True,
        "raw_payload_included": False,
    }


def _execution_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "institutional_lab" / "execution_sim"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _negative_metric(value: Any) -> bool:
    try:
        if value is None:
            return False
        return float(value) < 0.0
    except (TypeError, ValueError):
        return False


def _execution_action(asset_type: str) -> str:
    if asset_type in {"stock", "crypto", "etf", "bond_rate", "major_asset"}:
        return "NO_TRADE"
    return "NO_BET"


__all__ = [
    "BROKER_STATUSES",
    "MANIFOLD_TRAP_SCHEMA_VERSION",
    "MIN_TRAP_STATS_SAMPLE",
    "EXECUTION_SAFETY_FLAGS",
    "LIVE_FLAG_FIELDS",
    "ExecutionDeskRejected",
    "SAFETY_FLAGS",
    "score_broker_provider",
    "default_broker_quality_rows",
    "build_broker_quality_report",
    "score_price_band",
    "score_low_float_high_demand",
    "calculate_risk_reward",
    "score_a_quality_setup",
    "build_detection_context",
    "candidate_from_row",
    "run_small_account_review",
    "build_local_analyst_review",
    "detect_manifold_trap",
    "write_trap_report",
    "load_trap_report",
    "compact_trap_report",
    "validate_simulation_request",
    "simulate_execution",
    "rejection_response",
]
