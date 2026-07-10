from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from src.data.nfl_injuries_research_asset_population import (
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
from src.data.nfl_team_statistics_research_asset_population import (
    DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
    build_nfl_team_statistics_connector_bundle,
    build_nfl_team_statistics_research_asset_population,
)
from src.data.nfl_weather_research_asset_population import (
    build_nfl_weather_research_asset_population,
)
from src.market_intelligence.research_asset_coverage_planner import (
    build_research_asset_coverage_planner_snapshot,
)
from src.services.streamlit_dashboard_data import (
    get_nfl_team_statistics_research_asset_snapshot_for_dashboard,
)
from src.storage.local_store import LocalStorageEngine


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_certified_backbone(storage_path: Path) -> None:
    assert build_nfl_schedule_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )["ok"]
    assert build_nfl_results_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )["ok"]
    assert build_nfl_odds_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )["ok"]
    assert build_nfl_weather_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )["ok"]
    assert build_nfl_injuries_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )["ok"]


def test_nfl_team_statistics_asset_reuses_shared_runtime_and_certifies_joined_snapshots(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_team_statistics_research_asset.sqlite"
    _build_certified_backbone(storage_path)

    result = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert result["ok"]
    assert result["status"] == "ready"
    assert result["profile"]["profile_id"] == "sports:nfl"
    assert result["source_bundle"]["dataset_id"] == (
        f"{DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID}.raw_acquisition_cache"
    )
    assert result["source_bundle"]["provider"] == "nflverse"
    assert result["source_bundle"]["connector_id"] == "connector.feeds.nfl_team_stats"
    assert result["source_bundle"]["source_type"] == "team_stats_fixture"
    assert (
        result["source_bundle"]["provider_capability"]["provider_id"] == "nflverse"
    )
    assert result["source_bundle"]["provider_capability"]["supported_assets"] == [
        DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID
    ]
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
        "dataset.nfl.injury_snapshots": "certified",
    }
    assert result["join_validation"]["ok"]
    assert result["join_validation"]["matched_rows"] == 2
    assert result["join_validation"]["matched_injury_context_rows"] == 2
    assert (
        result["research_asset_certification"]["certification_status"] == "certified"
    )
    assert result["dataset_certification"]["certification_status"] == "certified"
    assert result["lifecycle_alignment"]["status"] == "aligned"

    row = result["normalized_rows"][0]
    assert row["asset_id"] == DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID
    assert row["event_id"] == row["game_id"]
    assert row["team_side"] in {"home", "away"}
    assert row["measurement_period"] == "rolling_prior_games"
    assert row["statistic_context"] == "pregame"
    assert row["alignment_status"] == "aligned"
    assert row["certification_state"] == "certified"
    assert (
        _parse_iso(row["window_start_time"])
        <= _parse_iso(row["team_stats_cutoff_time"])
        <= _parse_iso(row["snapshot_time"])
        <= _parse_iso(row["decision_time"])
        <= _parse_iso(row["kickoff_time"])
    )
    assert (
        row["field_provenance"]["offensive_efficiency"]["source_field_name"]
        == "offensive_efficiency"
    )
    assert (
        row["field_provenance"]["team_stats_cutoff_time"]["source_field_name"]
        == "team_stats_cutoff_time"
    )
    metric_units = (
        row["metric_units_json"]
        if isinstance(row["metric_units_json"], dict)
        else json.loads(row["metric_units_json"])
    )
    assert metric_units["pace"] == "plays_per_game"

    readiness = result["readiness_snapshot"]
    assert readiness["ok"]
    assert readiness["asset_id"] == DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID
    assert readiness["raw_acquisition_status"] == "raw_cache_ready"
    assert readiness["integrity_status"] == "validated"
    assert readiness["alignment_status"] == "aligned"
    assert readiness["lifecycle_state"] == "feature_ready"
    assert readiness["certification_status"] == "certified"
    assert readiness["dataset_certification_status"] == "certified"
    assert readiness["join_validation"]["ok"]
    assert readiness["row_count"] == 2
    assert readiness["provenance_completeness"] is True
    assert readiness["unresolved_blockers"] == []
    assert (
        readiness["coverage_planner_readiness"]["minimum_schema_completion_percentage"]
        == 100.0
    )
    assert readiness["coverage_planner_readiness"]["missing_required_asset_ids"] == []
    assert (
        readiness["coverage_planner_readiness"]["first_production_connector_target"]
        == ""
    )

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        raw_rows = storage.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[f"{DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID}.raw_acquisition_cache"],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == 2
        raw_payload = json.loads(raw_rows[0]["payload_json"])
        assert raw_payload["source_table"] == "nfl_team_stats_snapshots"
        assert raw_payload["provider"] == "nflverse"

        team_stats_rows = storage.fetch(
            "nfl_team_stats_snapshots",
            order_by="team_stats_snapshot_id ASC",
        )
        assert len(team_stats_rows) == 2
        assert {row["team_side"] for row in team_stats_rows} == {"away", "home"}
        assert all(row["alignment_status"] == "aligned" for row in team_stats_rows)
        assert all(row["certification_state"] == "certified" for row in team_stats_rows)

        asset_rows = storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=[DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == 1
        assert asset_rows[0]["certification_status"] == "certified"

        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
        )
        assert lifecycle_rows
        assert lifecycle_rows[-1]["lifecycle_state"] == "feature_ready"

        alignment_rows = storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=[DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
            order_by="alignment_certification_id ASC",
        )
        assert len(alignment_rows) == 2
        assert all(row["alignment_status"] == "aligned" for row in alignment_rows)
    finally:
        storage.close()

    dashboard = get_nfl_team_statistics_research_asset_snapshot_for_dashboard(
        storage_path=storage_path
    )
    assert dashboard["ok"]
    assert dashboard["asset_id"] == DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID
    assert dashboard["lifecycle_state"] == "feature_ready"
    assert dashboard["join_validation"]["ok"]
    assert dashboard["raw_acquisition_status"] == "raw_cache_ready"


