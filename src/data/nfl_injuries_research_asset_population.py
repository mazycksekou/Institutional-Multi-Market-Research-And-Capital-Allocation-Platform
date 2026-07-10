from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    NFL_P0_TABLE_CONTRACTS,
    build_nfl_p0_fixture,
    create_nfl_p0_storage_engine,
    get_nfl_p0_market_profile,
    normalize_nfl_p0_rows,
    validate_nfl_p0_rows,
)
from src.data.research_asset_lifecycle_runtime import (
    RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
    ResearchAssetIdentityContract,
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
    build_time_entity_alignment_certification,
    build_time_entity_alignment_certification_row,
    validate_time_entity_alignment_certification_row,
)
from src.data.source_quality_scoring import score_source
from src.market_intelligence.research_asset_coverage_planner import (
    build_research_asset_coverage_planner_snapshot,
)
from src.storage.local_store import LocalStorageEngine


DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID = "dataset.nfl.injury_snapshots"
NFL_INJURIES_RESEARCH_ASSET_STORAGE_PATH = get_runtime_data_path(
    "nfl_injuries_research_asset",
    "canonical_data.sqlite",
)
NFL_INJURIES_RESEARCH_ASSET_DATASET_NAME = "nfl_injuries_research_asset"
NFL_INJURIES_RAW_ACQUISITION_DATASET_NAME = "nfl_injuries_raw_acquisition_cache"
NFL_INJURIES_RESEARCH_ASSET_PROVIDER = "nflverse_injuries"
NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME = "nflverse injuries"
NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE = "primary_acquisition"
NFL_INJURIES_RESEARCH_ASSET_SOURCE_ROLE = NFL_INJURIES_RESEARCH_ASSET_PROVIDER
NFL_INJURIES_PROVIDER_SOURCE_TYPE = "injury_fixture"
NFL_INJURIES_RESEARCH_ASSET_PROFILE_ID = "sports:nfl"
NFL_INJURIES_RESEARCH_ASSET_LIFECYCLE_VERSION = "v1"
NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID = "connector.feeds.nfl_injuries"
NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_NAME = "NFL Injuries Connector"
NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY = "feeds"
NFL_INJURIES_CONNECTOR_EXECUTION_MODE = "deterministic_fixture"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        result = float(value)
        if result != result or result in {float("inf"), float("-inf")}:
            return float(default)
        return result
    except (TypeError, ValueError):
        return float(default)


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _injury_rows(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    tables = fixture.get("tables") or {}
    if not isinstance(tables, Mapping):
        return []
    rows = tables.get("nfl_injury_snapshots") or []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _field_provenance_for_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    created_at: str,
) -> dict[str, Any]:
    source_provider = _normalize_text(provider_capability.get("provider_id"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER)
    source_provider_name = _normalize_text(provider_capability.get("provider_name"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME)
    quality = _normalize_text(provider_capability.get("quality_tier"), "high_priority_adapter")
    row_id = _normalize_text(row.get("injury_snapshot_id") or row.get("player_id") or row.get("game_id") or "row")
    lineage_id = _stable_id("nfl_injury_field_lineage", source_bundle_id, row_id)
    field_map = {
        "injury_snapshot_id": "injury_snapshot_id",
        "game_id": "game_id",
        "event_id": "game_id",
        "season": "season",
        "week": "week",
        "league": "league",
        "sport": "sport",
        "team_id": "team_id",
        "team_name": "team_name",
        "opponent_team_id": "opponent_team_id",
        "home_team": "home_team",
        "away_team": "away_team",
        "player_id": "player_id",
        "player_name": "player_name",
        "position": "position",
        "report_status": "report_status",
        "availability_status": "availability_status",
        "practice_status": "practice_status",
        "report_primary_injury": "report_primary_injury",
        "injury_category": "injury_category",
        "report_time": "report_time",
        "timing_confidence": "timing_confidence",
        "report_source": "report_source",
        "kickoff_time": "kickoff_time",
        "source_name": "source_name",
        "source_type": "source_type",
        "source_key": "source_key",
        "provider": "provider",
        "provider_role": "provider_role",
        "connector_id": "connector_id",
        "connector_name": "connector_name",
        "connector_family": "connector_family",
        "execution_mode": "execution_mode",
        "source_snapshot_time": "source_snapshot_time",
        "snapshot_time": "snapshot_time",
        "decision_time": "decision_time",
        "source_market_id": "source_market_id",
        "source_selection_id": "source_selection_id",
        "dataset_version": "dataset_version",
        "schema_version": "schema_version",
        "status": "status",
        "quality_score": "quality_score",
        "completeness_score": "completeness_score",
        "market_type": "market_type",
    }
    provenance: dict[str, Any] = {}
    for field_name, source_field_name in field_map.items():
        confidence = 0.98 if source_field_name == "availability_status" else 1.0
        provenance[field_name] = {
            "source_provider": source_provider,
            "source_provider_name": source_provider_name,
            "source_field_name": source_field_name,
            "raw_field_name": source_field_name,
            "acquisition_timestamp": created_at,
            "raw_payload_reference": f"{source_bundle_id}:nfl_injury_snapshots:{row_id}:{source_field_name}",
            "lineage_id": lineage_id,
            "confidence": confidence,
            "quality": quality,
        }
    return provenance


def build_nfl_injuries_provider_capability(
    *,
    dataset_version: str | None = None,
    game_count: int = 1,
) -> dict[str, Any]:
    source_entry = {
        "source_id": NFL_INJURIES_RESEARCH_ASSET_PROVIDER,
        "source_name": NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME,
        "source_family": NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY,
        "source_category": "injuries",
        "source_access_type": "open_dataset",
        "coverage": {
            "historical": True,
            "injuries": True,
            "player_availability": True,
            "point_in_time_injury_reports": True,
            "manual_evidence_supported": True,
        },
        "freshness": {"expected_update_cadence": "daily"},
        "limits": {"rate_limit_known": False, "throttle_required": False},
        "legal_terms": {"requires_manual_review": False},
        "model_mapping": {
            "model_inputs_supported": [
                "game_id",
                "team_id",
                "player_id",
                "report_status",
                "availability_status",
                "practice_status",
                "report_time",
                "source_snapshot_time",
                "snapshot_time",
                "decision_time",
            ],
            "historical_backfill_fields_available": [
                "report_status",
                "availability_status",
                "practice_status",
                "report_primary_injury",
            ],
            "outcome_fields_available": [],
            "join_keys": ["game_id", "team_id", "player_id", "report_time", "snapshot_time"],
        },
        "current_phase_allowed": True,
        "approval_status": "approved_open_metadata",
        "source_aliases": [
            NFL_INJURIES_RESEARCH_ASSET_PROVIDER,
            "manual_import",
            "official_team_reports",
            "official_team_press_releases",
            "official_nfl_staff_or_news_pages",
        ],
    }
    source_quality = score_source(
        source_entry,
        required_inputs=[
            "game_id",
            "team_id",
            "player_id",
            "report_status",
            "report_time",
            "snapshot_time",
            "decision_time",
        ],
    )
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    injury_rows = _injury_rows(fixture)
    if not injury_rows:
        raise ValueError("NFL injuries connector did not produce any injury rows")
    supported_fields = sorted(set(injury_rows[0].keys()))
    return {
        "provider_id": NFL_INJURIES_RESEARCH_ASSET_PROVIDER,
        "provider_name": NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME,
        "provider_role": NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE,
        "connector_id": NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID,
        "connector_name": NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_NAME,
        "connector_family": NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY,
        "source_id": NFL_INJURIES_RESEARCH_ASSET_PROVIDER,
        "source_name": NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME,
        "source_family": NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY,
        "source_access_type": "open_dataset",
        "supported_assets": [DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID],
        "supported_fields": supported_fields,
        "supported_markets": ["sports:nfl", "injury_snapshot", "pregame_injury_report"],
        "historical_depth": "historical",
        "update_frequency": "daily / historical",
        "point_in_time_safe": True,
        "licensing_notes": "Fixture-backed local mode preserves the canonical open nflverse injuries path while retaining a manual evidence fallback for report-time review.",
        "cost_class": "open_dataset",
        "certification_readiness": "ready",
        "quality_score": round(float(source_quality.get("current_phase_usability_score") or source_quality.get("coverage_score") or 0.0) / 100.0, 4),
        "quality_tier": source_quality.get("quality_tier", "high_priority_adapter"),
        "source_aliases": source_entry["source_aliases"],
        "verification_provider_ids": ["official_team_reports", "official_team_press_releases"],
        "fallback_provider_ids": ["manual_import", "official_nfl_staff_or_news_pages"],
        "source_quality": source_quality,
        "evidence_role": "pregame_injury_report",
        "manual_evidence_supported": True,
    }


def _connector_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    execution_mode: str,
) -> dict[str, Any]:
    payload = dict(row)
    provider_id = _normalize_text(provider_capability.get("provider_id"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER)
    provider_name = _normalize_text(provider_capability.get("provider_name"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME)
    provider_role = _normalize_text(provider_capability.get("provider_role"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE)
    connector_id = _normalize_text(provider_capability.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID)
    connector_name = _normalize_text(provider_capability.get("connector_name"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_NAME)
    connector_family = _normalize_text(provider_capability.get("connector_family"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY)
    payload.update(
        {
            "source_name": provider_name,
            "source_type": NFL_INJURIES_PROVIDER_SOURCE_TYPE,
            "source_key": NFL_INJURIES_RESEARCH_ASSET_PROVIDER,
            "provider": provider_id,
            "provider_name": provider_name,
            "provider_role": provider_role,
            "connector_id": connector_id,
            "connector_name": connector_name,
            "connector_family": connector_family,
            "connector_role": "production_connector",
            "execution_mode": execution_mode,
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_table": "nfl_injury_snapshots",
            "acquisition_timestamp": _normalize_text(source_bundle.get("acquisition_timestamp"), _utc_now_iso()),
            "provider_capability": dict(provider_capability),
        }
    )
    return payload


def build_nfl_injuries_connector_bundle(
    *,
    game_count: int = 1,
    dataset_version: str | None = None,
    execution_mode: str = NFL_INJURIES_CONNECTOR_EXECUTION_MODE,
) -> dict[str, Any]:
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    raw_injury_rows = _injury_rows(fixture)
    if not raw_injury_rows:
        raise ValueError("NFL injuries connector did not produce any injury rows")

    created_at = _normalize_text(fixture.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(dataset_version or fixture.get("dataset_version"), NFL_P0_DATASET_VERSION)
    source_bundle_id = _stable_id(
        "nfl_injuries_connector_bundle",
        dataset_version,
        raw_injury_rows[0].get("game_id"),
        raw_injury_rows[0].get("season"),
        raw_injury_rows[0].get("week"),
        execution_mode,
    )
    provider_capability = build_nfl_injuries_provider_capability(
        dataset_version=dataset_version,
        game_count=max(int(game_count or 1), 1),
    )
    injury_rows = [
        _connector_row(
            row,
            provider_capability=provider_capability,
            source_bundle={
                "source_bundle_id": source_bundle_id,
                "acquisition_timestamp": created_at,
            },
            execution_mode=execution_mode,
        )
        for row in raw_injury_rows
    ]
    field_provenance = {
        "nfl_injury_snapshots": _field_provenance_for_row(
            injury_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=source_bundle_id,
            created_at=created_at,
        )
    }
    source_bundle = {
        "dataset_id": f"{DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID}.raw_acquisition_cache",
        "dataset_name": NFL_INJURIES_RAW_ACQUISITION_DATASET_NAME,
        "source_name": provider_capability["provider_name"],
        "source_type": NFL_INJURIES_PROVIDER_SOURCE_TYPE,
        "source_key": NFL_INJURIES_RESEARCH_ASSET_PROVIDER,
        "source_family": provider_capability["source_family"],
        "source_access_type": "open_dataset",
        "provider": provider_capability["provider_id"],
        "provider_name": provider_capability["provider_name"],
        "provider_role": provider_capability["provider_role"],
        "provider_sources": [provider_capability["provider_id"], "manual_import"],
        "provider_versions": [dataset_version],
        "source_bundle_id": source_bundle_id,
        "acquisition_timestamp": created_at,
        "source_snapshot_time": _normalize_text(injury_rows[0].get("source_snapshot_time"), created_at),
        "result_timestamp": _normalize_text(injury_rows[0].get("decision_time"), _normalize_text(injury_rows[0].get("snapshot_time"), created_at)),
        "source_market_id": _normalize_text(injury_rows[0].get("game_id"), _normalize_text(injury_rows[0].get("injury_snapshot_id"), "nfl_injury")),
        "source_selection_id": _normalize_text(injury_rows[0].get("player_id"), "injury"),
        "dataset_version": dataset_version,
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "source_tables": {"nfl_injury_snapshots": injury_rows},
        "tables": {"nfl_injury_snapshots": injury_rows},
        "source_file": "nflverse_injuries_fixture.json",
        "update_frequency": "daily",
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "connector_family": provider_capability["connector_family"],
        "connector_role": "production_connector",
        "execution_mode": execution_mode,
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "evidence_role": "pregame_injury_report",
        "manual_evidence_paths": ["manual_import", "official_team_reports", "official_team_press_releases"],
    }
    return {
        "ok": True,
        "status": "connector_ready" if execution_mode == NFL_INJURIES_CONNECTOR_EXECUTION_MODE else "connector_live_ready",
        "execution_mode": execution_mode,
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "fixture": fixture,
        "injury_rows": injury_rows,
        "source_bundle": source_bundle,
        "created_at": created_at,
        "dataset_version": dataset_version,
        "injury_row_count": len(injury_rows),
        "notes": [
            "The injuries connector path stays local-first and deterministic while preserving the canonical open nflverse injuries acquisition route.",
            "Manual evidence remains a documented fallback for report-time review and terms-sensitive cases.",
            "Field-level provenance is preserved for player, team, status, and report timing fields.",
        ],
    }


def _build_injury_asset_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
    created_at: str,
) -> dict[str, Any]:
    payload = dict(row)
    game_id = _normalize_text(payload.get("game_id"), _normalize_text(payload.get("event_id")))
    kickoff_time = _normalize_text(payload.get("kickoff_time"), _normalize_text(payload.get("scheduled_time")))
    injury_snapshot_id = _normalize_text(payload.get("injury_snapshot_id"), _stable_id("nfl_injury_snapshot", game_id, payload.get("team_id"), payload.get("player_id"), payload.get("report_time"), kickoff_time))
    player_id = _normalize_text(payload.get("player_id"))
    report_status = _normalize_text(payload.get("report_status"))
    payload.update(
        {
            "asset_id": DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
            "asset_family": "dataset",
            "asset_name": "NFL Injury Snapshots",
            "asset_type": "injury_snapshot",
            "market_profile": NFL_INJURIES_RESEARCH_ASSET_PROFILE_ID,
            "league": _normalize_text(payload.get("league"), "NFL"),
            "sport": "football",
            "event_id": _normalize_text(payload.get("event_id"), game_id),
            "market_id": injury_snapshot_id,
            "selection": player_id or report_status or "injury",
            "participant_id": player_id,
            "scheduled_time": kickoff_time,
            "completion_timestamp": _normalize_text(payload.get("completion_timestamp"), kickoff_time),
            "provider_timestamp": _normalize_text(payload.get("provider_timestamp"), _normalize_text(payload.get("source_snapshot_time"), _normalize_text(payload.get("report_time"), kickoff_time))),
            "source_market_id": _normalize_text(payload.get("source_market_id"), injury_snapshot_id),
            "source_selection_id": _normalize_text(payload.get("source_selection_id"), player_id or report_status or "injury"),
            "connector": _normalize_text(source_bundle.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID),
            "provider": _normalize_text(source_bundle.get("provider"), NFL_INJURIES_RESEARCH_ASSET_SOURCE_ROLE),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_INJURIES_PROVIDER_SOURCE_TYPE),
            "source_key": _normalize_text(source_bundle.get("source_key"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER),
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text(source_bundle.get("connector_name"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text(source_bundle.get("connector_family"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY),
            "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_INJURIES_CONNECTOR_EXECUTION_MODE),
            "evidence_role": "pregame_injury_report",
            "field_provenance": _field_provenance_for_row(
                payload,
                provider_capability=provider_capability,
                source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
                created_at=created_at,
            ),
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "dataset_version": dataset_version,
            "schema_version": NFL_P0_SCHEMA_VERSION,
            "version_id": dataset_version,
            "lineage_version": _normalize_text(dataset_version, NFL_INJURIES_RESEARCH_ASSET_LIFECYCLE_VERSION),
        }
    )
    return payload


def _build_injury_schedule_results_odds_weather_join_validation(
    *,
    schedule_rows: Sequence[Mapping[str, Any]],
    results_rows: Sequence[Mapping[str, Any]],
    odds_rows: Sequence[Mapping[str, Any]],
    weather_rows: Sequence[Mapping[str, Any]],
    injury_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    schedule_index = {_normalize_text(row.get("game_id")): dict(row) for row in schedule_rows if _normalize_text(row.get("game_id"))}
    results_index = {_normalize_text(row.get("game_id")): dict(row) for row in results_rows if _normalize_text(row.get("game_id"))}
    weather_index = {_normalize_text(row.get("game_id")): dict(row) for row in weather_rows if _normalize_text(row.get("game_id"))}
    odds_index: dict[str, list[dict[str, Any]]] = {}
    for row in odds_rows:
        game_id = _normalize_text(row.get("game_id"))
        if not game_id:
            continue
        odds_index.setdefault(game_id, []).append(dict(row))

    missing_schedule_rows: list[str] = []
    missing_results_rows: list[str] = []
    missing_odds_rows: list[str] = []
    missing_weather_rows: list[str] = []
    orphaned_injury_rows: list[str] = []
    post_decision_injury_rows: list[str] = []
    team_mismatches: list[dict[str, Any]] = []
    timing_issues: list[dict[str, Any]] = []
    matched_rows = 0

    for row in injury_rows:
        injury_snapshot_id = _normalize_text(row.get("injury_snapshot_id"))
        game_id = _normalize_text(row.get("game_id"))
        schedule_row = schedule_index.get(game_id)
        results_row = results_index.get(game_id)
        weather_row = weather_index.get(game_id)
        odds_for_game = odds_index.get(game_id, [])

        missing_backbone = False
        if not schedule_row:
            missing_schedule_rows.append(game_id)
            missing_backbone = True
        if not results_row:
            missing_results_rows.append(game_id)
            missing_backbone = True
        if not odds_for_game:
            missing_odds_rows.append(game_id)
            missing_backbone = True
        if not weather_row:
            missing_weather_rows.append(game_id)
            missing_backbone = True
        if missing_backbone:
            orphaned_injury_rows.append(injury_snapshot_id or game_id)
            continue

        matched_rows += 1
        schedule_teams = {
            _normalize_text(schedule_row.get("home_team_id")),
            _normalize_text(schedule_row.get("away_team_id")),
            _normalize_text(schedule_row.get("home_team")),
            _normalize_text(schedule_row.get("away_team")),
        }
        team_id = _normalize_text(row.get("team_id"))
        team_name = _normalize_text(row.get("team_name"))
        if team_id and team_id not in schedule_teams:
            team_mismatches.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "team_id"})
        if team_name and team_name not in schedule_teams:
            team_mismatches.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "team_name"})
        if _normalize_text(results_row.get("home_team")) != _normalize_text(schedule_row.get("home_team")):
            team_mismatches.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "results_home_team"})
        if _normalize_text(results_row.get("away_team")) != _normalize_text(schedule_row.get("away_team")):
            team_mismatches.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "results_away_team"})
        if _normalize_text(weather_row.get("home_team")) != _normalize_text(schedule_row.get("home_team")):
            team_mismatches.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "weather_home_team"})
        if _normalize_text(weather_row.get("away_team")) != _normalize_text(schedule_row.get("away_team")):
            team_mismatches.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "weather_away_team"})

        kickoff_time = _parse_iso(schedule_row.get("kickoff_time") or row.get("kickoff_time"))
        report_time = _parse_iso(row.get("report_time"))
        source_snapshot_time = _parse_iso(row.get("source_snapshot_time") or row.get("snapshot_time"))
        snapshot_time = _parse_iso(row.get("snapshot_time") or row.get("source_snapshot_time"))
        decision_time = _parse_iso(row.get("decision_time") or row.get("snapshot_time"))

        if kickoff_time is None:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "kickoff_time", "reason": "missing_kickoff_time"})
        if report_time is None:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "report_time", "reason": "missing_report_time"})
        if source_snapshot_time is None:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "source_snapshot_time", "reason": "missing_source_snapshot_time"})
        if snapshot_time is None:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "snapshot_time", "reason": "missing_snapshot_time"})
        if decision_time is None:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "decision_time", "reason": "missing_decision_time"})
        if any(item is None for item in (kickoff_time, report_time, source_snapshot_time, snapshot_time, decision_time)):
            continue

        if report_time > source_snapshot_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "report_time", "reason": "report_time_after_source_snapshot"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if source_snapshot_time > snapshot_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "source_snapshot_time", "reason": "source_snapshot_after_snapshot_time"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if report_time > decision_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "report_time", "reason": "report_time_after_decision"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if source_snapshot_time > decision_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "source_snapshot_time", "reason": "source_snapshot_after_decision"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if snapshot_time > decision_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "snapshot_time", "reason": "snapshot_after_decision"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if decision_time > kickoff_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "decision_time", "reason": "decision_time_after_kickoff"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if report_time > kickoff_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "report_time", "reason": "report_time_after_kickoff"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if source_snapshot_time > kickoff_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "source_snapshot_time", "reason": "source_snapshot_after_kickoff"})
            post_decision_injury_rows.append(injury_snapshot_id)
        if snapshot_time > kickoff_time:
            timing_issues.append({"injury_snapshot_id": injury_snapshot_id, "game_id": game_id, "field": "snapshot_time", "reason": "snapshot_after_kickoff"})
            post_decision_injury_rows.append(injury_snapshot_id)

    ok = bool(injury_rows) and not missing_schedule_rows and not missing_results_rows and not missing_odds_rows and not missing_weather_rows and not team_mismatches and not timing_issues
    return {
        "ok": ok,
        "status": "aligned" if ok else "blocked",
        "matched_rows": matched_rows,
        "missing_schedule_rows": sorted(set(filter(None, missing_schedule_rows))),
        "missing_results_rows": sorted(set(filter(None, missing_results_rows))),
        "missing_odds_rows": sorted(set(filter(None, missing_odds_rows))),
        "missing_weather_rows": sorted(set(filter(None, missing_weather_rows))),
        "orphaned_injury_rows": sorted(set(filter(None, orphaned_injury_rows))),
        "post_decision_injury_rows": sorted(set(filter(None, post_decision_injury_rows))),
        "team_mismatches": team_mismatches,
        "timing_issues": timing_issues,
        "injury_row_count": len(injury_rows),
        "schedule_row_count": len(schedule_rows),
        "results_row_count": len(results_rows),
        "odds_row_count": len(odds_rows),
        "weather_row_count": len(weather_rows),
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


def build_nfl_injuries_research_asset_identity(
    *,
    injury_row: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    payload = dict(injury_row)
    game_id = _normalize_text(payload.get("game_id"), _normalize_text(payload.get("event_id")))
    player_id = _normalize_text(payload.get("player_id"))
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market="nfl_p0",
        league=_normalize_text(payload.get("league"), _normalize_text(profile.metadata.get("league"), "NFL")),
        sport=_normalize_text(payload.get("sport"), _normalize_text(profile.metadata.get("sport"), "football")),
        season=_normalize_text(payload.get("season")),
        week_or_date=_normalize_text(payload.get("week")),
        event_id=_normalize_text(payload.get("event_id"), game_id),
        market_id=_normalize_text(payload.get("market_id"), _normalize_text(payload.get("injury_snapshot_id"), game_id)),
        selection=_normalize_text(payload.get("selection"), "injury_snapshot"),
        provider=_normalize_text(source_bundle.get("provider"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER),
        connector=_normalize_text(source_bundle.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_version=_normalize_text(dataset_version, NFL_INJURIES_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Injury Snapshots",
        asset_type="injury_snapshot",
        participant_id=player_id,
        team_id=_normalize_text(payload.get("team_id")),
        game_id=game_id,
        market_type=_normalize_text(payload.get("market_type"), "injury_snapshot"),
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_INJURIES_PROVIDER_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id")),
            "connector_name": _normalize_text(source_bundle.get("connector_name")),
            "connector_family": _normalize_text(source_bundle.get("connector_family")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
            "dataset_version": dataset_version,
            "injury_snapshot_id": _normalize_text(payload.get("injury_snapshot_id")),
            "game_id": game_id,
            "player_id": player_id,
            "team_id": _normalize_text(payload.get("team_id")),
            "report_time": _normalize_text(payload.get("report_time")),
            "report_source": _normalize_text(payload.get("report_source")),
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
            "evidence_role": "pregame_injury_report",
        },
    ).as_dict()


def build_nfl_injuries_dataset_identity(
    *,
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market="nfl_p0",
        league=_normalize_text(source_bundle.get("league"), _normalize_text(profile.metadata.get("league"), "NFL")),
        sport=_normalize_text(source_bundle.get("sport"), _normalize_text(profile.metadata.get("sport"), "football")),
        season="",
        week_or_date="",
        event_id="",
        market_id=DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
        selection="injury_snapshot",
        provider=_normalize_text(source_bundle.get("provider"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER),
        connector=_normalize_text(source_bundle.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_version=_normalize_text(dataset_version, NFL_INJURIES_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Injury Snapshots",
        asset_type="injury_snapshot",
        participant_id="",
        team_id="",
        game_id="",
        market_type="injury_snapshot",
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_INJURIES_PROVIDER_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id")),
            "connector_name": _normalize_text(source_bundle.get("connector_name")),
            "connector_family": _normalize_text(source_bundle.get("connector_family")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
            "dataset_version": dataset_version,
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
            "evidence_role": "pregame_injury_report",
        },
    ).as_dict()


def _promote_injuries_asset_lifecycle(
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
        lifecycle_reason=f"{asset_label} asset discovered through the canonical open-data + manual-evidence path",
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
        notes={
            "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
        },
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="connector_mapped",
        lifecycle_reason=f"connector mapped for {asset_label} research asset",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_INJURIES_CONNECTOR_EXECUTION_MODE),
        },
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="raw_acquired",
        lifecycle_reason=f"raw {asset_label} evidence captured in the shared acquisition cache",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"raw_record_count": int(raw_acquisition_result.get("raw_record_count") or 0)},
    )
    alignment_status = _normalize_text(alignment_result.get("alignment_certification", {}).get("alignment_status"))
    if alignment_status != "aligned":
        return
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="integrity_verified",
        lifecycle_reason=f"{asset_label} rows passed shared integrity validation and alignment checks",
        alignment_certification=alignment_result["alignment_certification"],
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={"alignment_status": alignment_result["alignment_certification"].get("alignment_status")},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="normalized",
        lifecycle_reason=f"{asset_label} rows normalized into the canonical nfl_injury_snapshots storage table",
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
        lifecycle_reason=f"{asset_label} evidence is queryable for future joins to {', '.join(future_joins)}",
        alignment_certification=alignment_result["alignment_certification"],
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "future_joins": list(future_joins),
            "manual_evidence_supported": True,
        },
    )


def build_nfl_injuries_research_asset_dashboard_snapshot(
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
    storage = create_nfl_p0_storage_engine(storage_path or NFL_INJURIES_RESEARCH_ASSET_STORAGE_PATH, backend=backend)
    try:
        injury_rows = [dict(row) for row in normalized_rows or storage.fetch("nfl_injury_snapshots", order_by="injury_snapshot_id ASC")]
        certification_rows = (
            storage.fetch(
                "historical_research_asset_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID],
                order_by="certification_id ASC",
            )
            if storage.table_exists("historical_research_asset_certifications")
            else []
        )
        dataset_rows = storage.fetch("historical_certifications", order_by="certification_id ASC") if storage.table_exists("historical_certifications") else []
        lifecycle_rows = storage.fetch("research_asset_lifecycles", where="asset_id = ?", params=[DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID]) if storage.table_exists("research_asset_lifecycles") else []
        alignment_rows = storage.fetch("research_asset_alignment_certifications", where="research_asset_id = ?", params=[DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID]) if storage.table_exists("research_asset_alignment_certifications") else []

        latest_certification = dict(certification_rows[-1]) if certification_rows else dict((certification_result or {}).get("research_asset_certification") or {})
        latest_dataset = dict(dataset_rows[-1]) if dataset_rows else dict(dataset_result or {})
        latest_lifecycle = dict(lifecycle_rows[-1]) if lifecycle_rows else dict((lifecycle_result or {}).get("research_asset_lifecycle") or {})
        latest_alignment = dict(alignment_rows[-1]) if alignment_rows else dict((lifecycle_result or {}).get("alignment_certification_row") or {})
        source_bundle = dict(source_bundle or {})

        injury_validation = dict(validation or validate_nfl_p0_rows("nfl_injury_snapshots", injury_rows))
        planner_snapshot = dict(
            coverage_planner_snapshot
            or build_research_asset_coverage_planner_snapshot(
                storage_path=storage_path,
                backend=backend,
                profile_id=NFL_INJURIES_RESEARCH_ASSET_PROFILE_ID,
            )
        )
        resolved_join_validation = dict(join_validation or {})
        if not resolved_join_validation and injury_rows:
            schedule_rows = storage.fetch("nfl_schedule", order_by="game_id ASC") if storage.table_exists("nfl_schedule") else []
            results_rows = storage.fetch("nfl_results", order_by="game_id ASC") if storage.table_exists("nfl_results") else []
            odds_rows = (
                storage.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")
                if storage.table_exists("nfl_odds_snapshots")
                else []
            )
            weather_rows = storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC") if storage.table_exists("nfl_weather_snapshots") else []
            resolved_join_validation = _build_injury_schedule_results_odds_weather_join_validation(
                schedule_rows=schedule_rows,
                results_rows=results_rows,
                odds_rows=odds_rows,
                weather_rows=weather_rows,
                injury_rows=injury_rows,
            )
        lifecycle_state = _normalize_text(latest_lifecycle.get("lifecycle_state"), "missing")
        asset_status = _normalize_text(latest_certification.get("certification_status"), "missing")
        alignment_status = _normalize_text(latest_alignment.get("alignment_status"), "missing")
        ready = bool(injury_rows) and injury_validation.get("ok") and asset_status == "certified" and alignment_status == "aligned"
        seasons = sorted({int(row["season"]) for row in injury_rows if _normalize_text(row.get("season")).isdigit()})
        provider_capability = dict(source_bundle.get("provider_capability") or {})
        connector_summary = {
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text(source_bundle.get("connector_name"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text(source_bundle.get("connector_family"), NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_FAMILY),
            "provider_id": _normalize_text(source_bundle.get("provider"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER),
            "provider_name": _normalize_text(source_bundle.get("source_name"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME),
            "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_INJURIES_CONNECTOR_EXECUTION_MODE),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
            "provider_capability": provider_capability,
        }
        source_summary = {
            "provider_id": connector_summary["provider_id"],
            "provider_name": connector_summary["provider_name"],
            "provider_role": connector_summary["provider_role"],
            "manual_evidence_supported": bool(provider_capability.get("manual_evidence_supported", True)),
        }
        return {
            "ok": ready,
            "status": "ready" if ready else "partial" if injury_rows else "missing",
            "asset_id": DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
            "asset_name": "NFL Injury Snapshots",
            "lifecycle_state": lifecycle_state,
            "certification_status": asset_status,
            "dataset_certification_status": _normalize_text(latest_dataset.get("certification_status"), "missing"),
            "row_count": len(injury_rows),
            "rows_produced": len(injury_rows),
            "coverage_seasons": seasons,
            "missing_required_fields": list(injury_validation.get("missing_fields") or []),
            "alignment_failures": list((latest_alignment.get("alignment_failures") or [])) if latest_alignment else [],
            "source_provider_role": source_summary,
            "readiness_percentage": 100.0 if ready else round((1.0 if injury_validation.get("ok") else 0.0) * 70.0 + (1.0 if asset_status == "certified" else 0.0) * 15.0 + (1.0 if alignment_status == "aligned" else 0.0) * 15.0, 2),
            "source_bundle": source_bundle,
            "validation": injury_validation,
            "research_asset_certifications": [dict(row) for row in certification_rows],
            "dataset_certifications": [dict(row) for row in dataset_rows],
            "research_asset_lifecycles": [dict(row) for row in lifecycle_rows],
            "research_asset_alignment_certifications": [dict(row) for row in alignment_rows],
            "normalized_rows": injury_rows,
            "storage": storage.health(),
            "connector_state": connector_summary,
            "field_provenance": dict((source_bundle or {}).get("field_provenance") or {}),
            "coverage_planner_readiness": {
                "first_production_connector_target": _normalize_text(planner_snapshot.get("coverage_gap_engine", {}).get("first_production_connector_target")),
                "missing_required_asset_ids": list(planner_snapshot.get("coverage_gap_engine", {}).get("missing_required_asset_ids", [])),
                "certified_required_asset_ids": list(planner_snapshot.get("coverage_gap_engine", {}).get("certified_required_asset_ids", [])),
                "future_asset_ids": list(planner_snapshot.get("coverage_gap_engine", {}).get("future_asset_ids", [])),
            },
            "coverage_planner_snapshot": planner_snapshot,
            "join_validation": resolved_join_validation,
            "warnings": [],
        }
    finally:
        storage.close()


def build_nfl_injuries_research_asset_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    game_count: int = 1,
    dataset_version: str | None = None,
    connector_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    if profile.profile_id != NFL_INJURIES_RESEARCH_ASSET_PROFILE_ID:
        raise ValueError(f"unexpected market profile: {profile.profile_id}")

    resolved_connector_bundle = dict(
        connector_bundle
        or build_nfl_injuries_connector_bundle(
            game_count=game_count,
            dataset_version=dataset_version,
        )
    )
    fixture = dict(resolved_connector_bundle.get("fixture") or {})
    raw_injury_rows = [dict(row) for row in resolved_connector_bundle.get("injury_rows", [])]
    if not raw_injury_rows:
        source_bundle_tables = dict((resolved_connector_bundle.get("source_bundle") or {}).get("tables") or {})
        raw_injury_rows = [dict(row) for row in source_bundle_tables.get("nfl_injury_snapshots", [])]
    if not raw_injury_rows:
        raise ValueError("NFL injuries connector did not produce any injury rows")

    created_at = _normalize_text(resolved_connector_bundle.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(resolved_connector_bundle.get("dataset_version"), NFL_P0_DATASET_VERSION)
    provider_capability = dict(resolved_connector_bundle.get("provider_capability") or {})
    source_bundle = dict(resolved_connector_bundle.get("source_bundle") or {})
    source_bundle["provider_capability"] = provider_capability
    source_bundle["tables"] = dict(source_bundle.get("tables") or {})
    source_bundle["source_tables"] = dict(source_bundle.get("source_tables") or {})
    source_bundle["tables"]["nfl_injury_snapshots"] = [dict(row) for row in raw_injury_rows]
    source_bundle["source_tables"]["nfl_injury_snapshots"] = [dict(row) for row in raw_injury_rows]
    source_bundle["field_provenance"] = {
        "nfl_injury_snapshots": _field_provenance_for_row(
            raw_injury_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
            created_at=created_at,
        )
    }

    storage_path = Path(storage_path or NFL_INJURIES_RESEARCH_ASSET_STORAGE_PATH).expanduser().resolve()
    acquisition_runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path, backend=backend)
    try:
        raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id=profile.profile_id,
            dataset_name=NFL_INJURIES_RAW_ACQUISITION_DATASET_NAME,
        )
    finally:
        acquisition_runtime.close()

    normalized_injury_rows = normalize_nfl_p0_rows(
        "nfl_injury_snapshots",
        [dict(row) for row in source_bundle["tables"]["nfl_injury_snapshots"]],
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    injury_validation = validate_nfl_p0_rows("nfl_injury_snapshots", normalized_injury_rows)

    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        storage_columns = set(storage.table_columns("nfl_injury_snapshots"))
        storage_rows_to_write = [{key: value for key, value in row.items() if key in storage_columns} for row in normalized_injury_rows]
        for row in storage_rows_to_write:
            storage.upsert("nfl_injury_snapshots", row, key_columns=("injury_snapshot_id",))
    finally:
        storage.close()

    injury_asset_rows = [
        _build_injury_asset_row(
            row,
            provider_capability=provider_capability,
            source_bundle=source_bundle,
            dataset_version=dataset_version,
            created_at=created_at,
        )
        for row in normalized_injury_rows
    ]

    injury_contract = NFL_P0_TABLE_CONTRACTS["nfl_injury_snapshots"]
    asset_contract = ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
        research_asset_name="NFL Injury Snapshots",
        asset_category="dataset",
        asset_type="table_snapshot",
        source_table_name="nfl_injury_snapshots",
        required_fields=tuple(injury_contract.required_fields),
        required_timestamps=tuple(injury_contract.required_timestamps),
        point_in_time_rules=tuple(
            (
                *injury_contract.point_in_time_rules,
                "report_time <= decision_time",
                "source_snapshot_time <= decision_time",
                "snapshot_time <= decision_time",
            )
        ),
        description="Pregame NFL injury and availability snapshots joined to the certified schedule, results, odds, and weather backbone.",
        priority="P1",
        required=False,
        future_asset=True,
        metadata={
            "market_profile": profile.profile_id,
            "market_family": "sports",
            "minimum_schema": False,
            "dataset_role": "injuries",
            "join_backbone": [
                "dataset.nfl.games",
                "dataset.sports.nfl.schedule",
                "dataset.sports.nfl.results",
                "dataset.nfl.odds_snapshots",
                "dataset.nfl.weather_snapshots",
            ],
            "evidence_role": "pregame_injury_report",
            "manual_evidence_supported": True,
        },
    )

    certification_runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path, backend=backend)
    try:
        schedule_rows = [dict(row) for row in certification_runtime.store.fetch("nfl_schedule", order_by="schedule_id ASC")] if certification_runtime.store.table_exists("nfl_schedule") else []
        results_rows = [dict(row) for row in certification_runtime.store.fetch("nfl_results", order_by="result_id ASC")] if certification_runtime.store.table_exists("nfl_results") else []
        odds_rows = [dict(row) for row in certification_runtime.store.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")] if certification_runtime.store.table_exists("nfl_odds_snapshots") else []
        weather_rows = [dict(row) for row in certification_runtime.store.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")] if certification_runtime.store.table_exists("nfl_weather_snapshots") else []
        games_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.nfl.games")
        schedule_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.sports.nfl.schedule")
        results_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.sports.nfl.results")
        odds_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.nfl.odds_snapshots")
        weather_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.nfl.weather_snapshots")
        join_validation = _build_injury_schedule_results_odds_weather_join_validation(
            schedule_rows=schedule_rows,
            results_rows=results_rows,
            odds_rows=odds_rows,
            weather_rows=weather_rows,
            injury_rows=injury_asset_rows,
        )
        games_certified = _normalize_text(games_cert_row.get("certification_status")) == "certified"
        schedule_certified = _normalize_text(schedule_cert_row.get("certification_status")) == "certified"
        results_certified = _normalize_text(results_cert_row.get("certification_status")) == "certified"
        odds_certified = _normalize_text(odds_cert_row.get("certification_status")) == "certified"
        weather_certified = _normalize_text(weather_cert_row.get("certification_status")) == "certified"
        certification_errors = list(injury_validation.get("errors") or [])
        if not join_validation["ok"]:
            certification_errors.append("schedule_results_odds_weather_join_alignment_failed")
        if not games_certified:
            certification_errors.append("games_backbone_not_certified")
        if not schedule_certified:
            certification_errors.append("schedule_backbone_not_certified")
        if not results_certified:
            certification_errors.append("results_backbone_not_certified")
        if not odds_certified:
            certification_errors.append("odds_backbone_not_certified")
        if not weather_certified:
            certification_errors.append("weather_backbone_not_certified")
        certification_errors = list(dict.fromkeys(certification_errors))
        certification_validation = {
            **dict(injury_validation),
            "ok": not certification_errors,
            "status": "validated" if not certification_errors else "rejected",
            "error_count": len(certification_errors),
            "errors": certification_errors,
            "join_keys": ["game_id", "team_id", "player_id", "report_time", "snapshot_time"],
            "schedule_results_odds_weather_join_validation": join_validation,
            "backbone_certification": {
                "dataset.nfl.games": "certified" if games_certified else "missing_or_blocked",
                "dataset.sports.nfl.schedule": "certified" if schedule_certified else "missing_or_blocked",
                "dataset.sports.nfl.results": "certified" if results_certified else "missing_or_blocked",
                "dataset.nfl.odds_snapshots": "certified" if odds_certified else "missing_or_blocked",
                "dataset.nfl.weather_snapshots": "certified" if weather_certified else "missing_or_blocked",
            },
        }
        injury_result = certification_runtime.certify_research_asset(
            asset_contract=asset_contract,
            rows=injury_asset_rows,
            profile_id=profile.profile_id,
            validation=certification_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=dataset_version,
            created_at=created_at,
            batch_id=f"{dataset_version}.injuries.batch.001",
        )
        dataset_asset_rows = [
            row
            for row in (
                games_cert_row,
                schedule_cert_row,
                results_cert_row,
                odds_cert_row,
                weather_cert_row,
                injury_result["research_asset_certification"],
            )
            if row
        ]
        dataset_row = build_historical_dataset_certification_row(
            profile=profile,
            dataset_version=dataset_version,
            batch_id=f"{dataset_version}.injuries.batch.001",
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=dataset_asset_rows,
        )
        certification_runtime.store.upsert("historical_certifications", dataset_row, key_columns=("certification_id",))
    finally:
        certification_runtime.close()

    alignment_rows = [dict(row) for row in injury_asset_rows]
    for row in alignment_rows:
        row["schema_version"] = RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION
        row["lineage_version"] = dataset_version

    lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path, backend=backend)
    try:
        alignment_results: list[dict[str, Any]] = []
        dataset_identity = build_nfl_injuries_dataset_identity(
            source_bundle=source_bundle,
            dataset_version=dataset_version,
        )
        dataset_identity_contract = ResearchAssetIdentityContract.from_mapping(dataset_identity)
        for row in alignment_rows:
            row_identity = ResearchAssetIdentityContract.from_mapping(
                build_nfl_injuries_research_asset_identity(
                    injury_row=row,
                    source_bundle=source_bundle,
                    dataset_version=dataset_version,
                )
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[row],
                required_fields=asset_contract.required_fields,
                required_timestamps=asset_contract.required_timestamps,
                profile=profile,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=created_at,
                asset_name=row_identity.asset_name,
                asset_type=row_identity.asset_type,
                lifecycle_state="integrity_verified",
                batch_id=_normalize_text(
                    row.get("injury_snapshot_id"),
                    _normalize_text(row.get("player_id"), _normalize_text(row.get("game_id"))),
                ),
            )
            alignment_row = build_time_entity_alignment_certification_row(
                identity=dataset_identity_contract,
                alignment=alignment_contract,
                profile=profile,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                batch_id=f"{dataset_version}.injuries.alignment.001",
            )
            alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
            if not alignment_validation["ok"]:
                raise ValueError(
                    "; ".join(alignment_validation.get("validation", {}).get("errors", []))
                    or "time entity alignment row validation failed"
                )
            lifecycle_runtime.store.upsert(
                "research_asset_alignment_certifications",
                alignment_row,
                key_columns=("alignment_certification_id",),
            )
            alignment_results.append(
                {
                    "ok": alignment_contract.alignment_status == "aligned",
                    "status": alignment_contract.alignment_status,
                    "identity": dataset_identity_contract.as_dict(),
                    "alignment_certification": alignment_contract.as_dict(),
                    "research_asset_lifecycle": {},
                    "alignment_certification_row": alignment_row,
                    "validation": alignment_validation,
                }
            )
        alignment_result = alignment_results[-1] if alignment_results else {}
        if alignment_rows:
            _promote_injuries_asset_lifecycle(
                lifecycle_runtime=lifecycle_runtime,
                identity=build_nfl_injuries_research_asset_identity(
                    injury_row=alignment_rows[-1],
                    source_bundle=source_bundle,
                    dataset_version=dataset_version,
                ),
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=created_at,
                normalized_rows=alignment_rows,
                alignment_result=alignment_result,
                certification_result=injury_result,
                dataset_result=dataset_row,
                asset_label="NFL injuries",
                future_joins=["team_stats", "player_stats", "betting_splits"],
            )
        coverage_planner_snapshot = build_research_asset_coverage_planner_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile.profile_id,
        )
        readiness_snapshot = build_nfl_injuries_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=fixture or resolved_connector_bundle,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=injury_asset_rows,
            validation=certification_validation,
            certification_result=injury_result,
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
            "fixture": fixture or resolved_connector_bundle,
            "source_bundle": source_bundle,
            "raw_acquisition_result": raw_acquisition_result,
            "normalized_rows": injury_asset_rows,
            "validation": certification_validation,
            "research_asset_certification": injury_result["research_asset_certification"],
            "dataset_certification": dataset_row,
            "alignment_results": alignment_results,
            "lifecycle_alignment": alignment_result,
            "join_validation": join_validation,
            "coverage_planner_snapshot": coverage_planner_snapshot,
            "readiness_snapshot": readiness_snapshot,
        }
    finally:
        lifecycle_runtime.close()


def get_nfl_injuries_research_asset_snapshot_for_dashboard(
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
    """Return the canonical NFL injuries research asset readiness snapshot."""
    try:
        return build_nfl_injuries_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=fixture,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=normalized_rows,
            validation=validation,
            certification_result=certification_result,
            dataset_result=dataset_result,
            lifecycle_result=lifecycle_result,
            join_validation=join_validation,
            coverage_planner_snapshot=coverage_planner_snapshot,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "nfl_injuries_research_asset_snapshot_error",
            "asset_id": DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID,
            "asset_name": "NFL Injury Snapshots",
            "lifecycle_state": "missing",
            "certification_status": "missing",
            "dataset_certification_status": "missing",
            "row_count": 0,
            "rows_produced": 0,
            "coverage_seasons": [],
            "missing_required_fields": [],
            "alignment_failures": [],
            "source_provider_role": {},
            "readiness_percentage": 0.0,
            "source_bundle": {},
            "validation": {},
            "research_asset_certifications": [],
            "dataset_certifications": [],
            "research_asset_lifecycles": [],
            "research_asset_alignment_certifications": [],
            "normalized_rows": [],
            "connector_state": {},
            "field_provenance": {},
            "coverage_planner_readiness": {},
            "coverage_planner_snapshot": {},
            "join_validation": {},
            "storage": {},
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_NFL_INJURIES_RESEARCH_ASSET_ID",
    "NFL_INJURIES_RAW_ACQUISITION_DATASET_NAME",
    "NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_ID",
    "NFL_INJURIES_RESEARCH_ASSET_CONNECTOR_NAME",
    "NFL_INJURIES_RESEARCH_ASSET_DATASET_NAME",
    "NFL_INJURIES_RESEARCH_ASSET_LIFECYCLE_VERSION",
    "NFL_INJURIES_RESEARCH_ASSET_PROFILE_ID",
    "NFL_INJURIES_RESEARCH_ASSET_PROVIDER",
    "NFL_INJURIES_RESEARCH_ASSET_PROVIDER_NAME",
    "NFL_INJURIES_RESEARCH_ASSET_PROVIDER_ROLE",
    "NFL_INJURIES_RESEARCH_ASSET_STORAGE_PATH",
    "build_nfl_injuries_connector_bundle",
    "build_nfl_injuries_provider_capability",
    "build_nfl_injuries_research_asset_dashboard_snapshot",
    "build_nfl_injuries_research_asset_identity",
    "build_nfl_injuries_research_asset_population",
    "get_nfl_injuries_research_asset_snapshot_for_dashboard",
]
