from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from src.data.nfl_injuries_research_asset_population import (
    DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
    build_nfl_injuries_connector_bundle,
    build_nfl_injuries_research_asset_population,
)
from src.data.nfl_odds_research_asset_population import (
    build_nfl_odds_research_asset_population,
)
from src.data.nfl_p0_foundation import create_nfl_p0_storage_engine
from src.data.nfl_results_research_asset_population import (
    build_nfl_results_research_asset_population,
)
from src.data.nfl_schedule_research_asset_population import (
    build_nfl_schedule_research_asset_population,
)
from src.data.nfl_weather_research_asset_population import (
    build_nfl_weather_research_asset_population,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_injuries_research_asset_snapshot_for_dashboard,
)


def _parse_iso(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_nfl_injuries_asset_reuses_shared_runtime_and_certifies_joined_injuries(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_injuries_research_asset.sqlite"

    assert build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_results_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_odds_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_weather_research_asset_population(storage_path=storage_path, game_count=1)["ok"]

    result = build_nfl_injuries_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert result["ok"]
    assert result["status"] == "ready"
    assert result["profile"]["profile_id"] == "sports:nfl"
    assert result["source_bundle"]["dataset_id"] == f"{DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID}.raw_acquisition_cache"
    assert result["source_bundle"]["provider"] == "nflverse_injuries"
    assert result["source_bundle"]["connector_id"] == "connector.feeds.nfl_injuries"
    assert result["source_bundle"]["source_type"] == "injury_fixture"
    assert result["source_bundle"]["provider_capability"]["provider_id"] == "nflverse_injuries"
    assert result["source_bundle"]["provider_capability"]["supported_assets"] == [DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID]
    assert "manual_import" in result["source_bundle"]["manual_evidence_paths"]
    assert result["raw_acquisition_result"]["status"] == "raw_cache_ready"
    assert result["raw_acquisition_result"]["raw_record_count"] == 2
    assert result["validation"]["ok"]
    assert result["validation"]["backbone_certification"] == {
        "dataset.nfl.games": "certified",
        "dataset.sports.nfl.schedule": "certified",
        "dataset.sports.nfl.results": "certified",
        "dataset.nfl.odds_snapshots": "certified",
        "dataset.nfl.weather_snapshots": "certified",
    }
    assert result["join_validation"]["ok"]
    assert result["join_validation"]["matched_rows"] == 2
    assert result["research_asset_certification"]["certification_status"] == "certified"
    assert result["dataset_certification"]["certification_status"] == "certified"
    assert result["lifecycle_alignment"]["status"] == "aligned"

    row = result["normalized_rows"][0]
    assert row["asset_id"] == DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID
    assert row["event_id"] == row["game_id"]
    assert row["participant_id"] == row["player_id"]
    assert _parse_iso(row["report_time"]) <= _parse_iso(row["snapshot_time"]) <= _parse_iso(row["decision_time"]) <= _parse_iso(row["kickoff_time"])
    assert row["field_provenance"]["report_status"]["source_field_name"] == "report_status"
    assert row["field_provenance"]["practice_status"]["source_field_name"] == "practice_status"
    assert row["field_provenance"]["report_time"]["source_field_name"] == "report_time"

    readiness = result["readiness_snapshot"]
    assert readiness["ok"]
    assert readiness["asset_id"] == DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID
    assert readiness["lifecycle_state"] == "feature_ready"
    assert readiness["certification_status"] == "certified"
    assert readiness["dataset_certification_status"] == "certified"
    assert readiness["join_validation"]["ok"]
    assert readiness["row_count"] == 2
    assert readiness["coverage_planner_readiness"]["first_production_connector_target"] == "dataset.nfl.team_stats_snapshots"
    assert DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID not in readiness["coverage_planner_readiness"]["missing_required_asset_ids"]
    assert DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID not in readiness["coverage_planner_readiness"]["future_asset_ids"]

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        raw_rows = storage.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[f"{DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID}.raw_acquisition_cache"],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == 2
        raw_payload = json.loads(raw_rows[0]["payload_json"])
        assert raw_payload["source_table"] == "nfl_injury_snapshots"
        assert raw_payload["provider"] == "nflverse_injuries"
        assert "manual_import" in json.dumps(result["source_bundle"])

        injury_rows = storage.fetch("nfl_injury_snapshots", order_by="injury_snapshot_id ASC")
        assert len(injury_rows) == 2
        assert injury_rows[0]["game_id"] == row["game_id"]

        asset_rows = storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=[DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == 1
        assert asset_rows[0]["certification_status"] == "certified"

        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID],
        )
        assert lifecycle_rows
        assert lifecycle_rows[-1]["lifecycle_state"] == "feature_ready"

        alignment_rows = storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=[DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID],
            order_by="alignment_certification_id ASC",
        )
        assert len(alignment_rows) == 2
        assert alignment_rows[-1]["alignment_status"] == "aligned"
    finally:
        storage.close()

    dashboard = get_nfl_injuries_research_asset_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard["ok"]
    assert dashboard["asset_id"] == DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID
    assert dashboard["lifecycle_state"] == "feature_ready"
    assert dashboard["join_validation"]["ok"]


def test_nfl_injuries_certification_is_blocked_without_certified_backbone(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_injuries_without_backbone.sqlite"

    result = build_nfl_injuries_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert "schedule_results_odds_weather_join_alignment_failed" in result["validation"]["errors"]
    assert "schedule_backbone_not_certified" in result["validation"]["errors"]
    assert "results_backbone_not_certified" in result["validation"]["errors"]
    assert "odds_backbone_not_certified" in result["validation"]["errors"]
    assert "weather_backbone_not_certified" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"


def test_nfl_injuries_post_decision_rows_cannot_certify(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_injuries_post_decision.sqlite"

    assert build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_results_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_odds_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_weather_research_asset_population(storage_path=storage_path, game_count=1)["ok"]

    connector_bundle = build_nfl_injuries_connector_bundle(game_count=1)
    injury_rows = [dict(row) for row in connector_bundle["injury_rows"]]
    injury_row = injury_rows[0]
    bad_text = (_parse_iso(injury_row["kickoff_time"]) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    injury_row["report_time"] = bad_text
    injury_row["source_snapshot_time"] = bad_text
    injury_row["snapshot_time"] = bad_text
    injury_row["decision_time"] = bad_text
    connector_bundle["injury_rows"] = injury_rows

    result = build_nfl_injuries_research_asset_population(
        storage_path=storage_path,
        connector_bundle=connector_bundle,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert result["join_validation"]["post_decision_injury_rows"] == [injury_row["injury_snapshot_id"]]
    assert "schedule_results_odds_weather_join_alignment_failed" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"
