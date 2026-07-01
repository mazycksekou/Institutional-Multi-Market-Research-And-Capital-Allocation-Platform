from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from src.data.data_paths import get_storage_health, resolve_base_data_dir
from src.market_intelligence.manifold_feature_builder import FEATURE_VECTOR_VERSION
from src.services.outcome_store import load_outcome_records
from src.brokerage.paper_decision_ledger import load_paper_decisions, to_float_or_none
from src.services.scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso


MANIFOLD_CALIBRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.market_state_manifold.calibration.v1"
MIN_CLUSTER_SAMPLE = 30


def _manifold_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "manifold"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _calibration_dir(base_data_dir: str = "data") -> Path:
    path = _manifold_dir(base_data_dir) / "calibration"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _calibration_dir(base_data_dir) / "latest.json"


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


def _outcome_label(row: dict[str, Any]) -> float | None:
    for key in ("final_outcome", "paper_result", "settlement_result", "return_or_result"):
        value = row.get(key)
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        text = str(value or "").strip().lower()
        if text in {"yes", "win", "true", "hit", "profitable", "1"}:
            return 1.0
        if text in {"no", "loss", "false", "miss", "unprofitable", "0"}:
            return 0.0
    ret = _return_value(row)
    if ret is not None:
        if ret > 0:
            return 1.0
        if ret < 0:
            return 0.0
    return None


def _return_value(row: dict[str, Any]) -> float | None:
    for key in ("return_or_result", "paper_roi_estimate", "return_pct", "return"):
        value = to_float_or_none(row.get(key))
        if value is not None:
            if abs(value) > 1.0 and key != "return_or_result":
                value = value / 100.0
            return value
    return None


def _probability(row: dict[str, Any]) -> float | None:
    for key in ("model_probability", "implied_probability", "no_vig_probability", "market_implied_probability"):
        value = to_float_or_none(row.get(key))
        if value is None:
            continue
        if value > 1.0:
            value = value / 100.0
        if 0.0 <= value <= 1.0:
            return value
    return None


def _is_settled(row: dict[str, Any]) -> bool:
    status = str(row.get("outcome_status") or row.get("settlement_status") or "").strip().lower()
    if status in {"settled", "completed", "closed"}:
        return True
    return _outcome_label(row) is not None


def _profit_factor(returns: list[float]) -> float | None:
    gains = sum(value for value in returns if value > 0)
    losses = abs(sum(value for value in returns if value < 0))
    if gains <= 0 and losses <= 0:
        return None
    if losses <= 0:
        return None
    return round(gains / losses, 6)


def _confidence_interval(rate: float, sample_size: int) -> dict[str, float] | None:
    if sample_size < MIN_CLUSTER_SAMPLE:
        return None
    stderr = math.sqrt(max(0.0, rate * (1.0 - rate)) / sample_size)
    return {
        "method": "normal_approximation",
        "lower": round(max(0.0, rate - 1.96 * stderr), 6),
        "upper": round(min(1.0, rate + 1.96 * stderr), 6),
    }


def _calibration_error(rows: list[dict[str, Any]]) -> float | None:
    pairs = []
    for row in rows:
        prediction = _probability(row)
        label = _outcome_label(row)
        if prediction is not None and label is not None:
            pairs.append((prediction, label))
    if not pairs:
        return None
    return round(sum(abs(prediction - label) for prediction, label in pairs) / len(pairs), 6)


def _negative_ev_rate(rows: list[dict[str, Any]]) -> float | None:
    returns = [_return_value(row) for row in rows]
    returns = [value for value in returns if value is not None]
    if not returns:
        return None
    return round(sum(1 for value in returns if value < 0) / len(returns), 6)


