from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data.data_paths import get_runtime_data_path
from src.data.historical_dataset_acquisition_runtime import HistoricalDatasetAcquisitionRuntime
from src.data.historical_research_asset_certification_runtime import (
    DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
    HistoricalResearchAssetCertificationRuntime,
    ResearchAssetCertificationContract,
    build_historical_dataset_certification_row,
    build_nfl_research_asset_certification_contracts,
    build_nfl_schedule_research_asset_certification_contract,
)
from src.connectors.feeds.nfl_schedule import build_nfl_schedule_connector_bundle
from src.data.nfl_p0_foundation import (
    DEFAULT_NFL_P0_GAME_COUNT,
    NFL_P0_SCHEMA_VERSION,
    NFL_P0_DATASET_VERSION,
    NFL_P0_SOURCE_NAME,
    NFL_P0_SOURCE_TYPE,
    NFL_P0_TABLE_CONTRACTS,
    build_nfl_p0_fixture,
    create_nfl_p0_storage_engine,
    get_nfl_p0_market_profile,
    normalize_nfl_p0_rows,
    validate_nfl_p0_rows,
)
from src.data.research_asset_lifecycle_runtime import (
    RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
)


NFL_SCHEDULE_RESEARCH_ASSET_STORAGE_PATH = get_runtime_data_path(
    "nfl_schedule_research_asset",
    "canonical_data.sqlite",
)
NFL_SCHEDULE_RESEARCH_ASSET_DATASET_NAME = "nfl_schedule_research_asset"
NFL_SCHEDULE_RAW_ACQUISITION_DATASET_NAME = "nfl_schedule_raw_acquisition_cache"
NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER = "nflverse"
NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_SOURCE_ID = "nflverse_schedules_results"
NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_ROLE = "primary_acquisition"
NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE = NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER
NFL_SCHEDULE_PROVIDER_SOURCE_ID = NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_SOURCE_ID
NFL_SCHEDULE_PROVIDER_SOURCE_TYPE = "deterministic_fixture"
NFL_SCHEDULE_RESEARCH_ASSET_PROFILE_ID = "sports:nfl"
NFL_SCHEDULE_RESEARCH_ASSET_LIFECYCLE_VERSION = "v1"
NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID = "connector.feeds.nfl_schedule"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, tuple):
            return list(obj)
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _connector_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    execution_mode: str,
    table_name: str,
) -> dict[str, Any]:
    payload = dict(row)
    provider_id = _normalize_text(provider_capability.get("provider_id"), NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER)
    provider_name = _normalize_text(provider_capability.get("provider_name"), provider_id)
    provider_role = _normalize_text(provider_capability.get("provider_role"), NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_ROLE)
    connector_id = _normalize_text(provider_capability.get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID)
    connector_name = _normalize_text(provider_capability.get("connector_name"), "NFL Schedule Connector")
    connector_family = _normalize_text(provider_capability.get("connector_family"), "feeds")
    payload.update(
        {
            "source_name": provider_name,
            "source_type": NFL_SCHEDULE_PROVIDER_SOURCE_TYPE,
            "source_key": NFL_SCHEDULE_PROVIDER_SOURCE_ID,
            "provider": provider_id,
            "provider_name": provider_name,
            "provider_role": provider_role,
            "connector_id": connector_id,
            "connector_name": connector_name,
            "connector_family": connector_family,
            "connector_role": "production_connector",
            "execution_mode": execution_mode,
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_table": table_name,
            "acquisition_timestamp": _normalize_text(source_bundle.get("acquisition_timestamp"), _utc_now_iso()),
            "provider_capability": dict(provider_capability),
        }
    )
    return payload


