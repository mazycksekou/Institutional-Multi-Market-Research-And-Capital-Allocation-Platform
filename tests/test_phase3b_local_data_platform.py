from __future__ import annotations

from pathlib import Path

import pytest

from src.data.local_platform import (
    build_local_platform_dashboard_snapshot,
    build_synthetic_local_dataset,
    create_local_platform,
)
from src.services.streamlit_dashboard_data import get_local_platform_snapshot_for_dashboard
from src.services.streamlit_dashboard_facade import get_local_platform_snapshot_for_dashboard as facade_get_local_platform_snapshot_for_dashboard
from src.storage import LocalStorageEngine, backend_available, create_local_storage_engine


def test_local_storage_engine_round_trip_and_duckdb_guard(tmp_path: Path) -> None:
    database_path = tmp_path / "local_store.sqlite"

    assert backend_available("sqlite") is True
    assert backend_available("duckdb") is False

    engine = create_local_storage_engine(database_path)
    try:
        assert isinstance(engine, LocalStorageEngine)
        assert engine.table_exists("provider_metadata") is True

        row = {
            "schema_version": "src.storage.local_store.test",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "source": "test",
            "provider": "provider_a",
            "market": "mixed",
            "market_type": "mixed",
            "asset_class": "mixed",
            "snapshot_id": "snapshot-1",
            "lineage_id": "lineage-1",
            "version_id": "version-1",
            "quality_score": 1.0,
            "provider_id": "provider_a",
            "provider_name": "Provider A",
            "provider_type": "sportsbook_odds",
            "contract_version": "v1",
            "metadata_json": "{}",
        }
        engine.upsert("provider_metadata", row, key_columns=("provider_id",))
        fetched = engine.fetch("provider_metadata", where="provider_id = ?", params=["provider_a"], limit=1)
        assert fetched and fetched[0]["provider_id"] == "provider_a"
        health = engine.health()
        assert health["backend"] == "sqlite"
        assert health["table_count"] >= 1
    finally:
        engine.close()

    with pytest.raises(RuntimeError):
        create_local_storage_engine(tmp_path / "duckdb.sqlite", backend="duckdb")


def test_local_platform_end_to_end_round_trip(tmp_path: Path) -> None:
    platform_path = tmp_path / "local_platform.sqlite"
    fixture = build_synthetic_local_dataset(12)

    platform = create_local_platform(platform_path)
    try:
        result = platform.ingest_dataset(
            fixture["rows"],
            contract=fixture["dataset"],
            validation_contract=fixture["validation_contract"],
        )

        assert result["ok"] is True
        dataset_id = result["dataset"]["dataset_id"]

        datasets = platform.list_datasets()
        versions = platform.list_versions(dataset_id)
        validations = platform.list_validation_results(dataset_id)
        snapshots = platform.list_feature_snapshots(dataset_id)
        lineage_edges = platform.list_lineage_edges(dataset_id)
        readback = platform.read_dataset(dataset_id)
        dashboard = platform.dashboard_snapshot(dataset_id)

        assert len(datasets) == 1
        assert readback["registry"]["dataset_id"] == dataset_id
        assert len(versions) == 1
        assert len(validations) == 1
        assert len(snapshots) == 1
        assert len(lineage_edges) == len(fixture["rows"]) * 2
        assert dashboard["ok"] is True
        assert dashboard["selected_dataset_id"] == dataset_id
        assert dashboard["validation_summary"]["status"] == "validated"
        assert dashboard["lineage_summary"]["edge_count"] == len(fixture["rows"]) * 2
        assert dashboard["storage"]["backend"] == "sqlite"
    finally:
        platform.close()

    service_snapshot = get_local_platform_snapshot_for_dashboard(platform_path, dataset_id=fixture["dataset"].dataset_id)
    facade_snapshot = facade_get_local_platform_snapshot_for_dashboard(platform_path, dataset_id=fixture["dataset"].dataset_id)
    canonical_snapshot = build_local_platform_dashboard_snapshot(platform_path, dataset_id=fixture["dataset"].dataset_id)

    assert service_snapshot["ok"] is True
    assert facade_snapshot["ok"] is True
    assert canonical_snapshot["ok"] is True
    assert service_snapshot["selected_dataset_id"] == fixture["dataset"].dataset_id
    assert facade_snapshot["selected_dataset_id"] == fixture["dataset"].dataset_id
    assert canonical_snapshot["selected_dataset_id"] == fixture["dataset"].dataset_id

