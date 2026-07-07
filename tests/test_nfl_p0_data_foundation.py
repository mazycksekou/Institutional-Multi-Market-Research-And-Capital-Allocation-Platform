from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.data.nfl_p0_foundation import (
    NFL_P0_TABLE_CONTRACTS,
    build_nfl_p0_dashboard_snapshot,
    build_nfl_p0_fixture,
    bootstrap_nfl_p0_foundation,
    create_nfl_p0_storage_engine,
    normalize_nfl_p0_rows,
    validate_nfl_p0_rows,
)
from src.data.validation import validate_dataset_rows


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_nfl_p0_storage_tables_exist_and_bootstrap(tmp_path: Path) -> None:
    storage_path = tmp_path / "nfl_p0.sqlite"
    engine = create_nfl_p0_storage_engine(storage_path)
    try:
        for table_name in NFL_P0_TABLE_CONTRACTS:
            assert engine.table_exists(table_name) is True
    finally:
        engine.close()

    fixture = build_nfl_p0_fixture(4)
    result = bootstrap_nfl_p0_foundation(storage_path, fixture=fixture)

    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["dataset_version"] == fixture["dataset_version"]
    assert result["summary"]["ready_table_count"] == len(NFL_P0_TABLE_CONTRACTS)
    assert result["summary"]["table_count"] == len(NFL_P0_TABLE_CONTRACTS)
    assert set(result["ready_tables"]) == set(NFL_P0_TABLE_CONTRACTS)

    snapshot = build_nfl_p0_dashboard_snapshot(storage_path)
    assert snapshot["ok"] is True
    assert snapshot["status"] == "ready"
    assert snapshot["dataset_readiness"]["ready_table_count"] == len(NFL_P0_TABLE_CONTRACTS)
    assert snapshot["table_counts"]["nfl_odds_snapshots"] >= 1
    assert snapshot["table_counts"]["nfl_team_stats_snapshots"] >= 1


def test_nfl_p0_validation_rejects_pregame_leakage() -> None:
    fixture = build_nfl_p0_fixture(1)
    rows = normalize_nfl_p0_rows(
        "nfl_odds_snapshots",
        fixture["tables"]["nfl_odds_snapshots"],
        dataset_version=fixture["dataset_version"],
        created_at=fixture["created_at"],
        updated_at=fixture["created_at"],
    )
    row = dict(rows[0])
    kickoff = _parse_iso(str(row["kickoff_time"]))
    row["snapshot_time"] = (kickoff + timedelta(hours=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    validation = validate_nfl_p0_rows("nfl_odds_snapshots", [row])

    assert validation["ok"] is False
    assert any(error.startswith("point_in_time:snapshot_time_after_kickoff") for error in validation["errors"])


def test_validate_dataset_rows_accepts_zero_valued_required_fields() -> None:
    validation = validate_dataset_rows(
        [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "source_name": "fixture",
                "indoor_flag": 0,
            }
        ],
        required_fields=("timestamp", "source_name", "indoor_flag"),
    )

    assert validation["ok"] is True