def _build_nfl_research_asset_identity(
    *,
    asset_id: str,
    asset_name: str,
    asset_type: str,
    market_type: str,
    row: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
    selection: str = "",
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    payload = dict(row)
    return build_research_asset_identity_contract(
        asset_id=asset_id,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market=_normalize_text(payload.get("market"), "nfl_p0"),
        league=_normalize_text(profile.metadata.get("league"), "NFL"),
        sport=_normalize_text(profile.metadata.get("sport"), "football"),
        season=_normalize_text(payload.get("season")),
        week_or_date=_normalize_text(payload.get("week")),
        event_id=_normalize_text(payload.get("event_id"), _normalize_text(payload.get("game_id"))),
        market_id=_normalize_text(payload.get("market_id"), _normalize_text(payload.get("schedule_id"), _normalize_text(payload.get("game_id")))),
        selection=_normalize_text(payload.get("selection"), selection),
        provider=_normalize_text(source_bundle.get("provider"), NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE),
        connector=_normalize_text(source_bundle.get("connector_id") or source_bundle.get("connector_name"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=_normalize_text(payload.get("schema_version"), NFL_P0_SCHEMA_VERSION),
        lineage_version=_normalize_text(dataset_version, NFL_SCHEDULE_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name=asset_name,
        asset_type=asset_type,
        participant_id="",
        team_id=_normalize_text(payload.get("team_id"), _normalize_text(payload.get("home_team_id"), _normalize_text(payload.get("away_team_id")))),
        game_id=_normalize_text(payload.get("game_id")),
        market_type=market_type,
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_P0_SOURCE_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_P0_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id") or source_bundle.get("connector_name")),
            "connector_name": _normalize_text(source_bundle.get("connector_name")),
            "connector_family": _normalize_text(source_bundle.get("connector_family")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
            "dataset_version": dataset_version,
            "schedule_id": _normalize_text(payload.get("schedule_id")),
            "game_id": _normalize_text(payload.get("game_id")),
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
        },
    ).as_dict()


def _promote_nfl_asset_lifecycle(
    *,
    lifecycle_runtime: ResearchAssetLifecycleRuntime,
    identity: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    raw_acquisition_result: Mapping[str, Any],
    created_at: str,
    normalized_rows: Sequence[Mapping[str, Any]],
    alignment_result: Mapping[str, Any],
    certification_result: Mapping[str, Any],
    dataset_result: Mapping[str, Any],
    asset_label: str,
    future_joins: Sequence[str],
) -> None:
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="discovered",
        lifecycle_reason=f"{asset_label} asset discovered through the production connector path",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"row_count": len(normalized_rows)},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="source_identified",
        lifecycle_reason=f"source identified for {asset_label} research asset",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_ROLE)},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="connector_mapped",
        lifecycle_reason=f"connector mapped for {asset_label} research asset",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), "deterministic_fixture"),
        },
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="raw_acquired",
        lifecycle_reason=f"raw {asset_label} payload staged in the shared raw acquisition cache",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"raw_record_count": raw_acquisition_result.get("raw_record_count", 0)},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="integrity_verified",
        lifecycle_reason=f"integrity verified for {asset_label} raw payload",
        alignment_certification=alignment_result["alignment_certification"],
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"alignment_status": alignment_result["alignment_certification"].get("alignment_status")},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="normalized",
        lifecycle_reason=f"{asset_label} rows normalized into the canonical nfl_p0 storage tables",
        alignment_certification=alignment_result["alignment_certification"],
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"normalized_row_count": len(normalized_rows)},
    )
    lifecycle_runtime.record_research_asset_certified(
        identity=identity,
        certification_result={
            **dict(certification_result),
            "alignment_certification": alignment_result["alignment_certification"],
        },
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
    )
    lifecycle_runtime.record_dataset_certified(
        identity=identity,
        certification_result=dataset_result,
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="feature_ready",
        lifecycle_reason=f"{asset_label} asset ready for future joins and research asset population",
        alignment_certification=alignment_result["alignment_certification"],
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "feature_ready": True,
            "future_joins": list(future_joins),
        },
    )


def _first_schedule_row(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, Mapping):
            return dict(row)
    return {}


def _certify_time_entity_alignments_for_rows(
    *,
    lifecycle_runtime: ResearchAssetLifecycleRuntime,
    rows: Sequence[Mapping[str, Any]],
    identity_builder,
    required_fields: Sequence[str],
    required_timestamps: Sequence[str],
    profile: Any,
    source_bundle: Mapping[str, Any],
    raw_acquisition_result: Mapping[str, Any],
    created_at: str,
) -> list[dict[str, Any]]:
    alignment_results: list[dict[str, Any]] = []
    for row in rows:
        identity = identity_builder(row)
        alignment_results.append(
            lifecycle_runtime.certify_time_entity_alignment(
                identity=identity,
                rows=[row],
                required_fields=required_fields,
                required_timestamps=required_timestamps,
                profile=profile,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=created_at,
                lifecycle_state="integrity_verified",
            )
        )
    return alignment_results


