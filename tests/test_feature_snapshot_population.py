from __future__ import annotations

import copy
import importlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.data import (
    build_feature_snapshot_population,
    build_feature_snapshot_population_dashboard_snapshot,
    get_feature_snapshot_population_snapshot_for_dashboard,
)
from src.data.feature_registry import (
    CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID,
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
    build_feature_snapshot_context,
    build_feature_snapshot_context_id,
    build_feature_value_identity,
    list_feature_definition_ids,
)
from src.data.historical_research_database import build_historical_dataset_population
from src.data.nfl_injuries_research_asset_population import build_nfl_injuries_research_asset_population
from src.data.nfl_odds_research_asset_population import (
    build_nfl_odds_connector_bundle,
    build_nfl_odds_research_asset_population,
)
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.data.nfl_results_research_asset_population import build_nfl_results_research_asset_population
from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_population
from src.data.nfl_team_statistics_research_asset_population import build_nfl_team_statistics_research_asset_population
from src.data.nfl_weather_research_asset_population import build_nfl_weather_research_asset_population
from src.storage import LocalStorageEngine
from src.services.streamlit_dashboard_data import (
    get_feature_snapshot_population_snapshot_for_dashboard as get_feature_snapshot_population_snapshot_for_dashboard_service,
)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_phase50_sources(storage_path: Path) -> dict[str, object]:
    return _build_phase50_sources_with_optional_odds_bundle(storage_path)


def _build_phase50_sources_with_optional_odds_bundle(
    storage_path: Path,
    *,
    odds_bundle: dict[str, object] | None = None,
) -> dict[str, object]:
    for builder in (
        build_nfl_schedule_research_asset_population,
        build_nfl_results_research_asset_population,
        build_nfl_odds_research_asset_population,
        build_nfl_weather_research_asset_population,
        build_nfl_injuries_research_asset_population,
        build_nfl_team_statistics_research_asset_population,
    ):
        kwargs: dict[str, object] = {"storage_path": storage_path, "game_count": 1}
        if builder is build_nfl_odds_research_asset_population:
            kwargs["connector_bundle"] = odds_bundle
        assert builder(**kwargs)["ok"]
    dataset_result = build_historical_dataset_population(storage_path=storage_path)
    assert dataset_result["ok"] is True
    return dataset_result


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


def _feature_rows_by_key(rows: list[dict[str, object]]) -> dict[tuple[str, str, str], dict[str, object]]:
    return {
        (str(row["dataset_row_id"]), str(row["feature_id"]), str(row["market_type"])): row
        for row in rows
    }


