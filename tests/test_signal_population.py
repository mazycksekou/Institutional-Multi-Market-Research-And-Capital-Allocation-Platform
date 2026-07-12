from __future__ import annotations

import importlib
import json
from pathlib import Path

from src.data import (
    build_feature_snapshot_population,
    build_historical_dataset_population,
    build_math_engine_population,
)
from src.data.nfl_injuries_research_asset_population import build_nfl_injuries_research_asset_population
from src.data.nfl_odds_research_asset_population import build_nfl_odds_research_asset_population
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.data.nfl_results_research_asset_population import build_nfl_results_research_asset_population
from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_population
from src.data.nfl_team_statistics_research_asset_population import build_nfl_team_statistics_research_asset_population
from src.data.nfl_weather_research_asset_population import build_nfl_weather_research_asset_population
from src.market_intelligence.signal_population import (
    DEFAULT_SIGNAL_DATASET_ID,
    SIGNAL_DEFINITION_VERSION,
    SIGNAL_TRANSFORMATION_VERSION,
    SIGNAL_USAGE_MODE,
    build_signal_population,
    build_signal_population_dashboard_snapshot,
    build_signal_value_identity,
    get_signal_definition,
    get_signal_population_snapshot_for_dashboard,
    list_signal_definition_ids,
    list_signal_definitions,
    summarize_signal_registry,
    validate_signal_registry,
)
from src.services.streamlit_dashboard_data import get_signal_population_snapshot_for_dashboard as get_signal_population_snapshot_for_dashboard_service
from src.storage import LocalStorageEngine


def _build_phase52_sources(storage_path: Path) -> None:
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


def test_signal_registry_definitions_are_observation_only_and_portable() -> None:
    definitions = list_signal_definitions()
    validation = validate_signal_registry(definitions)
    summary = summarize_signal_registry()

    assert validation["ok"] is True, validation["errors"]
    assert summary["definition_count"] == len(definitions) == len(list_signal_definition_ids())
    assert summary["classification_counts"] == {"direct": 7, "deterministic_derived": 3}
    assert summary["usage_mode_counts"] == {SIGNAL_USAGE_MODE: 10}
    assert summary["families"] == [
        "data_quality_context",
        "market_context",
        "regime_context",
    ]

    for definition in definitions:
        assert definition["signal_version"] == SIGNAL_DEFINITION_VERSION
        assert definition["transformation_version"] == SIGNAL_TRANSFORMATION_VERSION
        assert definition["signal_usage_mode"] == SIGNAL_USAGE_MODE
        assert definition["classification"] in {"direct", "deterministic_derived"}
        assert definition["entity_scope"] in {"market_context", "data_quality_context", "regime_context"}
        assert definition["portability_classification"] == "cross_market_signal"
        assert definition["signal_id"].startswith("signal.sports.")
        assert "bet" not in definition["signal_id"].lower()
        assert "trade" not in definition["signal_id"].lower()
        assert "recommend" not in definition["signal_name"].lower()
        assert definition["dataset_grain_compatibility"] == "dataset.sports.nfl.signal_snapshot.dataset_row_scope.v1"


