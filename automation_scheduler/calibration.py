from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paper_decision_ledger import load_paper_decisions, summarize_paper_decisions, to_float_or_none
from .review_queue import load_review_queue_state
from .scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso

CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.outcome_calibration.v1"
_OUTCOME_KEYS = ("outcome_status", "settlement_status", "final_outcome", "paper_result", "settled_at")
_SCORE_FIELDS = (
    "liquidity_score",
    "spread_score",
    "pricing_quality_score",
    "risk_score",
    "confidence_score",
    "review_priority_score",
)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _outcome_dir(base_data_dir: str = "data") -> Path:
    path = Path(base_data_dir) / "outcomes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _report_dir(base_data_dir: str = "data") -> Path:
    path = Path(base_data_dir) / "calibration_reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path(base_data_dir).resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _normalized_outcome_label(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"win", "yes", "true", "settled_yes", "resolved_yes", "1"}:
            return 1.0
        if text in {"loss", "no", "false", "settled_no", "resolved_no", "0"}:
            return 0.0
        return None
    parsed = to_float_or_none(value)
    if parsed is None:
        return None
    if parsed in {0.0, 1.0}:
        return parsed
    return None


def _bucket_probability(value: Any) -> str:
    parsed = to_float_or_none(value)
    if parsed is None:
        return "missing"
    if parsed > 1.0:
        parsed = parsed / 100.0
    bounded = max(0.0, min(0.999999, parsed))
    lower = int(bounded * 5) * 20
    upper = lower + 20
    return f"{lower:02d}-{upper:02d}"


