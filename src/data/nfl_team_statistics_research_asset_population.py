from __future__ import annotations

import hashlib
import json
from collections import defaultdict
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
    NFL_TEAM_STATS_METRIC_UNITS,
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


DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID = "dataset.nfl.team_stats_snapshots"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_STORAGE_PATH = get_runtime_data_path(
    "nfl_team_statistics_research_asset",
    "canonical_data.sqlite",
)
NFL_TEAM_STATISTICS_RESEARCH_ASSET_DATASET_NAME = "nfl_team_statistics_research_asset"
NFL_TEAM_STATISTICS_RAW_ACQUISITION_DATASET_NAME = "nfl_team_statistics_raw_acquisition_cache"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER = "nflverse"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME = "nflverse"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE = "primary_acquisition"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_SOURCE_ROLE = NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER
NFL_TEAM_STATISTICS_PROVIDER_SOURCE_TYPE = "team_stats_fixture"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROFILE_ID = "sports:nfl"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_LIFECYCLE_VERSION = "v1"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID = "connector.feeds.nfl_team_stats"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_NAME = "NFL Team Statistics Connector"
NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY = "feeds"
NFL_TEAM_STATISTICS_CONNECTOR_EXECUTION_MODE = "deterministic_fixture"

_ALLOWED_STATISTIC_CONTEXTS = {"pregame", "pregame_provider_snapshot"}
_ALLOWED_MEASUREMENT_PERIODS = {
    "rolling_prior_games",
    "season_to_date_excluding_current_event",
    "prior_game_realized",
}
_ALLOWED_WINDOW_TYPES = {
    "rolling_prior_games_excluding_current_event",
    "season_to_date_excluding_current_event",
    "prior_game_only",
}
_LEAKY_STATISTIC_CONTEXTS = {
    "live",
    "in_game",
    "postgame",
    "final",
    "target_event_live",
    "target_event_final",
}
_LEAKY_WINDOW_TYPES = {
    "same_event",
    "target_event_including_current",
    "target_event_live",
    "target_event_final",
    "final_box_score",
}


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


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


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


def _load_json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): payload for key, payload in value.items()}
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return {str(key): payload for key, payload in parsed.items()}
    return {}


