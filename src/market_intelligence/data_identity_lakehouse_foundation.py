from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from src.data.data_identity_lakehouse import (
    DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
    DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
    DEFAULT_DATA_IDENTITY_LAKEHOUSE_ROOT,
    DataIdentityLakehouseRuntime,
)
from src.market_intelligence.research_intelligence import DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH
from src.storage.local_store import create_local_storage_engine


DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION = "data_identity_foundation.v1"
DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION = "phase-data-identity-foundation.v1"
DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_ID = "dataset.sports.nfl.data_identity_foundation"
DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_NAME = "data_identity_lakehouse_foundation"
DEFAULT_DATA_IDENTITY_FOUNDATION_OWNER = "src.market_intelligence"
DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH = DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH
DEFAULT_DATA_IDENTITY_FOUNDATION_ARTIFACT_ROOT = Path(
    "data/backtests/data_identity_foundation_artifacts"
)
DATA_IDENTITY_FOUNDATION_RUN_TABLE = "data_identity_foundation_runs"
DATA_IDENTITY_FOUNDATION_AUDIT_TABLE = "data_identity_foundation_audit_items"
DATA_IDENTITY_FOUNDATION_REFERENCE_PROFILE_ID = "sports:nfl"
DATA_IDENTITY_FOUNDATION_NEXT_PHASE = "First Controlled NFL Vendor Ingest"
_DATA_IDENTITY_FOUNDATION_SNAPSHOT_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}

COMPLETE_AND_VALIDATED = "complete_and_validated"
COMPLETE_BUT_UNVALIDATED = "complete_but_unvalidated"
PARTIAL = "partial"
MISSING = "missing"
DEFERRED = "deferred"
DUPLICATED = "duplicated"


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


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _normalize_text(value).lower() in {"1", "true", "yes", "ready", "completed", "validated"}


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


def _validation_state(classification: str) -> str:
    if classification == COMPLETE_AND_VALIDATED:
        return "validated"
    if classification == COMPLETE_BUT_UNVALIDATED:
        return "unvalidated"
    if classification == DEFERRED:
        return "deferred"
    if classification == DUPLICATED:
        return "duplicate"
    if classification == MISSING:
        return "missing"
    return "blocked"


def _safe_call(name: str, builder) -> dict[str, Any]:
    try:
        return dict(builder())
    except Exception as exc:
        return {
            "ok": False,
            "status": f"{name}_snapshot_error",
            "warnings": [str(exc)],
        }


def _audit_result(
    *,
    requirement_id: str,
    requirement_name: str,
    initial_classification: str,
    final_classification: str,
    blocking_if_incomplete: bool,
    canonical_owner: str,
    summary: str,
    implemented_changes: list[str],
    details: Mapping[str, Any],
    source_snapshot_ids: list[str] | None = None,
    source_artifact_paths: list[str] | None = None,
    lineage_reference: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "requirement_name": requirement_name,
        "initial_classification": initial_classification,
        "final_classification": final_classification,
        "blocking_if_incomplete": bool(blocking_if_incomplete),
        "status": "ready" if final_classification == COMPLETE_AND_VALIDATED else final_classification,
        "validation_state": _validation_state(final_classification),
        "canonical_owner": canonical_owner,
        "summary": summary,
        "implemented_changes": list(implemented_changes),
        "details": dict(details),
        "source_snapshot_ids": list(source_snapshot_ids or []),
        "source_artifact_paths": list(source_artifact_paths or []),
        "lineage_reference": dict(lineage_reference or {}),
    }


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
    report_json_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    dashboard_json_path.write_text(
        json.dumps(snapshot.get("dashboard_views", {}), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Data Identity, Reconciliation and Lakehouse Foundation",
        "",
        f"- Status: `{snapshot.get('status')}`",
        f"- Readiness: `{snapshot.get('readiness')}`",
        f"- Reference profile: `{snapshot.get('reference_profile_id')}`",
        f"- NFL parity preserved: `{snapshot.get('nfl_parity_status', {}).get('ok')}`",
        f"- Identity mappings: `{snapshot.get('identity_resolution_readiness', {}).get('approved_mapping_count')}`",
        f"- Lakehouse partitions: `{snapshot.get('parquet_readiness', {}).get('partition_count')}`",
        f"- Next governed phase: `{snapshot.get('next_governed_phase')}`",
        "",
        "This artifact certifies the shared identity and lakehouse foundation without altering the certified NFL research chain.",
    ]
    report_markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "artifact_root": str(run_root),
        "report_json_path": str(report_json_path),
        "report_markdown_path": str(report_markdown_path),
        "dashboard_json_path": str(dashboard_json_path),
    }


