from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

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
    build_nfl_weather_connector_bundle,
    build_nfl_weather_research_asset_population,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_weather_research_asset_snapshot_for_dashboard,
)


WEATHER_ASSET_ID = "dataset.nfl.weather_snapshots"


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_nfl_weather_asset_reuses_shared_runtime_and_certifies_joined_weather(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_weather_research_asset.sqlite"

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

    odds_result = build_nfl_odds_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )
    assert odds_result["ok"]

    result = build_nfl_weather_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert result["ok"]
    assert result["status"] == "ready"
    assert result["profile"]["profile_id"] == "sports:nfl"
    assert result["source_bundle"]["dataset_id"] == f"{WEATHER_ASSET_ID}.raw_acquisition_cache"
    assert result["source_bundle"]["provider"] == "open_meteo"
    assert result["source_bundle"]["connector_id"] == "connector.market_data.weather"
    assert result["source_bundle"]["source_type"] == "forecast_fixture"
    assert result["source_bundle"]["provider_capability"]["provider_id"] == "open_meteo"
    assert result["source_bundle"]["provider_capability"]["supported_assets"] == [WEATHER_ASSET_ID]
    assert result["raw_acquisition_result"]["status"] == "raw_cache_ready"
    assert result["raw_acquisition_result"]["raw_record_count"] == 1
    assert result["validation"]["ok"]
    assert result["validation"]["backbone_certification"] == {
        "dataset.nfl.games": "certified",
        "dataset.sports.nfl.schedule": "certified",
        "dataset.sports.nfl.results": "certified",
        "dataset.nfl.odds_snapshots": "certified",
    }
    assert result["join_validation"]["ok"]
    assert result["join_validation"]["matched_rows"] == 1
    assert result["research_asset_certification"]["certification_status"] == "certified"
    assert result["dataset_certification"]["certification_status"] == "certified"
    assert result["lifecycle_alignment"]["status"] == "aligned"

    row = result["normalized_rows"][0]
    assert row["asset_id"] == WEATHER_ASSET_ID
    assert row["event_id"] == row["game_id"]
    assert row["location"]
    assert row["source_type"] == "forecast_fixture"
    assert _parse_iso(row["forecast_time"]) <= _parse_iso(row["snapshot_time"]) <= _parse_iso(row["decision_time"]) <= _parse_iso(row["kickoff_time"])
    assert row["field_provenance"]["temperature_f"]["source_field_name"] == "temperature_f"
    assert row["field_provenance"]["wind_mph"]["source_field_name"] == "wind_mph"
    assert row["field_provenance"]["location"]["source_field_name"] == "venue_name|venue_city|venue_state"

    readiness = result["readiness_snapshot"]
    assert readiness["ok"]
    assert readiness["asset_id"] == WEATHER_ASSET_ID
    assert readiness["lifecycle_state"] == "feature_ready"
    assert readiness["certification_status"] == "certified"
    assert readiness["dataset_certification_status"] == "certified"
    assert readiness["join_validation"]["ok"]
    assert readiness["row_count"] == 1
    assert readiness["coverage_planner_readiness"]["first_production_connector_target"] == "dataset.nfl.team_stats_snapshots"
    assert WEATHER_ASSET_ID in readiness["coverage_planner_readiness"]["certified_required_asset_ids"]

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        raw_rows = storage.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[f"{WEATHER_ASSET_ID}.raw_acquisition_cache"],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == 1
        raw_payload = json.loads(raw_rows[0]["payload_json"])
        assert raw_payload["source_table"] == "nfl_weather_snapshots"
        assert raw_payload["provider"] == "open_meteo"
        assert "forecast_fixture" in raw_rows[0]["payload_json"]

        weather_rows = storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")
        assert len(weather_rows) == 1
        assert weather_rows[0]["game_id"] == row["game_id"]

        asset_rows = storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=[WEATHER_ASSET_ID],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == 1
        assert asset_rows[0]["certification_status"] == "certified"

        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[WEATHER_ASSET_ID],
        )
        assert lifecycle_rows
        assert lifecycle_rows[-1]["lifecycle_state"] == "feature_ready"

        alignment_rows = storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=[WEATHER_ASSET_ID],
        )
        assert alignment_rows
        assert alignment_rows[-1]["alignment_status"] == "aligned"
    finally:
        storage.close()

    dashboard = get_nfl_weather_research_asset_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard["ok"]
    assert dashboard["asset_id"] == WEATHER_ASSET_ID
    assert dashboard["lifecycle_state"] == "feature_ready"
    assert dashboard["join_validation"]["ok"]


def test_nfl_weather_certification_is_blocked_without_certified_backbone(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_weather_without_backbone.sqlite"

    result = build_nfl_weather_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert "schedule_results_odds_join_alignment_failed" in result["validation"]["errors"]
    assert "schedule_backbone_not_certified" in result["validation"]["errors"]
    assert "results_backbone_not_certified" in result["validation"]["errors"]
    assert "odds_backbone_not_certified" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"


def test_nfl_weather_post_decision_rows_cannot_certify(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_weather_post_decision.sqlite"

    assert build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_results_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_odds_research_asset_population(storage_path=storage_path, game_count=1)["ok"]

    connector_bundle = build_nfl_weather_connector_bundle(game_count=1)
    weather_rows = [dict(row) for row in connector_bundle["weather_rows"]]
    weather_row = weather_rows[0]
    bad_text = (_parse_iso(weather_row["kickoff_time"]) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    weather_row["source_snapshot_time"] = bad_text
    weather_row["snapshot_time"] = bad_text
    weather_row["decision_time"] = bad_text
    connector_bundle["weather_rows"] = weather_rows

    result = build_nfl_weather_research_asset_population(
        storage_path=storage_path,
        connector_bundle=connector_bundle,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert result["join_validation"]["post_decision_weather_rows"] == [weather_row["game_id"]]
    assert "schedule_results_odds_join_alignment_failed" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"
