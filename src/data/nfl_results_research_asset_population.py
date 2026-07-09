from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.connectors.feeds.nfl_schedule import (
    build_nfl_results_connector_bundle,
)
from src.data.data_paths import get_runtime_data_path
from src.data.historical_dataset_acquisition_runtime import HistoricalDatasetAcquisitionRuntime
from src.data.historical_research_asset_certification_runtime import (
    HistoricalResearchAssetCertificationRuntime,
    ResearchAssetCertificationContract,
    build_historical_dataset_certification_row,
)
from src.data.nfl_p0_foundation import (
    NFL_P0_DATASET_VERSION,
    NFL_P0_SCHEMA_VERSION,
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
from src.market_intelligence.research_asset_coverage_planner import (
    build_research_asset_coverage_planner_snapshot,
)
from src.storage.local_store import LocalStorageEngine


DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID = "dataset.sports.nfl.results"
NFL_RESULTS_RESEARCH_ASSET_STORAGE_PATH = get_runtime_data_path(
    "nfl_results_research_asset",
    "canonical_data.sqlite",
)
NFL_RESULTS_RESEARCH_ASSET_DATASET_NAME = "nfl_results_research_asset"
NFL_RESULTS_RAW_ACQUISITION_DATASET_NAME = "nfl_results_raw_acquisition_cache"
NFL_RESULTS_RESEARCH_ASSET_PROVIDER = "nflverse"
NFL_RESULTS_RESEARCH_ASSET_PROVIDER_SOURCE_ID = "nflverse_schedules_results"
NFL_RESULTS_RESEARCH_ASSET_PROVIDER_ROLE = "primary_acquisition"
NFL_RESULTS_RESEARCH_ASSET_SOURCE_ROLE = NFL_RESULTS_RESEARCH_ASSET_PROVIDER
NFL_RESULTS_PROVIDER_SOURCE_TYPE = "deterministic_fixture"
NFL_RESULTS_RESEARCH_ASSET_PROFILE_ID = "sports:nfl"
NFL_RESULTS_RESEARCH_ASSET_LIFECYCLE_VERSION = "v1"
NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID = "connector.feeds.nfl_schedule"
NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_NAME = "NFL Schedule Connector"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_results_field_provenance(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    created_at: str,
) -> dict[str, Any]:
    lineage_id = _stable_id(
        "nfl_results_field_lineage",
        source_bundle_id,
        _normalize_text(row.get("game_id") or row.get("result_id") or "row"),
    )
    source_provider = _normalize_text(provider_capability.get("provider_id"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER)
    source_provider_name = _normalize_text(provider_capability.get("provider_name"), "nflverse schedules/results")
    quality = _normalize_text(provider_capability.get("quality_tier"), "high_priority_adapter")
    field_source_map = {
        "result_id": "result_id",
        "game_id": "game_id",
        "event_id": "game_id",
        "season": "season",
        "season_type": "season_type",
        "week": "week",
        "game_time": "game_time",
        "scheduled_time": "game_time",
        "final_scored_at": "final_scored_at",
        "completion_timestamp": "final_scored_at",
        "final_score_home": "final_score_home",
        "final_home_score": "final_score_home",
        "final_score_away": "final_score_away",
        "final_away_score": "final_score_away",
        "winner_team_id": "winner_team_id",
        "winner_team": "winner_team",
        "winning_team": "winner_team",
        "losing_team": "derived_from_winner_team",
        "margin": "margin",
        "total_points": "total_points",
        "tie_indicator": "derived_from_scores",
        "game_completed": "derived_from_status",
        "overtime_indicator": "derived_from_game_status",
        "postseason_indicator": "derived_from_season_type",
        "source_name": "source_name",
        "source_type": "source_type",
        "source_snapshot_time": "source_snapshot_time",
        "snapshot_time": "snapshot_time",
        "provider_timestamp": "source_snapshot_time",
        "dataset_version": "dataset_version",
        "lineage_id": "lineage_id",
        "schema_version": "schema_version",
        "quality_score": "quality_score",
        "completeness_score": "completeness_score",
        "status": "status",
        "settlement_status": "settlement_status",
        "finalization_status": "finalization_status",
        "market_type": "market_type",
        "market_id": "result_id",
        "selection": "result",
        "provider": "provider",
        "connector_id": "connector_id",
        "connector_name": "connector_name",
        "connector_family": "connector_family",
        "execution_mode": "execution_mode",
    }
    provenance: dict[str, Any] = {}
    for field_name, source_field_name in field_source_map.items():
        provenance[field_name] = {
            "source_provider": source_provider,
            "source_provider_name": source_provider_name,
            "source_field_name": source_field_name,
            "raw_field_name": source_field_name if not source_field_name.startswith("derived_") else source_field_name,
            "acquisition_timestamp": created_at,
            "raw_payload_reference": f"{source_bundle_id}:nfl_results:{_normalize_text(row.get('game_id') or row.get('result_id') or 'row')}:{source_field_name}",
            "lineage_id": lineage_id,
            "confidence": 1.0 if not source_field_name.startswith("derived_") else 0.98,
            "quality": quality,
        }
    return provenance


def _build_results_asset_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
    created_at: str,
) -> dict[str, Any]:
    payload = dict(row)
    game_time = _normalize_text(payload.get("game_time"), _normalize_text(payload.get("kickoff_time")))
    final_scored_at = _normalize_text(payload.get("final_scored_at"), _normalize_text(payload.get("source_snapshot_time"), created_at))
    home_score = _normalize_int(payload.get("final_score_home"))
    away_score = _normalize_int(payload.get("final_score_away"))
    home_team = _normalize_text(payload.get("home_team"))
    away_team = _normalize_text(payload.get("away_team"))
    tied = home_score == away_score
    winner_team = "" if tied else _normalize_text(
        payload.get("winner_team"),
        home_team if home_score > away_score else away_team,
    )
    if tied:
        losing_team = ""
    elif winner_team == home_team:
        losing_team = away_team
    elif winner_team == away_team:
        losing_team = home_team
    else:
        losing_team = ""
    season_type = _normalize_text(payload.get("season_type")).upper()
    payload.update(
        {
            "asset_id": DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID,
            "asset_family": "dataset",
            "asset_name": "NFL Results",
            "asset_type": "results",
            "market_profile": NFL_RESULTS_RESEARCH_ASSET_PROFILE_ID,
            "league": _normalize_text(payload.get("league"), "NFL"),
            "sport": "football",
            "event_id": _normalize_text(payload.get("event_id"), _normalize_text(payload.get("game_id"))),
            "market_id": _normalize_text(payload.get("market_id"), _normalize_text(payload.get("result_id"), _normalize_text(payload.get("game_id")))),
            "selection": _normalize_text(payload.get("selection"), "result"),
            "team_id": _normalize_text(payload.get("team_id"), _normalize_text(payload.get("home_team_id"), home_team)),
            "scheduled_time": game_time,
            "completion_timestamp": final_scored_at,
            "final_home_score": home_score,
            "final_away_score": away_score,
            "winning_team": winner_team,
            "losing_team": losing_team,
            "tie_indicator": 1 if tied else 0,
            "game_completed": 1 if _normalize_text(payload.get("finalization_status"), "").lower() == "final" or _normalize_text(payload.get("settlement_status"), "").lower() == "settled" else 0,
            "overtime_indicator": _normalize_int(payload.get("overtime_indicator"), 0),
            "postseason_indicator": 0 if season_type in {"", "REG", "REGULAR", "REGULAR_SEASON"} else 1,
            "provider_timestamp": _normalize_text(payload.get("provider_timestamp"), _normalize_text(payload.get("source_snapshot_time"), final_scored_at)),
            "source_market_id": _normalize_text(payload.get("source_market_id"), _normalize_text(payload.get("result_id"), _normalize_text(payload.get("game_id")))),
            "source_selection_id": _normalize_text(payload.get("source_selection_id"), "result"),
            "connector": _normalize_text(source_bundle.get("connector_id"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID),
            "provider": _normalize_text(source_bundle.get("provider"), NFL_RESULTS_RESEARCH_ASSET_SOURCE_ROLE),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_RESULTS_PROVIDER_SOURCE_TYPE),
            "source_key": _normalize_text(source_bundle.get("source_key"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER_SOURCE_ID),
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text(source_bundle.get("connector_name"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text(source_bundle.get("connector_family"), "feeds"),
            "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER_ROLE),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), "deterministic_fixture"),
            "field_provenance": _build_results_field_provenance(
                payload,
                provider_capability=provider_capability,
                source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
                created_at=created_at,
            ),
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "dataset_version": dataset_version,
            "schema_version": NFL_P0_SCHEMA_VERSION,
            "version_id": dataset_version,
            "lineage_version": _normalize_text(dataset_version, NFL_RESULTS_RESEARCH_ASSET_LIFECYCLE_VERSION),
        }
    )
    return payload


def build_nfl_results_research_asset_identity(
    *,
    results_row: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    payload = dict(results_row)
    game_id = _normalize_text(results_row.get("game_id"), _normalize_text(results_row.get("event_id")))
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market=_normalize_text(payload.get("market"), "nfl_p0"),
        league=_normalize_text(payload.get("league"), _normalize_text(profile.metadata.get("league"), "NFL")),
        sport=_normalize_text(payload.get("sport"), _normalize_text(profile.metadata.get("sport"), "football")),
        season=_normalize_text(payload.get("season")),
        week_or_date=_normalize_text(payload.get("week")),
        event_id=_normalize_text(payload.get("event_id"), game_id),
        market_id=_normalize_text(
            payload.get("market_id"),
            _normalize_text(payload.get("result_id"), game_id),
        ),
        selection=_normalize_text(payload.get("selection"), "result"),
        provider=_normalize_text(source_bundle.get("provider"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER),
        connector=_normalize_text(source_bundle.get("connector_id"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_version=_normalize_text(dataset_version, NFL_RESULTS_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Results",
        asset_type="results",
        participant_id="",
        team_id=_normalize_text(
            payload.get("team_id"),
            _normalize_text(payload.get("home_team_id"), _normalize_text(payload.get("home_team"))),
        ),
        game_id=game_id,
        market_type=_normalize_text(payload.get("market_type"), "results"),
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_RESULTS_PROVIDER_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id")),
            "connector_name": _normalize_text(source_bundle.get("connector_name")),
            "connector_family": _normalize_text(source_bundle.get("connector_family")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
            "dataset_version": dataset_version,
            "result_id": _normalize_text(payload.get("result_id")),
            "game_id": game_id,
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
        },
    ).as_dict()


def _build_results_schedule_join_validation(
    *,
    schedule_rows: Sequence[Mapping[str, Any]],
    results_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    schedule_index = {(_normalize_text(row.get("game_id"))): dict(row) for row in schedule_rows if _normalize_text(row.get("game_id"))}
    matched = 0
    mismatches: list[dict[str, Any]] = []
    missing_schedule: list[str] = []
    for row in results_rows:
        game_id = _normalize_text(row.get("game_id"))
        schedule_row = schedule_index.get(game_id)
        if not schedule_row:
            missing_schedule.append(game_id)
            continue
        matched += 1
        if _normalize_text(schedule_row.get("home_team")) != _normalize_text(row.get("home_team")):
            mismatches.append({"game_id": game_id, "field": "home_team"})
        if _normalize_text(schedule_row.get("away_team")) != _normalize_text(row.get("away_team")):
            mismatches.append({"game_id": game_id, "field": "away_team"})
        if _normalize_text(schedule_row.get("kickoff_time")) != _normalize_text(row.get("scheduled_time") or row.get("game_time")):
            mismatches.append({"game_id": game_id, "field": "scheduled_time"})
    ok = not missing_schedule and not mismatches and bool(results_rows)
    return {
        "ok": ok,
        "status": "aligned" if ok else "blocked",
        "matched_rows": matched,
        "missing_schedule_rows": missing_schedule,
        "mismatches": mismatches,
        "result_row_count": len(results_rows),
        "schedule_row_count": len(schedule_rows),
    }


def _latest_certified_asset_row(
    storage: LocalStorageEngine,
    *,
    research_asset_id: str,
) -> dict[str, Any]:
    if not storage.table_exists("historical_research_asset_certifications"):
        return {}
    rows = [
        dict(row)
        for row in storage.fetch(
            "historical_research_asset_certifications",
            where="research_asset_id = ?",
            params=[research_asset_id],
            order_by="certification_id ASC",
        )
    ]
    return rows[-1] if rows else {}


def _promote_results_asset_lifecycle(
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
        notes={"provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER_ROLE)},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="connector_mapped",
        lifecycle_reason=f"connector mapped for {asset_label} research asset",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID),
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
    alignment_status = _normalize_text(
        alignment_result.get("alignment_certification", {}).get("alignment_status")
    )
    if alignment_status != "aligned":
        return
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
        lifecycle_reason=f"{asset_label} rows normalized into the canonical nfl_results storage table",
        alignment_certification=alignment_result["alignment_certification"],
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"normalized_row_count": len(normalized_rows)},
    )
    if _normalize_text(certification_result.get("status")) != "certified":
        return
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
    if _normalize_text(dataset_result.get("certification_status")) != "certified":
        return
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


def build_nfl_results_research_asset_dashboard_snapshot(
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
    join_validation: Mapping[str, Any] | None = None,
    coverage_planner_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    close_storage = True
    try:
        results_rows = [dict(row) for row in normalized_rows or storage.fetch("nfl_results", order_by="result_id ASC")]
        schedule_rows = [
            dict(row)
            for row in storage.fetch("nfl_schedule", order_by="schedule_id ASC")
        ] if storage.table_exists("nfl_schedule") else []
        resolved_join_validation = dict(
            join_validation
            or _build_results_schedule_join_validation(
                schedule_rows=schedule_rows,
                results_rows=results_rows,
            )
        )
        certification_rows = [
            dict(row)
            for row in storage.fetch(
                "historical_research_asset_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID],
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
                params=[DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID],
                order_by="updated_at ASC",
            )
        ] if storage.table_exists("research_asset_lifecycles") else []
        alignment_rows = [
            dict(row)
            for row in storage.fetch(
                "research_asset_alignment_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID],
                order_by="alignment_certification_id ASC",
            )
        ] if storage.table_exists("research_asset_alignment_certifications") else []
        results_validation = dict(validation or validate_nfl_p0_rows("nfl_results", results_rows))
        asset_rows = certification_rows
        asset_status = _normalize_text(asset_rows[-1].get("certification_status"), "missing") if asset_rows else "missing"
        lifecycle_state = _normalize_text(lifecycle_rows[-1].get("lifecycle_state"), "missing") if lifecycle_rows else "missing"
        alignment_status = _normalize_text(alignment_rows[-1].get("alignment_status"), "missing") if alignment_rows else "missing"
        ready = bool(
            results_rows
            and results_validation.get("ok")
            and resolved_join_validation.get("ok")
            and asset_rows
            and asset_status == "certified"
            and dataset_rows
            and _normalize_text(dataset_rows[-1].get("certification_status")) == "certified"
            and lifecycle_state == "feature_ready"
            and alignment_status == "aligned"
        )
        seasons = sorted({str(row.get("season")) for row in results_rows if _normalize_text(row.get("season"))})
        source_summary = {
            "source_name": _normalize_text((certification_result or {}).get("source_name") or (source_bundle or {}).get("source_name") or (fixture or {}).get("source_name"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER),
            "source_type": _normalize_text((certification_result or {}).get("source_type") or (source_bundle or {}).get("source_type") or (fixture or {}).get("source_type"), NFL_RESULTS_PROVIDER_SOURCE_TYPE),
            "source_key": _normalize_text((certification_result or {}).get("source_key") or (source_bundle or {}).get("source_key") or (fixture or {}).get("source_key"), NFL_RESULTS_RESEARCH_ASSET_PROVIDER_SOURCE_ID),
            "provider": _normalize_text((certification_result or {}).get("provider") or (source_bundle or {}).get("provider") or (fixture or {}).get("provider"), NFL_RESULTS_RESEARCH_ASSET_SOURCE_ROLE),
        }
        connector_summary = {
            "connector_id": _normalize_text((source_bundle or {}).get("connector_id"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text((source_bundle or {}).get("connector_name"), NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text((source_bundle or {}).get("connector_family"), "feeds"),
            "execution_mode": _normalize_text((source_bundle or {}).get("execution_mode"), "deterministic_fixture"),
        }
        planner_snapshot = dict(coverage_planner_snapshot or {})
        return {
            "ok": ready,
            "status": "ready" if ready else "partial" if results_rows else "missing",
            "asset_id": DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID,
            "asset_name": "NFL Results",
            "lifecycle_state": lifecycle_state,
            "certification_status": asset_status,
            "dataset_certification_status": _normalize_text(dataset_rows[-1].get("certification_status"), "missing") if dataset_rows else "missing",
            "row_count": len(results_rows),
            "rows_produced": len(results_rows),
            "coverage_seasons": seasons,
            "missing_required_fields": list((results_validation.get("missing_fields") or [])),
            "alignment_failures": list((alignment_rows[-1].get("alignment_failures") or [])) if alignment_rows else [],
            "source_provider_role": source_summary,
            "readiness_percentage": 100.0 if ready else round((1.0 if results_validation.get("ok") else 0.0) * 70.0 + (1.0 if asset_status == "certified" else 0.0) * 15.0 + (1.0 if alignment_status == "aligned" else 0.0) * 15.0, 2),
            "source_bundle": dict(source_bundle or {}),
            "validation": results_validation,
            "research_asset_certifications": certification_rows,
            "dataset_certifications": dataset_rows,
            "research_asset_lifecycles": lifecycle_rows,
            "research_asset_alignment_certifications": alignment_rows,
            "normalized_rows": results_rows,
            "storage": storage.health(),
            "connector_state": connector_summary,
            "coverage_planner_readiness": {
                "first_production_connector_target": _normalize_text(planner_snapshot.get("coverage_gap_engine", {}).get("first_production_connector_target")),
                "missing_required_asset_ids": list(planner_snapshot.get("coverage_gap_engine", {}).get("missing_required_asset_ids", [])),
                "certified_required_asset_ids": list(planner_snapshot.get("coverage_gap_engine", {}).get("certified_required_asset_ids", [])),
            },
            "coverage_planner_snapshot": planner_snapshot,
            "join_validation": resolved_join_validation,
            "warnings": [],
        }
    finally:
        if close_storage:
            storage.close()


def build_nfl_results_research_asset_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    game_count: int = 1,
    dataset_version: str | None = None,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    if profile.profile_id != NFL_RESULTS_RESEARCH_ASSET_PROFILE_ID:
        raise ValueError(f"unexpected market profile: {profile.profile_id}")

    connector_bundle = build_nfl_results_connector_bundle(game_count=game_count, dataset_version=dataset_version)
    fixture = dict(connector_bundle.get("fixture") or {})
    raw_results_rows = [dict(row) for row in connector_bundle.get("results_rows", [])]
    if not raw_results_rows:
        raise ValueError("NFL results connector did not produce any result rows")

    created_at = _normalize_text(connector_bundle.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(connector_bundle.get("dataset_version"), NFL_P0_DATASET_VERSION)
    results_provider_capability = dict(connector_bundle.get("provider_capability") or {})
    source_bundle = dict(connector_bundle.get("source_bundle") or {})
    results_rows = [
        _build_results_asset_row(
            row,
            provider_capability=results_provider_capability,
            source_bundle=source_bundle,
            dataset_version=dataset_version,
            created_at=created_at,
        )
        for row in raw_results_rows
    ]
    source_bundle["field_provenance"] = {
        "nfl_results": _build_results_field_provenance(
            results_rows[0] if results_rows else {},
            provider_capability=results_provider_capability,
            source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
            created_at=created_at,
        )
    }

    storage_path = Path(storage_path or NFL_RESULTS_RESEARCH_ASSET_STORAGE_PATH).expanduser().resolve()
    acquisition_runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path, backend=backend)
    try:
        raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id=profile.profile_id,
            dataset_name=NFL_RESULTS_RAW_ACQUISITION_DATASET_NAME,
        )
    finally:
        acquisition_runtime.close()

    storage_rows = {
        "nfl_results": [dict(row) for row in source_bundle.get("tables", {}).get("nfl_results", raw_results_rows)],
    }
    normalized_results_rows = normalize_nfl_p0_rows(
        "nfl_results",
        storage_rows["nfl_results"],
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    results_validation = validate_nfl_p0_rows("nfl_results", normalized_results_rows)

    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        results_storage_columns = set(storage.table_columns("nfl_results"))
        results_storage_rows = [
            {key: value for key, value in row.items() if key in results_storage_columns}
            for row in normalized_results_rows
        ]
        for row in results_storage_rows:
            storage.upsert("nfl_results", row, key_columns=("result_id",))
    finally:
        storage.close()

    results_asset_rows = [
        _build_results_asset_row(
            row,
            provider_capability=results_provider_capability,
            source_bundle=source_bundle,
            dataset_version=dataset_version,
            created_at=created_at,
        )
        for row in normalized_results_rows
    ]

    asset_contract = ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID,
        research_asset_name="NFL Results",
        asset_category="dataset",
        asset_type="table_snapshot",
        source_table_name="nfl_results",
        required_fields=(
            "result_id",
            "game_id",
            "event_id",
            "season",
            "season_type",
            "week",
            "home_team",
            "away_team",
            "scheduled_time",
            "completion_timestamp",
            "final_score_home",
            "final_score_away",
            "final_home_score",
            "final_away_score",
            "winner_team_id",
            "winner_team",
            "winning_team",
            "losing_team",
            "tie_indicator",
            "game_completed",
            "overtime_indicator",
            "postseason_indicator",
            "game_time",
            "final_scored_at",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "provider_timestamp",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
            "settlement_status",
            "finalization_status",
        ),
        required_timestamps=(
            "game_time",
            "scheduled_time",
            "completion_timestamp",
            "final_scored_at",
            "source_snapshot_time",
            "snapshot_time",
            "created_at",
            "updated_at",
        ),
        point_in_time_rules=(
            "completion_timestamp >= scheduled_time",
            "snapshot_time >= completion_timestamp",
            "source_snapshot_time >= completion_timestamp",
        ),
        description="Settled NFL results row joined to the certified schedule backbone.",
        priority="P0",
        required=True,
        future_asset=False,
        metadata={
            "market_profile": profile.profile_id,
            "market_family": "sports",
            "minimum_schema": True,
            "dataset_role": "results",
            "join_backbone": DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID.replace("results", "schedule"),
        },
    )

    certification_runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path, backend=backend)
    try:
        schedule_rows = [
            dict(row)
            for row in certification_runtime.store.fetch(
                "nfl_schedule",
                order_by="schedule_id ASC",
            )
        ] if certification_runtime.store.table_exists("nfl_schedule") else []
        games_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.nfl.games")
        schedule_cert_row = _latest_certified_asset_row(
            certification_runtime.store,
            research_asset_id="dataset.sports.nfl.schedule",
        )
        join_validation = _build_results_schedule_join_validation(
            schedule_rows=schedule_rows,
            results_rows=results_asset_rows,
        )
        games_certified = _normalize_text(games_cert_row.get("certification_status")) == "certified"
        schedule_certified = _normalize_text(schedule_cert_row.get("certification_status")) == "certified"
        certification_errors = list(results_validation.get("errors") or [])
        if not join_validation["ok"]:
            certification_errors.append("schedule_join_alignment_failed")
        if not games_certified:
            certification_errors.append("games_backbone_not_certified")
        if not schedule_certified:
            certification_errors.append("schedule_backbone_not_certified")
        certification_errors = list(dict.fromkeys(certification_errors))
        certification_validation = {
            **dict(results_validation),
            "ok": not certification_errors,
            "status": "validated" if not certification_errors else "rejected",
            "error_count": len(certification_errors),
            "errors": certification_errors,
            "join_keys": ["game_id", "season", "week", "home_team", "away_team", "scheduled_time"],
            "schedule_join_validation": join_validation,
            "backbone_certification": {
                "dataset.nfl.games": "certified" if games_certified else "missing_or_blocked",
                "dataset.sports.nfl.schedule": "certified" if schedule_certified else "missing_or_blocked",
            },
        }
        results_result = certification_runtime.certify_research_asset(
            asset_contract=asset_contract,
            rows=results_asset_rows,
            profile_id=profile.profile_id,
            validation=certification_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=dataset_version,
            created_at=created_at,
            batch_id=f"{dataset_version}.results.batch.001",
        )
        dataset_asset_rows = [row for row in (games_cert_row, schedule_cert_row, results_result["research_asset_certification"]) if row]
        dataset_row = build_historical_dataset_certification_row(
            profile=profile,
            dataset_version=dataset_version,
            batch_id=f"{dataset_version}.results.batch.001",
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=dataset_asset_rows,
        )
        certification_runtime.store.upsert("historical_certifications", dataset_row, key_columns=("certification_id",))
    finally:
        certification_runtime.close()

    alignment_rows = [dict(row) for row in results_asset_rows]
    for row in alignment_rows:
        row["schema_version"] = RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION
        row["lineage_version"] = dataset_version

    lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path, backend=backend)
    try:
        alignment_results: list[dict[str, Any]] = []
        for row in alignment_rows:
            identity = build_nfl_results_research_asset_identity(
                results_row=row,
                source_bundle=source_bundle,
                dataset_version=dataset_version,
            )
            alignment_results.append(
                lifecycle_runtime.certify_time_entity_alignment(
                    identity=identity,
                    rows=[row],
                    required_fields=asset_contract.required_fields,
                    required_timestamps=asset_contract.required_timestamps,
                    profile=profile,
                    source_bundle=source_bundle,
                    raw_acquisition_result=raw_acquisition_result,
                    created_at=created_at,
                    lifecycle_state="integrity_verified",
                )
            )
        alignment_result = alignment_results[-1] if alignment_results else {}
        _promote_results_asset_lifecycle(
            lifecycle_runtime=lifecycle_runtime,
            identity=build_nfl_results_research_asset_identity(
                results_row=alignment_rows[-1],
                source_bundle=source_bundle,
                dataset_version=dataset_version,
            ),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            normalized_rows=alignment_rows,
            alignment_result=alignment_result,
            certification_result=results_result,
            dataset_result=dataset_row,
            asset_label="NFL results",
            future_joins=["schedule", "odds", "weather", "injuries", "officials", "team_stats", "player_stats", "betting_splits"],
        )
        coverage_planner_snapshot = build_research_asset_coverage_planner_snapshot(storage_path=storage_path, backend=backend, profile_id=profile.profile_id)
        readiness_snapshot = build_nfl_results_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=connector_bundle,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=results_asset_rows,
            validation=certification_validation,
            certification_result=results_result,
            dataset_result=dataset_row,
            lifecycle_result=alignment_result,
            join_validation=join_validation,
            coverage_planner_snapshot=coverage_planner_snapshot,
        )
        return {
            "ok": readiness_snapshot["ok"],
            "status": readiness_snapshot["status"],
            "profile": profile.as_dict(),
            "storage_path": str(storage_path),
            "fixture": connector_bundle,
            "source_bundle": source_bundle,
            "raw_acquisition_result": raw_acquisition_result,
            "normalized_rows": results_asset_rows,
            "validation": certification_validation,
            "research_asset_certification": results_result["research_asset_certification"],
            "dataset_certification": dataset_row,
            "alignment_results": alignment_results,
            "lifecycle_alignment": alignment_result,
            "join_validation": join_validation,
            "coverage_planner_snapshot": coverage_planner_snapshot,
            "readiness_snapshot": readiness_snapshot,
        }
    finally:
        lifecycle_runtime.close()


__all__ = [
    "DEFAULT_NFL_RESULTS_RESEARCH_ASSET_ID",
    "NFL_RESULTS_RAW_ACQUISITION_DATASET_NAME",
    "NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_ID",
    "NFL_RESULTS_RESEARCH_ASSET_CONNECTOR_NAME",
    "NFL_RESULTS_RESEARCH_ASSET_DATASET_NAME",
    "NFL_RESULTS_RESEARCH_ASSET_LIFECYCLE_VERSION",
    "NFL_RESULTS_RESEARCH_ASSET_PROFILE_ID",
    "NFL_RESULTS_RESEARCH_ASSET_PROVIDER",
    "NFL_RESULTS_RESEARCH_ASSET_PROVIDER_ROLE",
    "NFL_RESULTS_RESEARCH_ASSET_STORAGE_PATH",
    "build_nfl_results_research_asset_dashboard_snapshot",
    "build_nfl_results_research_asset_identity",
    "build_nfl_results_research_asset_population",
]