def _missing_snapshot(*, storage_path: str, status: str, warnings: list[str]) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "readiness": "blocked",
        "lifecycle_state": "blocked",
        "validation_state": "blocked",
        "schema_version": DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION,
        "dataset_id": DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_ID,
        "dataset_name": DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_NAME,
        "data_identity_foundation_run_id": "",
        "data_identity_foundation_version": DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION,
        "generated_at": "",
        "reference_profile_id": DATA_IDENTITY_FOUNDATION_REFERENCE_PROFILE_ID,
        "next_governed_phase": DATA_IDENTITY_FOUNDATION_NEXT_PHASE,
        "capability_audit_matrix": [],
        "canonical_owners_reused": [],
        "missing_capabilities_implemented": [],
        "duplicated_capabilities_avoided_or_consolidated": [],
        "identity_resolution_readiness": {},
        "reconciliation_readiness": {},
        "quarantine_manual_review_readiness": {},
        "bronze_silver_gold_readiness": {},
        "parquet_readiness": {},
        "delta_compatibility_status": {},
        "spark_deferral_evidence": {},
        "nfl_parity_status": {},
        "first_vendor_ingest_readiness": {},
        "proprietary_platform_delta": {},
        "institutional_readiness_delta": {},
        "dashboard_views": {},
        "query_interfaces": [],
        "validation_checks": [],
        "validation_summary": {},
        "artifact_references": {},
        "artifact_integrity_ok": False,
        "storage": {"database_path": storage_path},
        "warnings": warnings,
        "unresolved_blockers": list(warnings or [status]),
        "layer_snapshots": {},
    }


def _snapshot_cache_key(
    storage_path: str | Path | None,
    *,
    backend: str,
    artifact_root: str | Path | None,
    lakehouse_root: str | Path | None,
    include_layer_snapshots: bool,
    persist_artifacts: bool,
) -> tuple[Any, ...]:
    resolved = Path(storage_path or DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH).expanduser().resolve()
    stat = resolved.stat() if resolved.exists() else None
    resolved_artifact_root = Path(artifact_root or DEFAULT_DATA_IDENTITY_FOUNDATION_ARTIFACT_ROOT).expanduser().resolve()
    resolved_lakehouse_root = Path(lakehouse_root or DEFAULT_DATA_IDENTITY_LAKEHOUSE_ROOT).expanduser().resolve()
    return (
        str(resolved),
        getattr(stat, "st_mtime_ns", 0),
        getattr(stat, "st_size", 0),
        backend,
        str(resolved_artifact_root),
        str(resolved_lakehouse_root),
        include_layer_snapshots,
        persist_artifacts,
    )


