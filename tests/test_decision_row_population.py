from __future__ import annotations

import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.backtesting import (
    build_decision_row_population,
    build_decision_row_population_dashboard_snapshot,
    build_decision_snapshot_context_id,
    build_decision_value_identity,
    get_decision_definition,
    list_decision_definition_ids,
    list_decision_definitions,
    summarize_decision_registry,
    validate_decision_registry,
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
from src.data.math_engine_population import build_math_engine_population
from src.market_intelligence.signal_population import build_signal_population
from src.services.streamlit_dashboard_data import (
    get_decision_row_population_snapshot_for_dashboard as get_decision_row_population_snapshot_for_dashboard_service,
)
from src.data.research_asset_lifecycle_runtime import (
    build_research_asset_identity_contract,
    build_time_entity_alignment_certification,
)


def _build_phase53_sources(storage_path: Path) -> None:
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


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_decision_registry_definitions_are_observation_only_and_portable() -> None:
    definitions = list_decision_definitions()
    validation = validate_decision_registry(definitions)
    summary = summarize_decision_registry()
    definition = get_decision_definition("decision.sports.backtest_eligibility")

    assert validation["ok"] is True, validation["errors"]
    assert summary["definition_count"] == len(definitions) == len(list_decision_definition_ids()) == 1
    assert summary["classification_counts"] == {"deterministic_derived": 1}
    assert summary["value_type_counts"] == {"string": 1}
    assert summary["usage_mode_counts"] == {"backtest_readiness": 1}
    assert summary["families"] == ["backtest_readiness"]
    assert definition is not None
    assert definition["decision_id"] == "decision.sports.backtest_eligibility"
    assert definition["classification"] == "deterministic_derived"
    assert definition["value_type"] == "string"
    assert definition["unit"] == "state"
    assert definition["entity_scope"] == "decision_context"
    assert definition["decision_usage_mode"] == "backtest_readiness"
    assert definition["portability_classification"] == "cross_market_decision"
    assert definition["dataset_grain_compatibility"] == "dataset.sports.nfl.decision_snapshot.dataset_row_scope.v1"
    assert "bet" not in definition["decision_name"].lower()
    assert "trade" not in definition["decision_name"].lower()
    assert "recommend" not in definition["decision_name"].lower()


def test_decision_identity_helpers_preserve_grain_and_cutoff_and_alignment_batches_are_row_specific() -> None:
    definition = get_decision_definition("decision.sports.backtest_eligibility")
    assert definition is not None

    context = {
        "dataset_row_id": "dataset-row-1",
        "decision_context_id": "decision-context-1",
        "source_signal_context_id": "signal-context-1",
        "event_id": "nfl-p0-game-001",
        "selection": "decision.sports.backtest_eligibility",
        "book": "consensus",
        "scheduled_kickoff_time": "2024-09-05T20:20:00Z",
        "decision_cutoff_time": "2024-09-05T20:15:00Z",
        "source_signal_snapshot_ids_json": json.dumps(["signal-snapshot-1"], sort_keys=True),
    }

    context_id = build_decision_snapshot_context_id(context)
    changed_context_id = build_decision_snapshot_context_id({**context, "decision_context_id": "decision-context-2"})
    value_identity = build_decision_value_identity(
        definition,
        context,
        value="BACKTEST_ELIGIBLE",
        source_signal_snapshot_ids=["signal-snapshot-1"],
    )
    changed_value_identity = build_decision_value_identity(
        definition,
        {**context, "decision_context_id": "decision-context-2"},
        value="BACKTEST_ELIGIBLE",
        source_signal_snapshot_ids=["signal-snapshot-1"],
    )

    assert context_id != changed_context_id
    assert value_identity != changed_value_identity

    identity = build_research_asset_identity_contract(
        asset_id="decision.sports.reusable_decision_rows",
        asset_family="decision",
        market_profile="sports:nfl",
        market="sports:nfl",
        league="nfl",
        sport="football",
        season="2024",
        week_or_date="1",
        event_id="nfl-p0-game-001",
        market_id="decision.sports.backtest_eligibility",
        selection="decision.sports.backtest_eligibility",
        provider="repository",
        connector="signal_population",
        schema_version="src.backtesting.decision_row_population.v1",
        lineage_version="phase5.4.decision_row_population.v1",
        asset_name="Reusable Decision Rows",
        asset_type="decision_snapshot",
        team_id="BUF",
        game_id="nfl-p0-game-001",
        market_type="decision",
    )
    base_row = {
        "asset_id": identity.asset_id,
        "asset_family": identity.asset_family,
        "asset_name": identity.asset_name,
        "asset_type": identity.asset_type,
        "lineage_version": identity.lineage_version,
        "market_id": identity.market_id,
        "provider_timestamp": "2024-09-05T20:15:00Z",
        "snapshot_time": "2024-09-05T20:15:00Z",
        "decision_time": "2024-09-05T20:15:00Z",
        "result_timestamp": "2024-09-05T20:16:00Z",
        "market_profile": identity.market_profile,
        "market": identity.market,
        "league": identity.league,
        "sport": identity.sport,
        "season": identity.season,
        "week_or_date": identity.week_or_date,
        "event_id": identity.event_id,
        "game_id": identity.game_id,
        "provider": identity.provider,
        "schema_version": identity.schema_version,
        "team_id": identity.team_id,
        "participant_id": "",
        "selection": identity.selection,
        "connector": identity.connector,
        "market_type": identity.market_type,
        "dataset_id": "dataset.sports.nfl.decision_rows",
        "dataset_name": "nfl_decision_rows",
        "snapshot_id": "snapshot-a",
        "batch_id": "batch-a",
        "decision_id": "decision.sports.backtest_eligibility",
        "decision_name": "Backtest Eligibility",
        "decision_readiness_status": "BACKTEST_ELIGIBLE",
        "decision_value_json": json.dumps("BACKTEST_ELIGIBLE"),
        "decision_context_id": "decision-context-1",
        "decision_snapshot_context_id": "snapshot-a",
        "source_signal_batch_id": "signal-batch",
        "source_signal_population_summary_id": "signal-summary",
        "scheduled_kickoff_time": "2024-09-05T20:20:00Z",
        "decision_cutoff_time": "2024-09-05T20:15:00Z",
        "created_at": "2024-09-05T20:15:01Z",
        "updated_at": "2024-09-05T20:15:01Z",
    }
    row_b = {**base_row, "snapshot_id": "snapshot-b", "batch_id": "batch-b", "decision_snapshot_context_id": "snapshot-b"}

    alignment_a = build_time_entity_alignment_certification(
        identity=identity,
        rows=[base_row],
        required_fields=(
            "dataset_id",
            "dataset_name",
            "snapshot_id",
            "batch_id",
            "decision_id",
            "decision_name",
            "decision_readiness_status",
            "decision_value_json",
            "decision_context_id",
            "decision_snapshot_context_id",
            "source_signal_batch_id",
            "source_signal_population_summary_id",
        ),
        required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
        created_at="2024-09-05T20:15:02Z",
        asset_name="Reusable Decision Rows",
        asset_type="decision_snapshot",
        batch_id="snapshot-a",
    )
    alignment_b = build_time_entity_alignment_certification(
        identity=identity,
        rows=[row_b],
        required_fields=(
            "dataset_id",
            "dataset_name",
            "snapshot_id",
            "batch_id",
            "decision_id",
            "decision_name",
            "decision_readiness_status",
            "decision_value_json",
            "decision_context_id",
            "decision_snapshot_context_id",
            "source_signal_batch_id",
            "source_signal_population_summary_id",
        ),
        required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
        created_at="2024-09-05T20:15:02Z",
        asset_name="Reusable Decision Rows",
        asset_type="decision_snapshot",
        batch_id="snapshot-b",
    )

    assert alignment_a.alignment_certification_id != alignment_b.alignment_certification_id
    assert alignment_a.alignment_status == "aligned"
    assert alignment_b.alignment_status == "aligned"


def test_decision_row_population_materializes_reusable_decision_rows_and_reuses_persisted_state(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "decision_population.sqlite"
    _build_phase53_sources(storage_path)

    first = build_decision_row_population(storage_path=storage_path)
    second = build_decision_row_population(storage_path=storage_path)
    dashboard = build_decision_row_population_dashboard_snapshot(storage_path=storage_path)
    service_dashboard = get_decision_row_population_snapshot_for_dashboard_service(storage_path)
    canonical_dashboard = build_decision_row_population_dashboard_snapshot(storage_path=storage_path)
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert first["ok"] is True
    assert first["status"] == "certified"
    assert first["readiness"] == "backtest_ready"
    assert first["lifecycle_state"] == "backtest_ready"
    assert first["dataset_id"] == "dataset.sports.nfl.decision_rows"
    assert first["decision_definition_count"] == len(list_decision_definition_ids()) == 1
    assert first["decision_row_count"] == 3
    assert first["decision_context_count"] == 3
    assert len(first["decision_rows"]) == 3
    assert len(first["decision_alignment_rows"]) == 4
    assert len(first["decision_lineage_edges"]) == 3
    assert len(first["decision_lifecycle_rows"]) == 1
    assert len({row["snapshot_id"] for row in first["decision_rows"]}) == 3
    assert len({(row["dataset_row_id"], row["decision_context_id"], row["decision_id"]) for row in first["decision_rows"]}) == 3
    assert len({row["decision_snapshot_context_id"] for row in first["decision_rows"]}) == 3
    assert len({row["alignment_certification_id"] for row in first["decision_alignment_rows"]}) == 4
    assert len({row["batch_id"] for row in first["decision_alignment_rows"]}) == 4
    assert all(row["decision_readiness_status"] == "BACKTEST_ELIGIBLE" for row in first["decision_rows"])
    assert all(row["readiness"] == "backtest_ready" for row in first["decision_rows"])
    assert all(row["decision_usage_mode"] == "backtest_readiness" for row in first["decision_rows"])
    assert all(row["decision_missingness_state"] == "present" for row in first["decision_rows"])
    assert all(row["point_in_time_status"] == "safe" for row in first["decision_rows"])
    assert all(row["predictor_outcome_separation_status"] == "separated" for row in first["decision_rows"])
    assert all(
        int((
            _parse_iso(str(row["scheduled_kickoff_time"])) - _parse_iso(str(row["decision_cutoff_time"]))
        ).total_seconds())
        == 300
        for row in first["decision_rows"]
    )
    assert first["validation"]["ok"] is True
    assert first["decision_validation"]["ok"] is True
    assert first["dataset_certification_status"] == "certified"
    assert first["decision_population_summary"]["snapshot_kind"] == "decision_population_summary"
    assert first["decision_population_summary"]["decision_count"] == 3
    assert first["decision_population_summary"]["record_count"] == 3
    assert first["decision_population_summary"]["decision_readiness_status"] == "BACKTEST_ELIGIBLE"
    assert first["decision_population_summary"]["source_signal_batch_id"]
    assert len(first["decision_alignment_rows"]) == 4
    assert all(row["status"] == "aligned" for row in first["decision_alignment_rows"])
    assert len({row["batch_id"] for row in first["decision_alignment_rows"]}) == 4
    assert len({row["alignment_certification_id"] for row in first["decision_alignment_rows"]}) == 4

    assert second["ok"] is True
    assert second["status"] == "certified"
    assert second["batch_id"] == first["batch_id"]
    assert second["decision_population_summary_id"] == first["decision_population_summary_id"]
    assert second["decision_evidence_package_id"] == first["decision_evidence_package_id"]
    assert [row["snapshot_id"] for row in second["decision_rows"]] == [row["snapshot_id"] for row in first["decision_rows"]]
    assert second["idempotent_reuse"] is True
    assert second["decision_validation"]["ok"] is True

    assert dashboard["ok"] is True
    assert dashboard["status"] == "certified"
    assert dashboard["readiness"] == "backtest_ready"
    assert dashboard["lifecycle_state"] == "backtest_ready"
    assert dashboard["batch_id"] == first["batch_id"]
    assert dashboard["decision_population_summary_id"] == first["decision_population_summary_id"]
    assert dashboard["decision_row_count"] == 3
    assert dashboard["decision_definition_count"] == 1
    assert len(dashboard["decision_alignment_rows"]) == 4
    assert dashboard["decision_validation"]["ok"] is True
    assert dashboard["dataset_certification_status"] == "certified"

    assert service_dashboard["ok"] is True
    assert service_dashboard["status"] == "certified"
    assert service_dashboard["batch_id"] == first["batch_id"]
    assert service_dashboard["decision_row_count"] == 3

    assert canonical_dashboard["ok"] is True
    assert canonical_dashboard["batch_id"] == dashboard["batch_id"]

    assert p0_dashboard["decision_layer_readiness"]["status"] == "certified"
    assert p0_dashboard["decision_layer_readiness"]["lifecycle_state"] == "backtest_ready"
    assert p0_dashboard["decision_layer_readiness"]["readiness"] == "backtest_ready"
    assert p0_dashboard["decision_layer_readiness"]["decision_row_count"] == 3
    assert p0_dashboard["decision_layer_readiness"]["decision_definition_count"] == 1
    assert p0_dashboard["readiness_summary"]["decision_row_population_status"] == "certified"


def test_decision_row_population_rejects_missing_signal_layer(tmp_path: Path) -> None:
    result = build_decision_row_population(storage_path=tmp_path / "decision_population_missing.sqlite")

    assert result["ok"] is False
    assert result["status"] != "certified"
    assert result["readiness"] == "blocked"
    assert result["unresolved_blockers"]


def test_decision_row_population_package_exports_are_available() -> None:
    module = importlib.import_module("src.backtesting")
    assert callable(module.build_decision_row_population)
    assert callable(module.build_decision_row_population_dashboard_snapshot)
    assert callable(module.build_decision_snapshot_context_id)
    assert callable(module.build_decision_value_identity)
    assert callable(module.get_decision_row_population_snapshot_for_dashboard)
