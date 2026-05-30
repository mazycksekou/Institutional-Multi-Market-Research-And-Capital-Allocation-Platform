from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import resolve_base_data_dir
from .calibration_tracker import (
    calculate_brier_score,
    calculate_expected_calibration_error,
    calculate_log_loss,
    detect_overconfidence,
)
from .clv_tracker import calculate_clv_for_american_odds
from .historical_replay import load_historical_rows, replay_rows, summarize_replay_result, write_replay_result
from .model_performance_report import build_compact_performance_report, write_model_performance_report
from .paper_trade_ledger import load_paper_ledger, summarize_paper_ledger
from .performance_metrics import calculate_performance_metrics
from .scheduler_config import sanitize_filename, utc_now_iso


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _paper_rows_from_replay_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_rows = []
    for row in rows:
        result_status = str(row.get("result_status", "pending")).lower()
        stake = _to_float(row.get("paper_stake"), default=1.0)
        odds = _to_float(row.get("recommended_odds"))
        if result_status == "win":
            pnl = stake * (odds / 100.0) if odds >= 100 else stake * (100.0 / abs(odds)) if odds <= -100 else 0.0
            settlement_status = "settled"
        elif result_status == "loss":
            pnl = -stake
            settlement_status = "settled"
        elif result_status == "push":
            pnl = 0.0
            settlement_status = "settled"
        else:
            pnl = 0.0
            settlement_status = "open"
        paper_rows.append(
            {
                "model_id": row.get("model_id"),
                "market_type": row.get("market_type"),
                "recommended_odds": row.get("recommended_odds"),
                "closing_odds": row.get("closing_odds"),
                "model_probability": row.get("model_probability"),
                "result_status": result_status,
                "settlement_status": settlement_status,
                "paper_stake": stake,
                "paper_profit_loss": round(pnl, 4),
                "ev_percent": row.get("ev_percent", 0.0),
                "recommended_stake_percent": row.get("recommended_stake_percent", 1.0),
            }
        )
    return paper_rows


def compare_expected_vs_realized(expected_roi_percent: float, realized_roi_percent: float) -> dict[str, Any]:
    delta = _to_float(realized_roi_percent) - _to_float(expected_roi_percent)
    status = "watch_recheck"
    if delta >= 0:
        status = "backtest_complete"
    if delta < -2.0:
        status = "needs_revalidation"
    return {
        "expected_roi_percent": round(_to_float(expected_roi_percent), 4),
        "realized_roi_percent": round(_to_float(realized_roi_percent), 4),
        "roi_delta_percent": round(delta, 4),
        "status": status,
    }