def _bucket_score(value: Any) -> str:
    parsed = to_float_or_none(value)
    if parsed is None:
        return "missing"
    bounded = max(0.0, min(99.999999, parsed))
    lower = int(bounded // 20) * 20
    upper = lower + 20
    return f"{lower:02d}-{upper:02d}"


def _counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        out[value] = out.get(value, 0) + 1
    return out


def _score_presence(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: len([row for row in rows if row.get(field) is not None]) for field in _SCORE_FIELDS}


def _settlement_presence(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: len([row for row in rows if row.get(field) is not None]) for field in _OUTCOME_KEYS}


def _score_bucket_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        bucket = _bucket_score(row.get("review_priority_score"))
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def load_outcome_records(base_data_dir: str = "data") -> list[dict[str, Any]]:
    outcomes_dir = _outcome_dir(base_data_dir)
    rows: list[dict[str, Any]] = []
    for path in sorted(outcomes_dir.glob("*.json")):
        payload = _read_json(path)
        if isinstance(payload, list):
            rows.extend([row for row in payload if isinstance(row, dict)])
        elif isinstance(payload, dict):
            if isinstance(payload.get("items"), list):
                rows.extend([row for row in payload["items"] if isinstance(row, dict)])
            elif isinstance(payload.get("outcomes"), list):
                rows.extend([row for row in payload["outcomes"] if isinstance(row, dict)])
            else:
                rows.append(payload)
    return rows


def _match_key_pairs(decision: dict[str, Any], outcome: dict[str, Any]) -> bool:
    for key in ("decision_id", "review_item_id"):
        if decision.get(key) and outcome.get(key) and str(decision.get(key)) == str(outcome.get(key)):
            return True
    if decision.get("market_type") and outcome.get("market_type") and str(decision.get("market_type")) != str(outcome.get("market_type")):
        return False
    if decision.get("close_time") and outcome.get("close_time") and str(decision.get("close_time")) != str(outcome.get("close_time")):
        return False
    contract_decision = decision.get("contract_id") or decision.get("ticker")
    contract_outcome = outcome.get("contract_id") or outcome.get("ticker")
    if contract_decision and contract_outcome and str(contract_decision) == str(contract_outcome):
        if str(decision.get("provider") or "") == str(outcome.get("provider") or decision.get("provider") or ""):
            return True
    if decision.get("run_id") and outcome.get("run_id") and str(decision.get("run_id")) == str(outcome.get("run_id")):
        ticker_decision = decision.get("ticker") or decision.get("contract_id")
        ticker_outcome = outcome.get("ticker") or outcome.get("contract_id")
        if ticker_decision and ticker_outcome and str(ticker_decision) == str(ticker_outcome):
            return True
    return False


def match_outcomes_to_paper_decisions(
    decisions: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for decision in decisions:
        row = dict(decision)
        outcome_match = next((outcome for outcome in outcomes if _match_key_pairs(row, outcome)), None)
        if outcome_match:
            status = outcome_match.get("outcome_status") or outcome_match.get("settlement_status") or "settled"
            row["outcome_status"] = status
            row["settled_at"] = outcome_match.get("settled_at", row.get("settled_at"))
            row["final_outcome"] = outcome_match.get("final_outcome", row.get("final_outcome"))
            row["paper_result"] = outcome_match.get("paper_result", row.get("paper_result"))
            row["paper_roi_estimate"] = outcome_match.get("paper_roi_estimate", row.get("paper_roi_estimate"))
            row["calibration_bucket"] = outcome_match.get("calibration_bucket", row.get("calibration_bucket"))
        matched.append(row)
    return matched


def summarize_outcome_coverage(
    decisions: list[dict[str, Any]],
    outcomes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    outcomes = outcomes or []
    rows = match_outcomes_to_paper_decisions(decisions, outcomes) if outcomes else list(decisions)
    settled = [row for row in rows if _normalized_outcome_label(row.get("final_outcome")) is not None]
    pending = [
        row
        for row in rows
        if _normalized_outcome_label(row.get("final_outcome")) is None
        and str(row.get("outcome_status") or "pending").lower() not in {"void", "cancelled"}
    ]
    void = [row for row in rows if str(row.get("outcome_status") or "").lower() in {"void", "cancelled"}]
    total = len(rows)
    return {
        "sample_size": total,
        "settled_count": len(settled),
        "pending_count": len(pending),
        "void_count": len(void),
        "coverage_rate": round(len(settled) / total, 6) if total else 0.0,
        "matched_outcome_count": len(settled),
        "unmatched_outcome_count": max(0, len(outcomes) - len(settled)),
    }


def _labeled_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labeled = []
    for row in rows:
        prediction = to_float_or_none(row.get("implied_probability"))
        actual = _normalized_outcome_label(row.get("final_outcome"))
        if prediction is None or actual is None:
            continue
        if prediction > 1.0:
            prediction = prediction / 100.0
        if not 0.0 <= prediction <= 1.0:
            continue
        copy = dict(row)
        copy["_prediction"] = prediction
        copy["_actual"] = actual
        labeled.append(copy)
    return labeled


def _bucket_metrics(rows: list[dict[str, Any]], bucket_fn, field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        bucket = bucket_fn(row.get(field))
        grouped.setdefault(bucket, []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for bucket, members in sorted(grouped.items()):
        avg_pred = sum(float(row["_prediction"]) for row in members) / len(members)
        outcome_rate = sum(float(row["_actual"]) for row in members) / len(members)
        bucket_brier = sum((float(row["_prediction"]) - float(row["_actual"])) ** 2 for row in members) / len(members)
        out[bucket] = {
            "count": len(members),
            "average_prediction": round(avg_pred, 6),
            "outcome_rate": round(outcome_rate, 6),
            "brier_score": round(bucket_brier, 6),
        }
    return out


def _liquidity_metrics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("liquidity_tier") or "unknown"), []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for tier, members in sorted(grouped.items()):
        out[tier] = {
            "count": len(members),
            "outcome_rate": round(sum(float(row["_actual"]) for row in members) / len(members), 6),
            "average_prediction": round(sum(float(row["_prediction"]) for row in members) / len(members), 6),
        }
    return out


def calculate_calibration_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labeled = _labeled_rows(rows)
    if not labeled:
        return {}
    brier = sum((float(row["_prediction"]) - float(row["_actual"])) ** 2 for row in labeled) / len(labeled)
    false_positive_rows = [row for row in labeled if float(row["_prediction"]) >= 0.5]
    false_positive_rate = None
    if false_positive_rows:
        false_positive_rate = sum(1 for row in false_positive_rows if float(row["_actual"]) == 0.0) / len(false_positive_rows)
    roi_values = [to_float_or_none(row.get("paper_roi_estimate")) for row in labeled]
    roi_values = [value for value in roi_values if value is not None]
    metrics = {
        "brier_score": round(brier, 6),
        "calibration_buckets": _bucket_metrics(labeled, _bucket_probability, "implied_probability"),
        "confidence_bucket_performance": _bucket_metrics(labeled, _bucket_score, "confidence_score"),
        "review_priority_bucket_performance": _bucket_metrics(labeled, _bucket_score, "review_priority_score"),
        "performance_by_liquidity_tier": _liquidity_metrics(labeled),
    }
    if false_positive_rate is not None:
        metrics["false_positive_rate"] = round(false_positive_rate, 6)
    if roi_values:
        metrics["average_paper_roi_estimate"] = round(sum(roi_values) / len(roi_values), 6)
    return metrics


def _status_for_counts(total: int, settled: int) -> str:
    if total <= 0 or settled <= 0:
        return "insufficient_data"
    if settled < total:
        return "partial_calibration"
    return "metrics_ready"


def _next_required_data(status: str) -> list[str]:
    if status == "insufficient_data":
        return ["settlement_results"]
    if status == "partial_calibration":
        return ["additional_settlement_results"]
    return []


def build_calibration_report(
    *,
    base_data_dir: str = "data",
    paper_decisions: list[dict[str, Any]] | None = None,
    outcome_records: list[dict[str, Any]] | None = None,
    review_items: list[dict[str, Any]] | None = None,
    write_report: bool = False,
) -> dict[str, Any]:
    decisions = [row for row in (paper_decisions if paper_decisions is not None else load_paper_decisions(base_data_dir)) if isinstance(row, dict)]
    outcomes = [row for row in (outcome_records if outcome_records is not None else load_outcome_records(base_data_dir)) if isinstance(row, dict)]
    matched = match_outcomes_to_paper_decisions(decisions, outcomes) if outcomes else decisions
    coverage = summarize_outcome_coverage(decisions, outcomes)
    metrics = calculate_calibration_metrics(matched)
    status = _status_for_counts(coverage["sample_size"], coverage["settled_count"])
    queue_state = load_review_queue_state({"paths": {"review_queue": str(Path(base_data_dir) / "review_queue")}})
    queue_items = review_items if review_items is not None else list(queue_state.get("items", []))
    ledger_summary = summarize_paper_decisions(decisions)
    report = {
        "ok": True,
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "status": status,
        "created_at": utc_now_iso(),
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "review_items_count": len(queue_items),
        "paper_decisions_count": len(decisions),
        "review_items_available_count": len(queue_items),
        "paper_ledger_records_count": len(decisions),
        "records_with_outcome_count": coverage["settled_count"],
        "records_without_outcome_count": max(0, len(decisions) - coverage["settled_count"]),
        "provider_counts": ledger_summary["provider_counts"],
        "market_type_counts": ledger_summary["market_type_counts"],
        "liquidity_tier_counts": ledger_summary["liquidity_tier_counts"],
        "score_field_presence_counts": ledger_summary["score_field_presence_counts"],
        "settlement_field_presence_counts": ledger_summary["settlement_field_presence_counts"],
        "score_bucket_counts": _score_bucket_counts(decisions),
        "sample_size": coverage["sample_size"],
        "settled_count": coverage["settled_count"],
        "pending_count": coverage["pending_count"],
        "void_count": coverage["void_count"],
        "coverage_rate": coverage["coverage_rate"],
        "metrics": metrics if status != "insufficient_data" else {},
        "next_required_data": _next_required_data(status),
        "compact_response": True,
        "raw_payload_included": False,
    }
    if write_report:
        path = _report_dir(base_data_dir) / f"calibration_{sanitize_filename(report['created_at'])}.json"
        _atomic_write_json(path, report)
        report["report_path"] = _project_relative_path(base_data_dir, path)
    return report


def run_calibration_scaffold(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    report = build_calibration_report(paper_decisions=rows or [], outcome_records=[], review_items=[])
    return {
        "ok": True,
        "status": report["status"],
        "sample_size": report["sample_size"],
        "settled_count": report["settled_count"],
        "pending_count": report["pending_count"],
        "void_count": report["void_count"],
        "coverage_rate": report["coverage_rate"],
        "insufficient_data": report["status"] == "insufficient_data",
        "metrics": report["metrics"],
        "next_required_data": report["next_required_data"],
    }
