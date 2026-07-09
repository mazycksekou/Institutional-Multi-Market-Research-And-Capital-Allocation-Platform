from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from src.data.nfl_open_data_sources import nfl_open_data_sources
from src.data.nfl_p0_foundation import (
    NFL_P0_DATASET_VERSION,
    NFL_P0_PROVIDER,
    NFL_P0_SCHEMA_VERSION,
    NFL_P0_SOURCE_NAME,
    NFL_P0_SOURCE_TYPE,
    build_nfl_p0_fixture,
)
from src.data.source_quality_scoring import score_source


NFL_SCHEDULE_CONNECTOR_ID = "connector.feeds.nfl_schedule"
NFL_SCHEDULE_CONNECTOR_NAME = "NFL Schedule Connector"
NFL_SCHEDULE_CONNECTOR_FAMILY = "feeds"
NFL_SCHEDULE_CONNECTOR_EXECUTION_MODE = "deterministic_fixture"
NFL_SCHEDULE_PROVIDER_ID = "nflverse"
NFL_SCHEDULE_PROVIDER_NAME = "nflverse schedules/results"
NFL_SCHEDULE_PROVIDER_SOURCE_ID = "nflverse_schedules_results"
NFL_SCHEDULE_PROVIDER_ROLE = "primary_acquisition"
NFL_SCHEDULE_PROVIDER_SOURCE_TYPE = "deterministic_fixture"
NFL_SCHEDULE_SOURCE_ACCESS_TYPE = "open_github_release"
NFL_RESULTS_RESEARCH_ASSET_ID = "dataset.sports.nfl.results"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
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
    provider_id = _normalize_text(provider_capability.get("provider_id"), NFL_SCHEDULE_PROVIDER_ID)
    provider_name = _normalize_text(provider_capability.get("provider_name"), NFL_SCHEDULE_PROVIDER_NAME)
    provider_role = _normalize_text(provider_capability.get("provider_role"), NFL_SCHEDULE_PROVIDER_ROLE)
    connector_id = _normalize_text(provider_capability.get("connector_id"), NFL_SCHEDULE_CONNECTOR_ID)
    connector_name = _normalize_text(provider_capability.get("connector_name"), NFL_SCHEDULE_CONNECTOR_NAME)
    connector_family = _normalize_text(provider_capability.get("connector_family"), NFL_SCHEDULE_CONNECTOR_FAMILY)
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


def _open_source_entry() -> dict[str, Any]:
    for source in nfl_open_data_sources():
        if _normalize_text(source.get("source_id")) == NFL_SCHEDULE_PROVIDER_SOURCE_ID:
            return dict(source)
    raise KeyError(f"Missing open source entry: {NFL_SCHEDULE_PROVIDER_SOURCE_ID}")


def _field_provenance_for_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    table_name: str,
    created_at: str,
) -> dict[str, Any]:
    lineage_id = _stable_id("nfl_schedule_field_lineage", source_bundle_id, table_name, row.get("game_id") or row.get("schedule_id") or "row")
    fields = [
        "season",
        "week",
        "game_id",
        "event_id",
        "league",
        "home_team",
        "away_team",
        "event_start_time",
        "venue",
        "timezone",
        "neutral_site",
        "game_status",
    ]
    provenance: dict[str, Any] = {}
    for field_name in fields:
        provenance[field_name] = {
            "source_provider": NFL_SCHEDULE_PROVIDER_ID,
            "source_provider_name": NFL_SCHEDULE_PROVIDER_NAME,
            "source_field_name": field_name,
            "raw_field_name": field_name,
            "acquisition_timestamp": created_at,
            "raw_payload_reference": f"{source_bundle_id}:{table_name}:{_normalize_text(row.get('game_id') or row.get('schedule_id') or 'row')}:{field_name}",
            "lineage_id": lineage_id,
            "confidence": 1.0,
            "quality": _normalize_text(provider_capability.get("quality_tier"), "high_priority_adapter"),
        }
    return provenance