def _cluster_stats(cluster_id: str, rows: list[dict[str, Any]], *, min_sample: int = MIN_CLUSTER_SAMPLE) -> dict[str, Any]:
    settled = [row for row in rows if _is_settled(row) and _outcome_label(row) is not None]
    labels = [_outcome_label(row) for row in settled]
    labels = [label for label in labels if label is not None]
    returns = [_return_value(row) for row in settled]
    returns = [value for value in returns if value is not None]
    sample_size = len(settled)
    win_rate = round(sum(labels) / len(labels), 6) if labels else None
    loss_rate = round(1.0 - win_rate, 6) if win_rate is not None else None
    average_return = round(sum(returns) / len(returns), 6) if returns else None
    false_breakouts = [row for row in settled if bool(row.get("false_breakout"))]
    high_confidence = [
        row
        for row in settled
        if (to_float_or_none(row.get("confidence_score")) or 0.0) >= 70.0
        or ((_probability(row) or 0.0) >= 0.60)
    ]
    false_positive_rate = None
    if high_confidence:
        false_positive_rate = round(
            sum(1 for row in high_confidence if _outcome_label(row) == 0.0) / len(high_confidence),
            6,
        )
    no_bet_rows = [row for row in rows if str(row.get("recommended_action_at_detection") or row.get("recommended_action") or "").upper() in {"NO_BET", "NO_TRADE", "NO_REVIEW"}]
    no_bet_success_rate = None
    if no_bet_rows:
        avoided_bad = [row for row in no_bet_rows if (_outcome_label(row) == 0.0 or (_return_value(row) is not None and (_return_value(row) or 0.0) <= 0.0))]
        no_bet_success_rate = round(len(avoided_bad) / len(no_bet_rows), 6)
    mfe = [to_float_or_none(row.get("max_favorable_excursion")) for row in rows]
    mae = [to_float_or_none(row.get("max_adverse_excursion")) for row in rows]
    mfe = [value for value in mfe if value is not None]
    mae = [value for value in mae if value is not None]
    calibration_error = _calibration_error(settled)
    expected_value = average_return
    insufficient = sample_size < min_sample
    return {
        "manifold_cluster_id": cluster_id,
        "sample_size": sample_size,
        "outcome_coverage": round(sample_size / len(rows), 6) if rows else 0.0,
        "win_rate": win_rate if not insufficient else None,
        "loss_rate": loss_rate if not insufficient else None,
        "average_return": average_return if not insufficient else None,
        "historical_roi": average_return if not insufficient else None,
        "profit_factor": _profit_factor(returns) if not insufficient else None,
        "average_mfe": round(sum(mfe) / len(mfe), 6) if mfe and not insufficient else None,
        "average_mae": round(sum(mae) / len(mae), 6) if mae and not insufficient else None,
        "false_positive_rate": false_positive_rate if not insufficient else None,
        "false_breakout_rate": round(len(false_breakouts) / sample_size, 6) if sample_size and not insufficient else None,
        "no_bet_success_rate": no_bet_success_rate if not insufficient else None,
        "calibration_error": calibration_error if not insufficient else None,
        "expected_value": expected_value if not insufficient else None,
        "confidence_interval": _confidence_interval(win_rate, len(labels)) if win_rate is not None and not insufficient else None,
        "historical_negative_ev_rate": _negative_ev_rate(settled) if not insufficient else None,
        "insufficient_sample": insufficient,
    }


def compute_historical_cluster_stats(records: list[dict[str, Any]] | None, *, min_sample: int = MIN_CLUSTER_SAMPLE) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in records or []:
        if not isinstance(row, dict):
            continue
        cluster_id = row.get("manifold_cluster_id")
        if not cluster_id:
            continue
        grouped.setdefault(str(cluster_id), []).append(row)
    return {cluster_id: _cluster_stats(cluster_id, rows, min_sample=min_sample) for cluster_id, rows in sorted(grouped.items())}


def calibration_status_for_sample(sample_size: int, *, min_sample: int = MIN_CLUSTER_SAMPLE) -> str:
    if sample_size <= 0:
        return "insufficient_data"
    if sample_size < min_sample:
        return "partial_calibration"
    return "metrics_ready"


