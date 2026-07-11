from __future__ import annotations

import copy
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.data import (
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
    build_historical_dataset_population,
    build_historical_dataset_population_dashboard_snapshot,
    get_historical_dataset_population_snapshot_for_dashboard,
)
from src.data.nfl_injuries_research_asset_population import (
    build_nfl_injuries_connector_bundle,
    build_nfl_injuries_research_asset_population,
)
from src.data.nfl_odds_research_asset_population import (
    build_nfl_odds_connector_bundle,
    build_nfl_odds_research_asset_population,
)
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.data.nfl_results_research_asset_population import (
    build_nfl_results_research_asset_population,
)
from src.data.nfl_schedule_research_asset_population import (
    build_nfl_schedule_research_asset_population,
)
from src.data.nfl_team_statistics_research_asset_population import (
    build_nfl_team_statistics_connector_bundle,
    build_nfl_team_statistics_research_asset_population,
)
from src.data.nfl_weather_research_asset_population import (
    build_nfl_weather_research_asset_population,
)
from src.market_intelligence.research_asset_coverage_planner import (
    build_research_asset_coverage_planner_snapshot,
)
from src.storage.local_store import LocalStorageEngine


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _set_bundle_rows(
    bundle: dict[str, object],
    *,
    row_key: str,
    table_name: str,
    rows: list[dict[str, object]],
) -> None:
    bundle[row_key] = rows
    source_bundle = bundle["source_bundle"]
    source_bundle["tables"][table_name] = rows
    source_bundle["source_tables"][table_name] = rows


def _build_phase50_sources(
    storage_path: Path,
    *,
    odds_bundle: dict[str, object] | None = None,
) -> None:
    assert build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_results_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_odds_research_asset_population(
        storage_path=storage_path,
        connector_bundle=odds_bundle,
        game_count=1,
    )["ok"]
    assert build_nfl_weather_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_injuries_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_team_statistics_research_asset_population(storage_path=storage_path, game_count=1)["ok"]


def _rows_by_market(result: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        row["market_type"]: row
        for row in result["dataset_rows"]
    }


def _fetch_lineage_edges(storage_path: Path) -> list[dict[str, object]]:
    storage = LocalStorageEngine(storage_path)
    try:
        return [
            dict(row)
            for row in storage.fetch(
                "lineage_edges",
                where="dataset_id = ? AND target_stage = ?",
                params=[DEFAULT_NFL_HISTORICAL_DATASET_ID, "historical_dataset_row"],
                order_by="lineage_edge_id ASC",
            )
        ]
    finally:
        storage.close()


def _legacy_seed_dataset_tables(storage_path: Path) -> None:
    connection = sqlite3.connect(storage_path)
    try:
        connection.execute("CREATE TABLE historical_dataset_batches (batch_id TEXT PRIMARY KEY)")
        connection.execute("CREATE TABLE historical_dataset_rows (dataset_row_id TEXT PRIMARY KEY)")
        connection.commit()
    finally:
        connection.close()


def _clone_alignment_row(
    storage: LocalStorageEngine,
    *,
    research_asset_id: str,
    template_market_id: str,
    new_alignment_id: str,
    new_market_id: str,
    new_team_id: str | None = None,
    new_participant_id: str | None = None,
    new_snapshot_time: str | None = None,
    new_decision_time: str | None = None,
) -> None:
    template = dict(
        storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ? AND market_id = ?",
            params=[research_asset_id, template_market_id],
            limit=1,
        )[0]
    )
    template["alignment_certification_id"] = new_alignment_id
    template["market_id"] = new_market_id
    if new_team_id is not None:
        template["team_id"] = new_team_id
    if new_participant_id is not None:
        template["participant_id"] = new_participant_id
    if new_snapshot_time is not None:
        template["snapshot_time"] = new_snapshot_time
        template["source_snapshot_time"] = new_snapshot_time
        template["provider_timestamp"] = new_snapshot_time
        template["result_timestamp"] = new_snapshot_time
    if new_decision_time is not None:
        template["decision_time"] = new_decision_time
    storage.upsert(
        "research_asset_alignment_certifications",
        template,
        key_columns=("alignment_certification_id",),
    )