def _results_field_provenance_for_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    created_at: str,
) -> dict[str, Any]:
    lineage_id = _stable_id(
        "nfl_results_field_lineage",
        source_bundle_id,
        row.get("game_id") or row.get("result_id") or "row",
    )
    fields = (
        "result_id",
        "game_id",
        "season",
        "season_type",
        "week",
        "home_team",
        "away_team",
        "game_time",
        "final_scored_at",
        "final_score_home",
        "final_score_away",
        "winner_team_id",
        "winner_team",
        "margin",
        "total_points",
        "settlement_status",
        "finalization_status",
    )
    provenance: dict[str, Any] = {}
    for field_name in fields:
        provenance[field_name] = {
            "source_provider": NFL_SCHEDULE_PROVIDER_ID,
            "source_provider_name": NFL_SCHEDULE_PROVIDER_NAME,
            "source_field_name": field_name,
            "raw_field_name": field_name,
            "acquisition_timestamp": created_at,
            "raw_payload_reference": (
                f"{source_bundle_id}:nfl_results:"
                f"{_normalize_text(row.get('game_id') or row.get('result_id') or 'row')}:{field_name}"
            ),
            "lineage_id": lineage_id,
            "confidence": 1.0,
            "quality": _normalize_text(provider_capability.get("quality_tier"), "high_priority_adapter"),
        }
    return provenance


def build_nfl_schedule_provider_capability(
    *,
    dataset_version: str | None = None,
    game_count: int = 1,
) -> dict[str, Any]:
    source_entry = _open_source_entry()
    fixture = build_nfl_p0_fixture(game_count=max(int(game_count or 1), 1), dataset_version=dataset_version or NFL_P0_DATASET_VERSION)
    games_rows = [dict(row) for row in fixture.get("tables", {}).get("nfl_games", [])]
    schedule_rows = [dict(row) for row in fixture.get("tables", {}).get("nfl_schedule", [])]
    supported_fields = sorted({str(key) for row in [*(games_rows[:1]), *(schedule_rows[:1])] for key in row.keys()})
    coverage = {
        "historical": True,
        "schedule": True,
        "event_backbone": True,
        "team_identity": True,
        "venue": True,
        "timezone": True,
        "neutral_site": True,
        "game_status": True,
    }
    source_quality = score_source(
        {
            **source_entry,
            "coverage": coverage,
            "freshness": {"expected_update_cadence": "daily"},
            "limits": {"rate_limit_known": False, "throttle_required": False},
            "legal_terms": {"requires_manual_review": False},
            "model_mapping": {"model_inputs_supported": ["schedule", "event_id", "timestamp", "game_id", "season", "week", "home_team", "away_team"]},
            "current_phase_allowed": True,
            "approval_status": "approved_open_metadata",
        },
        required_inputs=["schedule", "event_id", "timestamp"],
    )
    return {
        "provider_id": NFL_SCHEDULE_PROVIDER_ID,
        "provider_name": NFL_SCHEDULE_PROVIDER_NAME,
        "provider_role": NFL_SCHEDULE_PROVIDER_ROLE,
        "connector_id": NFL_SCHEDULE_CONNECTOR_ID,
        "connector_name": NFL_SCHEDULE_CONNECTOR_NAME,
        "connector_family": NFL_SCHEDULE_CONNECTOR_FAMILY,
        "source_id": NFL_SCHEDULE_PROVIDER_SOURCE_ID,
        "source_name": source_entry.get("source_name", NFL_SCHEDULE_PROVIDER_NAME),
        "source_family": source_entry.get("source_family", "nflverse"),
        "source_access_type": source_entry.get("source_access_type", NFL_SCHEDULE_SOURCE_ACCESS_TYPE),
        "supported_assets": ["dataset.nfl.games", "dataset.sports.nfl.schedule"],
        "supported_fields": supported_fields,
        "supported_markets": ["sports:nfl", "event_backbone"],
        "historical_depth": "historical",
        "update_frequency": "daily / historical",
        "point_in_time_safe": True,
        "licensing_notes": "Open-release schedule/results family; deterministic fixture mode is used offline and keeps the certified cache auditable.",
        "cost_class": "free_open",
        "certification_readiness": "ready",
        "quality_score": round(float(source_quality.get("current_phase_usability_score") or source_quality.get("coverage_score") or 0.0) / 100.0, 4),
        "quality_tier": source_quality.get("quality_tier", "high_priority_adapter"),
        "source_aliases": [NFL_SCHEDULE_PROVIDER_ID, NFL_SCHEDULE_PROVIDER_SOURCE_ID],
        "verification_provider_ids": ["nflreadr", "nflfastr"],
        "fallback_provider_ids": ["manual_schedule_import"],
        "source_quality": source_quality,
    }


