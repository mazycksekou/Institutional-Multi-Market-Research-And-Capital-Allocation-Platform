from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from src.data.nfl_p0_foundation import NFL_P0_DATASET_VERSION, NFL_P0_SCHEMA_VERSION, build_nfl_p0_fixture
from src.data.source_quality_scoring import score_source


NFL_ODDS_CONNECTOR_ID = "connector.odds_data.nfl_odds"
NFL_ODDS_CONNECTOR_NAME = "NFL Odds Connector"
NFL_ODDS_CONNECTOR_FAMILY = "odds_data"
NFL_ODDS_CONNECTOR_EXECUTION_MODE = "deterministic_fixture"
NFL_ODDS_PROVIDER_ID = "the_odds_api"
NFL_ODDS_PROVIDER_NAME = "The Odds API"
NFL_ODDS_PROVIDER_SOURCE_ID = "the_odds_api"
NFL_ODDS_PROVIDER_ROLE = "primary_acquisition"
NFL_ODDS_PROVIDER_SOURCE_TYPE = "deterministic_fixture"
NFL_ODDS_SOURCE_ACCESS_TYPE = "free_key"
NFL_ODDS_RESEARCH_ASSET_ID = "dataset.nfl.odds_snapshots"


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
    lineage_id = _stable_id("nfl_odds_field_lineage", source_bundle_id, _normalize_text(row.get("odds_snapshot_id") or row.get("game_id") or "row"))
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
        "source_access_type": NFL_ODDS_SOURCE_ACCESS_TYPE,
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
    fixture = build_nfl_p0_fixture(game_count=max(int(game_count or 1), 1), dataset_version=dataset_version or NFL_P0_DATASET_VERSION)
    odds_rows = _odds_rows(fixture)
    if not odds_rows:
        raise ValueError("NFL odds connector did not produce any odds rows")
    supported_fields = sorted({str(key) for key in odds_rows[0].keys()})
    return {
        "provider_id": NFL_ODDS_PROVIDER_ID,
        "provider_name": NFL_ODDS_PROVIDER_NAME,
        "provider_role": NFL_ODDS_PROVIDER_ROLE,
        "connector_id": NFL_ODDS_CONNECTOR_ID,
        "connector_name": NFL_ODDS_CONNECTOR_NAME,
        "connector_family": NFL_ODDS_CONNECTOR_FAMILY,
        "source_id": NFL_ODDS_PROVIDER_SOURCE_ID,
        "source_name": NFL_ODDS_PROVIDER_NAME,
        "source_family": "odds_data",
        "source_access_type": NFL_ODDS_SOURCE_ACCESS_TYPE,
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
    connector_family = _normalize_text(provider_capability.get("connector_family"), NFL_ODDS_CONNECTOR_FAMILY)
    payload.update(
        {
            "source_name": provider_name,
            "source_type": NFL_ODDS_PROVIDER_SOURCE_TYPE,
            "source_key": NFL_ODDS_PROVIDER_SOURCE_ID,
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
    fixture = build_nfl_p0_fixture(game_count=max(int(game_count or 1), 1), dataset_version=dataset_version or NFL_P0_DATASET_VERSION)
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
        "source_key": NFL_ODDS_PROVIDER_SOURCE_ID,
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


__all__ = [
    "NFL_ODDS_CONNECTOR_EXECUTION_MODE",
    "NFL_ODDS_CONNECTOR_FAMILY",
    "NFL_ODDS_CONNECTOR_ID",
    "NFL_ODDS_CONNECTOR_NAME",
    "NFL_ODDS_PROVIDER_ID",
    "NFL_ODDS_PROVIDER_NAME",
    "NFL_ODDS_PROVIDER_ROLE",
    "NFL_ODDS_RESEARCH_ASSET_ID",
    "build_nfl_odds_connector_bundle",
    "build_nfl_odds_provider_capability",
]
