from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.data.data_paths import get_runtime_data_path
from src.data.market_profile_contracts import MarketProfileContract, validate_market_profile_contract
from src.data.market_profile_registry import get_market_profile, register_market_profile
from src.data.nfl_p0_foundation import NFL_P0_SCHEMA_VERSION, NFL_P0_TABLE_CONTRACTS, validate_nfl_p0_rows
from src.data.validation import validate_dataset_rows
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION = "src.data.historical_research_asset_certification_runtime.v1"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_STORAGE_PATH = get_runtime_data_path(
    "historical_research_asset_certification",
    "canonical_data.sqlite",
)
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_DATASET_NAME = "historical_research_asset_certifications"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_NAME = "historical_research_asset_certification_runtime"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_TYPE = "certification_runtime"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_KEY = "historical_research_asset_certification_runtime"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROVIDER = "repository"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_OWNER = "src.data"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID = "sports:nfl"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_MARKET = "historical"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_MARKET_TYPE = "research_asset_certification"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_ASSET_CLASS = "historical"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_BATCH_ID = "historical.research.asset.certification.batch.001"
DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID = "dataset.sports.nfl.schedule"

CERTIFICATION_STATES: tuple[str, ...] = (
    "unknown",
    "discovered",
    "acquired",
    "validated",
    "partially_certified",
    "certified",
    "rejected",
    "superseded",
    "revoked",
)

CERTIFICATION_FAILURE_REASONS: tuple[str, ...] = (
    "missing_fields",
    "coverage_failure",
    "schema_failure",
    "timestamp_failure",
    "duplicate_records",
    "corrupted_payload",
    "failed_checksum",
    "lineage_failure",
    "provider_conflict",
    "point_in_time_violation",
)


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


