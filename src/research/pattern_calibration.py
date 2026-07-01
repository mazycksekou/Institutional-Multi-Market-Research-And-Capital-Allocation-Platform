from __future__ import annotations

import math
from typing import Any

from src.analytics.micro_outcome_calibration import settle_outcome_window, supports_outcome_window
from src.services.scheduler_config import utc_now_iso


NORMAL_OUTCOME_WINDOWS = ("5m", "15m", "30m", "60m", "end_of_day")
SEGMENT_FIELDS = (
    "pattern_id",
    "asset_type",
    "timeframe",
    "session_time_bucket",
    "liquidity_tier",
    "price_band",
    "catalyst_type",
    "balance_sheet_risk_bucket",
    "data_resolution",
)


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    avg = sum(values) / len(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def _max_streak(results: list[bool], target: bool) -> int:
    best = current = 0
    for result in results:
        if result is target:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def record_trade_outcome_windows(
    detection: dict[str, Any],
    price_history: list[dict[str, Any]] | None,
    *,
    data_resolution: str,
    windows: tuple[str, ...] = NORMAL_OUTCOME_WINDOWS,
) -> dict[str, Any]:
    records = [
        settle_outcome_window(detection, price_history, outcome_window=window, data_resolution=data_resolution)
        for window in windows
    ]
    status_counts: dict[str, int] = {}
    for record in records:
        for key in SEGMENT_FIELDS:
            if record.get(key) is None and detection.get(key) is not None:
                record[key] = detection.get(key)
        status = str(record.get("outcome_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "ok": True,
        "status": "trade_outcomes_recorded",
        "created_at": utc_now_iso(),
        "detection_id": detection.get("detection_id"),
        "data_resolution": data_resolution,
        "records": records,
        "record_count": len(records),
        "status_counts": status_counts,
        "unsupported_windows": [window for window in windows if not supports_outcome_window(data_resolution, window)],
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


def calculate_performance_metrics(records: list[dict[str, Any]] | None) -> dict[str, Any]:
    rows = [row for row in (records or []) if isinstance(row, dict)]
    trade_rows = [
        row
        for row in rows
        if row.get("outcome_status") == "settled"
        and (_num(row.get("profit_loss")) is not None or _num(row.get("follow_through_percent")) is not None)
    ]
    pnl = [
        _num(row.get("profit_loss"), _num(row.get("follow_through_percent"), 0.0))
        for row in trade_rows
    ]
    pnl = [value for value in pnl if value is not None]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    results = [value > 0 for value in pnl]
    total = len(pnl)
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    win_rate = len(wins) / total if total else 0.0
    avg_win = _mean(wins)
    avg_loss = _mean(losses)
    largest_gain = max(pnl) if pnl else None
    largest_loss = min(pnl) if pnl else None
    std = _std(pnl)
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (None if gross_win <= 0 else float("inf"))
    average_win_abs = avg_win if avg_win is not None else 0.0
    average_loss_abs = abs(avg_loss) if avg_loss is not None else 0.0
    kelly = None
    if average_win_abs > 0 and average_loss_abs > 0 and total:
        payoff = average_win_abs / average_loss_abs
        kelly = win_rate - ((1.0 - win_rate) / payoff)
    hold_times = [_num(row.get("hold_time_seconds")) for row in trade_rows]
    hold_times = [value for value in hold_times if value is not None]
    maes = [_num(row.get("max_adverse_excursion")) for row in trade_rows]
    mfes = [_num(row.get("max_favorable_excursion")) for row in trade_rows]
    maes = [value for value in maes if value is not None]
    mfes = [value for value in mfes if value is not None]
    commissions = [_num(row.get("commission"), 0.0) or 0.0 for row in trade_rows]
    fees = [_num(row.get("fee"), _num(row.get("fees"), 0.0)) or 0.0 for row in trade_rows]
    probability_random_chance = None
    if total >= 30:
        # Normal approximation for a 50/50 null; enough for a compact caution signal, not a claim of proof.
        z = (len(wins) - total * 0.5) / math.sqrt(total * 0.25)
        probability_random_chance = round(max(0.0, min(1.0, 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0)))))), 6)
    return {
        "total_gain_loss": round(sum(pnl), 6) if pnl else 0.0,
        "average_daily_gain_loss": None,
        "average_trade_gain_loss": round(_mean(pnl), 6) if pnl else None,
        "total_number_of_trades": total,
        "number_winning_trades": len(wins),
        "number_losing_trades": len(losses),
        "win_rate": round(win_rate, 6) if total else 0.0,
        "average_winning_trade": round(avg_win, 6) if avg_win is not None else None,
        "average_losing_trade": round(avg_loss, 6) if avg_loss is not None else None,
        "largest_gain": round(largest_gain, 6) if largest_gain is not None else None,
        "largest_loss": round(largest_loss, 6) if largest_loss is not None else None,
        "average_hold_time": round(_mean(hold_times), 6) if hold_times else None,
        "max_consecutive_wins": _max_streak(results, True),
        "max_consecutive_losses": _max_streak(results, False),
        "trade_pnl_standard_deviation": round(std, 6) if std is not None else None,
        "kelly_percentage": round(kelly * 100.0, 6) if kelly is not None else None,
        "fractional_kelly_paper_only": round(max(0.0, kelly or 0.0) * 0.25 * 100.0, 6) if kelly is not None else None,
        "k_ratio": None,
        "profit_factor": round(profit_factor, 6) if isinstance(profit_factor, float) and math.isfinite(profit_factor) else profit_factor,
        "total_commissions": round(sum(commissions), 6),
        "total_fees": round(sum(fees), 6),
        "average_position_mae": round(_mean(maes), 6) if maes else None,
        "average_position_mfe": round(_mean(mfes), 6) if mfes else None,
        "probability_random_chance": probability_random_chance,
        "sample_size": total,
        "insufficient_sample": total < 30,
    }


def segment_calibration_records(records: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    rows = [row for row in (records or []) if isinstance(row, dict)]
    segments: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = "|".join(str(row.get(field) or "unknown") for field in SEGMENT_FIELDS)
        segments.setdefault(key, []).append(row)
    return {
        key: {
            "sample_size": len(members),
            "settled_count": len([row for row in members if row.get("outcome_status") == "settled"]),
            "data_resolution": members[0].get("data_resolution") if members else None,
            "insufficient_sample": len([row for row in members if row.get("outcome_status") == "settled"]) < 30,
        }
        for key, members in sorted(segments.items())
    }


def build_pattern_calibration_report(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (records or []) if isinstance(row, dict)]
    settled = [row for row in rows if row.get("outcome_status") == "settled"]
    status = "metrics_ready" if len(settled) >= 30 else "insufficient_data"
    return {
        "ok": True,
        "status": status,
        "created_at": utc_now_iso(),
        "record_count": len(rows),
        "settled_count": len(settled),
        "sample_size": len(settled),
        "insufficient_sample": len(settled) < 30,
        "performance_metrics": calculate_performance_metrics(settled),
        "segments": segment_calibration_records(rows),
        "next_required_data": ["additional_settled_trade_outcomes"] if len(settled) < 30 else [],
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
