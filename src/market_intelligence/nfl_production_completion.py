from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from src.market_intelligence.research_intelligence import DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH
from src.storage.local_store import create_local_storage_engine


NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION = "nfl_production_completion.v1"
NFL_PRODUCTION_COMPLETION_RUNTIME_VERSION = "phase-nfl-production-completion.v1"
DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_ID = "dataset.sports.nfl.production_completion"
DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_NAME = "nfl_production_completion"
DEFAULT_NFL_PRODUCTION_COMPLETION_OWNER = "src.market_intelligence"
DEFAULT_NFL_PRODUCTION_COMPLETION_STORAGE_PATH = DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH
DEFAULT_NFL_PRODUCTION_COMPLETION_ARTIFACT_ROOT = Path(
    "data/backtests/nfl_production_completion_artifacts"
)
NFL_PRODUCTION_COMPLETION_RUN_TABLE = "nfl_production_completion_runs"
NFL_PRODUCTION_COMPLETION_AUDIT_TABLE = "nfl_production_completion_audit_items"
NFL_PRODUCTION_COMPLETION_REFERENCE_PROFILE_ID = "sports:nfl"
NFL_PRODUCTION_COMPLETION_NEXT_PHASE = "Covariance and Time-Dependent Risk Capability Audit"
_NFL_PRODUCTION_COMPLETION_SNAPSHOT_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}

COMPLETE_AND_VALIDATED = "complete_and_validated"
COMPLETE_BUT_UNVALIDATED = "complete_but_unvalidated"
PARTIAL = "partial"
MISSING = "missing"
DEFERRED_NON_BLOCKING = "deferred_non_blocking"

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_REQUIRED_DOCUMENTS: tuple[Path, ...] = (
    _REPOSITORY_ROOT / "docs" / "architecture" / "NFL_PRODUCTION_COMPLETION.md",
    _REPOSITORY_ROOT / "docs" / "architecture" / "NFL_P0_DATA_FOUNDATION.md",
    _REPOSITORY_ROOT / "docs" / "reports" / "PHASE5_8_NFL_PRODUCTION_COMPLETION.md",
    _REPOSITORY_ROOT / "docs" / "PROJECT_STATUS.md",
    _REPOSITORY_ROOT / "docs" / "NEXT_ACTION.md",
    _REPOSITORY_ROOT / "docs" / "MASTER_DOCUMENT_INDEX.md",
    _REPOSITORY_ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md",
)


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


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _normalize_text(value).lower()
    return text in {"1", "true", "yes", "y", "ok", "ready", "certified", "completed", "validated"}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}.{digest}"


def _as_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _path_exists(path: Any) -> bool:
    try:
        return Path(str(path)).exists()
    except (OSError, TypeError, ValueError):
        return False


def _safe_call(name: str, builder: Callable[[], Mapping[str, Any]]) -> dict[str, Any]:
    try:
        return dict(builder())
    except Exception as exc:
        return {
            "ok": False,
            "status": f"{name}_snapshot_error",
            "warnings": [str(exc)],
        }


def _classify(ok: bool, *, validated: bool = True, missing: bool = False) -> str:
    if ok and validated:
        return COMPLETE_AND_VALIDATED
    if ok:
        return COMPLETE_BUT_UNVALIDATED
    return MISSING if missing else PARTIAL


def _validation_state(classification: str) -> str:
    if classification == COMPLETE_AND_VALIDATED:
        return "validated"
    if classification == COMPLETE_BUT_UNVALIDATED:
        return "unvalidated"
    if classification == DEFERRED_NON_BLOCKING:
        return "deferred"
    if classification == MISSING:
        return "missing"
    return "blocked"


def _audit_result(
    *,
    requirement_id: str,
    requirement_name: str,
    classification: str,
    blocking_if_incomplete: bool,
    canonical_owner: str,
    summary: str,
    details: Mapping[str, Any],
    source_snapshot_ids: list[str] | None = None,
    source_artifact_paths: list[str] | None = None,
    lineage_reference: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "requirement_name": requirement_name,
        "classification": classification,
        "blocking_if_incomplete": bool(blocking_if_incomplete),
        "status": "ready" if classification == COMPLETE_AND_VALIDATED else classification,
        "validation_state": _validation_state(classification),
        "canonical_owner": canonical_owner,
        "summary": summary,
        "details": dict(details),
        "source_snapshot_ids": list(source_snapshot_ids or []),
        "source_artifact_paths": list(source_artifact_paths or []),
        "lineage_reference": dict(lineage_reference or {}),
    }