def test_nfl_team_statistics_certification_is_blocked_without_certified_backbone(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_team_statistics_without_backbone.sqlite"

    result = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert (
        "schedule_results_odds_weather_team_statistics_join_alignment_failed"
        in result["validation"]["errors"]
    )
    assert "games_backbone_not_certified" in result["validation"]["errors"]
    assert "schedule_backbone_not_certified" in result["validation"]["errors"]
    assert "results_backbone_not_certified" in result["validation"]["errors"]
    assert "odds_backbone_not_certified" in result["validation"]["errors"]
    assert "weather_backbone_not_certified" in result["validation"]["errors"]
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"


def test_nfl_team_statistics_post_decision_rows_cannot_certify(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_team_statistics_post_decision.sqlite"
    _build_certified_backbone(storage_path)

    connector_bundle = build_nfl_team_statistics_connector_bundle(game_count=1)
    team_stats_rows = [dict(row) for row in connector_bundle["team_stats_rows"]]
    team_stats_row = team_stats_rows[0]
    bad_text = (_parse_iso(team_stats_row["kickoff_time"]) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    team_stats_row["source_snapshot_time"] = bad_text
    team_stats_row["snapshot_time"] = bad_text
    team_stats_row["decision_time"] = bad_text
    team_stats_row["source_retrieved_at"] = bad_text
    connector_bundle["team_stats_rows"] = team_stats_rows

    result = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        connector_bundle=connector_bundle,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert result["join_validation"]["post_decision_team_stats_rows"] == [
        team_stats_row["team_stats_snapshot_id"]
    ]
    assert (
        "schedule_results_odds_weather_team_statistics_join_alignment_failed"
        in result["validation"]["errors"]
    )
    assert result["research_asset_certification"]["certification_status"] != "certified"
    assert result["dataset_certification"]["certification_status"] != "certified"
    assert result["readiness_snapshot"]["lifecycle_state"] != "feature_ready"


def test_nfl_team_statistics_same_event_final_statistics_are_rejected(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_team_statistics_same_event_final.sqlite"
    _build_certified_backbone(storage_path)

    connector_bundle = build_nfl_team_statistics_connector_bundle(game_count=1)
    team_stats_rows = [dict(row) for row in connector_bundle["team_stats_rows"]]
    team_stats_row = team_stats_rows[0]
    team_stats_row["statistic_context"] = "target_event_final"
    team_stats_row["measurement_period"] = "target_event_final"
    team_stats_row["statistic_window_type"] = "final_box_score"
    team_stats_row["window_excludes_current_event"] = 0
    team_stats_row["metric_units_json"] = {
        **json.loads(json.dumps(team_stats_row["metric_units_json"])),
        "pace": "yards_per_play",
    }
    connector_bundle["team_stats_rows"] = team_stats_rows

    result = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        connector_bundle=connector_bundle,
    )

    assert not result["ok"]
    assert result["status"] == "partial"
    assert not result["join_validation"]["ok"]
    assert result["join_validation"]["same_event_final_stat_rows"] == [
        team_stats_row["team_stats_snapshot_id"]
    ]
    assert result["join_validation"]["rolling_window_leakage_rows"] == [
        team_stats_row["team_stats_snapshot_id"]
    ]
    assert result["join_validation"]["unsupported_metric_unit_rows"] == [
        team_stats_row["team_stats_snapshot_id"]
    ]
    assert any(
        error.startswith("semantic:0:unsupported_statistic_context")
        for error in result["validation"]["errors"]
    )
    assert result["research_asset_certification"]["certification_status"] != "certified"


def test_nfl_team_statistics_orphaned_events_are_rejected(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_team_statistics_orphaned.sqlite"
    _build_certified_backbone(storage_path)

    connector_bundle = build_nfl_team_statistics_connector_bundle(game_count=1)
    team_stats_rows = [dict(row) for row in connector_bundle["team_stats_rows"]]
    team_stats_row = team_stats_rows[0]
    team_stats_row["game_id"] = "NFL-2099-01-01-ORPHAN"
    connector_bundle["team_stats_rows"] = team_stats_rows

    result = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        connector_bundle=connector_bundle,
    )

    assert not result["ok"]
    assert not result["join_validation"]["ok"]
    assert result["join_validation"]["missing_schedule_rows"] == [
        "NFL-2099-01-01-ORPHAN"
    ]
    assert team_stats_row["team_stats_snapshot_id"] in result["join_validation"][
        "orphaned_team_stats_rows"
    ]
    assert result["research_asset_certification"]["certification_status"] != "certified"


def test_nfl_team_statistics_rerun_is_deterministic_and_idempotent(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_team_statistics_rerun.sqlite"
    _build_certified_backbone(storage_path)

    first = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )
    second = build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )

    assert first["ok"] and second["ok"]
    assert [
        row["team_stats_snapshot_id"] for row in first["normalized_rows"]
    ] == [row["team_stats_snapshot_id"] for row in second["normalized_rows"]]

    storage = create_nfl_p0_storage_engine(storage_path)
    try:
        assert storage.count("nfl_team_stats_snapshots") == 2
        assert (
            storage.count("research_asset_alignment_certifications") >= 2
        )
    finally:
        storage.close()


def test_team_statistics_schema_reconciliation_adds_new_columns(tmp_path: Path) -> None:
    storage_path = tmp_path / "legacy_team_stats.sqlite"
    storage = LocalStorageEngine(storage_path, auto_initialize=False)
    try:
        storage.execute(
            'CREATE TABLE "nfl_team_stats_snapshots" ("team_stats_snapshot_id" TEXT PRIMARY KEY);'
        )
        storage.ensure_schema()
        columns = set(storage.table_columns("nfl_team_stats_snapshots"))
        assert {
            "team_side",
            "source_record_id",
            "source_retrieved_at",
            "measurement_period",
            "statistic_context",
            "statistic_window_type",
            "window_start_time",
            "team_stats_cutoff_time",
            "window_excludes_current_event",
            "metric_units_json",
            "field_provenance_json",
            "alignment_status",
            "certification_state",
        }.issubset(columns)
    finally:
        storage.close()


def test_team_statistics_completion_closes_the_minimum_schema_gap(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "nfl_team_statistics_coverage.sqlite"
    _build_certified_backbone(storage_path)
    assert build_nfl_team_statistics_research_asset_population(
        storage_path=storage_path,
        game_count=1,
    )["ok"]

    snapshot = build_research_asset_coverage_planner_snapshot(storage_path=storage_path)

    assert snapshot["ok"]
    assert snapshot["status"] == "ready"
    assert snapshot["planner_readiness"]["status"] == "ready"
    assert snapshot["coverage_gap_engine"]["minimum_schema_completion_percentage"] == 100.0
    assert snapshot["coverage_gap_engine"]["missing_required_asset_ids"] == []
    assert (
        snapshot["coverage_gap_engine"]["first_production_connector_target"] == ""
    )
    assert (
        DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID
        in snapshot["coverage_gap_engine"]["certified_required_asset_ids"]
    )
