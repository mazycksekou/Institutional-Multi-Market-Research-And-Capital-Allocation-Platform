from __future__ import annotations

import json
from pathlib import Path

from src.data.nfl_p0_foundation import create_nfl_p0_storage_engine
from src.data.nfl_results_research_asset_population import (
    build_nfl_results_research_asset_population,
)
from src.data.nfl_schedule_research_asset_population import (
    build_nfl_schedule_research_asset_population,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_results_research_asset_snapshot_for_dashboard,
)


RESULTS_ASSET_ID = "dataset.sports.nfl.results"


def test_nfl_results_asset_reuses_schedule_connector_and_certifies_joined_results(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_results_research_asset.sqlite"
    schedule_result = build_nfl_schedule_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )
    assert schedule_result["ok"]

    result = build_nfl_results_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert result["ok"]
    assert result["status"] == "ready"
    assert result["profile"]["profile_id"] == "sports:nfl"
    assert result["source_bundle"]["dataset_id"] == f"{RESULTS_ASSET_ID}.raw_acquisition_cache"
    assert result["source_bundle"]["connector_id"] == "connector.feeds.nfl_schedule"
    assert result["source_bundle"]["provider"] == "nflverse"
    assert result["source_bundle"]["provider_capability"]["supported_assets"] == [RESULTS_ASSET_ID]
    assert result["raw_acquisition_result"]["status"] == "raw_cache_ready"
    assert result["raw_acquisition_result"]["raw_record_count"] == 1
    assert result["validation"]["ok"]
    assert result["validation"]["backbone_certification"] == {
        "dataset.nfl.games": "certified",
        "dataset.sports.nfl.schedule": "certified",
    }
    assert result["join_validation"]["ok"]
    assert result["join_validation"]["matched_rows"] == 1
    assert result["research_asset_certification"]["certification_status"] == "certified"
    assert result["dataset_certification"]["certification_status"] == "certified"
    assert result["lifecycle_alignment"]["status"] == "aligned"

    row = result["normalized_rows"][0]
    assert row["asset_id"] == RESULTS_ASSET_ID
    assert row["event_id"] == row["game_id"]
    assert row["final_home_score"] == row["final_score_home"]
    assert row["final_away_score"] == row["final_score_away"]
    assert row["game_completed"] == 1
    assert row["completion_timestamp"] >= row["scheduled_time"]
    assert row["field_provenance"]["final_home_score"]["source_field_name"] == "final_score_home"
    assert row["field_provenance"]["winning_team"]["source_field_name"] == "winner_team"

    readiness = result["readiness_snapshot"]
    assert readiness["ok"]
    assert readiness["asset_id"] == RESULTS_ASSET_ID
    assert readiness["lifecycle_state"] == "feature_ready"
    assert readiness["certification_status"] == "certified"
    assert readiness["dataset_certification_status"] == "certified"
    assert readiness["join_validation"]["ok"]
    assert readiness["row_count"] == 1
    assert readiness["coverage_planner_readiness"]["first_production_connector_target"] == "dataset.nfl.odds_snapshots"
    assert RESULTS_ASSET_ID in readiness["coverage_planner_readiness"]["certified_required_asset_ids"]

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        raw_rows = storage.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[f"{RESULTS_ASSET_ID}.raw_acquisition_cache"],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == 1
        raw_payload = json.loads(raw_rows[0]["payload_json"])
        assert raw_payload["source_table"] == "nfl_results"
        assert "connector.feeds.nfl_schedule" in raw_payload["context_json"]

        results_rows = storage.fetch("nfl_results", order_by="result_id ASC")
        assert len(results_rows) == 1
        assert results_rows[0]["game_id"] == row["game_id"]

        asset_rows = storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=[RESULTS_ASSET_ID],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == 1
        assert asset_rows[0]["certification_status"] == "certified"

        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[RESULTS_ASSET_ID],
        )
        assert len(lifecycle_rows) == 1
        assert lifecycle_rows[0]["lifecycle_state"] == "feature_ready"

        alignment_rows = storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=[RESULTS_ASSET_ID],
        )
        assert len(alignment_rows) == 1
        assert alignment_rows[0]["alignment_status"] == "aligned"
    finally:
        storage.close()

    dashboard = get_nfl_results_research_asset_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard["ok"]
    assert dashboard["asset_id"] == RESULTS_ASSET_ID
    assert dashboard["lifecycle_state"] == "feature_ready"
    assert dashboard["join_validation"]["ok"]


def test_nfl_results_certification_is_blocked_without_certified_schedule(tmp_path: Path) -> None:
    storage_path = tmp_path / "results_without_schedule.sqlite"

    result = build_nfl_results_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert "schedule_join_alignment_failed" in result["validation"]["errors"]
    assert "schedule_backbone_not_certified" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"
