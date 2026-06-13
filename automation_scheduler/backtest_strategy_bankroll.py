"""Backtest strategy and bankroll simulation helpers.

This is not a second backtesting engine.

The canonical owner remains:
automation_scheduler.backtesting_engine

These helpers let one backtest run include:
- bet/no-bet strategy
- bankroll curve
- ROI
- PnL
- max drawdown
- edge buckets
- CLV buckets
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .backtest_schema import normalize_backtest_row


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _american_profit(stake: float, odds: float) -> float:
    if stake <= 0:
        return 0.0
    if odds >= 100:
        return stake * (odds / 100.0)
    if odds <= -100:
        return stake * (100.0 / abs(odds))
    return 0.0


def _bucket(value: float, *, width: float = 2.5, floor: float = -20.0, ceiling: float = 20.0) -> str:
    if value <= floor:
        return f"<= {floor:g}"
    if value >= ceiling:
        return f">= {ceiling:g}"

    start = int(value // width) * width
    end = start + width
    return f"{start:g} to {end:g}"


def decide_backtest_bet(
    row: Mapping[str, Any],
    *,
    min_edge_percent: float = 0.0,
    min_model_probability: float = 0.0,
    allow_pending: bool = True,
) -> dict[str, Any]:
    """Simple sharp-style strategy gate.

    This is intentionally conservative and transparent. Regression/model work can
    later replace the probability source, while this strategy still controls
    bet/no-bet behavior.
    """

    normalized = normalize_backtest_row(row)

    edge = _to_float(normalized.get("edge"), _to_float(normalized.get("ev_percent"), 0.0))
    model_probability = _to_float(normalized.get("model_probability"), 0.0)
    result_status = str(normalized.get("result_status") or normalized.get("final_result") or "pending").lower()

    reasons: list[str] = []

    if edge < min_edge_percent:
        reasons.append("edge_below_threshold")

    if model_probability < min_model_probability:
        reasons.append("model_probability_below_threshold")

    if result_status == "pending" and not allow_pending:
        reasons.append("pending_result_not_allowed")

    bet = not reasons

    return {
        "bet": bet,
        "decision": "bet" if bet else "no_bet",
        "reasons": reasons,
        "edge_percent": edge,
        "model_probability": model_probability,
    }


def simulate_backtest_bankroll(
    rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
    *,
    starting_bankroll: float = 1000.0,
    unit_size: float = 10.0,
    min_edge_percent: float = 0.0,
    min_model_probability: float = 0.0,
    max_stake_percent: float = 0.05,
) -> dict[str, Any]:
    """Simulate bankroll through normalized backtest rows."""

    bankroll = float(starting_bankroll)
    peak_bankroll = bankroll
    max_drawdown = 0.0

    decisions: list[dict[str, Any]] = []
    bankroll_curve: list[dict[str, Any]] = []
    bucket_stats: dict[str, dict[str, Any]] = {}
    clv_bucket_stats: dict[str, dict[str, Any]] = {}

    total_staked = 0.0
    total_profit_loss = 0.0
    wins = 0
    losses = 0
    pushes = 0
    bets = 0

    normalized_rows = [normalize_backtest_row(row) for row in (rows or [])]

    for index, row in enumerate(normalized_rows):
        strategy = decide_backtest_bet(
            row,
            min_edge_percent=min_edge_percent,
            min_model_probability=min_model_probability,
        )

        result_status = str(row.get("result_status") or row.get("final_result") or "pending").lower()
        odds = _to_float(row.get("recommended_odds"), _to_float(row.get("odds_at_decision_time"), 0.0))
        edge = _to_float(row.get("edge"), _to_float(row.get("ev_percent"), 0.0))
        clv = _to_float(row.get("clv"), _to_float(row.get("clv_percent"), 0.0))

        raw_stake = _to_float(row.get("paper_stake"), _to_float(row.get("stake"), unit_size))
        stake_cap = max(float(unit_size), bankroll * float(max_stake_percent))
        stake = max(0.0, min(raw_stake if raw_stake > 0 else unit_size, stake_cap, bankroll))

        profit_loss = 0.0

        if strategy["bet"] and stake > 0:
            bets += 1
            total_staked += stake

            if result_status == "win":
                profit_loss = _american_profit(stake, odds)
                wins += 1
            elif result_status == "loss":
                profit_loss = -stake
                losses += 1
            elif result_status == "push":
                profit_loss = 0.0
                pushes += 1
            else:
                profit_loss = 0.0

            bankroll += profit_loss
            total_profit_loss += profit_loss

        peak_bankroll = max(peak_bankroll, bankroll)
        drawdown = peak_bankroll - bankroll
        max_drawdown = max(max_drawdown, drawdown)

        edge_bucket = _bucket(edge)
        clv_bucket = _bucket(clv)

        bucket = bucket_stats.setdefault(
            edge_bucket,
            {"bets": 0, "profit_loss": 0.0, "staked": 0.0, "wins": 0, "losses": 0, "pushes": 0},
        )
        clv_bucket_row = clv_bucket_stats.setdefault(
            clv_bucket,
            {"bets": 0, "profit_loss": 0.0, "staked": 0.0, "wins": 0, "losses": 0, "pushes": 0},
        )

        if strategy["bet"]:
            bucket["bets"] += 1
            bucket["profit_loss"] += profit_loss
            bucket["staked"] += stake
            clv_bucket_row["bets"] += 1
            clv_bucket_row["profit_loss"] += profit_loss
            clv_bucket_row["staked"] += stake

            if result_status == "win":
                bucket["wins"] += 1
                clv_bucket_row["wins"] += 1
            elif result_status == "loss":
                bucket["losses"] += 1
                clv_bucket_row["losses"] += 1
            elif result_status == "push":
                bucket["pushes"] += 1
                clv_bucket_row["pushes"] += 1

        decision = {
            "index": index,
            "event_id": row.get("event_id"),
            "contract_id": row.get("contract_id"),
            "sport": row.get("sport"),
            "league": row.get("league"),
            "market": row.get("market") or row.get("market_type"),
            "decision": strategy["decision"],
            "reasons": strategy["reasons"],
            "stake": round(stake if strategy["bet"] else 0.0, 4),
            "odds": odds,
            "edge_percent": edge,
            "model_probability": strategy["model_probability"],
            "result_status": result_status,
            "profit_loss": round(profit_loss, 4),
            "bankroll_after": round(bankroll, 4),
            "drawdown_after": round(drawdown, 4),
        }

        decisions.append(decision)
        bankroll_curve.append(
            {
                "index": index,
                "bankroll": round(bankroll, 4),
                "drawdown": round(drawdown, 4),
                "profit_loss": round(profit_loss, 4),
            }
        )

    roi_percent = round((total_profit_loss / total_staked) * 100.0, 4) if total_staked else 0.0
    win_rate = round(wins / bets, 4) if bets else 0.0

    for stats in list(bucket_stats.values()) + list(clv_bucket_stats.values()):
        stats["profit_loss"] = round(stats["profit_loss"], 4)
        stats["staked"] = round(stats["staked"], 4)
        stats["roi_percent"] = round((stats["profit_loss"] / stats["staked"]) * 100.0, 4) if stats["staked"] else 0.0

    return {
        "ok": True,
        "policy": "simple_edge_probability_bankroll_simulation",
        "starting_bankroll": round(float(starting_bankroll), 4),
        "ending_bankroll": round(bankroll, 4),
        "unit_size": round(float(unit_size), 4),
        "rows_seen": len(normalized_rows),
        "bets": bets,
        "no_bets": len(normalized_rows) - bets,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": win_rate,
        "total_staked": round(total_staked, 4),
        "profit_loss": round(total_profit_loss, 4),
        "roi_percent": roi_percent,
        "max_drawdown": round(max_drawdown, 4),
        "max_drawdown_percent": round((max_drawdown / float(starting_bankroll)) * 100.0, 4) if starting_bankroll else 0.0,
        "edge_buckets": bucket_stats,
        "clv_buckets": clv_bucket_stats,
        "bankroll_curve": bankroll_curve,
        "decisions": decisions,
    }


def summarize_strategy_bankroll_report(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(report.get("ok")),
        "policy": report.get("policy"),
        "starting_bankroll": report.get("starting_bankroll"),
        "ending_bankroll": report.get("ending_bankroll"),
        "bets": report.get("bets", 0),
        "no_bets": report.get("no_bets", 0),
        "profit_loss": report.get("profit_loss", 0.0),
        "roi_percent": report.get("roi_percent", 0.0),
        "max_drawdown": report.get("max_drawdown", 0.0),
        "max_drawdown_percent": report.get("max_drawdown_percent", 0.0),
        "win_rate": report.get("win_rate", 0.0),
    }