def _normalize_items(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        values = (values,)
    return tuple(item for item in (_normalize_text(value) for value in values) if item)


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_iso(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    text = _to_iso(value)
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


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _source_signature(source_name: Any, source_snapshot_time: Any) -> str:
    return _stable_id("source_signature", source_name, source_snapshot_time)


def _row_identifier(row: Mapping[str, Any], index: int) -> str:
    for key in (
        "record_id",
        "game_id",
        "result_id",
        "schedule_id",
        "odds_snapshot_id",
        "weather_snapshot_id",
        "team_stats_snapshot_id",
        "event_id",
        "market_id",
        "selection_id",
        "row_id",
    ):
        value = _normalize_text(row.get(key))
        if value:
            return value
    return f"row.{index:05d}"


def _row_checksum(row: Mapping[str, Any]) -> str:
    return hashlib.sha256(_as_json(row).encode("utf-8")).hexdigest()


def _latest_timestamp(rows: Sequence[Mapping[str, Any]], field_name: str) -> str:
    instants = [_parse_iso(row.get(field_name)) for row in rows]
    instants = [instant for instant in instants if instant is not None]
    if not instants:
        return ""
    return max(instants).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _first_timestamp(rows: Sequence[Mapping[str, Any]], field_name: str) -> str:
    instants = [_parse_iso(row.get(field_name)) for row in rows]
    instants = [instant for instant in instants if instant is not None]
    if not instants:
        return ""
    return min(instants).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_market_profile(profile_id: str) -> MarketProfileContract:
    profile = get_market_profile(profile_id)
    if profile is not None:
        return profile
    if profile_id == DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID:
        from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE

        try:
            register_market_profile(NFL_AS_SPORTS_PROFILE_INSTANCE)
        except ValueError:
            pass
        resolved = get_market_profile(profile_id)
        return resolved or NFL_AS_SPORTS_PROFILE_INSTANCE
    raise KeyError(f"Unknown market profile: {profile_id}")


def _validate_market_profile(profile: MarketProfileContract | Mapping[str, Any]) -> dict[str, Any]:
    resolved = profile if isinstance(profile, MarketProfileContract) else MarketProfileContract.from_mapping(profile)
    validation = validate_market_profile_contract(resolved)
    errors = list(validation.get("errors", []))
    warnings = list(validation.get("warnings", []))
    if resolved.profile_family not in {"sports", "prediction_markets", "options_0dte"}:
        errors.append(f"unsupported profile_family: {resolved.profile_family}")
    if not resolved.storage_requirements:
        errors.append("storage_requirements are required")
    if not resolved.backtest_requirements:
        errors.append("backtest_requirements are required")
    if not resolved.worldview_permissions:
        errors.append("worldview_permissions are required")
    return {
        "ok": not errors,
        "profile": resolved,
        "profile_id": resolved.profile_id,
        "profile_family": resolved.profile_family,
        "errors": errors,
        "warnings": warnings,
    }


def _normalize_certification_state(value: Any, default: str = "unknown") -> str:
    state = _normalize_text(value, default).lower()
    return state if state in CERTIFICATION_STATES else default


def _normalize_failure_reason(value: Any, default: str = "") -> str:
    reason = _normalize_text(value, default).lower().replace(" ", "_")
    return reason if reason in CERTIFICATION_FAILURE_REASONS else default


def _classify_failure_reason(validation: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "coverage_failure"
    if validation.get("schema_version_issues"):
        return "schema_failure"
    if validation.get("point_in_time_issues"):
        return "point_in_time_violation"
    if validation.get("lineage_issues"):
        return "lineage_failure"
    if validation.get("duplicate_keys"):
        return "duplicate_records"
    if validation.get("source_issues"):
        return "schema_failure"
    if validation.get("metadata_issues"):
        return "corrupted_payload"
    if validation.get("missing_fields"):
        return "missing_fields"
    if validation.get("numeric_issues"):
        return "schema_failure"
    return "coverage_failure"


def _calculate_scores(validation: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    row_count = int(validation.get("row_count") or len(rows))
    invalid_count = int(validation.get("error_count") or 0)
    valid_count = max(row_count - invalid_count, 0)
    coverage_score = 1.0 if row_count > 0 else 0.0
    completeness_score = valid_count / row_count if row_count else 0.0
    quality_score = max(0.0, 1.0 - (invalid_count / row_count)) if row_count else 0.0
    certification_score = round((coverage_score + completeness_score + quality_score) / 3.0, 4)
    return {
        "coverage_score": round(coverage_score, 4),
        "completeness_score": round(completeness_score, 4),
        "quality_score": round(quality_score, 4),
        "certification_score": certification_score,
        "valid_row_count": float(valid_count),
        "invalid_row_count": float(invalid_count),
    }


@dataclass(slots=True, frozen=True)
class ResearchAssetCertificationContract:
    research_asset_id: str
    research_asset_name: str
    asset_category: str
    asset_type: str
    source_table_name: str
    required_fields: tuple[str, ...] = ()
    required_timestamps: tuple[str, ...] = ()
    point_in_time_rules: tuple[str, ...] = ()
    description: str = ""
    priority: str = "P0"
    required: bool = True
    future_asset: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "research_asset_id", _normalize_text(self.research_asset_id))
        object.__setattr__(self, "research_asset_name", _normalize_text(self.research_asset_name))
        object.__setattr__(self, "asset_category", _normalize_text(self.asset_category))
        object.__setattr__(self, "asset_type", _normalize_text(self.asset_type))
        object.__setattr__(self, "source_table_name", _normalize_text(self.source_table_name))
        object.__setattr__(self, "required_fields", _normalize_items(self.required_fields))
        object.__setattr__(self, "required_timestamps", _normalize_items(self.required_timestamps))
        object.__setattr__(self, "point_in_time_rules", _normalize_items(self.point_in_time_rules))
        object.__setattr__(self, "description", _normalize_text(self.description))
        object.__setattr__(self, "priority", _normalize_text(self.priority, "P0"))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return {
            "research_asset_id": self.research_asset_id,
            "research_asset_name": self.research_asset_name,
            "asset_category": self.asset_category,
            "asset_type": self.asset_type,
            "source_table_name": self.source_table_name,
            "required_fields": list(self.required_fields),
            "required_timestamps": list(self.required_timestamps),
            "point_in_time_rules": list(self.point_in_time_rules),
            "description": self.description,
            "priority": self.priority,
            "required": self.required,
            "future_asset": self.future_asset,
            "metadata": dict(self.metadata),
        }


def build_nfl_research_asset_certification_contracts(
    *,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
) -> list[ResearchAssetCertificationContract]:
    _ = _resolve_market_profile(profile_id)
    table_label_map = {
        "nfl_games": ("dataset.nfl.games", "NFL Games"),
        "nfl_schedule": (DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID, "NFL Schedule"),
        "nfl_results": ("dataset.sports.nfl.results", "NFL Results"),
        "nfl_odds_snapshots": ("dataset.nfl.odds", "NFL Odds Snapshots"),
        "nfl_weather_snapshots": ("dataset.nfl.weather", "NFL Weather Snapshots"),
        "nfl_team_stats_snapshots": ("dataset.nfl.team_stats", "NFL Team Statistics"),
    }
    contracts: list[ResearchAssetCertificationContract] = []
    for table_name, (asset_id, asset_name) in table_label_map.items():
        table_contract = NFL_P0_TABLE_CONTRACTS[table_name]
        contracts.append(
            ResearchAssetCertificationContract(
                research_asset_id=asset_id,
                research_asset_name=asset_name,
                asset_category="dataset",
                asset_type="table_snapshot",
                source_table_name=table_name,
                required_fields=table_contract.required_fields,
                required_timestamps=table_contract.required_timestamps,
                point_in_time_rules=table_contract.point_in_time_rules,
                description=table_contract.description,
                priority="P0",
                required=True,
                future_asset=False,
                metadata={
                    "market_profile": profile_id,
                    "market_family": "sports",
                    "minimum_schema": True,
                },
            )
        )
    return contracts


def build_nfl_research_asset_future_contracts(
    *,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
) -> list[ResearchAssetCertificationContract]:
    _ = _resolve_market_profile(profile_id)
    future_assets = [
        ("dataset.nfl.injuries", "NFL Injuries", "injury_context"),
        ("dataset.nfl.officials", "NFL Officials", "official_assignment"),
        ("dataset.nfl.coaching", "NFL Coaching", "coaching_context"),
        ("dataset.nfl.player_statistics", "NFL Player Statistics", "player_statistics"),
        ("dataset.nfl.opening_odds", "NFL Opening Odds", "odds_context"),
        ("dataset.nfl.closing_odds", "NFL Closing Odds", "odds_context"),
    ]
    return [
        ResearchAssetCertificationContract(
            research_asset_id=asset_id,
            research_asset_name=asset_name,
            asset_category="dataset",
            asset_type=asset_type,
            source_table_name="",
            required_fields=(),
            required_timestamps=(),
            point_in_time_rules=(),
            description="Discovered future research asset; not part of the minimum certified schema yet.",
            priority="P2",
            required=False,
            future_asset=True,
            metadata={
                "market_profile": profile_id,
                "market_family": "sports",
                "minimum_schema": False,
                "discovery_only": True,
            },
        )
        for asset_id, asset_name, asset_type in future_assets
    ]


def build_nfl_schedule_research_asset_certification_contract(
    *,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
) -> ResearchAssetCertificationContract:
    _ = _resolve_market_profile(profile_id)
    table_contract = NFL_P0_TABLE_CONTRACTS["nfl_schedule"]
    return ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID,
        research_asset_name="NFL Schedule",
        asset_category="dataset",
        asset_type="table_snapshot",
        source_table_name="nfl_schedule",
        required_fields=table_contract.required_fields,
        required_timestamps=table_contract.required_timestamps,
        point_in_time_rules=table_contract.point_in_time_rules,
        description=table_contract.description,
        priority="P0",
        required=True,
        future_asset=False,
        metadata={
            "market_profile": profile_id,
            "market_family": "sports",
            "minimum_schema": True,
            "dataset_role": "schedule",
        },
    )


def build_nfl_research_asset_catalog(
    *,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
) -> list[ResearchAssetCertificationContract]:
    return [
        *build_nfl_research_asset_certification_contracts(profile_id=profile_id),
        *build_nfl_research_asset_future_contracts(profile_id=profile_id),
    ]


def build_research_asset_certification_row(
    *,
    profile: MarketProfileContract,
    asset_contract: ResearchAssetCertificationContract,
    rows: Sequence[Mapping[str, Any]],
    validation: Mapping[str, Any],
    dataset_version: str,
    batch_id: str,
    created_at: str,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
    certification_state: str,
    certification_reason: str,
    failure_reason: str,
) -> dict[str, Any]:
    source_bundle = dict(source_bundle or {})
    raw_acquisition_result = dict(raw_acquisition_result or {})
    source_name = _normalize_text(
        source_bundle.get("source_name") or raw_acquisition_result.get("source_name"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_NAME,
    )
    source_type = _normalize_text(
        source_bundle.get("source_type") or raw_acquisition_result.get("source_type"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_TYPE,
    )
    source_key = _normalize_text(
        source_bundle.get("source_key") or raw_acquisition_result.get("source_key"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_KEY,
    )
    provider = _normalize_text(
        source_bundle.get("provider") or raw_acquisition_result.get("provider"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROVIDER,
    )
    source_snapshot_time = _latest_timestamp(rows, "source_snapshot_time") or _first_timestamp(rows, "snapshot_time") or created_at
    snapshot_time = _latest_timestamp(rows, "snapshot_time") or source_snapshot_time
    decision_time = _latest_timestamp(rows, "decision_time") or snapshot_time
    certified_at = created_at
    validation = dict(validation)
    scores = _calculate_scores(validation, rows)
    source_row_ids = [_row_identifier(row, index) for index, row in enumerate(rows)]
    source_table = asset_contract.source_table_name
    lineage_record = create_lineage_record(
        provider_id=provider,
        provider_type=profile.profile_family,
        payload_schema_version=HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        snapshot_id=_stable_id("research_asset_certification_snapshot", profile.profile_id, dataset_version, asset_contract.research_asset_id, batch_id),
        source_type=source_type,
        schema_version=HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        lineage_id=_stable_id("research_asset_certification_lineage", profile.profile_id, dataset_version, asset_contract.research_asset_id, batch_id),
        dataset_id="historical_research_asset_certifications",
        dataset_name="historical_research_asset_certifications",
        source_record_id=source_table or asset_contract.research_asset_id,
        target_record_id=_stable_id("research_asset_certification_target", profile.profile_id, dataset_version, asset_contract.research_asset_id, batch_id),
        source_stage="raw_acquisition_cache",
        target_stage="research_asset_certification",
        transformation="certify_research_asset",
    )
    certification_id = _stable_id("research_asset_certification", profile.profile_id, dataset_version, asset_contract.research_asset_id, batch_id)
    row = {
        "dataset_id": "historical_research_asset_certifications",
        "dataset_name": DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_DATASET_NAME,
        "market_profile": profile.profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": "historical_research_asset_certifications",
        "batch_id": batch_id,
        "certification_id": certification_id,
        "research_asset_id": asset_contract.research_asset_id,
        "research_asset_name": asset_contract.research_asset_name,
        "asset_category": asset_contract.asset_category,
        "asset_type": asset_contract.asset_type,
        "asset_version": dataset_version,
        "certification_version": HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        "certification_state": certification_state,
        "certification_reason": certification_reason,
        "failure_reason": failure_reason,
        "coverage_score": scores["coverage_score"],
        "certification_score": scores["certification_score"],
        "required_fields_json": _as_json(list(asset_contract.required_fields)),
        "required_timestamps_json": _as_json(list(asset_contract.required_timestamps)),
        "point_in_time_rules_json": _as_json(list(asset_contract.point_in_time_rules)),
        "validation_json": _as_json(validation),
        "lineage_json": _as_json(lineage_record),
        "provenance_json": _as_json(
            {
                "profile": profile.as_dict(),
                "source_bundle": source_bundle,
                "raw_acquisition_result": {
                    "ok": bool(raw_acquisition_result.get("ok")) if raw_acquisition_result else None,
                    "status": raw_acquisition_result.get("status") if raw_acquisition_result else None,
                    "dataset_id": (raw_acquisition_result.get("contract") or {}).get("dataset_id") if raw_acquisition_result else None,
                },
                "source_table": source_table,
                "source_row_ids": source_row_ids,
                "source_row_count": len(rows),
            }
        ),
        "certification_notes_json": _as_json(
            {
                "certification_reason": certification_reason,
                "failure_reason": failure_reason,
                "validation_errors": list(validation.get("errors", [])),
            }
        ),
        "missing_fields_json": _as_json(list(validation.get("missing_fields", []))),
        "duplicate_keys_json": _as_json(list(validation.get("duplicate_keys", []))),
        "join_keys_json": _as_json(list(validation.get("join_keys", [])) or [asset_contract.source_table_name, asset_contract.research_asset_id]),
        "valid_row_count": int(scores["valid_row_count"]),
        "invalid_row_count": int(scores["invalid_row_count"]),
        "warning_count": int(validation.get("warning_count") or 0),
        "source_row_count": len(rows),
        "checksum": _row_checksum(rows),
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_file": _normalize_text(source_bundle.get("source_file") or raw_acquisition_result.get("source_file")),
        "source_event_id": _normalize_text(source_bundle.get("source_event_id") or raw_acquisition_result.get("source_event_id")),
        "source_market_id": _normalize_text(source_bundle.get("source_market_id") or raw_acquisition_result.get("source_market_id")),
        "source_selection_id": _normalize_text(source_bundle.get("source_selection_id") or raw_acquisition_result.get("source_selection_id")),
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": certified_at,
        "certification_status": certification_state,
        "point_in_time_status": "safe" if certification_state in {"certified", "validated", "discovered"} else "blocked",
        "leakage_status": "none" if certification_state in {"certified", "validated", "discovered"} else "suspect",
        "status": certification_state,
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "provider": provider,
                "source_signature": _source_signature(source_name, source_snapshot_time),
            }
        ),
        "context_json": _as_json(
            {
                "profile": profile.as_dict(),
                "asset_contract": asset_contract.as_dict(),
                "validation": validation,
                "source_bundle": source_bundle,
            }
        ),
        "payload_json": _as_json(
            {
                "research_asset_id": asset_contract.research_asset_id,
                "research_asset_name": asset_contract.research_asset_name,
                "asset_category": asset_contract.asset_category,
                "asset_type": asset_contract.asset_type,
                "asset_version": dataset_version,
                "certification_state": certification_state,
                "certification_reason": certification_reason,
                "failure_reason": failure_reason,
                "certification_score": scores["certification_score"],
                "coverage_score": scores["coverage_score"],
                "completeness_score": scores["completeness_score"],
                "quality_score": scores["quality_score"],
                "lineage_record": lineage_record,
            }
        ),
        "schema_version": HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        "created_at": certified_at,
        "updated_at": certified_at,
        "source": source_name,
        "provider": provider,
        "market": profile.profile_id,
        "market_type": DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_MARKET_TYPE,
        "asset_class": profile.profile_family,
        "snapshot_id": _stable_id("research_asset_certification_snapshot", profile.profile_id, dataset_version, asset_contract.research_asset_id, batch_id),
        "lineage_id": _stable_id("research_asset_certification_lineage", profile.profile_id, dataset_version, asset_contract.research_asset_id, batch_id),
        "version_id": dataset_version,
        "quality_score": scores["quality_score"],
        "completeness_score": scores["completeness_score"],
    }
    return row


def build_historical_dataset_certification_row(
    *,
    profile: MarketProfileContract,
    dataset_version: str,
    batch_id: str,
    created_at: str,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
    asset_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    source_bundle = dict(source_bundle or {})
    raw_acquisition_result = dict(raw_acquisition_result or {})
    source_name = _normalize_text(
        source_bundle.get("source_name") or raw_acquisition_result.get("source_name"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_NAME,
    )
    source_type = _normalize_text(
        source_bundle.get("source_type") or raw_acquisition_result.get("source_type"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_TYPE,
    )
    source_key = _normalize_text(
        source_bundle.get("source_key") or raw_acquisition_result.get("source_key"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_KEY,
    )
    provider = _normalize_text(
        source_bundle.get("provider") or raw_acquisition_result.get("provider"),
        DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROVIDER,
    )
    certified_assets = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "certified"]
    partially_certified_assets = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "partially_certified"]
    discovered_assets = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "discovered"]
    rejected_assets = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "rejected"]
    required_asset_ids = [_normalize_text(row.get("research_asset_id")) for row in asset_rows if _normalize_text(row.get("research_asset_id"))]
    missing_asset_ids = [
        _normalize_text(row.get("research_asset_id"))
        for row in asset_rows
        if _normalize_text(row.get("certification_status")) in {"discovered", "rejected"}
    ]
    invalid_reason_ids = [
        {
            "research_asset_id": _normalize_text(row.get("research_asset_id")),
            "failure_reason": _normalize_text(row.get("failure_reason")),
            "certification_reason": _normalize_text(row.get("certification_reason")),
        }
        for row in asset_rows
        if _normalize_text(row.get("certification_status")) != "certified"
    ]
    validation = {
        "ok": not (partially_certified_assets or discovered_assets or rejected_assets),
        "status": "certified" if not (partially_certified_assets or discovered_assets or rejected_assets) else "blocked",
        "required_asset_count": len(asset_rows),
        "certified_asset_count": len(certified_assets),
        "partial_asset_count": len(partially_certified_assets),
        "discovered_asset_count": len(discovered_assets),
        "rejected_asset_count": len(rejected_assets),
        "missing_asset_ids": [asset_id for asset_id in missing_asset_ids if asset_id],
        "invalid_assets": invalid_reason_ids,
    }
    state = "certified" if validation["ok"] else "partially_certified" if certified_assets else "rejected"
    source_snapshot_time = _latest_timestamp(asset_rows, "certified_at") or created_at
    snapshot_time = source_snapshot_time
    decision_time = source_snapshot_time
    lineage_record = create_lineage_record(
        provider_id=provider,
        provider_type=profile.profile_family,
        payload_schema_version=HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        snapshot_id=_stable_id("historical_dataset_certification_snapshot", profile.profile_id, dataset_version, batch_id),
        source_type=source_type,
        schema_version=HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        lineage_id=_stable_id("historical_dataset_certification_lineage", profile.profile_id, dataset_version, batch_id),
        dataset_id="historical_certifications",
        dataset_name="historical_certifications",
        source_record_id=";".join(required_asset_ids) or batch_id,
        target_record_id=_stable_id("historical_dataset_certification_target", profile.profile_id, dataset_version, batch_id),
        source_stage="research_asset_certification",
        target_stage="dataset_certification",
        transformation="certify_dataset_from_research_assets",
    )
    certification_id = _stable_id("historical_dataset_certification", profile.profile_id, dataset_version, batch_id)
    warning_count = len(partially_certified_assets) + len(discovered_assets)
    return {
        "dataset_id": "historical_certifications",
        "dataset_name": "historical_certifications",
        "market_profile": profile.profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": "dataset.minimum_certified_schema",
        "batch_id": batch_id,
        "certification_id": certification_id,
        "row_count": len(asset_rows),
        "valid_row_count": len(certified_assets),
        "invalid_row_count": len(asset_rows) - len(certified_assets),
        "warning_count": warning_count,
        "missing_fields_json": _as_json([asset_id for asset_id in missing_asset_ids if asset_id]),
        "duplicate_keys_json": _as_json([]),
        "join_keys_json": _as_json(["research_asset_id", "dataset_version"]),
        "validation_json": _as_json(validation),
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_file": _normalize_text(source_bundle.get("source_file") or raw_acquisition_result.get("source_file")),
        "source_event_id": _normalize_text(source_bundle.get("source_event_id") or raw_acquisition_result.get("source_event_id")),
        "source_market_id": _normalize_text(source_bundle.get("source_market_id") or raw_acquisition_result.get("source_market_id")),
        "source_selection_id": _normalize_text(source_bundle.get("source_selection_id") or raw_acquisition_result.get("source_selection_id")),
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": created_at,
        "certification_status": state,
        "point_in_time_status": "safe" if validation["ok"] else "blocked",
        "leakage_status": "none" if validation["ok"] else "suspect",
        "status": state,
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "provider": provider,
                "source_signature": _source_signature(source_name, source_snapshot_time),
            }
        ),
        "context_json": _as_json(
            {
                "profile": profile.as_dict(),
                "asset_rows": list(asset_rows),
                "validation": validation,
            }
        ),
        "payload_json": _as_json(
            {
                "dataset_version": dataset_version,
                "batch_id": batch_id,
                "certified_asset_ids": [str(row.get("research_asset_id")) for row in certified_assets],
                "missing_asset_ids": [str(row.get("research_asset_id")) for row in asset_rows if _normalize_text(row.get("certification_status")) in {"discovered", "rejected"}],
                "partial_asset_ids": [str(row.get("research_asset_id")) for row in partially_certified_assets],
                "validation": validation,
                "lineage_record": lineage_record,
            }
        ),
        "schema_version": HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": source_name,
        "provider": provider,
        "market": profile.profile_id,
        "market_type": "dataset_certification",
        "asset_class": profile.profile_family,
        "snapshot_id": _stable_id("historical_dataset_certification_snapshot", profile.profile_id, dataset_version, batch_id),
        "lineage_id": _stable_id("historical_dataset_certification_lineage", profile.profile_id, dataset_version, batch_id),
        "version_id": dataset_version,
        "quality_score": 1.0 if validation["ok"] else 0.0,
        "completeness_score": round(len(certified_assets) / len(asset_rows), 4) if asset_rows else 0.0,
    }


class HistoricalResearchAssetCertificationRuntime:
    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        backend: str = "sqlite",
        dataset_owner: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_OWNER,
        store: LocalStorageEngine | None = None,
    ) -> None:
        self.storage_path = Path(storage_path or DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_STORAGE_PATH).expanduser().resolve()
        self.backend = str(backend or "sqlite").strip().lower()
        self.dataset_owner = _normalize_text(dataset_owner, DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_OWNER)
        self.store = store or create_local_storage_engine(self.storage_path, backend=self.backend)
        self._owns_store = store is None
        self.store.ensure_schema()

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> "HistoricalResearchAssetCertificationRuntime":
        _ = self.store.connection
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def build_required_asset_catalog(self, *, profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID) -> list[ResearchAssetCertificationContract]:
        profile = _resolve_market_profile(profile_id)
        validation = _validate_market_profile(profile)
        if not validation["ok"]:
            raise ValueError("; ".join(validation["errors"]) or "historical research asset profile validation failed")
        if profile.profile_id == DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID:
            return build_nfl_research_asset_certification_contracts(profile_id=profile.profile_id)
        raise NotImplementedError(f"Unsupported profile for research asset certification: {profile.profile_id}")

    def build_discovered_future_asset_catalog(self, *, profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID) -> list[ResearchAssetCertificationContract]:
        profile = _resolve_market_profile(profile_id)
        if profile.profile_id == DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID:
            return build_nfl_research_asset_future_contracts(profile_id=profile.profile_id)
        return []

    def build_asset_catalog(self, *, profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID) -> list[ResearchAssetCertificationContract]:
        return [
            *self.build_required_asset_catalog(profile_id=profile_id),
            *self.build_discovered_future_asset_catalog(profile_id=profile_id),
        ]

    def certify_research_asset(
        self,
        *,
        asset_contract: ResearchAssetCertificationContract,
        rows: Sequence[Mapping[str, Any]],
        profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
        validation: Mapping[str, Any] | None = None,
        source_bundle: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
        dataset_version: str | None = None,
        created_at: str | None = None,
        batch_id: str | None = None,
    ) -> dict[str, Any]:
        profile = _resolve_market_profile(profile_id)
        profile_validation = _validate_market_profile(profile)
        if not profile_validation["ok"]:
            raise ValueError("; ".join(profile_validation["errors"]) or "historical research asset profile validation failed")

        source_bundle = dict(source_bundle or {})
        raw_acquisition_result = dict(raw_acquisition_result or {})
        dataset_version = _normalize_text(
            dataset_version,
            _normalize_text(
                raw_acquisition_result.get("dataset_version")
                or source_bundle.get("dataset_version")
                or (rows[0].get("dataset_version") if rows else ""),
                "historical.research.v1",
            ),
        )
        created_at = _normalize_text(created_at, _utc_now_iso())
        batch_id = _normalize_text(batch_id, f"{dataset_version}.batch.001")
        normalized_rows = self._normalize_source_asset_rows(rows, source_bundle=source_bundle, raw_acquisition_result=raw_acquisition_result)
        validation_payload = dict(
            validation
            or (
                validate_nfl_p0_rows(asset_contract.source_table_name, normalized_rows)
                if asset_contract.source_table_name in NFL_P0_TABLE_CONTRACTS
                else validate_dataset_rows(normalized_rows, required_fields=asset_contract.required_fields)
            )
        )
        certification_state, certification_reason, failure_reason = self._classify_asset_state(asset_contract, normalized_rows, validation_payload)
        row = build_research_asset_certification_row(
            profile=profile,
            asset_contract=asset_contract,
            rows=normalized_rows,
            validation=validation_payload,
            dataset_version=dataset_version,
            batch_id=batch_id,
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            certification_state=certification_state,
            certification_reason=certification_reason,
            failure_reason=failure_reason,
        )
        self.store.upsert("historical_research_asset_certifications", row, key_columns=("certification_id",))
        return {
            "ok": certification_state == "certified",
            "status": certification_state,
            "profile": profile.as_dict(),
            "dataset_version": dataset_version,
            "batch_id": batch_id,
            "asset_contract": asset_contract.as_dict(),
            "normalized_rows": normalized_rows,
            "validation": validation_payload,
            "research_asset_certification": row,
            "certification_state": certification_state,
            "certification_reason": certification_reason,
            "failure_reason": failure_reason,
        }

    @staticmethod
    def _normalize_source_asset_rows(
        rows: Sequence[Mapping[str, Any]],
        *,
        source_bundle: Mapping[str, Any],
        raw_acquisition_result: Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        source_bundle = dict(source_bundle or {})
        raw_acquisition_result = dict(raw_acquisition_result or {})
        source_name = _normalize_text(
            source_bundle.get("source_name") or raw_acquisition_result.get("source_name"),
            DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_NAME,
        )
        source_type = _normalize_text(
            source_bundle.get("source_type") or raw_acquisition_result.get("source_type"),
            DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_TYPE,
        )
        source_key = _normalize_text(
            source_bundle.get("source_key") or raw_acquisition_result.get("source_key"),
            DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_KEY,
        )
        provider = _normalize_text(
            source_bundle.get("provider") or raw_acquisition_result.get("provider"),
            DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROVIDER,
        )
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["schema_version"] = _normalize_text(payload.get("schema_version"), NFL_P0_SCHEMA_VERSION)
            payload["source_metadata_json"] = _as_json(
                {
                    "source_name": source_name,
                    "source_type": source_type,
                    "source_key": source_key,
                    "provider": provider,
                }
            )
            payload["payload_json"] = _as_json(dict(row))
            payload["source_signature"] = _normalize_text(
                payload.get("source_signature"),
                _source_signature(source_name, payload.get("source_snapshot_time") or payload.get("snapshot_time")),
            )
            normalized_rows.append(payload)
        return normalized_rows

    def certify(
        self,
        *,
        fixture: Mapping[str, Any],
        profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
        raw_acquisition_result: Mapping[str, Any] | None = None,
        dataset_version: str | None = None,
        created_at: str | None = None,
        batch_id: str | None = None,
    ) -> dict[str, Any]:
        profile = _resolve_market_profile(profile_id)
        profile_validation = _validate_market_profile(profile)
        if not profile_validation["ok"]:
            raise ValueError("; ".join(profile_validation["errors"]) or "historical research asset profile validation failed")
        fixture_payload = dict(fixture)
        source_tables = self._source_tables(fixture_payload)
        source_bundle = dict(fixture_payload.get("source_bundle") or {})
        dataset_version = _normalize_text(dataset_version, _normalize_text(fixture_payload.get("dataset_version"), "historical.research.v1"))
        created_at = _normalize_text(created_at, _utc_now_iso())
        batch_id = _normalize_text(batch_id, f"{dataset_version}.batch.001")
        source_bundle.setdefault("source_name", fixture_payload.get("source_name"))
        source_bundle.setdefault("source_type", fixture_payload.get("source_type"))
        source_bundle.setdefault("source_key", fixture_payload.get("source_key"))
        source_bundle.setdefault("provider", fixture_payload.get("provider"))

        asset_rows: list[dict[str, Any]] = []
        for asset_contract in self.build_required_asset_catalog(profile_id=profile.profile_id):
            rows = source_tables.get(asset_contract.source_table_name, [])
            asset_result = self.certify_research_asset(
                asset_contract=asset_contract,
                rows=rows,
                profile_id=profile.profile_id,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                dataset_version=dataset_version,
                created_at=created_at,
                batch_id=batch_id,
            )
            asset_rows.append(dict(asset_result["research_asset_certification"]))

        dataset_row = build_historical_dataset_certification_row(
            profile=profile,
            dataset_version=dataset_version,
            batch_id=batch_id,
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=asset_rows,
        )
        self.store.upsert("historical_certifications", dataset_row, key_columns=("certification_id",))

        summary = self._summarize_asset_rows(asset_rows, dataset_row)
        return {
            "ok": summary["dataset_status"] == "certified",
            "status": summary["dataset_status"],
            "profile": profile.as_dict(),
            "dataset_version": dataset_version,
            "batch_id": batch_id,
            "asset_catalog": [asset.as_dict() for asset in self.build_asset_catalog(profile_id=profile.profile_id)],
            "required_asset_catalog": [asset.as_dict() for asset in self.build_required_asset_catalog(profile_id=profile.profile_id)],
            "future_asset_catalog": [asset.as_dict() for asset in self.build_discovered_future_asset_catalog(profile_id=profile.profile_id)],
            "research_asset_certifications": asset_rows,
            "dataset_certification": dataset_row,
            "summary": summary,
            "source_bundle": source_bundle,
            "raw_acquisition_result": dict(raw_acquisition_result or {}),
        }

    def build_readiness_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
        fixture: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = _resolve_market_profile(profile_id)
        profile_validation = _validate_market_profile(profile)
        asset_contracts = self.build_required_asset_catalog(profile_id=profile.profile_id)
        future_contracts = self.build_discovered_future_asset_catalog(profile_id=profile.profile_id)
        asset_rows = self.store.fetch("historical_research_asset_certifications", order_by="certification_id ASC") if self.store.table_exists("historical_research_asset_certifications") else []
        dataset_rows = self.store.fetch("historical_certifications", order_by="certification_id ASC") if self.store.table_exists("historical_certifications") else []
        table_ready = bool(asset_rows) and bool(dataset_rows)
        asset_summary = self._summarize_asset_rows(asset_rows, dataset_rows[0] if dataset_rows else {})
        if fixture is not None:
            source_bundle = dict(fixture.get("source_bundle") or {})
        else:
            source_bundle = {}
        if raw_acquisition_result:
            source_bundle = dict((raw_acquisition_result.get("source_bundle") or source_bundle))
        try:
            from src.data.research_asset_lifecycle_runtime import ResearchAssetLifecycleRuntime

            lifecycle_runtime = ResearchAssetLifecycleRuntime(
                self.storage_path,
                backend=self.backend,
                dataset_owner=self.dataset_owner,
                store=self.store,
            )
            lifecycle_snapshot = lifecycle_runtime.build_readiness_snapshot(
                profile_id=profile.profile_id,
                fixture=fixture,
                raw_acquisition_result=raw_acquisition_result,
            )
        except Exception as exc:
            lifecycle_snapshot = {
                "ok": False,
                "status": "research_asset_lifecycle_snapshot_error",
                "warnings": [str(exc)],
            }
        return {
            "ok": bool(table_ready and asset_summary["dataset_status"] == "certified" and profile_validation["ok"]),
            "status": "ready" if table_ready and asset_summary["dataset_status"] == "certified" and profile_validation["ok"] else "partial" if asset_rows or dataset_rows else "missing",
            "profile": profile.as_dict(),
            "profile_validation": profile_validation,
            "required_asset_catalog": [asset.as_dict() for asset in asset_contracts],
            "future_asset_catalog": [asset.as_dict() for asset in future_contracts],
            "research_asset_certifications": asset_rows,
            "dataset_certifications": dataset_rows,
            "asset_summary": asset_summary,
            "missing_research_assets": asset_summary["missing_research_assets"],
            "failed_research_assets": asset_summary["failed_research_assets"],
            "pending_research_assets": asset_summary["pending_research_assets"],
            "certification_scores": asset_summary["certification_scores"],
            "lifecycle_readiness": lifecycle_snapshot,
            "source_bundle": source_bundle,
            "raw_acquisition_result": dict(raw_acquisition_result or {}),
            "storage": self.store.health(),
        }

    def dashboard_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
        fixture: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = self.build_readiness_snapshot(
            profile_id=profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
        asset_summary = dict(snapshot.get("asset_summary") or {})
        snapshot["dataset_readiness"] = {
            "status": snapshot.get("status"),
            "ready_asset_count": asset_summary.get("certified_asset_count", 0),
            "total_asset_count": asset_summary.get("required_asset_count", 0),
            "missing_assets": snapshot.get("missing_research_assets", []),
            "blocked_assets": snapshot.get("failed_research_assets", []),
        }
        snapshot["research_asset_readiness"] = {
            "status": asset_summary.get("dataset_status"),
            "certified_asset_count": asset_summary.get("certified_asset_count", 0),
            "partial_asset_count": asset_summary.get("partial_asset_count", 0),
            "missing_asset_count": len(snapshot.get("missing_research_assets", [])),
            "failed_asset_count": len(snapshot.get("failed_research_assets", [])),
            "pending_asset_count": len(snapshot.get("pending_research_assets", [])),
            "certification_scores": snapshot.get("certification_scores", {}),
            "missing_research_assets": snapshot.get("missing_research_assets", []),
            "failed_research_assets": snapshot.get("failed_research_assets", []),
            "pending_research_assets": snapshot.get("pending_research_assets", []),
        }
        snapshot["readiness_summary"] = {
            "research_asset_status": asset_summary.get("dataset_status"),
            "dataset_status": asset_summary.get("dataset_status"),
            "certified_asset_count": asset_summary.get("certified_asset_count", 0),
            "missing_asset_count": len(snapshot.get("missing_research_assets", [])),
            "failed_asset_count": len(snapshot.get("failed_research_assets", [])),
        }
        lifecycle_snapshot = dict(snapshot.get("lifecycle_readiness") or {})
        snapshot["lifecycle_readiness"] = lifecycle_snapshot
        snapshot["time_entity_alignment_readiness"] = {
            "status": lifecycle_snapshot.get("status", "missing"),
            "alignment_failures": lifecycle_snapshot.get("alignment_failures", []),
            "alignment_status_counts": lifecycle_snapshot.get("alignment_status_counts", {}),
            "blocked_assets": lifecycle_snapshot.get("blocked_assets", []),
            "missing_assets": lifecycle_snapshot.get("missing_assets", []),
        }
        return snapshot

    @staticmethod
    def _source_tables(fixture: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
        tables = fixture.get("source_tables") or fixture.get("tables") or {}
        if not isinstance(tables, Mapping):
            return {}
        return {str(name): [dict(row) for row in rows if isinstance(row, Mapping)] for name, rows in tables.items()}

    @staticmethod
    def _classify_asset_state(
        asset_contract: ResearchAssetCertificationContract,
        rows: Sequence[Mapping[str, Any]],
        validation: Mapping[str, Any],
    ) -> tuple[str, str, str]:
        row_count = int(validation.get("row_count") or len(rows))
        valid_count = max(row_count - int(validation.get("error_count") or 0), 0)
        if not rows:
            return "discovered", "asset discovered but not yet acquired", "coverage_failure"
        if validation.get("ok"):
            return "certified", "asset validated with point-in-time-safe rows", "not_applicable"
        if valid_count > 0:
            reason = _classify_failure_reason(validation, rows)
            return "partially_certified", "asset partially certified; review the validation output", reason
        reason = _classify_failure_reason(validation, rows)
        return "rejected", "asset failed validation and cannot be certified", reason

    @staticmethod
    def _summarize_asset_rows(
        asset_rows: Sequence[Mapping[str, Any]],
        dataset_row: Mapping[str, Any],
    ) -> dict[str, Any]:
        certified_asset_rows = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "certified"]
        partial_asset_rows = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "partially_certified"]
        discovered_asset_rows = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "discovered"]
        rejected_asset_rows = [row for row in asset_rows if _normalize_text(row.get("certification_status")) == "rejected"]
        missing_research_assets = [
            str(row.get("research_asset_id"))
            for row in asset_rows
            if _normalize_text(row.get("certification_status")) in {"discovered", "rejected"}
        ]
        failed_research_assets = [
            str(row.get("research_asset_id"))
            for row in asset_rows
            if _normalize_text(row.get("certification_status")) == "rejected"
        ]
        pending_research_assets = [
            str(row.get("research_asset_id"))
            for row in asset_rows
            if _normalize_text(row.get("certification_status")) in {"discovered", "partially_certified"}
        ]
        certification_scores = {
            str(row.get("research_asset_id")): _normalize_float(row.get("certification_score"), 0.0)
            for row in asset_rows
        }
        dataset_status = _normalize_text(dataset_row.get("certification_status")) if dataset_row else "missing"
        return {
            "required_asset_count": len(asset_rows),
            "certified_asset_count": len(certified_asset_rows),
            "partial_asset_count": len(partial_asset_rows),
            "discovered_asset_count": len(discovered_asset_rows),
            "rejected_asset_count": len(rejected_asset_rows),
            "missing_research_assets": [asset_id for asset_id in missing_research_assets if asset_id],
            "failed_research_assets": [asset_id for asset_id in failed_research_assets if asset_id],
            "pending_research_assets": [asset_id for asset_id in pending_research_assets if asset_id],
            "certification_scores": certification_scores,
            "dataset_status": dataset_status,
            "dataset_certified": dataset_status == "certified",
        }


def build_historical_research_asset_certification_runtime_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
    fixture: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path, backend=backend)
    try:
        return runtime.dashboard_snapshot(
            profile_id=profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
    finally:
        runtime.close()


def get_historical_research_asset_certification_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
    fixture: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return build_historical_research_asset_certification_runtime_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "historical_research_asset_certification_snapshot_error",
            "profile": {},
            "required_asset_catalog": [],
            "future_asset_catalog": [],
            "research_asset_certifications": [],
            "dataset_certifications": [],
            "asset_summary": {},
            "missing_research_assets": [],
            "failed_research_assets": [],
            "pending_research_assets": [],
            "certification_scores": {},
            "dataset_readiness": {},
            "research_asset_readiness": {},
            "readiness_summary": {},
            "storage": {},
            "warnings": [str(exc)],
        }


__all__ = [
    "CERTIFICATION_FAILURE_REASONS",
    "CERTIFICATION_STATES",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_ASSET_CLASS",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_BATCH_ID",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_DATASET_NAME",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_MARKET",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_MARKET_TYPE",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_OWNER",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROVIDER",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_KEY",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_NAME",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SOURCE_TYPE",
    "DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_STORAGE_PATH",
    "DEFAULT_NFL_SCHEDULE_RESEARCH_ASSET_ID",
    "HISTORICAL_RESEARCH_ASSET_CERTIFICATION_SCHEMA_VERSION",
    "HistoricalResearchAssetCertificationRuntime",
    "ResearchAssetCertificationContract",
    "build_historical_dataset_certification_row",
    "build_historical_research_asset_certification_runtime_dashboard_snapshot",
    "build_nfl_research_asset_catalog",
    "build_nfl_research_asset_certification_contracts",
    "build_nfl_schedule_research_asset_certification_contract",
    "build_nfl_research_asset_future_contracts",
    "build_research_asset_certification_row",
    "get_historical_research_asset_certification_snapshot_for_dashboard",
]
