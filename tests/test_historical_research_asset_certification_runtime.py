from __future__ import annotations

from pathlib import Path

from src.data.historical_research_asset_certification_runtime import (
    HistoricalResearchAssetCertificationRuntime,
    build_historical_research_asset_certification_runtime_dashboard_snapshot,
    get_historical_research_asset_certification_snapshot_for_dashboard,
)
from src.data.historical_research_database import build_historical_research_fixture


def test_historical_research_asset_certification_runtime_certifies_required_assets(tmp_path: Path) -> None:
    storage_path = tmp_path / "historical_research_asset_certification.sqlite"
    fixture = build_historical_research_fixture(game_count=2, profile_id="sports:nfl")

    runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path)
    try:
        result = runtime.certify(fixture=fixture, profile_id="sports:nfl")

        assert result["ok"]
        assert result["status"] == "certified"
        assert result["dataset_certification"]["certification_status"] == "certified"
        assert len(result["research_asset_certifications"]) == len(result["required_asset_catalog"])
        assert result["summary"]["dataset_status"] == "certified"
        assert result["summary"]["certified_asset_count"] == len(result["required_asset_catalog"])

        asset_rows = runtime.store.fetch(
            "historical_research_asset_certifications",
            where="market_profile = ?",
            params=["sports:nfl"],
            order_by="certification_id ASC",
        )
        assert len(asset_rows) == len(result["required_asset_catalog"])
        assert {row["certification_status"] for row in asset_rows} == {"certified"}

        dataset_rows = runtime.store.fetch(
            "historical_certifications",
            where="market_profile = ?",
            params=["sports:nfl"],
            order_by="certification_id ASC",
        )
        assert len(dataset_rows) == 1
        assert dataset_rows[0]["certification_status"] == "certified"

        readiness_snapshot = runtime.build_readiness_snapshot(profile_id="sports:nfl")
        assert readiness_snapshot["ok"]
        assert readiness_snapshot["status"] == "ready"
        assert readiness_snapshot["asset_summary"]["dataset_certified"]
        assert readiness_snapshot["missing_research_assets"] == []
        assert readiness_snapshot["failed_research_assets"] == []

        dashboard_snapshot = runtime.dashboard_snapshot(profile_id="sports:nfl", fixture=fixture)
        assert dashboard_snapshot["dataset_readiness"]["status"] == "ready"
        assert dashboard_snapshot["research_asset_readiness"]["status"] == "certified"
        assert dashboard_snapshot["research_asset_readiness"]["certified_asset_count"] == len(result["required_asset_catalog"])

        helper_snapshot = build_historical_research_asset_certification_runtime_dashboard_snapshot(
            storage_path=storage_path,
            profile_id="sports:nfl",
            fixture=fixture,
        )
        assert helper_snapshot["ok"]

        helper_snapshot_for_dashboard = get_historical_research_asset_certification_snapshot_for_dashboard(
            storage_path=storage_path,
            profile_id="sports:nfl",
            fixture=fixture,
        )
        assert helper_snapshot_for_dashboard["ok"]
    finally:
        runtime.close()