def _document_summary() -> dict[str, Any]:
    document_status = {str(path.relative_to(_REPOSITORY_ROOT)): path.exists() for path in _REQUIRED_DOCUMENTS}
    project_status_text = (_REPOSITORY_ROOT / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8") if (_REPOSITORY_ROOT / "docs" / "PROJECT_STATUS.md").exists() else ""
    next_action_text = (_REPOSITORY_ROOT / "docs" / "NEXT_ACTION.md").read_text(encoding="utf-8") if (_REPOSITORY_ROOT / "docs" / "NEXT_ACTION.md").exists() else ""
    p0_text = (_REPOSITORY_ROOT / "docs" / "architecture" / "NFL_P0_DATA_FOUNDATION.md").read_text(encoding="utf-8") if (_REPOSITORY_ROOT / "docs" / "architecture" / "NFL_P0_DATA_FOUNDATION.md").exists() else ""
    master_index_text = (_REPOSITORY_ROOT / "docs" / "MASTER_DOCUMENT_INDEX.md").read_text(encoding="utf-8") if (_REPOSITORY_ROOT / "docs" / "MASTER_DOCUMENT_INDEX.md").exists() else ""
    retention_index_text = (_REPOSITORY_ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md").read_text(encoding="utf-8") if (_REPOSITORY_ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md").exists() else ""
    documentation_checks = {
        "project_status_phase_complete": "NFL Production Completion (complete)" in project_status_text,
        "project_status_next_phase": NFL_PRODUCTION_COMPLETION_NEXT_PHASE in project_status_text,
        "project_status_architecture_reference": "docs/architecture/NFL_PRODUCTION_COMPLETION.md" in project_status_text,
        "project_status_report_reference": "docs/reports/PHASE5_8_NFL_PRODUCTION_COMPLETION.md" in project_status_text,
        "next_action_advanced": NFL_PRODUCTION_COMPLETION_NEXT_PHASE in next_action_text,
        "next_action_records_completed_phase": "NFL Production Completion" in next_action_text,
        "p0_rollup_updated": "NFL Production Completion" in p0_text
        and (
            NFL_PRODUCTION_COMPLETION_NEXT_PHASE in p0_text
            or "First Controlled NFL Vendor Ingest" in p0_text
        ),
        "master_index_updated": "docs/architecture/NFL_PRODUCTION_COMPLETION.md" in master_index_text,
        "retention_index_updated": "docs/architecture/NFL_PRODUCTION_COMPLETION.md" in retention_index_text
        and "docs/reports/PHASE5_8_NFL_PRODUCTION_COMPLETION.md" in retention_index_text,
    }
    digest = hashlib.sha256()
    for path in _REQUIRED_DOCUMENTS:
        digest.update(str(path.relative_to(_REPOSITORY_ROOT)).encode("utf-8"))
        if path.exists():
            digest.update(path.read_bytes())
        else:
            digest.update(b"missing")
    return {
        "required_documents": document_status,
        "documentation_checks": documentation_checks,
        "documentation_digest": digest.hexdigest(),
        "all_required_documents_present": all(document_status.values()),
        "all_documentation_checks_passed": all(documentation_checks.values()),
    }


def _query_interfaces() -> list[dict[str, Any]]:
    return [
        {
            "query_id": "list_nfl_production_audit_results",
            "purpose": "List the deterministic NFL production audit classifications and evidence references.",
            "source_surface": "production_audit_results",
        },
        {
            "query_id": "inspect_nfl_production_gap_register",
            "purpose": "Inspect current blocking and warning gaps for the certified NFL production scope.",
            "source_surface": "production_gap_register",
        },
        {
            "query_id": "inspect_nfl_reference_parity",
            "purpose": "Verify NFL reference parity remains unchanged after production-completion hardening.",
            "source_surface": "nfl_reference_parity",
        },
        {
            "query_id": "inspect_nfl_production_reporting_surfaces",
            "purpose": "Inspect persisted artifact paths and dashboard/report/query readiness for certified NFL production.",
            "source_surface": "reporting_surface_summary",
        },
    ]


def _write_artifacts(
    *,
    artifact_root: Path,
    run_id: str,
    snapshot: Mapping[str, Any],
) -> dict[str, str]:
    run_root = artifact_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    report_json_path = run_root / "report.json"
    report_markdown_path = run_root / "summary.md"
    dashboard_json_path = run_root / "dashboard.json"
    report_payload = {
        "nfl_production_completion_run_id": snapshot.get("nfl_production_completion_run_id"),
        "schema_version": snapshot.get("schema_version"),
        "nfl_production_completion_version": snapshot.get("nfl_production_completion_version"),
        "status": snapshot.get("status"),
        "readiness": snapshot.get("readiness"),
        "lifecycle_state": snapshot.get("lifecycle_state"),
        "validation_state": snapshot.get("validation_state"),
        "reference_profile_id": snapshot.get("reference_profile_id"),
        "next_governed_phase": snapshot.get("next_governed_phase"),
        "nfl_reference_parity": snapshot.get("nfl_reference_parity"),
        "production_audit_results": snapshot.get("production_audit_results"),
        "production_gap_register": snapshot.get("production_gap_register"),
        "lineage_summary": snapshot.get("lineage_summary"),
        "certification_summary": snapshot.get("certification_summary"),
        "reporting_surface_summary": snapshot.get("reporting_surface_summary"),
        "validation_summary": snapshot.get("validation_summary"),
        "warnings": snapshot.get("warnings"),
        "unresolved_blockers": snapshot.get("unresolved_blockers"),
    }
    report_json_path.write_text(
        json.dumps(report_payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    dashboard_json_path.write_text(
        json.dumps(snapshot.get("dashboard_views", {}), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# NFL Production Completion",
        "",
        f"- Status: `{snapshot.get('status')}`",
        f"- Readiness: `{snapshot.get('readiness')}`",
        f"- Reference profile: `{snapshot.get('reference_profile_id')}`",
        f"- NFL reference parity preserved: `{snapshot.get('nfl_reference_parity', {}).get('ok')}`",
        f"- Blocking gaps: `{len(snapshot.get('production_gap_register', {}).get('blocking_gaps', []))}`",
        f"- Warning gaps: `{len(snapshot.get('production_gap_register', {}).get('warning_gaps', []))}`",
        f"- Next governed phase: `{snapshot.get('next_governed_phase')}`",
        "",
        "This artifact certifies the NFL production scope without altering the underlying research pipeline.",
    ]
    report_markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "artifact_root": str(run_root),
        "report_json_path": str(report_json_path),
        "report_markdown_path": str(report_markdown_path),
        "dashboard_json_path": str(dashboard_json_path),
    }


def _snapshot_cache_key(
    storage_path: str | Path | None,
    *,
    backend: str,
    artifact_root: str | Path | None,
    include_layer_snapshots: bool,
    persist_artifacts: bool,
) -> tuple[Any, ...]:
    resolved = Path(storage_path or DEFAULT_NFL_PRODUCTION_COMPLETION_STORAGE_PATH).expanduser().resolve()
    stat = resolved.stat() if resolved.exists() else None
    resolved_artifact_root = Path(artifact_root or DEFAULT_NFL_PRODUCTION_COMPLETION_ARTIFACT_ROOT).expanduser().resolve()
    return (
        str(resolved),
        getattr(stat, "st_mtime_ns", 0),
        getattr(stat, "st_size", 0),
        backend,
        str(resolved_artifact_root),
        include_layer_snapshots,
        persist_artifacts,
    )


def _missing_snapshot(
    *,
    storage_path: str,
    status: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "readiness": "blocked",
        "lifecycle_state": "missing",
        "validation_state": "missing",
        "schema_version": NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION,
        "dataset_id": DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_ID,
        "dataset_name": DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_NAME,
        "nfl_production_completion_run_id": "",
        "nfl_production_completion_version": NFL_PRODUCTION_COMPLETION_RUNTIME_VERSION,
        "generated_at": "",
        "reference_profile_id": NFL_PRODUCTION_COMPLETION_REFERENCE_PROFILE_ID,
        "next_governed_phase": NFL_PRODUCTION_COMPLETION_NEXT_PHASE,
        "nfl_reference_parity": {},
        "production_audit_results": [],
        "production_gap_register": {
            "blocking_gaps": [status],
            "warning_gaps": [],
        },
        "dashboard_views": {},
        "query_interfaces": _query_interfaces(),
        "validation_checks": [],
        "validation_summary": {},
        "lineage_summary": {},
        "certification_summary": {},
        "reporting_surface_summary": {},
        "artifact_references": {},
        "artifact_integrity_ok": False,
        "storage": {
            "database_path": storage_path,
        },
        "warnings": warnings,
        "unresolved_blockers": list(warnings or [status]),
        "layer_snapshots": {},
    }


def build_nfl_production_completion_snapshot(
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
    cached_snapshot = _NFL_PRODUCTION_COMPLETION_SNAPSHOT_CACHE.get(cache_key)
    if cached_snapshot is not None:
        return copy.deepcopy(cached_snapshot)

    from src.backtesting.baseline_backtesting import build_baseline_backtest_dashboard_snapshot
    from src.backtesting.decision_row_population import build_decision_row_population_dashboard_snapshot
    from src.backtesting.pipeline_validation import build_pipeline_validation_snapshot
    from src.data.feature_registry import build_feature_snapshot_population_dashboard_snapshot
    from src.data.historical_research_database import build_historical_dataset_population_dashboard_snapshot
    from src.data.math_engine_population import build_math_engine_population_dashboard_snapshot
    from src.data.nfl_injuries_research_asset_population import build_nfl_injuries_research_asset_dashboard_snapshot
    from src.data.nfl_odds_research_asset_population import build_nfl_odds_research_asset_dashboard_snapshot
    from src.data.nfl_results_research_asset_population import build_nfl_results_research_asset_dashboard_snapshot
    from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_dashboard_snapshot
    from src.data.nfl_team_statistics_research_asset_population import build_nfl_team_statistics_research_asset_dashboard_snapshot
    from src.data.nfl_weather_research_asset_population import build_nfl_weather_research_asset_dashboard_snapshot
    from src.market_intelligence.research_intelligence import build_research_intelligence_snapshot
    from src.market_intelligence.signal_population import get_signal_population_snapshot_for_dashboard
    from src.market_intelligence.universal_market_framework import build_universal_market_framework_snapshot

    storage = create_local_storage_engine(
        storage_path or DEFAULT_NFL_PRODUCTION_COMPLETION_STORAGE_PATH,
        backend=backend,
    )
    try:
        pipeline_validation_snapshot = _safe_call(
            "pipeline_validation",
            lambda: build_pipeline_validation_snapshot(
                storage_path=storage.path,
                backend=backend,
                include_layer_snapshots=True,
                persist_artifacts=True,
            ),
        )
        pipeline_layer_snapshots = dict(pipeline_validation_snapshot.get("layer_snapshots") or {})

        def _layer_or_fallback(
            layer_key: str,
            fallback_name: str,
            builder,
        ) -> dict[str, Any]:
            layer_snapshot = pipeline_layer_snapshots.get(layer_key)
            if isinstance(layer_snapshot, Mapping) and layer_snapshot:
                return dict(layer_snapshot)
            return _safe_call(fallback_name, builder)

        dataset_snapshot = _layer_or_fallback(
            "dataset",
            "historical_dataset_population",
            lambda: build_historical_dataset_population_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
                profile_id=NFL_PRODUCTION_COMPLETION_REFERENCE_PROFILE_ID,
            ),
        )
        feature_snapshot = _layer_or_fallback(
            "feature",
            "feature_snapshot_population",
            lambda: build_feature_snapshot_population_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
                dataset_id="dataset.sports.nfl.historical_dataset",
            ),
        )
        math_snapshot = _layer_or_fallback(
            "math",
            "math_engine_population",
            lambda: build_math_engine_population_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
            ),
        )
        signal_snapshot = _layer_or_fallback(
            "signal",
            "signal_population",
            lambda: get_signal_population_snapshot_for_dashboard(
                storage_path=storage.path,
                backend=backend,
            ),
        )
        decision_snapshot = _layer_or_fallback(
            "decision",
            "decision_row_population",
            lambda: build_decision_row_population_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
            ),
        )
        backtest_snapshot = _layer_or_fallback(
            "backtest",
            "baseline_backtesting",
            lambda: build_baseline_backtest_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
            ),
        )
        research_intelligence_snapshot = _safe_call(
            "research_intelligence",
            lambda: build_research_intelligence_snapshot(
                storage_path=storage.path,
                backend=backend,
                include_layer_snapshots=False,
                persist_artifacts=persist_artifacts,
            ),
        )
        universal_market_framework_snapshot = _safe_call(
            "universal_market_framework",
            lambda: build_universal_market_framework_snapshot(
                storage_path=storage.path,
                backend=backend,
                persist_artifacts=persist_artifacts,
                research_snapshot=research_intelligence_snapshot,
            ),
        )
        asset_snapshots = {
            "schedule": _safe_call(
                "nfl_schedule_research_asset",
                lambda: build_nfl_schedule_research_asset_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                ),
            ),
            "results": _safe_call(
                "nfl_results_research_asset",
                lambda: build_nfl_results_research_asset_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                ),
            ),
            "odds": _safe_call(
                "nfl_odds_research_asset",
                lambda: build_nfl_odds_research_asset_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                ),
            ),
            "weather": _safe_call(
                "nfl_weather_research_asset",
                lambda: build_nfl_weather_research_asset_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                ),
            ),
            "injuries": _safe_call(
                "nfl_injuries_research_asset",
                lambda: build_nfl_injuries_research_asset_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                ),
            ),
            "team_statistics": _safe_call(
                "nfl_team_statistics_research_asset",
                lambda: build_nfl_team_statistics_research_asset_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                ),
            ),
        }
        document_summary = _document_summary()
        reference_parity = dict(universal_market_framework_snapshot.get("nfl_reference_parity") or {})
        lineage_summary = {
            "dataset_batch_id": _normalize_text(dataset_snapshot.get("batch_id")),
            "feature_batch_id": _normalize_text(feature_snapshot.get("batch_id")),
            "math_batch_id": _normalize_text(math_snapshot.get("batch_id")),
            "signal_batch_id": _normalize_text(signal_snapshot.get("batch_id")),
            "decision_batch_id": _normalize_text(decision_snapshot.get("batch_id")),
            "backtest_run_id": _normalize_text(backtest_snapshot.get("backtest_run_id")),
            "pipeline_validation_run_id": _normalize_text(pipeline_validation_snapshot.get("pipeline_validation_run_id")),
            "research_intelligence_run_id": _normalize_text(research_intelligence_snapshot.get("research_intelligence_run_id")),
            "universal_market_framework_run_id": _normalize_text(
                universal_market_framework_snapshot.get("universal_market_framework_run_id")
            ),
        }
        certification_summary = {
            "dataset_certification_id": _normalize_text(dataset_snapshot.get("dataset_certification_id")),
            "feature_dataset_certification_id": _normalize_text(feature_snapshot.get("dataset_certification_id")),
            "math_dataset_certification_id": _normalize_text(math_snapshot.get("dataset_certification_id")),
            "signal_dataset_certification_id": _normalize_text(signal_snapshot.get("dataset_certification_id")),
            "decision_dataset_certification_id": _normalize_text(decision_snapshot.get("dataset_certification_id")),
            "backtest_dataset_certification_id": _normalize_text(backtest_snapshot.get("dataset_certification_id")),
            "pipeline_validation_status": _normalize_text(pipeline_validation_snapshot.get("status")),
            "research_intelligence_status": _normalize_text(research_intelligence_snapshot.get("status")),
            "universal_market_framework_status": _normalize_text(universal_market_framework_snapshot.get("status")),
        }
        run_id = _stable_id(
            "nfl_production_completion",
            NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION,
            lineage_summary,
            certification_summary,
            document_summary.get("documentation_digest"),
            reference_parity.get("parity_digest"),
        )

        asset_status_rows = [
            {
                "asset_key": asset_key,
                "asset_id": _normalize_text(snapshot.get("asset_id")),
                "status": _normalize_text(snapshot.get("status")),
                "certification_status": _normalize_text(snapshot.get("certification_status")),
                "dataset_certification_status": _normalize_text(snapshot.get("dataset_certification_status")),
                "readiness_percentage": _normalize_float(snapshot.get("readiness_percentage")),
                "ok": _normalize_bool(snapshot.get("ok")),
            }
            for asset_key, snapshot in asset_snapshots.items()
        ]
        certified_research_assets_ok = all(
            row["ok"]
            and row["certification_status"] == "certified"
            and row["dataset_certification_status"] == "certified"
            and row["readiness_percentage"] >= 100.0
            for row in asset_status_rows
        )
        certified_research_assets_missing = not any(row["ok"] for row in asset_status_rows)
        dataset_ok = (
            _normalize_bool(dataset_snapshot.get("ok"))
            and _normalize_text(dataset_snapshot.get("status")) == "ready"
            and _normalize_text(dataset_snapshot.get("dataset_certification_status")) == "certified"
            and _normalize_int(dataset_snapshot.get("dataset_row_count")) > 0
        )
        feature_ok = (
            _normalize_bool(feature_snapshot.get("ok"))
            and _normalize_text(feature_snapshot.get("status")) == "ready"
            and _normalize_text(feature_snapshot.get("readiness")) == "feature_ready"
            and _normalize_text(feature_snapshot.get("validation_state")) == "validated"
            and _normalize_text(feature_snapshot.get("dataset_certification_status")) == "certified"
            and _normalize_int(feature_snapshot.get("feature_snapshot_count")) > 0
        )
        math_ok = (
            _normalize_bool(math_snapshot.get("ok"))
            and _normalize_text(math_snapshot.get("status")) == "ready"
            and _normalize_text(math_snapshot.get("readiness")) == "math_ready"
            and _normalize_text(math_snapshot.get("validation_state")) == "validated"
            and _normalize_text(math_snapshot.get("dataset_certification_status")) == "certified"
            and _normalize_int(math_snapshot.get("engine_row_count")) > 0
        )
        signal_ok = (
            _normalize_bool(signal_snapshot.get("ok"))
            and _normalize_text(signal_snapshot.get("status")) == "certified"
            and _normalize_text(signal_snapshot.get("readiness")) == "signal_ready"
            and _normalize_text(signal_snapshot.get("validation_state")) == "validated"
            and _normalize_text(signal_snapshot.get("dataset_certification_status")) == "certified"
            and _normalize_int(signal_snapshot.get("signal_row_count")) > 0
        )
        decision_ok = (
            _normalize_bool(decision_snapshot.get("ok"))
            and _normalize_text(decision_snapshot.get("status")) == "certified"
            and _normalize_text(decision_snapshot.get("readiness")) == "backtest_ready"
            and _normalize_text(decision_snapshot.get("dataset_certification_status")) == "certified"
            and _normalize_int(decision_snapshot.get("decision_row_count")) > 0
        )
        backtest_validation_summary = dict(backtest_snapshot.get("benchmark_comparison") or {})
        backtest_ok = (
            _normalize_bool(backtest_snapshot.get("ok"))
            and _normalize_text(backtest_snapshot.get("status")) == "completed"
            and _normalize_text(backtest_snapshot.get("readiness")) == "backtest_ready"
            and _normalize_text(backtest_snapshot.get("validation_state")) == "validated"
            and _normalize_text(backtest_snapshot.get("dataset_certification_status")) == "certified"
            and _normalize_bool(backtest_snapshot.get("artifact_integrity_ok"))
            and _normalize_bool(backtest_snapshot.get("point_in_time_ok"))
            and _normalize_int(backtest_snapshot.get("sample_size")) > 0
        )
        pipeline_validation_ok = (
            _normalize_bool(pipeline_validation_snapshot.get("ok"))
            and _normalize_text(pipeline_validation_snapshot.get("status")) == "certified"
            and _normalize_text(pipeline_validation_snapshot.get("readiness")) == "research_intelligence_ready"
            and _normalize_bool(pipeline_validation_snapshot.get("artifact_integrity_ok"))
            and _normalize_int(
                dict(pipeline_validation_snapshot.get("validation_summary") or {}).get("error_check_count")
            )
            == _normalize_int(
                dict(pipeline_validation_snapshot.get("validation_summary") or {}).get("error_checks_passed")
            )
        )
        research_summary = dict(research_intelligence_snapshot.get("research_summary") or {})
        evidence_packages = list(research_intelligence_snapshot.get("supporting_evidence_packages") or [])
        research_intelligence_ok = (
            _normalize_bool(research_intelligence_snapshot.get("ok"))
            and _normalize_text(research_intelligence_snapshot.get("status")) == "completed"
            and _normalize_text(research_intelligence_snapshot.get("readiness")) == "universal_market_framework_ready"
            and _normalize_text(research_intelligence_snapshot.get("validation_state")) == "validated"
            and _normalize_bool(research_intelligence_snapshot.get("artifact_integrity_ok"))
            and _normalize_int(research_summary.get("sample_size")) > 0
            and len(evidence_packages) > 0
        )
        parity_ok = (
            _normalize_bool(reference_parity.get("ok"))
            and _normalize_text(reference_parity.get("research_intelligence_run_id"))
            == _normalize_text(research_intelligence_snapshot.get("research_intelligence_run_id"))
            and _normalize_text(reference_parity.get("pipeline_validation_run_id"))
            == _normalize_text(pipeline_validation_snapshot.get("pipeline_validation_run_id"))
            and _normalize_text(reference_parity.get("backtest_run_id"))
            == _normalize_text(backtest_snapshot.get("backtest_run_id"))
            and _normalize_text(reference_parity.get("decision_batch_id"))
            == _normalize_text(decision_snapshot.get("batch_id"))
        )
        evidence_package_ids = [
            _normalize_text(package.get("evidence_package_id"))
            for package in evidence_packages
            if _normalize_text(package.get("evidence_package_id"))
        ]
        evidence_packages_ok = (
            len(evidence_package_ids) == len(evidence_packages)
            and len(evidence_package_ids) > 0
            and bool(_normalize_text(feature_snapshot.get("feature_evidence_package_id")))
            and bool(_normalize_text(math_snapshot.get("math_engine_evidence_package_id")))
            and bool(_normalize_text(signal_snapshot.get("signal_evidence_package_id")))
            and bool(_normalize_text(decision_snapshot.get("decision_evidence_package_id")))
            and _normalize_bool(backtest_snapshot.get("artifact_integrity_ok"))
        )
        documentation_ok = (
            _normalize_bool(document_summary.get("all_required_documents_present"))
            and _normalize_bool(document_summary.get("all_documentation_checks_passed"))
        )
        current_artifact_references: dict[str, str] = {}
        current_artifact_integrity_ok = False
        query_interfaces = _query_interfaces()
        query_surfaces_ok = (
            storage.table_exists(NFL_PRODUCTION_COMPLETION_RUN_TABLE)
            and storage.table_exists(NFL_PRODUCTION_COMPLETION_AUDIT_TABLE)
            and len(query_interfaces) >= 3
        )

        audit_results = [
            _audit_result(
                requirement_id="certified_research_assets",
                requirement_name="Certified research assets",
                classification=_classify(
                    certified_research_assets_ok,
                    missing=certified_research_assets_missing,
                ),
                blocking_if_incomplete=True,
                canonical_owner="src.data",
                summary="All six certified NFL research assets are present, certified, and dataset-certified.",
                details={
                    "asset_count": len(asset_status_rows),
                    "certified_asset_count": sum(1 for row in asset_status_rows if row["certification_status"] == "certified"),
                    "assets": asset_status_rows,
                },
                source_snapshot_ids=[row["asset_id"] for row in asset_status_rows if row["asset_id"]],
            ),
            _audit_result(
                requirement_id="historical_data_coverage",
                requirement_name="Historical data coverage",
                classification=_classify(dataset_ok, missing=_normalize_int(dataset_snapshot.get("dataset_row_count")) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.data.historical_research_database",
                summary="The certified historical dataset is point-in-time safe, lineage-complete, and queryable for NFL scope.",
                details={
                    "status": dataset_snapshot.get("status"),
                    "dataset_row_count": dataset_snapshot.get("dataset_row_count"),
                    "dataset_certification_status": dataset_snapshot.get("dataset_certification_status"),
                    "lineage_completeness": dataset_snapshot.get("lineage_completeness"),
                    "provenance_completeness": dataset_snapshot.get("provenance_completeness"),
                },
                source_snapshot_ids=[_normalize_text(dataset_snapshot.get("dataset_id")), _normalize_text(dataset_snapshot.get("batch_id"))],
                lineage_reference={"dataset_batch_id": lineage_summary["dataset_batch_id"]},
            ),
            _audit_result(
                requirement_id="feature_coverage",
                requirement_name="Deterministic feature coverage",
                classification=_classify(feature_ok, missing=_normalize_int(feature_snapshot.get("feature_snapshot_count")) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.data.feature_registry",
                summary="Certified feature snapshots cover the deterministic NFL research scope with lineage and evidence references.",
                details={
                    "status": feature_snapshot.get("status"),
                    "feature_snapshot_count": feature_snapshot.get("feature_snapshot_count"),
                    "feature_definition_count": feature_snapshot.get("feature_definition_count"),
                    "dataset_certification_status": feature_snapshot.get("dataset_certification_status"),
                    "validation_state": feature_snapshot.get("validation_state"),
                },
                source_snapshot_ids=[_normalize_text(feature_snapshot.get("dataset_id")), _normalize_text(feature_snapshot.get("batch_id"))],
                lineage_reference={"feature_batch_id": lineage_summary["feature_batch_id"]},
            ),
            _audit_result(
                requirement_id="mathematical_outputs",
                requirement_name="Mathematical outputs",
                classification=_classify(math_ok, missing=_normalize_int(math_snapshot.get("engine_row_count")) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.data.math_engine_population",
                summary="Certified math engine outputs remain deterministic, point-in-time safe, and lineage-complete.",
                details={
                    "status": math_snapshot.get("status"),
                    "engine_row_count": math_snapshot.get("engine_row_count"),
                    "engine_definition_count": math_snapshot.get("engine_definition_count"),
                    "dataset_certification_status": math_snapshot.get("dataset_certification_status"),
                    "validation_state": math_snapshot.get("validation_state"),
                },
                source_snapshot_ids=[_normalize_text(math_snapshot.get("dataset_id")), _normalize_text(math_snapshot.get("batch_id"))],
                lineage_reference={"math_batch_id": lineage_summary["math_batch_id"]},
            ),
            _audit_result(
                requirement_id="signals",
                requirement_name="Signals",
                classification=_classify(signal_ok, missing=_normalize_int(signal_snapshot.get("signal_row_count")) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.signal_population",
                summary="Certified signal rows preserve deterministic behavior, lineage, and dataset certification.",
                details={
                    "status": signal_snapshot.get("status"),
                    "signal_row_count": signal_snapshot.get("signal_row_count"),
                    "signal_definition_count": signal_snapshot.get("signal_definition_count"),
                    "dataset_certification_status": signal_snapshot.get("dataset_certification_status"),
                    "validation_state": signal_snapshot.get("validation_state"),
                },
                source_snapshot_ids=[_normalize_text(signal_snapshot.get("dataset_id")), _normalize_text(signal_snapshot.get("batch_id"))],
                lineage_reference={"signal_batch_id": lineage_summary["signal_batch_id"]},
            ),
            _audit_result(
                requirement_id="decision_rows",
                requirement_name="Decision rows",
                classification=_classify(decision_ok, missing=_normalize_int(decision_snapshot.get("decision_row_count")) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.backtesting.decision_row_population",
                summary="Certified immutable decision rows remain the sole evidence input for replay and downstream analysis.",
                details={
                    "status": decision_snapshot.get("status"),
                    "decision_row_count": decision_snapshot.get("decision_row_count"),
                    "decision_definition_count": decision_snapshot.get("decision_definition_count"),
                    "dataset_certification_status": decision_snapshot.get("dataset_certification_status"),
                },
                source_snapshot_ids=[_normalize_text(decision_snapshot.get("dataset_id")), _normalize_text(decision_snapshot.get("batch_id"))],
                lineage_reference={"decision_batch_id": lineage_summary["decision_batch_id"]},
            ),
            _audit_result(
                requirement_id="baseline_backtesting",
                requirement_name="Baseline backtesting",
                classification=_classify(backtest_ok, missing=_normalize_int(backtest_snapshot.get("sample_size")) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.backtesting.baseline_backtesting",
                summary="Deterministic baseline backtesting remains replay-safe, benchmarked, and artifact-backed for NFL scope.",
                details={
                    "status": backtest_snapshot.get("status"),
                    "sample_size": backtest_snapshot.get("sample_size"),
                    "wins": backtest_snapshot.get("wins"),
                    "losses": backtest_snapshot.get("losses"),
                    "pushes": backtest_snapshot.get("pushes"),
                    "roi_percent": backtest_snapshot.get("roi_percent"),
                    "point_in_time_ok": backtest_snapshot.get("point_in_time_ok"),
                    "benchmark_comparison": backtest_validation_summary,
                },
                source_snapshot_ids=[_normalize_text(backtest_snapshot.get("backtest_run_id"))],
                source_artifact_paths=[
                    str(path)
                    for key, path in dict(backtest_snapshot.get("artifact_references") or {}).items()
                    if key != "artifact_root"
                ],
                lineage_reference={"backtest_run_id": lineage_summary["backtest_run_id"]},
            ),
            _audit_result(
                requirement_id="pipeline_validation",
                requirement_name="Pipeline validation",
                classification=_classify(
                    pipeline_validation_ok,
                    missing=not _normalize_text(pipeline_validation_snapshot.get("pipeline_validation_run_id")),
                ),
                blocking_if_incomplete=True,
                canonical_owner="src.backtesting.pipeline_validation",
                summary="The certified NFL pipeline validation gate remains green with artifact integrity and full error-check coverage.",
                details={
                    "status": pipeline_validation_snapshot.get("status"),
                    "readiness": pipeline_validation_snapshot.get("readiness"),
                    "validation_summary": pipeline_validation_snapshot.get("validation_summary"),
                    "artifact_integrity_ok": pipeline_validation_snapshot.get("artifact_integrity_ok"),
                },
                source_snapshot_ids=[_normalize_text(pipeline_validation_snapshot.get("pipeline_validation_run_id"))],
                source_artifact_paths=[
                    str(path)
                    for key, path in dict(pipeline_validation_snapshot.get("artifact_references") or {}).items()
                    if key != "artifact_root"
                ],
                lineage_reference={"pipeline_validation_run_id": lineage_summary["pipeline_validation_run_id"]},
            ),
            _audit_result(
                requirement_id="research_intelligence",
                requirement_name="Research Intelligence",
                classification=_classify(
                    research_intelligence_ok,
                    missing=not _normalize_text(research_intelligence_snapshot.get("research_intelligence_run_id")),
                ),
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.research_intelligence",
                summary="Research Intelligence remains explanatory-only, deterministic, evidence-backed, and downstream of the certified NFL chain.",
                details={
                    "status": research_intelligence_snapshot.get("status"),
                    "readiness": research_intelligence_snapshot.get("readiness"),
                    "validation_summary": research_intelligence_snapshot.get("validation_summary"),
                    "research_summary": research_summary,
                    "evidence_package_count": len(evidence_packages),
                },
                source_snapshot_ids=[_normalize_text(research_intelligence_snapshot.get("research_intelligence_run_id"))],
                source_artifact_paths=[
                    str(path)
                    for key, path in dict(research_intelligence_snapshot.get("artifact_references") or {}).items()
                    if key != "artifact_root"
                ],
                lineage_reference={"research_intelligence_run_id": lineage_summary["research_intelligence_run_id"]},
            ),
            _audit_result(
                requirement_id="nfl_reference_parity",
                requirement_name="NFL reference parity",
                classification=_classify(parity_ok, missing=not bool(reference_parity)),
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.universal_market_framework",
                summary="The generalized framework and production-completion layer do not alter certified NFL reference behavior.",
                details={
                    "parity": reference_parity,
                    "research_intelligence_run_id": research_intelligence_snapshot.get("research_intelligence_run_id"),
                    "pipeline_validation_run_id": pipeline_validation_snapshot.get("pipeline_validation_run_id"),
                    "backtest_run_id": backtest_snapshot.get("backtest_run_id"),
                    "decision_batch_id": decision_snapshot.get("batch_id"),
                },
                source_snapshot_ids=[_normalize_text(universal_market_framework_snapshot.get("universal_market_framework_run_id"))],
                source_artifact_paths=[
                    str(path)
                    for key, path in dict(universal_market_framework_snapshot.get("artifact_references") or {}).items()
                    if key != "artifact_root"
                ],
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="dashboard_surfaces",
                requirement_name="Dashboard surfaces",
                classification=_classify(
                    bool(dict(research_intelligence_snapshot.get("dashboard_views") or {}))
                    and bool(dict(universal_market_framework_snapshot.get("dashboard_views") or {})),
                    missing=False,
                ),
                blocking_if_incomplete=True,
                canonical_owner="src.services.streamlit_dashboard_data",
                summary="Canonical dashboard adapters expose production-audit, parity, reporting, and readiness views without duplicating framework logic.",
                details={
                    "research_dashboard_view_keys": sorted(dict(research_intelligence_snapshot.get("dashboard_views") or {}).keys()),
                    "framework_dashboard_view_keys": sorted(dict(universal_market_framework_snapshot.get("dashboard_views") or {}).keys()),
                },
            ),
            _audit_result(
                requirement_id="query_surfaces",
                requirement_name="Query surfaces",
                classification=_classify(query_surfaces_ok, missing=False),
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.nfl_production_completion",
                summary="The production-completion layer persists deterministic audit rows and exposes query-ready interfaces for downstream consumers.",
                details={
                    "query_interfaces": query_interfaces,
                    "run_table_present": storage.table_exists(NFL_PRODUCTION_COMPLETION_RUN_TABLE),
                    "audit_table_present": storage.table_exists(NFL_PRODUCTION_COMPLETION_AUDIT_TABLE),
                },
            ),
            _audit_result(
                requirement_id="evidence_packages",
                requirement_name="Evidence packages",
                classification=_classify(evidence_packages_ok, missing=len(evidence_packages) == 0),
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.research_intelligence",
                summary="Supporting evidence packages, feature evidence, math evidence, signal evidence, and decision evidence remain complete and queryable.",
                details={
                    "research_evidence_package_count": len(evidence_packages),
                    "research_opportunity_count": len(list(research_intelligence_snapshot.get("opportunity_summaries") or [])),
                    "feature_evidence_package_id": feature_snapshot.get("feature_evidence_package_id"),
                    "math_engine_evidence_package_id": math_snapshot.get("math_engine_evidence_package_id"),
                    "signal_evidence_package_id": signal_snapshot.get("signal_evidence_package_id"),
                    "decision_evidence_package_id": decision_snapshot.get("decision_evidence_package_id"),
                },
                source_snapshot_ids=evidence_package_ids,
            ),
            _audit_result(
                requirement_id="documentation",
                requirement_name="Documentation",
                classification=_classify(documentation_ok, missing=not document_summary.get("all_required_documents_present")),
                blocking_if_incomplete=True,
                canonical_owner="docs",
                summary="Architecture, report, status, sequencing, and retention indexes document NFL production completion and the next governed audit lane.",
                details=document_summary,
            ),
        ]
        warning_gaps: list[dict[str, Any]] = []
        dashboard_views = {
            "summary_cards": [
                {
                    "label": "NFL production status",
                    "value": "pending",
                    "detail": "Awaiting final production audit synthesis",
                },
                {
                    "label": "NFL reference parity",
                    "value": "preserved" if parity_ok else "mismatch",
                    "detail": reference_parity.get("parity_digest", ""),
                },
                {
                    "label": "Blocking gaps",
                    "value": "pending",
                    "detail": "Awaiting final production audit synthesis",
                },
                {
                    "label": "Next governed phase",
                    "value": NFL_PRODUCTION_COMPLETION_NEXT_PHASE,
                    "detail": "Pending",
                },
            ],
            "production_audit_results": audit_results,
            "production_gap_register": {
                "blocking_gaps": [],
                "warning_gaps": warning_gaps,
            },
            "nfl_reference_parity": reference_parity,
            "lineage_reference_summary": lineage_summary,
            "reporting_surface_summary": {
                "upstream_backtest_artifacts_ok": _normalize_bool(backtest_snapshot.get("artifact_integrity_ok")),
                "upstream_pipeline_validation_artifacts_ok": _normalize_bool(
                    pipeline_validation_snapshot.get("artifact_integrity_ok")
                ),
                "upstream_research_intelligence_artifacts_ok": _normalize_bool(
                    research_intelligence_snapshot.get("artifact_integrity_ok")
                ),
                "upstream_universal_market_framework_artifacts_ok": _normalize_bool(
                    universal_market_framework_snapshot.get("artifact_integrity_ok")
                ),
                "current_artifacts_requested": persist_artifacts,
            },
        }
        provisional_blocking_gaps = [
            result
            for result in audit_results
            if result["blocking_if_incomplete"] and result["classification"] != COMPLETE_AND_VALIDATED
        ]
        provisional_validation_checks = [
            {
                "check_id": result["requirement_id"],
                "category": "production_completion",
                "severity": "error" if result["blocking_if_incomplete"] else "warning",
                "ok": result["classification"] == COMPLETE_AND_VALIDATED
                or result["classification"] == DEFERRED_NON_BLOCKING,
                "expected": COMPLETE_AND_VALIDATED,
                "actual": result["classification"],
            }
            for result in audit_results
        ]
        provisional_error_checks = [check for check in provisional_validation_checks if check["severity"] == "error"]
        provisional_warning_checks = [check for check in provisional_validation_checks if check["severity"] == "warning"]
        provisional_ok = all(check["ok"] for check in provisional_error_checks)
        current_artifact_references: dict[str, str] = {}
        current_artifact_integrity_ok = False
        reporting_artifact_paths: list[str] = []
        reporting_surfaces_ok = (
            _normalize_bool(backtest_snapshot.get("artifact_integrity_ok"))
            and _normalize_bool(pipeline_validation_snapshot.get("artifact_integrity_ok"))
            and _normalize_bool(research_intelligence_snapshot.get("artifact_integrity_ok"))
            and _normalize_bool(universal_market_framework_snapshot.get("artifact_integrity_ok"))
            and persist_artifacts
        )
        reporting_classification = (
            DEFERRED_NON_BLOCKING
            if not persist_artifacts
            else _classify(
                reporting_surfaces_ok,
                validated=True,
                missing=False,
            )
        )
        audit_results.insert(
            11,
            _audit_result(
                requirement_id="reporting_surfaces",
                requirement_name="Reporting surfaces",
                classification=reporting_classification,
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.nfl_production_completion",
                summary="Persisted report, dashboard, and summary artifacts exist for backtesting, validation, research, framework parity, and NFL production completion.",
                details={
                    "current_artifact_integrity_ok": current_artifact_integrity_ok,
                    "upstream_backtest_artifacts_ok": backtest_snapshot.get("artifact_integrity_ok"),
                    "upstream_pipeline_validation_artifacts_ok": pipeline_validation_snapshot.get("artifact_integrity_ok"),
                    "upstream_research_intelligence_artifacts_ok": research_intelligence_snapshot.get("artifact_integrity_ok"),
                    "upstream_universal_market_framework_artifacts_ok": universal_market_framework_snapshot.get("artifact_integrity_ok"),
                    "persist_artifacts": persist_artifacts,
                },
                source_artifact_paths=reporting_artifact_paths,
            ),
        )
        blocking_gaps = [
            result
            for result in audit_results
            if result["blocking_if_incomplete"] and result["classification"] != COMPLETE_AND_VALIDATED
        ]
        production_readiness_classification = _classify(not blocking_gaps, missing=False)
        audit_results.append(
            _audit_result(
                requirement_id="production_readiness_blockers",
                requirement_name="Production-readiness blockers",
                classification=production_readiness_classification,
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.nfl_production_completion",
                summary=(
                    "No blocking NFL production gaps remain inside the certified NFL scope."
                    if not blocking_gaps
                    else "Blocking NFL production gaps remain inside the certified NFL scope."
                ),
                details={
                    "blocking_gap_requirements": [gap["requirement_id"] for gap in blocking_gaps],
                    "warning_gap_requirements": [gap["requirement_id"] for gap in warning_gaps],
                    "next_governed_phase": NFL_PRODUCTION_COMPLETION_NEXT_PHASE,
                },
            )
        )
        blocking_gaps = [
            result
            for result in audit_results
            if result["blocking_if_incomplete"] and result["classification"] != COMPLETE_AND_VALIDATED
        ]
        validation_checks = [
            {
                "check_id": result["requirement_id"],
                "category": "production_completion",
                "severity": "error" if result["blocking_if_incomplete"] else "warning",
                "ok": result["classification"] == COMPLETE_AND_VALIDATED
                or result["classification"] == DEFERRED_NON_BLOCKING,
                "expected": COMPLETE_AND_VALIDATED,
                "actual": result["classification"],
            }
            for result in audit_results
        ]
        error_checks = [check for check in validation_checks if check["severity"] == "error"]
        warning_checks = [check for check in validation_checks if check["severity"] == "warning"]
        ok = all(check["ok"] for check in error_checks)
        dashboard_views["production_audit_results"] = audit_results
        dashboard_views["production_gap_register"] = {
            "blocking_gaps": blocking_gaps,
            "warning_gaps": warning_gaps,
        }
        dashboard_views["summary_cards"][0] = {
            "label": "NFL production status",
            "value": "completed" if ok else "blocked",
            "detail": f"{sum(1 for result in audit_results if result['classification'] == COMPLETE_AND_VALIDATED)} of {len(audit_results)} requirements complete and validated",
        }
        dashboard_views["summary_cards"][2] = {
            "label": "Blocking gaps",
            "value": str(len(blocking_gaps)),
            "detail": ", ".join(gap["requirement_name"] for gap in blocking_gaps) if blocking_gaps else "None",
        }
        dashboard_views["summary_cards"][3] = {
            "label": "Next governed phase",
            "value": NFL_PRODUCTION_COMPLETION_NEXT_PHASE,
            "detail": "Ready" if ok else "Blocked",
        }
        reporting_surface_summary = {
            "upstream_backtest_artifacts_ok": _normalize_bool(backtest_snapshot.get("artifact_integrity_ok")),
            "upstream_pipeline_validation_artifacts_ok": _normalize_bool(
                pipeline_validation_snapshot.get("artifact_integrity_ok")
            ),
            "upstream_research_intelligence_artifacts_ok": _normalize_bool(
                research_intelligence_snapshot.get("artifact_integrity_ok")
            ),
            "upstream_universal_market_framework_artifacts_ok": _normalize_bool(
                universal_market_framework_snapshot.get("artifact_integrity_ok")
            ),
            "current_artifacts_requested": persist_artifacts,
            "current_artifact_integrity_ok": current_artifact_integrity_ok,
            "current_artifact_paths": reporting_artifact_paths,
        }
        snapshot = {
            "ok": ok,
            "status": "completed" if ok else "blocked",
            "readiness": "covariance_and_time_dependent_risk_audit_ready" if ok else "blocked",
            "lifecycle_state": "nfl_production_complete" if ok else "blocked",
            "validation_state": "validated" if ok else "blocked",
            "schema_version": NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION,
            "dataset_id": DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_ID,
            "dataset_name": DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_NAME,
            "nfl_production_completion_run_id": run_id,
            "nfl_production_completion_version": NFL_PRODUCTION_COMPLETION_RUNTIME_VERSION,
            "generated_at": _utc_now(),
            "reference_profile_id": NFL_PRODUCTION_COMPLETION_REFERENCE_PROFILE_ID,
            "next_governed_phase": NFL_PRODUCTION_COMPLETION_NEXT_PHASE,
            "nfl_reference_parity": reference_parity,
            "production_audit_results": audit_results,
            "production_gap_register": dashboard_views["production_gap_register"],
            "dashboard_views": dashboard_views,
            "query_interfaces": query_interfaces,
            "validation_checks": validation_checks,
            "validation_summary": {
                "error_check_count": len(error_checks),
                "error_checks_passed": sum(1 for check in error_checks if check["ok"]),
                "warning_check_count": len(warning_checks),
                "warning_checks_passed": sum(1 for check in warning_checks if check["ok"]),
            },
            "lineage_summary": lineage_summary,
            "certification_summary": certification_summary,
            "reporting_surface_summary": reporting_surface_summary,
            "artifact_references": current_artifact_references,
            "artifact_integrity_ok": current_artifact_integrity_ok,
            "storage": {},
            "warnings": [],
            "unresolved_blockers": [gap["requirement_id"] for gap in blocking_gaps],
            "layer_snapshots": (
                {
                    "certified_research_assets": asset_snapshots,
                    "historical_dataset": dataset_snapshot,
                    "feature_snapshots": feature_snapshot,
                    "mathematical_engines": math_snapshot,
                    "signals": signal_snapshot,
                    "decision_rows": decision_snapshot,
                    "baseline_backtesting": backtest_snapshot,
                    "pipeline_validation": pipeline_validation_snapshot,
                    "research_intelligence": research_intelligence_snapshot,
                    "universal_market_framework": universal_market_framework_snapshot,
                }
                if include_layer_snapshots
                else {}
            ),
        }
        if persist_artifacts:
            current_artifact_references = _write_artifacts(
                artifact_root=Path(artifact_root or DEFAULT_NFL_PRODUCTION_COMPLETION_ARTIFACT_ROOT),
                run_id=run_id,
                snapshot=snapshot,
            )
            snapshot["artifact_references"] = current_artifact_references
            snapshot["artifact_integrity_ok"] = all(
                _path_exists(path)
                for key, path in current_artifact_references.items()
                if key != "artifact_root"
            )
            snapshot["reporting_surface_summary"]["current_artifact_integrity_ok"] = snapshot["artifact_integrity_ok"]
            snapshot["reporting_surface_summary"]["current_artifact_paths"] = [
                str(path)
                for key, path in current_artifact_references.items()
                if key != "artifact_root"
            ]
            for result in audit_results:
                if result["requirement_id"] != "reporting_surfaces":
                    continue
                result["details"]["current_artifact_integrity_ok"] = snapshot["artifact_integrity_ok"]
                result["details"]["persist_artifacts"] = persist_artifacts
                result["source_artifact_paths"] = list(snapshot["reporting_surface_summary"]["current_artifact_paths"])
                if snapshot["artifact_integrity_ok"]:
                    result["classification"] = COMPLETE_AND_VALIDATED
                    result["status"] = "ready"
                    result["validation_state"] = _validation_state(COMPLETE_AND_VALIDATED)
                    break
                result["classification"] = PARTIAL
                result["status"] = PARTIAL
                result["validation_state"] = _validation_state(PARTIAL)
                break

        for result in audit_results:
            audit_row = {
                "audit_item_id": _stable_id(
                    "nfl_production_completion_audit",
                    run_id,
                    result["requirement_id"],
                ),
                "nfl_production_completion_run_id": run_id,
                "requirement_id": result["requirement_id"],
                "requirement_name": result["requirement_name"],
                "classification": result["classification"],
                "blocking_if_incomplete": 1 if result["blocking_if_incomplete"] else 0,
                "status": result["status"],
                "validation_state": result["validation_state"],
                "canonical_owner": result["canonical_owner"],
                "summary": result["summary"],
                "source_snapshot_ids_json": _as_json(result["source_snapshot_ids"]),
                "source_artifact_paths_json": _as_json(result["source_artifact_paths"]),
                "lineage_reference_json": _as_json(result["lineage_reference"]),
                "details_json": _as_json(result["details"]),
                "schema_version": NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION,
                "created_at": snapshot["generated_at"],
                "updated_at": snapshot["generated_at"],
                "source": "nfl_production_completion_runtime",
                "provider": "local_repo",
                "market": NFL_PRODUCTION_COMPLETION_REFERENCE_PROFILE_ID,
                "market_type": "production_completion_audit",
                "asset_class": "sports",
                "snapshot_id": run_id,
                "lineage_id": _stable_id(
                    "nfl_production_completion_audit_lineage",
                    run_id,
                    result["requirement_id"],
                ),
                "version_id": _stable_id(
                    "nfl_production_completion_audit_version",
                    run_id,
                    result["requirement_id"],
                    NFL_PRODUCTION_COMPLETION_RUNTIME_VERSION,
                ),
                "quality_score": 1.0 if result["classification"] == COMPLETE_AND_VALIDATED else 0.0,
            }
            storage.upsert(NFL_PRODUCTION_COMPLETION_AUDIT_TABLE, audit_row, key_columns=("audit_item_id",))

        run_row = {
            "nfl_production_completion_run_id": run_id,
            "dataset_id": DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_ID,
            "dataset_name": DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_NAME,
            "owner": DEFAULT_NFL_PRODUCTION_COMPLETION_OWNER,
            "sport": "football",
            "feature_pack": "production_completion.sports.nfl",
            "storage_location": str(storage.path),
            "readiness": snapshot["readiness"],
            "update_frequency": "manual",
            "validation_state": snapshot["validation_state"],
            "status": snapshot["status"],
            "research_intelligence_run_id": lineage_summary["research_intelligence_run_id"],
            "universal_market_framework_run_id": lineage_summary["universal_market_framework_run_id"],
            "pipeline_validation_run_id": lineage_summary["pipeline_validation_run_id"],
            "backtest_run_id": lineage_summary["backtest_run_id"],
            "decision_batch_id": lineage_summary["decision_batch_id"],
            "audit_item_count": len(audit_results),
            "blocking_gap_count": len(blocking_gaps),
            "warning_gap_count": len(warning_gaps),
            "dashboard_view_count": len(dashboard_views),
            "query_interface_count": len(query_interfaces),
            "artifact_root": snapshot["artifact_references"].get("artifact_root", ""),
            "report_json_path": snapshot["artifact_references"].get("report_json_path", ""),
            "report_markdown_path": snapshot["artifact_references"].get("report_markdown_path", ""),
            "dashboard_json_path": snapshot["artifact_references"].get("dashboard_json_path", ""),
            "results_json": _as_json(
                {
                    "production_gap_register": snapshot["production_gap_register"],
                    "reporting_surface_summary": snapshot["reporting_surface_summary"],
                    "validation_summary": snapshot["validation_summary"],
                }
            ),
            "payload_json": _as_json(
                {
                    "nfl_reference_parity": snapshot["nfl_reference_parity"],
                    "lineage_summary": snapshot["lineage_summary"],
                    "certification_summary": snapshot["certification_summary"],
                    "artifact_integrity_ok": snapshot["artifact_integrity_ok"],
                }
            ),
            "schema_version": NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION,
            "created_at": snapshot["generated_at"],
            "updated_at": snapshot["generated_at"],
            "source": "nfl_production_completion_runtime",
            "provider": "local_repo",
            "market": NFL_PRODUCTION_COMPLETION_REFERENCE_PROFILE_ID,
            "market_type": "production_completion_audit",
            "asset_class": "sports",
            "snapshot_id": run_id,
            "lineage_id": _stable_id(
                "nfl_production_completion_lineage",
                run_id,
                lineage_summary,
            ),
            "version_id": _stable_id(
                "nfl_production_completion_version",
                run_id,
                NFL_PRODUCTION_COMPLETION_RUNTIME_VERSION,
            ),
            "quality_score": 1.0 if snapshot["ok"] else 0.0,
        }
        storage.upsert(NFL_PRODUCTION_COMPLETION_RUN_TABLE, run_row, key_columns=("nfl_production_completion_run_id",))
        snapshot["storage"] = storage.health()
        _NFL_PRODUCTION_COMPLETION_SNAPSHOT_CACHE[cache_key] = copy.deepcopy(snapshot)
        return snapshot
    finally:
        storage.close()


def get_nfl_production_completion_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> dict[str, Any]:
    try:
        return build_nfl_production_completion_snapshot(
            storage_path=storage_path,
            backend=backend,
            include_layer_snapshots=True,
            persist_artifacts=True,
        )
    except Exception as exc:
        return _missing_snapshot(
            storage_path=str(Path(storage_path or DEFAULT_NFL_PRODUCTION_COMPLETION_STORAGE_PATH)),
            status="nfl_production_completion_snapshot_error",
            warnings=[str(exc)],
        )


__all__ = [
    "DEFAULT_NFL_PRODUCTION_COMPLETION_ARTIFACT_ROOT",
    "DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_ID",
    "DEFAULT_NFL_PRODUCTION_COMPLETION_DATASET_NAME",
    "DEFAULT_NFL_PRODUCTION_COMPLETION_STORAGE_PATH",
    "NFL_PRODUCTION_COMPLETION_RUNTIME_VERSION",
    "NFL_PRODUCTION_COMPLETION_SCHEMA_VERSION",
    "build_nfl_production_completion_snapshot",
    "get_nfl_production_completion_snapshot_for_dashboard",
]
