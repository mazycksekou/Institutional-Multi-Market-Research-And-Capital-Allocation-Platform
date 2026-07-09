from __future__ import annotations

from pathlib import Path

from src.data.research_asset_lifecycle_runtime import (
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
    build_research_asset_lifecycle_row,
    build_research_asset_lifecycle_runtime_dashboard_snapshot,
    build_time_entity_alignment_certification,
    build_time_entity_alignment_certification_row,
    get_research_asset_lifecycle_snapshot_for_dashboard,
    validate_research_asset_identity_contract,
    validate_research_asset_lifecycle_row,
    validate_time_entity_alignment_certification_row,
)
from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE


def _aligned_row() -> dict[str, str]:
    return {
        "asset_id": "dataset.nfl.games",
        "research_asset_id": "dataset.nfl.games",
        "research_asset_name": "NFL Games",
        "asset_family": "dataset",
        "asset_type": "dataset",
        "asset_name": "NFL Games",
        "market_profile": "sports:nfl",
        "market": "historical",
        "market_type": "historical_research",
        "league": "NFL",
        "sport": "football",
        "season": "2026",
        "week_or_date": "2026-W01",
        "event_id": "nfl.2026.week01.buf.ne",
        "game_id": "nfl.2026.week01.buf.ne",
        "market_id": "market.nfl.week01.spread",
        "selection": "Bills -3.5",
        "participant_id": "",
        "team_id": "BUF",
        "provider_timestamp": "2026-07-01T12:00:00Z",
        "snapshot_time": "2026-07-01T12:00:00Z",
        "decision_time": "2026-07-01T13:00:00Z",
        "result_timestamp": "2026-07-02T00:00:00Z",
        "alignment_status": "aligned",
        "alignment_reason": "time_and_entity_alignment_checked",
        "failure_reason": "",
        "alignment_score": "1.0",
        "row_count": "1",
        "source_row_count": "1",
        "source_name": "fixture_source",
        "source_type": "fixture",
        "source_key": "fixture_source",
        "provider": "repository",
        "connector": "fixture",
        "schema_version": "src.data.research_asset_lifecycle_runtime.v1",
        "lineage_version": "v1",
        "certification_timestamp": "2026-07-01T13:05:00Z",
    }


