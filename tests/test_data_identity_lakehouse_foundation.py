from __future__ import annotations

import importlib
from pathlib import Path

from src.data.data_identity_lakehouse import DataIdentityLakehouseRuntime
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.market_intelligence.data_identity_lakehouse_foundation import (
    build_data_identity_foundation_snapshot,
)
from src.services.streamlit_dashboard_data import (
    get_data_identity_foundation_snapshot_for_dashboard as get_data_identity_foundation_snapshot_for_dashboard_service,
)
from src.storage.local_store import create_local_storage_engine
from tests.test_pipeline_validation import _build_phase55_chain


def test_data_identity_foundation_completes_and_persists_lakehouse_readiness(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "data_identity_foundation.sqlite"
    artifact_root = tmp_path / "data_identity_foundation_artifacts"
    lakehouse_root = tmp_path / "lakehouse"
    _build_phase55_chain(storage_path)

    snapshot = build_data_identity_foundation_snapshot(
        storage_path=storage_path,
        artifact_root=artifact_root,
        lakehouse_root=lakehouse_root,
    )

    assert snapshot["ok"] is True
    assert snapshot["status"] == "completed"
    assert snapshot["readiness"] == "first_controlled_nfl_vendor_ingest_ready"
    assert snapshot["lifecycle_state"] == "data_identity_lakehouse_foundation_complete"
    assert snapshot["validation_state"] == "validated"
    assert snapshot["reference_profile_id"] == "sports:nfl"
    assert snapshot["next_governed_phase"] == "First Controlled NFL Vendor Ingest"
    assert snapshot["nfl_parity_status"]["ok"] is True
    assert snapshot["first_vendor_ingest_readiness"]["status"] == "ready"
    assert snapshot["artifact_integrity_ok"] is True
    assert snapshot["parquet_readiness"]["partition_count"] > 0
    assert snapshot["parquet_readiness"]["roundtrip_ok"] is True
    assert snapshot["bronze_silver_gold_readiness"]["status"] == "ready"
    assert snapshot["identity_resolution_readiness"]["approved_mapping_count"] > 0
    assert snapshot["reconciliation_readiness"]["reconciliation_result_count"] > 0
    assert snapshot["validation_summary"]["error_check_count"] >= 12
    assert (
        snapshot["validation_summary"]["error_checks_passed"]
        == snapshot["validation_summary"]["error_check_count"]
    )

    results = {
        row["requirement_id"]: row
        for row in snapshot["capability_audit_matrix"]
    }
    expected_requirements = {
        "canonical_identity_foundation",
        "matching",
        "reconciliation",
        "point_in_time_and_revision_contract",
        "quality_quarantine_review",
        "bronze_silver_gold_mapping",
        "parquet_analytical_storage",
        "delta_compatible_interfaces",
        "security_and_governance",
        "readiness_surfaces",
    }
    assert expected_requirements == set(results)
    assert all(
        row["final_classification"] == "complete_and_validated"
        for row in results.values()
    )

    artifact_refs = snapshot["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()

    storage = create_local_storage_engine(storage_path)
    try:
        assert storage.count("data_identity_foundation_runs") >= 1
        assert storage.count("data_identity_foundation_audit_items") >= len(expected_requirements)
        assert storage.count("identity_mappings") > 0
        assert storage.count("identity_reconciliation_results") > 0
        assert storage.count("lakehouse_partitions") > 0
    finally:
        storage.close()


def test_data_identity_runtime_preserves_revisions_and_blocks_ambiguous_matches(
    tmp_path: Path,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        first = runtime.register_identity_mapping(
            provider="seed_vendor",
            external_identifier="ACME",
            internal_identifier="company::acme",
            entity_type="company",
            entity_name="ACME Holdings",
            approval_evidence={"seed": True},
        )
        repeated = runtime.register_identity_mapping(
            provider="seed_vendor",
            external_identifier="ACME",
            internal_identifier="company::acme",
            entity_type="company",
            entity_name="ACME Holdings",
            approval_evidence={"seed": True},
        )
        changed = runtime.register_identity_mapping(
            provider="seed_vendor",
            external_identifier="ACME",
            internal_identifier="company::acme.v2",
            entity_type="company",
            entity_name="ACME Holdings Renamed",
            approval_evidence={"seed": True, "revision": 2},
        )

        assert repeated["mapping_id"] == first["mapping_id"]
        assert changed["mapping_id"] != first["mapping_id"]
        latest_rows = runtime.store.fetch(
            "identity_mappings",
            where="provider = ? AND entity_type = ? AND external_identifier = ?",
            params=["seed_vendor", "company", "ACME"],
            order_by="revision_number ASC",
        )
        assert len(latest_rows) == 2
        assert latest_rows[0]["mapping_status"] == "superseded"
        assert int(latest_rows[0]["is_latest"] or 0) == 0
        assert latest_rows[1]["mapping_status"] == "accepted"
        assert int(latest_rows[1]["is_latest"] or 0) == 1

        resolution = runtime.resolve_identity_mapping(
            entity_type="team",
            provider="seed_vendor",
            external_identifier="Springfield Isotopes",
            source_row={"entity_name": "Springfield Isotopes"},
            candidate_rows=[
                {"internal_identifier": "team::home", "entity_name": "Springfield Isotopes A"},
                {"internal_identifier": "team::away", "entity_name": "Springfield Isotopes B"},
            ],
            normalized_fields=("entity_name",),
        )

        assert resolution["accepted"] is False
        assert resolution["decision_status"] == "manual_review"
        assert resolution["match_method"] == "manual_review"
        assert runtime.store.count("manual_review_queue") >= 1
        assert runtime.store.count("quarantine_records") >= 1
    finally:
        runtime.close()


def test_data_identity_foundation_updates_p0_and_service_exports(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "data_identity_foundation_p0.sqlite"
    _build_phase55_chain(storage_path)

    snapshot = build_data_identity_foundation_snapshot(storage_path=storage_path)
    p0_snapshot = build_nfl_p0_dashboard_snapshot(storage_path)
    service_snapshot = get_data_identity_foundation_snapshot_for_dashboard_service(
        storage_path=storage_path
    )

    assert p0_snapshot["nfl_production_completion_layer_readiness"]["status"] == "completed"
    assert p0_snapshot["data_identity_foundation_layer_readiness"]["status"] == "completed"
    assert (
        p0_snapshot["data_identity_foundation_layer_readiness"]["next_governed_phase"]
        == "First Controlled NFL Vendor Ingest"
    )
    assert p0_snapshot["readiness_summary"]["data_identity_foundation_status"] == "completed"
    assert (
        service_snapshot["data_identity_foundation_run_id"]
        == snapshot["data_identity_foundation_run_id"]
    )

    module = importlib.import_module("src.market_intelligence")
    assert callable(module.build_data_identity_foundation_snapshot)
    assert callable(module.get_data_identity_foundation_snapshot_for_dashboard)
    assert callable(get_data_identity_foundation_snapshot_for_dashboard_service)
