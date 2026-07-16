from __future__ import annotations

import importlib
from pathlib import Path

from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.market_intelligence.research_intelligence import build_research_intelligence_snapshot
from src.services.streamlit_dashboard_data import (
    get_research_intelligence_snapshot_for_dashboard as get_research_intelligence_snapshot_for_dashboard_service,
)
from src.storage import LocalStorageEngine
from tests.test_pipeline_validation import _build_phase55_chain


def test_research_intelligence_builds_deterministic_snapshot_from_certified_pipeline(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "research_intelligence.sqlite"
    _build_phase55_chain(storage_path)

    snapshot = build_research_intelligence_snapshot(storage_path=storage_path)
    service_snapshot = get_research_intelligence_snapshot_for_dashboard_service(storage_path)
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert snapshot["ok"] is True
    assert snapshot["status"] == "completed"
    assert snapshot["readiness"] == "universal_market_framework_ready"
    assert snapshot["lifecycle_state"] == "research_intelligence_ready"
    assert snapshot["validation_state"] == "validated"
    assert snapshot["validation_summary"]["error_check_count"] == 14
    assert snapshot["validation_summary"]["error_checks_passed"] == 14
    assert snapshot["validation_summary"]["warning_check_count"] == 1
    assert snapshot["validation_summary"]["warning_checks_passed"] == 1
    assert snapshot["unresolved_blockers"] == []

    assert snapshot["research_summary"]["sample_size"] == 3
    assert snapshot["research_summary"]["wins"] == 2
    assert snapshot["research_summary"]["losses"] == 1
    assert snapshot["research_summary"]["pushes"] == 0
    assert snapshot["research_summary"]["roi_percent"] == 20.0

    assert len(snapshot["opportunity_summaries"]) == 3
    assert len(snapshot["supporting_evidence_packages"]) == 3
    assert [row["market_type"] for row in snapshot["opportunity_summaries"]] == [
        "spread",
        "moneyline",
        "total",
    ]
    assert snapshot["signal_agreement_summary"]["agreement_state_counts"]
    assert snapshot["feature_contribution_summary"]["family_counts"]["data_quality_context"] > 0

    artifact_refs = snapshot["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()
    assert snapshot["artifact_integrity_ok"] is True

    assert service_snapshot["ok"] is True
    assert service_snapshot["research_intelligence_run_id"] == snapshot["research_intelligence_run_id"]
    assert service_snapshot["artifact_references"] == artifact_refs

    assert p0_dashboard["research_intelligence_layer_readiness"]["status"] == "completed"
    assert p0_dashboard["research_intelligence_layer_readiness"]["readiness"] == "universal_market_framework_ready"
    assert p0_dashboard["research_intelligence_layer_readiness"]["artifact_integrity_ok"] is True
    assert p0_dashboard["research_intelligence_layer_readiness"]["error_check_count"] == 14
    assert p0_dashboard["research_intelligence_layer_readiness"]["error_checks_passed"] == 14
    assert p0_dashboard["readiness_summary"]["research_intelligence_status"] == "completed"


def test_research_intelligence_blocks_when_pipeline_validation_is_tampered(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "research_intelligence_tampered.sqlite"
    _build_phase55_chain(storage_path)

    storage = LocalStorageEngine(storage_path)
    try:
        summary_row = dict(
            storage.fetch(
                "feature_snapshots",
                where="snapshot_kind = ?",
                params=["feature_population_summary"],
                order_by="created_at ASC, snapshot_id ASC",
                limit=1,
            )[0]
        )
        summary_row["dataset_batch_id"] = "tampered.feature.dataset_batch"
        storage.upsert("feature_snapshots", summary_row, key_columns=("snapshot_id",))
    finally:
        storage.close()

    snapshot = build_research_intelligence_snapshot(storage_path=storage_path)

    assert snapshot["ok"] is False
    assert snapshot["status"] == "blocked"
    assert snapshot["readiness"] == "blocked"
    assert "pipeline_validation:pipeline_validation_ready" in snapshot["unresolved_blockers"]
    failed_check = next(
        check
        for check in snapshot["validation_checks"]
        if check["check_id"] == "pipeline_validation_ready"
    )
    assert failed_check["ok"] is False
    assert failed_check["actual"] == "blocked / blocked"


def test_research_intelligence_package_exports_are_available() -> None:
    module = importlib.import_module("src.market_intelligence")
    assert callable(module.build_research_intelligence_snapshot)
    assert callable(module.get_research_intelligence_snapshot_for_dashboard)
    assert callable(get_research_intelligence_snapshot_for_dashboard_service)
