from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.data_paths import resolve_base_data_dir
from src.analytics.calibration_tracker import (
    calculate_brier_score,
    calculate_expected_calibration_error,
    calculate_log_loss,
    detect_overconfidence,
)
from src.market_intelligence.clv_tracker import calculate_clv_for_american_odds
from src.analytics.model_performance_report import build_compact_performance_report, write_model_performance_report
from src.brokerage.paper_trade_ledger import load_paper_ledger, summarize_paper_ledger
from src.analytics.performance_metrics import calculate_performance_metrics
from src.services.scheduler_config import sanitize_filename, utc_now_iso

from src.analytics.calibration import calculate_calibration_metrics, summarize_outcome_coverage
from src.data.data_paths import get_runtime_data_path
from .backtest_schema import normalize_backtest_row, normalize_backtest_rows, validate_no_leakage_features
from .backtest_leakage import assert_backtest_rows_no_hard_leakage, summarize_backtest_leakage_report
from .backtest_strategy_bankroll import apply_regression_strategy_to_rows, simulate_backtest_bankroll, summarize_strategy_bankroll_report
from .backtest_strategy_profiles import build_strategy_config_for_row

# Absorbed Phase 10B canonical backtesting helpers.
def _group_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
def _reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason_codes = row.get("reason_codes") if isinstance(row.get("reason_codes"), list) else []
        if not reason_codes:
            reason_codes = [row.get("reason") or "unknown"]
        for reason in reason_codes:
            key = str(reason or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return counts
def run_backtesting_scaffold(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (rows or []) if isinstance(row, dict)]
    coverage = summarize_outcome_coverage(rows)
    if not rows or coverage["settled_count"] == 0:
        return {
            "ok": True,
            "status": "insufficient_data",
            "sample_size": len(rows),
            "settled_count": 0,
            "pending_count": coverage["pending_count"],
            "void_count": coverage["void_count"],
            "coverage_rate": coverage["coverage_rate"],
            "insufficient_data": True,
            "metrics": {},
            "group_counts": {
                "provider": _group_counts(rows, "provider"),
                "market_type": _group_counts(rows, "market_type"),
                "reason": _reason_counts(rows),
            },
            "next_required_data": ["settlement_results"],
        }

    status = "metrics_ready" if coverage["settled_count"] >= len(rows) else "partial_calibration"
    return {
        "ok": True,
        "status": status,
        "sample_size": len(rows),
        "settled_count": coverage["settled_count"],
        "pending_count": coverage["pending_count"],
        "void_count": coverage["void_count"],
        "coverage_rate": coverage["coverage_rate"],
        "insufficient_data": False,
        "metrics": calculate_calibration_metrics(rows),
        "group_counts": {
            "provider": _group_counts(rows, "provider"),
            "market_type": _group_counts(rows, "market_type"),
            "reason": _reason_counts(rows),
        },
        "next_required_data": [] if status == "metrics_ready" else ["additional_settlement_results"],
    }
def load_historical_rows(path: str) -> list[dict[str, Any]]:
    if "://" in str(path):
        raise ValueError("historical replay supports local JSON rows only")
    file_path = Path(path)
    if not file_path.exists():
        return []
    if file_path.suffix.lower() != ".json":
        raise ValueError("historical replay expects a local JSON file")
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("historical replay JSON must be a list of rows")
    return payload
def replay_rows(rows: list[dict[str, Any]], model_id: str = "historical_replay") -> dict[str, Any]:
    """Replay historical rows through the canonical backtest row schema.

    This preserves the old public contract while normalizing aliases through
    the canonical backtest schema registry.
    """

    rows = normalize_backtest_rows(rows)
    replayed = []

    for row in rows:
        replayed.append(
            {
                "event_id": row.get("event_id"),
                "contract_id": row.get("contract_id"),
                "sport": row.get("sport"),
                "league": row.get("league"),
                "market_type": row.get("market_type") or row.get("market"),
                "event_name": row.get("event_name"),
                "market_name": row.get("market_name"),
                "selection_name": row.get("selection_name"),
                "recommended_odds": row.get("recommended_odds") if row.get("recommended_odds") is not None else row.get("odds_at_decision_time"),
                "closing_odds": row.get("closing_odds") if row.get("closing_odds") is not None else row.get("closing_line"),
                "model_probability": _to_float(row.get("model_probability")),
                "market_implied_probability": _to_float(row.get("market_implied_probability")),
                "ev_percent": _to_float(row.get("ev_percent") if row.get("ev_percent") is not None else row.get("edge"), 0.0),
                "paper_stake": _to_float(row.get("paper_stake") if row.get("paper_stake") is not None else row.get("stake"), 1.0),
                "recommended_stake_percent": row.get("recommended_stake_percent"),
                "result_status": row.get("result_status") or row.get("final_result") or "pending",
                "timestamp": row.get("timestamp") or row.get("decision_time") or utc_now_iso(),
                "features_known_at_decision_time": row.get("features_known_at_decision_time"),
            }
        )

    return {
        "model_id": model_id,
        "replayed_at": utc_now_iso(),
        "sample_size": len(replayed),
        "rows": replayed,
    }
def write_replay_result(result: dict[str, Any], base_dir: str = "data/backtests") -> str:
    """Write replay result and guarantee the persisted contract."""

    payload = dict(result or {})
    rows = list(payload.get("rows") or [])

    payload["sample_size"] = payload.get("sample_size", len(rows))
    payload["rows"] = rows

    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)

    model_id = sanitize_filename(str(payload.get("model_id") or "unknown_model"))
    replay_id = sanitize_filename(str(payload.get("replayed_at") or utc_now_iso()))
    output_path = path / f"replay_{model_id}_{replay_id}.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    return str(output_path)