def build_nfl_schedule_research_asset_fixture(
    game_count: int = 1,
    *,
    dataset_version: str | None = None,
) -> dict[str, Any]:
    fixture = build_nfl_p0_fixture(game_count=max(int(game_count or 1), 1), dataset_version=dataset_version or NFL_P0_DATASET_VERSION)
    schedule_rows = [dict(row) for row in fixture["tables"].get("nfl_schedule", [])][:1]
    if not schedule_rows:
        raise ValueError("NFL schedule fixture did not produce any schedule rows")
    selected_row = schedule_rows[0]
    schedule_market_id = _normalize_text(selected_row.get("schedule_id"), _normalize_text(selected_row.get("game_id"), "nfl_schedule"))
    schedule_selection = "schedule"
    schedule_team_id = _normalize_text(selected_row.get("home_team_id"), _normalize_text(selected_row.get("away_team_id"), "NFL"))
    schedule_result_timestamp = _normalize_text(selected_row.get("kickoff_time"), _normalize_text(selected_row.get("source_snapshot_time"), _utc_now_iso()))
    selected_row.update(
        {
            "market_id": schedule_market_id,
            "selection": schedule_selection,
            "team_id": schedule_team_id,
            "result_timestamp": schedule_result_timestamp,
            "source_market_id": schedule_market_id,
            "source_selection_id": schedule_selection,
            "provider_timestamp": _normalize_text(selected_row.get("source_snapshot_time"), schedule_result_timestamp),
        }
    )
    created_at = _normalize_text(fixture.get("created_at"), _utc_now_iso())
    source_bundle_id = _stable_id(
        "nfl_schedule_source_bundle",
        fixture.get("dataset_version"),
        selected_row.get("game_id"),
        selected_row.get("season"),
        selected_row.get("week"),
    )
    source_bundle = {
        "dataset_id": "dataset.sports.nfl.schedule.raw_acquisition_cache",
        "dataset_name": NFL_SCHEDULE_RAW_ACQUISITION_DATASET_NAME,
        "source_name": fixture.get("source_name", NFL_P0_SOURCE_NAME),
        "source_type": fixture.get("source_type", NFL_P0_SOURCE_TYPE),
        "source_key": fixture.get("source_key", NFL_P0_SOURCE_NAME),
        "provider": fixture.get("provider", NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE),
        "provider_sources": [fixture.get("source_name", NFL_P0_SOURCE_NAME)],
        "provider_versions": [fixture.get("dataset_version", NFL_P0_DATASET_VERSION)],
        "source_bundle_id": source_bundle_id,
        "acquisition_timestamp": created_at,
        "source_snapshot_time": _normalize_text(selected_row.get("source_snapshot_time"), created_at),
        "result_timestamp": schedule_result_timestamp,
        "source_market_id": schedule_market_id,
        "source_selection_id": schedule_selection,
        "dataset_version": fixture.get("dataset_version", NFL_P0_DATASET_VERSION),
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "source_tables": {"nfl_schedule": schedule_rows},
        "tables": {"nfl_schedule": schedule_rows},
        "source_file": "deterministic_nfl_schedule_fixture.csv",
        "update_frequency": "manual",
    }
    return {
        "dataset_version": fixture.get("dataset_version", NFL_P0_DATASET_VERSION),
        "created_at": created_at,
        "game_count": 1,
        "source_name": source_bundle["source_name"],
        "source_type": source_bundle["source_type"],
        "source_key": source_bundle["source_key"],
        "provider": source_bundle["provider"],
        "source_bundle_id": source_bundle_id,
        "schedule_rows": schedule_rows,
        "source_bundle": source_bundle,
        "fixture": fixture,
    }


