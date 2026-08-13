from __future__ import annotations

import importlib
from pathlib import Path

from src.data.data_identity_lakehouse import DataIdentityLakehouseRuntime
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.market_intelligence.data_identity_lakehouse_foundation import (
    build_data_identity_foundation_snapshot,
)
from src.services.streamlit_dashboard_data import (
    get_data_identity_foundation_snapshot_for_dashboard as get_data_identity_foundation_snapshot_for_dashboard_service,
)
from src.storage.local_store import create_local_storage_engine
from tests.test_pipeline_validation import _build_phase55_chain


def _build_seed_fixture_rows(count: int = 8) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    events: list[dict[str, object]] = []
    markets: list[dict[str, object]] = []
    selections: list[dict[str, object]] = []
    for index in range(count):
        event_id = f"event::{index}"
        market_id = f"market::{index}"
        selection_id = f"selection::{index}"
        day = (index % 28) + 1
        event_date = f"2026-09-{day:02d}"
        events.append(
            {
                "event_id": event_id,
                "event_key": f"Away {index} at Home {index}",
                "event_date": event_date,
                "event_start_time": f"{event_date}T20:20:00Z",
                "home_team_id": f"HOME::{index}",
                "home_team": f"Home {index}",
                "away_team_id": f"AWAY::{index}",
                "away_team": f"Away {index}",
                "provider": "oddswarehouse",
                "dataset_id": "dataset.sports.nfl.oddswarehouse.nfl_basic.historical",
                "dataset_name": "oddswarehouse_nfl_basic",
                "sport": "football",
                "league": "NFL",
                "source_event_id": f"ow-event-{index}",
                "batch_id": "batch::seed",
                "created_at": f"{event_date}T00:00:00Z",
            }
        )
        markets.append(
            {
                "market_id": market_id,
                "event_id": event_id,
                "book": "Circa",
                "market_family": "spread",
                "market_type": "spread",
                "market_name": "spread",
                "market_label": "spread",
                "line_value": 3.5,
                "provider": "oddswarehouse",
                "dataset_id": "dataset.sports.nfl.oddswarehouse.nfl_basic.historical",
                "dataset_name": "oddswarehouse_nfl_basic",
                "source_market_id": f"ow-market-{index}",
                "batch_id": "batch::seed",
                "created_at": f"{event_date}T00:00:00Z",
            }
        )
        selections.append(
            {
                "selection_id": selection_id,
                "market_id": market_id,
                "event_id": event_id,
                "book": "Circa",
                "selection": "away",
                "market_type": "spread",
                "line_value": 3.5,
                "provider": "oddswarehouse",
                "dataset_id": "dataset.sports.nfl.oddswarehouse.nfl_basic.historical",
                "dataset_name": "oddswarehouse_nfl_basic",
                "source_selection_id": f"ow-selection-{index}",
                "batch_id": "batch::seed",
                "created_at": f"{event_date}T00:00:00Z",
            }
        )
    return events, markets, selections