def summarize_replay_result(result: dict[str, Any]) -> dict[str, Any]:
    rows = list(result.get("rows") or [])
    settled = [row for row in rows if str(row.get("result_status")).lower() in {"win", "loss", "push"}]
    return {
        "model_id": result.get("model_id"),
        "sample_size": len(rows),
        "settled_count": len(settled),
        "status": "backtest_complete" if rows else "needs_more_sample",
    }




def _apply_backtest_strategy_config(
    rows: list[dict[str, Any]],
    strategy_config: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not strategy_config:
        return rows

    mode = strategy_config.get("mode") or strategy_config.get("profile_mode")

    if mode != "sport_profiles":
        return apply_regression_strategy_to_rows(rows, **strategy_config)

    profile_scope = strategy_config.get("profile_scope", "auto")
    all_sports_profile = strategy_config.get("all_sports_profile")
    sport_profiles = strategy_config.get("sport_profiles")

    enriched_rows: list[dict[str, Any]] = []
    for row in rows:
        row_config = build_strategy_config_for_row(
            row,
            profile_scope=profile_scope,
            all_sports_profile=all_sports_profile,
            sport_profiles=sport_profiles,
        )
        enriched_rows.extend(apply_regression_strategy_to_rows([row], **row_config))

    return enriched_rows


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _paper_rows_from_replay_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = normalize_backtest_rows(rows)
    assert_backtest_rows_no_hard_leakage(rows)
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
    strategy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if rows is not None:
        rows = normalize_backtest_rows(rows)
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    Path(base_data_dir, "clv").mkdir(parents=True, exist_ok=True)
    Path(base_data_dir, "calibration").mkdir(parents=True, exist_ok=True)
    source_rows = list(rows or [])
    if historical_rows_path:
        source_rows = load_historical_rows(historical_rows_path)
    if strategy_config:
        source_rows = _apply_backtest_strategy_config(source_rows, strategy_config)
    leakage_report = assert_backtest_rows_no_hard_leakage(source_rows)
    strategy_bankroll_report = simulate_backtest_bankroll(source_rows)
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
        "leakage_report": summarize_backtest_leakage_report(leakage_report),
        "strategy_bankroll_summary": summarize_strategy_bankroll_report(strategy_bankroll_report),
        "strategy_bankroll_report": strategy_bankroll_report,
        "strategy_config": strategy_config or {},
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