def build_nfl_schedule_research_asset_identity(
    *,
    schedule_row: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    return _build_nfl_research_asset_identity(
        asset_id=DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
        asset_name="NFL Schedule",
        asset_type="schedule",
        market_type=_normalize_text(schedule_row.get("market_type"), "schedule"),
        row=schedule_row,
        source_bundle=source_bundle,
        dataset_version=dataset_version,
        selection="schedule",
    )


def build_nfl_schedule_research_asset_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    fixture: Mapping[str, Any] | None = None,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
    normalized_rows: Sequence[Mapping[str, Any]] | None = None,
    validation: Mapping[str, Any] | None = None,
    certification_result: Mapping[str, Any] | None = None,
    dataset_result: Mapping[str, Any] | None = None,
    lifecycle_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    close_storage = True
    try:
        schedule_rows = [dict(row) for row in normalized_rows or storage.fetch("nfl_schedule", order_by="schedule_id ASC")]
        certification_rows = [
            dict(row)
            for row in storage.fetch(
                "historical_research_asset_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID],
                order_by="certification_id ASC",
            )
        ] if storage.table_exists("historical_research_asset_certifications") else []
        dataset_rows = [
            dict(row)
            for row in storage.fetch("historical_certifications", order_by="certification_id ASC")
        ] if storage.table_exists("historical_certifications") else []
        lifecycle_rows = [
            dict(row)
            for row in storage.fetch(
                "research_asset_lifecycles",
                where="asset_id = ?",
                params=[DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID],
                order_by="updated_at ASC",
            )
        ] if storage.table_exists("research_asset_lifecycles") else []
        alignment_rows = [
            dict(row)
            for row in storage.fetch(
                "research_asset_alignment_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID],
                order_by="alignment_certification_id ASC",
            )
        ] if storage.table_exists("research_asset_alignment_certifications") else []
        schedule_validation = dict(validation or validate_nfl_p0_rows("nfl_schedule", schedule_rows))
        asset_rows = certification_rows
        asset_status = _normalize_text(asset_rows[-1].get("certification_status"), "missing") if asset_rows else "missing"
        lifecycle_state = _normalize_text(lifecycle_rows[-1].get("lifecycle_state"), "missing") if lifecycle_rows else "missing"
        alignment_status = _normalize_text(alignment_rows[-1].get("alignment_status"), "missing") if alignment_rows else "missing"
        ready = bool(
            schedule_rows
            and schedule_validation.get("ok")
            and asset_rows
            and asset_status == "certified"
            and dataset_rows
            and _normalize_text(dataset_rows[-1].get("certification_status")) == "certified"
            and lifecycle_state == "feature_ready"
            and alignment_status == "aligned"
        )
        seasons = sorted({str(row.get("season")) for row in schedule_rows if _normalize_text(row.get("season"))})
        source_summary = {
            "source_name": _normalize_text((certification_result or {}).get("source_name") or (source_bundle or {}).get("source_name") or (fixture or {}).get("source_name"), NFL_P0_SOURCE_NAME),
            "source_type": _normalize_text((certification_result or {}).get("source_type") or (source_bundle or {}).get("source_type") or (fixture or {}).get("source_type"), NFL_P0_SOURCE_TYPE),
            "source_key": _normalize_text((certification_result or {}).get("source_key") or (source_bundle or {}).get("source_key") or (fixture or {}).get("source_key"), NFL_P0_SOURCE_NAME),
            "provider": _normalize_text((certification_result or {}).get("provider") or (source_bundle or {}).get("provider") or (fixture or {}).get("provider"), NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE),
        }
        connector_summary = {
            "connector_id": _normalize_text((source_bundle or {}).get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text((source_bundle or {}).get("connector_name"), "NFL Schedule Connector"),
            "connector_family": _normalize_text((source_bundle or {}).get("connector_family"), "feeds"),
            "execution_mode": _normalize_text((source_bundle or {}).get("execution_mode"), "deterministic_fixture"),
            "provider_capability": dict((source_bundle or {}).get("provider_capability") or {}),
            "field_provenance": dict((source_bundle or {}).get("field_provenance") or {}),
            "supported_assets": list((source_bundle or {}).get("provider_capability", {}).get("supported_assets", [])),
            "supported_fields": list((source_bundle or {}).get("provider_capability", {}).get("supported_fields", [])),
        }
        return {
            "ok": ready,
            "status": "ready" if ready else "partial" if schedule_rows or asset_rows or lifecycle_rows else "missing",
            "asset_id": DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
            "asset_name": "NFL Schedule",
            "lifecycle_state": lifecycle_state,
            "certification_status": asset_status,
            "dataset_certification_status": _normalize_text(dataset_rows[-1].get("certification_status"), "missing") if dataset_rows else "missing",
            "row_count": len(schedule_rows),
            "rows_produced": len(schedule_rows),
            "coverage_seasons": seasons,
            "missing_required_fields": list(schedule_validation.get("missing_fields", [])),
            "alignment_failures": [dict(row) for row in alignment_rows if _normalize_text(row.get("alignment_status")) != "aligned"],
            "source_provider_role": source_summary,
            "connector_state": connector_summary,
            "provider_capability": connector_summary["provider_capability"],
            "field_provenance": connector_summary["field_provenance"],
            "readiness_percentage": 100.0 if ready else round(100.0 * (1.0 if schedule_rows else 0.0), 2),
            "source_bundle": dict(source_bundle or (fixture or {}).get("source_bundle") or {}),
            "validation": schedule_validation,
            "research_asset_certifications": asset_rows,
            "dataset_certifications": dataset_rows,
            "research_asset_lifecycles": lifecycle_rows,
            "research_asset_alignment_certifications": alignment_rows,
            "normalized_rows": schedule_rows,
            "notes": [
                "The NFL schedule asset is populated through the canonical NFL schedule connector path.",
                "When live provider access is unavailable, the connector uses deterministic offline mode backed by the shared raw acquisition cache.",
                "The schedule slice is certified before later assets such as results, odds, weather, injuries, and team statistics exist.",
                "This asset preserves the join keys needed for future event-centric research and queryability.",
            ],
            "storage": storage.health(),
            "fixture_summary": {
                "game_count": (fixture or {}).get("game_count", len(schedule_rows)),
                "dataset_version": (fixture or {}).get("dataset_version") or (raw_acquisition_result or {}).get("dataset_version") or NFL_P0_DATASET_VERSION,
            },
        }
    finally:
        if close_storage:
            storage.close()


def build_nfl_schedule_research_asset_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    game_count: int = 1,
    dataset_version: str | None = None,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    if profile.profile_id != NFL_SCHEDULE_RESEARCH_ASSET_PROFILE_ID:
        raise ValueError(f"unexpected market profile: {profile.profile_id}")

    connector_bundle = build_nfl_schedule_connector_bundle(game_count=game_count, dataset_version=dataset_version)
    source_bundle = dict(connector_bundle["source_bundle"])
    games_rows = [dict(row) for row in connector_bundle.get("games_rows", [])]
    schedule_rows = [dict(row) for row in connector_bundle.get("schedule_rows", [])]
    source_tables = dict(source_bundle.get("source_tables") or {})
    storage_rows = {
        "nfl_games": [dict(row) for row in source_tables.get("nfl_games", games_rows)],
        "nfl_schedule": [dict(row) for row in source_tables.get("nfl_schedule", schedule_rows)],
    }
    created_at = _normalize_text(connector_bundle["created_at"], _utc_now_iso())
    dataset_version = _normalize_text(connector_bundle["dataset_version"], NFL_P0_DATASET_VERSION)
    storage_path = Path(storage_path or NFL_SCHEDULE_RESEARCH_ASSET_STORAGE_PATH).expanduser().resolve()

    acquisition_runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path, backend=backend)
    try:
        raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id=profile.profile_id,
            dataset_name=NFL_SCHEDULE_RAW_ACQUISITION_DATASET_NAME,
        )
    finally:
        acquisition_runtime.close()

    asset_contracts = {
        contract.research_asset_id: contract
        for contract in build_nfl_research_asset_certification_contracts(profile_id=profile.profile_id)
    }
    games_contract = asset_contracts["dataset.nfl.games"]
    schedule_contract = asset_contracts[DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID]

    games_normalized = normalize_nfl_p0_rows(
        "nfl_games",
        storage_rows["nfl_games"] or games_rows,
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    schedule_normalized = normalize_nfl_p0_rows(
        "nfl_schedule",
        storage_rows["nfl_schedule"] or schedule_rows,
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    games_certification_rows = [dict(row) for row in games_normalized]
    schedule_certification_rows = [dict(row) for row in schedule_normalized]
    for row in games_certification_rows:
        row.update(
            {
                "asset_id": "dataset.nfl.games",
                "asset_family": "dataset",
                "market_profile": profile.profile_id,
                "market_id": _normalize_text(row.get("market_id"), _normalize_text(row.get("game_id"))),
                "selection": _normalize_text(row.get("selection"), "game_identity"),
                "team_id": _normalize_text(row.get("team_id"), _normalize_text(row.get("home_team_id"), _normalize_text(row.get("away_team_id")))),
                "result_timestamp": _normalize_text(row.get("result_timestamp"), _normalize_text(row.get("kickoff_time"), created_at)),
                "source_market_id": _normalize_text(row.get("source_market_id"), _normalize_text(row.get("game_id"))),
                "source_selection_id": _normalize_text(row.get("source_selection_id"), _normalize_text(row.get("selection"), "game_identity")),
                "provider_timestamp": _normalize_text(row.get("provider_timestamp"), _normalize_text(row.get("source_snapshot_time"), created_at)),
                "league": _normalize_text(profile.metadata.get("league"), "NFL"),
                "sport": _normalize_text(profile.metadata.get("sport"), "football"),
                "event_id": _normalize_text(row.get("event_id"), _normalize_text(row.get("game_id"))),
                "asset_name": "NFL Games",
                "asset_type": "game_identity",
                "connector": _normalize_text(source_bundle.get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
                "provider": _normalize_text(source_bundle.get("provider"), NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE),
                "source_name": _normalize_text(source_bundle.get("source_name"), NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER),
                "source_type": _normalize_text(source_bundle.get("source_type"), NFL_SCHEDULE_PROVIDER_SOURCE_TYPE),
                "source_key": _normalize_text(source_bundle.get("source_key"), NFL_SCHEDULE_PROVIDER_SOURCE_ID),
                "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
                "connector_name": _normalize_text(source_bundle.get("connector_name"), "NFL Schedule Connector"),
                "connector_family": _normalize_text(source_bundle.get("connector_family"), "feeds"),
                "execution_mode": _normalize_text(source_bundle.get("execution_mode"), "deterministic_fixture"),
                "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_ROLE),
            }
        )
    for row in schedule_certification_rows:
        row.update(
            {
                "asset_id": DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
                "asset_family": "dataset",
                "market_profile": profile.profile_id,
                "market_id": _normalize_text(row.get("market_id"), _normalize_text(row.get("schedule_id"), _normalize_text(row.get("game_id")))),
                "selection": _normalize_text(row.get("selection"), "schedule"),
                "team_id": _normalize_text(row.get("team_id"), _normalize_text(row.get("home_team_id"), _normalize_text(row.get("away_team_id")))),
                "result_timestamp": _normalize_text(row.get("result_timestamp"), _normalize_text(row.get("kickoff_time"), created_at)),
                "source_market_id": _normalize_text(row.get("source_market_id"), _normalize_text(row.get("schedule_id"), _normalize_text(row.get("game_id")))),
                "source_selection_id": _normalize_text(row.get("source_selection_id"), _normalize_text(row.get("selection"), "schedule")),
                "provider_timestamp": _normalize_text(row.get("provider_timestamp"), _normalize_text(row.get("source_snapshot_time"), created_at)),
                "league": _normalize_text(profile.metadata.get("league"), "NFL"),
                "sport": _normalize_text(profile.metadata.get("sport"), "football"),
                "event_id": _normalize_text(row.get("event_id"), _normalize_text(row.get("game_id"))),
                "asset_name": "NFL Schedule",
                "asset_type": "schedule",
                "connector": _normalize_text(source_bundle.get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
                "provider": _normalize_text(source_bundle.get("provider"), NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE),
                "source_name": _normalize_text(source_bundle.get("source_name"), NFL_P0_SOURCE_NAME),
                "source_type": _normalize_text(source_bundle.get("source_type"), NFL_SCHEDULE_PROVIDER_SOURCE_TYPE),
                "source_key": _normalize_text(source_bundle.get("source_key"), NFL_SCHEDULE_PROVIDER_SOURCE_ID),
                "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_SCHEDULE_RESEARCH_ASSET_CONNECTOR_ID),
                "connector_name": _normalize_text(source_bundle.get("connector_name"), "NFL Schedule Connector"),
                "connector_family": _normalize_text(source_bundle.get("connector_family"), "feeds"),
                "execution_mode": _normalize_text(source_bundle.get("execution_mode"), "deterministic_fixture"),
                "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_SCHEDULE_RESEARCH_ASSET_PROVIDER_ROLE),
            }
        )
    games_validation = validate_nfl_p0_rows("nfl_games", games_certification_rows)
    schedule_validation = validate_nfl_p0_rows("nfl_schedule", schedule_certification_rows)
    validation = {
        "ok": bool(games_validation.get("ok")) and bool(schedule_validation.get("ok")),
        "status": "validated" if bool(games_validation.get("ok")) and bool(schedule_validation.get("ok")) else "rejected",
        "games": games_validation,
        "schedule": schedule_validation,
    }
    alignment_game_rows = [dict(row) for row in games_certification_rows]
    alignment_schedule_rows = [dict(row) for row in schedule_certification_rows]
    for row in alignment_game_rows + alignment_schedule_rows:
        row["schema_version"] = RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION
        row["lineage_version"] = dataset_version

    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        games_table_contract = NFL_P0_TABLE_CONTRACTS["nfl_games"]
        schedule_table_contract = NFL_P0_TABLE_CONTRACTS["nfl_schedule"]
        games_storage_columns = set(storage.table_columns("nfl_games"))
        schedule_storage_columns = set(storage.table_columns("nfl_schedule"))
        games_storage_rows = [{key: value for key, value in row.items() if key in games_storage_columns} for row in games_normalized]
        schedule_storage_rows = [{key: value for key, value in row.items() if key in schedule_storage_columns} for row in schedule_normalized]
        for row in games_storage_rows:
            storage.upsert("nfl_games", row, key_columns=(games_table_contract.row_id_field,))
        for row in schedule_storage_rows:
            storage.upsert("nfl_schedule", row, key_columns=(schedule_table_contract.row_id_field,))
    finally:
        storage.close()

    certification_runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path, backend=backend)
    try:
        games_result = certification_runtime.certify_research_asset(
            asset_contract=games_contract,
            rows=games_certification_rows,
            profile_id=profile.profile_id,
            validation=games_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=dataset_version,
            created_at=created_at,
            batch_id=f"{dataset_version}.batch.001",
        )
        schedule_result = certification_runtime.certify_research_asset(
            asset_contract=schedule_contract,
            rows=schedule_certification_rows,
            profile_id=profile.profile_id,
            validation=schedule_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=dataset_version,
            created_at=created_at,
            batch_id=f"{dataset_version}.batch.001",
        )
        dataset_row = build_historical_dataset_certification_row(
            profile=profile,
            dataset_version=dataset_version,
            batch_id=f"{dataset_version}.batch.001",
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=[games_result["research_asset_certification"], schedule_result["research_asset_certification"]],
        )
        certification_runtime.store.upsert("historical_certifications", dataset_row, key_columns=("certification_id",))
    finally:
        certification_runtime.close()

    lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path, backend=backend)
    try:
        games_alignment_results = _certify_time_entity_alignments_for_rows(
            lifecycle_runtime=lifecycle_runtime,
            rows=alignment_game_rows,
            identity_builder=lambda row: _build_nfl_research_asset_identity(
                asset_id="dataset.nfl.games",
                asset_name="NFL Games",
                asset_type="game_identity",
                market_type="game_identity",
                row=row,
                source_bundle=source_bundle,
                dataset_version=dataset_version,
                selection="game_identity",
            ),
            required_fields=games_contract.required_fields,
            required_timestamps=games_contract.required_timestamps,
            profile=profile,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
        )
        schedule_alignment_results = _certify_time_entity_alignments_for_rows(
            lifecycle_runtime=lifecycle_runtime,
            rows=alignment_schedule_rows,
            identity_builder=lambda row: build_nfl_schedule_research_asset_identity(
                schedule_row=row,
                source_bundle=source_bundle,
                dataset_version=dataset_version,
            ),
            required_fields=schedule_contract.required_fields,
            required_timestamps=schedule_contract.required_timestamps,
            profile=profile,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
        )
        games_alignment_result = games_alignment_results[-1] if games_alignment_results else {}
        schedule_alignment_result = schedule_alignment_results[-1] if schedule_alignment_results else {}
        _promote_nfl_asset_lifecycle(
            lifecycle_runtime=lifecycle_runtime,
            identity=_build_nfl_research_asset_identity(
                asset_id="dataset.nfl.games",
                asset_name="NFL Games",
                asset_type="game_identity",
                market_type="game_identity",
                row=alignment_game_rows[-1],
                source_bundle=source_bundle,
                dataset_version=dataset_version,
                selection="game_identity",
            ),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            normalized_rows=alignment_game_rows,
            alignment_result=games_alignment_result,
            certification_result=games_result,
            dataset_result=dataset_row,
            asset_label="NFL games",
            future_joins=["schedule", "results", "odds", "weather", "injuries", "officials", "team_stats"],
        )
        _promote_nfl_asset_lifecycle(
            lifecycle_runtime=lifecycle_runtime,
            identity=build_nfl_schedule_research_asset_identity(
                schedule_row=alignment_schedule_rows[-1],
                source_bundle=source_bundle,
                dataset_version=dataset_version,
            ),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            normalized_rows=alignment_schedule_rows,
            alignment_result=schedule_alignment_result,
            certification_result=schedule_result,
            dataset_result=dataset_row,
            asset_label="NFL schedule",
            future_joins=["results", "odds", "weather", "injuries", "officials", "team_stats"],
        )
        readiness_snapshot = build_nfl_schedule_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=connector_bundle,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=alignment_schedule_rows,
            validation=schedule_validation,
            certification_result=schedule_result,
            dataset_result=dataset_row,
            lifecycle_result=schedule_alignment_result,
        )
        return {
            "ok": readiness_snapshot["ok"],
            "status": readiness_snapshot["status"],
            "profile": profile.as_dict(),
            "storage_path": str(storage_path),
            "fixture": connector_bundle,
            "source_bundle": source_bundle,
            "raw_acquisition_result": raw_acquisition_result,
            "normalized_rows": alignment_schedule_rows,
            "games_normalized_rows": alignment_game_rows,
            "validation": validation,
            "games_validation": games_validation,
            "schedule_validation": schedule_validation,
            "games_research_asset_certification": games_result["research_asset_certification"],
            "research_asset_certification": schedule_result["research_asset_certification"],
            "dataset_certification": dataset_row,
            "games_alignment_results": games_alignment_results,
            "schedule_alignment_results": schedule_alignment_results,
            "games_lifecycle_alignment": games_alignment_result,
            "lifecycle_alignment": schedule_alignment_result,
            "readiness_snapshot": readiness_snapshot,
        }
    finally:
        lifecycle_runtime.close()


__all__ = [
    "DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID",
    "NFL_SCHEDULE_RESEARCH_ASSET_DATASET_NAME",
    "NFL_SCHEDULE_RESEARCH_ASSET_LIFECYCLE_VERSION",
    "NFL_SCHEDULE_RESEARCH_ASSET_PROFILE_ID",
    "NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE",
    "NFL_SCHEDULE_RESEARCH_ASSET_STORAGE_PATH",
    "NFL_SCHEDULE_RAW_ACQUISITION_DATASET_NAME",
    "build_nfl_schedule_research_asset_dashboard_snapshot",
    "build_nfl_schedule_research_asset_fixture",
    "build_nfl_schedule_research_asset_identity",
    "build_nfl_schedule_research_asset_population",
]
