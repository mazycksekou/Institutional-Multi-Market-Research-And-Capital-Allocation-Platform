from __future__ import annotations

from pathlib import Path

from src.data.historical_dataset_acquisition_runtime import (
    HistoricalDatasetAcquisitionRuntime,
    build_historical_dataset_acquisition_runtime_dashboard_snapshot,
    get_historical_dataset_acquisition_runtime_snapshot_for_dashboard,
)
from src.data.nfl_p0_foundation import build_nfl_p0_fixture, get_nfl_p0_market_profile


def test_historical_dataset_acquisition_runtime_stages_raw_acquisition_cache(tmp_path: Path) -> None:
    storage_path = tmp_path / "historical_acquisition_runtime.sqlite"
    fixture = build_nfl_p0_fixture(2)
    profile = get_nfl_p0_market_profile()
    assert profile.profile_id == "sports:nfl"

    runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path)
    try:
        result = runtime.stage_raw_acquisition_cache(fixture, profile_id="sports:nfl")

        assert result["ok"]
        assert result["status"] == "raw_cache_ready"
        assert result["raw_record_count"] > 0
        assert result["contract"]["profile_id"] == "sports:nfl"
        assert result["dataset_registry"]["dataset_id"] == result["contract"]["dataset_id"]
        assert result["dataset_version"]["version_id"]
        assert result["validation_result"]["validation_id"]
        assert result["normalization_request"]["status"] == "normalization_ready"
        assert result["certification_request"]["status"] == "certification_ready"
        assert result["readiness_snapshot"]["ok"]
        assert result["readiness_snapshot"]["status"] == "ready"
        assert result["readiness_snapshot"]["raw_acquisition_cache"]["status"] == "ready"
        assert result["readiness_snapshot"]["raw_acquisition_cache"]["raw_record_count"] == result["raw_record_count"]

        raw_rows = runtime.platform.store.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[result["contract"]["dataset_id"]],
            order_by="row_index ASC",
        )
        assert len(raw_rows) == result["raw_record_count"]
        validation_rows = runtime.platform.store.fetch(
            "validation_results",
            where="dataset_id = ?",
            params=[result["contract"]["dataset_id"]],
            order_by="created_at ASC",
        )
        assert validation_rows

        dashboard_snapshot = runtime.dashboard_snapshot(
            profile_id="sports:nfl",
            dataset_id=result["contract"]["dataset_id"],
            source_bundle=fixture,
        )
        assert dashboard_snapshot["ok"]
        assert dashboard_snapshot["dataset_readiness"]["status"] == "ready"
        assert dashboard_snapshot["dataset_readiness"]["raw_acquisition_cache"]["status"] == "ready"
        assert dashboard_snapshot["readiness_summary"]["raw_acquisition_cache_status"] == "ready"

        helper_snapshot = build_historical_dataset_acquisition_runtime_dashboard_snapshot(
            storage_path=storage_path,
            profile_id="sports:nfl",
            dataset_id=result["contract"]["dataset_id"],
            source_bundle=fixture,
        )
        assert helper_snapshot["ok"]

        helper_snapshot_for_dashboard = get_historical_dataset_acquisition_runtime_snapshot_for_dashboard(
            storage_path=storage_path,
            profile_id="sports:nfl",
            dataset_id=result["contract"]["dataset_id"],
            source_bundle=fixture,
        )
        assert helper_snapshot_for_dashboard["ok"]
    finally:
        runtime.close()
