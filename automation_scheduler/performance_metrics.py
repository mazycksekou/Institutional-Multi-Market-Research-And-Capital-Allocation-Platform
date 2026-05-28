from __future__ import annotations

import math
from statistics import pstdev
from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _max_drawdown_percent(entries: list[dict[str, Any]], starting_equity: float = 100.0) -> float:
    equity = starting_equity
    peak = starting_equity
    max_drawdown = 0.0
    for row in entries:
        if str(row.get("settlement_status")) != "settled":
            continue
        equity += _to_float(row.get("paper_profit_loss"))
        if equity > peak:
            peak = equity
        if peak > 0:
            drawdown = (peak - equity) / peak * 100.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    return round(max_drawdown, 4)


def calculate_performance_metrics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    total_recommendations = len(entries)
    settled_entries = [e for e in entries if str(e.get("settlement_status")) == "settled"]
    settled_count = len(settled_entries)
    win_count = sum(1 for e in settled_entries if str(e.get("result_status")) == "win")
    loss_count = sum(1 for e in settled_entries if str(e.get("result_status")) == "loss")
    push_count = sum(1 for e in settled_entries if str(e.get("result_status")) == "push")
    non_push = max(1, win_count + loss_count)
    hit_rate = win_count / non_push

    total_stake = sum(_to_float(e.get("paper_stake")) for e in settled_entries)
    total_pnl = sum(_to_float(e.get("paper_profit_loss")) for e in settled_entries)
    realized_roi_percent = (total_pnl / total_stake * 100.0) if total_stake > 0 else 0.0

    ev_values = [_to_float(e.get("ev_percent")) for e in entries if e.get("ev_percent") is not None]
    expected_roi_percent = (sum(ev_values) / len(ev_values)) if ev_values else 0.0
    average_edge_percent = expected_roi_percent

    gross_wins = sum(_to_float(e.get("paper_profit_loss")) for e in settled_entries if _to_float(e.get("paper_profit_loss")) > 0)
    gross_losses = abs(
        sum(_to_float(e.get("paper_profit_loss")) for e in settled_entries if _to_float(e.get("paper_profit_loss")) < 0)
    )
    if gross_losses == 0:
        profit_factor = float("inf") if gross_wins > 0 else 0.0
    else:
        profit_factor = gross_wins / gross_losses

    stake_percents = [_to_float(e.get("recommended_stake_percent")) for e in entries if e.get("recommended_stake_percent") is not None]
    average_stake_percent = (sum(stake_percents) / len(stake_percents)) if stake_percents else 0.0

    realized_returns = []
    for entry in settled_entries:
        stake = _to_float(entry.get("paper_stake"))
        pnl = _to_float(entry.get("paper_profit_loss"))
        realized_returns.append((pnl / stake) if stake > 0 else 0.0)
    volatility = pstdev(realized_returns) if len(realized_returns) > 1 else 0.0
    risk_adjusted_return = realized_roi_percent / (volatility * 100.0 + 1e-9) if settled_count > 0 else 0.0

    sample_size_warning = "needs_more_sample" if settled_count < 30 else "sample_ok"

    return {
        "total_recommendations": total_recommendations,
        "settled_count": settled_count,
        "win_count": win_count,
        "loss_count": loss_count,
        "push_count": push_count,
        "hit_rate": round(hit_rate, 4),
        "realized_roi_percent": round(realized_roi_percent, 4),
        "expected_roi_percent": round(expected_roi_percent, 4),
        "profit_factor": "inf" if math.isinf(profit_factor) else round(profit_factor, 4),
        "average_edge_percent": round(average_edge_percent, 4),
        "max_drawdown_percent": _max_drawdown_percent(entries),
        "average_stake_percent": round(average_stake_percent, 4),
        "risk_adjusted_return": round(risk_adjusted_return, 4),
        "sample_size_warning": sample_size_warning,
        "confidence_interval_placeholder": "ci_pending_more_samples",
    }