def test_signal_population_materializes_reusable_signals_and_reuses_persisted_state(tmp_path: Path) -> None:
    storage_path = tmp_path / "signal_population.sqlite"
    _build_phase52_sources(storage_path)

    first = build_signal_population(storage_path=storage_path)
    second = build_signal_population(storage_path=storage_path)
    dashboard = build_signal_population_dashboard_snapshot(storage_path=storage_path)
    service_dashboard = get_signal_population_snapshot_for_dashboard_service(storage_path)
    canonical_dashboard = get_signal_population_snapshot_for_dashboard(storage_path=storage_path)
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert first["ok"] is True
    assert first["status"] == "certified"
    assert first["readiness"] == "signal_ready"
    assert first["lifecycle_state"] == "signal_ready"
    assert first["dataset_id"] == DEFAULT_SIGNAL_DATASET_ID
    assert first["dataset_row_count"] == 3
    assert first["signal_definition_count"] == len(list_signal_definition_ids()) == 10
    assert first["signal_context_count"] == 3
    assert first["signal_row_count"] == 30
    assert len(first["signal_rows"]) == 30
    assert len(first["signal_summary_rows"]) == 1
    assert len(first["signal_lineage_edges"]) == 30
    assert len(first["signal_alignment_rows"]) == 31
    assert len(first["signal_lifecycle_rows"]) == 1
    assert first["signal_alignment_rows"][0]["source_file"] == str(storage_path)
    assert first["signal_alignment_rows"][0]["result_timestamp"]
    assert first["dataset_certification_status"] == "certified"
    assert first["signal_validation"]["ok"] is True
    assert first["validation"]["ok"] is True
    assert all(row["signal_usage_mode"] == SIGNAL_USAGE_MODE for row in first["signal_rows"])
    assert len({row["snapshot_id"] for row in first["signal_rows"]}) == 30
    assert len({(row["dataset_row_id"], row["decision_context_id"], row["signal_id"]) for row in first["signal_rows"]}) == 30
    assert "label_" not in json.dumps(first["signal_rows"]).lower()
    assert "label_" not in json.dumps(first["signal_population_summary"]).lower()
    assert first["join_diagnostics"]["signal_row_count"] == 30
    assert first["join_diagnostics"]["signal_definition_count"] == 10
    assert first["join_diagnostics"]["signal_context_ids"]
    assert first["signal_population_summary"]["signal_id"] == "signal.sports.reusable_signals.summary"
    assert first["signal_population_summary"]["signal_usage_mode"] == SIGNAL_USAGE_MODE
    assert first["signal_population_summary"]["source_math_certification_id"]
    assert first["signal_population_summary"]["source_math_dataset_certification_id"]

    sample_row = first["signal_rows"][0]
    sample_definition = get_signal_definition(sample_row["signal_id"])
    signal_value = json.loads(sample_row["signal_value_json"])
    signal_context = {
        "batch_id": sample_row["batch_id"],
        "dataset_row_id": sample_row["dataset_row_id"],
        "decision_context_id": sample_row["decision_context_id"],
    }
    assert build_signal_value_identity(
        sample_definition,
        signal_context,
        value=signal_value,
        source_math_snapshot_ids=json.loads(sample_row["source_math_snapshot_ids_json"]),
    ) == sample_row["snapshot_id"]
    assert build_signal_value_identity(
        sample_definition,
        signal_context,
        value=signal_value,
        source_math_snapshot_ids=json.loads(sample_row["source_math_snapshot_ids_json"]),
    ) == sample_row["snapshot_id"]
    assert sample_row["source_math_certification_id"]
    assert sample_row["source_math_dataset_certification_id"]

    sibling_row = next(
        row
        for row in first["signal_rows"]
        if row["signal_id"] == sample_row["signal_id"] and row["dataset_row_id"] != sample_row["dataset_row_id"]
    )
    assert sibling_row["snapshot_id"] != sample_row["snapshot_id"]

    assert second["ok"] is True
    assert second["status"] == "certified"
    assert second["batch_id"] == first["batch_id"]
    assert second["signal_population_summary_id"] == first["signal_population_summary_id"]
    assert second["signal_evidence_package_id"] == first["signal_evidence_package_id"]
    assert [row["snapshot_id"] for row in second["signal_rows"]] == [row["snapshot_id"] for row in first["signal_rows"]]
    assert second["idempotent_reuse"] is True

    assert dashboard["ok"] is True
    assert dashboard["status"] == "certified"
    assert dashboard["readiness"] == "signal_ready"
    assert dashboard["batch_id"] == first["batch_id"]
    assert dashboard["signal_population_summary_id"] == first["signal_population_summary_id"]
    assert dashboard["signal_row_count"] == 30
    assert dashboard["signal_definition_count"] == 10
    assert len(dashboard["signal_lineage_edges"]) == 30
    assert dashboard["signal_validation"]["ok"] is True

    assert service_dashboard["ok"] is True
    assert service_dashboard["status"] == "certified"
    assert service_dashboard["batch_id"] == first["batch_id"]
    assert service_dashboard["signal_population_summary_id"] == first["signal_population_summary_id"]
    assert service_dashboard["signal_row_count"] == 30

    assert canonical_dashboard["ok"] is True
    assert canonical_dashboard["batch_id"] == first["batch_id"]

    assert p0_dashboard["signal_layer_readiness"]["status"] == "certified"
    assert p0_dashboard["signal_layer_readiness"]["lifecycle_state"] == "signal_ready"
    assert p0_dashboard["signal_layer_readiness"]["readiness"] == "signal_ready"
    assert p0_dashboard["signal_layer_readiness"]["validation_state"] == "validated"
    assert p0_dashboard["signal_layer_readiness"]["signal_row_count"] == 30
    assert p0_dashboard["signal_layer_readiness"]["signal_definition_count"] == 10
    assert p0_dashboard["readiness_summary"]["signal_population_status"] == "certified"


def test_signal_population_ignores_raw_mutations_after_math_certification(tmp_path: Path) -> None:
    storage_path = tmp_path / "signal_population_raw_mutation.sqlite"
    _build_phase52_sources(storage_path)

    baseline = build_signal_population(storage_path=storage_path)

    storage = LocalStorageEngine(storage_path)
    try:
        raw_row = dict(storage.fetch("historical_dataset_rows", order_by="snapshot_id ASC", limit=1)[0])
        raw_row["payload_json"] = json.dumps({"mutated": True, "snapshot_id": raw_row["snapshot_id"]}, sort_keys=True)
        storage.upsert("historical_dataset_rows", raw_row, key_columns=("snapshot_id",))
    finally:
        storage.close()

    mutated = build_signal_population(storage_path=storage_path)

    assert mutated["ok"] is True
    assert mutated["batch_id"] == baseline["batch_id"]
    assert mutated["signal_population_summary_id"] == baseline["signal_population_summary_id"]
    assert [row["snapshot_id"] for row in mutated["signal_rows"]] == [row["snapshot_id"] for row in baseline["signal_rows"]]


def test_signal_population_package_exports_are_available() -> None:
    module = importlib.import_module("src.market_intelligence.signal_population")
    assert callable(module.build_signal_population)
    assert callable(module.build_signal_population_dashboard_snapshot)
    assert callable(module.get_signal_population_snapshot_for_dashboard)
    assert callable(module.build_signal_value_identity)
