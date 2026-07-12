from __future__ import annotations

import importlib
from pathlib import Path

from src.data import (
    build_math_engine_population,
    build_math_engine_population_dashboard_snapshot,
    get_math_engine_population_snapshot_for_dashboard,
)
from src.data.historical_research_database import build_historical_dataset_population
from src.data.nfl_injuries_research_asset_population import build_nfl_injuries_research_asset_population
from src.data.nfl_odds_research_asset_population import build_nfl_odds_research_asset_population
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.data.nfl_results_research_asset_population import build_nfl_results_research_asset_population
from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_population
from src.data.nfl_team_statistics_research_asset_population import build_nfl_team_statistics_research_asset_population
from src.data.nfl_weather_research_asset_population import build_nfl_weather_research_asset_population
from src.data.feature_registry import build_feature_snapshot_population
from src.data.math_engine_population import (
    DEFAULT_MATH_ENGINE_DATASET_ID,
    DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
    list_math_engine_definition_ids,
)


def _build_phase50_sources(storage_path: Path) -> None:
    for builder in (
        build_nfl_schedule_research_asset_population,
        build_nfl_results_research_asset_population,
        build_nfl_odds_research_asset_population,
        build_nfl_weather_research_asset_population,
        build_nfl_injuries_research_asset_population,
        build_nfl_team_statistics_research_asset_population,
    ):
        result = builder(storage_path=storage_path, game_count=1)
        assert result["ok"] is True

    dataset_result = build_historical_dataset_population(storage_path=storage_path)
    assert dataset_result["ok"] is True

    feature_result = build_feature_snapshot_population(storage_path=storage_path)
    assert feature_result["ok"] is True


def test_math_engine_population_materializes_reusable_engine_rows_and_reuses_persisted_state(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "math_population.sqlite"
    _build_phase50_sources(storage_path)

    first = build_math_engine_population(storage_path=storage_path)
    second = build_math_engine_population(storage_path=storage_path)
    dashboard = build_math_engine_population_dashboard_snapshot(storage_path=storage_path)
    service_dashboard = get_math_engine_population_snapshot_for_dashboard(storage_path)
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert first["ok"] is True
    assert first["status"] == "certified"
    assert first["dataset_id"] == DEFAULT_MATH_ENGINE_DATASET_ID
    assert first["engine_definition_count"] == len(list_math_engine_definition_ids())
    assert first["engine_row_count"] == 27
    assert first["dataset_row_count"] == 3
    assert first["math_engine_context_count"] == 3
    assert first["math_engine_validation"]["ok"] is True
    assert first["math_engine_alignment_rows"]
    assert all(row["status"] == "aligned" for row in first["math_engine_alignment_rows"])
    assert first["dataset_certification_status"] == "certified"
    assert first["lifecycle_state"] == "math_ready"

    assert second["ok"] is True
    assert second["status"] == "ready" or second["status"] == "certified"
    assert second["batch_id"] == first["batch_id"]
    assert second["math_engine_population_summary_id"] == first["math_engine_population_summary_id"]
    assert [row["snapshot_id"] for row in second["math_engine_rows"]] == [row["snapshot_id"] for row in first["math_engine_rows"]]
    assert second["idempotent_reuse"] is True
    assert second["math_engine_validation"]["ok"] is True

    assert dashboard["ok"] is True
    assert dashboard["status"] == "ready"
    assert dashboard["batch_id"] == first["batch_id"]
    assert dashboard["math_engine_population_summary_id"] == first["math_engine_population_summary_id"]
    assert dashboard["engine_row_count"] == 27
    assert dashboard["dataset_certification_status"] == "certified"
    assert dashboard["lifecycle_state"] == "math_ready"
    assert service_dashboard["ok"] is True
    assert service_dashboard["status"] == "ready"
    assert service_dashboard["batch_id"] == first["batch_id"]
    assert service_dashboard["math_engine_population_summary_id"] == first["math_engine_population_summary_id"]
    assert service_dashboard["math_engine_row_count"] == 27
    assert len(dashboard["math_engine_lineage_edges"]) == 27

    assert p0_dashboard["math_layer_readiness"]["status"] == "ready"
    assert p0_dashboard["math_layer_readiness"]["engine_row_count"] == 27
    assert p0_dashboard["math_layer_readiness"]["dataset_certification_status"] == "certified"
    assert p0_dashboard["readiness_summary"]["math_engine_population_status"] == "ready"


def test_math_engine_population_package_exports_are_available() -> None:
    module = importlib.import_module("src.data")
    assert callable(module.build_math_engine_population)
    assert callable(module.build_math_engine_population_dashboard_snapshot)
    assert callable(module.get_math_engine_population_snapshot_for_dashboard)
    assert module.DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID == DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID
