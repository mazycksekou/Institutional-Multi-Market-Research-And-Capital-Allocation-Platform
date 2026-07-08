from __future__ import annotations

from pathlib import Path

from src.data import get_historical_research_market_profile, validate_historical_research_profile
from src.data.historical_research_database import (
    HISTORICAL_STAGE_CONTRACTS,
    HistoricalResearchDatabase,
    build_historical_research_fixture,
)
from src.services.streamlit_dashboard_data import get_historical_research_snapshot_for_dashboard
from src.storage.local_store import LocalStorageEngine


def test_historical_research_database_bootstrap_uses_shared_storage_and_profile(tmp_path: Path) -> None:
    storage_path = tmp_path / "historical_research.sqlite"
    fixture = build_historical_research_fixture(game_count=2, profile_id="sports:nfl")
    profile = get_historical_research_market_profile("sports:nfl")
    profile_validation = validate_historical_research_profile(profile)

    assert profile_validation["ok"]

    database = HistoricalResearchDatabase(storage_path)
    try:
        bootstrap = database.bootstrap(profile_id="sports:nfl", fixture=fixture)

        assert isinstance(database.store, LocalStorageEngine)
        assert bootstrap["ok"]
        assert bootstrap["status"] == "ready"
        assert bootstrap["market_profile"]["ok"]
        assert bootstrap["bootstrap"]["raw_acquisition_result"]["ok"]
        assert bootstrap["bootstrap"]["raw_acquisition_result"]["status"] == "raw_cache_ready"
        assert bootstrap["bootstrap"]["raw_acquisition_result"]["raw_record_count"] > 0
        assert bootstrap["dataset_name"] == "historical_research_database"
        assert bootstrap["ready_tables"]
        assert set(bootstrap["ready_tables"]) == set(HISTORICAL_STAGE_CONTRACTS)
        assert bootstrap["raw_acquisition_cache"]["status"] == "ready"
        assert bootstrap["summary"]["raw_acquisition_cache_ready"]
        assert bootstrap["summary"]["raw_acquisition_cache_status"] == "ready"

        for stage_name, contract in HISTORICAL_STAGE_CONTRACTS.items():
            assert database.store.table_exists(contract.table_name)
            rows = database.list_rows(stage_name)
            assert rows, f"expected rows for {stage_name}"
            assert bootstrap["table_readiness"][contract.table_name]["status"] == "ready"
            assert bootstrap["table_readiness"][contract.table_name]["validation"]["ok"]
    finally:
        database.close()


def test_historical_research_dashboard_snapshot_is_shared_and_readable(tmp_path: Path) -> None:
    storage_path = tmp_path / "historical_research.sqlite"
    fixture = build_historical_research_fixture(game_count=2, profile_id="sports:nfl")

    database = HistoricalResearchDatabase(storage_path)
    try:
        database.bootstrap(profile_id="sports:nfl", fixture=fixture)
    finally:
        database.close()

    snapshot = get_historical_research_snapshot_for_dashboard(storage_path=storage_path, profile_id="sports:nfl")

    assert snapshot["ok"]
    assert snapshot["status"] == "ready"
    assert snapshot["market_profile"]["ok"]
    assert snapshot["dataset_readiness"]["status"] == "ready"
    assert snapshot["dataset_readiness"]["ready_table_count"] == len(HISTORICAL_STAGE_CONTRACTS)
    assert snapshot["ready_tables"]
    assert not snapshot["missing_tables"]
    assert not snapshot["blocked_tables"]
    assert snapshot["table_readiness"]["historical_events"]["status"] == "ready"