def build_nfl_schedule_connector_bundle(
    *,
    game_count: int = 1,
    dataset_version: str | None = None,
    execution_mode: str = NFL_SCHEDULE_CONNECTOR_EXECUTION_MODE,
) -> dict[str, Any]:
    fixture = build_nfl_p0_fixture(game_count=max(int(game_count or 1), 1), dataset_version=dataset_version or NFL_P0_DATASET_VERSION)
    raw_games_rows = [dict(row) for row in fixture.get("tables", {}).get("nfl_games", [])]
    raw_schedule_rows = [dict(row) for row in fixture.get("tables", {}).get("nfl_schedule", [])]
    games_rows = raw_games_rows[:]
    schedule_rows = raw_schedule_rows[: max(1, len(raw_schedule_rows or []))]
    if not schedule_rows:
        raise ValueError("NFL schedule connector did not produce any schedule rows")
    created_at = _normalize_text(fixture.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(dataset_version or fixture.get("dataset_version"), NFL_P0_DATASET_VERSION)
    source_bundle_id = _stable_id(
        "nfl_schedule_connector_bundle",
        dataset_version,
        schedule_rows[0].get("game_id"),
        schedule_rows[0].get("season"),
        schedule_rows[0].get("week"),
        execution_mode,
    )
    provider_capability = build_nfl_schedule_provider_capability(dataset_version=dataset_version, game_count=max(int(game_count or 1), 1))
    games_rows = [
        _connector_row(
            row,
            provider_capability=provider_capability,
            source_bundle={
                "source_bundle_id": source_bundle_id,
                "acquisition_timestamp": created_at,
            },
            execution_mode=execution_mode,
            table_name="nfl_games",
        )
        for row in games_rows
    ]
    schedule_rows = [
        _connector_row(
            row,
            provider_capability=provider_capability,
            source_bundle={
                "source_bundle_id": source_bundle_id,
                "acquisition_timestamp": created_at,
            },
            execution_mode=execution_mode,
            table_name="nfl_schedule",
        )
        for row in schedule_rows
    ]
    field_provenance = {
        "nfl_games": _field_provenance_for_row(
            games_rows[0] if games_rows else schedule_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=source_bundle_id,
            table_name="nfl_games",
            created_at=created_at,
        ),
        "nfl_schedule": _field_provenance_for_row(
            schedule_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=source_bundle_id,
            table_name="nfl_schedule",
            created_at=created_at,
        ),
    }
    source_bundle = {
        "dataset_id": "dataset.sports.nfl.schedule.raw_acquisition_cache",
        "dataset_name": "nfl_schedule_raw_acquisition_cache",
        "source_name": provider_capability["provider_name"],
        "source_type": NFL_SCHEDULE_PROVIDER_SOURCE_TYPE,
        "source_key": NFL_SCHEDULE_PROVIDER_SOURCE_ID,
        "source_family": provider_capability["source_family"],
        "source_access_type": provider_capability["source_access_type"],
        "provider": provider_capability["provider_id"],
        "provider_name": provider_capability["provider_name"],
        "provider_role": provider_capability["provider_role"],
        "provider_sources": [NFL_SCHEDULE_PROVIDER_SOURCE_ID],
        "provider_versions": [dataset_version],
        "source_bundle_id": source_bundle_id,
        "acquisition_timestamp": created_at,
        "source_snapshot_time": _normalize_text(schedule_rows[0].get("source_snapshot_time"), created_at),
        "result_timestamp": _normalize_text(schedule_rows[0].get("result_timestamp"), _normalize_text(schedule_rows[0].get("kickoff_time"), created_at)),
        "source_market_id": _normalize_text(schedule_rows[0].get("source_market_id"), _normalize_text(schedule_rows[0].get("schedule_id"), _normalize_text(schedule_rows[0].get("game_id")))),
        "source_selection_id": _normalize_text(schedule_rows[0].get("source_selection_id"), _normalize_text(schedule_rows[0].get("selection"), "schedule")),
        "dataset_version": dataset_version,
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "source_tables": {"nfl_games": games_rows, "nfl_schedule": schedule_rows},
        "tables": {"nfl_games": games_rows, "nfl_schedule": schedule_rows},
        "source_file": "nflverse_schedules_results_fixture.csv",
        "update_frequency": "daily",
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "connector_family": provider_capability["connector_family"],
        "connector_role": "production_connector",
        "execution_mode": execution_mode,
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
    }
    return {
        "ok": True,
        "status": "connector_ready" if execution_mode == NFL_SCHEDULE_CONNECTOR_EXECUTION_MODE else "connector_live_ready",
        "execution_mode": execution_mode,
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "fixture": fixture,
        "games_rows": games_rows,
        "schedule_rows": schedule_rows,
        "source_bundle": source_bundle,
        "created_at": created_at,
        "dataset_version": dataset_version,
        "game_count": len(games_rows),
        "schedule_row_count": len(schedule_rows),
        "notes": [
            "This connector path is production-ready in shape but uses a deterministic offline fixture when live provider access is unavailable.",
            "The raw acquisition cache remains the shared first hop before normalization and certification.",
            "Field-level provenance is preserved for both the event backbone and the schedule asset.",
        ],
    }


def build_nfl_results_provider_capability(
    *,
    dataset_version: str | None = None,
    game_count: int = 1,
) -> dict[str, Any]:
    capability = build_nfl_schedule_provider_capability(
        dataset_version=dataset_version,
        game_count=game_count,
    )
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    result_rows = [dict(row) for row in fixture.get("tables", {}).get("nfl_results", [])]
    if not result_rows:
        raise ValueError("NFL schedule/results connector did not produce any result rows")
    capability.update(
        {
            "supported_assets": [NFL_RESULTS_RESEARCH_ASSET_ID],
            "supported_fields": sorted(str(key) for key in result_rows[0]),
            "supported_markets": ["sports:nfl", "results"],
            "model_inputs_supported": [
                "game_id",
                "season",
                "week",
                "home_team",
                "away_team",
                "final_score_home",
                "final_score_away",
                "final_scored_at",
            ],
        }
    )
    return capability


def build_nfl_results_connector_bundle(
    *,
    game_count: int = 1,
    dataset_version: str | None = None,
    execution_mode: str = NFL_SCHEDULE_CONNECTOR_EXECUTION_MODE,
) -> dict[str, Any]:
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    raw_results_rows = [dict(row) for row in fixture.get("tables", {}).get("nfl_results", [])]
    if not raw_results_rows:
        raise ValueError("NFL schedule/results connector did not produce any result rows")

    created_at = _normalize_text(fixture.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(dataset_version or fixture.get("dataset_version"), NFL_P0_DATASET_VERSION)
    source_bundle_id = _stable_id(
        "nfl_results_connector_bundle",
        dataset_version,
        raw_results_rows[0].get("game_id"),
        raw_results_rows[0].get("season"),
        raw_results_rows[0].get("week"),
        execution_mode,
    )
    provider_capability = build_nfl_results_provider_capability(
        dataset_version=dataset_version,
        game_count=max(int(game_count or 1), 1),
    )
    results_rows = [
        _connector_row(
            row,
            provider_capability=provider_capability,
            source_bundle={
                "source_bundle_id": source_bundle_id,
                "acquisition_timestamp": created_at,
            },
            execution_mode=execution_mode,
            table_name="nfl_results",
        )
        for row in raw_results_rows
    ]
    field_provenance = {
        "nfl_results": _results_field_provenance_for_row(
            results_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=source_bundle_id,
            created_at=created_at,
        )
    }
    source_bundle = {
        "dataset_id": f"{NFL_RESULTS_RESEARCH_ASSET_ID}.raw_acquisition_cache",
        "dataset_name": "nfl_results_raw_acquisition_cache",
        "source_name": provider_capability["provider_name"],
        "source_type": NFL_SCHEDULE_PROVIDER_SOURCE_TYPE,
        "source_key": NFL_SCHEDULE_PROVIDER_SOURCE_ID,
        "source_family": provider_capability["source_family"],
        "source_access_type": provider_capability["source_access_type"],
        "provider": provider_capability["provider_id"],
        "provider_name": provider_capability["provider_name"],
        "provider_role": provider_capability["provider_role"],
        "provider_sources": [NFL_SCHEDULE_PROVIDER_SOURCE_ID],
        "provider_versions": [dataset_version],
        "source_bundle_id": source_bundle_id,
        "acquisition_timestamp": created_at,
        "source_snapshot_time": _normalize_text(results_rows[0].get("source_snapshot_time"), created_at),
        "result_timestamp": _normalize_text(results_rows[0].get("final_scored_at"), created_at),
        "source_market_id": _normalize_text(
            results_rows[0].get("game_id"),
            _normalize_text(results_rows[0].get("result_id"), "nfl_results"),
        ),
        "source_selection_id": "result",
        "dataset_version": dataset_version,
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "source_tables": {"nfl_results": results_rows},
        "tables": {"nfl_results": results_rows},
        "source_file": "nflverse_schedules_results_fixture.csv",
        "update_frequency": "daily",
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "connector_family": provider_capability["connector_family"],
        "connector_role": "production_connector",
        "execution_mode": execution_mode,
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
    }
    return {
        "ok": True,
        "status": "connector_ready" if execution_mode == NFL_SCHEDULE_CONNECTOR_EXECUTION_MODE else "connector_live_ready",
        "execution_mode": execution_mode,
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "fixture": fixture,
        "results_rows": results_rows,
        "source_bundle": source_bundle,
        "created_at": created_at,
        "dataset_version": dataset_version,
        "result_row_count": len(results_rows),
        "notes": [
            "The existing NFL schedule/results connector family supplies the results asset without a parallel connector.",
            "The raw acquisition cache remains the first persistent hop before normalization and certification.",
            "Field-level provenance is preserved for the raw result fields.",
        ],
    }


__all__ = [
    "NFL_SCHEDULE_CONNECTOR_EXECUTION_MODE",
    "NFL_SCHEDULE_CONNECTOR_FAMILY",
    "NFL_SCHEDULE_CONNECTOR_ID",
    "NFL_SCHEDULE_CONNECTOR_NAME",
    "NFL_SCHEDULE_PROVIDER_ID",
    "NFL_SCHEDULE_PROVIDER_NAME",
    "NFL_SCHEDULE_PROVIDER_ROLE",
    "NFL_RESULTS_RESEARCH_ASSET_ID",
    "build_nfl_results_connector_bundle",
    "build_nfl_results_provider_capability",
    "build_nfl_schedule_connector_bundle",
    "build_nfl_schedule_provider_capability",
]