def test_feature_snapshot_population_materializes_all_registered_features_and_preserves_grain(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "feature_population.sqlite"
    _build_phase50_sources(storage_path)

    result = build_feature_snapshot_population(storage_path=storage_path)

    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["dataset_id"] == DEFAULT_NFL_HISTORICAL_DATASET_ID
    assert result["dataset_row_count"] == 3
    assert result["feature_definition_count"] == len(list_feature_definition_ids())
    assert result["feature_snapshot_count"] == 114
    assert len(result["feature_rows"]) == 114
    assert len(result["feature_lineage_edges"]) == 115
    assert result["feature_population_summary_id"] == result["feature_population_summary"]["snapshot_id"]
    assert result["feature_population_summary"]["snapshot_kind"] == "feature_population_summary"
    assert all(row["snapshot_kind"] == "feature_value" for row in result["feature_rows"])
    assert all(row["feature_snapshot_grain_id"] == CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID for row in result["feature_rows"])

    context_ids = {str(row["dataset_row_id"]) for row in result["feature_rows"]}
    assert len(context_ids) == 3
    assert all(count == len(list_feature_definition_ids()) for count in Counter(str(row["dataset_row_id"]) for row in result["feature_rows"]).values())
    assert len({str(row["snapshot_id"]) for row in result["feature_rows"]}) == 114
    assert len({(str(row["dataset_row_id"]), str(row["feature_id"]), str(row["feature_context_id"])) for row in result["feature_rows"]}) == 114

    sample = next(row for row in result["feature_rows"] if row["feature_missingness_state"] != "present")
    sample_context = json.loads(sample["feature_context_json"])
    assert "label_" not in json.dumps(sample_context)
    assert sample["feature_missingness_reason"]
    assert sample["decision_cutoff_time"] == "2024-09-05T20:15:00Z"
    assert int((_parse_iso(str(sample["scheduled_kickoff_time"])) - _parse_iso(str(sample["decision_cutoff_time"]))).total_seconds()) == 300

    feature_context = build_feature_snapshot_context({
        **sample_context,
        "selected_source_row_ids_json": sample["selected_source_row_ids_json"],
        "source_certification_ids_json": sample["source_certification_ids_json"],
        "source_alignment_certification_ids_json": sample["source_alignment_certification_ids_json"],
        "source_lineage_ids_json": sample["source_lineage_ids_json"],
        "missing_required_assets_json": sample["missing_required_assets_json"],
    })
    assert build_feature_snapshot_context_id(feature_context) == str(sample["feature_context_id"])
    assert build_feature_value_identity(json.loads(sample["feature_definition_json"]), feature_context) == str(sample["snapshot_id"])


def test_feature_snapshot_population_is_idempotent_and_dashboard_reconstructs_persisted_state(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "feature_population_idempotent.sqlite"
    _build_phase50_sources(storage_path)

    first = build_feature_snapshot_population(storage_path=storage_path)
    second = build_feature_snapshot_population(storage_path=storage_path)
    dashboard = get_feature_snapshot_population_snapshot_for_dashboard(storage_path=storage_path)
    service_dashboard = get_feature_snapshot_population_snapshot_for_dashboard_service(storage_path)
    canonical_dashboard = build_feature_snapshot_population_dashboard_snapshot(storage_path=storage_path)
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["idempotent_reuse"] is True
    assert first["batch_id"] == second["batch_id"]
    assert [row["snapshot_id"] for row in first["feature_rows"]] == [row["snapshot_id"] for row in second["feature_rows"]]
    assert dashboard["ok"] is True
    assert dashboard["status"] == "ready"
    assert service_dashboard["ok"] is True
    assert service_dashboard["feature_snapshot_count"] == 114
    assert canonical_dashboard["ok"] is True
    assert canonical_dashboard["batch_id"] == dashboard["batch_id"]
    assert dashboard["feature_snapshot_count"] == 114
    assert dashboard["batch_id"] == first["batch_id"]
    assert dashboard["feature_population_summary_id"] == first["feature_population_summary_id"]
    assert len(dashboard["feature_lineage_edges"]) == 115
    assert p0_dashboard["feature_layer_readiness"]["status"] == "ready"
    assert p0_dashboard["feature_layer_readiness"]["feature_snapshot_count"] == 114
    assert p0_dashboard["readiness_summary"]["feature_snapshot_population_status"] == "ready"


def test_feature_snapshot_population_changes_identity_when_source_lineage_changes_but_ignores_raw_mutations_after_dataset_certification(
    tmp_path: Path,
) -> None:
    baseline_path = tmp_path / "feature_population_baseline.sqlite"
    changed_path = tmp_path / "feature_population_changed.sqlite"
    raw_mutated_path = tmp_path / "feature_population_raw_mutated.sqlite"

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
    _build_phase50_sources_with_optional_odds_bundle(changed_path, odds_bundle=odds_bundle)
    _build_phase50_sources(raw_mutated_path)

    baseline_dataset = build_historical_dataset_population(storage_path=baseline_path)
    changed_dataset = build_historical_dataset_population(storage_path=changed_path)
    raw_mutated_dataset = build_historical_dataset_population(storage_path=raw_mutated_path)

    assert baseline_dataset["ok"] is True
    assert changed_dataset["ok"] is True
    assert raw_mutated_dataset["ok"] is True

    baseline = build_feature_snapshot_population(storage_path=baseline_path)
    changed = build_feature_snapshot_population(storage_path=changed_path)

    raw_mutated_storage = LocalStorageEngine(raw_mutated_path)
    try:
        weather_row = dict(
            raw_mutated_storage.fetch(
                "nfl_weather_snapshots",
                order_by="weather_snapshot_id ASC",
                limit=1,
            )[0]
        )
        weather_row["lineage_id"] = "nfl_p0.v001.game.001.weather.raw.mutated.lineage"
        raw_mutated_storage.upsert("nfl_weather_snapshots", weather_row, key_columns=("weather_snapshot_id",))
    finally:
        raw_mutated_storage.close()

    raw_mutated = build_feature_snapshot_population(storage_path=raw_mutated_path)

    baseline_row = next(
        row
        for row in baseline["feature_rows"]
        if row["feature_id"] == "feature.sports.nfl.market.market_type" and row["market_type"] == "spread"
    )
    changed_row = next(
        row
        for row in changed["feature_rows"]
        if row["feature_id"] == "feature.sports.nfl.market.market_type" and row["market_type"] == "spread"
    )
    raw_mutated_row = next(
        row
        for row in raw_mutated["feature_rows"]
        if row["feature_id"] == "feature.sports.nfl.market.market_type" and row["market_type"] == "spread"
    )

    assert baseline_row["snapshot_id"] != changed_row["snapshot_id"]
    assert baseline_row["feature_lineage_id"] != changed_row["feature_lineage_id"]
    assert baseline_row["selected_source_row_ids_json"] == changed_row["selected_source_row_ids_json"]
    assert json.loads(baseline_row["source_lineage_ids_json"]) != json.loads(changed_row["source_lineage_ids_json"])

    assert baseline["batch_id"] == raw_mutated["batch_id"]
    assert [row["snapshot_id"] for row in baseline["feature_rows"]] == [row["snapshot_id"] for row in raw_mutated["feature_rows"]]
    assert raw_mutated_row["snapshot_id"] == baseline_row["snapshot_id"]


def test_feature_snapshot_population_package_exports_are_available() -> None:
    module = importlib.import_module("src.data")
    assert callable(module.build_feature_snapshot_population)
    assert callable(module.build_feature_snapshot_population_dashboard_snapshot)
    assert callable(module.get_feature_snapshot_population_snapshot_for_dashboard)
    assert callable(get_feature_snapshot_population_snapshot_for_dashboard_service)
