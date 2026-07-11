from __future__ import annotations

from datetime import datetime
import importlib

import pytest

from src.data.feature_registry import (
    CANONICAL_DATASET_ROW_GRAIN_ID,
    CANONICAL_FEATURE_REGISTRY_DOC,
    CANONICAL_FEATURE_SNAPSHOT_CONTRACT_DOC,
    CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID,
    CANONICAL_FEATURE_STORE_ARCHITECTURE_DOC,
    CANONICAL_FEATURE_STORE_CONTRACT_DOC,
    DEFAULT_CUTOFF_SEMANTICS,
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
    build_feature_snapshot_context,
    build_feature_snapshot_context_id,
    build_feature_value_identity,
    get_feature_definition,
    list_deferred_feature_ids,
    list_feature_definition_ids,
    list_feature_definitions,
    list_feature_families,
    summarize_dataset_row_contexts,
    summarize_feature_registry,
    validate_feature_registry,
)
from src.data.historical_research_database import build_historical_dataset_population
from src.data.nfl_injuries_research_asset_population import (
    build_nfl_injuries_research_asset_population,
)
from src.data.nfl_odds_research_asset_population import build_nfl_odds_research_asset_population
from src.data.nfl_results_research_asset_population import (
    build_nfl_results_research_asset_population,
)
from src.data.nfl_schedule_research_asset_population import (
    build_nfl_schedule_research_asset_population,
)
from src.data.nfl_team_statistics_research_asset_population import (
    build_nfl_team_statistics_research_asset_population,
)
from src.data.nfl_weather_research_asset_population import (
    build_nfl_weather_research_asset_population,
)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_phase50_sources(storage_path) -> dict[str, object]:
    assert build_nfl_schedule_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_results_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_odds_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_weather_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_injuries_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    assert build_nfl_team_statistics_research_asset_population(storage_path=storage_path, game_count=1)["ok"]
    return build_historical_dataset_population(storage_path=storage_path)


