from __future__ import annotations

import json
from pathlib import Path

from src.data.nfl_p0_foundation import create_nfl_p0_storage_engine
from src.data.nfl_schedule_research_asset_population import (
    build_nfl_schedule_research_asset_population,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_schedule_research_asset_snapshot_for_dashboard,
)


def test_nfl_schedule_research_asset_population_uses_shared_runtime_and_certifies_asset(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_schedule_research_asset.sqlite"

    result = build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)

    assert result["ok"]
    assert result["status"] == "ready"
    assert result["profile"]["profile_id"] == "sports:nfl"
    assert result["fixture"]["source_bundle"]["dataset_id"] == "dataset.sports.nfl.schedule.raw_acquisition_cache"
    assert result["source_bundle"]["provider"] == "nflverse"
    assert result["source_bundle"]["connector_id"] == "connector.feeds.nfl_schedule"
    assert result["source_bundle"]["provider_capability"]["provider_id"] == "nflverse"
    assert result["source_bundle"]["provider_capability"]["supported_assets"] == [
        "dataset.nfl.games",
        "dataset.sports.nfl.schedule",
    ]
    assert result["raw_acquisition_result"]["status"] == "raw_cache_ready"
    assert result["raw_acquisition_result"]["raw_record_count"] == 2
    assert result["raw_acquisition_result"]["normalization_request"]["status"] == "normalization_ready"
    assert result["raw_acquisition_result"]["certification_request"]["status"] == "certification_ready"
    assert result["validation"]["ok"]
    assert result["games_validation"]["ok"]
    assert result["schedule_validation"]["ok"]
    assert result["research_asset_certification"]["certification_status"] == "certified"
    assert result["games_research_asset_certification"]["certification_status"] == "certified"
    assert result["dataset_certification"]["certification_status"] == "certified"
    assert result["games_lifecycle_alignment"]["status"] == "aligned"
    assert result["lifecycle_alignment"]["status"] == "aligned"
    assert len(result["games_alignment_results"]) == 1
    assert len(result["schedule_alignment_results"]) == 1

    readiness = result["readiness_snapshot"]
    assert readiness["ok"]
    assert readiness["asset_id"] == "dataset.sports.nfl.schedule"
    assert readiness["lifecycle_state"] == "feature_ready"
    assert readiness["certification_status"] == "certified"
    assert readiness["dataset_certification_status"] == "certified"
    assert readiness["row_count"] == 1
    assert readiness["coverage_seasons"]
    assert readiness["source_provider_role"]["provider"] == "nflverse"
    assert readiness["connector_state"]["connector_id"] == "connector.feeds.nfl_schedule"
    assert readiness["connector_state"]["execution_mode"] == "deterministic_fixture"
    assert readiness["provider_capability"]["provider_id"] == "nflverse"
    assert readiness["field_provenance"]["nfl_schedule"]["week"]["source_provider"] == "nflverse"
    assert any("canonical nfl schedule connector path" in note.lower() for note in readiness["notes"])

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        raw_rows = storage.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=["dataset.sports.nfl.schedule.raw_acquisition_cache"],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == 2
        assert raw_rows[0]["provider"] == "nflverse"
        assert raw_rows[0]["source"] == "nflverse schedules/results"
        assert "connector.feeds.nfl_schedule" in raw_rows[0]["payload_json"]
        lineage_payload = json.loads(json.loads(raw_rows[0]["payload_json"])["lineage_record_json"])
        assert lineage_payload["target_stage"] == "raw_acquisition_cache"

        provider_rows = storage.fetch("provider_metadata", order_by="provider_id ASC")
        assert len(provider_rows) == 1
        assert provider_rows[0]["provider_id"] == "nflverse"
        provider_metadata = json.loads(provider_rows[0]["metadata_json"])
        assert provider_metadata["connector_id"] == "connector.feeds.nfl_schedule"

        schedule_rows = storage.fetch("nfl_schedule", order_by="schedule_id ASC")
        assert len(schedule_rows) == 1

        asset_rows = storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=["dataset.sports.nfl.schedule"],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == 1
        assert asset_rows[0]["certification_status"] == "certified"

        dataset_rows = storage.fetch("historical_certifications", order_by="certification_id ASC")
        assert len(dataset_rows) == 1
        assert dataset_rows[0]["certification_status"] == "certified"

        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=["dataset.sports.nfl.schedule"],
            order_by="updated_at ASC",
        )
        assert lifecycle_rows
        assert lifecycle_rows[-1]["lifecycle_state"] == "feature_ready"
        assert lifecycle_rows[-1]["alignment_status"] == "aligned"

        alignment_rows = storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=["dataset.sports.nfl.schedule"],
            order_by="alignment_certification_id ASC",
        )
        assert alignment_rows
        assert alignment_rows[-1]["alignment_status"] == "aligned"
    finally:
        storage.close()

    dashboard_snapshot = get_nfl_schedule_research_asset_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard_snapshot["ok"]
    assert dashboard_snapshot["asset_id"] == "dataset.sports.nfl.schedule"
    assert dashboard_snapshot["lifecycle_state"] == "feature_ready"
    assert dashboard_snapshot["certification_status"] == "certified"
    assert dashboard_snapshot["dataset_certification_status"] == "certified"
    assert dashboard_snapshot["connector_state"]["connector_id"] == "connector.feeds.nfl_schedule"
