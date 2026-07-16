from __future__ import annotations

import importlib
from pathlib import Path

from src.market_intelligence.universal_market_framework import (
    build_universal_market_framework_snapshot,
)
from src.services.streamlit_dashboard_data import (
    get_universal_market_framework_snapshot_for_dashboard as get_universal_market_framework_snapshot_for_dashboard_service,
)
from tests.test_pipeline_validation import _build_phase55_chain


def test_universal_market_framework_preserves_certified_nfl_reference_parity(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "universal_market_framework.sqlite"
    artifact_root = tmp_path / "umf_artifacts"
    _build_phase55_chain(storage_path)

    snapshot = build_universal_market_framework_snapshot(
        storage_path=storage_path,
        artifact_root=artifact_root,
    )

    assert snapshot["ok"] is True
    assert snapshot["status"] == "completed"
    assert snapshot["readiness"] == "first_market_profile_onboarding_ready"
    assert snapshot["lifecycle_state"] == "universal_market_framework_ready"
    assert snapshot["reference_profile_id"] == "sports:nfl"
    assert snapshot["unresolved_blockers"] == []
    assert snapshot["validation_summary"]["error_check_count"] == 5
    assert snapshot["validation_summary"]["error_checks_passed"] == 5

    assert snapshot["nfl_reference_parity"]["ok"] is True
    assert snapshot["nfl_reference_parity"]["research_intelligence_run_id"]
    assert snapshot["nfl_reference_parity"]["pipeline_validation_run_id"]
    assert snapshot["nfl_reference_parity"]["backtest_run_id"]
    assert snapshot["nfl_reference_parity"]["decision_batch_id"]
    assert snapshot["nfl_reference_parity"]["sample_size"] == 3
    assert snapshot["nfl_reference_parity"]["roi_percent"] == 20.0
    assert (
        snapshot["certified_pipeline_reference"]["decision_batch_id"]
        == snapshot["nfl_reference_parity"]["decision_batch_id"]
    )

    profile_states = {
        row["profile_id"]: row["activation_state"]
        for row in snapshot["profile_contract_registry"]
    }
    assert profile_states["sports:nfl"] == "reference_implementation"
    assert profile_states["sports"] == "framework_family_contract"
    assert profile_states["prediction_markets"] == "roadmap_only_contract"
    assert profile_states["options_0dte"] == "roadmap_only_contract"

    forbidden = snapshot["forbidden_activation_summary"]
    assert forbidden["new_market_implementations_added"] is False
    assert forbidden["new_connectors_or_providers_added"] is False
    assert forbidden["paper_or_live_execution_added"] is False
    assert forbidden["capital_allocation_added"] is False

    artifact_refs = snapshot["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()
    assert snapshot["artifact_integrity_ok"] is True


def test_universal_market_framework_package_exports_are_available() -> None:
    module = importlib.import_module("src.market_intelligence")
    assert callable(module.build_universal_market_framework_snapshot)
    assert callable(module.get_universal_market_framework_snapshot_for_dashboard)
    assert callable(get_universal_market_framework_snapshot_for_dashboard_service)
