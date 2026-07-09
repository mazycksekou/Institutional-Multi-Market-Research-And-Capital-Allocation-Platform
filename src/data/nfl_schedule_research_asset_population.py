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
    build_nfl_schedule_research_asset_certification_contract,
)
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
NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE = "local_fixture"
NFL_SCHEDULE_RESEARCH_ASSET_PROFILE_ID = "sports:nfl"
NFL_SCHEDULE_RESEARCH_ASSET_LIFECYCLE_VERSION = "v1"


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


def _first_schedule_row(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, Mapping):
            return dict(row)
    return {}


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
    profile = get_nfl_p0_market_profile()
    row = dict(schedule_row)
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market=_normalize_text(row.get("market"), "nfl_p0"),
        league=_normalize_text(profile.metadata.get("league"), "NFL"),
        sport=_normalize_text(profile.metadata.get("sport"), "football"),
        season=_normalize_text(row.get("season")),
        week_or_date=_normalize_text(row.get("week")),
        event_id=_normalize_text(row.get("game_id")),
        game_id=_normalize_text(row.get("game_id")),
        market_id=_normalize_text(row.get("market_id"), _normalize_text(row.get("schedule_id"), _normalize_text(row.get("game_id")))),
        selection=_normalize_text(row.get("selection"), "schedule"),
        provider=_normalize_text(source_bundle.get("provider"), NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE),
        connector=_normalize_text(source_bundle.get("source_type"), NFL_P0_SOURCE_TYPE),
        schema_version=_normalize_text(row.get("schema_version"), NFL_P0_SCHEMA_VERSION),
        lineage_version=_normalize_text(dataset_version, NFL_SCHEDULE_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Schedule",
        asset_type="schedule",
        participant_id="",
        team_id=_normalize_text(row.get("team_id"), _normalize_text(row.get("home_team_id"), _normalize_text(row.get("away_team_id")))),
        market_type=_normalize_text(row.get("market_type"), "schedule"),
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_P0_SOURCE_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_P0_SOURCE_TYPE),
            "dataset_version": dataset_version,
            "schedule_id": _normalize_text(row.get("schedule_id")),
            "game_id": _normalize_text(row.get("game_id")),
        },
    ).as_dict()


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
            "readiness_percentage": 100.0 if ready else round(100.0 * (1.0 if schedule_rows else 0.0), 2),
            "source_bundle": dict(source_bundle or (fixture or {}).get("source_bundle") or {}),
            "validation": schedule_validation,
            "research_asset_certifications": asset_rows,
            "dataset_certifications": dataset_rows,
            "research_asset_lifecycles": lifecycle_rows,
            "research_asset_alignment_certifications": alignment_rows,
            "normalized_rows": schedule_rows,
            "notes": [
                "The NFL schedule asset is intentionally populated from a deterministic local fixture.",
                "The raw acquisition cache remains the shared first hop before normalization and certification.",
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

    fixture_bundle = build_nfl_schedule_research_asset_fixture(game_count=game_count, dataset_version=dataset_version)
    source_bundle = dict(fixture_bundle["source_bundle"])
    schedule_rows = [dict(row) for row in fixture_bundle["schedule_rows"]]
    storage_rows = [dict(row) for row in (fixture_bundle["fixture"].get("tables", {}).get("nfl_schedule", []) if isinstance(fixture_bundle.get("fixture"), dict) else [])][:1]
    created_at = _normalize_text(fixture_bundle["created_at"], _utc_now_iso())
    dataset_version = _normalize_text(fixture_bundle["dataset_version"], NFL_P0_DATASET_VERSION)
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

    normalized_rows = normalize_nfl_p0_rows(
        "nfl_schedule",
        storage_rows or schedule_rows,
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    certification_rows = [dict(row) for row in normalized_rows]
    for index, row in enumerate(certification_rows):
        source_row = schedule_rows[min(index, len(schedule_rows) - 1)]
        row.update(
            {
                "asset_id": DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
                "asset_family": "dataset",
                "market_profile": profile.profile_id,
                "market_id": _normalize_text(source_row.get("market_id"), _normalize_text(source_row.get("schedule_id"), _normalize_text(source_row.get("game_id")))),
                "selection": _normalize_text(source_row.get("selection"), "schedule"),
                "team_id": _normalize_text(source_row.get("team_id"), _normalize_text(source_row.get("home_team_id"), _normalize_text(source_row.get("away_team_id")))),
                "result_timestamp": _normalize_text(source_row.get("result_timestamp"), _normalize_text(source_row.get("kickoff_time"), created_at)),
                "source_market_id": _normalize_text(source_row.get("source_market_id"), _normalize_text(source_row.get("schedule_id"), _normalize_text(source_row.get("game_id")))),
                "source_selection_id": _normalize_text(source_row.get("source_selection_id"), _normalize_text(source_row.get("selection"), "schedule")),
                "provider_timestamp": _normalize_text(source_row.get("provider_timestamp"), _normalize_text(source_row.get("source_snapshot_time"), created_at)),
                "league": _normalize_text(profile.metadata.get("league"), "NFL"),
                "sport": _normalize_text(profile.metadata.get("sport"), "football"),
                "event_id": _normalize_text(source_row.get("event_id"), _normalize_text(source_row.get("game_id"))),
                "asset_name": "NFL Schedule",
                "asset_type": "schedule",
                "connector": _normalize_text(source_bundle.get("source_type"), NFL_P0_SOURCE_TYPE),
            }
        )
    alignment_rows = [dict(row) for row in certification_rows]
    for row in alignment_rows:
        row["schema_version"] = RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION
        row["lineage_version"] = dataset_version
    validation = validate_nfl_p0_rows("nfl_schedule", certification_rows)

    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        schedule_contract = NFL_P0_TABLE_CONTRACTS["nfl_schedule"]
        for row in normalized_rows:
            storage.upsert("nfl_schedule", row, key_columns=(schedule_contract.row_id_field,))
    finally:
        storage.close()

    certification_runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path, backend=backend)
    try:
        asset_contract = build_nfl_schedule_research_asset_certification_contract(profile_id=profile.profile_id)
        asset_result = certification_runtime.certify_research_asset(
            asset_contract=asset_contract,
            rows=certification_rows,
            profile_id=profile.profile_id,
            validation=validation,
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
            asset_rows=[asset_result["research_asset_certification"]],
        )
        certification_runtime.store.upsert("historical_certifications", dataset_row, key_columns=("certification_id",))
    finally:
        certification_runtime.close()

    lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path, backend=backend)
    try:
        identity = build_nfl_schedule_research_asset_identity(
            schedule_row=alignment_rows[0],
            source_bundle=source_bundle,
            dataset_version=dataset_version,
        )
        lifecycle_runtime.record_lifecycle_state(
            identity=identity,
            lifecycle_state="discovered",
            lifecycle_reason="schedule asset discovered from deterministic local fixture",
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes={"game_count": len(normalized_rows)},
        )
        lifecycle_runtime.record_lifecycle_state(
            identity=identity,
            lifecycle_state="source_identified",
            lifecycle_reason="source identified for NFL schedule research asset",
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes={"source_role": NFL_SCHEDULE_RESEARCH_ASSET_SOURCE_ROLE},
        )
        lifecycle_runtime.record_lifecycle_state(
            identity=identity,
            lifecycle_state="connector_mapped",
            lifecycle_reason="deterministic fixture mapped to shared raw acquisition cache",
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes={"connector": "local_fixture"},
        )
        lifecycle_runtime.record_lifecycle_state(
            identity=identity,
            lifecycle_state="raw_acquired",
            lifecycle_reason="raw schedule payload staged in the shared raw acquisition cache",
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes={"raw_record_count": raw_acquisition_result.get("raw_record_count", 0)},
        )
        alignment_result = lifecycle_runtime.certify_time_entity_alignment(
            identity=identity,
            rows=alignment_rows,
            required_fields=schedule_contract.required_fields,
            required_timestamps=schedule_contract.required_timestamps,
            profile=profile,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            lifecycle_state="integrity_verified",
        )
        lifecycle_runtime.record_lifecycle_state(
            identity=identity,
            lifecycle_state="normalized",
            lifecycle_reason="schedule rows normalized into the canonical nfl_schedule table",
            alignment_certification=alignment_result["alignment_certification"],
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes={"normalized_row_count": len(alignment_rows)},
        )
        lifecycle_runtime.record_research_asset_certified(
            identity=identity,
            certification_result={
                **asset_result,
                "alignment_certification": alignment_result["alignment_certification"],
            },
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
        )
        lifecycle_runtime.record_dataset_certified(
            identity=identity,
            certification_result=dataset_row,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
        )
        lifecycle_runtime.record_lifecycle_state(
            identity=identity,
            lifecycle_state="feature_ready",
            lifecycle_reason="schedule asset ready for later feature population and event-centric joins",
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes={
                "feature_ready": True,
                "future_joins": ["results", "odds", "weather", "injuries", "officials", "team_stats"],
            },
        )
        readiness_snapshot = build_nfl_schedule_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=fixture_bundle,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=alignment_rows,
            validation=validation,
            certification_result=asset_result,
            dataset_result=dataset_row,
            lifecycle_result=alignment_result,
        )
        return {
            "ok": readiness_snapshot["ok"],
            "status": readiness_snapshot["status"],
            "profile": profile.as_dict(),
            "storage_path": str(storage_path),
            "fixture": fixture_bundle,
            "source_bundle": source_bundle,
            "raw_acquisition_result": raw_acquisition_result,
            "normalized_rows": alignment_rows,
            "validation": validation,
            "research_asset_certification": asset_result["research_asset_certification"],
            "dataset_certification": dataset_row,
            "lifecycle_alignment": alignment_result,
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
