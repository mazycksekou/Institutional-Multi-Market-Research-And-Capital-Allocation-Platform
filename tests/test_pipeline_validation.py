from __future__ import annotations

import importlib
from pathlib import Path

from src.backtesting import build_pipeline_validation_snapshot
from src.backtesting.baseline_backtesting import run_baseline_backtest
from src.backtesting.decision_row_population import build_decision_row_population
from src.data.feature_registry import (
    FEATURE_SNAPSHOT_BATCH_KIND,
    build_feature_snapshot_population,
    build_feature_snapshot_population_dashboard_snapshot,
)
from src.data.historical_research_database import build_historical_dataset_population
from src.data.math_engine_population import build_math_engine_population
from src.data.nfl_injuries_research_asset_population import build_nfl_injuries_research_asset_population
from src.data.nfl_odds_research_asset_population import build_nfl_odds_research_asset_population
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.data.nfl_results_research_asset_population import build_nfl_results_research_asset_population
from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_population
from src.data.nfl_team_statistics_research_asset_population import build_nfl_team_statistics_research_asset_population
from src.data.nfl_weather_research_asset_population import build_nfl_weather_research_asset_population
from src.market_intelligence.signal_population import build_signal_population
from src.services.streamlit_dashboard_data import (
    get_pipeline_validation_snapshot_for_dashboard as get_pipeline_validation_snapshot_for_dashboard_service,
)
from src.storage import LocalStorageEngine


def _build_phase55_chain(storage_path: Path) -> None:
    for builder in (
        build_nfl_schedule_research_asset_population,
        build_nfl_results_research_asset_population,
        build_nfl_odds_research_asset_population,
        build_nfl_weather_research_asset_population,
        build_nfl_injuries_research_asset_population,
        build_nfl_team_statistics_research_asset_population,
    ):
        assert builder(storage_path=storage_path, game_count=1)["ok"] is True

    assert build_historical_dataset_population(storage_path=storage_path)["ok"] is True
    assert build_feature_snapshot_population(storage_path=storage_path)["ok"] is True
    assert build_math_engine_population(storage_path=storage_path)["ok"] is True
    assert build_signal_population(storage_path=storage_path)["ok"] is True
    assert build_decision_row_population(storage_path=storage_path)["ok"] is True
    assert run_baseline_backtest(storage_path=storage_path)["ok"] is True


def test_pipeline_validation_certifies_full_nfl_chain_and_surfaces_dashboard_readiness(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "pipeline_validation.sqlite"
    _build_phase55_chain(storage_path)

    feature_snapshot = build_feature_snapshot_population_dashboard_snapshot(storage_path=storage_path)
    validation = build_pipeline_validation_snapshot(storage_path=storage_path)
    service_validation = get_pipeline_validation_snapshot_for_dashboard_service(storage_path)
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert feature_snapshot["dataset_certification_status"] == "certified"
    assert feature_snapshot["dataset_certification_id"]
    assert feature_snapshot["lifecycle_state"] == "feature_ready"
    assert feature_snapshot["point_in_time_validation_status"] == "safe"

    assert validation["ok"] is True
    assert validation["status"] == "certified"
    assert validation["readiness"] == "research_intelligence_ready"
    assert validation["lifecycle_state"] == "validation_complete"
    assert validation["validation_summary"]["error_check_count"] == 32
    assert validation["validation_summary"]["error_checks_passed"] == 32
    assert validation["validation_summary"]["warning_check_count"] == 1
    assert validation["validation_summary"]["warning_checks_passed"] == 1
    assert validation["unresolved_blockers"] == []
    assert validation["performance_summary"]["sample_size"] == 3
    assert validation["performance_summary"]["roi_percent"] == 20.0

    artifact_refs = validation["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()
    assert validation["artifact_integrity_ok"] is True

    assert service_validation["ok"] is True
    assert service_validation["pipeline_validation_run_id"] == validation["pipeline_validation_run_id"]
    assert service_validation["artifact_references"] == artifact_refs

    assert p0_dashboard["pipeline_validation_layer_readiness"]["status"] == "certified"
    assert p0_dashboard["pipeline_validation_layer_readiness"]["readiness"] == "research_intelligence_ready"
    assert p0_dashboard["pipeline_validation_layer_readiness"]["artifact_integrity_ok"] is True
    assert p0_dashboard["pipeline_validation_layer_readiness"]["error_check_count"] == 32
    assert p0_dashboard["pipeline_validation_layer_readiness"]["error_checks_passed"] == 32
    assert p0_dashboard["readiness_summary"]["pipeline_validation_status"] == "certified"


def test_pipeline_validation_blocks_when_feature_source_dataset_batch_is_tampered(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "pipeline_validation_tampered.sqlite"
    _build_phase55_chain(storage_path)

    storage = LocalStorageEngine(storage_path)
    try:
        summary_row = dict(
            storage.fetch(
                "feature_snapshots",
                where="snapshot_kind = ?",
                params=[FEATURE_SNAPSHOT_BATCH_KIND],
                order_by="created_at ASC, snapshot_id ASC",
                limit=1,
            )[0]
        )
        summary_row["dataset_batch_id"] = "tampered.feature.dataset_batch"
        storage.upsert("feature_snapshots", summary_row, key_columns=("snapshot_id",))
    finally:
        storage.close()

    validation = build_pipeline_validation_snapshot(storage_path=storage_path)

    assert validation["ok"] is False
    assert validation["status"] == "blocked"
    assert "feature:feature_source_dataset_batch_match" in validation["unresolved_blockers"]
    failed_check = next(
        check
        for check in validation["validation_checks"]
        if check["check_id"] == "feature_source_dataset_batch_match"
    )
    assert failed_check["ok"] is False
    assert failed_check["actual"] == "tampered.feature.dataset_batch"


def test_pipeline_validation_package_exports_are_available() -> None:
    module = importlib.import_module("src.backtesting")
    assert callable(module.build_pipeline_validation_snapshot)
    assert callable(module.get_pipeline_validation_snapshot_for_dashboard)
    assert callable(get_pipeline_validation_snapshot_for_dashboard_service)
