from __future__ import annotations

"""Canonical Phase 5.6 pipeline validation and hardening snapshot."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.backtesting.baseline_backtesting import (
    DEFAULT_BASELINE_BACKTEST_STORAGE_PATH,
    build_baseline_backtest_dashboard_snapshot,
)
from src.backtesting.decision_row_population import build_decision_row_population_dashboard_snapshot
from src.data.feature_registry import (
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
    build_feature_snapshot_population_dashboard_snapshot,
)
from src.data.historical_research_database import build_historical_dataset_population_dashboard_snapshot
from src.data.math_engine_population import build_math_engine_population_dashboard_snapshot
from src.market_intelligence.signal_population import get_signal_population_snapshot_for_dashboard
from src.storage.local_store import create_local_storage_engine


PIPELINE_VALIDATION_SCHEMA_VERSION = "src.backtesting.pipeline_validation.v1"
PIPELINE_VALIDATION_RUNTIME_VERSION = "phase5.6.pipeline_validation.v1"
DEFAULT_PIPELINE_VALIDATION_DATASET_ID = "dataset.sports.nfl.pipeline_validation"
DEFAULT_PIPELINE_VALIDATION_DATASET_NAME = "nfl_pipeline_validation"
DEFAULT_PIPELINE_VALIDATION_STORAGE_PATH = DEFAULT_BASELINE_BACKTEST_STORAGE_PATH
_PIPELINE_VALIDATION_SNAPSHOT_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _normalize_text(value).lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return default


def _parse_iso(value: Any) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _to_iso8601_utc(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, tuple):
            return list(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _path_exists(path_value: Any) -> bool:
    path_text = _normalize_text(path_value)
    return bool(path_text) and Path(path_text).exists()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _resolve_artifact_root(storage_path: Path, artifact_root: str | Path | None) -> Path:
    if artifact_root is not None:
        root = Path(artifact_root).expanduser().resolve()
    else:
        root = storage_path.resolve().parent / "pipeline_validation_artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _snapshot_cache_key(
    storage_path: str | Path | None,
    *,
    backend: str,
    artifact_root: str | Path | None,
    include_layer_snapshots: bool,
    persist_artifacts: bool,
) -> tuple[Any, ...]:
    resolved = Path(storage_path or DEFAULT_PIPELINE_VALIDATION_STORAGE_PATH).expanduser().resolve()
    stat = resolved.stat() if resolved.exists() else None
    resolved_artifact_root = _resolve_artifact_root(resolved, artifact_root)
    return (
        str(resolved),
        getattr(stat, "st_mtime_ns", 0),
        getattr(stat, "st_size", 0),
        backend,
        str(resolved_artifact_root),
        include_layer_snapshots,
        persist_artifacts,
    )


def _layer_timestamp(snapshot: Mapping[str, Any]) -> datetime | None:
    candidate_paths = (
        ("created_at",),
        ("updated_at",),
        ("backtest_run_row", "created_at"),
        ("backtest_run_row", "updated_at"),
        ("decision_population_summary", "created_at"),
        ("signal_population_summary", "created_at"),
        ("math_engine_population_summary", "created_at"),
        ("feature_population_summary", "created_at"),
    )
    parsed: list[datetime] = []
    for path in candidate_paths:
        current: Any = snapshot
        for key in path:
            if not isinstance(current, Mapping):
                current = ""
                break
            current = current.get(key)
        value = _parse_iso(current)
        if value is not None:
            parsed.append(value)
    return max(parsed) if parsed else None


def _check(
    *,
    layer: str,
    category: str,
    check_id: str,
    ok: bool,
    expected: Any,
    actual: Any,
    details: str,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "layer": layer,
        "category": category,
        "check_id": check_id,
        "ok": bool(ok),
        "expected": expected,
        "actual": actual,
        "details": details,
        "severity": severity,
    }


def _write_artifacts(
    *,
    artifact_root: Path,
    pipeline_validation_run_id: str,
    snapshot: Mapping[str, Any],
) -> dict[str, str]:
    run_root = artifact_root / pipeline_validation_run_id
    run_root.mkdir(parents=True, exist_ok=True)
    report_json_path = run_root / "report.json"
    report_markdown_path = run_root / "summary.md"
    dashboard_json_path = run_root / "dashboard.json"
    dashboard_payload = {
        "pipeline_validation_run_id": snapshot.get("pipeline_validation_run_id"),
        "status": snapshot.get("status"),
        "readiness": snapshot.get("readiness"),
        "lifecycle_state": snapshot.get("lifecycle_state"),
        "validation_timestamp": snapshot.get("validation_timestamp"),
        "lineage_summary": snapshot.get("lineage_summary"),
        "certification_summary": snapshot.get("certification_summary"),
        "performance_summary": snapshot.get("performance_summary"),
        "validation_summary": snapshot.get("validation_summary"),
        "unresolved_blockers": snapshot.get("unresolved_blockers"),
        "warnings": snapshot.get("warnings"),
    }
    markdown_lines = [
        f"# Phase 5.6 Pipeline Validation `{pipeline_validation_run_id}`",
        "",
        f"- Validation status: `{snapshot.get('status')}`",
        f"- Readiness: `{snapshot.get('readiness')}`",
        f"- Dataset batch: `{snapshot.get('lineage_summary', {}).get('dataset_batch_id', '')}`",
        f"- Decision batch: `{snapshot.get('lineage_summary', {}).get('decision_batch_id', '')}`",
        f"- Backtest run: `{snapshot.get('lineage_summary', {}).get('backtest_run_id', '')}`",
        f"- Error checks passed: `{snapshot.get('validation_summary', {}).get('error_checks_passed', 0)}` / `{snapshot.get('validation_summary', {}).get('error_check_count', 0)}`",
        f"- Warning checks passed: `{snapshot.get('validation_summary', {}).get('warning_checks_passed', 0)}` / `{snapshot.get('validation_summary', {}).get('warning_check_count', 0)}`",
        f"- Backtest sample size: `{snapshot.get('performance_summary', {}).get('sample_size', 0)}`",
        f"- Backtest ROI percent: `{snapshot.get('performance_summary', {}).get('roi_percent', 0.0)}`",
    ]
    layer_snapshot_summaries = {
        layer_name: {
            "status": layer_snapshot.get("status"),
            "readiness": layer_snapshot.get("readiness"),
            "batch_id": layer_snapshot.get("batch_id"),
            "dataset_id": layer_snapshot.get("dataset_id"),
            "dataset_certification_status": layer_snapshot.get("dataset_certification_status"),
            "backtest_run_id": layer_snapshot.get("backtest_run_id"),
            "sample_size": layer_snapshot.get("sample_size"),
            "artifact_integrity_ok": layer_snapshot.get("artifact_integrity_ok"),
        }
        for layer_name, layer_snapshot in dict(snapshot.get("layer_snapshots") or {}).items()
        if isinstance(layer_snapshot, Mapping)
    }
    report_payload = {
        "pipeline_validation_run_id": snapshot.get("pipeline_validation_run_id"),
        "schema_version": snapshot.get("schema_version"),
        "pipeline_validation_version": snapshot.get("pipeline_validation_version"),
        "status": snapshot.get("status"),
        "readiness": snapshot.get("readiness"),
        "lifecycle_state": snapshot.get("lifecycle_state"),
        "validation_timestamp": snapshot.get("validation_timestamp"),
        "dataset_id": snapshot.get("dataset_id"),
        "dataset_name": snapshot.get("dataset_name"),
        "lineage_summary": snapshot.get("lineage_summary"),
        "certification_summary": snapshot.get("certification_summary"),
        "performance_summary": snapshot.get("performance_summary"),
        "validation_summary": snapshot.get("validation_summary"),
        "validation_checks": snapshot.get("validation_checks"),
        "unresolved_blockers": snapshot.get("unresolved_blockers"),
        "warnings": snapshot.get("warnings"),
        "source_backtest_artifact_references": snapshot.get("source_backtest_artifact_references"),
        "layer_snapshot_summaries": layer_snapshot_summaries,
    }
    _write_text(report_json_path, json.dumps(report_payload, indent=2, sort_keys=True) + "\n")
    _write_text(report_markdown_path, "\n".join(markdown_lines) + "\n")
    _write_text(dashboard_json_path, json.dumps(dashboard_payload, indent=2, sort_keys=True) + "\n")
    return {
        "artifact_root": str(run_root),
        "report_json_path": str(report_json_path),
        "report_markdown_path": str(report_markdown_path),
        "dashboard_json_path": str(dashboard_json_path),
    }


def build_pipeline_validation_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    artifact_root: str | Path | None = None,
    include_layer_snapshots: bool = True,
    persist_artifacts: bool = True,
) -> dict[str, Any]:
    cache_key = _snapshot_cache_key(
        storage_path,
        backend=backend,
        artifact_root=artifact_root,
        include_layer_snapshots=include_layer_snapshots,
        persist_artifacts=persist_artifacts,
    )
    cached_snapshot = _PIPELINE_VALIDATION_SNAPSHOT_CACHE.get(cache_key)
    if cached_snapshot is not None:
        return copy.deepcopy(cached_snapshot)

    storage = create_local_storage_engine(
        storage_path or DEFAULT_PIPELINE_VALIDATION_STORAGE_PATH,
        backend=backend,
    )
    try:
        dataset_snapshot = build_historical_dataset_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            profile_id="sports:nfl",
            dataset_id=DEFAULT_NFL_HISTORICAL_DATASET_ID,
        )
        feature_snapshot = build_feature_snapshot_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=DEFAULT_NFL_HISTORICAL_DATASET_ID,
            include_source_dataset_snapshot=True,
        )
        math_snapshot = build_math_engine_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
        )
        signal_snapshot = get_signal_population_snapshot_for_dashboard(
            storage_path=storage.path,
            backend=backend,
        )
        decision_snapshot = build_decision_row_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
        )
        backtest_snapshot = build_baseline_backtest_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
        )

        validation_timestamp = _to_iso8601_utc(
            _layer_timestamp(backtest_snapshot)
            or _layer_timestamp(decision_snapshot)
            or _layer_timestamp(signal_snapshot)
            or _layer_timestamp(math_snapshot)
            or _layer_timestamp(feature_snapshot)
            or _layer_timestamp(dataset_snapshot)
        )
        pipeline_validation_run_id = _stable_id(
            "pipeline_validation",
            dataset_snapshot.get("batch_id"),
            feature_snapshot.get("batch_id"),
            math_snapshot.get("batch_id"),
            signal_snapshot.get("batch_id"),
            decision_snapshot.get("batch_id"),
            backtest_snapshot.get("backtest_run_id"),
            PIPELINE_VALIDATION_RUNTIME_VERSION,
        )

        checks = [
            _check(layer="dataset", category="status", check_id="dataset_ready", ok=dataset_snapshot.get("status") == "ready", expected="ready", actual=dataset_snapshot.get("status"), details="Historical dataset population snapshot must be ready."),
            _check(layer="dataset", category="certification", check_id="dataset_certified", ok=dataset_snapshot.get("dataset_certification_status") == "certified", expected="certified", actual=dataset_snapshot.get("dataset_certification_status"), details="Historical dataset must remain certified."),
            _check(layer="dataset", category="point_in_time", check_id="dataset_point_in_time_safe", ok=dataset_snapshot.get("point_in_time_validation_status") == "safe", expected="safe", actual=dataset_snapshot.get("point_in_time_validation_status"), details="Historical dataset point-in-time validation must remain safe."),
            _check(layer="dataset", category="lineage", check_id="dataset_lineage_complete", ok=_normalize_bool(dataset_snapshot.get("lineage_completeness")), expected=True, actual=dataset_snapshot.get("lineage_completeness"), details="Historical dataset lineage must be complete."),
            _check(layer="dataset", category="provenance", check_id="dataset_provenance_complete", ok=_normalize_bool(dataset_snapshot.get("provenance_completeness")), expected=True, actual=dataset_snapshot.get("provenance_completeness"), details="Historical dataset provenance must be complete."),
            _check(layer="feature", category="status", check_id="feature_ready", ok=feature_snapshot.get("status") == "ready" and feature_snapshot.get("readiness") == "feature_ready", expected="ready/feature_ready", actual=f"{feature_snapshot.get('status')} / {feature_snapshot.get('readiness')}", details="Feature snapshot population must be ready and feature_ready."),
            _check(layer="feature", category="certification", check_id="feature_source_dataset_certified", ok=feature_snapshot.get("dataset_certification_status") == "certified", expected="certified", actual=feature_snapshot.get("dataset_certification_status"), details="Feature snapshot summary must expose the certified source dataset status."),
            _check(layer="feature", category="point_in_time", check_id="feature_source_dataset_point_in_time_safe", ok=feature_snapshot.get("point_in_time_validation_status") == "safe", expected="safe", actual=feature_snapshot.get("point_in_time_validation_status"), details="Feature snapshot summary must expose the safe source dataset point-in-time status."),
            _check(layer="feature", category="lineage", check_id="feature_source_dataset_batch_match", ok=_normalize_text(feature_snapshot.get("source_dataset_batch_id")) == _normalize_text(dataset_snapshot.get("batch_id")), expected=_normalize_text(dataset_snapshot.get("batch_id")), actual=_normalize_text(feature_snapshot.get("source_dataset_batch_id")), details="Feature snapshot source dataset batch must match the certified dataset batch."),
            _check(layer="feature", category="lineage", check_id="feature_lineage_complete", ok=_normalize_bool(feature_snapshot.get("lineage_completeness")), expected=True, actual=feature_snapshot.get("lineage_completeness"), details="Feature snapshot summary must preserve source dataset lineage completeness."),
            _check(layer="feature", category="provenance", check_id="feature_provenance_complete", ok=_normalize_bool(feature_snapshot.get("provenance_completeness")), expected=True, actual=feature_snapshot.get("provenance_completeness"), details="Feature snapshot summary must preserve source dataset provenance completeness."),
            _check(layer="math", category="status", check_id="math_ready", ok=math_snapshot.get("status") == "ready" and math_snapshot.get("readiness") == "math_ready", expected="ready/math_ready", actual=f"{math_snapshot.get('status')} / {math_snapshot.get('readiness')}", details="Math engine population must be ready and math_ready."),
            _check(layer="math", category="certification", check_id="math_certified", ok=math_snapshot.get("dataset_certification_status") == "certified", expected="certified", actual=math_snapshot.get("dataset_certification_status"), details="Math engine output must remain certified."),
            _check(layer="math", category="lineage", check_id="math_source_feature_batch_match", ok=_normalize_text(math_snapshot.get("source_feature_batch_id")) == _normalize_text(feature_snapshot.get("batch_id")), expected=_normalize_text(feature_snapshot.get("batch_id")), actual=_normalize_text(math_snapshot.get("source_feature_batch_id")), details="Math engine source feature batch must match the persisted feature batch."),
            _check(layer="signal", category="status", check_id="signal_certified", ok=signal_snapshot.get("status") == "certified" and signal_snapshot.get("readiness") == "signal_ready", expected="certified/signal_ready", actual=f"{signal_snapshot.get('status')} / {signal_snapshot.get('readiness')}", details="Signal population must be certified and signal_ready."),
            _check(layer="signal", category="certification", check_id="signal_certification_complete", ok=signal_snapshot.get("dataset_certification_status") == "certified" and bool(_normalize_text(signal_snapshot.get("dataset_certification_id"))), expected="certified + certification id", actual=f"{signal_snapshot.get('dataset_certification_status')} / {_normalize_text(signal_snapshot.get('dataset_certification_id'))}", details="Signal layer must expose complete certification metadata."),
            _check(layer="signal", category="lineage", check_id="signal_source_math_batch_match", ok=_normalize_text(signal_snapshot.get("source_math_batch_id")) == _normalize_text(math_snapshot.get("batch_id")), expected=_normalize_text(math_snapshot.get("batch_id")), actual=_normalize_text(signal_snapshot.get("source_math_batch_id")), details="Signal source math batch must match the persisted math batch."),
            _check(layer="signal", category="lineage", check_id="signal_source_feature_batch_match", ok=_normalize_text(signal_snapshot.get("source_feature_batch_id")) == _normalize_text(feature_snapshot.get("batch_id")), expected=_normalize_text(feature_snapshot.get("batch_id")), actual=_normalize_text(signal_snapshot.get("source_feature_batch_id")), details="Signal source feature batch must match the persisted feature batch."),
            _check(layer="decision", category="status", check_id="decision_certified", ok=decision_snapshot.get("status") == "certified" and decision_snapshot.get("readiness") == "backtest_ready", expected="certified/backtest_ready", actual=f"{decision_snapshot.get('status')} / {decision_snapshot.get('readiness')}", details="Decision row population must be certified and backtest_ready."),
            _check(layer="decision", category="certification", check_id="decision_certification_complete", ok=decision_snapshot.get("dataset_certification_status") == "certified" and bool(_normalize_text(decision_snapshot.get("dataset_certification_id"))), expected="certified + certification id", actual=f"{decision_snapshot.get('dataset_certification_status')} / {_normalize_text(decision_snapshot.get('dataset_certification_id'))}", details="Decision row layer must expose complete certification metadata."),
            _check(layer="decision", category="lineage", check_id="decision_source_signal_batch_match", ok=_normalize_text(decision_snapshot.get("source_signal_batch_id")) == _normalize_text(signal_snapshot.get("batch_id")), expected=_normalize_text(signal_snapshot.get("batch_id")), actual=_normalize_text(decision_snapshot.get("source_signal_batch_id")), details="Decision row source signal batch must match the persisted signal batch."),
            _check(layer="decision", category="lineage", check_id="decision_source_signal_summary_match", ok=_normalize_text(decision_snapshot.get("source_signal_population_summary_id")) == _normalize_text(signal_snapshot.get("signal_population_summary_id")), expected=_normalize_text(signal_snapshot.get("signal_population_summary_id")), actual=_normalize_text(decision_snapshot.get("source_signal_population_summary_id")), details="Decision row source signal summary id must match the persisted signal summary id."),
            _check(layer="decision", category="lineage", check_id="decision_source_feature_batch_match", ok=_normalize_text(decision_snapshot.get("source_feature_batch_id")) == _normalize_text(feature_snapshot.get("batch_id")), expected=_normalize_text(feature_snapshot.get("batch_id")), actual=_normalize_text(decision_snapshot.get("source_feature_batch_id")), details="Decision row source feature batch must match the persisted feature batch."),
            _check(layer="backtest", category="status", check_id="backtest_completed", ok=backtest_snapshot.get("status") == "completed" and backtest_snapshot.get("readiness") == "backtest_ready", expected="completed/backtest_ready", actual=f"{backtest_snapshot.get('status')} / {backtest_snapshot.get('readiness')}", details="Baseline backtest must be completed and backtest_ready."),
            _check(layer="backtest", category="lineage", check_id="backtest_decision_batch_match", ok=_normalize_text(backtest_snapshot.get("decision_batch_id")) == _normalize_text(decision_snapshot.get("batch_id")), expected=_normalize_text(decision_snapshot.get("batch_id")), actual=_normalize_text(backtest_snapshot.get("decision_batch_id")), details="Baseline backtest decision batch must match the certified decision batch."),
            _check(layer="backtest", category="lineage", check_id="backtest_decision_summary_match", ok=_normalize_text(backtest_snapshot.get("source_decision_population_summary_id")) == _normalize_text(decision_snapshot.get("decision_population_summary_id")), expected=_normalize_text(decision_snapshot.get("decision_population_summary_id")), actual=_normalize_text(backtest_snapshot.get("source_decision_population_summary_id")), details="Baseline backtest must preserve the persisted decision population summary id."),
            _check(layer="backtest", category="point_in_time", check_id="backtest_point_in_time_safe", ok=_normalize_bool(backtest_snapshot.get("point_in_time_ok")), expected=True, actual=backtest_snapshot.get("point_in_time_ok"), details="Baseline backtest must preserve point-in-time safety."),
            _check(layer="backtest", category="persistence", check_id="backtest_artifacts_exist", ok=_normalize_bool(backtest_snapshot.get("artifact_integrity_ok")), expected=True, actual=backtest_snapshot.get("artifact_integrity_checks"), details="Baseline backtest report and dashboard artifacts must remain on disk."),
            _check(layer="chain", category="row_counts", check_id="dataset_row_counts_align", ok=all(_normalize_int(candidate.get("dataset_row_count")) == _normalize_int(dataset_snapshot.get("dataset_row_count")) for candidate in (feature_snapshot, math_snapshot, signal_snapshot, decision_snapshot)), expected=_normalize_int(dataset_snapshot.get("dataset_row_count")), actual={"dataset": _normalize_int(dataset_snapshot.get("dataset_row_count")), "feature": _normalize_int(feature_snapshot.get("dataset_row_count")), "math": _normalize_int(math_snapshot.get("dataset_row_count")), "signal": _normalize_int(signal_snapshot.get("dataset_row_count")), "decision": _normalize_int(decision_snapshot.get("dataset_row_count"))}, details="Dataset row counts must stay aligned through dataset, feature, math, signal, and decision layers."),
            _check(layer="chain", category="replay", check_id="backtest_sample_matches_eligible_decisions", ok=_normalize_int(backtest_snapshot.get("sample_size")) == _normalize_int(backtest_snapshot.get("backtest_report", {}).get("eligible_decisions")), expected=_normalize_int(backtest_snapshot.get("backtest_report", {}).get("eligible_decisions")), actual=_normalize_int(backtest_snapshot.get("sample_size")), details="Backtest sample size must match the eligible decision count in the persisted report."),
            _check(layer="chain", category="replay", check_id="backtest_has_no_rejected_decisions", ok=_normalize_int(backtest_snapshot.get("backtest_report", {}).get("rejected_decisions")) == 0, expected=0, actual=_normalize_int(backtest_snapshot.get("backtest_report", {}).get("rejected_decisions")), details="Baseline backtest validation expects no rejected decisions for the certified NFL fixture chain."),
            _check(layer="chain", category="dashboard", check_id="backtest_dashboard_summary_consistent", ok=abs(_normalize_float(backtest_snapshot.get("roi_percent")) - _normalize_float(backtest_snapshot.get("backtest_report", {}).get("roi_percent"))) < 1e-9, expected=_normalize_float(backtest_snapshot.get("backtest_report", {}).get("roi_percent")), actual=_normalize_float(backtest_snapshot.get("roi_percent")), details="Backtest dashboard ROI must match the persisted backtest report ROI."),
            _check(layer="backtest", category="benchmark", check_id="backtest_low_sample_warning_present", ok="low_sample_size" in list(backtest_snapshot.get("validation", {}).get("warnings", [])), expected=True, actual="low_sample_size" in list(backtest_snapshot.get("validation", {}).get("warnings", [])), details="The deterministic NFL fixture slice should preserve the explicit low-sample-size warning.", severity="warning"),
        ]

        unresolved_blockers = [f"{check['layer']}:{check['check_id']}" for check in checks if not check["ok"] and check["severity"] == "error"]
        warnings = sorted(
            {
                str(item)
                for source in (
                    dataset_snapshot.get("warnings", []),
                    feature_snapshot.get("warnings", []),
                    math_snapshot.get("warnings", []),
                    signal_snapshot.get("warnings", []),
                    decision_snapshot.get("warnings", []),
                    backtest_snapshot.get("warnings", []),
                )
                for item in source
                if str(item)
            }
        )
        error_checks = [check for check in checks if check["severity"] == "error"]
        warning_checks = [check for check in checks if check["severity"] == "warning"]
        snapshot: dict[str, Any] = {
            "ok": not unresolved_blockers,
            "status": "certified" if not unresolved_blockers else "blocked",
            "readiness": "research_intelligence_ready" if not unresolved_blockers else "blocked",
            "lifecycle_state": "validation_complete" if not unresolved_blockers else "blocked",
            "schema_version": PIPELINE_VALIDATION_SCHEMA_VERSION,
            "dataset_id": DEFAULT_PIPELINE_VALIDATION_DATASET_ID,
            "dataset_name": DEFAULT_PIPELINE_VALIDATION_DATASET_NAME,
            "pipeline_validation_run_id": pipeline_validation_run_id,
            "pipeline_validation_version": PIPELINE_VALIDATION_RUNTIME_VERSION,
            "validation_timestamp": validation_timestamp,
            "validation_summary": {
                "error_check_count": len(error_checks),
                "error_checks_passed": sum(1 for check in error_checks if check["ok"]),
                "warning_check_count": len(warning_checks),
                "warning_checks_passed": sum(1 for check in warning_checks if check["ok"]),
            },
            "validation_checks": checks,
            "lineage_summary": {
                "dataset_batch_id": _normalize_text(dataset_snapshot.get("batch_id")),
                "feature_batch_id": _normalize_text(feature_snapshot.get("batch_id")),
                "math_batch_id": _normalize_text(math_snapshot.get("batch_id")),
                "signal_batch_id": _normalize_text(signal_snapshot.get("batch_id")),
                "decision_batch_id": _normalize_text(decision_snapshot.get("batch_id")),
                "backtest_run_id": _normalize_text(backtest_snapshot.get("backtest_run_id")),
                "feature_source_dataset_batch_id": _normalize_text(feature_snapshot.get("source_dataset_batch_id")),
                "math_source_feature_batch_id": _normalize_text(math_snapshot.get("source_feature_batch_id")),
                "signal_source_math_batch_id": _normalize_text(signal_snapshot.get("source_math_batch_id")),
                "decision_source_signal_batch_id": _normalize_text(decision_snapshot.get("source_signal_batch_id")),
            },
            "certification_summary": {
                "dataset_certification_id": _normalize_text(dataset_snapshot.get("dataset_certification_id")),
                "feature_dataset_certification_id": _normalize_text(feature_snapshot.get("dataset_certification_id")),
                "math_dataset_certification_id": _normalize_text(math_snapshot.get("dataset_certification_id")),
                "signal_dataset_certification_id": _normalize_text(signal_snapshot.get("dataset_certification_id")),
                "decision_dataset_certification_id": _normalize_text(decision_snapshot.get("dataset_certification_id")),
                "backtest_source_decision_dataset_certification_id": _normalize_text(backtest_snapshot.get("dataset_certification_id")),
            },
            "performance_summary": {
                "sample_size": _normalize_int(backtest_snapshot.get("sample_size")),
                "wins": _normalize_int(backtest_snapshot.get("wins")),
                "losses": _normalize_int(backtest_snapshot.get("losses")),
                "pushes": _normalize_int(backtest_snapshot.get("pushes")),
                "profit_loss_units": _normalize_float(backtest_snapshot.get("profit_loss_units")),
                "roi_percent": _normalize_float(backtest_snapshot.get("roi_percent")),
                "benchmark_no_trade_roi_percent": _normalize_float(backtest_snapshot.get("benchmark_comparison", {}).get("no_trade", {}).get("roi_percent")),
                "benchmark_market_implied_sample_size": _normalize_int(backtest_snapshot.get("benchmark_comparison", {}).get("market_implied", {}).get("sample_size")),
            },
            "artifact_references": {},
            "artifact_integrity_ok": False,
            "source_backtest_artifact_references": dict(backtest_snapshot.get("artifact_references") or {}),
            "source_backtest_artifact_integrity": dict(backtest_snapshot.get("artifact_integrity_checks") or {}),
            "storage": storage.health(),
            "warnings": warnings,
            "unresolved_blockers": unresolved_blockers,
            "idempotent_reuse": True,
            "layer_snapshots": {},
        }
        if include_layer_snapshots:
            snapshot["layer_snapshots"] = {
                "dataset": dataset_snapshot,
                "feature": feature_snapshot,
                "math": math_snapshot,
                "signal": signal_snapshot,
                "decision": decision_snapshot,
                "backtest": backtest_snapshot,
            }
        if persist_artifacts:
            artifact_references = _write_artifacts(
                artifact_root=_resolve_artifact_root(storage.path, artifact_root),
                pipeline_validation_run_id=pipeline_validation_run_id,
                snapshot=snapshot,
            )
            snapshot["artifact_references"] = artifact_references
            snapshot["artifact_integrity_ok"] = all(_path_exists(path) for key, path in artifact_references.items() if key != "artifact_root")
        _PIPELINE_VALIDATION_SNAPSHOT_CACHE[cache_key] = copy.deepcopy(snapshot)
        return snapshot
    finally:
        storage.close()


def get_pipeline_validation_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> dict[str, Any]:
    try:
        return build_pipeline_validation_snapshot(
            storage_path=storage_path,
            backend=backend,
            include_layer_snapshots=True,
            persist_artifacts=True,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "pipeline_validation_snapshot_error",
            "readiness": "blocked",
            "lifecycle_state": "missing",
            "schema_version": PIPELINE_VALIDATION_SCHEMA_VERSION,
            "dataset_id": DEFAULT_PIPELINE_VALIDATION_DATASET_ID,
            "dataset_name": DEFAULT_PIPELINE_VALIDATION_DATASET_NAME,
            "pipeline_validation_run_id": "",
            "pipeline_validation_version": PIPELINE_VALIDATION_RUNTIME_VERSION,
            "validation_timestamp": "",
            "validation_summary": {},
            "validation_checks": [],
            "lineage_summary": {},
            "certification_summary": {},
            "performance_summary": {},
            "artifact_references": {},
            "artifact_integrity_ok": False,
            "source_backtest_artifact_references": {},
            "source_backtest_artifact_integrity": {},
            "storage": {},
            "warnings": [str(exc)],
            "unresolved_blockers": [str(exc)],
            "idempotent_reuse": False,
            "layer_snapshots": {},
        }


__all__ = [
    "DEFAULT_PIPELINE_VALIDATION_DATASET_ID",
    "DEFAULT_PIPELINE_VALIDATION_DATASET_NAME",
    "DEFAULT_PIPELINE_VALIDATION_STORAGE_PATH",
    "PIPELINE_VALIDATION_RUNTIME_VERSION",
    "PIPELINE_VALIDATION_SCHEMA_VERSION",
    "build_pipeline_validation_snapshot",
    "get_pipeline_validation_snapshot_for_dashboard",
]
