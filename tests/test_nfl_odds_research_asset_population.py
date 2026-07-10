from __future__ import annotations

import json
from pathlib import Path

from src.data.nfl_p0_foundation import create_nfl_p0_storage_engine
from src.data.nfl_odds_research_asset_population import (
    build_nfl_odds_research_asset_population,
)
from src.data.nfl_results_research_asset_population import (
    build_nfl_results_research_asset_population,
)
from src.data.nfl_schedule_research_asset_population import (
    build_nfl_schedule_research_asset_population,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_odds_research_asset_snapshot_for_dashboard,
)


ODDS_ASSET_ID = "dataset.nfl.odds_snapshots"


def test_nfl_odds_asset_reuses_shared_runtime_and_certifies_joined_odds(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_odds_research_asset.sqlite"

    schedule_result = build_nfl_schedule_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )
    assert schedule_result["ok"]

    results_result = build_nfl_results_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )
    assert results_result["ok"]

    result = build_nfl_odds_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert result["ok"]
    assert result["status"] == "ready"
    assert result["profile"]["profile_id"] == "sports:nfl"
    assert result["source_bundle"]["dataset_id"] == f"{ODDS_ASSET_ID}.raw_acquisition_cache"
    assert result["source_bundle"]["provider"] == "the_odds_api"
    assert result["source_bundle"]["connector_id"] == "connector.odds_data.nfl_odds"
    assert result["source_bundle"]["provider_capability"]["provider_id"] == "the_odds_api"
    assert result["source_bundle"]["provider_capability"]["supported_assets"] == [ODDS_ASSET_ID]
    assert result["raw_acquisition_result"]["status"] == "raw_cache_ready"
    assert result["raw_acquisition_result"]["raw_record_count"] == 3
    assert result["validation"]["ok"]
    assert result["validation"]["backbone_certification"] == {
        "dataset.nfl.games": "certified",
        "dataset.sports.nfl.schedule": "certified",
        "dataset.sports.nfl.results": "certified",
    }
    assert result["join_validation"]["ok"]
    assert result["join_validation"]["matched_rows"] == 3
    assert result["research_asset_certification"]["certification_status"] == "certified"
    assert result["dataset_certification"]["certification_status"] == "certified"
    assert result["lifecycle_alignment"]["status"] == "aligned"

    row = result["normalized_rows"][0]
    assert row["asset_id"] == ODDS_ASSET_ID
    assert row["event_id"] == row["game_id"]
    assert row["book"] == "consensus"
    assert row["market"] in {"spread", "moneyline", "total"}
    assert row["snapshot_time"] <= row["decision_time"] <= row["kickoff_time"]
    assert row["field_provenance"]["book"]["source_field_name"] == "book"
    assert row["field_provenance"]["market"]["source_field_name"] == "market"
    assert row["field_provenance"]["selection"]["source_field_name"] == "selection"

    readiness = result["readiness_snapshot"]
    assert readiness["ok"]
    assert readiness["asset_id"] == ODDS_ASSET_ID
    assert readiness["lifecycle_state"] == "feature_ready"
    assert readiness["certification_status"] == "certified"
    assert readiness["dataset_certification_status"] == "certified"
    assert readiness["join_validation"]["ok"]
    assert readiness["row_count"] == 3
    assert readiness["coverage_planner_readiness"]["first_production_connector_target"] == "dataset.nfl.weather_snapshots"
    assert ODDS_ASSET_ID in readiness["coverage_planner_readiness"]["certified_required_asset_ids"]

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        raw_rows = storage.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[f"{ODDS_ASSET_ID}.raw_acquisition_cache"],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == 3
        raw_payload = json.loads(raw_rows[0]["payload_json"])
        assert raw_payload["source_table"] == "nfl_odds_snapshots"
        assert raw_payload["provider"] == "the_odds_api"
        assert "connector.odds_data.nfl_odds" in raw_rows[0]["payload_json"]

        odds_rows = storage.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")
        assert len(odds_rows) == 3
        assert odds_rows[0]["game_id"] == row["game_id"]

        asset_rows = storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=[ODDS_ASSET_ID],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == 1
        assert asset_rows[0]["certification_status"] == "certified"

        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[ODDS_ASSET_ID],
        )
        assert lifecycle_rows
        assert lifecycle_rows[-1]["lifecycle_state"] == "feature_ready"

        alignment_rows = storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=[ODDS_ASSET_ID],
        )
        assert alignment_rows
        assert alignment_rows[-1]["alignment_status"] == "aligned"
    finally:
        storage.close()

    dashboard = get_nfl_odds_research_asset_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard["ok"]
    assert dashboard["asset_id"] == ODDS_ASSET_ID
    assert dashboard["lifecycle_state"] == "feature_ready"
    assert dashboard["join_validation"]["ok"]


def test_nfl_odds_certification_is_blocked_without_certified_backbone(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_odds_without_backbone.sqlite"

    result = build_nfl_odds_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert "schedule_backbone_not_certified" in result["validation"]["errors"]
    assert "results_backbone_not_certified" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"