def build_manifold_calibration_bucket(
    detection: dict[str, Any],
    *,
    outcome_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = dict(outcome_record or {})
    source = {**row, **detection}
    return {
        "asset_type": source.get("asset_type"),
        "market_type": source.get("market_type"),
        "provider_name": source.get("provider_name") or source.get("provider") or source.get("provider_id"),
        "model_family": source.get("model_family") or source.get("model_group") or source.get("institutional_model_family"),
        "manifold_cluster_id": source.get("manifold_cluster_id"),
        "pattern_id": source.get("pattern_id") or source.get("candlestick_pattern_id"),
        "game_script_cluster": source.get("game_script_cluster") or source.get("manifold_cluster_name"),
        "liquidity_tier": source.get("liquidity_tier") or source.get("liquidity_quality"),
        "time_of_day": source.get("time_of_day") or source.get("time_of_day_bucket"),
        "data_resolution": source.get("data_resolution"),
        "latency_tier": source.get("latency_tier"),
        "requested_window_seconds": source.get("requested_window_seconds"),
        "effective_window_seconds": source.get("effective_window_seconds"),
        "delayed_by_seconds": source.get("delayed_by_seconds"),
        "delay_source": source.get("delay_source"),
        "usable_for_calibration": source.get("usable_for_calibration"),
        "catalyst_type": source.get("catalyst_type"),
        "balance_sheet_risk_bucket": source.get("balance_sheet_risk_bucket"),
        "settlement_required": bool(source.get("settlement_required", source.get("asset_type") == "prediction_market")),
        "feature_vector_version": source.get("feature_vector_version", FEATURE_VECTOR_VERSION),
        "neighbor_count_at_detection": source.get("neighbor_count_at_detection", source.get("neighbor_sample_size")),
        "out_of_distribution_score_at_detection": source.get(
            "out_of_distribution_score_at_detection",
            source.get("out_of_distribution_score"),
        ),
        "recommended_action_at_detection": source.get("recommended_action_at_detection", source.get("recommended_action")),
        "outcome_window": source.get("outcome_window"),
        "final_outcome": source.get("final_outcome"),
        "return_or_result": source.get("return_or_result", source.get("paper_roi_estimate", source.get("return_pct"))),
        "max_favorable_excursion": source.get("max_favorable_excursion"),
        "max_adverse_excursion": source.get("max_adverse_excursion"),
        "hit_target": source.get("hit_target"),
        "hit_stop": source.get("hit_stop"),
        "false_breakout": source.get("false_breakout"),
        "line_moved_with_prediction": source.get("line_moved_with_prediction"),
        "settlement_result": source.get("settlement_result"),
        "calibration_status": source.get("calibration_status"),
    }


def build_manifold_calibration_report(
    *,
    records: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
    write_report: bool = False,
    min_sample: int = MIN_CLUSTER_SAMPLE,
) -> dict[str, Any]:
    if records is None:
        paper_rows = [row for row in load_paper_decisions(base_data_dir) if isinstance(row, dict)]
        outcome_rows = [row for row in load_outcome_records(base_data_dir) if isinstance(row, dict)]
        records = [row for row in paper_rows + outcome_rows if row.get("manifold_cluster_id")]
    stats = compute_historical_cluster_stats(records, min_sample=min_sample)
    total_records = len([row for row in records or [] if isinstance(row, dict)])
    settled_records = len([row for row in records or [] if isinstance(row, dict) and _is_settled(row)])
    report = {
        "ok": True,
        "schema_version": MANIFOLD_CALIBRATION_SCHEMA_VERSION,
        "status": "metrics_ready" if any(not row.get("insufficient_sample") for row in stats.values()) else "insufficient_data",
        "created_at": utc_now_iso(),
        "feature_vector_version": FEATURE_VECTOR_VERSION,
        "cluster_count": len(stats),
        "records_count": total_records,
        "settled_count": settled_records,
        "outcome_coverage": round(settled_records / total_records, 6) if total_records else 0.0,
        "clusters": stats,
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
    if write_report:
        report.update(write_manifold_calibration_report(report, base_data_dir=base_data_dir))
    return report


def write_manifold_calibration_report(report: dict[str, Any], *, base_data_dir: str = "data") -> dict[str, Any]:
    payload = dict(report)
    payload["schema_version"] = payload.get("schema_version") or MANIFOLD_CALIBRATION_SCHEMA_VERSION
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    payload["auto_execution"] = False
    payload["auto_execution_enabled"] = False
    payload["human_approval_required"] = True
    payload["actual_orders_submitted"] = 0
    payload["actual_bets_submitted"] = 0
    payload["actual_trades_submitted"] = 0
    payload["raw_payload_included"] = False
    payload["secrets_included"] = False
    latest = _latest_path(base_data_dir)
    history = _calibration_dir(base_data_dir) / f"{sanitize_filename(utc_now_iso()[:10])}.json"
    _atomic_write_json(latest, payload)
    _atomic_write_json(history, payload)
    return {
        "storage_backend": "file",
        "calibration_path": _project_relative_path(base_data_dir, latest),
        "calibration_history_path": _project_relative_path(base_data_dir, history),
    }


def load_manifold_calibration_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    if isinstance(payload, dict):
        payload["storage_health"] = get_storage_health()
        return payload
    return build_manifold_calibration_report(base_data_dir=base_data_dir, write_report=False)


def compact_manifold_calibration_report(report: dict[str, Any], *, limit: int = 25) -> dict[str, Any]:
    cap = max(1, min(int(limit or 25), 100))
    clusters = []
    cluster_map = report.get("clusters", {}) if isinstance(report.get("clusters"), dict) else {}
    for cluster_id, stats in list(cluster_map.items())[:cap]:
        if not isinstance(stats, dict):
            continue
        clusters.append(
            {
                "manifold_cluster_id": cluster_id,
                "sample_size": int(stats.get("sample_size", 0) or 0),
                "outcome_coverage": stats.get("outcome_coverage"),
                "win_rate": stats.get("win_rate"),
                "historical_roi": stats.get("historical_roi"),
                "profit_factor": stats.get("profit_factor"),
                "calibration_error": stats.get("calibration_error"),
                "insufficient_sample": bool(stats.get("insufficient_sample", True)),
            }
        )
    return {
        "ok": bool(report.get("ok", True)),
        "status": report.get("status", "insufficient_data"),
        "schema_version": report.get("schema_version", MANIFOLD_CALIBRATION_SCHEMA_VERSION),
        "feature_vector_version": report.get("feature_vector_version", FEATURE_VECTOR_VERSION),
        "cluster_count": int(report.get("cluster_count", len(clusters))),
        "records_count": int(report.get("records_count", 0)),
        "settled_count": int(report.get("settled_count", 0)),
        "outcome_coverage": report.get("outcome_coverage", 0.0),
        "clusters": clusters,
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
