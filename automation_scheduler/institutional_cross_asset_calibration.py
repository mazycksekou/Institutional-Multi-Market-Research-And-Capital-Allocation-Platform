from __future__ import annotations

from statistics import median
from typing import Any

from .institutional_cross_asset_scores import normalize_probability, to_float


ASSET_CLASSES = ("prediction_market", "stock", "bond", "major_asset", "sportsbook")
FIRST_REVIEW_CHECKPOINT = 30


def _bucket_probability(value: Any) -> str:
    parsed = normalize_probability(value)
    if parsed is None:
        return "missing"
    lower = int(min(0.999999, parsed) * 5) * 20
    return f"{lower:02d}-{lower + 20:02d}"


def _bucket_score(value: Any) -> str:
    parsed = to_float(value)
    if parsed is None:
        return "missing"
    bounded = max(0.0, min(99.999999, parsed))
    lower = int(bounded // 20) * 20
    return f"{lower:02d}-{lower + 20:02d}"


def _outcome_label(row: dict[str, Any]) -> float | None:
    status = str(row.get("outcome_status") or "").lower()
    final = row.get("final_outcome")
    if status not in {"settled", "completed"}:
        return None
    text = str(final or "").strip().lower()
    if text in {"yes", "win", "true", "1"}:
        return 1.0
    if text in {"no", "loss", "false", "0"}:
        return 0.0
    return None


def _prediction_value(row: dict[str, Any]) -> float | None:
    for field in ("model_probability", "implied_probability", "no_vig_probability"):
        value = row.get(field)
        if value is not None:
            return normalize_probability(value)
    return None


def _status(outcome_count: int) -> str:
    if outcome_count <= 0:
        return "insufficient_data"
    if outcome_count < FIRST_REVIEW_CHECKPOINT:
        return "partial_calibration"
    return "metrics_ready"


def _sample_warning(outcome_count: int) -> list[str]:
    if outcome_count <= 0:
        return ["missing_outcomes"]
    if outcome_count < 30:
        return ["severe_insufficient_sample"]
    if outcome_count < 100:
        return ["first_review_checkpoint_only"]
    if outcome_count < 300:
        return ["limited_bucket_level_sample"]
    if outcome_count < 1000:
        return ["useful_but_not_long_term_sample"]
    return []


def _base_report(asset_class: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    settled = [row for row in records if str(row.get("outcome_status") or "").lower() in {"settled", "completed"}]
    void = [row for row in records if str(row.get("outcome_status") or "").lower() in {"void", "cancelled"}]
    return {
        "status": "insufficient_data",
        "asset_class": asset_class,
        "paper_decisions_count": len(records),
        "outcome_records_count": len(settled) + len(void),
        "matched_outcomes_count": 0,
        "pending_count": max(0, len(records) - len(settled) - len(void)),
        "settled_count": len(settled),
        "void_count": len(void),
        "coverage_rate": 0.0,
        "insufficient_sample": True,
        "metrics": {},
        "warnings": [],
        "next_required_data": [],
    }


def _grouped_binary_metrics(rows: list[dict[str, Any]], bucket_field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    bucket_fn = _bucket_probability if bucket_field in {"implied_probability", "model_probability", "no_vig_probability"} else _bucket_score
    for row in rows:
        groups.setdefault(bucket_fn(row.get(bucket_field)), []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for bucket, members in sorted(groups.items()):
        predictions = [_prediction_value(row) for row in members]
        labels = [_outcome_label(row) for row in members]
        pairs = [(p, y) for p, y in zip(predictions, labels) if p is not None and y is not None]
        if not pairs:
            continue
        out[bucket] = {
            "count": len(pairs),
            "average_prediction": round(sum(p for p, _ in pairs) / len(pairs), 6),
            "outcome_rate": round(sum(y for _, y in pairs) / len(pairs), 6),
            "brier_score": round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 6),
        }
    return out


def _prediction_market_metrics(records: list[dict[str, Any]]) -> tuple[int, dict[str, Any], list[str]]:
    labeled = [row for row in records if _outcome_label(row) is not None and _prediction_value(row) is not None]
    if not labeled:
        return 0, {}, ["explicit_yes_no_outcomes_with_probabilities"]
    pairs = [(_prediction_value(row), _outcome_label(row)) for row in labeled]
    clean_pairs = [(p, y) for p, y in pairs if p is not None and y is not None]
    brier = sum((p - y) ** 2 for p, y in clean_pairs) / len(clean_pairs)
    return len(clean_pairs), {
        "brier_score": round(brier, 6),
        "calibration_buckets": _grouped_binary_metrics(labeled, "implied_probability"),
        "performance_by_liquidity_tier": _group_by_outcome_rate(labeled, "liquidity_tier"),
        "pricing_quality_bucket_performance": _grouped_binary_metrics(labeled, "pricing_quality_score"),
        "review_priority_bucket_performance": _grouped_binary_metrics(labeled, "review_priority_score"),
        "confidence_bucket_performance": _grouped_binary_metrics(labeled, "confidence_score"),
    }, []


def _group_by_outcome_rate(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row.get(field) or "unknown"), []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for key, members in sorted(groups.items()):
        labels = [_outcome_label(row) for row in members]
        labels = [label for label in labels if label is not None]
        if labels:
            out[key] = {"count": len(labels), "outcome_rate": round(sum(labels) / len(labels), 6)}
    return out


def _return_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in records:
        observed = to_float(row.get("observed_price"))
        final = to_float(row.get("final_price"))
        ret = to_float(row.get("return_pct"))
        if ret is None and observed and final is not None:
            ret = ((final - observed) / observed) * 100.0
        if ret is None:
            continue
        copy = dict(row)
        copy["_return_pct"] = ret
        out.append(copy)
    return out


def _return_metrics(records: list[dict[str, Any]]) -> tuple[int, dict[str, Any], list[str]]:
    rows = _return_rows(records)
    if not rows:
        return 0, {}, ["horizon_final_price"]
    returns = [float(row["_return_pct"]) for row in rows]
    metrics = {
        "average_forward_return_pct": round(sum(returns) / len(returns), 6),
        "median_forward_return_pct": round(median(returns), 6),
        "positive_return_rate": round(sum(1 for value in returns if value > 0) / len(returns), 6),
        "performance_by_liquidity_tier": _group_return(rows, "liquidity_tier"),
        "performance_by_risk_score_bucket": _group_return(rows, "risk_score"),
        "performance_by_confidence_score_bucket": _group_return(rows, "confidence_score"),
    }
    if any(row.get("asset_class") == "stock" for row in records):
        metrics["performance_by_valuation_score_bucket"] = _group_return(rows, "valuation_score")
        metrics["performance_by_financial_quality_score_bucket"] = _group_return(rows, "financial_quality_score")
    else:
        metrics["performance_by_macro_quality_score_bucket"] = _group_return(rows, "macro_quality_score")
    return len(rows), metrics, []


def _group_return(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        key = str(row.get(field) or "unknown")
        if field.endswith("_score") or field == "risk_score":
            key = _bucket_score(row.get(field))
        groups.setdefault(key, []).append(float(row["_return_pct"]))
    out: dict[str, dict[str, Any]] = {}
    for key, values in sorted(groups.items()):
        out[key] = {
            "count": len(values),
            "average_return_pct": round(sum(values) / len(values), 6),
            "median_return_pct": round(median(values), 6),
        }
    return out


def _sportsbook_metrics(records: list[dict[str, Any]]) -> tuple[int, dict[str, Any], list[str]]:
    settled = [
        row
        for row in records
        if str(row.get("outcome_status") or "").lower() in {"settled", "completed"}
        and str(row.get("final_outcome") or "").lower() in {"win", "loss", "push"}
    ]
    if not settled:
        return 0, {}, ["settled_win_loss_push_results"]
    wins = [row for row in settled if str(row.get("final_outcome") or "").lower() == "win"]
    pushes = [row for row in settled if str(row.get("final_outcome") or "").lower() == "push"]
    losses = [row for row in settled if str(row.get("final_outcome") or "").lower() == "loss"]
    metrics = {
        "hit_rate": round(len(wins) / max(1, len(wins) + len(losses)), 6),
        "push_rate": round(len(pushes) / len(settled), 6),
        "void_rate": round(len([row for row in records if str(row.get("outcome_status") or "").lower() in {"void", "cancelled"}]) / max(1, len(records)), 6),
        "performance_by_market_type": _group_sports_result(settled, "market_type"),
        "performance_by_liquidity_tier": _group_sports_result(settled, "liquidity_tier"),
        "edge_bucket_performance": _group_sports_result(settled, "edge"),
        "confidence_bucket_performance": _group_sports_result(settled, "confidence_score"),
    }
    brier_rows = [row for row in settled if _prediction_value(row) is not None and _outcome_label(row) is not None]
    if brier_rows:
        metrics["brier_score"] = round(
            sum((_prediction_value(row) - _outcome_label(row)) ** 2 for row in brier_rows) / len(brier_rows),
            6,
        )
    return len(settled), metrics, []


def _group_sports_result(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = str(row.get(field) or "unknown")
        if field in {"edge", "confidence_score"}:
            key = _bucket_score(row.get(field))
        groups.setdefault(key, []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for key, members in sorted(groups.items()):
        wins = len([row for row in members if str(row.get("final_outcome") or "").lower() == "win"])
        losses = len([row for row in members if str(row.get("final_outcome") or "").lower() == "loss"])
        pushes = len([row for row in members if str(row.get("final_outcome") or "").lower() == "push"])
        out[key] = {
            "count": len(members),
            "hit_rate": round(wins / max(1, wins + losses), 6),
            "push_rate": round(pushes / len(members), 6),
        }
    return out


def calibrate_asset_class(records: list[dict[str, Any]], asset_class: str) -> dict[str, Any]:
    rows = [row for row in records if row.get("asset_class") == asset_class]
    report = _base_report(asset_class, rows)
    if asset_class == "prediction_market":
        matched_count, metrics, required = _prediction_market_metrics(rows)
    elif asset_class in {"stock", "bond", "major_asset"}:
        matched_count, metrics, required = _return_metrics(rows)
    elif asset_class == "sportsbook":
        matched_count, metrics, required = _sportsbook_metrics(rows)
    else:
        matched_count, metrics, required = 0, {}, ["supported_asset_class"]

    report["matched_outcomes_count"] = matched_count
    report["coverage_rate"] = round(matched_count / len(rows), 6) if rows else 0.0
    report["status"] = _status(matched_count)
    report["insufficient_sample"] = matched_count < FIRST_REVIEW_CHECKPOINT
    report["metrics"] = metrics if matched_count > 0 else {}
    report["warnings"] = _sample_warning(matched_count)
    if required:
        report["next_required_data"] = required
    elif matched_count < FIRST_REVIEW_CHECKPOINT:
        report["next_required_data"] = ["more_explicit_outcomes"]
    elif matched_count < 100:
        report["next_required_data"] = ["more_outcomes_for_useful_calibration_read"]
    else:
        report["next_required_data"] = []
    return report


def build_calibration_by_asset_class(records: list[dict[str, Any]]) -> dict[str, Any]:
    reports = {asset_class: calibrate_asset_class(records, asset_class) for asset_class in ASSET_CLASSES}
    return {
        "status": "metrics_ready" if any(report["status"] == "metrics_ready" for report in reports.values()) else (
            "partial_calibration" if any(report["status"] == "partial_calibration" for report in reports.values()) else "insufficient_data"
        ),
        "asset_classes": reports,
        "matched_outcomes_count": sum(report["matched_outcomes_count"] for report in reports.values()),
        "outcome_records_count": sum(report["outcome_records_count"] for report in reports.values()),
        "insufficient_sample": any(report["insufficient_sample"] for report in reports.values()),
        "next_required_data": sorted({item for report in reports.values() for item in report.get("next_required_data", [])}),
    }