@pytest.fixture(scope="module")
def phase50_dataset_result(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("phase51a_feature_registry")
    storage_path = tmp_dir / "phase50_dataset.sqlite"
    result = _build_phase50_sources(storage_path)
    assert result["ok"] is True
    return result


def test_feature_registry_module_imports_without_src_data_export_cycle():
    module = importlib.import_module("src.data.feature_registry")
    assert module.FEATURE_REGISTRY_SCHEMA_VERSION == "src.data.feature_registry.v1"


def test_feature_registry_reuses_canonical_runtime_and_doc_owners():
    assert DEFAULT_NFL_HISTORICAL_DATASET_ID == "dataset.sports.nfl.historical_dataset"
    assert CANONICAL_DATASET_ROW_GRAIN_ID == "dataset.sports.nfl.historical_dataset.event_market_context.v1"
    assert CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID == "dataset.sports.nfl.feature_snapshot.dataset_row_scope.v1"
    assert CANONICAL_FEATURE_REGISTRY_DOC.endswith("docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md")
    assert CANONICAL_FEATURE_STORE_CONTRACT_DOC.endswith("docs/contracts/NFL_FEATURE_STORE_CONTRACT.md")
    assert CANONICAL_FEATURE_SNAPSHOT_CONTRACT_DOC.endswith("docs/contracts/FEATURE_SNAPSHOT_CONTRACT.md")
    assert CANONICAL_FEATURE_STORE_ARCHITECTURE_DOC.endswith("docs/architecture/FEATURE_STORE_ARCHITECTURE.md")


def test_feature_registry_definitions_are_complete_unique_and_dataset_only():
    definitions = list_feature_definitions()
    validation = validate_feature_registry(definitions)
    assert validation["ok"] is True, validation["errors"]

    ids = list_feature_definition_ids()
    assert ids
    assert len(ids) == len(set(ids))

    families = list_feature_families()
    assert families == [
        "data_quality_context",
        "event_context",
        "injury_context",
        "market_context",
        "team_statistics_context",
        "weather_context",
    ]

    for definition in definitions:
        assert definition["feature_version"] == "phase5.1a.feature_definitions.v1"
        assert definition["dataset_grain_compatibility"] == CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID
        assert definition["cutoff_semantics"] == DEFAULT_CUTOFF_SEMANTICS
        assert definition["transformation_version"] == "phase5.1b.feature_snapshot_population.v1"
        assert definition["classification"] in {"direct", "deterministic_derived"}
        assert definition["value_type"]
        assert definition["unit"]
        assert definition["missingness_policy"]
        for field_ref in definition["source_dataset_field_refs"]:
            assert not field_ref.startswith("label_")
            assert "nfl_schedule" not in field_ref
            assert "nfl_results" not in field_ref
            assert "nfl_odds_snapshots" not in field_ref
            assert "nfl_weather_snapshots" not in field_ref
            assert "nfl_injury_snapshots" not in field_ref
            assert "nfl_team_stats_snapshots" not in field_ref


def test_phase50_fixture_exposes_three_distinct_dataset_contexts(phase50_dataset_result):
    summary = summarize_dataset_row_contexts(phase50_dataset_result["dataset_rows"])
    assert summary["dataset_row_grain_id"] == CANONICAL_DATASET_ROW_GRAIN_ID
    assert summary["identity_fields"] == [
        "dataset_id",
        "game_id",
        "market_type",
        "selection",
        "book",
        "decision_cutoff_time",
    ]
    assert summary["context_count"] == 3
    assert {
        (
            context["market_type"],
            context["selection"],
            context["book"],
            context["team_side"],
        )
        for context in summary["contexts"]
    } == {
        ("moneyline", "home", "consensus", "home"),
        ("spread", "home", "consensus", "home"),
        ("total", "over", "consensus", ""),
    }


def test_feature_snapshot_contexts_preserve_market_scope_and_total_scope(phase50_dataset_result):
    contexts = [build_feature_snapshot_context(row) for row in phase50_dataset_result["dataset_rows"]]
    context_ids = [build_feature_snapshot_context_id(context) for context in contexts]
    assert len(context_ids) == 3
    assert len(set(context_ids)) == 3

    total_context = next(context for context in contexts if context["market_type"] == "total")
    assert total_context["team_side"] == ""
    assert total_context["home_team_id"] == "BUF"
    assert total_context["away_team_id"] == "KC"
    assert total_context["decision_cutoff_time"] == "2024-09-05T20:15:00Z"

    spread_context = next(context for context in contexts if context["market_type"] == "spread")
    assert spread_context["team_side"] == "home"
    assert spread_context["home_team_id"] == "BUF"
    assert spread_context["away_team_id"] == "KC"


def test_feature_value_identities_are_deterministic_and_context_sensitive(phase50_dataset_result):
    definition = get_feature_definition("feature.sports.nfl.market.market_type")
    spread_row = next(row for row in phase50_dataset_result["dataset_rows"] if row["market_type"] == "spread")
    moneyline_row = next(row for row in phase50_dataset_result["dataset_rows"] if row["market_type"] == "moneyline")

    spread_context = build_feature_snapshot_context(spread_row)
    moneyline_context = build_feature_snapshot_context(moneyline_row)

    spread_id_first = build_feature_value_identity(definition, spread_context)
    spread_id_second = build_feature_value_identity(definition, spread_context)
    moneyline_id = build_feature_value_identity(definition, moneyline_context)

    assert spread_id_first == spread_id_second
    assert spread_id_first != moneyline_id


def test_feature_registry_preserves_kickoff_minus_five_cutoff(phase50_dataset_result):
    row = next(row for row in phase50_dataset_result["dataset_rows"] if row["market_type"] == "spread")
    kickoff = _parse_iso(row["scheduled_kickoff_time"])
    cutoff = _parse_iso(row["decision_cutoff_time"])
    assert int((kickoff - cutoff).total_seconds()) == 300

    summary = summarize_feature_registry()
    assert set(summary["classifications"]) == {"direct", "deterministic_derived"}
    assert summary["classifications"]["direct"] > 0
    assert summary["classifications"]["deterministic_derived"] > 0


def test_predictor_registry_excludes_outcomes_and_math_outputs():
    active_ids = set(list_feature_definition_ids())
    deferred = list_deferred_feature_ids()

    assert "feature.sports.nfl.market.edge" not in active_ids
    assert "feature.sports.nfl.model.win_probability" not in active_ids
    assert set(deferred["deferred_mathematical_engine_output"]).isdisjoint(active_ids)

    for definition in list_feature_definitions():
        assert definition["predictor_namespace"] is True
        assert not any(field_ref.startswith("label_") for field_ref in definition["source_dataset_field_refs"])


def test_invalid_duplicate_feature_definitions_are_rejected():
    definitions = list_feature_definitions()
    duplicated = [*definitions, dict(definitions[0])]
    validation = validate_feature_registry(duplicated)
    assert validation["ok"] is False
    assert any(error.startswith("duplicate_feature_definition:feature.sports.nfl.event.season") for error in validation["errors"])