def _team_stats_rows(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    tables = fixture.get("tables") or {}
    if not isinstance(tables, Mapping):
        return []
    rows = tables.get("nfl_team_stats_snapshots") or []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _field_provenance_for_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    created_at: str,
) -> dict[str, Any]:
    source_provider = _normalize_text(
        provider_capability.get("provider_id"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
    )
    source_provider_name = _normalize_text(
        provider_capability.get("provider_name"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
    )
    quality = _normalize_text(provider_capability.get("quality_tier"), "high_priority_adapter")
    row_id = _normalize_text(
        row.get("team_stats_snapshot_id")
        or row.get("source_record_id")
        or row.get("team_id")
        or row.get("game_id")
        or "row"
    )
    lineage_id = _stable_id("nfl_team_stats_field_lineage", source_bundle_id, row_id)
    field_map = {
        "team_stats_snapshot_id": "team_stats_snapshot_id",
        "game_id": "game_id",
        "event_id": "game_id",
        "season": "season",
        "week": "week",
        "league": "league",
        "sport": "sport",
        "team_id": "team_id",
        "team_name": "team_name",
        "opponent_team_id": "opponent_team_id",
        "team_side": "team_side",
        "kickoff_time": "kickoff_time",
        "source_record_id": "source_record_id",
        "source_retrieved_at": "source_retrieved_at",
        "measurement_period": "measurement_period",
        "statistic_context": "statistic_context",
        "statistic_window_type": "statistic_window_type",
        "window_start_time": "window_start_time",
        "team_stats_cutoff_time": "team_stats_cutoff_time",
        "window_excludes_current_event": "window_excludes_current_event",
        "rest_days": "rest_days",
        "travel_distance_miles": "travel_distance_miles",
        "travel_timezone_change": "travel_timezone_change",
        "offensive_efficiency": "offensive_efficiency",
        "defensive_efficiency": "defensive_efficiency",
        "pace": "pace",
        "play_volume": "play_volume",
        "scoring_efficiency": "scoring_efficiency",
        "turnover_rate": "turnover_rate",
        "red_zone_efficiency": "red_zone_efficiency",
        "third_down_efficiency": "third_down_efficiency",
        "special_teams_efficiency": "special_teams_efficiency",
        "coaching_continuity": "coaching_continuity",
        "roster_continuity": "roster_continuity",
        "injury_adjusted_availability": "injury_adjusted_availability",
        "position_group": "position_group",
        "efficiency_window_games": "efficiency_window_games",
        "metric_units_json": "metric_units_json",
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
        "dataset_version": "dataset_version",
        "schema_version": "schema_version",
        "status": "status",
        "quality_score": "quality_score",
        "completeness_score": "completeness_score",
        "alignment_status": "alignment_status",
        "certification_state": "certification_state",
        "market_type": "market_type",
    }
    provenance: dict[str, Any] = {}
    for field_name, source_field_name in field_map.items():
        provenance[field_name] = {
            "source_provider": source_provider,
            "source_provider_name": source_provider_name,
            "source_field_name": source_field_name,
            "raw_field_name": source_field_name,
            "acquisition_timestamp": created_at,
            "raw_payload_reference": (
                f"{source_bundle_id}:nfl_team_stats_snapshots:{row_id}:{source_field_name}"
            ),
            "lineage_id": lineage_id,
            "confidence": 1.0,
            "quality": quality,
        }
    return provenance


def build_nfl_team_statistics_provider_capability(
    *,
    dataset_version: str | None = None,
    game_count: int = 1,
) -> dict[str, Any]:
    metric_fields = list(NFL_TEAM_STATS_METRIC_UNITS)
    source_entry = {
        "source_id": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
        "source_name": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
        "source_family": NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY,
        "source_category": "team_statistics",
        "source_access_type": "open_dataset",
        "coverage": {
            "historical": True,
            "team_stats": True,
            "team_efficiency": True,
            "rolling_prior_games": True,
            "season_to_date_excluding_current_event": True,
            "point_in_time_team_stats": True,
            "manual_evidence_supported": True,
        },
        "freshness": {"expected_update_cadence": "daily"},
        "limits": {"rate_limit_known": False, "throttle_required": False},
        "legal_terms": {"requires_manual_review": True},
        "model_mapping": {
            "model_inputs_supported": [
                "game_id",
                "team_id",
                "opponent_team_id",
                "team_side",
                "source_snapshot_time",
                "snapshot_time",
                "decision_time",
                "team_stats_cutoff_time",
                *metric_fields,
            ],
            "historical_backfill_fields_available": metric_fields,
            "outcome_fields_available": [],
            "join_keys": [
                "game_id",
                "team_id",
                "team_stats_snapshot_id",
                "snapshot_time",
                "team_stats_cutoff_time",
            ],
        },
        "current_phase_allowed": True,
        "approval_status": "approved_open_metadata",
        "source_aliases": [
            NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
            "nflverse_team_stats",
            "nflfastr",
            "nflreadr",
            "manual_import",
        ],
    }
    source_quality = score_source(
        source_entry,
        required_inputs=[
            "game_id",
            "team_id",
            "team_side",
            "snapshot_time",
            "decision_time",
            "team_stats_cutoff_time",
            "offensive_efficiency",
            "pace",
        ],
    )
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    team_stats_rows = _team_stats_rows(fixture)
    if not team_stats_rows:
        raise ValueError("NFL team statistics connector did not produce any rows")
    supported_fields = sorted(set(team_stats_rows[0].keys()))
    return {
        "provider_id": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
        "provider_name": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
        "provider_role": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE,
        "connector_id": NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID,
        "connector_name": NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_NAME,
        "connector_family": NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY,
        "source_id": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
        "source_name": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
        "source_family": NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY,
        "source_access_type": "open_dataset",
        "supported_assets": [DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
        "supported_fields": supported_fields,
        "supported_markets": ["sports:nfl", "team_efficiency", "pregame_team_stats_snapshot"],
        "historical_depth": "historical",
        "update_frequency": "daily / historical",
        "point_in_time_safe": True,
        "licensing_notes": (
            "Fixture-backed local mode preserves the canonical open nflverse team-statistics lane "
            "while retaining a manual-import fallback for reviewed local evidence."
        ),
        "cost_class": "open_dataset",
        "certification_readiness": "ready",
        "quality_score": round(
            float(
                source_quality.get("current_phase_usability_score")
                or source_quality.get("coverage_score")
                or 0.0
            )
            / 100.0,
            4,
        ),
        "quality_tier": source_quality.get("quality_tier", "high_priority_adapter"),
        "source_aliases": source_entry["source_aliases"],
        "verification_provider_ids": ["nflfastr"],
        "fallback_provider_ids": ["nflreadr", "manual_import"],
        "source_quality": source_quality,
        "evidence_role": "pregame_team_stats_snapshot",
        "manual_evidence_supported": True,
        "timestamp_semantics": {
            "source_snapshot_time": "Frozen provider snapshot time for the target event context.",
            "team_stats_cutoff_time": "Latest included completed-game cutoff; must exclude the target event.",
            "decision_time": "Pregame decision cutoff for the target event.",
        },
        "revision_behavior": (
            "Fixture mode is immutable; any future open-data revision must produce a new lineage "
            "revision instead of silently overwriting certified history."
        ),
        "metric_coverage": metric_fields,
        "known_limitations": [
            "The current phase remains deterministic fixture mode and does not claim a live connector.",
            "Same-event live or final team statistics are intentionally rejected by certification.",
        ],
    }


def _connector_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    execution_mode: str,
) -> dict[str, Any]:
    payload = dict(row)
    provider_id = _normalize_text(
        provider_capability.get("provider_id"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
    )
    provider_name = _normalize_text(
        provider_capability.get("provider_name"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
    )
    provider_role = _normalize_text(
        provider_capability.get("provider_role"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE,
    )
    connector_id = _normalize_text(
        provider_capability.get("connector_id"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID,
    )
    connector_name = _normalize_text(
        provider_capability.get("connector_name"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_NAME,
    )
    connector_family = _normalize_text(
        provider_capability.get("connector_family"),
        NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY,
    )
    payload.update(
        {
            "source_name": provider_name,
            "source_type": NFL_TEAM_STATISTICS_PROVIDER_SOURCE_TYPE,
            "source_key": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
            "provider": provider_id,
            "provider_name": provider_name,
            "provider_role": provider_role,
            "connector_id": connector_id,
            "connector_name": connector_name,
            "connector_family": connector_family,
            "connector_role": "production_connector",
            "execution_mode": execution_mode,
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_table": "nfl_team_stats_snapshots",
            "acquisition_timestamp": _normalize_text(
                source_bundle.get("acquisition_timestamp"),
                _utc_now_iso(),
            ),
            "provider_capability": dict(provider_capability),
        }
    )
    return payload


def build_nfl_team_statistics_connector_bundle(
    *,
    game_count: int = 1,
    dataset_version: str | None = None,
    execution_mode: str = NFL_TEAM_STATISTICS_CONNECTOR_EXECUTION_MODE,
) -> dict[str, Any]:
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    raw_team_stats_rows = _team_stats_rows(fixture)
    if not raw_team_stats_rows:
        raise ValueError("NFL team statistics connector did not produce any rows")

    created_at = _normalize_text(fixture.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(
        dataset_version or fixture.get("dataset_version"),
        NFL_P0_DATASET_VERSION,
    )
    first_row = raw_team_stats_rows[0]
    source_bundle_id = _stable_id(
        "nfl_team_statistics_connector_bundle",
        dataset_version,
        first_row.get("game_id"),
        first_row.get("team_id"),
        first_row.get("season"),
        first_row.get("week"),
        execution_mode,
    )
    provider_capability = build_nfl_team_statistics_provider_capability(
        dataset_version=dataset_version,
        game_count=max(int(game_count or 1), 1),
    )
    team_stats_rows = [
        _connector_row(
            row,
            provider_capability=provider_capability,
            source_bundle={
                "source_bundle_id": source_bundle_id,
                "acquisition_timestamp": created_at,
            },
            execution_mode=execution_mode,
        )
        for row in raw_team_stats_rows
    ]
    field_provenance = {
        "nfl_team_stats_snapshots": _field_provenance_for_row(
            team_stats_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=source_bundle_id,
            created_at=created_at,
        )
    }
    source_bundle = {
        "dataset_id": f"{DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID}.raw_acquisition_cache",
        "dataset_name": NFL_TEAM_STATISTICS_RAW_ACQUISITION_DATASET_NAME,
        "source_name": provider_capability["provider_name"],
        "source_type": NFL_TEAM_STATISTICS_PROVIDER_SOURCE_TYPE,
        "source_key": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
        "source_family": provider_capability["source_family"],
        "source_access_type": "open_dataset",
        "provider": provider_capability["provider_id"],
        "provider_name": provider_capability["provider_name"],
        "provider_role": provider_capability["provider_role"],
        "provider_sources": [
            provider_capability["provider_id"],
            "nflfastr",
            "nflreadr",
            "manual_import",
        ],
        "provider_versions": [dataset_version],
        "source_bundle_id": source_bundle_id,
        "acquisition_timestamp": created_at,
        "source_snapshot_time": _normalize_text(
            team_stats_rows[0].get("source_snapshot_time"),
            created_at,
        ),
        "result_timestamp": _normalize_text(
            team_stats_rows[0].get("team_stats_cutoff_time"),
            created_at,
        ),
        "source_market_id": _normalize_text(
            team_stats_rows[0].get("game_id"),
            _normalize_text(team_stats_rows[0].get("team_stats_snapshot_id"), "nfl_team_stats"),
        ),
        "source_selection_id": _normalize_text(team_stats_rows[0].get("team_id"), "team"),
        "dataset_version": dataset_version,
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "source_tables": {"nfl_team_stats_snapshots": team_stats_rows},
        "tables": {"nfl_team_stats_snapshots": team_stats_rows},
        "source_file": "nflverse_team_stats_fixture.json",
        "update_frequency": "daily / historical",
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "connector_family": provider_capability["connector_family"],
        "connector_role": "production_connector",
        "execution_mode": execution_mode,
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "evidence_role": "pregame_team_stats_snapshot",
        "manual_evidence_paths": ["manual_import"],
    }
    return {
        "ok": True,
        "status": (
            "connector_ready"
            if execution_mode == NFL_TEAM_STATISTICS_CONNECTOR_EXECUTION_MODE
            else "connector_live_ready"
        ),
        "execution_mode": execution_mode,
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "fixture": fixture,
        "team_stats_rows": team_stats_rows,
        "source_bundle": source_bundle,
        "created_at": created_at,
        "dataset_version": dataset_version,
        "team_stats_row_count": len(team_stats_rows),
        "notes": [
            "The team-statistics connector path stays local-first and deterministic while preserving the canonical nflverse source lane.",
            "The minimum slice keeps explicit cutoff semantics so rolling and season-to-date metrics cannot include the target event.",
            "Field-level provenance is preserved for identifiers, cutoff timestamps, and the canonical metric fields.",
        ],
    }


def _build_team_stats_asset_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
    created_at: str,
    alignment_status: str = "pending",
    certification_state: str = "pending",
) -> dict[str, Any]:
    payload = dict(row)
    game_id = _normalize_text(payload.get("game_id"), _normalize_text(payload.get("event_id")))
    team_id = _normalize_text(payload.get("team_id"))
    team_stats_snapshot_id = _normalize_text(
        payload.get("team_stats_snapshot_id"),
        _stable_id(
            "nfl_team_stats_snapshot",
            game_id,
            team_id,
            payload.get("source_snapshot_time"),
        ),
    )
    team_side = _normalize_text(payload.get("team_side"))
    field_provenance = _field_provenance_for_row(
        payload,
        provider_capability=provider_capability,
        source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
        created_at=created_at,
    )
    payload.update(
        {
            "asset_id": DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
            "asset_family": "dataset",
            "asset_name": "NFL Team Statistics Snapshots",
            "asset_type": "team_stats_snapshot",
            "market_profile": NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROFILE_ID,
            "league": _normalize_text(payload.get("league"), "NFL"),
            "sport": "football",
            "event_id": _normalize_text(payload.get("event_id"), game_id),
            "market_id": team_stats_snapshot_id,
            "selection": team_side or team_id or "team_stats_snapshot",
            "participant_id": team_id,
            "scheduled_time": _normalize_text(payload.get("kickoff_time")),
            "completion_timestamp": _normalize_text(
                payload.get("completion_timestamp"),
                payload.get("team_stats_cutoff_time"),
            ),
            "provider_timestamp": _normalize_text(
                payload.get("provider_timestamp"),
                _normalize_text(
                    payload.get("source_snapshot_time"),
                    _normalize_text(payload.get("team_stats_cutoff_time")),
                ),
            ),
            "source_market_id": _normalize_text(payload.get("source_market_id"), game_id),
            "source_selection_id": _normalize_text(payload.get("source_selection_id"), team_id or team_side or "team"),
            "connector": _normalize_text(
                source_bundle.get("connector_id"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID,
            ),
            "provider": _normalize_text(
                source_bundle.get("provider"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_SOURCE_ROLE,
            ),
            "source_name": _normalize_text(
                source_bundle.get("source_name"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
            ),
            "source_type": _normalize_text(
                source_bundle.get("source_type"),
                NFL_TEAM_STATISTICS_PROVIDER_SOURCE_TYPE,
            ),
            "source_key": _normalize_text(
                source_bundle.get("source_key"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
            ),
            "connector_id": _normalize_text(
                source_bundle.get("connector_id"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID,
            ),
            "connector_name": _normalize_text(
                source_bundle.get("connector_name"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_NAME,
            ),
            "connector_family": _normalize_text(
                source_bundle.get("connector_family"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY,
            ),
            "provider_role": _normalize_text(
                source_bundle.get("provider_role"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE,
            ),
            "execution_mode": _normalize_text(
                source_bundle.get("execution_mode"),
                NFL_TEAM_STATISTICS_CONNECTOR_EXECUTION_MODE,
            ),
            "evidence_role": "pregame_team_stats_snapshot",
            "field_provenance": field_provenance,
            "field_provenance_json": field_provenance,
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "dataset_version": dataset_version,
            "schema_version": NFL_P0_SCHEMA_VERSION,
            "version_id": dataset_version,
            "lineage_version": _normalize_text(
                dataset_version,
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_LIFECYCLE_VERSION,
            ),
            "alignment_status": alignment_status,
            "certification_state": certification_state,
        }
    )
    return payload


def _build_team_stats_backbone_join_validation(
    *,
    schedule_rows: Sequence[Mapping[str, Any]],
    results_rows: Sequence[Mapping[str, Any]],
    odds_rows: Sequence[Mapping[str, Any]],
    weather_rows: Sequence[Mapping[str, Any]],
    injury_rows: Sequence[Mapping[str, Any]],
    team_stats_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    schedule_index = {
        _normalize_text(row.get("game_id")): dict(row)
        for row in schedule_rows
        if _normalize_text(row.get("game_id"))
    }
    results_index = {
        _normalize_text(row.get("game_id")): dict(row)
        for row in results_rows
        if _normalize_text(row.get("game_id"))
    }
    weather_index = {
        _normalize_text(row.get("game_id")): dict(row)
        for row in weather_rows
        if _normalize_text(row.get("game_id"))
    }
    odds_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in odds_rows:
        game_id = _normalize_text(row.get("game_id"))
        if game_id:
            odds_index[game_id].append(dict(row))
    injury_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in injury_rows:
        game_id = _normalize_text(row.get("game_id"))
        team_id = _normalize_text(row.get("team_id"))
        if game_id and team_id:
            injury_index[(game_id, team_id)].append(dict(row))

    missing_schedule_rows: list[str] = []
    missing_results_rows: list[str] = []
    missing_odds_rows: list[str] = []
    missing_weather_rows: list[str] = []
    orphaned_team_stats_rows: list[str] = []
    duplicate_identity_rows: list[str] = []
    post_decision_team_stats_rows: list[str] = []
    same_event_final_stat_rows: list[str] = []
    rolling_window_leakage_rows: list[str] = []
    unsupported_metric_unit_rows: list[str] = []
    team_mismatches: list[dict[str, Any]] = []
    opponent_mismatches: list[dict[str, Any]] = []
    home_away_conflicts: list[dict[str, Any]] = []
    timing_issues: list[dict[str, Any]] = []
    seen_identity_seeds: set[tuple[str, str, str, str, str]] = set()
    matched_rows = 0
    matched_injury_context_rows = 0

    for row in team_stats_rows:
        team_stats_snapshot_id = _normalize_text(row.get("team_stats_snapshot_id"))
        game_id = _normalize_text(row.get("game_id"))
        team_id = _normalize_text(row.get("team_id"))
        snapshot_time_text = _normalize_text(row.get("snapshot_time"))
        source_name = _normalize_text(row.get("source_name"))
        source_record_id = _normalize_text(
            row.get("source_record_id"),
            team_stats_snapshot_id or team_id or game_id,
        )
        identity_seed = (
            game_id,
            team_id,
            source_record_id,
            snapshot_time_text,
            source_name,
        )
        if identity_seed in seen_identity_seeds and team_stats_snapshot_id:
            duplicate_identity_rows.append(team_stats_snapshot_id)
        seen_identity_seeds.add(identity_seed)

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
            orphaned_team_stats_rows.append(team_stats_snapshot_id or game_id or team_id)
            continue

        matched_rows += 1
        home_team_id = _normalize_text(schedule_row.get("home_team_id"))
        away_team_id = _normalize_text(schedule_row.get("away_team_id"))
        opponent_team_id = _normalize_text(row.get("opponent_team_id"))
        team_side = _normalize_text(row.get("team_side")).lower()
        if team_id not in {home_team_id, away_team_id}:
            team_mismatches.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "team_id",
                    "team_id": team_id,
                }
            )
        if opponent_team_id not in {home_team_id, away_team_id} or opponent_team_id == team_id:
            opponent_mismatches.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "opponent_team_id",
                    "opponent_team_id": opponent_team_id,
                }
            )
        if team_side == "home" and team_id != home_team_id:
            home_away_conflicts.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "expected": "home",
                    "team_id": team_id,
                }
            )
        if team_side == "away" and team_id != away_team_id:
            home_away_conflicts.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "expected": "away",
                    "team_id": team_id,
                }
            )
        if team_side not in {"home", "away"}:
            home_away_conflicts.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "expected": "home_or_away",
                    "team_side": team_side,
                }
            )
        if _normalize_text(results_row.get("home_team_id")) not in {"", home_team_id}:
            team_mismatches.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "results_home_team_id",
                }
            )
        if _normalize_text(results_row.get("away_team_id")) not in {"", away_team_id}:
            team_mismatches.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "results_away_team_id",
                }
            )
        if _normalize_text(weather_row.get("home_team_id")) not in {"", home_team_id}:
            team_mismatches.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "weather_home_team_id",
                }
            )
        if _normalize_text(weather_row.get("away_team_id")) not in {"", away_team_id}:
            team_mismatches.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "weather_away_team_id",
                }
            )

        if injury_index and injury_index.get((game_id, team_id)):
            matched_injury_context_rows += 1

        kickoff_time = _parse_iso(schedule_row.get("kickoff_time") or row.get("kickoff_time"))
        source_snapshot_time = _parse_iso(row.get("source_snapshot_time"))
        snapshot_time = _parse_iso(row.get("snapshot_time"))
        decision_time = _parse_iso(row.get("decision_time"))
        source_retrieved_at = _parse_iso(row.get("source_retrieved_at"))
        window_start_time = _parse_iso(row.get("window_start_time"))
        team_stats_cutoff_time = _parse_iso(row.get("team_stats_cutoff_time"))

        for field_name, instant in (
            ("kickoff_time", kickoff_time),
            ("source_snapshot_time", source_snapshot_time),
            ("snapshot_time", snapshot_time),
            ("decision_time", decision_time),
            ("source_retrieved_at", source_retrieved_at),
            ("window_start_time", window_start_time),
            ("team_stats_cutoff_time", team_stats_cutoff_time),
        ):
            if instant is None:
                timing_issues.append(
                    {
                        "team_stats_snapshot_id": team_stats_snapshot_id,
                        "game_id": game_id,
                        "field": field_name,
                        "reason": f"missing_{field_name}",
                    }
                )
        if any(
            instant is None
            for instant in (
                kickoff_time,
                source_snapshot_time,
                snapshot_time,
                decision_time,
                source_retrieved_at,
                window_start_time,
                team_stats_cutoff_time,
            )
        ):
            continue

        if source_retrieved_at < source_snapshot_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "source_retrieved_at",
                    "reason": "source_retrieved_before_source_snapshot",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if source_snapshot_time > snapshot_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "source_snapshot_time",
                    "reason": "source_snapshot_after_snapshot_time",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if source_snapshot_time > decision_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "source_snapshot_time",
                    "reason": "source_snapshot_after_decision",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if snapshot_time > decision_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "snapshot_time",
                    "reason": "snapshot_after_decision",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if decision_time > kickoff_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "decision_time",
                    "reason": "decision_time_after_kickoff",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if source_snapshot_time > kickoff_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "source_snapshot_time",
                    "reason": "source_snapshot_after_kickoff",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if snapshot_time > kickoff_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "snapshot_time",
                    "reason": "snapshot_after_kickoff",
                }
            )
            post_decision_team_stats_rows.append(team_stats_snapshot_id)
        if team_stats_cutoff_time > decision_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "team_stats_cutoff_time",
                    "reason": "team_stats_cutoff_after_decision",
                }
            )
            rolling_window_leakage_rows.append(team_stats_snapshot_id)
        if team_stats_cutoff_time > kickoff_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "team_stats_cutoff_time",
                    "reason": "team_stats_cutoff_after_kickoff",
                }
            )
            rolling_window_leakage_rows.append(team_stats_snapshot_id)
        if team_stats_cutoff_time > snapshot_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "team_stats_cutoff_time",
                    "reason": "team_stats_cutoff_after_snapshot",
                }
            )
            rolling_window_leakage_rows.append(team_stats_snapshot_id)
        if window_start_time > team_stats_cutoff_time:
            timing_issues.append(
                {
                    "team_stats_snapshot_id": team_stats_snapshot_id,
                    "game_id": game_id,
                    "field": "window_start_time",
                    "reason": "window_start_after_team_stats_cutoff",
                }
            )
            rolling_window_leakage_rows.append(team_stats_snapshot_id)

        statistic_context = _normalize_text(row.get("statistic_context")).lower()
        measurement_period = _normalize_text(row.get("measurement_period")).lower()
        statistic_window_type = _normalize_text(row.get("statistic_window_type")).lower()
        if (
            statistic_context in _LEAKY_STATISTIC_CONTEXTS
            or measurement_period in _LEAKY_STATISTIC_CONTEXTS
            or statistic_window_type in _LEAKY_WINDOW_TYPES
        ):
            same_event_final_stat_rows.append(team_stats_snapshot_id)
        if _normalize_int(row.get("window_excludes_current_event"), 0) != 1:
            rolling_window_leakage_rows.append(team_stats_snapshot_id)

        metric_units = _load_json_mapping(row.get("metric_units_json"))
        if not metric_units:
            unsupported_metric_unit_rows.append(team_stats_snapshot_id)
        else:
            for field_name, expected_unit in NFL_TEAM_STATS_METRIC_UNITS.items():
                if _normalize_text(metric_units.get(field_name)).lower() != expected_unit.lower():
                    unsupported_metric_unit_rows.append(team_stats_snapshot_id)
                    break

    ok = bool(team_stats_rows) and not any(
        (
            missing_schedule_rows,
            missing_results_rows,
            missing_odds_rows,
            missing_weather_rows,
            orphaned_team_stats_rows,
            duplicate_identity_rows,
            post_decision_team_stats_rows,
            same_event_final_stat_rows,
            rolling_window_leakage_rows,
            unsupported_metric_unit_rows,
            team_mismatches,
            opponent_mismatches,
            home_away_conflicts,
            timing_issues,
        )
    )
    return {
        "ok": ok,
        "status": "aligned" if ok else "blocked",
        "matched_rows": matched_rows,
        "missing_schedule_rows": sorted(set(filter(None, missing_schedule_rows))),
        "missing_results_rows": sorted(set(filter(None, missing_results_rows))),
        "missing_odds_rows": sorted(set(filter(None, missing_odds_rows))),
        "missing_weather_rows": sorted(set(filter(None, missing_weather_rows))),
        "orphaned_team_stats_rows": sorted(set(filter(None, orphaned_team_stats_rows))),
        "duplicate_identity_rows": sorted(set(filter(None, duplicate_identity_rows))),
        "post_decision_team_stats_rows": sorted(
            set(filter(None, post_decision_team_stats_rows))
        ),
        "same_event_final_stat_rows": sorted(
            set(filter(None, same_event_final_stat_rows))
        ),
        "rolling_window_leakage_rows": sorted(
            set(filter(None, rolling_window_leakage_rows))
        ),
        "unsupported_metric_unit_rows": sorted(
            set(filter(None, unsupported_metric_unit_rows))
        ),
        "team_mismatches": team_mismatches,
        "opponent_mismatches": opponent_mismatches,
        "home_away_conflicts": home_away_conflicts,
        "timing_issues": timing_issues,
        "team_stats_row_count": len(team_stats_rows),
        "schedule_row_count": len(schedule_rows),
        "results_row_count": len(results_rows),
        "odds_row_count": len(odds_rows),
        "weather_row_count": len(weather_rows),
        "injury_row_count": len(injury_rows),
        "optional_injury_backbone_available": bool(injury_rows),
        "matched_injury_context_rows": matched_injury_context_rows,
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


def build_nfl_team_statistics_research_asset_identity(
    *,
    team_stats_row: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    payload = dict(team_stats_row)
    game_id = _normalize_text(payload.get("game_id"), _normalize_text(payload.get("event_id")))
    team_id = _normalize_text(payload.get("team_id"))
    team_stats_snapshot_id = _normalize_text(
        payload.get("team_stats_snapshot_id"),
        _stable_id("team_stats_identity", game_id, team_id),
    )
    team_side = _normalize_text(payload.get("team_side"), team_id or "team")
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market="nfl_p0",
        league=_normalize_text(payload.get("league"), _normalize_text(profile.metadata.get("league"), "NFL")),
        sport=_normalize_text(payload.get("sport"), _normalize_text(profile.metadata.get("sport"), "football")),
        season=_normalize_text(payload.get("season")),
        week_or_date=_normalize_text(payload.get("week")),
        event_id=_normalize_text(payload.get("event_id"), game_id),
        market_id=team_stats_snapshot_id,
        selection=team_side,
        provider=_normalize_text(source_bundle.get("provider"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER),
        connector=_normalize_text(source_bundle.get("connector_id"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_version=_normalize_text(dataset_version, NFL_TEAM_STATISTICS_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Team Statistics Snapshots",
        asset_type="team_stats_snapshot",
        participant_id=team_id,
        team_id=team_id,
        game_id=game_id,
        market_type=_normalize_text(payload.get("market_type"), "team_efficiency"),
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_TEAM_STATISTICS_PROVIDER_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id")),
            "connector_name": _normalize_text(source_bundle.get("connector_name")),
            "connector_family": _normalize_text(source_bundle.get("connector_family")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
            "dataset_version": dataset_version,
            "team_stats_snapshot_id": team_stats_snapshot_id,
            "game_id": game_id,
            "team_id": team_id,
            "team_side": team_side,
            "source_record_id": _normalize_text(payload.get("source_record_id")),
            "source_retrieved_at": _normalize_text(payload.get("source_retrieved_at")),
            "measurement_period": _normalize_text(payload.get("measurement_period")),
            "statistic_context": _normalize_text(payload.get("statistic_context")),
            "statistic_window_type": _normalize_text(payload.get("statistic_window_type")),
            "team_stats_cutoff_time": _normalize_text(payload.get("team_stats_cutoff_time")),
            "window_excludes_current_event": _normalize_int(payload.get("window_excludes_current_event"), 0),
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
            "evidence_role": "pregame_team_stats_snapshot",
        },
    ).as_dict()


def build_nfl_team_statistics_dataset_identity(
    *,
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market="nfl_p0",
        league=_normalize_text(source_bundle.get("league"), _normalize_text(profile.metadata.get("league"), "NFL")),
        sport=_normalize_text(source_bundle.get("sport"), _normalize_text(profile.metadata.get("sport"), "football")),
        season="",
        week_or_date="",
        event_id="",
        market_id=DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
        selection="team_stats_snapshot",
        provider=_normalize_text(source_bundle.get("provider"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER),
        connector=_normalize_text(source_bundle.get("connector_id"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_version=_normalize_text(dataset_version, NFL_TEAM_STATISTICS_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Team Statistics Snapshots",
        asset_type="team_stats_snapshot",
        participant_id="",
        team_id="",
        game_id="",
        market_type="team_efficiency",
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_TEAM_STATISTICS_PROVIDER_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id")),
            "connector_name": _normalize_text(source_bundle.get("connector_name")),
            "connector_family": _normalize_text(source_bundle.get("connector_family")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
            "dataset_version": dataset_version,
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
            "evidence_role": "pregame_team_stats_snapshot",
        },
    ).as_dict()


def _promote_team_stats_asset_lifecycle(
    *,
    lifecycle_runtime: ResearchAssetLifecycleRuntime,
    identity: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    raw_acquisition_result: Mapping[str, Any],
    created_at: str,
    normalized_rows: Sequence[Mapping[str, Any]],
    alignment_results: Sequence[Mapping[str, Any]],
    certification_result: Mapping[str, Any],
    dataset_result: Mapping[str, Any],
    asset_label: str,
    future_joins: Sequence[str],
) -> None:
    alignment_summary = {
        "alignment_status": "aligned" if alignment_results and all(bool(item.get("ok")) for item in alignment_results) else "blocked",
        "alignment_reason": (
            "row_level_team_statistics_alignment_certified"
            if alignment_results and all(bool(item.get("ok")) for item in alignment_results)
            else "row_level_team_statistics_alignment_blocked"
        ),
        "alignment_score": round(
            sum(
                float(
                    (item.get("alignment_certification") or {}).get("alignment_score")
                    or 0.0
                )
                for item in alignment_results
            )
            / max(len(alignment_results), 1),
            4,
        ),
        "summary": {
            "alignment_row_count": len(alignment_results),
            "aligned_row_count": sum(
                1 for item in alignment_results if bool(item.get("ok"))
            ),
            "blocked_alignment_ids": [
                _normalize_text(
                    (item.get("alignment_certification") or {}).get(
                        "alignment_certification_id"
                    )
                )
                for item in alignment_results
                if not bool(item.get("ok"))
            ],
        },
    }
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
            "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE),
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
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_TEAM_STATISTICS_CONNECTOR_EXECUTION_MODE),
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
    all_alignments_ok = bool(alignment_results) and all(bool(item.get("ok")) for item in alignment_results)
    if not all_alignments_ok:
        return
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="integrity_verified",
        lifecycle_reason=f"{asset_label} rows passed shared integrity validation and alignment checks",
        certification_result=alignment_summary,
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "alignment_status": alignment_summary.get("alignment_status"),
            "alignment_row_count": len(alignment_results),
        },
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="normalized",
        lifecycle_reason=f"{asset_label} rows normalized into the canonical nfl_team_stats_snapshots storage table",
        certification_result=alignment_summary,
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
            **alignment_summary,
            **dict(certification_result),
        },
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
    )
    if _normalize_text(dataset_result.get("certification_status")) != "certified":
        return
    lifecycle_runtime.record_dataset_certified(
        identity=identity,
        certification_result={
            **alignment_summary,
            **dict(dataset_result),
        },
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="feature_ready",
        lifecycle_reason=f"{asset_label} evidence is queryable for future joins to {', '.join(future_joins)}",
        certification_result=alignment_summary,
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "future_joins": list(future_joins),
            "minimum_schema_asset": True,
            "alignment_row_count": len(alignment_results),
        },
    )


def build_nfl_team_statistics_research_asset_dashboard_snapshot(
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
    storage = create_nfl_p0_storage_engine(
        storage_path or NFL_TEAM_STATISTICS_RESEARCH_ASSET_STORAGE_PATH,
        backend=backend,
    )
    try:
        team_stats_rows = [
            dict(row)
            for row in (
                normalized_rows
                or storage.fetch("nfl_team_stats_snapshots", order_by="team_stats_snapshot_id ASC")
            )
        ]
        certification_rows = (
            storage.fetch(
                "historical_research_asset_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
                order_by="certification_id ASC",
            )
            if storage.table_exists("historical_research_asset_certifications")
            else []
        )
        dataset_rows = (
            storage.fetch("historical_certifications", order_by="certification_id ASC")
            if storage.table_exists("historical_certifications")
            else []
        )
        raw_cache_rows = (
            storage.fetch(
                "raw_records",
                where="dataset_id = ?",
                params=[
                    f"{DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID}.raw_acquisition_cache"
                ],
                order_by="row_index ASC",
            )
            if storage.table_exists("raw_records")
            else []
        )
        lifecycle_rows = (
            storage.fetch(
                "research_asset_lifecycles",
                where="asset_id = ?",
                params=[DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
            )
            if storage.table_exists("research_asset_lifecycles")
            else []
        )
        alignment_rows = (
            storage.fetch(
                "research_asset_alignment_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID],
                order_by="alignment_certification_id ASC",
            )
            if storage.table_exists("research_asset_alignment_certifications")
            else []
        )

        latest_certification = (
            dict(certification_rows[-1])
            if certification_rows
            else dict((certification_result or {}).get("research_asset_certification") or {})
        )
        latest_dataset = (
            dict(dataset_rows[-1])
            if dataset_rows
            else dict(dataset_result or {})
        )
        latest_lifecycle = (
            dict(lifecycle_rows[-1])
            if lifecycle_rows
            else dict((lifecycle_result or {}).get("research_asset_lifecycle") or {})
        )
        resolved_validation = dict(
            validation or validate_nfl_p0_rows("nfl_team_stats_snapshots", team_stats_rows)
        )
        planner_snapshot = dict(
            coverage_planner_snapshot
            or build_research_asset_coverage_planner_snapshot(
                storage_path=storage_path,
                backend=backend,
                profile_id=NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROFILE_ID,
            )
        )
        resolved_join_validation = dict(join_validation or {})
        if not resolved_join_validation and team_stats_rows:
            schedule_rows = (
                storage.fetch("nfl_schedule", order_by="game_id ASC")
                if storage.table_exists("nfl_schedule")
                else []
            )
            results_rows = (
                storage.fetch("nfl_results", order_by="game_id ASC")
                if storage.table_exists("nfl_results")
                else []
            )
            odds_rows = (
                storage.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")
                if storage.table_exists("nfl_odds_snapshots")
                else []
            )
            weather_rows = (
                storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")
                if storage.table_exists("nfl_weather_snapshots")
                else []
            )
            injury_rows = (
                storage.fetch("nfl_injury_snapshots", order_by="injury_snapshot_id ASC")
                if storage.table_exists("nfl_injury_snapshots")
                else []
            )
            resolved_join_validation = _build_team_stats_backbone_join_validation(
                schedule_rows=schedule_rows,
                results_rows=results_rows,
                odds_rows=odds_rows,
                weather_rows=weather_rows,
                injury_rows=injury_rows,
                team_stats_rows=team_stats_rows,
            )
        lifecycle_state = _normalize_text(latest_lifecycle.get("lifecycle_state"), "missing")
        asset_status = _normalize_text(
            latest_certification.get("certification_status"),
            "missing",
        )
        dataset_status = _normalize_text(
            latest_dataset.get("certification_status"),
            "missing",
        )
        alignment_statuses = [
            _normalize_text(row.get("alignment_status"))
            for row in alignment_rows
            if _normalize_text(row.get("alignment_status"))
        ]
        alignment_status = (
            "aligned"
            if alignment_statuses and all(status == "aligned" for status in alignment_statuses)
            else "blocked"
            if alignment_statuses
            else _normalize_text(
                dict((lifecycle_result or {}).get("alignment_certification_row") or {}).get(
                    "alignment_status"
                ),
                "missing",
            )
        )
        ready = (
            bool(team_stats_rows)
            and resolved_validation.get("ok")
            and resolved_join_validation.get("ok")
            and asset_status == "certified"
            and dataset_status == "certified"
            and alignment_status == "aligned"
        )
        seasons = sorted(
            {
                int(row["season"])
                for row in team_stats_rows
                if _normalize_text(row.get("season")).isdigit()
            }
        )
        source_bundle = dict(source_bundle or {})
        provider_capability = dict(source_bundle.get("provider_capability") or {})
        connector_summary = {
            "connector_id": _normalize_text(
                source_bundle.get("connector_id"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID,
            ),
            "connector_name": _normalize_text(
                source_bundle.get("connector_name"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_NAME,
            ),
            "connector_family": _normalize_text(
                source_bundle.get("connector_family"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_FAMILY,
            ),
            "provider_id": _normalize_text(
                source_bundle.get("provider"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER,
            ),
            "provider_name": _normalize_text(
                source_bundle.get("source_name"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME,
            ),
            "provider_role": _normalize_text(
                source_bundle.get("provider_role"),
                NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE,
            ),
            "execution_mode": _normalize_text(
                source_bundle.get("execution_mode"),
                NFL_TEAM_STATISTICS_CONNECTOR_EXECUTION_MODE,
            ),
            "manual_evidence_paths": list(source_bundle.get("manual_evidence_paths") or []),
            "provider_capability": provider_capability,
        }
        unresolved_blockers = list(dict.fromkeys([
            *list(resolved_validation.get("errors") or []),
            *(
                ["schedule_results_odds_weather_team_statistics_join_alignment_failed"]
                if not resolved_join_validation.get("ok", True)
                else []
            ),
            *(
                [f"alignment:{row.get('failure_reason')}" for row in alignment_rows if _normalize_text(row.get("alignment_status")) != "aligned" and _normalize_text(row.get("failure_reason"))]
            ),
            *([] if asset_status == "certified" else [f"research_asset_certification:{asset_status or 'missing'}"]),
            *([] if dataset_status == "certified" else [f"dataset_certification:{dataset_status or 'missing'}"]),
        ]))
        provenance_completeness = all(
            bool(_load_json_mapping(row.get("field_provenance_json")))
            for row in team_stats_rows
        )
        raw_acquisition_status = _normalize_text(
            (raw_acquisition_result or {}).get("status"),
            "raw_cache_ready" if raw_cache_rows else "missing",
        )
        return {
            "ok": ready,
            "status": "ready" if ready else "partial" if team_stats_rows else "missing",
            "asset_id": DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
            "asset_name": "NFL Team Statistics Snapshots",
            "raw_acquisition_status": raw_acquisition_status,
            "integrity_status": _normalize_text(
                resolved_validation.get("status"),
                "missing",
            ),
            "alignment_status": alignment_status,
            "lifecycle_state": lifecycle_state,
            "certification_status": asset_status,
            "dataset_certification_status": dataset_status,
            "row_count": len(team_stats_rows),
            "rows_produced": len(team_stats_rows),
            "coverage_seasons": seasons,
            "missing_required_fields": list(resolved_validation.get("missing_fields") or []),
            "alignment_failures": [
                _normalize_text(row.get("failure_reason"))
                for row in alignment_rows
                if _normalize_text(row.get("failure_reason"))
            ],
            "source_provider_role": {
                "provider_id": connector_summary["provider_id"],
                "provider_name": connector_summary["provider_name"],
                "provider_role": connector_summary["provider_role"],
                "manual_evidence_supported": bool(
                    provider_capability.get("manual_evidence_supported", True)
                ),
            },
            "readiness_percentage": (
                100.0
                if ready
                else round(
                    (1.0 if resolved_validation.get("ok") else 0.0) * 40.0
                    + (1.0 if resolved_join_validation.get("ok") else 0.0) * 20.0
                    + (1.0 if asset_status == "certified" else 0.0) * 20.0
                    + (1.0 if alignment_status == "aligned" else 0.0) * 10.0
                    + (1.0 if dataset_status == "certified" else 0.0) * 10.0,
                    2,
                )
            ),
            "source_bundle": source_bundle,
            "validation": resolved_validation,
            "research_asset_certifications": [dict(row) for row in certification_rows],
            "dataset_certifications": [dict(row) for row in dataset_rows],
            "research_asset_lifecycles": [dict(row) for row in lifecycle_rows],
            "research_asset_alignment_certifications": [dict(row) for row in alignment_rows],
            "normalized_rows": team_stats_rows,
            "storage": storage.health(),
            "connector_state": connector_summary,
            "field_provenance": dict((source_bundle or {}).get("field_provenance") or {}),
            "provenance_completeness": provenance_completeness,
            "coverage_planner_readiness": {
                "status": _normalize_text(
                    planner_snapshot.get("coverage_planner_readiness", {}).get("status"),
                    _normalize_text(planner_snapshot.get("planner_readiness", {}).get("status")),
                ),
                "first_production_connector_target": _normalize_text(
                    planner_snapshot.get("coverage_gap_engine", {}).get(
                        "first_production_connector_target"
                    )
                ),
                "missing_required_asset_ids": list(
                    planner_snapshot.get("coverage_gap_engine", {}).get(
                        "missing_required_asset_ids",
                        [],
                    )
                ),
                "certified_required_asset_ids": list(
                    planner_snapshot.get("coverage_gap_engine", {}).get(
                        "certified_required_asset_ids",
                        [],
                    )
                ),
                "future_asset_ids": list(
                    planner_snapshot.get("coverage_gap_engine", {}).get(
                        "future_asset_ids",
                        [],
                    )
                ),
                "minimum_schema_completion_percentage": _normalize_float(
                    planner_snapshot.get("coverage_gap_engine", {}).get(
                        "minimum_schema_completion_percentage",
                        0.0,
                    )
                ),
            },
            "coverage_planner_snapshot": planner_snapshot,
            "join_validation": resolved_join_validation,
            "unresolved_blockers": unresolved_blockers,
            "warnings": [],
        }
    finally:
        storage.close()


def build_nfl_team_statistics_research_asset_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    game_count: int = 1,
    dataset_version: str | None = None,
    connector_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    if profile.profile_id != NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROFILE_ID:
        raise ValueError(f"unexpected market profile: {profile.profile_id}")

    resolved_connector_bundle = dict(
        connector_bundle
        or build_nfl_team_statistics_connector_bundle(
            game_count=game_count,
            dataset_version=dataset_version,
        )
    )
    fixture = dict(resolved_connector_bundle.get("fixture") or {})
    raw_team_stats_rows = [
        dict(row) for row in resolved_connector_bundle.get("team_stats_rows", [])
    ]
    if not raw_team_stats_rows:
        source_bundle_tables = dict(
            (resolved_connector_bundle.get("source_bundle") or {}).get("tables") or {}
        )
        raw_team_stats_rows = [
            dict(row)
            for row in source_bundle_tables.get("nfl_team_stats_snapshots", [])
        ]
    if not raw_team_stats_rows:
        raise ValueError("NFL team statistics connector did not produce any rows")

    created_at = _normalize_text(resolved_connector_bundle.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(
        resolved_connector_bundle.get("dataset_version"),
        NFL_P0_DATASET_VERSION,
    )
    provider_capability = dict(
        resolved_connector_bundle.get("provider_capability") or {}
    )
    source_bundle = dict(resolved_connector_bundle.get("source_bundle") or {})
    source_bundle["provider_capability"] = provider_capability
    source_bundle["tables"] = dict(source_bundle.get("tables") or {})
    source_bundle["source_tables"] = dict(source_bundle.get("source_tables") or {})
    source_bundle["tables"]["nfl_team_stats_snapshots"] = [
        dict(row) for row in raw_team_stats_rows
    ]
    source_bundle["source_tables"]["nfl_team_stats_snapshots"] = [
        dict(row) for row in raw_team_stats_rows
    ]
    source_bundle["field_provenance"] = {
        "nfl_team_stats_snapshots": _field_provenance_for_row(
            raw_team_stats_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
            created_at=created_at,
        )
    }

    storage_path = Path(
        storage_path or NFL_TEAM_STATISTICS_RESEARCH_ASSET_STORAGE_PATH
    ).expanduser().resolve()
    acquisition_runtime = HistoricalDatasetAcquisitionRuntime(
        storage_path=storage_path,
        backend=backend,
    )
    try:
        raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id=profile.profile_id,
            dataset_name=NFL_TEAM_STATISTICS_RAW_ACQUISITION_DATASET_NAME,
        )
    finally:
        acquisition_runtime.close()

    normalized_team_stats_rows = normalize_nfl_p0_rows(
        "nfl_team_stats_snapshots",
        [dict(row) for row in source_bundle["tables"]["nfl_team_stats_snapshots"]],
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    team_stats_validation = validate_nfl_p0_rows(
        "nfl_team_stats_snapshots",
        normalized_team_stats_rows,
    )

    team_stats_asset_rows = [
        _build_team_stats_asset_row(
            row,
            provider_capability=provider_capability,
            source_bundle=source_bundle,
            dataset_version=dataset_version,
            created_at=created_at,
        )
        for row in normalized_team_stats_rows
    ]

    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        schedule_rows = (
            [dict(row) for row in storage.fetch("nfl_schedule", order_by="schedule_id ASC")]
            if storage.table_exists("nfl_schedule")
            else []
        )
        results_rows = (
            [dict(row) for row in storage.fetch("nfl_results", order_by="result_id ASC")]
            if storage.table_exists("nfl_results")
            else []
        )
        odds_rows = (
            [dict(row) for row in storage.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")]
            if storage.table_exists("nfl_odds_snapshots")
            else []
        )
        weather_rows = (
            [dict(row) for row in storage.fetch("nfl_weather_snapshots", order_by="weather_snapshot_id ASC")]
            if storage.table_exists("nfl_weather_snapshots")
            else []
        )
        injury_rows = (
            [dict(row) for row in storage.fetch("nfl_injury_snapshots", order_by="injury_snapshot_id ASC")]
            if storage.table_exists("nfl_injury_snapshots")
            else []
        )
        games_cert_row = _latest_certified_asset_row(
            storage,
            research_asset_id="dataset.nfl.games",
        )
        schedule_cert_row = _latest_certified_asset_row(
            storage,
            research_asset_id="dataset.sports.nfl.schedule",
        )
        results_cert_row = _latest_certified_asset_row(
            storage,
            research_asset_id="dataset.sports.nfl.results",
        )
        odds_cert_row = _latest_certified_asset_row(
            storage,
            research_asset_id="dataset.nfl.odds_snapshots",
        )
        weather_cert_row = _latest_certified_asset_row(
            storage,
            research_asset_id="dataset.nfl.weather_snapshots",
        )
        injuries_cert_row = _latest_certified_asset_row(
            storage,
            research_asset_id="dataset.nfl.injury_snapshots",
        )
    finally:
        storage.close()

    join_validation = _build_team_stats_backbone_join_validation(
        schedule_rows=schedule_rows,
        results_rows=results_rows,
        odds_rows=odds_rows,
        weather_rows=weather_rows,
        injury_rows=injury_rows,
        team_stats_rows=team_stats_asset_rows,
    )

    alignment_rows = [dict(row) for row in team_stats_asset_rows]
    for row in alignment_rows:
        row["schema_version"] = RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION
        row["lineage_version"] = dataset_version

    lifecycle_runtime = ResearchAssetLifecycleRuntime(
        storage_path=storage_path,
        backend=backend,
    )
    try:
        alignment_results: list[dict[str, Any]] = []
        alignment_status_by_row_id: dict[str, str] = {}
        for row in alignment_rows:
            row_identity = ResearchAssetIdentityContract.from_mapping(
                build_nfl_team_statistics_research_asset_identity(
                    team_stats_row=row,
                    source_bundle=source_bundle,
                    dataset_version=dataset_version,
                )
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[row],
                required_fields=tuple(
                    NFL_P0_TABLE_CONTRACTS["nfl_team_stats_snapshots"].required_fields
                ),
                required_timestamps=tuple(
                    NFL_P0_TABLE_CONTRACTS["nfl_team_stats_snapshots"].required_timestamps
                ),
                profile=profile,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=created_at,
                asset_name=row_identity.asset_name,
                asset_type=row_identity.asset_type,
                lifecycle_state="integrity_verified",
                batch_id=_normalize_text(
                    row.get("team_stats_snapshot_id"),
                    _normalize_text(row.get("team_id"), _normalize_text(row.get("game_id"))),
                ),
            )
            alignment_row = build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=profile,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                batch_id=f"{dataset_version}.team_stats.alignment.001",
            )
            alignment_validation = validate_time_entity_alignment_certification_row(
                alignment_row
            )
            if not alignment_validation["ok"]:
                raise ValueError(
                    "; ".join(
                        alignment_validation.get("validation", {}).get("errors", [])
                    )
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
                    "identity": row_identity.as_dict(),
                    "alignment_certification": alignment_contract.as_dict(),
                    "research_asset_lifecycle": {},
                    "alignment_certification_row": alignment_row,
                    "validation": alignment_validation,
                }
            )
            alignment_status_by_row_id[
                _normalize_text(row.get("team_stats_snapshot_id"))
            ] = alignment_contract.alignment_status

        for row in team_stats_asset_rows:
            row["alignment_status"] = alignment_status_by_row_id.get(
                _normalize_text(row.get("team_stats_snapshot_id")),
                row.get("alignment_status", "blocked"),
            )
            row["field_provenance_json"] = row.get("field_provenance_json") or row.get(
                "field_provenance",
                {},
            )
    finally:
        lifecycle_runtime.close()

    games_certified = _normalize_text(games_cert_row.get("certification_status")) == "certified"
    schedule_certified = _normalize_text(schedule_cert_row.get("certification_status")) == "certified"
    results_certified = _normalize_text(results_cert_row.get("certification_status")) == "certified"
    odds_certified = _normalize_text(odds_cert_row.get("certification_status")) == "certified"
    weather_certified = _normalize_text(weather_cert_row.get("certification_status")) == "certified"
    injuries_certified = _normalize_text(injuries_cert_row.get("certification_status")) == "certified"
    all_alignments_ok = bool(alignment_results) and all(bool(item.get("ok")) for item in alignment_results)

    certification_errors = list(team_stats_validation.get("errors") or [])
    if not join_validation["ok"]:
        certification_errors.append(
            "schedule_results_odds_weather_team_statistics_join_alignment_failed"
        )
    if not all_alignments_ok:
        certification_errors.append("time_entity_alignment_failed")
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

    team_stats_contract = NFL_P0_TABLE_CONTRACTS["nfl_team_stats_snapshots"]
    asset_contract = ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
        research_asset_name="NFL Team Statistics Snapshots",
        asset_category="dataset",
        asset_type="table_snapshot",
        source_table_name="nfl_team_stats_snapshots",
        required_fields=tuple(team_stats_contract.required_fields),
        required_timestamps=tuple(team_stats_contract.required_timestamps),
        point_in_time_rules=tuple(team_stats_contract.point_in_time_rules),
        description=(
            "Pregame NFL team-statistics snapshots joined to the certified schedule, "
            "results, odds, and forecast-weather backbone with explicit target-event "
            "exclusion semantics."
        ),
        priority="P0",
        required=True,
        future_asset=False,
        metadata={
            "market_profile": profile.profile_id,
            "market_family": "sports",
            "minimum_schema": True,
            "dataset_role": "team_statistics",
            "join_backbone": [
                "dataset.nfl.games",
                "dataset.sports.nfl.schedule",
                "dataset.sports.nfl.results",
                "dataset.nfl.odds_snapshots",
                "dataset.nfl.weather_snapshots",
            ],
            "optional_backbone": ["dataset.nfl.injury_snapshots"],
            "evidence_role": "pregame_team_stats_snapshot",
            "manual_evidence_supported": True,
        },
    )

    certification_validation = {
        **dict(team_stats_validation),
        "ok": not certification_errors,
        "status": "validated" if not certification_errors else "rejected",
        "error_count": len(certification_errors),
        "errors": certification_errors,
        "join_keys": [
            "team_stats_snapshot_id",
            "game_id",
            "team_id",
            "source_record_id",
            "snapshot_time",
            "team_stats_cutoff_time",
        ],
        "schedule_results_odds_weather_team_statistics_join_validation": join_validation,
        "time_entity_alignment": {
            "ok": all_alignments_ok,
            "alignment_count": len(alignment_results),
            "blocked_alignment_ids": [
                item["alignment_certification"]["alignment_certification_id"]
                for item in alignment_results
                if not item.get("ok")
            ],
        },
        "backbone_certification": {
            "dataset.nfl.games": "certified" if games_certified else "missing_or_blocked",
            "dataset.sports.nfl.schedule": "certified" if schedule_certified else "missing_or_blocked",
            "dataset.sports.nfl.results": "certified" if results_certified else "missing_or_blocked",
            "dataset.nfl.odds_snapshots": "certified" if odds_certified else "missing_or_blocked",
            "dataset.nfl.weather_snapshots": "certified" if weather_certified else "missing_or_blocked",
            "dataset.nfl.injury_snapshots": "certified" if injuries_certified else "optional_missing_or_not_required",
        },
    }

    certification_runtime = HistoricalResearchAssetCertificationRuntime(
        storage_path=storage_path,
        backend=backend,
    )
    try:
        team_stats_result = certification_runtime.certify_research_asset(
            asset_contract=asset_contract,
            rows=team_stats_asset_rows,
            profile_id=profile.profile_id,
            validation=certification_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=dataset_version,
            created_at=created_at,
            batch_id=f"{dataset_version}.team_stats.batch.001",
        )
        certification_state = _normalize_text(
            team_stats_result["research_asset_certification"].get("certification_status"),
            "missing",
        )
        for row in team_stats_asset_rows:
            row["certification_state"] = certification_state
        source_bundle["alignment_certification_ids"] = [
            item["alignment_certification"]["alignment_certification_id"]
            for item in alignment_results
        ]
        storage_columns = set(certification_runtime.store.table_columns("nfl_team_stats_snapshots"))
        for row in team_stats_asset_rows:
            storage_row = {
                key: value
                for key, value in row.items()
                if key in storage_columns
            }
            certification_runtime.store.upsert(
                "nfl_team_stats_snapshots",
                storage_row,
                key_columns=("team_stats_snapshot_id",),
            )
        dataset_asset_rows = [
            row
            for row in (
                games_cert_row,
                schedule_cert_row,
                results_cert_row,
                odds_cert_row,
                weather_cert_row,
                team_stats_result["research_asset_certification"],
            )
            if row
        ]
        dataset_row = build_historical_dataset_certification_row(
            profile=profile,
            dataset_version=dataset_version,
            batch_id=f"{dataset_version}.team_stats.batch.001",
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=dataset_asset_rows,
        )
        certification_runtime.store.upsert(
            "historical_certifications",
            dataset_row,
            key_columns=("certification_id",),
        )
    finally:
        certification_runtime.close()

    lifecycle_runtime = ResearchAssetLifecycleRuntime(
        storage_path=storage_path,
        backend=backend,
    )
    try:
        _promote_team_stats_asset_lifecycle(
            lifecycle_runtime=lifecycle_runtime,
            identity=build_nfl_team_statistics_dataset_identity(
                source_bundle=source_bundle,
                dataset_version=dataset_version,
            ),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            normalized_rows=team_stats_asset_rows,
            alignment_results=alignment_results,
            certification_result=team_stats_result,
            dataset_result=dataset_row,
            asset_label="NFL team statistics",
            future_joins=["player_stats", "betting_splits", "feature_snapshots"],
        )
        coverage_planner_snapshot = build_research_asset_coverage_planner_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile.profile_id,
        )
        readiness_snapshot = build_nfl_team_statistics_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=fixture or resolved_connector_bundle,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=team_stats_asset_rows,
            validation=certification_validation,
            certification_result=team_stats_result,
            dataset_result=dataset_row,
            lifecycle_result=alignment_results[-1] if alignment_results else {},
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
            "normalized_rows": team_stats_asset_rows,
            "validation": certification_validation,
            "research_asset_certification": team_stats_result["research_asset_certification"],
            "dataset_certification": dataset_row,
            "alignment_results": alignment_results,
            "lifecycle_alignment": alignment_results[-1] if alignment_results else {},
            "join_validation": join_validation,
            "coverage_planner_snapshot": coverage_planner_snapshot,
            "readiness_snapshot": readiness_snapshot,
        }
    finally:
        lifecycle_runtime.close()


def get_nfl_team_statistics_research_asset_snapshot_for_dashboard(
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
    """Return the canonical NFL team statistics research asset readiness snapshot."""
    try:
        return build_nfl_team_statistics_research_asset_dashboard_snapshot(
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
            "status": "nfl_team_statistics_research_asset_snapshot_error",
            "asset_id": DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID,
            "asset_name": "NFL Team Statistics Snapshots",
            "raw_acquisition_status": "missing",
            "integrity_status": "missing",
            "alignment_status": "missing",
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
            "provenance_completeness": False,
            "coverage_planner_readiness": {},
            "coverage_planner_snapshot": {},
            "join_validation": {},
            "storage": {},
            "unresolved_blockers": [],
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_NFL_TEAM_STATISTICS_RESEARCH_ASSET_ID",
    "NFL_TEAM_STATISTICS_RAW_ACQUISITION_DATASET_NAME",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_ID",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_CONNECTOR_NAME",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_DATASET_NAME",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_LIFECYCLE_VERSION",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROFILE_ID",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_NAME",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_PROVIDER_ROLE",
    "NFL_TEAM_STATISTICS_RESEARCH_ASSET_STORAGE_PATH",
    "build_nfl_team_statistics_connector_bundle",
    "build_nfl_team_statistics_provider_capability",
    "build_nfl_team_statistics_research_asset_dashboard_snapshot",
    "build_nfl_team_statistics_research_asset_identity",
    "build_nfl_team_statistics_research_asset_population",
    "get_nfl_team_statistics_research_asset_snapshot_for_dashboard",
]