def run_backtest(
    *,
    model_id: str,
    historical_rows_path: str | None = None,
    rows: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    Path(base_data_dir, "clv").mkdir(parents=True, exist_ok=True)
    Path(base_data_dir, "calibration").mkdir(parents=True, exist_ok=True)
    source_rows = list(rows or [])
    if historical_rows_path:
        source_rows = load_historical_rows(historical_rows_path)
    replay = replay_rows(source_rows, model_id=model_id)
    replay_path = write_replay_result(replay, base_dir=str(Path(base_data_dir) / "backtests"))
    replay_rows_data = list(replay.get("rows", []))

    paper_rows = _paper_rows_from_replay_rows(replay_rows_data)
    metrics = calculate_performance_metrics(paper_rows)
    clv_values = [
        calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))
        for entry in paper_rows
        if entry.get("recommended_odds") is not None and entry.get("closing_odds") is not None
    ]
    average_clv_percent = round(sum(clv_values) / len(clv_values), 4) if clv_values else 0.0
    positive_clv_rate = round(sum(1 for v in clv_values if v > 0) / len(clv_values), 4) if clv_values else 0.0

    brier_score = calculate_brier_score(paper_rows)
    log_loss = calculate_log_loss(paper_rows)
    ece = calculate_expected_calibration_error(paper_rows)
    overconfident = detect_overconfidence(paper_rows)

    stamp = sanitize_filename(utc_now_iso())
    model_slug = sanitize_filename(model_id)
    clv_path = Path(base_data_dir) / "clv" / f"clv_{model_slug}_{stamp}.json"
    clv_path.write_text(
        json.dumps(
            {
                "model_id": model_id,
                "sample_size": len(clv_values),
                "average_clv_percent": average_clv_percent,
                "positive_clv_rate": positive_clv_rate,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    calibration_path = Path(base_data_dir) / "calibration" / f"calibration_{model_slug}_{stamp}.json"
    calibration_path.write_text(
        json.dumps(
            {
                "model_id": model_id,
                "brier_score": brier_score,
                "log_loss": log_loss,
                "expected_calibration_error": ece,
                "overconfidence_detected": overconfident,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    calibration_status = "backtest_complete"
    if overconfident or ece > 0.08:
        calibration_status = "needs_revalidation"

    performance_status = "backtest_complete"
    blocked_reasons: list[str] = []
    if str(metrics.get("sample_size_warning")) == "needs_more_sample":
        performance_status = "needs_more_sample"
        blocked_reasons.append("blocked_by_performance")
    if calibration_status == "needs_revalidation":
        blocked_reasons.append("blocked_by_calibration")
    if average_clv_percent < 0:
        blocked_reasons.append("negative_clv")
    elif clv_values:
        blocked_reasons.append("positive_clv")

    recommended_next_action = "watch_recheck"
    if blocked_reasons:
        recommended_next_action = "needs_revalidation"
    if performance_status == "needs_more_sample":
        recommended_next_action = "needs_more_sample"

    return {
        "model_id": model_id,
        "sample_size": int(metrics["total_recommendations"]),
        "expected_roi_percent": metrics["expected_roi_percent"],
        "realized_roi_percent": metrics["realized_roi_percent"],
        "average_clv_percent": average_clv_percent,
        "positive_clv_rate": positive_clv_rate,
        "max_drawdown_percent": metrics["max_drawdown_percent"],
        "brier_score": brier_score,
        "log_loss": log_loss,
        "calibration_status": calibration_status,
        "performance_status": performance_status,
        "blocked_reasons": blocked_reasons,
        "recommended_next_action": recommended_next_action,
        "expected_vs_realized": compare_expected_vs_realized(metrics["expected_roi_percent"], metrics["realized_roi_percent"]),
        "replay_summary": summarize_replay_result(replay),
        "replay_path": replay_path,
        "ece": ece,
        "clv_path": str(clv_path),
        "calibration_path": str(calibration_path),
    }


def run_paper_summary(base_data_dir: str = "data") -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    ledger_base = str(Path(base_data_dir) / "paper_ledger")
    ledger_entries = load_paper_ledger(base_dir=ledger_base)
    summary = summarize_paper_ledger(base_dir=ledger_base)
    metrics = calculate_performance_metrics(ledger_entries)
    return {
        "ok": True,
        "status": "paper_tracking",
        "paper_ledger_count": len(ledger_entries),
        "settled_paper_count": int(summary.get("settled_entries", 0)),
        "summary": summary,
        "metrics": metrics,
    }


def generate_backtest_report(
    *,
    model_id: str,
    historical_rows_path: str | None = None,
    rows: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    result = run_backtest(model_id=model_id, historical_rows_path=historical_rows_path, rows=rows, base_data_dir=base_data_dir)
    report = write_model_performance_report(result, base_dir=str(Path(base_data_dir) / "performance_reports"))
    compact = build_compact_performance_report(report["full_report"], report["report_path"])
    return {
        "ok": True,
        "status": "backtest_complete",
        "report_id": report["full_report"]["report_id"],
        "compact_report": compact,
        "full_report": report["full_report"],
        "report_path": report["report_path"],
    }