def test_historical_dataset_population_accepts_later_weather_and_injuries_before_cutoff(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "phase50_later_weather_injuries.sqlite"
    _build_phase50_sources(storage_path)

    storage = LocalStorageEngine(storage_path)
    try:
        weather_row = dict(storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")[0])
        later_weather = copy.deepcopy(weather_row)
        later_weather["weather_snapshot_id"] = "nfl-p0-game-001.weather.latest"
        later_weather["snapshot_id"] = "nfl-p0-game-001.weather.latest.snapshot"
        later_weather["lineage_id"] = "nfl_p0.v001.game.001.weather.latest.lineage"
        for field_name in ("forecast_time", "source_snapshot_time", "snapshot_time", "decision_time"):
            later_weather[field_name] = "2024-09-05T20:12:00Z"
        storage.upsert("nfl_weather_snapshots", later_weather, key_columns=("weather_snapshot_id",))

        injury_row = dict(
            storage.fetch(
                "nfl_injury_snapshots",
                where="team_id = ?",
                params=["BUF"],
                order_by="injury_snapshot_id ASC",
                limit=1,
            )[0]
        )
        later_injury = copy.deepcopy(injury_row)
        later_injury["injury_snapshot_id"] = "nfl-p0-game-001.BUF.injury.03"
        later_injury["player_id"] = "BUF_WR_03"
        later_injury["player_name"] = "Later Injury Player"
        later_injury["snapshot_id"] = "nfl-p0-game-001.BUF.injury.03.snapshot"
        later_injury["lineage_id"] = "nfl_p0.v001.game.001.buf.injury.03.lineage"
        later_injury["report_time"] = "2024-09-05T20:13:00Z"
        later_injury["source_snapshot_time"] = "2024-09-05T20:13:00Z"
        later_injury["snapshot_time"] = "2024-09-05T20:13:00Z"
        later_injury["decision_time"] = "2024-09-05T20:13:00Z"
        storage.upsert("nfl_injury_snapshots", later_injury, key_columns=("injury_snapshot_id",))
        _clone_alignment_row(
            storage,
            research_asset_id="dataset.nfl.injury_snapshots",
            template_market_id=injury_row["injury_snapshot_id"],
            new_alignment_id="align.nfl-p0-game-001.BUF.injury.03",
            new_market_id=later_injury["injury_snapshot_id"],
            new_team_id="BUF",
            new_participant_id="BUF_WR_03",
            new_snapshot_time="2024-09-05T20:13:00Z",
            new_decision_time="2024-09-05T20:13:00Z",
        )
    finally:
        storage.close()

    result = build_historical_dataset_population(storage_path=storage_path)
    assert result["ok"]
    assert result["dataset_row_count"] == 3

    rows_by_market = _rows_by_market(result)
    spread_row = rows_by_market["spread"]
    assert spread_row["decision_cutoff_time"] == "2024-09-05T20:15:00Z"
    assert spread_row["selected_odds_timestamp"] == "2024-09-04T20:20:00Z"
    assert spread_row["selected_weather_timestamp"] == "2024-09-05T20:12:00Z"
    assert spread_row["selected_home_injury_timestamp"] == "2024-09-05T20:13:00Z"
    assert _parse_iso(spread_row["selected_weather_timestamp"]) > _parse_iso(
        spread_row["selected_odds_timestamp"]
    )
    assert _parse_iso(spread_row["selected_home_injury_timestamp"]) > _parse_iso(
        spread_row["selected_odds_timestamp"]
    )
    assert spread_row["home_injury_record_count"] == 2
    assert spread_row["decision_readiness_status"] == "ready"

    planner_snapshot = build_research_asset_coverage_planner_snapshot(storage_path=storage_path)
    assert planner_snapshot["coverage_gap_engine"]["missing_required_asset_ids"] == []
    assert planner_snapshot["dataset_population_readiness"]["status"] == "ready"

    p0_snapshot = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)
    assert p0_snapshot["dataset_layer_readiness"]["status"] == "ready"


def test_historical_dataset_population_selects_latest_eligible_rows_and_excludes_after_cutoff_records_without_row_multiplication(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "phase50_selection_rules.sqlite"
    _build_phase50_sources(storage_path)

    storage = LocalStorageEngine(storage_path)
    try:
        odds_rows = [dict(row) for row in storage.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")]
        spread_row = next(row for row in odds_rows if row["market_type"] == "spread")
        later_spread = copy.deepcopy(spread_row)
        later_spread["odds_snapshot_id"] = "nfl-p0-game-001.spread.odds.latest"
        later_spread["snapshot_id"] = "nfl-p0-game-001.spread.odds.latest.snapshot"
        later_spread["lineage_id"] = "nfl_p0.v001.game.001.spread.latest.lineage"
        later_spread["snapshot_time"] = "2024-09-05T20:14:00Z"
        later_spread["source_snapshot_time"] = "2024-09-05T20:14:00Z"
        later_spread["decision_time"] = "2024-09-05T20:14:00Z"
        storage.upsert("nfl_odds_snapshots", later_spread, key_columns=("odds_snapshot_id",))

        weather_row = dict(storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")[0])
        earlier_weather = copy.deepcopy(weather_row)
        earlier_weather["weather_snapshot_id"] = "nfl-p0-game-001.weather.earlier"
        earlier_weather["snapshot_id"] = "nfl-p0-game-001.weather.earlier.snapshot"
        earlier_weather["lineage_id"] = "nfl_p0.v001.game.001.weather.earlier.lineage"
        for field_name in ("forecast_time", "source_snapshot_time", "snapshot_time", "decision_time"):
            earlier_weather[field_name] = "2024-09-05T20:10:00Z"
        later_weather = copy.deepcopy(earlier_weather)
        later_weather["weather_snapshot_id"] = "nfl-p0-game-001.weather.latest"
        later_weather["snapshot_id"] = "nfl-p0-game-001.weather.latest.snapshot"
        later_weather["lineage_id"] = "nfl_p0.v001.game.001.weather.latest.lineage"
        for field_name in ("forecast_time", "source_snapshot_time", "snapshot_time", "decision_time"):
            later_weather[field_name] = "2024-09-05T20:12:00Z"
        rejected_weather = copy.deepcopy(earlier_weather)
        rejected_weather["weather_snapshot_id"] = "nfl-p0-game-001.weather.rejected"
        rejected_weather["snapshot_id"] = "nfl-p0-game-001.weather.rejected.snapshot"
        rejected_weather["lineage_id"] = "nfl_p0.v001.game.001.weather.rejected.lineage"
        for field_name in ("forecast_time", "source_snapshot_time", "snapshot_time", "decision_time"):
            rejected_weather[field_name] = "2024-09-05T20:16:00Z"
        for row in (earlier_weather, later_weather, rejected_weather):
            storage.upsert("nfl_weather_snapshots", row, key_columns=("weather_snapshot_id",))

        injury_row = dict(
            storage.fetch(
                "nfl_injury_snapshots",
                where="team_id = ?",
                params=["BUF"],
                order_by="injury_snapshot_id ASC",
                limit=1,
            )[0]
        )
        extra_home_injury = copy.deepcopy(injury_row)
        extra_home_injury["injury_snapshot_id"] = "nfl-p0-game-001.BUF.injury.03"
        extra_home_injury["player_id"] = "BUF_WR_03"
        extra_home_injury["player_name"] = "Home Injury 03"
        extra_home_injury["snapshot_id"] = "nfl-p0-game-001.BUF.injury.03.snapshot"
        extra_home_injury["lineage_id"] = "nfl_p0.v001.game.001.buf.injury.03.lineage"
        extra_home_injury["report_time"] = "2024-09-05T20:13:00Z"
        extra_home_injury["source_snapshot_time"] = "2024-09-05T20:13:00Z"
        extra_home_injury["snapshot_time"] = "2024-09-05T20:13:00Z"
        extra_home_injury["decision_time"] = "2024-09-05T20:13:00Z"
        rejected_home_injury = copy.deepcopy(extra_home_injury)
        rejected_home_injury["injury_snapshot_id"] = "nfl-p0-game-001.BUF.injury.04"
        rejected_home_injury["player_id"] = "BUF_WR_04"
        rejected_home_injury["player_name"] = "Home Injury 04"
        rejected_home_injury["snapshot_id"] = "nfl-p0-game-001.BUF.injury.04.snapshot"
        rejected_home_injury["lineage_id"] = "nfl_p0.v001.game.001.buf.injury.04.lineage"
        rejected_home_injury["report_time"] = "2024-09-05T20:16:00Z"
        rejected_home_injury["source_snapshot_time"] = "2024-09-05T20:16:00Z"
        rejected_home_injury["snapshot_time"] = "2024-09-05T20:16:00Z"
        rejected_home_injury["decision_time"] = "2024-09-05T20:16:00Z"
        for row in (extra_home_injury, rejected_home_injury):
            storage.upsert("nfl_injury_snapshots", row, key_columns=("injury_snapshot_id",))
        _clone_alignment_row(
            storage,
            research_asset_id="dataset.nfl.injury_snapshots",
            template_market_id=injury_row["injury_snapshot_id"],
            new_alignment_id="align.nfl-p0-game-001.BUF.injury.03",
            new_market_id=extra_home_injury["injury_snapshot_id"],
            new_team_id="BUF",
            new_participant_id="BUF_WR_03",
            new_snapshot_time="2024-09-05T20:13:00Z",
            new_decision_time="2024-09-05T20:13:00Z",
        )
        _clone_alignment_row(
            storage,
            research_asset_id="dataset.nfl.injury_snapshots",
            template_market_id=injury_row["injury_snapshot_id"],
            new_alignment_id="align.nfl-p0-game-001.BUF.injury.04",
            new_market_id=rejected_home_injury["injury_snapshot_id"],
            new_team_id="BUF",
            new_participant_id="BUF_WR_04",
            new_snapshot_time="2024-09-05T20:16:00Z",
            new_decision_time="2024-09-05T20:16:00Z",
        )

        team_stats_rows = [dict(row) for row in storage.fetch("nfl_team_stats_snapshots", order_by="team_stats_snapshot_id ASC")]
        home_stats = next(row for row in team_stats_rows if row["team_side"] == "home")
        away_stats = next(row for row in team_stats_rows if row["team_side"] == "away")
        later_home_stats = copy.deepcopy(home_stats)
        later_home_stats["team_stats_snapshot_id"] = "nfl-p0-game-001.BUF.team_stats.latest"
        later_home_stats["snapshot_id"] = "nfl-p0-game-001.BUF.team_stats.latest.snapshot"
        later_home_stats["lineage_id"] = "nfl_p0.v001.game.001.buf.team_stats.latest.lineage"
        later_home_stats["source_snapshot_time"] = "2024-09-05T20:10:00Z"
        later_home_stats["source_retrieved_at"] = "2024-09-05T20:10:00Z"
        later_home_stats["snapshot_time"] = "2024-09-05T20:10:00Z"
        later_home_stats["decision_time"] = "2024-09-05T20:10:00Z"
        later_away_stats = copy.deepcopy(away_stats)
        later_away_stats["team_stats_snapshot_id"] = "nfl-p0-game-001.KC.team_stats.latest"
        later_away_stats["snapshot_id"] = "nfl-p0-game-001.KC.team_stats.latest.snapshot"
        later_away_stats["lineage_id"] = "nfl_p0.v001.game.001.kc.team_stats.latest.lineage"
        later_away_stats["source_snapshot_time"] = "2024-09-05T20:11:00Z"
        later_away_stats["source_retrieved_at"] = "2024-09-05T20:11:00Z"
        later_away_stats["snapshot_time"] = "2024-09-05T20:11:00Z"
        later_away_stats["decision_time"] = "2024-09-05T20:11:00Z"
        for row in (later_home_stats, later_away_stats):
            storage.upsert("nfl_team_stats_snapshots", row, key_columns=("team_stats_snapshot_id",))
        _clone_alignment_row(
            storage,
            research_asset_id="dataset.nfl.team_stats_snapshots",
            template_market_id=home_stats["team_stats_snapshot_id"],
            new_alignment_id="align.nfl-p0-game-001.BUF.team_stats.latest",
            new_market_id=later_home_stats["team_stats_snapshot_id"],
            new_team_id="BUF",
            new_snapshot_time="2024-09-05T20:10:00Z",
            new_decision_time="2024-09-05T20:10:00Z",
        )
        _clone_alignment_row(
            storage,
            research_asset_id="dataset.nfl.team_stats_snapshots",
            template_market_id=away_stats["team_stats_snapshot_id"],
            new_alignment_id="align.nfl-p0-game-001.KC.team_stats.latest",
            new_market_id=later_away_stats["team_stats_snapshot_id"],
            new_team_id="KC",
            new_snapshot_time="2024-09-05T20:11:00Z",
            new_decision_time="2024-09-05T20:11:00Z",
        )
    finally:
        storage.close()

    result = build_historical_dataset_population(storage_path=storage_path)
    assert result["ok"]
    assert result["dataset_row_count"] == 3
    assert result["validation"]["rejected_evidence"]["after_cutoff_weather_rows"] == [
        "nfl-p0-game-001.weather.rejected"
    ]
    assert result["validation"]["rejected_evidence"]["post_cutoff_injury_rows"] == [
        "nfl-p0-game-001.BUF.injury.04"
    ]

    rows_by_market = _rows_by_market(result)
    spread_row = rows_by_market["spread"]
    assert spread_row["selected_odds_timestamp"] == "2024-09-05T20:14:00Z"
    assert spread_row["selected_weather_timestamp"] == "2024-09-05T20:12:00Z"
    assert spread_row["selected_home_injury_timestamp"] == "2024-09-05T20:13:00Z"
    assert spread_row["selected_home_team_stats_timestamp"] == "2024-09-05T20:10:00Z"
    assert spread_row["selected_away_team_stats_timestamp"] == "2024-09-05T20:11:00Z"
    assert spread_row["home_injury_record_count"] == 2
    assert result["join_diagnostics"]["final_dataset_row_count"] == 3
    assert result["join_diagnostics"]["expected_market_context_count"] == 3


def test_historical_dataset_population_blocks_when_required_predictor_evidence_is_only_after_cutoff(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "phase50_missing_weather.sqlite"
    _build_phase50_sources(storage_path)

    storage = LocalStorageEngine(storage_path)
    try:
        weather_rows = [
            dict(row)
            for row in storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")
        ]
        for row in weather_rows:
            row["forecast_time"] = "2024-09-05T20:21:00Z"
            row["source_snapshot_time"] = "2024-09-05T20:21:00Z"
            row["snapshot_time"] = "2024-09-05T20:21:00Z"
            row["decision_time"] = "2024-09-05T20:21:00Z"
            storage.upsert("nfl_weather_snapshots", row, key_columns=("weather_snapshot_id",))
    finally:
        storage.close()

    result = build_historical_dataset_population(storage_path=storage_path)
    assert not result["ok"]
    assert result["dataset_row_count"] == 0
    assert result["validation"]["rejected_evidence"]["after_cutoff_weather_rows"] == [
        "nfl-p0-game-001.weather"
    ]
    assert result["validation"]["errors"] == [
        "unmatched_entities:weather:nfl-p0-game-001"
    ]
    assert result["join_diagnostics"]["decision_cutoff_time_by_game"] == {
        "nfl-p0-game-001": "2024-09-05T20:15:00Z"
    }
    assert result["dataset_certification"]["certification_status"] == "rejected"


def test_historical_dataset_population_results_remain_labels_only_and_do_not_change_identity(
    tmp_path: Path,
) -> None:
    baseline_path = tmp_path / "phase50_result_identity_baseline.sqlite"
    mutated_path = tmp_path / "phase50_result_identity_mutated.sqlite"

    _build_phase50_sources(baseline_path)
    _build_phase50_sources(mutated_path)

    storage = LocalStorageEngine(mutated_path)
    try:
        result_row = dict(storage.fetch("nfl_results", order_by="result_id ASC")[0])
        result_row["winner_team_id"] = "KC"
        result_row["winner_team"] = "Kansas City Chiefs"
        result_row["final_score_home"] = 17
        result_row["final_score_away"] = 24
        result_row["margin"] = -7
        result_row["total_points"] = 41
        result_row["final_scored_at"] = "2024-09-05T23:45:00Z"
        storage.upsert("nfl_results", result_row, key_columns=("result_id",))
    finally:
        storage.close()

    baseline = build_historical_dataset_population(storage_path=baseline_path)
    mutated = build_historical_dataset_population(storage_path=mutated_path)

    assert baseline["ok"]
    assert mutated["ok"]
    assert baseline["batch_id"] == mutated["batch_id"]
    assert [row["dataset_row_id"] for row in baseline["dataset_rows"]] == [
        row["dataset_row_id"] for row in mutated["dataset_rows"]
    ]
    assert sorted({row["decision_cutoff_time"] for row in baseline["dataset_rows"]}) == [
        "2024-09-05T20:15:00Z"
    ]
    assert sorted({row["decision_cutoff_time"] for row in mutated["dataset_rows"]}) == [
        "2024-09-05T20:15:00Z"
    ]
    assert sorted({row["label_final_result"] for row in baseline["dataset_rows"]}) == ["home_win"]
    assert sorted({row["label_final_result"] for row in mutated["dataset_rows"]}) == ["away_win"]
    assert all(
        _parse_iso(row["label_result_recorded_time"]) > _parse_iso(row["event_start_time"])
        for row in mutated["dataset_rows"]
    )


def test_historical_dataset_population_is_deterministic_and_idempotent(tmp_path: Path) -> None:
    storage_a = tmp_path / "phase50_deterministic_a.sqlite"
    storage_b = tmp_path / "phase50_deterministic_b.sqlite"

    _build_phase50_sources(storage_a)
    _build_phase50_sources(storage_b)

    first = build_historical_dataset_population(storage_path=storage_a)
    second = build_historical_dataset_population(storage_path=storage_a)
    third = build_historical_dataset_population(storage_path=storage_b)

    assert first["ok"]
    assert second["ok"]
    assert third["ok"]
    assert second["idempotent_reuse"] is True
    assert first["batch_id"] == second["batch_id"] == third["batch_id"]
    assert [row["dataset_row_id"] for row in first["dataset_rows"]] == [
        row["dataset_row_id"] for row in second["dataset_rows"]
    ] == [
        row["dataset_row_id"] for row in third["dataset_rows"]
    ]
    assert [edge["lineage_edge_id"] for edge in _fetch_lineage_edges(storage_a)] == [
        edge["lineage_edge_id"] for edge in _fetch_lineage_edges(storage_b)
    ]


def test_historical_dataset_population_changed_predictor_evidence_updates_lineage_and_batch_when_material(
    tmp_path: Path,
) -> None:
    baseline_path = tmp_path / "phase50_changed_evidence_baseline.sqlite"
    changed_path = tmp_path / "phase50_changed_evidence_changed.sqlite"

    _build_phase50_sources(baseline_path)

    odds_bundle = build_nfl_odds_connector_bundle(game_count=1)
    changed_odds_rows = [copy.deepcopy(row) for row in odds_bundle["odds_rows"]]
    spread_row = next(row for row in changed_odds_rows if row["market_type"] == "spread")
    spread_row["snapshot_time"] = "2024-09-05T20:14:00Z"
    spread_row["source_snapshot_time"] = "2024-09-05T20:14:00Z"
    spread_row["decision_time"] = "2024-09-05T20:14:00Z"
    spread_row["lineage_id"] = "nfl_p0.v001.game.001.spread.changed.lineage"
    _set_bundle_rows(
        odds_bundle,
        row_key="odds_rows",
        table_name="nfl_odds_snapshots",
        rows=changed_odds_rows,
    )
    _build_phase50_sources(changed_path, odds_bundle=odds_bundle)

    baseline = build_historical_dataset_population(storage_path=baseline_path)
    changed = build_historical_dataset_population(storage_path=changed_path)

    baseline_spread = _rows_by_market(baseline)["spread"]
    changed_spread = _rows_by_market(changed)["spread"]

    assert baseline_spread["dataset_row_id"] == changed_spread["dataset_row_id"]
    assert baseline_spread["selected_odds_timestamp"] != changed_spread["selected_odds_timestamp"]
    assert baseline_spread["source_lineage_ids_json"] != changed_spread["source_lineage_ids_json"]
    assert baseline_spread["selected_source_row_ids_json"] == changed_spread["selected_source_row_ids_json"]
    assert baseline["batch_id"] == changed["batch_id"]
    assert baseline_spread["evidence_package_id"] == changed_spread["evidence_package_id"]


def test_historical_dataset_population_dashboard_and_planner_embedding_states_are_distinct(
    tmp_path: Path,
    monkeypatch,
) -> None:
    storage_path = tmp_path / "phase50_dashboard_states.sqlite"
    _build_phase50_sources(storage_path)
    assert build_historical_dataset_population(storage_path=storage_path)["ok"]

    not_embedded = build_historical_dataset_population_dashboard_snapshot(
        storage_path=storage_path,
        include_coverage_planner_snapshot=False,
    )
    assert not_embedded["coverage_planner_snapshot"]["status"] == "not_embedded"

    import src.market_intelligence.research_asset_coverage_planner as coverage_module

    def _boom(**_: object) -> dict[str, object]:
        raise RuntimeError("planner boom")

    monkeypatch.setattr(
        coverage_module,
        "build_research_asset_coverage_planner_snapshot",
        _boom,
    )
    failed = build_historical_dataset_population_dashboard_snapshot(
        storage_path=storage_path,
        include_coverage_planner_snapshot=True,
    )
    assert failed["coverage_planner_snapshot"]["status"] == "coverage_planner_snapshot_failed"
    assert failed["coverage_planner_snapshot"]["warnings"] == ["planner boom"]


def test_historical_dataset_population_exports_dashboard_rebuild_and_schema_reconciliation(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "phase50_legacy_schema.sqlite"
    _legacy_seed_dataset_tables(storage_path)

    _build_phase50_sources(storage_path)
    result = build_historical_dataset_population(storage_path=storage_path)
    assert result["ok"]

    dashboard = get_historical_dataset_population_snapshot_for_dashboard(storage_path=storage_path)
    assert dashboard["ok"]
    assert dashboard["dataset_row_count"] == 3
    assert dashboard["cutoff_policy_version"] == "nfl.minimum_schema.kickoff_minus_five_minutes.v1"
    assert dashboard["coverage_planner_snapshot"]["ok"]

    assert callable(build_historical_dataset_population)
    assert callable(build_historical_dataset_population_dashboard_snapshot)
    assert callable(get_historical_dataset_population_snapshot_for_dashboard)
    assert DEFAULT_NFL_HISTORICAL_DATASET_ID == "dataset.sports.nfl.historical_dataset"
