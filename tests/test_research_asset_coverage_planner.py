from __future__ import annotations

from pathlib import Path

from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_population
from src.market_intelligence.research_asset_coverage_planner import build_research_asset_coverage_planner_snapshot
from src.services.streamlit_dashboard_data import get_research_asset_coverage_planner_snapshot_for_dashboard


def test_research_asset_coverage_planner_prioritizes_the_certified_schedule_asset(tmp_path: Path) -> None:
    storage_path = tmp_path / "coverage_planner.sqlite"

    population_result = build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)
    assert population_result["ok"]
    assert population_result["readiness_snapshot"]["asset_id"] == "dataset.sports.nfl.schedule"

    snapshot = build_research_asset_coverage_planner_snapshot(storage_path=storage_path)

    assert snapshot["ok"]
    assert snapshot["status"] == "partial"
    assert snapshot["schema_version"] == "src.market_intelligence.research_asset_coverage_planner.v1"
    assert snapshot["profile"]["profile_id"] == "sports:nfl"

    gap_engine = snapshot["coverage_gap_engine"]
    assert gap_engine["first_production_connector_target"] == "dataset.sports.nfl.results"
    assert gap_engine["missing_asset_count"] >= 1
    assert gap_engine["minimum_schema_completion_percentage"] < 100.0
    assert "dataset.sports.nfl.results" in gap_engine["missing_required_asset_ids"]
    assert gap_engine["next_acquisition_targets"][0]["target_type"] == "missing_required_asset"
    assert gap_engine["next_acquisition_targets"][0]["research_asset_ids"] == ["dataset.sports.nfl.results"]

    asset_registry = snapshot["research_asset_coverage_registry"]
    schedule_rows = [row for row in asset_registry if row["research_asset_id"] == "dataset.sports.nfl.schedule"]
    assert len(schedule_rows) == 1
    schedule_row = schedule_rows[0]
    assert schedule_row["certification_state"] == "certified"
    assert schedule_row["readiness_state"] == "ready"
    assert schedule_row["current_source_role"] == "nflverse"
    assert schedule_row["recommended_primary_provider"] in {"nflverse", "nflreadr", "nflfastr", "manual_schedule_import"}
    assert schedule_row["completion_percentage"] >= 100.0
    assert "nflverse" in schedule_row["provider_bundle"]["selected_provider_ids"]

    provider_registry = snapshot["provider_coverage_registry"]
    provider_ids = {row["provider_id"] for row in provider_registry}
    assert {"nflverse", "nflreadr", "nflfastr", "the_odds_api", "open_meteo"}.issubset(provider_ids)
    assert any(row["future_candidate"] for row in provider_registry)

    worldview_surface = snapshot["worldview_query_surface"]
    query_surface = [prompt.lower() for prompt in worldview_surface["query_surface"]]
    assert "what assets are missing?" in query_surface
    assert "which datasets are certified?" in query_surface
    assert "why is this dataset blocked?" in query_surface
    assert "what connector would close this gap?" in query_surface

    planner_readiness = snapshot["planner_readiness"]
    assert planner_readiness["status"] == "partial"
    assert planner_readiness["first_production_connector_target"] == "dataset.sports.nfl.results"

    dashboard_snapshot = get_research_asset_coverage_planner_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard_snapshot["ok"]
    assert dashboard_snapshot["dashboard_ready"]
    assert dashboard_snapshot["coverage_planner_readiness"]["first_production_connector_target"] == "dataset.sports.nfl.results"