def test_data_identity_foundation_completes_and_persists_lakehouse_readiness(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "data_identity_foundation.sqlite"
    artifact_root = tmp_path / "data_identity_foundation_artifacts"
    lakehouse_root = tmp_path / "lakehouse"
    _build_phase55_chain(storage_path)

    snapshot = build_data_identity_foundation_snapshot(
        storage_path=storage_path,
        artifact_root=artifact_root,
        lakehouse_root=lakehouse_root,
    )

    assert snapshot["ok"] is True
    assert snapshot["status"] == "completed"
    assert snapshot["readiness"] == "first_controlled_nfl_vendor_ingest_ready"
    assert snapshot["lifecycle_state"] == "data_identity_lakehouse_foundation_complete"
    assert snapshot["validation_state"] == "validated"
    assert snapshot["reference_profile_id"] == "sports:nfl"
    assert snapshot["next_governed_phase"] == "First Controlled NFL Vendor Ingest"
    assert snapshot["nfl_parity_status"]["ok"] is True
    assert snapshot["first_vendor_ingest_readiness"]["status"] == "ready"
    assert snapshot["artifact_integrity_ok"] is True
    assert snapshot["parquet_readiness"]["partition_count"] > 0
    assert snapshot["parquet_readiness"]["roundtrip_ok"] is True
    assert snapshot["bronze_silver_gold_readiness"]["status"] == "ready"
    assert snapshot["identity_resolution_readiness"]["approved_mapping_count"] > 0
    assert snapshot["reconciliation_readiness"]["reconciliation_result_count"] > 0
    assert snapshot["validation_summary"]["error_check_count"] >= 12
    assert (
        snapshot["validation_summary"]["error_checks_passed"]
        == snapshot["validation_summary"]["error_check_count"]
    )

    results = {
        row["requirement_id"]: row
        for row in snapshot["capability_audit_matrix"]
    }
    expected_requirements = {
        "canonical_identity_foundation",
        "matching",
        "reconciliation",
        "point_in_time_and_revision_contract",
        "quality_quarantine_review",
        "bronze_silver_gold_mapping",
        "parquet_analytical_storage",
        "delta_compatible_interfaces",
        "security_and_governance",
        "readiness_surfaces",
    }
    assert expected_requirements == set(results)
    assert all(
        row["final_classification"] == "complete_and_validated"
        for row in results.values()
    )

    artifact_refs = snapshot["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()

    storage = create_local_storage_engine(storage_path)
    try:
        assert storage.count("data_identity_foundation_runs") >= 1
        assert storage.count("data_identity_foundation_audit_items") >= len(expected_requirements)
        assert storage.count("identity_mappings") > 0
        assert storage.count("identity_reconciliation_results") > 0
        assert storage.count("lakehouse_partitions") > 0
    finally:
        storage.close()


def test_data_identity_runtime_preserves_revisions_and_blocks_ambiguous_matches(
    tmp_path: Path,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        first = runtime.register_identity_mapping(
            provider="seed_vendor",
            external_identifier="ACME",
            internal_identifier="company::acme",
            entity_type="company",
            entity_name="ACME Holdings",
            approval_evidence={"seed": True},
        )
        repeated = runtime.register_identity_mapping(
            provider="seed_vendor",
            external_identifier="ACME",
            internal_identifier="company::acme",
            entity_type="company",
            entity_name="ACME Holdings",
            approval_evidence={"seed": True},
        )
        changed = runtime.register_identity_mapping(
            provider="seed_vendor",
            external_identifier="ACME",
            internal_identifier="company::acme.v2",
            entity_type="company",
            entity_name="ACME Holdings Renamed",
            approval_evidence={"seed": True, "revision": 2},
        )

        assert repeated["mapping_id"] == first["mapping_id"]
        assert changed["mapping_id"] != first["mapping_id"]
        latest_rows = runtime.store.fetch(
            "identity_mappings",
            where="provider = ? AND entity_type = ? AND external_identifier = ?",
            params=["seed_vendor", "company", "ACME"],
            order_by="revision_number ASC",
        )
        assert len(latest_rows) == 2
        assert latest_rows[0]["mapping_status"] == "superseded"
        assert int(latest_rows[0]["is_latest"] or 0) == 0
        assert latest_rows[1]["mapping_status"] == "accepted"
        assert int(latest_rows[1]["is_latest"] or 0) == 1

        resolution = runtime.resolve_identity_mapping(
            entity_type="team",
            provider="seed_vendor",
            external_identifier="Springfield Isotopes",
            source_row={"entity_name": "Springfield Isotopes"},
            candidate_rows=[
                {"internal_identifier": "team::home", "entity_name": "Springfield Isotopes A"},
                {"internal_identifier": "team::away", "entity_name": "Springfield Isotopes B"},
            ],
            normalized_fields=("entity_name",),
        )

        assert resolution["accepted"] is False
        assert resolution["decision_status"] == "manual_review"
        assert resolution["match_method"] == "manual_review"
        assert runtime.store.count("manual_review_queue") >= 1
        assert runtime.store.count("quarantine_records") >= 1
    finally:
        runtime.close()


def test_data_identity_runtime_ignores_fallback_processing_timestamps_for_same_mapping(
    tmp_path: Path,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_timestamps.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        first = runtime.register_identity_mapping(
            provider="repository",
            external_identifier="OddsWarehouse",
            internal_identifier="oddswarehouse",
            entity_type="provider",
            entity_name="OddsWarehouse",
            source_payload={
                "provider_id": "oddswarehouse",
                "created_at": "2026-08-06T12:00:00Z",
            },
            approval_reference="dataset.sports.nfl.oddswarehouse.raw_acquisition_cache.v001",
        )
        repeated = runtime.register_identity_mapping(
            provider="repository",
            external_identifier="OddsWarehouse",
            internal_identifier="oddswarehouse",
            entity_type="provider",
            entity_name="OddsWarehouse",
            source_payload={
                "provider_id": "oddswarehouse",
                "created_at": "2026-08-06T12:05:00Z",
            },
            approval_reference="dataset.sports.nfl.oddswarehouse.raw_acquisition_cache.v002",
        )

        rows = runtime.store.fetch(
            "identity_mappings",
            where="provider = ? AND entity_type = ? AND external_identifier = ?",
            params=["repository", "provider", "OddsWarehouse"],
            order_by="revision_number ASC",
        )

        assert repeated["mapping_id"] == first["mapping_id"]
        assert len(rows) == 1
        assert rows[0]["mapping_status"] == "accepted"
        assert int(rows[0]["is_latest"] or 0) == 1
    finally:
        runtime.close()


def test_data_identity_runtime_reuses_matching_historical_revision_without_reordering_latest(
    tmp_path: Path,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_historical_revisions.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        older = runtime.register_identity_mapping(
            provider="oddswarehouse",
            external_identifier="Washington",
            internal_identifier="WAS",
            entity_type="team",
            entity_name="Washington Redskins",
            canonical_key="nfl.franchise.washington",
            valid_from="1937-01-01",
            source_payload={"valid_from": "1937-01-01"},
            approval_reference="oddswarehouse.batch.001",
        )
        newer = runtime.register_identity_mapping(
            provider="oddswarehouse",
            external_identifier="Washington",
            internal_identifier="WAS",
            entity_type="team",
            entity_name="Washington Redskins",
            canonical_key="nfl.franchise.washington",
            valid_from="2020-07-13",
            source_payload={"valid_from": "2020-07-13"},
            approval_reference="oddswarehouse.batch.002",
        )
        replayed_older = runtime.register_identity_mapping(
            provider="oddswarehouse",
            external_identifier="Washington",
            internal_identifier="WAS",
            entity_type="team",
            entity_name="Washington Redskins",
            canonical_key="nfl.franchise.washington",
            valid_from="1937-01-01",
            source_payload={"valid_from": "1937-01-01", "created_at": "2026-08-08T12:10:00Z"},
            approval_reference="oddswarehouse.batch.003",
        )

        rows = runtime.store.fetch(
            "identity_mappings",
            where="provider = ? AND entity_type = ? AND external_identifier = ?",
            params=["oddswarehouse", "team", "Washington"],
            order_by="revision_number ASC",
        )

        assert older["mapping_id"] == replayed_older["mapping_id"]
        assert len(rows) == 2
        assert int(rows[0]["is_latest"] or 0) == 0
        assert int(rows[1]["is_latest"] or 0) == 1
        assert rows[1]["mapping_id"] == newer["mapping_id"]
    finally:
        runtime.close()


def test_data_identity_runtime_scopes_reconciliation_to_supplied_selection_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_reconciliation_scope.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        runtime.store.ensure_schema()
        selection_row = {
            "selection_id": "selection::scoped",
            "market_id": "market::scoped",
            "event_id": "event::scoped",
            "provider": "oddswarehouse",
            "book": "Circa",
            "selection": "away",
            "market_type": "spread",
            "line_value": 3.5,
            "odds": -108,
            "source_selection_id": "selection::scoped",
            "dataset_id": "dataset.sports.nfl.oddswarehouse.nfl_basic.historical",
            "dataset_name": "oddswarehouse_nfl_basic",
            "created_at": "2026-08-10T00:01:00Z",
        }
        original_fetch = runtime._fetch

        def _guarded_fetch(table_name: str, **kwargs):
            if table_name == "historical_selections":
                raise AssertionError("scoped reconciliation should not refetch all historical selections")
            return original_fetch(table_name, **kwargs)

        monkeypatch.setattr(runtime, "_fetch", _guarded_fetch)

        result = runtime.reconcile_certified_outputs(selection_rows=[selection_row])

        assert result["ok"] is True
        assert result["reconciliation_result_count"] == 1
        assert runtime.store.count("identity_reconciliation_results") == 1
    finally:
        runtime.close()


def test_data_identity_runtime_batches_seed_identity_mapping_fetches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_seed_batch.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        events, markets, selections = _build_seed_fixture_rows(40)
        seeded = runtime.seed_from_certified_outputs(
            events=events,
            markets=markets,
            selections=selections,
        )
        initial_count = runtime.store.count("identity_mappings")
        fetch_calls = 0
        original_fetch = runtime.store.fetch

        def _recording_fetch(table_name: str, **kwargs):
            nonlocal fetch_calls
            if table_name == "identity_mappings":
                fetch_calls += 1
            return original_fetch(table_name, **kwargs)

        monkeypatch.setattr(runtime.store, "fetch", _recording_fetch)

        replay = runtime.seed_from_certified_outputs(
            events=events,
            markets=markets,
            selections=selections,
        )

        assert seeded["ok"] is True
        assert replay["ok"] is True
        assert runtime.store.count("identity_mappings") == initial_count
        assert replay["identity_mapping_count"] == initial_count
        assert fetch_calls < 12
    finally:
        runtime.close()


def test_data_identity_runtime_batches_explicit_identity_mapping_registrations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_explicit_batch.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        requests = [
            {
                "provider": "oddswarehouse",
                "external_identifier": f"TEAM-{index:03d}",
                "internal_identifier": f"nfl.team.{index:03d}",
                "entity_type": "team",
                "entity_name": f"Team {index:03d}",
                "canonical_key": f"franchise.{index:03d}",
                "approval_reference": "test_batch",
                "approval_evidence": {"row": index},
                "source_payload": {"row": index},
            }
            for index in range(40)
        ]
        seeded = runtime.register_identity_mappings_batch(requests)
        initial_count = runtime.store.count("identity_mappings")
        fetch_calls = 0
        original_fetch = runtime.store.fetch

        def _recording_fetch(table_name: str, **kwargs):
            nonlocal fetch_calls
            if table_name == "identity_mappings":
                fetch_calls += 1
            return original_fetch(table_name, **kwargs)

        monkeypatch.setattr(runtime.store, "fetch", _recording_fetch)

        replay = runtime.register_identity_mappings_batch(requests)

        assert len(seeded) == 40
        assert len(replay) == 40
        assert runtime.store.count("identity_mappings") == initial_count
        assert fetch_calls <= 2
    finally:
        runtime.close()


def test_data_identity_runtime_batches_reconciliation_fetches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_reconciliation_batch.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        _, _, selections = _build_seed_fixture_rows(40)
        seeded = runtime.reconcile_certified_outputs(selection_rows=selections)
        initial_count = runtime.store.count("identity_reconciliation_results")
        fetch_calls = 0
        original_fetch = runtime.store.fetch

        def _recording_fetch(table_name: str, **kwargs):
            nonlocal fetch_calls
            if table_name == "identity_reconciliation_results":
                fetch_calls += 1
            return original_fetch(table_name, **kwargs)

        monkeypatch.setattr(runtime.store, "fetch", _recording_fetch)

        replay = runtime.reconcile_certified_outputs(selection_rows=selections)

        assert seeded["ok"] is True
        assert replay["ok"] is True
        assert runtime.store.count("identity_reconciliation_results") == initial_count
        assert replay["reconciliation_result_count"] == len(selections)
        assert fetch_calls <= 2
    finally:
        runtime.close()


def test_data_identity_runtime_scopes_lakehouse_fetches_to_affected_partitions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=tmp_path / "identity_runtime_lakehouse_scope.sqlite",
        lakehouse_root=tmp_path / "lakehouse",
    )
    try:
        runtime.store.ensure_schema()
        common = {
            "market_profile": "sports:nfl",
            "provider": "oddswarehouse",
            "asset_class": "historical",
            "dataset_id": "dataset.sports.nfl.oddswarehouse.nfl_basic.historical",
            "dataset_name": "oddswarehouse_nfl_basic",
            "sport": "football",
            "league": "NFL",
        }
        runtime.store.upsert(
            "historical_events",
            {
                **common,
                "event_id": "event::2009",
                "event_start_time": "2009-09-10T20:20:00Z",
                "event_date": "2009-09-10",
                "season": "2009",
                "batch_id": "batch::2009",
                "home_team_id": "PIT",
                "away_team_id": "TEN",
                "source_event_id": "ow::2009",
            },
            key_columns=("event_id",),
        )
        runtime.store.upsert(
            "historical_events",
            {
                **common,
                "event_id": "event::2010",
                "event_start_time": "2010-09-09T20:20:00Z",
                "event_date": "2010-09-09",
                "season": "2010",
                "batch_id": "batch::2010",
                "home_team_id": "NO",
                "away_team_id": "MIN",
                "source_event_id": "ow::2010",
            },
            key_columns=("event_id",),
        )

        fetch_calls: list[tuple[str, str | None]] = []
        original_fetch = runtime.store.fetch

        def _recording_fetch(table_name: str, **kwargs):
            fetch_calls.append((table_name, kwargs.get("where")))
            return original_fetch(table_name, **kwargs)

        monkeypatch.setattr(runtime.store, "fetch", _recording_fetch)

        publication_scope = {
            "historical_events": {
                "layer_name": "silver",
                "row_count": 1,
                "affected_partition_values": [
                    {
                        "market_family": "historical",
                        "sport_or_profile": "sports:nfl",
                        "dataset": "dataset.sports.nfl.oddswarehouse.nfl_basic.historical",
                        "provider": "oddswarehouse",
                        "season": "2009",
                        "publication_batch": "batch::2009",
                    }
                ],
            }
        }

        result = runtime.publish_lakehouse_views(publication_scope=publication_scope)

        event_fetches = [where for table_name, where in fetch_calls if table_name == "historical_events"]
        assert result["ok"] is True
        assert result["partition_count"] == 1
        assert event_fetches
        assert event_fetches[-1]
        assert "season" in event_fetches[-1]
    finally:
        runtime.close()


def test_data_identity_foundation_updates_p0_and_service_exports(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "data_identity_foundation_p0.sqlite"
    _build_phase55_chain(storage_path)

    snapshot = build_data_identity_foundation_snapshot(storage_path=storage_path)
    p0_snapshot = build_nfl_p0_dashboard_snapshot(storage_path)
    service_snapshot = get_data_identity_foundation_snapshot_for_dashboard_service(
        storage_path=storage_path
    )

    assert p0_snapshot["nfl_production_completion_layer_readiness"]["status"] == "completed"
    assert p0_snapshot["data_identity_foundation_layer_readiness"]["status"] == "completed"
    assert (
        p0_snapshot["data_identity_foundation_layer_readiness"]["next_governed_phase"]
        == "First Controlled NFL Vendor Ingest"
    )
    assert p0_snapshot["readiness_summary"]["data_identity_foundation_status"] == "completed"
    assert (
        service_snapshot["data_identity_foundation_run_id"]
        == snapshot["data_identity_foundation_run_id"]
    )

    module = importlib.import_module("src.market_intelligence")
    assert callable(module.build_data_identity_foundation_snapshot)
    assert callable(module.get_data_identity_foundation_snapshot_for_dashboard)
    assert callable(get_data_identity_foundation_snapshot_for_dashboard_service)
