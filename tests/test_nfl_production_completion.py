from __future__ import annotations

import importlib
from pathlib import Path

from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.market_intelligence.nfl_production_completion import (
    build_nfl_production_completion_snapshot,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_production_completion_snapshot_for_dashboard as get_nfl_production_completion_snapshot_for_dashboard_service,
)
from src.storage.local_store import create_local_storage_engine
from tests.test_pipeline_validation import _build_phase55_chain


def test_nfl_production_completion_certifies_the_canonical_nfl_scope(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_production_completion.sqlite"
    artifact_root = tmp_path / "nfl_production_completion_artifacts"
    _build_phase55_chain(storage_path)

    snapshot = build_nfl_production_completion_snapshot(
        storage_path=storage_path,
        artifact_root=artifact_root,
    )

    assert snapshot["ok"] is True
    assert snapshot["status"] == "completed"
    assert snapshot["readiness"] == "covariance_and_time_dependent_risk_audit_ready"
    assert snapshot["lifecycle_state"] == "nfl_production_complete"
    assert snapshot["validation_state"] == "validated"
    assert snapshot["reference_profile_id"] == "sports:nfl"
    assert snapshot["next_governed_phase"] == "Covariance and Time-Dependent Risk Capability Audit"
    assert snapshot["nfl_reference_parity"]["ok"] is True
    assert snapshot["production_gap_register"]["blocking_gaps"] == []
    assert snapshot["artifact_integrity_ok"] is True
    assert snapshot["reporting_surface_summary"]["current_artifact_integrity_ok"] is True
    assert snapshot["validation_summary"]["error_check_count"] == 16
    assert snapshot["validation_summary"]["error_checks_passed"] == 16

    results = {
        row["requirement_id"]: row
        for row in snapshot["production_audit_results"]
    }
    expected_requirements = {
        "certified_research_assets",
        "historical_data_coverage",
        "feature_coverage",
        "mathematical_outputs",
        "signals",
        "decision_rows",
        "baseline_backtesting",
        "pipeline_validation",
        "research_intelligence",
        "nfl_reference_parity",
        "dashboard_surfaces",
        "reporting_surfaces",
        "query_surfaces",
        "evidence_packages",
        "documentation",
        "production_readiness_blockers",
    }
    assert expected_requirements == set(results)
    assert all(
        row["classification"] == "complete_and_validated"
        for row in results.values()
    )

    artifact_refs = snapshot["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()

    storage = create_local_storage_engine(storage_path)
    try:
        assert storage.count("nfl_production_completion_runs") >= 1
        assert storage.count("nfl_production_completion_audit_items") >= len(expected_requirements)
    finally:
        storage.close()


def test_nfl_production_completion_updates_p0_readiness_and_service_exports(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_production_completion_p0.sqlite"
    _build_phase55_chain(storage_path)

    snapshot = build_nfl_production_completion_snapshot(storage_path=storage_path)
    p0_snapshot = build_nfl_p0_dashboard_snapshot(storage_path)
    service_snapshot = get_nfl_production_completion_snapshot_for_dashboard_service(
        storage_path=storage_path
    )

    assert p0_snapshot["universal_market_framework_layer_readiness"]["status"] == "completed"
    assert p0_snapshot["nfl_production_completion_layer_readiness"]["status"] == "completed"
    assert (
        p0_snapshot["nfl_production_completion_layer_readiness"]["next_governed_phase"]
        == "Covariance and Time-Dependent Risk Capability Audit"
    )
    assert p0_snapshot["readiness_summary"]["nfl_production_completion_status"] == "completed"
    assert (
        service_snapshot["nfl_production_completion_run_id"]
        == snapshot["nfl_production_completion_run_id"]
    )

    module = importlib.import_module("src.market_intelligence")
    assert callable(module.build_nfl_production_completion_snapshot)
    assert callable(module.get_nfl_production_completion_snapshot_for_dashboard)
    assert callable(get_nfl_production_completion_snapshot_for_dashboard_service)

