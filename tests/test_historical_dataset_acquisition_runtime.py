from __future__ import annotations

import json
from pathlib import Path

from src.data.historical_dataset_acquisition_runtime import (
    HistoricalDatasetAcquisitionRuntime,
    _legacy_source_bundle_digest,
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
        assert result["dataset_registry"]["latest_version_number"] == 1
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


def test_historical_dataset_acquisition_runtime_reuses_identical_source_bundle(tmp_path: Path) -> None:
    storage_path = tmp_path / "historical_acquisition_runtime_reuse.sqlite"
    fixture = build_nfl_p0_fixture(2)

    runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path)
    try:
        first = runtime.stage_raw_acquisition_cache(fixture, profile_id="sports:nfl")
        second = runtime.stage_raw_acquisition_cache(fixture, profile_id="sports:nfl")
        changed = runtime.stage_raw_acquisition_cache(build_nfl_p0_fixture(3), profile_id="sports:nfl")

        assert first["status"] == "raw_cache_ready"
        assert second["status"] == "raw_cache_reused"
        assert second["replay_status"] == "IDEMPOTENT_REUSE"
        assert second["dataset_version"]["version_id"] == first["dataset_version"]["version_id"]
        assert changed["status"] == "raw_cache_ready"
        assert changed["replay_status"] == "NEW_PUBLICATION"
        assert changed["dataset_version"]["version_id"] != first["dataset_version"]["version_id"]
        assert changed["dataset_version"]["version_id"].endswith(".v002")

        raw_rows = runtime.platform.store.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[first["contract"]["dataset_id"]],
            order_by="row_index ASC",
        )
        version_rows = runtime.platform.store.fetch(
            "dataset_versions",
            where="dataset_id = ?",
            params=[first["contract"]["dataset_id"]],
            order_by="version_number ASC",
        )
        dataset_registry = runtime.platform.read_dataset(first["contract"]["dataset_id"]).get("registry") or {}

        assert len(raw_rows) == first["raw_record_count"] + changed["raw_record_count"]
        assert len(version_rows) == 2
        assert int(dataset_registry.get("latest_version_number") or 0) == 2
    finally:
        runtime.close()


def test_historical_dataset_acquisition_runtime_reuses_identical_content_with_different_bundle_identity(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "historical_acquisition_runtime_content_reuse.sqlite"
    fixture = build_nfl_p0_fixture(2)
    renamed_fixture = {
        **fixture,
        "source_bundle_id": "oddswarehouse.bundle.renamed",
        "acquisition_timestamp": "2026-08-08T12:05:00Z",
    }

    runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path)
    try:
        first = runtime.stage_raw_acquisition_cache(fixture, profile_id="sports:nfl")
        second = runtime.stage_raw_acquisition_cache(renamed_fixture, profile_id="sports:nfl")

        assert first["status"] == "raw_cache_ready"
        assert second["status"] == "raw_cache_reused"
        assert second["replay_status"] == "IDEMPOTENT_REUSE"
        assert second["reuse_match_type"] == "content_digest"
        assert second["dataset_version"]["version_id"] == first["dataset_version"]["version_id"]
    finally:
        runtime.close()


def test_historical_dataset_acquisition_runtime_reuses_legacy_fingerprint_contract(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "historical_acquisition_runtime_legacy_digest.sqlite"
    fixture = build_nfl_p0_fixture(2)

    runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path)
    try:
        first = runtime.stage_raw_acquisition_cache(fixture, profile_id="sports:nfl")
        version_rows = runtime.platform.store.fetch(
            "dataset_versions",
            where="dataset_id = ?",
            params=[first["contract"]["dataset_id"]],
            order_by="version_number ASC",
        )
        assert len(version_rows) == 1
        version_row = dict(version_rows[0])
        legacy_metadata = HistoricalDatasetAcquisitionRuntime._version_metadata_payload(version_row)
        legacy_metadata["source_bundle_digest"] = _legacy_source_bundle_digest(
            fixture,
            source_bundle_id=first["contract"]["source_bundle_id"],
        )
        version_row["metadata_json"] = json.dumps(legacy_metadata, sort_keys=True)
        runtime.platform.store.upsert("dataset_versions", version_row, key_columns=("version_id",))

        replayed = runtime.stage_raw_acquisition_cache(fixture, profile_id="sports:nfl")

        assert replayed["status"] == "raw_cache_reused"
        assert replayed["replay_status"] == "IDEMPOTENT_REUSE"
        assert replayed["dataset_version"]["version_id"] == first["dataset_version"]["version_id"]
    finally:
        runtime.close()