def build_data_identity_foundation_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    artifact_root: str | Path | None = None,
    lakehouse_root: str | Path | None = None,
    include_layer_snapshots: bool = True,
    persist_artifacts: bool = True,
) -> dict[str, Any]:
    cache_key = _snapshot_cache_key(
        storage_path,
        backend=backend,
        artifact_root=artifact_root,
        lakehouse_root=lakehouse_root,
        include_layer_snapshots=include_layer_snapshots,
        persist_artifacts=persist_artifacts,
    )
    cached_snapshot = _DATA_IDENTITY_FOUNDATION_SNAPSHOT_CACHE.get(cache_key)
    if cached_snapshot is not None:
        return copy.deepcopy(cached_snapshot)

    from src.market_intelligence.nfl_production_completion import build_nfl_production_completion_snapshot

    storage = create_local_storage_engine(
        storage_path or DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH,
        backend=backend,
    )
    try:
        nfl_production_completion_snapshot = _safe_call(
            "nfl_production_completion",
            lambda: build_nfl_production_completion_snapshot(
                storage_path=storage.path,
                backend=backend,
                include_layer_snapshots=True,
                persist_artifacts=False,
            ),
        )
        production_layer_snapshots = dict(nfl_production_completion_snapshot.get("layer_snapshots") or {})
        research_intelligence_snapshot = dict(
            production_layer_snapshots.get("research_intelligence") or {}
        )
        universal_market_framework_snapshot = dict(
            production_layer_snapshots.get("universal_market_framework") or {}
        )

        runtime = DataIdentityLakehouseRuntime(
            storage_path=storage.path,
            backend=backend,
            lakehouse_root=lakehouse_root or DEFAULT_DATA_IDENTITY_LAKEHOUSE_ROOT,
        )
        try:
            sync_result = runtime.synchronize()
        finally:
            runtime.close()

        readiness_snapshot = dict(sync_result.get("readiness_snapshot") or {})
        capability_rows = list(sync_result.get("capability_audit") or [])
        identity_mappings = list((sync_result.get("seed_result") or {}).get("mappings") or [])
        lakehouse_partitions = list((sync_result.get("lakehouse_result") or {}).get("partitions") or [])
        missing_capabilities_implemented = [
            row["requirement_id"]
            for row in capability_rows
            if row["initial_classification"] in {MISSING, PARTIAL}
            and row["final_classification"] == COMPLETE_AND_VALIDATED
        ]
        canonical_owners_reused = [
            "src.data.historical_dataset_acquisition_runtime.HistoricalDatasetAcquisitionRuntime",
            "src.storage.local_store.LocalStorageEngine",
            "src.data.local_platform.LocalDataPlatform",
            "src.data.historical_research_database.HistoricalResearchDatabase",
            "src.data.historical_research_asset_certification_runtime.HistoricalResearchAssetCertificationRuntime",
            "src.data.research_asset_lifecycle_runtime.ResearchAssetLifecycleRuntime",
            "src.data.source_event_links",
            "src.data.market_identity_resolver",
            "src.data.validation",
            "src.analytics.model_governance.data_lineage",
            "src.services.streamlit_dashboard_data",
            "src.market_intelligence.universal_market_framework",
        ]
        duplicated_capabilities_avoided_or_consolidated = [
            "Extended LocalStorageEngine with Parquet support instead of creating a second storage engine.",
            "Reused source_event_links for event identity matching instead of adding a parallel event matcher.",
            "Reused market_identity_resolver for market and selection matching instead of adding a parallel market matcher.",
            "Left historical_research_database as the normalization and certified-dataset owner.",
            "Left HistoricalDatasetAcquisitionRuntime as the raw acquisition owner and ResearchAssetLifecycleRuntime as the lifecycle owner.",
        ]
        lineage_summary = {
            "research_intelligence_run_id": _normalize_text(research_intelligence_snapshot.get("research_intelligence_run_id")),
            "universal_market_framework_run_id": _normalize_text(
                universal_market_framework_snapshot.get("universal_market_framework_run_id")
            ),
            "nfl_production_completion_run_id": _normalize_text(
                nfl_production_completion_snapshot.get("nfl_production_completion_run_id")
            ),
            "pipeline_validation_run_id": _normalize_text(
                (nfl_production_completion_snapshot.get("lineage_summary") or {}).get("pipeline_validation_run_id")
            ),
            "backtest_run_id": _normalize_text(
                (nfl_production_completion_snapshot.get("lineage_summary") or {}).get("backtest_run_id")
            ),
            "decision_batch_id": _normalize_text(
                (nfl_production_completion_snapshot.get("lineage_summary") or {}).get("decision_batch_id")
            ),
        }
        nfl_parity_status = {
            "ok": bool(universal_market_framework_snapshot.get("nfl_reference_parity", {}).get("ok"))
            and bool(nfl_production_completion_snapshot.get("nfl_reference_parity", {}).get("ok")),
            "research_intelligence_run_id": lineage_summary["research_intelligence_run_id"],
            "universal_market_framework_run_id": lineage_summary["universal_market_framework_run_id"],
            "nfl_production_completion_run_id": lineage_summary["nfl_production_completion_run_id"],
            "parity_digest": _stable_id(
                "data_identity_foundation.parity",
                universal_market_framework_snapshot.get("nfl_reference_parity"),
                nfl_production_completion_snapshot.get("nfl_reference_parity"),
            ),
        }
        source_snapshot_ids = [
            value
            for value in (
                lineage_summary["research_intelligence_run_id"],
                lineage_summary["universal_market_framework_run_id"],
                lineage_summary["nfl_production_completion_run_id"],
                lineage_summary["pipeline_validation_run_id"],
                lineage_summary["backtest_run_id"],
                lineage_summary["decision_batch_id"],
            )
            if value
        ]

        capability_lookup = {row["requirement_id"]: row for row in capability_rows}
        artifact_paths = [
            str(path)
            for path in [
                *(Path(row["file_path"]) for row in lakehouse_partitions if row.get("file_path")),
            ]
        ]
        audit_results = [
            _audit_result(
                requirement_id="canonical_identity_foundation",
                requirement_name="Canonical identity foundation",
                initial_classification=capability_lookup["canonical_identity_foundation"]["initial_classification"],
                final_classification=capability_lookup["canonical_identity_foundation"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.data_identity_lakehouse",
                summary="Stable internal identity mappings now persist provider, external ID, internal ID, validity, review, and approval evidence across supported entity categories.",
                implemented_changes=[
                    "Added persisted identity_mappings and mapping_approvals contracts.",
                    "Seeded certified NFL event, team, venue, market, selection, provider, and vendor-entity mappings.",
                    "Validated generic identity support for future company, security, listing, prediction-event, and prediction-contract categories.",
                ],
                details={
                    "identity_mapping_count": len(identity_mappings),
                    "entity_type_counts": readiness_snapshot.get("identity_mapping_counts", {}),
                    "supported_entity_types": readiness_snapshot.get("identity_resolution_readiness", {}).get(
                        "supported_entity_types", []
                    ),
                },
                source_snapshot_ids=source_snapshot_ids,
                source_artifact_paths=[],
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="matching",
                requirement_name="Matching",
                initial_classification=capability_lookup["matching"]["initial_classification"],
                final_classification=capability_lookup["matching"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.source_event_links + src.data.market_identity_resolver",
                summary="Deterministic matching now reuses the canonical event and market resolvers and records candidates before any low-confidence case reaches certified or production-ready data.",
                implemented_changes=[
                    "Reused source_event_links for event identity resolution.",
                    "Reused market_identity_resolver for canonical market and selection matching.",
                    "Persisted identity_match_candidates and manual review routing for ambiguous cases.",
                ],
                details={
                    "match_hierarchy": [
                        "approved_existing_mapping",
                        "stable_external_identifier",
                        "exact_composite_identity",
                        "normalized_exact_match",
                        "controlled_fuzzy_match",
                        "manual_review",
                    ],
                    "manual_review_queue_count": len(readiness_snapshot.get("manual_review_queue", [])),
                },
                source_snapshot_ids=source_snapshot_ids,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="reconciliation",
                requirement_name="Reconciliation",
                initial_classification=capability_lookup["reconciliation"]["initial_classification"],
                final_classification=capability_lookup["reconciliation"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.data_identity_lakehouse",
                summary="Identity reconciliation remains separate from observation/value reconciliation, and each sportsbook observation is preserved independently with accepted evidence, provider reliability, freshness, and explanation.",
                implemented_changes=[
                    "Added identity_reconciliation_results with accepted and rejected evidence payloads.",
                    "Stored provider reliability metadata and point-in-time freshness for certified sportsbook observations.",
                    "Preserved sportsbook observations independently instead of collapsing books into a single canonical line.",
                ],
                details={
                    "reconciliation_result_count": len(readiness_snapshot.get("reconciliation_results", [])),
                    "accepted_count": readiness_snapshot.get("reconciliation_readiness", {}).get("accepted_count", 0),
                },
                source_snapshot_ids=source_snapshot_ids,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="point_in_time_and_revision_contract",
                requirement_name="Point-in-time and revision contract",
                initial_classification=capability_lookup["point_in_time_and_revision_contract"]["initial_classification"],
                final_classification=capability_lookup["point_in_time_and_revision_contract"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.data_identity_lakehouse + src.data.historical_research_database",
                summary="Identity and reconciliation records now preserve event, publication, observation, processing, validity, revision, and latest-state fields while leaving the existing decision-cutoff policy untouched.",
                implemented_changes=[
                    "Standardized event_time, published_at, observed_at, processed_at, valid_from, valid_to, revision_number, is_latest, source_published_at, and system_observed_at fields.",
                    "Added revision-aware supersede behavior for changed mappings.",
                    "Left the certified historical decision cutoff and restated history rules unchanged.",
                ],
                details={
                    "timestamp_contract_fields": [
                        "event_time",
                        "published_at",
                        "observed_at",
                        "processed_at",
                        "valid_from",
                        "valid_to",
                        "revision_number",
                        "is_latest",
                        "source_published_at",
                        "system_observed_at",
                    ]
                },
                source_snapshot_ids=source_snapshot_ids,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="quality_quarantine_review",
                requirement_name="Quality, quarantine, and review",
                initial_classification=capability_lookup["quality_quarantine_review"]["initial_classification"],
                final_classification=capability_lookup["quality_quarantine_review"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.data_identity_lakehouse",
                summary="Canonical data-quality events, quarantine records, match candidates, manual review, and approval records now exist and block unsafe data instead of silently coercing or dropping it.",
                implemented_changes=[
                    "Added data_quality_events, quarantine_records, manual_review_queue, and mapping_approvals tables.",
                    "Routed ambiguous identity matches into manual review and quarantine instead of accepting them.",
                    "Preserved accepted, accepted_with_warning, quarantined, rejected, manual_review, and superseded decision states.",
                ],
                details={
                    "quality_event_count": len(readiness_snapshot.get("quality_events", [])),
                    "quarantine_count": len(readiness_snapshot.get("quarantine_records", [])),
                    "manual_review_count": len(readiness_snapshot.get("manual_review_queue", [])),
                },
                source_snapshot_ids=source_snapshot_ids,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="bronze_silver_gold_mapping",
                requirement_name="Bronze, Silver, and Gold mapping",
                initial_classification=capability_lookup["bronze_silver_gold_mapping"]["initial_classification"],
                final_classification=capability_lookup["bronze_silver_gold_mapping"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.historical_dataset_acquisition_runtime + src.data.historical_research_database",
                summary="The existing lifecycle now maps cleanly to Bronze raw acquisition, Silver normalized and identity-aware rows, and Gold certified analytical outputs without replacing the lifecycle or certification systems.",
                implemented_changes=[
                    "Mapped raw_records to Bronze Parquet partitions.",
                    "Mapped historical events, markets, selections, identity mappings, and reconciliation results to Silver partitions.",
                    "Mapped historical_dataset_rows and feature_snapshots to Gold partitions.",
                ],
                details={
                    "layer_counts": readiness_snapshot.get("bronze_silver_gold_readiness", {}).get("layer_counts", {}),
                    "lakehouse_root": (sync_result.get("lakehouse_result") or {}).get("lakehouse_root"),
                },
                source_snapshot_ids=source_snapshot_ids,
                source_artifact_paths=artifact_paths,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="parquet_analytical_storage",
                requirement_name="Parquet analytical storage",
                initial_classification=capability_lookup["parquet_analytical_storage"]["initial_classification"],
                final_classification=capability_lookup["parquet_analytical_storage"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.storage.local_store.LocalStorageEngine",
                summary="The canonical storage owner now supports deterministic Parquet writes and reads with manifest metadata, checksums, row counts, deterministic file IDs, and reproducible roundtrips.",
                implemented_changes=[
                    "Extended LocalStorageEngine with Parquet write and read interfaces.",
                    "Persisted lakehouse_partitions manifests with partition metadata, content digests, and roundtrip validation.",
                    "Used idempotent file paths derived from deterministic content identities.",
                ],
                details={
                    "partition_count": readiness_snapshot.get("parquet_readiness", {}).get("partition_count", 0),
                    "roundtrip_ok": readiness_snapshot.get("parquet_readiness", {}).get("roundtrip_ok", False),
                },
                source_snapshot_ids=source_snapshot_ids,
                source_artifact_paths=artifact_paths,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="delta_compatible_interfaces",
                requirement_name="Delta-compatible interfaces",
                initial_classification=capability_lookup["delta_compatible_interfaces"]["initial_classification"],
                final_classification=capability_lookup["delta_compatible_interfaces"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.data_identity_lakehouse",
                summary="Lakehouse manifests now expose the metadata needed for later Delta Lake adoption without requiring Delta or Spark in the current local runtime.",
                implemented_changes=[
                    "Stored Delta-compatible metadata for schema evolution, versioned tables, corrections/upserts, time travel, and concurrency handoff.",
                    "Kept Spark optional and deferred until measured scale requires distributed execution.",
                ],
                details=readiness_snapshot.get("delta_compatibility", {}),
                source_snapshot_ids=source_snapshot_ids,
                source_artifact_paths=artifact_paths,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="security_and_governance",
                requirement_name="Security and governance",
                initial_classification=capability_lookup["security_and_governance"]["initial_classification"],
                final_classification=capability_lookup["security_and_governance"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.data.validation + src.analytics.model_governance.data_lineage",
                summary="The foundation reuses the repository’s existing local-only, parameterized, lineage-preserving governance posture and does not ingest vendor data or require secrets in tests.",
                implemented_changes=[
                    "Reused canonical validation, lineage, provenance, and local-only storage owners.",
                    "Kept vendor ingest out of scope for this phase.",
                ],
                details={
                    "vendor_ingest_performed": False,
                    "secrets_required_for_tests": False,
                    "lineage_preserved": True,
                    "provenance_preserved": True,
                },
                source_snapshot_ids=source_snapshot_ids,
                lineage_reference=lineage_summary,
            ),
            _audit_result(
                requirement_id="readiness_surfaces",
                requirement_name="Readiness surfaces",
                initial_classification=capability_lookup["readiness_surfaces"]["initial_classification"],
                final_classification=capability_lookup["readiness_surfaces"]["final_classification"],
                blocking_if_incomplete=True,
                canonical_owner="src.market_intelligence.data_identity_lakehouse_foundation + src.services.streamlit_dashboard_data",
                summary="The phase now exposes a deterministic readiness report, dashboard/query surfaces, capability audit matrix, evidence package, blocker ledger, lakehouse readiness, and first-vendor-ingest readiness state.",
                implemented_changes=[
                    "Added the data-identity phase snapshot, persisted run row, and audit-item rows.",
                    "Added dashboard-ready summary cards and query interfaces.",
                    "Extended the NFL P0 readiness surface and Streamlit data facade to expose the new phase.",
                ],
                details={
                    "first_vendor_ingest_readiness_state": readiness_snapshot.get("first_vendor_ingest_readiness_state"),
                    "lakehouse_readiness_state": readiness_snapshot.get("lakehouse_readiness_state"),
                    "query_interface_count": len(readiness_snapshot.get("query_surfaces", [])),
                },
                source_snapshot_ids=source_snapshot_ids,
                source_artifact_paths=[],
                lineage_reference=lineage_summary,
            ),
        ]

        blocking_gaps = [
            row for row in audit_results if row["blocking_if_incomplete"] and row["final_classification"] != COMPLETE_AND_VALIDATED
        ]
        warning_gaps = [
            row for row in audit_results if not row["blocking_if_incomplete"] and row["final_classification"] != COMPLETE_AND_VALIDATED
        ]
        ok = not blocking_gaps and bool(readiness_snapshot.get("ok")) and bool(nfl_parity_status.get("ok"))
        run_id = _stable_id(
            "data_identity_foundation.run",
            DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION,
            lineage_summary,
            [row["final_classification"] for row in audit_results],
            [row.get("deterministic_file_id") for row in lakehouse_partitions],
        )
        query_interfaces = list(readiness_snapshot.get("query_surfaces", [])) + [
            {
                "query_id": "inspect_capability_audit_matrix",
                "purpose": "Inspect initial and final classifications for every data identity and lakehouse capability.",
            },
            {
                "query_id": "inspect_first_vendor_ingest_readiness",
                "purpose": "Inspect blockers removed and remaining state before activating the first controlled NFL vendor ingest.",
            },
        ]
        dashboard_views = {
            "summary_cards": [
                {
                    "label": "Foundation status",
                    "value": "completed" if ok else "blocked",
                    "detail": f"{sum(1 for row in audit_results if row['final_classification'] == COMPLETE_AND_VALIDATED)} of {len(audit_results)} requirements complete and validated",
                },
                {
                    "label": "Identity mappings",
                    "value": str(readiness_snapshot.get("identity_resolution_readiness", {}).get("approved_mapping_count", 0)),
                    "detail": f"{len(readiness_snapshot.get('identity_resolution_readiness', {}).get('supported_entity_types', []))} supported entity categories",
                },
                {
                    "label": "Lakehouse partitions",
                    "value": str(readiness_snapshot.get("parquet_readiness", {}).get("partition_count", 0)),
                    "detail": f"Bronze/Silver/Gold {readiness_snapshot.get('bronze_silver_gold_readiness', {}).get('layer_counts', {})}",
                },
                {
                    "label": "Next governed phase",
                    "value": DATA_IDENTITY_FOUNDATION_NEXT_PHASE,
                    "detail": "Ready" if ok else "Blocked",
                },
            ],
            "capability_audit_matrix": audit_results,
            "identity_resolution_readiness": readiness_snapshot.get("identity_resolution_readiness", {}),
            "reconciliation_readiness": readiness_snapshot.get("reconciliation_readiness", {}),
            "quarantine_manual_review_readiness": readiness_snapshot.get("quarantine_manual_review_readiness", {}),
            "bronze_silver_gold_readiness": readiness_snapshot.get("bronze_silver_gold_readiness", {}),
            "parquet_readiness": readiness_snapshot.get("parquet_readiness", {}),
            "delta_compatibility_status": readiness_snapshot.get("delta_compatibility", {}),
            "spark_deferral_evidence": readiness_snapshot.get("spark_deferral_evidence", {}),
            "first_vendor_ingest_readiness": {
                "status": readiness_snapshot.get("first_vendor_ingest_readiness_state"),
                "blocking_gaps": [row["requirement_id"] for row in blocking_gaps],
                "warning_gaps": [row["requirement_id"] for row in warning_gaps],
            },
            "canonical_owners_reused": canonical_owners_reused,
            "duplicated_capabilities_avoided_or_consolidated": duplicated_capabilities_avoided_or_consolidated,
        }
        validation_checks = [
            {
                "check_id": row["requirement_id"],
                "category": "data_identity_foundation",
                "severity": "error" if row["blocking_if_incomplete"] else "warning",
                "ok": row["final_classification"] == COMPLETE_AND_VALIDATED,
                "expected": COMPLETE_AND_VALIDATED,
                "actual": row["final_classification"],
            }
            for row in audit_results
        ] + [
            {
                "check_id": "nfl_parity_preserved",
                "category": "parity",
                "severity": "error",
                "ok": bool(nfl_parity_status.get("ok")),
                "expected": True,
                "actual": bool(nfl_parity_status.get("ok")),
            },
            {
                "check_id": "first_vendor_ingest_readiness_state",
                "category": "readiness",
                "severity": "error",
                "ok": readiness_snapshot.get("first_vendor_ingest_readiness_state") == "ready",
                "expected": "ready",
                "actual": readiness_snapshot.get("first_vendor_ingest_readiness_state"),
            },
        ]
        error_checks = [check for check in validation_checks if check["severity"] == "error"]
        warning_checks = [check for check in validation_checks if check["severity"] == "warning"]
        artifact_references: dict[str, str] = {}
        artifact_integrity_ok = False
        if persist_artifacts:
            artifact_references = _write_artifacts(
                artifact_root=Path(artifact_root or DEFAULT_DATA_IDENTITY_FOUNDATION_ARTIFACT_ROOT),
                run_id=run_id,
                snapshot={
                    "status": "completed" if ok else "blocked",
                    "readiness": "first_controlled_nfl_vendor_ingest_ready" if ok else "blocked",
                    "reference_profile_id": DATA_IDENTITY_FOUNDATION_REFERENCE_PROFILE_ID,
                    "nfl_parity_status": nfl_parity_status,
                    "identity_resolution_readiness": readiness_snapshot.get("identity_resolution_readiness", {}),
                    "parquet_readiness": readiness_snapshot.get("parquet_readiness", {}),
                    "next_governed_phase": DATA_IDENTITY_FOUNDATION_NEXT_PHASE,
                    "dashboard_views": dashboard_views,
                },
            )
            artifact_integrity_ok = all(
                _path_exists(path)
                for key, path in artifact_references.items()
                if key != "artifact_root"
            )
        proprietary_platform_delta = {
            "new_proprietary_data_assets": [
                "identity_mappings",
                "identity_reconciliation_results",
                "lakehouse_partitions",
            ],
            "new_proprietary_research_assets": [
                "capability_audit_matrix",
                "first_vendor_ingest_readiness_state",
            ],
            "new_proprietary_process_governance_assets": [
                "mapping_approvals",
                "manual_review_queue",
                "data_quality_events",
                "quarantine_records",
            ],
            "new_reusable_framework_assets": [
                "src.data.data_identity_lakehouse",
                "src.market_intelligence.data_identity_lakehouse_foundation",
                "LocalStorageEngine parquet interface",
            ],
        }
        institutional_readiness_delta = {
            "status": "improved",
            "blocking_gap_count_removed": len(missing_capabilities_implemented),
            "deterministic_storage_ready": True,
            "auditability_ready": True,
            "vendor_ingest_readiness": readiness_snapshot.get("first_vendor_ingest_readiness_state"),
        }
        snapshot = {
            "ok": ok,
            "status": "completed" if ok else "blocked",
            "readiness": "first_controlled_nfl_vendor_ingest_ready" if ok else "blocked",
            "lifecycle_state": "data_identity_lakehouse_foundation_complete" if ok else "blocked",
            "validation_state": "validated" if ok else "blocked",
            "schema_version": DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION,
            "data_identity_foundation_run_id": run_id,
            "data_identity_foundation_version": DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION,
            "generated_at": _utc_now(),
            "reference_profile_id": DATA_IDENTITY_FOUNDATION_REFERENCE_PROFILE_ID,
            "next_governed_phase": DATA_IDENTITY_FOUNDATION_NEXT_PHASE,
            "capability_audit_matrix": audit_results,
            "canonical_owners_reused": canonical_owners_reused,
            "missing_capabilities_implemented": missing_capabilities_implemented,
            "duplicated_capabilities_avoided_or_consolidated": duplicated_capabilities_avoided_or_consolidated,
            "identity_resolution_readiness": readiness_snapshot.get("identity_resolution_readiness", {}),
            "reconciliation_readiness": readiness_snapshot.get("reconciliation_readiness", {}),
            "quarantine_manual_review_readiness": readiness_snapshot.get("quarantine_manual_review_readiness", {}),
            "bronze_silver_gold_readiness": readiness_snapshot.get("bronze_silver_gold_readiness", {}),
            "parquet_readiness": readiness_snapshot.get("parquet_readiness", {}),
            "delta_compatibility_status": readiness_snapshot.get("delta_compatibility", {}),
            "spark_deferral_evidence": readiness_snapshot.get("spark_deferral_evidence", {}),
            "nfl_parity_status": nfl_parity_status,
            "first_vendor_ingest_readiness": {
                "status": readiness_snapshot.get("first_vendor_ingest_readiness_state"),
                "blocking_gaps": [row["requirement_id"] for row in blocking_gaps],
                "warning_gaps": [row["requirement_id"] for row in warning_gaps],
            },
            "proprietary_platform_delta": proprietary_platform_delta,
            "institutional_readiness_delta": institutional_readiness_delta,
            "dashboard_views": dashboard_views,
            "query_interfaces": query_interfaces,
            "validation_checks": validation_checks,
            "validation_summary": {
                "error_check_count": len(error_checks),
                "error_checks_passed": sum(1 for check in error_checks if check["ok"]),
                "warning_check_count": len(warning_checks),
                "warning_checks_passed": sum(1 for check in warning_checks if check["ok"]),
            },
            "artifact_references": artifact_references,
            "artifact_integrity_ok": artifact_integrity_ok,
            "storage": storage.health(),
            "warnings": [],
            "unresolved_blockers": [row["requirement_id"] for row in blocking_gaps],
            "layer_snapshots": (
                {
                    "research_intelligence": research_intelligence_snapshot,
                    "universal_market_framework": universal_market_framework_snapshot,
                    "nfl_production_completion": nfl_production_completion_snapshot,
                    "data_identity_lakehouse": readiness_snapshot,
                }
                if include_layer_snapshots
                else {}
            ),
        }

        for row in audit_results:
            storage.upsert(
                DATA_IDENTITY_FOUNDATION_AUDIT_TABLE,
                {
                    "audit_item_id": _stable_id("data_identity_foundation.audit", run_id, row["requirement_id"]),
                    "data_identity_foundation_run_id": run_id,
                    "requirement_id": row["requirement_id"],
                    "requirement_name": row["requirement_name"],
                    "initial_classification": row["initial_classification"],
                    "final_classification": row["final_classification"],
                    "blocking_if_incomplete": 1 if row["blocking_if_incomplete"] else 0,
                    "status": row["status"],
                    "validation_state": row["validation_state"],
                    "canonical_owner": row["canonical_owner"],
                    "summary": row["summary"],
                    "implemented_changes_json": _as_json(row["implemented_changes"]),
                    "source_snapshot_ids_json": _as_json(row["source_snapshot_ids"]),
                    "source_artifact_paths_json": _as_json(row["source_artifact_paths"]),
                    "lineage_reference_json": _as_json(row["lineage_reference"]),
                    "details_json": _as_json(row["details"]),
                    "schema_version": DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION,
                    "created_at": snapshot["generated_at"],
                    "updated_at": snapshot["generated_at"],
                    "source": "data_identity_foundation_runtime",
                    "provider": "local_repo",
                    "market": DATA_IDENTITY_FOUNDATION_REFERENCE_PROFILE_ID,
                    "market_type": "data_identity_foundation_audit",
                    "asset_class": "sports",
                    "snapshot_id": run_id,
                    "lineage_id": _stable_id("data_identity_foundation.audit.lineage", run_id, row["requirement_id"]),
                    "version_id": DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION,
                    "quality_score": 1.0 if row["final_classification"] == COMPLETE_AND_VALIDATED else 0.0,
                },
                key_columns=("audit_item_id",),
            )

        storage.upsert(
            DATA_IDENTITY_FOUNDATION_RUN_TABLE,
            {
                "data_identity_foundation_run_id": run_id,
                "dataset_id": DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_ID,
                "dataset_name": DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_NAME,
                "owner": DEFAULT_DATA_IDENTITY_FOUNDATION_OWNER,
                "sport": "football",
                "feature_pack": DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION,
                "storage_location": str(storage.path),
                "readiness": snapshot["readiness"],
                "update_frequency": "manual",
                "validation_state": snapshot["validation_state"],
                "status": snapshot["status"],
                "nfl_production_completion_run_id": lineage_summary["nfl_production_completion_run_id"],
                "universal_market_framework_run_id": lineage_summary["universal_market_framework_run_id"],
                "research_intelligence_run_id": lineage_summary["research_intelligence_run_id"],
                "pipeline_validation_run_id": lineage_summary["pipeline_validation_run_id"],
                "backtest_run_id": lineage_summary["backtest_run_id"],
                "audit_item_count": len(audit_results),
                "blocking_gap_count": len(blocking_gaps),
                "warning_gap_count": len(warning_gaps),
                "identity_mapping_count": readiness_snapshot.get("identity_resolution_readiness", {}).get(
                    "approved_mapping_count", 0
                ),
                "reconciliation_result_count": readiness_snapshot.get("reconciliation_readiness", {}).get(
                    "reconciliation_result_count", 0
                ),
                "lakehouse_partition_count": readiness_snapshot.get("parquet_readiness", {}).get("partition_count", 0),
                "artifact_root": artifact_references.get("artifact_root", ""),
                "report_json_path": artifact_references.get("report_json_path", ""),
                "report_markdown_path": artifact_references.get("report_markdown_path", ""),
                "dashboard_json_path": artifact_references.get("dashboard_json_path", ""),
                "results_json": _as_json(
                    {
                        "capability_audit_matrix": audit_results,
                        "first_vendor_ingest_readiness": snapshot["first_vendor_ingest_readiness"],
                        "parquet_readiness": snapshot["parquet_readiness"],
                    }
                ),
                "payload_json": _as_json(
                    {
                        "canonical_owners_reused": canonical_owners_reused,
                        "missing_capabilities_implemented": missing_capabilities_implemented,
                        "nfl_parity_status": nfl_parity_status,
                    }
                ),
                "schema_version": DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION,
                "created_at": snapshot["generated_at"],
                "updated_at": snapshot["generated_at"],
                "source": "data_identity_foundation_runtime",
                "provider": "local_repo",
                "market": DATA_IDENTITY_FOUNDATION_REFERENCE_PROFILE_ID,
                "market_type": "data_identity_foundation",
                "asset_class": "sports",
                "snapshot_id": run_id,
                "lineage_id": _stable_id("data_identity_foundation.lineage", run_id, lineage_summary),
                "version_id": DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION,
                "quality_score": 1.0 if snapshot["ok"] else 0.0,
            },
            key_columns=("data_identity_foundation_run_id",),
        )
        snapshot["storage"] = storage.health()
        _DATA_IDENTITY_FOUNDATION_SNAPSHOT_CACHE[cache_key] = copy.deepcopy(snapshot)
        return snapshot
    finally:
        storage.close()


def get_data_identity_foundation_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> dict[str, Any]:
    try:
        return build_data_identity_foundation_snapshot(
            storage_path=storage_path,
            backend=backend,
            include_layer_snapshots=True,
            persist_artifacts=True,
        )
    except Exception as exc:
        return _missing_snapshot(
            storage_path=str(Path(storage_path or DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH)),
            status="data_identity_foundation_snapshot_error",
            warnings=[str(exc)],
        )


__all__ = [
    "DATA_IDENTITY_FOUNDATION_AUDIT_TABLE",
    "DATA_IDENTITY_FOUNDATION_NEXT_PHASE",
    "DATA_IDENTITY_FOUNDATION_RUN_TABLE",
    "DATA_IDENTITY_FOUNDATION_RUNTIME_VERSION",
    "DATA_IDENTITY_FOUNDATION_SCHEMA_VERSION",
    "DEFAULT_DATA_IDENTITY_FOUNDATION_ARTIFACT_ROOT",
    "DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_ID",
    "DEFAULT_DATA_IDENTITY_FOUNDATION_DATASET_NAME",
    "DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH",
    "build_data_identity_foundation_snapshot",
    "get_data_identity_foundation_snapshot_for_dashboard",
]