def test_research_asset_lifecycle_runtime_certifies_alignment_and_lifecycle_rows(tmp_path: Path) -> None:
    storage_path = tmp_path / "research_asset_lifecycle.sqlite"
    identity = build_research_asset_identity_contract(
        asset_id="dataset.nfl.games",
        asset_family="dataset",
        market_profile="sports:nfl",
        market="historical",
        league="NFL",
        sport="football",
        season="2026",
        week_or_date="2026-W01",
        event_id="nfl.2026.week01.buf.ne",
        game_id="nfl.2026.week01.buf.ne",
        market_id="market.nfl.week01.spread",
        selection="Bills -3.5",
        provider="repository",
        connector="fixture",
        schema_version="src.data.research_asset_lifecycle_runtime.v1",
        lineage_version="v1",
        asset_name="NFL Games",
        asset_type="dataset",
        participant_id="",
        team_id="BUF",
        market_type="historical_research",
    )

    identity_validation = validate_research_asset_identity_contract(identity)
    assert identity_validation["ok"]

    input_row = _aligned_row()
    alignment = build_time_entity_alignment_certification(
        identity=identity,
        rows=[input_row],
        source_bundle={
            "source_name": "fixture_source",
            "source_type": "fixture",
            "source_key": "fixture_source",
            "source_file": "fixture_source.csv",
            "source_event_id": "nfl.2026.week01.buf.ne",
            "source_market_id": "market.nfl.week01.spread",
            "source_selection_id": "Bills -3.5",
            "provider": "repository",
            "profile_family": "sports",
        },
        raw_acquisition_result={
            "rows": [input_row],
            "source_file": "fixture_source.csv",
            "source_event_id": "nfl.2026.week01.buf.ne",
            "source_market_id": "market.nfl.week01.spread",
            "source_selection_id": "Bills -3.5",
            "profile_family": "sports",
        },
        created_at="2026-07-01T13:05:00Z",
    )
    assert alignment.alignment_status == "aligned"
    assert alignment.failure_reason == ""

    alignment_row = build_time_entity_alignment_certification_row(
        identity=identity,
        alignment=alignment,
        profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
        source_bundle={
            "source_name": "fixture_source",
            "source_type": "fixture",
            "source_key": "fixture_source",
            "source_file": "fixture_source.csv",
            "source_event_id": "nfl.2026.week01.buf.ne",
            "source_market_id": "market.nfl.week01.spread",
            "source_selection_id": "Bills -3.5",
            "provider": "repository",
            "profile_family": "sports",
        },
        raw_acquisition_result={
            "rows": [input_row],
            "source_file": "fixture_source.csv",
            "source_event_id": "nfl.2026.week01.buf.ne",
            "source_market_id": "market.nfl.week01.spread",
            "source_selection_id": "Bills -3.5",
            "profile_family": "sports",
        },
        batch_id="lifecycle.batch.001",
    )
    assert validate_time_entity_alignment_certification_row(alignment_row)["ok"]

    runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path)
    try:
        lifecycle_result = runtime.certify_time_entity_alignment(
            identity=identity,
            rows=[input_row],
            source_bundle={
                "source_name": "fixture_source",
                "source_type": "fixture",
                "source_key": "fixture_source",
                "source_file": "fixture_source.csv",
                "source_event_id": "nfl.2026.week01.buf.ne",
                "source_market_id": "market.nfl.week01.spread",
                "source_selection_id": "Bills -3.5",
                "provider": "repository",
                "profile_family": "sports",
            },
            raw_acquisition_result={
                "rows": [input_row],
                "source_file": "fixture_source.csv",
                "source_event_id": "nfl.2026.week01.buf.ne",
                "source_market_id": "market.nfl.week01.spread",
                "source_selection_id": "Bills -3.5",
                "profile_family": "sports",
            },
            created_at="2026-07-01T13:05:00Z",
        )
        assert lifecycle_result["ok"]
        assert lifecycle_result["status"] == "aligned"
        assert lifecycle_result["alignment_certification"]["alignment_status"] == "aligned"
        assert lifecycle_result["research_asset_lifecycle"]["lifecycle_state"] == "integrity_verified"
        assert lifecycle_result["alignment_certification_row"]["alignment_status"] == "aligned"

        lifecycle_row = runtime.store.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[identity.asset_id],
            limit=1,
        )
        assert lifecycle_row and lifecycle_row[0]["lifecycle_state"] == "integrity_verified"

        alignment_rows = runtime.store.fetch(
            "research_asset_alignment_certifications",
            where="alignment_certification_id = ?",
            params=[lifecycle_result["alignment_certification"]["alignment_certification_id"]],
            limit=1,
        )
        assert alignment_rows and alignment_rows[0]["alignment_status"] == "aligned"

        lifecycle_update = runtime.record_lifecycle_state(
            identity={**identity.as_dict(), "metadata": {"note": "metadata can change without changing the core identity"}},
            lifecycle_state="research_asset_certified",
            lifecycle_reason="asset certified after alignment",
            alignment_certification=lifecycle_result["alignment_certification"],
            certification_result={"certification_status": "certified", "certification_state": "certified"},
            source_bundle={
                "source_name": "fixture_source",
                "source_type": "fixture",
                "source_key": "fixture_source",
                "source_file": "fixture_source.csv",
                "source_event_id": "nfl.2026.week01.buf.ne",
                "source_market_id": "market.nfl.week01.spread",
                "source_selection_id": "Bills -3.5",
                "provider": "repository",
                "profile_family": "sports",
            },
            raw_acquisition_result={
                "rows": [input_row],
                "source_file": "fixture_source.csv",
                "source_event_id": "nfl.2026.week01.buf.ne",
                "source_market_id": "market.nfl.week01.spread",
                "source_selection_id": "Bills -3.5",
                "profile_family": "sports",
            },
            created_at="2026-07-01T13:06:00Z",
            notes={"checked": True},
        )
        assert lifecycle_update["ok"]
        assert lifecycle_update["research_asset_lifecycle"]["lifecycle_state"] == "research_asset_certified"

        lifecycle_row_validation = validate_research_asset_lifecycle_row(lifecycle_update["research_asset_lifecycle"])
        assert lifecycle_row_validation["ok"]

        dashboard_snapshot = runtime.dashboard_snapshot(profile_id="sports:nfl")
        assert dashboard_snapshot["status"] in {"ready", "partial"}
        assert dashboard_snapshot["lifecycle_readiness"]["status"] in {"ready", "partial"}
        assert "failures" in dashboard_snapshot["alignment_readiness"]

        helper_snapshot = build_research_asset_lifecycle_runtime_dashboard_snapshot(
            storage_path=storage_path,
            profile_id="sports:nfl",
        )
        assert helper_snapshot["status"] in {"ready", "partial"}

        helper_snapshot_for_dashboard = get_research_asset_lifecycle_snapshot_for_dashboard(
            storage_path=storage_path,
            profile_id="sports:nfl",
        )
        assert helper_snapshot_for_dashboard["status"] in {"ready", "partial"}
    finally:
        runtime.close()
