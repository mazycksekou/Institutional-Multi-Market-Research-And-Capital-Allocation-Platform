from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.connectors.odds_data.nfl import (
    NFL_ODDS_CONNECTOR_EXECUTION_MODE,
    NFL_ODDS_CONNECTOR_ID,
    NFL_ODDS_CONNECTOR_NAME,
    NFL_ODDS_PROVIDER_ID,
    NFL_ODDS_PROVIDER_NAME,
    NFL_ODDS_PROVIDER_ROLE,
    NFL_ODDS_RESEARCH_ASSET_ID,
    build_nfl_odds_connector_bundle,
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
from src.market_intelligence.research_asset_coverage_planner import (
    build_research_asset_coverage_planner_snapshot,
)


DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID = NFL_ODDS_RESEARCH_ASSET_ID
NFL_ODDS_RESEARCH_ASSET_STORAGE_PATH = get_runtime_data_path(
    "nfl_odds_research_asset",
    "canonical_data.sqlite",
)
NFL_ODDS_RESEARCH_ASSET_DATASET_NAME = "nfl_odds_research_asset"
NFL_ODDS_RAW_ACQUISITION_DATASET_NAME = "nfl_odds_raw_acquisition_cache"
NFL_ODDS_RESEARCH_ASSET_PROVIDER = NFL_ODDS_PROVIDER_ID
NFL_ODDS_RESEARCH_ASSET_PROVIDER_NAME = NFL_ODDS_PROVIDER_NAME
NFL_ODDS_RESEARCH_ASSET_PROVIDER_ROLE = NFL_ODDS_PROVIDER_ROLE
NFL_ODDS_RESEARCH_ASSET_SOURCE_ROLE = NFL_ODDS_PROVIDER_ID
NFL_ODDS_PROVIDER_SOURCE_TYPE = "deterministic_fixture"
NFL_ODDS_RESEARCH_ASSET_PROFILE_ID = "sports:nfl"
NFL_ODDS_RESEARCH_ASSET_LIFECYCLE_VERSION = "v1"
NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID = NFL_ODDS_CONNECTOR_ID
NFL_ODDS_RESEARCH_ASSET_CONNECTOR_NAME = NFL_ODDS_CONNECTOR_NAME


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
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


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

    return json.dumps(value, default=default, sort_keys=True, ensure_ascii=False)


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


def _odds_rows(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    tables = fixture.get("tables") or {}
    if not isinstance(tables, Mapping):
        return []
    rows = tables.get("nfl_odds_snapshots") or []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _field_provenance_for_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    created_at: str,
) -> dict[str, Any]:
    source_provider = _normalize_text(provider_capability.get("provider_id"), NFL_ODDS_PROVIDER_ID)
    source_provider_name = _normalize_text(provider_capability.get("provider_name"), NFL_ODDS_PROVIDER_NAME)
    quality = _normalize_text(provider_capability.get("quality_tier"), "high_priority_adapter")
    lineage_id = _stable_id(
        "nfl_odds_field_lineage",
        source_bundle_id,
        _normalize_text(row.get("odds_snapshot_id") or row.get("game_id") or "row"),
    )
    field_map = {
        "odds_snapshot_id": "odds_snapshot_id",
        "game_id": "game_id",
        "event_id": "game_id",
        "season": "season",
        "week": "week",
        "league": "league",
        "sport": "sport",
        "home_team": "home_team",
        "away_team": "away_team",
        "kickoff_time": "kickoff_time",
        "book": "book",
        "market": "market",
        "selection": "selection",
        "line_value": "line_value",
        "american_odds": "american_odds",
        "decimal_odds": "decimal_odds",
        "implied_probability": "implied_probability",
        "market_label": "market_label",
        "freshness_score": "freshness_score",
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
    row_id = _normalize_text(row.get("odds_snapshot_id") or row.get("game_id") or "row")
    for field_name, source_field_name in field_map.items():
        provenance[field_name] = {
            "source_provider": source_provider,
            "source_provider_name": source_provider_name,
            "source_field_name": source_field_name,
            "raw_field_name": source_field_name,
            "acquisition_timestamp": created_at,
            "raw_payload_reference": f"{source_bundle_id}:nfl_odds:{row_id}:{source_field_name}",
            "lineage_id": lineage_id,
            "confidence": 1.0,
            "quality": quality,
        }
    return provenance


def build_nfl_odds_provider_capability(
    *,
    dataset_version: str | None = None,
    game_count: int = 1,
) -> dict[str, Any]:
    source_entry = {
        "source_id": NFL_ODDS_PROVIDER_ID,
        "source_name": NFL_ODDS_PROVIDER_NAME,
        "source_family": "odds_data",
        "source_category": "sports",
        "source_access_type": "free_key",
        "coverage": {
            "historical": True,
            "odds": True,
            "spread": True,
            "moneyline": True,
            "total": True,
            "pre_kickoff_snapshots": True,
            "decision_time_snapshots": True,
        },
        "freshness": {"expected_update_cadence": "near_live"},
        "limits": {"rate_limit_known": True, "throttle_required": True},
        "legal_terms": {"requires_manual_review": False},
        "model_mapping": {
            "model_inputs_supported": [
                "game_id",
                "event_id",
                "season",
                "week",
                "book",
                "market",
                "selection",
                "line_value",
                "american_odds",
                "decimal_odds",
                "implied_probability",
                "source_snapshot_time",
                "snapshot_time",
                "decision_time",
                "kickoff_time",
            ],
            "historical_backfill_fields_available": [
                "line_value",
                "american_odds",
                "decimal_odds",
                "implied_probability",
            ],
            "outcome_fields_available": ["line_move", "clv", "profit_loss"],
            "join_keys": ["game_id", "book", "market", "selection", "snapshot_time"],
        },
        "current_phase_allowed": True,
        "approval_status": "approved_open_metadata",
        "source_aliases": [NFL_ODDS_PROVIDER_ID, "theoddsapi"],
    }
    from src.data.source_quality_scoring import score_source

    source_quality = score_source(
        source_entry,
        required_inputs=[
            "game_id",
            "book",
            "market",
            "selection",
            "line_value",
            "american_odds",
            "decimal_odds",
            "implied_probability",
            "snapshot_time",
            "decision_time",
            "kickoff_time",
        ],
    )
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    odds_rows = _odds_rows(fixture)
    if not odds_rows:
        raise ValueError("NFL odds connector did not produce any odds rows")
    supported_fields = sorted({str(key) for row in odds_rows for key in row.keys()})
    return {
        "provider_id": NFL_ODDS_PROVIDER_ID,
        "provider_name": NFL_ODDS_PROVIDER_NAME,
        "provider_role": NFL_ODDS_PROVIDER_ROLE,
        "connector_id": NFL_ODDS_CONNECTOR_ID,
        "connector_name": NFL_ODDS_CONNECTOR_NAME,
        "connector_family": "odds_data",
        "source_id": NFL_ODDS_PROVIDER_ID,
        "source_name": NFL_ODDS_PROVIDER_NAME,
        "source_family": "odds_data",
        "source_access_type": "free_key",
        "supported_assets": [NFL_ODDS_RESEARCH_ASSET_ID],
        "supported_fields": supported_fields,
        "supported_markets": ["sports:nfl", "odds_snapshot", "spread", "moneyline", "total"],
        "historical_depth": "historical",
        "update_frequency": "near_live / historical",
        "point_in_time_safe": True,
        "licensing_notes": "Fixture-backed offline mode preserves evidence; live odds use would require the provider terms review already documented in discovery.",
        "cost_class": "free_key",
        "certification_readiness": "ready",
        "quality_score": round(float(source_quality.get("current_phase_usability_score") or source_quality.get("coverage_score") or 0.0) / 100.0, 4),
        "quality_tier": source_quality.get("quality_tier", "high_priority_adapter"),
        "source_aliases": source_entry["source_aliases"],
        "verification_provider_ids": ["manual_export", "odds_snapshot_review"],
        "fallback_provider_ids": ["local_fixture", "manual_export"],
        "source_quality": source_quality,
    }


def _connector_row(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    execution_mode: str,
) -> dict[str, Any]:
    payload = dict(row)
    provider_id = _normalize_text(provider_capability.get("provider_id"), NFL_ODDS_PROVIDER_ID)
    provider_name = _normalize_text(provider_capability.get("provider_name"), NFL_ODDS_PROVIDER_NAME)
    provider_role = _normalize_text(provider_capability.get("provider_role"), NFL_ODDS_PROVIDER_ROLE)
    connector_id = _normalize_text(provider_capability.get("connector_id"), NFL_ODDS_CONNECTOR_ID)
    connector_name = _normalize_text(provider_capability.get("connector_name"), NFL_ODDS_CONNECTOR_NAME)
    connector_family = _normalize_text(provider_capability.get("connector_family"), "odds_data")
    payload.update(
        {
            "source_name": provider_name,
            "source_type": NFL_ODDS_PROVIDER_SOURCE_TYPE,
            "source_key": NFL_ODDS_PROVIDER_ID,
            "provider": provider_id,
            "provider_name": provider_name,
            "provider_role": provider_role,
            "connector_id": connector_id,
            "connector_name": connector_name,
            "connector_family": connector_family,
            "connector_role": "production_connector",
            "execution_mode": execution_mode,
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_table": "nfl_odds_snapshots",
            "acquisition_timestamp": _normalize_text(source_bundle.get("acquisition_timestamp"), _utc_now_iso()),
            "provider_capability": dict(provider_capability),
        }
    )
    return payload


def build_nfl_odds_connector_bundle(
    *,
    game_count: int = 1,
    dataset_version: str | None = None,
    execution_mode: str = NFL_ODDS_CONNECTOR_EXECUTION_MODE,
) -> dict[str, Any]:
    fixture = build_nfl_p0_fixture(
        game_count=max(int(game_count or 1), 1),
        dataset_version=dataset_version or NFL_P0_DATASET_VERSION,
    )
    raw_odds_rows = _odds_rows(fixture)
    if not raw_odds_rows:
        raise ValueError("NFL odds connector did not produce any odds rows")

    created_at = _normalize_text(fixture.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(dataset_version or fixture.get("dataset_version"), NFL_P0_DATASET_VERSION)
    source_bundle_id = _stable_id(
        "nfl_odds_connector_bundle",
        dataset_version,
        raw_odds_rows[0].get("game_id"),
        raw_odds_rows[0].get("season"),
        raw_odds_rows[0].get("week"),
        execution_mode,
    )
    provider_capability = build_nfl_odds_provider_capability(dataset_version=dataset_version, game_count=max(int(game_count or 1), 1))
    odds_rows = [
        _connector_row(
            row,
            provider_capability=provider_capability,
            source_bundle={
                "source_bundle_id": source_bundle_id,
                "acquisition_timestamp": created_at,
            },
            execution_mode=execution_mode,
        )
        for row in raw_odds_rows
    ]
    field_provenance = {
        "nfl_odds_snapshots": _field_provenance_for_row(
            odds_rows[0],
            provider_capability=provider_capability,
            source_bundle_id=source_bundle_id,
            created_at=created_at,
        )
    }
    source_bundle = {
        "dataset_id": "dataset.nfl.odds_snapshots.raw_acquisition_cache",
        "dataset_name": "nfl_odds_raw_acquisition_cache",
        "source_name": provider_capability["provider_name"],
        "source_type": NFL_ODDS_PROVIDER_SOURCE_TYPE,
        "source_key": NFL_ODDS_PROVIDER_ID,
        "source_family": provider_capability["source_family"],
        "source_access_type": provider_capability["source_access_type"],
        "provider": provider_capability["provider_id"],
        "provider_name": provider_capability["provider_name"],
        "provider_role": provider_capability["provider_role"],
        "provider_sources": [provider_capability["provider_id"]],
        "provider_versions": [dataset_version],
        "source_bundle_id": source_bundle_id,
        "acquisition_timestamp": created_at,
        "source_snapshot_time": _normalize_text(odds_rows[0].get("source_snapshot_time"), created_at),
        "result_timestamp": _normalize_text(odds_rows[0].get("decision_time"), _normalize_text(odds_rows[0].get("snapshot_time"), created_at)),
        "source_market_id": _normalize_text(odds_rows[0].get("game_id"), _normalize_text(odds_rows[0].get("odds_snapshot_id"), "nfl_odds")),
        "source_selection_id": _normalize_text(odds_rows[0].get("selection"), "odds"),
        "dataset_version": dataset_version,
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "source_tables": {"nfl_odds_snapshots": odds_rows},
        "tables": {"nfl_odds_snapshots": odds_rows},
        "source_file": "the_odds_api_fixture.csv",
        "update_frequency": "near_live",
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
        "status": "connector_ready" if execution_mode == NFL_ODDS_CONNECTOR_EXECUTION_MODE else "connector_live_ready",
        "execution_mode": execution_mode,
        "connector_id": provider_capability["connector_id"],
        "connector_name": provider_capability["connector_name"],
        "provider_capability": provider_capability,
        "field_provenance": field_provenance,
        "fixture": fixture,
        "odds_rows": odds_rows,
        "source_bundle": source_bundle,
        "created_at": created_at,
        "dataset_version": dataset_version,
        "odds_row_count": len(odds_rows),
        "notes": [
            "The odds connector path is production-shaped but runs in deterministic offline mode for tests and local validation.",
            "The shared raw acquisition cache remains the first persistent hop before normalization and certification.",
            "Field-level provenance is preserved for each pregame odds snapshot row.",
        ],
    }


def _build_odds_field_provenance(
    row: Mapping[str, Any],
    *,
    provider_capability: Mapping[str, Any],
    source_bundle_id: str,
    created_at: str,
) -> dict[str, Any]:
    return _field_provenance_for_row(
        row,
        provider_capability=provider_capability,
        source_bundle_id=source_bundle_id,
        created_at=created_at,
    )


def _build_odds_asset_row(
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
    market = _normalize_text(payload.get("market"), "odds_snapshot")
    selection = _normalize_text(payload.get("selection"), "odds")
    odds_snapshot_id = _normalize_text(payload.get("odds_snapshot_id"), _stable_id("nfl_odds_snapshot", game_id, market, selection, kickoff_time))
    provider_name = _normalize_text(source_bundle.get("source_name"), NFL_ODDS_PROVIDER_NAME)
    payload.update(
        {
            "asset_id": DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID,
            "asset_family": "dataset",
            "asset_name": "NFL Odds Snapshots",
            "asset_type": "odds_snapshot",
            "market_profile": NFL_ODDS_RESEARCH_ASSET_PROFILE_ID,
            "league": _normalize_text(payload.get("league"), "NFL"),
            "sport": "football",
            "event_id": _normalize_text(payload.get("event_id"), game_id),
            "market_id": odds_snapshot_id,
            "selection": selection,
            "team_id": _normalize_text(payload.get("team_id"), _normalize_text(payload.get("home_team"), "")),
            "participant_id": _normalize_text(payload.get("participant_id"), ""),
            "season": _normalize_text(payload.get("season")),
            "week": _normalize_text(payload.get("week")),
            "scheduled_time": kickoff_time,
            "completion_timestamp": _normalize_text(payload.get("completion_timestamp"), kickoff_time),
            "provider_timestamp": _normalize_text(payload.get("provider_timestamp"), _normalize_text(payload.get("source_snapshot_time"), kickoff_time)),
            "source_market_id": _normalize_text(payload.get("source_market_id"), odds_snapshot_id),
            "source_selection_id": _normalize_text(payload.get("source_selection_id"), selection),
            "connector": _normalize_text(source_bundle.get("connector_id"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID),
            "provider": _normalize_text(source_bundle.get("provider"), NFL_ODDS_RESEARCH_ASSET_SOURCE_ROLE),
            "source_name": provider_name,
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_ODDS_PROVIDER_SOURCE_TYPE),
            "source_key": _normalize_text(source_bundle.get("source_key"), NFL_ODDS_PROVIDER_ID),
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text(source_bundle.get("connector_name"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text(source_bundle.get("connector_family"), "odds_data"),
            "provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_ODDS_RESEARCH_ASSET_PROVIDER_ROLE),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_ODDS_CONNECTOR_EXECUTION_MODE),
            "field_provenance": _build_odds_field_provenance(
                payload,
                provider_capability=provider_capability,
                source_bundle_id=_normalize_text(source_bundle.get("source_bundle_id")),
                created_at=created_at,
            ),
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "dataset_version": dataset_version,
            "schema_version": NFL_P0_SCHEMA_VERSION,
            "version_id": dataset_version,
            "lineage_version": _normalize_text(dataset_version, NFL_ODDS_RESEARCH_ASSET_LIFECYCLE_VERSION),
        }
    )
    return payload


def _build_odds_schedule_results_join_validation(
    *,
    schedule_rows: Sequence[Mapping[str, Any]],
    results_rows: Sequence[Mapping[str, Any]],
    odds_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    schedule_index = {_normalize_text(row.get("game_id")): dict(row) for row in schedule_rows if _normalize_text(row.get("game_id"))}
    results_index = {_normalize_text(row.get("game_id")): dict(row) for row in results_rows if _normalize_text(row.get("game_id"))}
    missing_schedule_rows: list[str] = []
    missing_results_rows: list[str] = []
    mismatches: list[dict[str, Any]] = []
    timing_issues: list[dict[str, Any]] = []

    for row in odds_rows:
        game_id = _normalize_text(row.get("game_id"))
        schedule_row = schedule_index.get(game_id)
        results_row = results_index.get(game_id)
        if not schedule_row:
            missing_schedule_rows.append(game_id)
            continue
        if not results_row:
            missing_results_rows.append(game_id)
            continue

        kickoff_time = _parse_iso(schedule_row.get("kickoff_time") or row.get("kickoff_time"))
        source_snapshot_time = _parse_iso(row.get("source_snapshot_time") or row.get("snapshot_time"))
        decision_time = _parse_iso(row.get("decision_time") or row.get("snapshot_time"))
        completion_time = _parse_iso(results_row.get("completion_timestamp") or results_row.get("final_scored_at") or results_row.get("game_time"))
        if _normalize_text(schedule_row.get("home_team")) != _normalize_text(row.get("home_team")):
            mismatches.append({"game_id": game_id, "field": "home_team"})
        if _normalize_text(schedule_row.get("away_team")) != _normalize_text(row.get("away_team")):
            mismatches.append({"game_id": game_id, "field": "away_team"})
        if kickoff_time is not None and source_snapshot_time is not None and source_snapshot_time > kickoff_time:
            timing_issues.append({"game_id": game_id, "field": "source_snapshot_time"})
        if kickoff_time is not None and decision_time is not None and decision_time > kickoff_time:
            timing_issues.append({"game_id": game_id, "field": "decision_time"})
        if kickoff_time is not None and completion_time is not None and completion_time < kickoff_time:
            timing_issues.append({"game_id": game_id, "field": "completion_timestamp"})

    ok = not missing_schedule_rows and not missing_results_rows and not mismatches and not timing_issues and bool(odds_rows)
    return {
        "ok": ok,
        "status": "aligned" if ok else "blocked",
        "matched_rows": len(odds_rows) - len(missing_schedule_rows) - len(missing_results_rows),
        "missing_schedule_rows": missing_schedule_rows,
        "missing_results_rows": missing_results_rows,
        "mismatches": mismatches,
        "timing_issues": timing_issues,
        "odds_row_count": len(odds_rows),
        "schedule_row_count": len(schedule_rows),
        "results_row_count": len(results_rows),
    }


def _latest_certified_asset_row(
    storage,
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


def _build_odds_research_asset_identity(
    *,
    odds_row: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    payload = dict(odds_row)
    game_id = _normalize_text(payload.get("game_id"), _normalize_text(payload.get("event_id")))
    market_id = _normalize_text(payload.get("market_id"), _normalize_text(payload.get("odds_snapshot_id"), game_id))
    return build_research_asset_identity_contract(
        asset_id=DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID,
        asset_family="dataset",
        market_profile=profile.profile_id,
        market=_normalize_text(payload.get("market"), "nfl_p0"),
        league=_normalize_text(payload.get("league"), _normalize_text(profile.metadata.get("league"), "NFL")),
        sport=_normalize_text(payload.get("sport"), _normalize_text(profile.metadata.get("sport"), "football")),
        season=_normalize_text(payload.get("season")),
        week_or_date=_normalize_text(payload.get("week")),
        event_id=_normalize_text(payload.get("event_id"), game_id),
        market_id=market_id,
        selection=_normalize_text(payload.get("selection"), "odds"),
        provider=_normalize_text(source_bundle.get("provider"), NFL_ODDS_RESEARCH_ASSET_SOURCE_ROLE),
        connector=_normalize_text(source_bundle.get("connector_id"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID),
        schema_version=_normalize_text(payload.get("schema_version"), NFL_P0_SCHEMA_VERSION),
        lineage_version=_normalize_text(dataset_version, NFL_ODDS_RESEARCH_ASSET_LIFECYCLE_VERSION),
        asset_name="NFL Odds Snapshots",
        asset_type="odds_snapshot",
        participant_id="",
        team_id=_normalize_text(payload.get("team_id"), _normalize_text(payload.get("home_team"), "")),
        game_id=game_id,
        market_type=_normalize_text(payload.get("market_type"), "odds_snapshot"),
        metadata={
            "source_bundle_id": _normalize_text(source_bundle.get("source_bundle_id")),
            "source_name": _normalize_text(source_bundle.get("source_name"), NFL_ODDS_RESEARCH_ASSET_PROVIDER_NAME),
            "source_type": _normalize_text(source_bundle.get("source_type"), NFL_ODDS_PROVIDER_SOURCE_TYPE),
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text(source_bundle.get("connector_name"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text(source_bundle.get("connector_family"), "odds_data"),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_ODDS_CONNECTOR_EXECUTION_MODE),
            "dataset_version": dataset_version,
            "game_id": game_id,
            "market_id": market_id,
            "selection": _normalize_text(payload.get("selection"), "odds"),
            "provider_capability": dict(source_bundle.get("provider_capability") or {}),
        },
    ).as_dict()


def _promote_odds_asset_lifecycle(
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
        notes={"provider_role": _normalize_text(source_bundle.get("provider_role"), NFL_ODDS_RESEARCH_ASSET_PROVIDER_ROLE)},
    )
    lifecycle_runtime.record_lifecycle_state(
        identity=identity,
        lifecycle_state="connector_mapped",
        lifecycle_reason=f"connector mapped for {asset_label} research asset",
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
        created_at=created_at,
        notes={
            "connector_id": _normalize_text(source_bundle.get("connector_id"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode"), NFL_ODDS_CONNECTOR_EXECUTION_MODE),
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
    alignment_status = _normalize_text(alignment_result.get("alignment_certification", {}).get("alignment_status"))
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
        lifecycle_reason=f"{asset_label} rows normalized into the canonical nfl_odds storage table",
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


def build_nfl_odds_research_asset_dashboard_snapshot(
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
        odds_rows = [dict(row) for row in normalized_rows or storage.fetch("nfl_odds_snapshots", order_by="odds_snapshot_id ASC")]
        schedule_rows = [dict(row) for row in storage.fetch("nfl_schedule", order_by="schedule_id ASC")] if storage.table_exists("nfl_schedule") else []
        results_rows = [dict(row) for row in storage.fetch("nfl_results", order_by="result_id ASC")] if storage.table_exists("nfl_results") else []
        resolved_join_validation = dict(
            join_validation
            or _build_odds_schedule_results_join_validation(
                schedule_rows=schedule_rows,
                results_rows=results_rows,
                odds_rows=odds_rows,
            )
        )
        certification_rows = [
            dict(row)
            for row in storage.fetch(
                "historical_research_asset_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID],
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
                params=[DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID],
                order_by="updated_at ASC",
            )
        ] if storage.table_exists("research_asset_lifecycles") else []
        alignment_rows = [
            dict(row)
            for row in storage.fetch(
                "research_asset_alignment_certifications",
                where="research_asset_id = ?",
                params=[DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID],
                order_by="alignment_certification_id ASC",
            )
        ] if storage.table_exists("research_asset_alignment_certifications") else []
        odds_validation = dict(validation or validate_nfl_p0_rows("nfl_odds_snapshots", odds_rows))
        asset_rows = certification_rows
        asset_status = _normalize_text(asset_rows[-1].get("certification_status"), "missing") if asset_rows else "missing"
        lifecycle_state = _normalize_text(lifecycle_rows[-1].get("lifecycle_state"), "missing") if lifecycle_rows else "missing"
        alignment_status = _normalize_text(alignment_rows[-1].get("alignment_status"), "missing") if alignment_rows else "missing"
        ready = bool(
            odds_rows
            and odds_validation.get("ok")
            and resolved_join_validation.get("ok")
            and asset_rows
            and asset_status == "certified"
            and dataset_rows
            and _normalize_text(dataset_rows[-1].get("certification_status")) == "certified"
            and lifecycle_state == "feature_ready"
            and alignment_status == "aligned"
        )
        seasons = sorted({str(row.get("season")) for row in odds_rows if _normalize_text(row.get("season"))})
        source_summary = {
            "source_name": _normalize_text((certification_result or {}).get("source_name") or (source_bundle or {}).get("source_name") or (fixture or {}).get("source_name"), NFL_ODDS_PROVIDER_NAME),
            "source_type": _normalize_text((certification_result or {}).get("source_type") or (source_bundle or {}).get("source_type") or (fixture or {}).get("source_type"), NFL_ODDS_PROVIDER_SOURCE_TYPE),
            "source_key": _normalize_text((certification_result or {}).get("source_key") or (source_bundle or {}).get("source_key") or (fixture or {}).get("source_key"), NFL_ODDS_PROVIDER_ID),
            "provider": _normalize_text((certification_result or {}).get("provider") or (source_bundle or {}).get("provider") or (fixture or {}).get("provider"), NFL_ODDS_RESEARCH_ASSET_SOURCE_ROLE),
        }
        connector_summary = {
            "connector_id": _normalize_text((source_bundle or {}).get("connector_id"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID),
            "connector_name": _normalize_text((source_bundle or {}).get("connector_name"), NFL_ODDS_RESEARCH_ASSET_CONNECTOR_NAME),
            "connector_family": _normalize_text((source_bundle or {}).get("connector_family"), "odds_data"),
            "execution_mode": _normalize_text((source_bundle or {}).get("execution_mode"), NFL_ODDS_CONNECTOR_EXECUTION_MODE),
        }
        planner_snapshot = dict(coverage_planner_snapshot or {})
        return {
            "ok": ready,
            "status": "ready" if ready else "partial" if odds_rows else "missing",
            "asset_id": DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID,
            "asset_name": "NFL Odds Snapshots",
            "lifecycle_state": lifecycle_state,
            "certification_status": asset_status,
            "dataset_certification_status": _normalize_text(dataset_rows[-1].get("certification_status"), "missing") if dataset_rows else "missing",
            "row_count": len(odds_rows),
            "rows_produced": len(odds_rows),
            "coverage_seasons": seasons,
            "missing_required_fields": list((odds_validation.get("missing_fields") or [])),
            "alignment_failures": list((alignment_rows[-1].get("alignment_failures") or [])) if alignment_rows else [],
            "source_provider_role": source_summary,
            "readiness_percentage": 100.0 if ready else round((1.0 if odds_validation.get("ok") else 0.0) * 70.0 + (1.0 if asset_status == "certified" else 0.0) * 15.0 + (1.0 if alignment_status == "aligned" else 0.0) * 15.0, 2),
            "source_bundle": dict(source_bundle or {}),
            "validation": odds_validation,
            "research_asset_certifications": certification_rows,
            "dataset_certifications": dataset_rows,
            "research_asset_lifecycles": lifecycle_rows,
            "research_asset_alignment_certifications": alignment_rows,
            "normalized_rows": odds_rows,
            "storage": storage.health(),
            "connector_state": connector_summary,
            "field_provenance": dict((source_bundle or {}).get("field_provenance") or {}),
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


def build_nfl_odds_research_asset_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    game_count: int = 1,
    dataset_version: str | None = None,
) -> dict[str, Any]:
    profile = get_nfl_p0_market_profile()
    if profile.profile_id != NFL_ODDS_RESEARCH_ASSET_PROFILE_ID:
        raise ValueError(f"unexpected market profile: {profile.profile_id}")

    connector_bundle = build_nfl_odds_connector_bundle(game_count=game_count, dataset_version=dataset_version)
    fixture = dict(connector_bundle.get("fixture") or {})
    raw_odds_rows = [dict(row) for row in connector_bundle.get("odds_rows", [])]
    if not raw_odds_rows:
        raise ValueError("NFL odds connector did not produce any odds rows")

    created_at = _normalize_text(connector_bundle.get("created_at"), _utc_now_iso())
    dataset_version = _normalize_text(connector_bundle.get("dataset_version"), NFL_P0_DATASET_VERSION)
    provider_capability = dict(connector_bundle.get("provider_capability") or {})
    source_bundle = dict(connector_bundle.get("source_bundle") or {})
    source_bundle["field_provenance"] = dict(connector_bundle.get("field_provenance") or {})

    storage_path = Path(storage_path or NFL_ODDS_RESEARCH_ASSET_STORAGE_PATH).expanduser().resolve()
    acquisition_runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path, backend=backend)
    try:
        raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id=profile.profile_id,
            dataset_name=NFL_ODDS_RAW_ACQUISITION_DATASET_NAME,
        )
    finally:
        acquisition_runtime.close()

    storage_rows = {
        "nfl_odds_snapshots": [dict(row) for row in source_bundle.get("tables", {}).get("nfl_odds_snapshots", raw_odds_rows)],
    }
    normalized_odds_rows = normalize_nfl_p0_rows(
        "nfl_odds_snapshots",
        storage_rows["nfl_odds_snapshots"],
        dataset_version=dataset_version,
        created_at=created_at,
        updated_at=created_at,
    )
    odds_validation = validate_nfl_p0_rows("nfl_odds_snapshots", normalized_odds_rows)

    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        storage_columns = set(storage.table_columns("nfl_odds_snapshots"))
        storage_rows_to_write = [{key: value for key, value in row.items() if key in storage_columns} for row in normalized_odds_rows]
        for row in storage_rows_to_write:
            storage.upsert("nfl_odds_snapshots", row, key_columns=("odds_snapshot_id",))
    finally:
        storage.close()

    odds_asset_rows = [
        _build_odds_asset_row(
            row,
            provider_capability=provider_capability,
            source_bundle=source_bundle,
            dataset_version=dataset_version,
            created_at=created_at,
        )
        for row in normalized_odds_rows
    ]

    asset_contract = ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID,
        research_asset_name="NFL Odds Snapshots",
        asset_category="dataset",
        asset_type="table_snapshot",
        source_table_name="nfl_odds_snapshots",
        required_fields=tuple(NFL_P0_TABLE_CONTRACTS["nfl_odds_snapshots"].required_fields),
        required_timestamps=tuple(NFL_P0_TABLE_CONTRACTS["nfl_odds_snapshots"].required_timestamps),
        point_in_time_rules=tuple(NFL_P0_TABLE_CONTRACTS["nfl_odds_snapshots"].point_in_time_rules),
        description="Pregame NFL odds snapshots joined to the certified schedule and results backbone.",
        priority="P0",
        required=True,
        future_asset=False,
        metadata={
            "market_profile": profile.profile_id,
            "market_family": "sports",
            "minimum_schema": True,
            "dataset_role": "odds",
            "join_backbone": ["dataset.nfl.games", "dataset.sports.nfl.schedule", "dataset.sports.nfl.results"],
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
        results_rows = [
            dict(row)
            for row in certification_runtime.store.fetch(
                "nfl_results",
                order_by="result_id ASC",
            )
        ] if certification_runtime.store.table_exists("nfl_results") else []
        games_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.nfl.games")
        schedule_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.sports.nfl.schedule")
        results_cert_row = _latest_certified_asset_row(certification_runtime.store, research_asset_id="dataset.sports.nfl.results")
        join_validation = _build_odds_schedule_results_join_validation(
            schedule_rows=schedule_rows,
            results_rows=results_rows,
            odds_rows=odds_asset_rows,
        )
        games_certified = _normalize_text(games_cert_row.get("certification_status")) == "certified"
        schedule_certified = _normalize_text(schedule_cert_row.get("certification_status")) == "certified"
        results_certified = _normalize_text(results_cert_row.get("certification_status")) == "certified"
        certification_errors = list(odds_validation.get("errors") or [])
        if not join_validation["ok"]:
            certification_errors.append("schedule_results_join_alignment_failed")
        if not games_certified:
            certification_errors.append("games_backbone_not_certified")
        if not schedule_certified:
            certification_errors.append("schedule_backbone_not_certified")
        if not results_certified:
            certification_errors.append("results_backbone_not_certified")
        certification_errors = list(dict.fromkeys(certification_errors))
        certification_validation = {
            **dict(odds_validation),
            "ok": not certification_errors,
            "status": "validated" if not certification_errors else "rejected",
            "error_count": len(certification_errors),
            "errors": certification_errors,
            "join_keys": ["game_id", "book", "market", "selection", "snapshot_time"],
            "schedule_results_join_validation": join_validation,
            "backbone_certification": {
                "dataset.nfl.games": "certified" if games_certified else "missing_or_blocked",
                "dataset.sports.nfl.schedule": "certified" if schedule_certified else "missing_or_blocked",
                "dataset.sports.nfl.results": "certified" if results_certified else "missing_or_blocked",
            },
        }
        odds_result = certification_runtime.certify_research_asset(
            asset_contract=asset_contract,
            rows=odds_asset_rows,
            profile_id=profile.profile_id,
            validation=certification_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=dataset_version,
            created_at=created_at,
            batch_id=f"{dataset_version}.odds.batch.001",
        )
        dataset_asset_rows = [row for row in (games_cert_row, schedule_cert_row, results_cert_row, odds_result["research_asset_certification"]) if row]
        dataset_row = build_historical_dataset_certification_row(
            profile=profile,
            dataset_version=dataset_version,
            batch_id=f"{dataset_version}.odds.batch.001",
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=dataset_asset_rows,
        )
        certification_runtime.store.upsert("historical_certifications", dataset_row, key_columns=("certification_id",))
    finally:
        certification_runtime.close()

    alignment_rows = [dict(row) for row in odds_asset_rows]
    for row in alignment_rows:
        row["schema_version"] = RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION
        row["lineage_version"] = dataset_version

    lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path, backend=backend)
    try:
        asset_identity = _build_odds_research_asset_identity(
            odds_row=alignment_rows[0],
            source_bundle=source_bundle,
            dataset_version=dataset_version,
        )
        alignment_result = lifecycle_runtime.certify_time_entity_alignment(
            identity=asset_identity,
            rows=[alignment_rows[0]],
            required_fields=asset_contract.required_fields,
            required_timestamps=asset_contract.required_timestamps,
            profile=profile,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            lifecycle_state="integrity_verified",
        )
        _promote_odds_asset_lifecycle(
            lifecycle_runtime=lifecycle_runtime,
            identity=asset_identity,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            normalized_rows=alignment_rows,
            alignment_result=alignment_result,
            certification_result=odds_result,
            dataset_result=dataset_row,
            asset_label="NFL odds",
            future_joins=["weather", "injuries", "officials", "team_stats", "player_stats", "betting_splits"],
        )
        coverage_planner_snapshot = build_research_asset_coverage_planner_snapshot(storage_path=storage_path, backend=backend, profile_id=profile.profile_id)
        readiness_snapshot = build_nfl_odds_research_asset_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            fixture=connector_bundle,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            normalized_rows=odds_asset_rows,
            validation=certification_validation,
            certification_result=odds_result,
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
            "normalized_rows": odds_asset_rows,
            "validation": certification_validation,
            "research_asset_certification": odds_result["research_asset_certification"],
            "dataset_certification": dataset_row,
            "alignment_results": [alignment_result],
            "lifecycle_alignment": alignment_result,
            "join_validation": join_validation,
            "coverage_planner_snapshot": coverage_planner_snapshot,
            "readiness_snapshot": readiness_snapshot,
        }
    finally:
        lifecycle_runtime.close()


def get_nfl_odds_research_asset_snapshot_for_dashboard(
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
    """Return the canonical NFL odds research asset readiness snapshot."""
    try:
        return build_nfl_odds_research_asset_dashboard_snapshot(
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
            "status": "nfl_odds_research_asset_snapshot_error",
            "asset_id": DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID,
            "asset_name": "NFL Odds Snapshots",
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
    "DEFAULT_NFL_ODDS_RESEARCH_ASSET_ID",
    "NFL_ODDS_RAW_ACQUISITION_DATASET_NAME",
    "NFL_ODDS_RESEARCH_ASSET_CONNECTOR_ID",
    "NFL_ODDS_RESEARCH_ASSET_CONNECTOR_NAME",
    "NFL_ODDS_RESEARCH_ASSET_DATASET_NAME",
    "NFL_ODDS_RESEARCH_ASSET_LIFECYCLE_VERSION",
    "NFL_ODDS_RESEARCH_ASSET_PROFILE_ID",
    "NFL_ODDS_RESEARCH_ASSET_PROVIDER",
    "NFL_ODDS_RESEARCH_ASSET_PROVIDER_NAME",
    "NFL_ODDS_RESEARCH_ASSET_PROVIDER_ROLE",
    "NFL_ODDS_RESEARCH_ASSET_STORAGE_PATH",
    "build_nfl_odds_research_asset_dashboard_snapshot",
    "build_nfl_odds_research_asset_population",
    "get_nfl_odds_research_asset_snapshot_for_dashboard",
]
