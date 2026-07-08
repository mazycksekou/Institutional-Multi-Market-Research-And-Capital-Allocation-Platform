from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.data.data_paths import get_runtime_data_path
from src.data.historical_research_asset_certification_runtime import HistoricalResearchAssetCertificationRuntime
from src.data.historical_dataset_acquisition_runtime import HistoricalDatasetAcquisitionRuntime
from src.data.market_profile_contracts import MarketProfileContract, validate_market_profile_contract
from src.data.market_profile_registry import get_market_profile, register_market_profile
from src.data.source_event_links import build_event_link_index, resolve_source_event_links
from src.data.validation import validate_dataset_rows
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine

HISTORICAL_RESEARCH_SCHEMA_VERSION = "src.data.historical_research_database.v1"
HISTORICAL_RESEARCH_DATASET_NAME = "historical_research_database"
DEFAULT_HISTORICAL_RESEARCH_DATASET_NAME = HISTORICAL_RESEARCH_DATASET_NAME
DEFAULT_HISTORICAL_RESEARCH_STORAGE_PATH = get_runtime_data_path("historical_research", "historical_research.sqlite")
DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID = "sports:nfl"
DEFAULT_HISTORICAL_RESEARCH_PROVIDER = "local_fixture"
DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME = "local_historical_fixture"
DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE = "fixture"
DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY = "local_historical_fixture"
DEFAULT_HISTORICAL_RESEARCH_OWNER = "local"
DEFAULT_HISTORICAL_RESEARCH_ASSET_CLASS = "sports"
DEFAULT_HISTORICAL_RESEARCH_MARKET = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID

HISTORICAL_SHARED_REQUIRED_FIELDS: tuple[str, ...] = (
    "dataset_id",
    "dataset_name",
    "market_profile",
    "profile_id",
    "profile_family",
    "stage_name",
    "batch_id",
    "source_name",
    "source_type",
    "source_key",
    "source_snapshot_time",
    "snapshot_time",
    "decision_time",
    "certified_at",
    "certification_status",
    "point_in_time_status",
    "leakage_status",
    "status",
    "source_metadata_json",
    "context_json",
    "payload_json",
    "schema_version",
    "created_at",
    "updated_at",
    "source",
    "provider",
    "market",
    "market_type",
    "asset_class",
    "snapshot_id",
    "lineage_id",
    "version_id",
    "quality_score",
    "completeness_score",
)

HISTORICAL_SHARED_REQUIRED_TIMESTAMPS: tuple[str, ...] = (
    "source_snapshot_time",
    "snapshot_time",
    "decision_time",
    "certified_at",
    "created_at",
    "updated_at",
)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return float(default)
        return result
    except (TypeError, ValueError):
        return float(default)


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


def _market_family(market: Any, selection: Any = None) -> str:
    market_text = _normalize_text(market).lower()
    selection_text = _normalize_text(selection).lower()
    if "spread" in market_text or "run line" in market_text or market_text == "spread":
        return "spread_or_runline"
    if "team total" in market_text:
        return "team_total"
    if "total" in market_text or "over/under" in market_text:
        return "total"
    if "moneyline" in market_text or market_text in {"ml", "h2h", "1x2", "match winner"}:
        return "moneyline"
    if "player" in market_text or "player" in selection_text:
        return "player_prop"
    return "other"


def _source_signature(source_name: Any, source_snapshot_time: Any) -> str:
    return _stable_id("source_signature", source_name, source_snapshot_time)


def _context_payload(
    *,
    schedule_row: Mapping[str, Any] | None = None,
    weather_row: Mapping[str, Any] | None = None,
    result_row: Mapping[str, Any] | None = None,
    home_team_stats: Mapping[str, Any] | None = None,
    away_team_stats: Mapping[str, Any] | None = None,
    extras: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schedule": dict(schedule_row or {}),
        "weather": dict(weather_row or {}),
        "result": dict(result_row or {}),
        "officials": [],
        "injuries": [],
        "coaching": [],
        "rest_travel": {
            "home": {
                "rest_days": (home_team_stats or {}).get("rest_days"),
                "travel_distance_miles": (home_team_stats or {}).get("travel_distance_miles"),
                "travel_timezone_change": (home_team_stats or {}).get("travel_timezone_change"),
            },
            "away": {
                "rest_days": (away_team_stats or {}).get("rest_days"),
                "travel_distance_miles": (away_team_stats or {}).get("travel_distance_miles"),
                "travel_timezone_change": (away_team_stats or {}).get("travel_timezone_change"),
            },
        },
        "team_stats": {
            "home": dict(home_team_stats or {}),
            "away": dict(away_team_stats or {}),
        },
    }
    if extras:
        payload.update(dict(extras))
    return payload


@dataclass(slots=True, frozen=True)
class HistoricalStageContract:
    table_name: str
    row_id_field: str
    required_fields: tuple[str, ...]
    required_timestamps: tuple[str, ...]
    join_keys: tuple[str, ...]
    point_in_time_rules: tuple[str, ...]
    numeric_fields: tuple[str, ...]
    description: str
    time_anchor_field: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "table_name", _normalize_text(self.table_name))
        object.__setattr__(self, "row_id_field", _normalize_text(self.row_id_field))
        object.__setattr__(self, "required_fields", tuple(_normalize_text(value) for value in self.required_fields if _normalize_text(value)))
        object.__setattr__(self, "required_timestamps", tuple(_normalize_text(value) for value in self.required_timestamps if _normalize_text(value)))
        object.__setattr__(self, "join_keys", tuple(_normalize_text(value) for value in self.join_keys if _normalize_text(value)))
        object.__setattr__(self, "point_in_time_rules", tuple(_normalize_text(value) for value in self.point_in_time_rules if _normalize_text(value)))
        object.__setattr__(self, "numeric_fields", tuple(_normalize_text(value) for value in self.numeric_fields if _normalize_text(value)))
        object.__setattr__(self, "description", _normalize_text(self.description))
        object.__setattr__(self, "time_anchor_field", _normalize_text(self.time_anchor_field))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return {
            "table_name": self.table_name,
            "row_id_field": self.row_id_field,
            "required_fields": list(self.required_fields),
            "required_timestamps": list(self.required_timestamps),
            "join_keys": list(self.join_keys),
            "point_in_time_rules": list(self.point_in_time_rules),
            "numeric_fields": list(self.numeric_fields),
            "description": self.description,
            "time_anchor_field": self.time_anchor_field,
            "metadata": dict(self.metadata),
        }


HISTORICAL_STAGE_CONTRACTS: dict[str, HistoricalStageContract] = {
    "historical_acquisition_batches": HistoricalStageContract(
        table_name="historical_acquisition_batches",
        row_id_field="batch_id",
        required_fields=HISTORICAL_SHARED_REQUIRED_FIELDS
        + (
            "batch_id",
            "acquisition_started_at",
            "acquisition_completed_at",
            "source_count",
            "event_count",
            "market_count",
            "selection_count",
            "certified_row_count",
            "rejected_row_count",
            "coverage_json",
            "licensing_json",
            "provenance_json",
            "notes_json",
        ),
        required_timestamps=HISTORICAL_SHARED_REQUIRED_TIMESTAMPS
        + ("acquisition_started_at", "acquisition_completed_at"),
        join_keys=("batch_id", "dataset_id", "dataset_name"),
        point_in_time_rules=("acquisition_started_at <= acquisition_completed_at",),
        numeric_fields=("source_count", "event_count", "market_count", "selection_count", "certified_row_count", "rejected_row_count", "quality_score", "completeness_score"),
        description="Acquisition summary for one certified historical bundle.",
        time_anchor_field="acquisition_completed_at",
        metadata={"stage": "batch"},
    ),
    "historical_events": HistoricalStageContract(
        table_name="historical_events",
        row_id_field="event_id",
        required_fields=HISTORICAL_SHARED_REQUIRED_FIELDS
        + (
            "event_id",
            "event_key",
            "batch_id",
            "sport",
            "league",
            "season",
            "season_type",
            "week",
            "game_id",
            "event_date",
            "event_start_time",
            "home_team",
            "away_team",
            "venue_id",
            "venue_name",
            "venue_city",
            "venue_state",
            "neutral_site",
            "final_result",
            "final_score_home",
            "final_score_away",
            "winner_team",
            "margin",
            "total_points",
            "result_recorded_time",
            "result_status",
            "settlement_status",
        ),
        required_timestamps=HISTORICAL_SHARED_REQUIRED_TIMESTAMPS
        + ("event_date", "event_start_time", "result_recorded_time"),
        join_keys=("event_id", "event_key", "game_id"),
        point_in_time_rules=("snapshot_time <= event_start_time", "decision_time <= event_start_time", "source_snapshot_time <= event_start_time"),
        numeric_fields=("season", "week", "neutral_site", "final_score_home", "final_score_away", "margin", "total_points", "quality_score", "completeness_score"),
        description="Canonical historical event row with one shared event context.",
        time_anchor_field="event_start_time",
        metadata={"stage": "event"},
    ),
    "historical_markets": HistoricalStageContract(
        table_name="historical_markets",
        row_id_field="market_id",
        required_fields=HISTORICAL_SHARED_REQUIRED_FIELDS
        + (
            "market_id",
            "batch_id",
            "event_id",
            "event_start_time",
            "market_family",
            "market_type",
            "market_name",
            "book",
            "line_value",
            "odds",
            "opening_odds",
            "closing_odds",
            "price_type",
            "market_label",
            "selection_count",
        ),
        required_timestamps=HISTORICAL_SHARED_REQUIRED_TIMESTAMPS,
        join_keys=("market_id", "event_id", "book", "market_type"),
        point_in_time_rules=("snapshot_time <= event_start_time", "decision_time <= event_start_time", "source_snapshot_time <= event_start_time"),
        numeric_fields=("line_value", "odds", "opening_odds", "closing_odds", "selection_count", "quality_score", "completeness_score"),
        description="Canonical historical market snapshot belonging to one event.",
        time_anchor_field="event_start_time",
        metadata={"stage": "market"},
    ),
    "historical_selections": HistoricalStageContract(
        table_name="historical_selections",
        row_id_field="selection_id",
        required_fields=HISTORICAL_SHARED_REQUIRED_FIELDS
        + (
            "selection_id",
            "batch_id",
            "event_id",
            "event_start_time",
            "market_id",
            "market_family",
            "market_type",
            "market_name",
            "book",
            "selection",
            "selection_side",
            "line_value",
            "odds",
            "opening_odds",
            "closing_odds",
            "price_type",
            "market_label",
            "selection_count",
        ),
        required_timestamps=HISTORICAL_SHARED_REQUIRED_TIMESTAMPS,
        join_keys=("selection_id", "market_id", "event_id", "selection"),
        point_in_time_rules=("snapshot_time <= event_start_time", "decision_time <= event_start_time", "source_snapshot_time <= event_start_time"),
        numeric_fields=("line_value", "odds", "opening_odds", "closing_odds", "quality_score", "completeness_score"),
        description="Canonical historical selection snapshot belonging to one market.",
        time_anchor_field="event_start_time",
        metadata={"stage": "selection"},
    ),
    "historical_research_asset_certifications": HistoricalStageContract(
        table_name="historical_research_asset_certifications",
        row_id_field="certification_id",
        required_fields=HISTORICAL_SHARED_REQUIRED_FIELDS
        + (
            "certification_id",
            "research_asset_id",
            "research_asset_name",
            "asset_category",
            "asset_type",
            "asset_version",
            "certification_version",
            "certification_state",
            "certification_reason",
            "failure_reason",
            "coverage_score",
            "certification_score",
            "required_fields_json",
            "required_timestamps_json",
            "point_in_time_rules_json",
            "validation_json",
            "lineage_json",
            "provenance_json",
            "certification_notes_json",
            "missing_fields_json",
            "duplicate_keys_json",
            "join_keys_json",
            "valid_row_count",
            "invalid_row_count",
            "warning_count",
            "source_row_count",
            "checksum",
        ),
        required_timestamps=HISTORICAL_SHARED_REQUIRED_TIMESTAMPS,
        join_keys=("certification_id", "research_asset_id", "batch_id"),
        point_in_time_rules=("certified_at >= snapshot_time",),
        numeric_fields=("coverage_score", "certification_score", "valid_row_count", "invalid_row_count", "warning_count", "source_row_count", "quality_score", "completeness_score"),
        description="Certification ledger for individual research assets composed into the historical dataset.",
        time_anchor_field="certified_at",
        metadata={"stage": "research_asset_certification"},
    ),
    "historical_certifications": HistoricalStageContract(
        table_name="historical_certifications",
        row_id_field="certification_id",
        required_fields=HISTORICAL_SHARED_REQUIRED_FIELDS
        + (
            "certification_id",
            "batch_id",
            "stage_name",
            "row_count",
            "valid_row_count",
            "invalid_row_count",
            "warning_count",
            "missing_fields_json",
            "duplicate_keys_json",
            "join_keys_json",
            "validation_json",
        ),
        required_timestamps=HISTORICAL_SHARED_REQUIRED_TIMESTAMPS,
        join_keys=("certification_id", "batch_id", "stage_name"),
        point_in_time_rules=("certified_at >= snapshot_time",),
        numeric_fields=("row_count", "valid_row_count", "invalid_row_count", "warning_count", "quality_score", "completeness_score"),
        description="Dataset certification summary for the historical research database.",
        time_anchor_field="certified_at",
        metadata={"stage": "certification"},
    ),
}


def _ensure_profile(profile: MarketProfileContract | Mapping[str, Any] | None = None, *, profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID) -> MarketProfileContract:
    if profile is not None:
        resolved = profile if isinstance(profile, MarketProfileContract) else MarketProfileContract.from_mapping(profile)
    else:
        resolved = get_historical_research_market_profile(profile_id)
    validation = validate_historical_research_profile(resolved)
    if not validation["ok"]:
        raise ValueError("; ".join(validation["errors"]) or "historical research profile validation failed")
    return resolved


def get_historical_research_market_profile(profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID) -> MarketProfileContract:
    profile = get_market_profile(profile_id)
    if profile is not None:
        return profile
    if profile_id == "sports:nfl":
        from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE

        try:
            register_market_profile(NFL_AS_SPORTS_PROFILE_INSTANCE)
        except ValueError:
            pass
        registered = get_market_profile(profile_id)
        return registered or NFL_AS_SPORTS_PROFILE_INSTANCE
    raise KeyError(f"Unknown market profile: {profile_id}")


def validate_historical_research_profile(profile: MarketProfileContract | Mapping[str, Any]) -> dict[str, Any]:
    resolved = profile if isinstance(profile, MarketProfileContract) else MarketProfileContract.from_mapping(profile)
    validation = validate_market_profile_contract(resolved)
    errors = list(validation.get("errors", []))
    warnings = list(validation.get("warnings", []))
    if resolved.profile_family not in {"sports", "prediction_markets", "options_0dte"}:
        errors.append(f"unsupported profile_family: {resolved.profile_family}")
    if not resolved.canonical_identifiers:
        errors.append("canonical_identifiers are required")
    if not resolved.required_timestamps:
        errors.append("required_timestamps are required")
    if not resolved.storage_requirements:
        errors.append("storage_requirements are required")
    if not resolved.backtest_requirements:
        errors.append("backtest_requirements are required")
    if not resolved.worldview_permissions:
        errors.append("worldview_permissions are required")
    if resolved.profile_family == "sports" and "league" not in {item.lower() for item in resolved.canonical_fields}:
        warnings.append("sports profile should include league in canonical_fields")
    return {
        "ok": not errors,
        "profile": resolved,
        "profile_id": resolved.profile_id,
        "profile_family": resolved.profile_family,
        "errors": errors,
        "warnings": warnings,
    }


def create_historical_research_storage_engine(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> LocalStorageEngine:
    path = Path(storage_path or DEFAULT_HISTORICAL_RESEARCH_STORAGE_PATH)
    return create_local_storage_engine(path, backend=backend)


def _historical_row_base(
    *,
    profile: MarketProfileContract,
    stage_name: str,
    row_id: str,
    batch_id: str,
    dataset_version: str,
    source_name: str,
    source_type: str,
    source_key: str,
    source_snapshot_time: str,
    snapshot_time: str,
    decision_time: str,
    certified_at: str,
    status: str,
    point_in_time_status: str,
    leakage_status: str,
    completeness_score: float,
    quality_score: float,
    context: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
    market_type: str | None = None,
    market_profile: str | None = None,
    asset_class: str | None = None,
) -> dict[str, Any]:
    now = created_at or _utc_now_iso()
    updated = updated_at or now
    market_profile_id = market_profile or profile.profile_id
    dataset_id = _normalize_text(payload.get("dataset_id") if payload else None, stage_name)
    dataset_name = _normalize_text(payload.get("dataset_name") if payload else None, stage_name)
    source_signature = _source_signature(source_name, source_snapshot_time)
    base = {
        "dataset_id": dataset_id or stage_name,
        "dataset_name": dataset_name or stage_name,
        "market_profile": market_profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": stage_name,
        "batch_id": batch_id,
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_file": "",
        "source_event_id": "",
        "source_market_id": "",
        "source_selection_id": "",
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": certified_at,
        "certification_status": status,
        "point_in_time_status": point_in_time_status,
        "leakage_status": leakage_status,
        "status": status,
        "completeness_score": completeness_score,
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "source_signature": source_signature,
                "source_snapshot_time": source_snapshot_time,
            }
        ),
        "context_json": _as_json(dict(context or {})),
        "payload_json": _as_json(dict(payload or {})),
        "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
        "created_at": now,
        "updated_at": updated,
        "source": source_name,
        "provider": source_key,
        "market": market_profile_id,
        "market_type": _normalize_text(market_type, stage_name),
        "asset_class": _normalize_text(asset_class, profile.profile_family),
        "snapshot_id": _stable_id("snapshot", stage_name, batch_id, row_id),
        "lineage_id": _stable_id("lineage", stage_name, batch_id, row_id),
        "version_id": dataset_version,
        "quality_score": quality_score,
    }
    return base


def _validate_point_in_time_rows(
    rows: Sequence[Mapping[str, Any]],
    contract: HistoricalStageContract,
) -> tuple[list[str], list[str]]:
    point_in_time_issues: list[str] = []
    lineage_issues: list[str] = []
    for index, row in enumerate(rows):
        anchor = _parse_iso(row.get(contract.time_anchor_field))
        if anchor is None:
            point_in_time_issues.append(f"{index}:missing_{contract.time_anchor_field}")
        for field_name in ("snapshot_time", "source_snapshot_time", "decision_time"):
            field_value = _parse_iso(row.get(field_name))
            if anchor is not None and field_value is not None and field_value > anchor:
                point_in_time_issues.append(f"{index}:{field_name}_after_{contract.time_anchor_field}")
        if contract.table_name == "historical_events":
            result_time = _parse_iso(row.get("result_recorded_time"))
            if anchor is not None and result_time is not None and result_time < anchor:
                point_in_time_issues.append(f"{index}:result_recorded_time_before_event_start")
        if not _normalize_text(row.get("lineage_id")) or not _normalize_text(row.get("snapshot_id")) or not _normalize_text(row.get("version_id")):
            lineage_issues.append(f"{index}:missing_lineage_metadata")
    return point_in_time_issues, lineage_issues


def validate_historical_stage_rows(
    stage_name: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: MarketProfileContract | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = HISTORICAL_STAGE_CONTRACTS[stage_name]
    resolved_profile = _ensure_profile(profile)
    profile_validation = validate_historical_research_profile(resolved_profile)
    base_validation = validate_dataset_rows(rows, required_fields=contract.required_fields)
    missing_rows = list(base_validation.get("missing_rows", []))
    missing_fields = [field for row in missing_rows for field in row.get("missing_fields", [])]
    duplicate_ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        record_id = _normalize_text(row.get(contract.row_id_field))
        if not record_id:
            continue
        if record_id in seen and record_id not in duplicate_ids:
            duplicate_ids.append(record_id)
        seen.add(record_id)
    point_in_time_issues, lineage_issues = _validate_point_in_time_rows(rows, contract)
    type_warnings: list[str] = []
    for field_name in contract.numeric_fields:
        for row in rows:
            value = row.get(field_name)
            if value in (None, ""):
                continue
            try:
                float(value)
            except (TypeError, ValueError):
                type_warnings.append(f"invalid_numeric:{field_name}")
                break
    errors = list(dict.fromkeys(
        [
            *missing_fields,
            *[f"duplicate:{value}" for value in duplicate_ids],
            *[f"point_in_time:{issue}" for issue in point_in_time_issues],
            *[f"lineage:{issue}" for issue in lineage_issues],
            *profile_validation.get("errors", []),
        ]
    ))
    warnings = list(dict.fromkeys([*base_validation.get("warnings", []), *type_warnings, *profile_validation.get("warnings", [])]))
    ok = not errors
    return {
        "ok": ok,
        "status": "certified" if ok else "rejected",
        "stage_name": stage_name,
        "row_count": len(rows),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "missing_fields": missing_fields,
        "duplicate_keys": duplicate_ids,
        "join_keys": [key for row in rows for key in contract.join_keys if not _normalize_text(row.get(key))],
        "point_in_time_issues": point_in_time_issues,
        "lineage_issues": lineage_issues,
        "errors": errors,
        "warnings": warnings,
        "profile_validation": profile_validation,
        "validation_contract": contract.as_dict(),
        "base_validation": base_validation,
    }


def _build_event_context(
    *,
    game_row: Mapping[str, Any],
    schedule_row: Mapping[str, Any] | None = None,
    weather_row: Mapping[str, Any] | None = None,
    result_row: Mapping[str, Any] | None = None,
    home_team_stats: Mapping[str, Any] | None = None,
    away_team_stats: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _context_payload(
        schedule_row=schedule_row or game_row,
        weather_row=weather_row,
        result_row=result_row,
        home_team_stats=home_team_stats,
        away_team_stats=away_team_stats,
        extras={
            "game": dict(game_row),
        },
    )


def build_historical_research_fixture(
    game_count: int = 4,
    *,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
    dataset_version: str | None = None,
) -> dict[str, Any]:
    if profile_id != "sports:nfl":
        raise NotImplementedError("Historical research fixture bootstrap currently seeds NFL first.")
    from src.data.nfl_p0_foundation import build_nfl_p0_fixture

    profile = get_historical_research_market_profile(profile_id)
    nfl_fixture = build_nfl_p0_fixture(game_count)
    version = dataset_version or str(nfl_fixture.get("dataset_version") or "historical.research.v1")
    created_at = str(nfl_fixture.get("created_at") or _utc_now_iso())
    tables = nfl_fixture.get("tables", {})
    games = [dict(row) for row in tables.get("nfl_games", [])]
    schedules = {str(row.get("game_id")): dict(row) for row in tables.get("nfl_schedule", [])}
    results = {str(row.get("game_id")): dict(row) for row in tables.get("nfl_results", [])}
    weather = {str(row.get("game_id")): dict(row) for row in tables.get("nfl_weather_snapshots", [])}
    team_stats: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in tables.get("nfl_team_stats_snapshots", []):
        payload = dict(row)
        team_stats[str(payload.get("game_id"))].append(payload)
    odds_rows = [dict(row) for row in tables.get("nfl_odds_snapshots", [])]

    event_rows: list[dict[str, Any]] = []
    for game in games:
        game_id = _normalize_text(game.get("game_id"))
        schedule_row = schedules.get(game_id) or {}
        result_row = results.get(game_id) or {}
        weather_row = weather.get(game_id) or {}
        team_rows = team_stats.get(game_id, [])
        home_stats = next((row for row in team_rows if _normalize_text(row.get("team_id")) == _normalize_text(game.get("home_team_id"))), {})
        away_stats = next((row for row in team_rows if _normalize_text(row.get("team_id")) == _normalize_text(game.get("away_team_id"))), {})
        event_start_time = _to_iso(game.get("kickoff_time"))
        source_snapshot_time = _to_iso(schedule_row.get("snapshot_time") or game.get("snapshot_time") or created_at)
        result_recorded_time = _to_iso(result_row.get("final_scored_at") or result_row.get("game_time") or game.get("final_scored_at") or event_start_time)
        final_result = _normalize_text(result_row.get("final_result"))
        if not final_result:
            winner_team = _normalize_text(result_row.get("winner_team"))
            home_team = _normalize_text(game.get("home_team"))
            away_team = _normalize_text(game.get("away_team"))
            if winner_team and winner_team == home_team:
                final_result = "home_win"
            elif winner_team and winner_team == away_team:
                final_result = "away_win"
            elif _normalize_text(result_row.get("final_score_home")) == _normalize_text(result_row.get("final_score_away")):
                final_result = "draw"
            else:
                final_result = "unknown"
        event_snapshot_id = _stable_id("historical_event_snapshot", profile.profile_id, game_id, source_snapshot_time)
        event_lineage_id = _stable_id("historical_event_lineage", profile.profile_id, game_id, source_snapshot_time)
        event_lineage_record = create_lineage_record(
            provider_id=profile.profile_id,
            provider_type=profile.profile_family,
            payload_schema_version=HISTORICAL_RESEARCH_SCHEMA_VERSION,
            snapshot_id=event_snapshot_id,
            source_type=DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
            schema_version=HISTORICAL_RESEARCH_SCHEMA_VERSION,
            lineage_id=event_lineage_id,
            dataset_id="historical_events",
            dataset_name="historical_events",
            source_record_id=game_id,
            target_record_id=game_id,
            source_stage="acquisition",
            target_stage="event",
            transformation="certify_event_context",
        )
        payload = {
            **dict(game),
            "schedule": schedule_row,
            "weather": weather_row,
            "result": result_row,
            "team_stats": {"home": home_stats, "away": away_stats},
        }
        context = _build_event_context(
            game_row=game,
            schedule_row=schedule_row,
            weather_row=weather_row,
            result_row=result_row,
            home_team_stats=home_stats,
            away_team_stats=away_stats,
        )
        context["lineage_record"] = event_lineage_record
        event_row = {
            "dataset_id": "historical_events",
            "dataset_name": "historical_events",
            "market_profile": profile.profile_id,
            "profile_id": profile.profile_id,
            "profile_family": profile.profile_family,
            "stage_name": "historical_events",
            "batch_id": f"{version}.batch.001",
            "event_id": game_id,
            "event_key": game_id,
            "sport": profile.metadata.get("sport") or "americanfootball_nfl",
            "league": _normalize_text(profile.metadata.get("league"), "NFL"),
            "season": int(_normalize_text(game.get("season"), "0") or 0),
            "season_type": _normalize_text(game.get("season_type"), "regular"),
            "week": int(_normalize_text(game.get("week"), "0") or 0),
            "game_id": game_id,
            "event_date": _to_iso(game.get("game_date")),
            "event_start_time": event_start_time,
            "home_team": _normalize_text(game.get("home_team")),
            "away_team": _normalize_text(game.get("away_team")),
            "venue_id": _normalize_text(game.get("venue_id")),
            "venue_name": _normalize_text(game.get("venue_name")),
            "venue_city": _normalize_text(game.get("venue_city")),
            "venue_state": _normalize_text(game.get("venue_state")),
            "neutral_site": int(_normalize_text(game.get("neutral_site"), "0") or 0),
            "final_result": final_result,
            "final_score_home": int(_normalize_text(result_row.get("final_score_home"), "0") or 0) if result_row else None,
            "final_score_away": int(_normalize_text(result_row.get("final_score_away"), "0") or 0) if result_row else None,
            "winner_team": _normalize_text(result_row.get("winner_team")),
            "margin": int(_normalize_text(result_row.get("margin"), "0") or 0) if result_row else 0,
            "total_points": int(_normalize_text(result_row.get("total_points"), "0") or 0) if result_row else 0,
            "result_recorded_time": result_recorded_time,
            "result_status": _normalize_text(result_row.get("status"), "final"),
            "settlement_status": _normalize_text(result_row.get("settlement_status"), "settled"),
            "source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
            "source_key": DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
            "source_snapshot_time": source_snapshot_time,
            "snapshot_time": source_snapshot_time,
            "decision_time": source_snapshot_time,
            "certified_at": created_at,
            "certification_status": "certified",
            "point_in_time_status": "safe",
            "leakage_status": "none",
            "status": "certified",
            "source_metadata_json": _as_json(
                {
                    "source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
                    "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
                    "source_key": DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
                    "source_signature": _source_signature(DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME, source_snapshot_time),
                }
            ),
            "context_json": _as_json(context),
            "payload_json": _as_json(payload),
            "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
            "created_at": created_at,
            "updated_at": created_at,
            "source": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "provider": DEFAULT_HISTORICAL_RESEARCH_PROVIDER,
            "market": profile.profile_id,
            "market_type": "event",
            "asset_class": profile.profile_family,
            "snapshot_id": event_snapshot_id,
            "lineage_id": event_lineage_id,
            "version_id": version,
            "quality_score": 1.0,
            "completeness_score": 1.0,
        }
        event_rows.append(event_row)

    event_index = build_event_link_index(event_rows)
    market_rows = normalize_historical_market_rows(
        odds_rows,
        profile=profile,
        dataset_version=version,
        batch_id=f"{version}.batch.001",
        created_at=created_at,
        updated_at=created_at,
        canonical_event_rows=event_rows,
        event_index=event_index,
    )
    selection_rows = normalize_historical_selection_rows(
        odds_rows,
        profile=profile,
        dataset_version=version,
        batch_id=f"{version}.batch.001",
        created_at=created_at,
        updated_at=created_at,
        canonical_event_rows=event_rows,
        event_index=event_index,
    )

    acquisition_batches = [
        {
            "dataset_id": "historical_acquisition_batches",
            "dataset_name": "historical_acquisition_batches",
            "market_profile": profile.profile_id,
            "profile_id": profile.profile_id,
            "profile_family": profile.profile_family,
            "stage_name": "historical_acquisition_batches",
            "batch_id": f"{version}.batch.001",
            "acquisition_started_at": created_at,
            "acquisition_completed_at": created_at,
            "source_count": 1,
            "event_count": len(event_rows),
            "market_count": len(market_rows),
            "selection_count": len(selection_rows),
            "certified_row_count": len(event_rows) + len(market_rows) + len(selection_rows),
            "rejected_row_count": 0,
            "coverage_json": _as_json(
                {
                    "historical": True,
                    "event_centric": True,
                    "markets": ["spread", "moneyline", "total"],
                    "selection_rows": len(selection_rows),
                }
            ),
            "licensing_json": _as_json({"status": "documentation_only", "notes": ["See phase report for candidate source review."]}),
            "provenance_json": _as_json({"source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME, "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE}),
            "notes_json": _as_json(
                {
                    "fixture": True,
                    "decision_rows_deferred": True,
                    "feature_population_next": True,
                }
            ),
            "source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
            "source_key": DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
            "source_snapshot_time": created_at,
            "snapshot_time": created_at,
            "decision_time": created_at,
            "certified_at": created_at,
            "certification_status": "certified",
            "point_in_time_status": "safe",
            "leakage_status": "none",
            "status": "certified",
            "source_metadata_json": _as_json(
                {
                    "source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
                    "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
                    "source_key": DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
                }
            ),
            "context_json": _as_json({"profile": profile.as_dict(), "event_index": event_index}),
            "payload_json": _as_json({"profile": profile.as_dict(), "event_count": len(event_rows)}),
            "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
            "created_at": created_at,
            "updated_at": created_at,
            "source": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "provider": DEFAULT_HISTORICAL_RESEARCH_PROVIDER,
            "market": profile.profile_id,
            "market_type": "acquisition_batch",
            "asset_class": profile.profile_family,
            "snapshot_id": _stable_id("historical_acquisition_snapshot", profile.profile_id, version, "batch", "001"),
            "lineage_id": _stable_id("historical_acquisition_lineage", profile.profile_id, version, "batch", "001"),
            "version_id": version,
            "quality_score": 1.0,
            "completeness_score": 1.0,
        }
    ]

    source_tables = {name: [dict(row) for row in rows] for name, rows in tables.items()}

    certifications = [
        {
            "dataset_id": "historical_certifications",
            "dataset_name": "historical_certifications",
            "market_profile": profile.profile_id,
            "profile_id": profile.profile_id,
            "profile_family": profile.profile_family,
            "stage_name": "historical_certifications",
            "certification_id": _stable_id("historical_certification", profile.profile_id, version, "bundle"),
            "batch_id": f"{version}.batch.001",
            "row_count": len(event_rows) + len(market_rows) + len(selection_rows),
            "valid_row_count": len(event_rows) + len(market_rows) + len(selection_rows),
            "invalid_row_count": 0,
            "warning_count": 0,
            "missing_fields_json": _as_json([]),
            "duplicate_keys_json": _as_json([]),
            "join_keys_json": _as_json([]),
            "validation_json": _as_json({"ok": True, "status": "certified"}),
            "source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
            "source_key": DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
            "source_snapshot_time": created_at,
            "snapshot_time": created_at,
            "decision_time": created_at,
            "certified_at": created_at,
            "certification_status": "certified",
            "point_in_time_status": "safe",
            "leakage_status": "none",
            "status": "certified",
            "source_metadata_json": _as_json({"source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME, "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE}),
            "context_json": _as_json({"profile": profile.as_dict(), "batch_id": f"{version}.batch.001"}),
            "payload_json": _as_json({"profile": profile.as_dict(), "batch_id": f"{version}.batch.001"}),
            "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
            "created_at": created_at,
            "updated_at": created_at,
            "source": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "provider": DEFAULT_HISTORICAL_RESEARCH_PROVIDER,
            "market": profile.profile_id,
            "market_type": "certification",
            "asset_class": profile.profile_family,
            "snapshot_id": _stable_id("historical_certification_snapshot", profile.profile_id, version, "bundle"),
            "lineage_id": _stable_id("historical_certification_lineage", profile.profile_id, version, "bundle"),
            "version_id": version,
            "quality_score": 1.0,
            "completeness_score": 1.0,
        }
    ]

    return {
        "profile": profile,
        "dataset_version": version,
        "created_at": created_at,
        "acquisition_batches": acquisition_batches,
        "events": event_rows,
        "markets": market_rows,
        "selections": selection_rows,
        "certifications": certifications,
        "source_tables": source_tables,
        "source_bundle": {
            "source_name": DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
            "source_type": DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
            "source_key": DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
            "provider": DEFAULT_HISTORICAL_RESEARCH_PROVIDER,
            "source_count": 1,
            "provider_sources": [DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME],
            "provider_versions": [version],
            "acquisition_timestamp": created_at,
            "source_tables": source_tables,
        },
        "event_index": event_index,
    }


def _normalize_event_source_row(
    row: Mapping[str, Any],
    *,
    profile: MarketProfileContract,
    batch_id: str,
    dataset_version: str,
    created_at: str,
    updated_at: str,
    source_name: str,
    source_type: str,
    source_key: str,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(row)
    source_snapshot_time = _to_iso(payload.get("source_snapshot_time") or payload.get("snapshot_time") or created_at)
    snapshot_time = _to_iso(payload.get("snapshot_time") or source_snapshot_time)
    decision_time = _to_iso(payload.get("decision_time") or snapshot_time)
    event_start_time = _to_iso(payload.get("event_start_time") or payload.get("kickoff_time") or payload.get("event_date") or snapshot_time)
    event_id = _normalize_text(payload.get("event_id") or payload.get("game_id") or payload.get("source_event_id"))
    event_key = _normalize_text(payload.get("event_key") or event_id)
    return {
        "dataset_id": "historical_events",
        "dataset_name": "historical_events",
        "market_profile": profile.profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": "historical_events",
        "batch_id": batch_id,
        "event_id": event_id or _stable_id("historical_event", profile.profile_id, event_key, source_snapshot_time),
        "event_key": event_key or _stable_id("historical_event_key", profile.profile_id, event_start_time, payload.get("home_team"), payload.get("away_team")),
        "sport": _normalize_text(payload.get("sport") or profile.metadata.get("sport") or "americanfootball_nfl"),
        "league": _normalize_text(payload.get("league") or profile.metadata.get("league") or "NFL"),
        "season": int(_normalize_text(payload.get("season"), "0") or 0),
        "season_type": _normalize_text(payload.get("season_type"), "regular"),
        "week": int(_normalize_text(payload.get("week"), "0") or 0),
        "game_id": _normalize_text(payload.get("game_id") or event_id),
        "event_date": _to_iso(payload.get("event_date") or payload.get("game_date") or event_start_time),
        "event_start_time": event_start_time,
        "home_team": _normalize_text(payload.get("home_team")),
        "away_team": _normalize_text(payload.get("away_team")),
        "venue_id": _normalize_text(payload.get("venue_id")),
        "venue_name": _normalize_text(payload.get("venue_name")),
        "venue_city": _normalize_text(payload.get("venue_city")),
        "venue_state": _normalize_text(payload.get("venue_state")),
        "neutral_site": int(_normalize_text(payload.get("neutral_site"), "0") or 0),
        "final_result": _normalize_text(payload.get("final_result")),
        "final_score_home": int(_normalize_text(payload.get("final_score_home"), "0") or 0) if payload.get("final_score_home") not in (None, "") else None,
        "final_score_away": int(_normalize_text(payload.get("final_score_away"), "0") or 0) if payload.get("final_score_away") not in (None, "") else None,
        "winner_team": _normalize_text(payload.get("winner_team")),
        "margin": int(_normalize_text(payload.get("margin"), "0") or 0) if payload.get("margin") not in (None, "") else 0,
        "total_points": int(_normalize_text(payload.get("total_points"), "0") or 0) if payload.get("total_points") not in (None, "") else 0,
        "result_recorded_time": _to_iso(payload.get("result_recorded_time") or payload.get("final_scored_at") or event_start_time),
        "result_status": _normalize_text(payload.get("result_status"), "certified"),
        "settlement_status": _normalize_text(payload.get("settlement_status"), "settled"),
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": created_at,
        "certification_status": "certified",
        "point_in_time_status": "safe" if snapshot_time <= event_start_time else "needs_review",
        "leakage_status": "none" if snapshot_time <= event_start_time else "possible",
        "status": "certified" if snapshot_time <= event_start_time else "review",
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "source_snapshot_time": source_snapshot_time,
            }
        ),
        "context_json": _as_json(dict(context or {})),
        "payload_json": _as_json(payload),
        "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": updated_at,
        "source": source_name,
        "provider": source_key,
        "market": profile.profile_id,
        "market_type": "event",
        "asset_class": profile.profile_family,
        "snapshot_id": _stable_id("historical_event_snapshot", profile.profile_id, event_id, snapshot_time),
        "lineage_id": _stable_id("historical_event_lineage", profile.profile_id, event_id, snapshot_time),
        "version_id": dataset_version,
        "quality_score": 1.0,
        "completeness_score": 1.0,
    }


def normalize_historical_event_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: MarketProfileContract | Mapping[str, Any] | None = None,
    batch_id: str,
    dataset_version: str,
    created_at: str | None = None,
    updated_at: str | None = None,
    source_name: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
    source_type: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
    source_key: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
    context_rows: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    resolved_profile = _ensure_profile(profile)
    now = created_at or _utc_now_iso()
    changed = updated_at or now
    normalized: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        event_key = _normalize_text(payload.get("event_id") or payload.get("game_id") or payload.get("source_event_id"))
        context = dict((context_rows or {}).get(event_key, {}))
        normalized.append(
            _normalize_event_source_row(
                payload,
                profile=resolved_profile,
                batch_id=batch_id,
                dataset_version=dataset_version,
                created_at=now,
                updated_at=changed,
                source_name=source_name,
                source_type=source_type,
                source_key=source_key,
                context=context,
            )
        )
    return normalized


def _normalize_market_or_selection_source_row(
    row: Mapping[str, Any],
    *,
    profile: MarketProfileContract,
    batch_id: str,
    dataset_version: str,
    created_at: str,
    updated_at: str,
    source_name: str,
    source_type: str,
    source_key: str,
    event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: Mapping[str, Any] | None = None,
    stage: str = "market",
) -> dict[str, Any]:
    payload = dict(row)
    resolution = resolve_source_event_links(
        [payload],
        canonical_event_rows=event_rows,
        event_index=event_index,
        limit=1,
    )
    resolved_row = dict(payload)
    if resolution.get("rows"):
        row_resolution = resolution["rows"][0]
        if row_resolution.get("resolved") and row_resolution.get("event_id"):
            resolved_row["event_id"] = row_resolution["event_id"]
    event_id = _normalize_text(resolved_row.get("event_id") or resolved_row.get("game_id") or resolved_row.get("source_event_id"))
    market = _normalize_text(resolved_row.get("market") or resolved_row.get("market_type"))
    selection = _normalize_text(resolved_row.get("selection"))
    source_snapshot_time = _to_iso(resolved_row.get("source_snapshot_time") or resolved_row.get("snapshot_time") or created_at)
    snapshot_time = _to_iso(resolved_row.get("snapshot_time") or source_snapshot_time)
    decision_time = _to_iso(resolved_row.get("decision_time") or snapshot_time)
    event_start_time = ""
    if event_rows:
        for event_row in event_rows:
            if _normalize_text(event_row.get("event_id")) == event_id:
                event_start_time = _normalize_text(event_row.get("event_start_time"))
                break
    market_family = _market_family(market, selection)
    market_name = _normalize_text(resolved_row.get("market_label") or resolved_row.get("market_name") or market)
    market_id_seed = [profile.profile_id, event_id, market_family, market, _normalize_text(resolved_row.get("book")), selection, source_snapshot_time]
    if stage == "selection":
        row_id = _normalize_text(resolved_row.get("selection_id")) or _stable_id("historical_selection", *market_id_seed)
    else:
        row_id = _normalize_text(resolved_row.get("market_id")) or _stable_id("historical_market", *market_id_seed)
    market_id = _normalize_text(resolved_row.get("market_id")) or _stable_id("historical_market_id", profile.profile_id, event_id, market_family, market, _normalize_text(resolved_row.get("book")))
    base = {
        "dataset_id": "historical_markets" if stage == "market" else "historical_selections",
        "dataset_name": "historical_markets" if stage == "market" else "historical_selections",
        "market_profile": profile.profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": "historical_markets" if stage == "market" else "historical_selections",
        "batch_id": batch_id,
        "event_id": event_id,
        "event_start_time": event_start_time,
        "market_id": market_id,
        "market_family": market_family,
        "market_type": market or market_family,
        "market_name": market_name,
        "book": _normalize_text(resolved_row.get("book") or resolved_row.get("bookmaker") or "unknown"),
        "line_value": _normalize_float(resolved_row.get("line_value") or resolved_row.get("line")),
        "odds": _normalize_float(resolved_row.get("odds") or resolved_row.get("american_odds")),
        "opening_odds": _normalize_float(resolved_row.get("opening_odds") or resolved_row.get("odds") or resolved_row.get("american_odds")),
        "closing_odds": _normalize_float(resolved_row.get("closing_odds") or resolved_row.get("odds") or resolved_row.get("american_odds")),
        "price_type": _normalize_text(resolved_row.get("price_type"), "american"),
        "market_label": _normalize_text(resolved_row.get("market_label") or market_name),
        "selection_count": int(_normalize_text(resolved_row.get("selection_count"), "1") or 1),
        "selection": selection,
        "selection_side": _normalize_text(resolved_row.get("selection_side") or selection),
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": created_at,
        "certification_status": "certified",
        "point_in_time_status": "safe" if event_start_time and snapshot_time <= event_start_time else "needs_review",
        "leakage_status": "none" if event_start_time and snapshot_time <= event_start_time else "possible",
        "status": "certified" if event_start_time and snapshot_time <= event_start_time else "review",
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "source_snapshot_time": source_snapshot_time,
            }
        ),
        "context_json": _as_json(
            {
                "event_id": event_id,
                "event_start_time": event_start_time,
                "market_family": market_family,
                "market_type": market,
                "selection": selection,
            }
        ),
        "payload_json": _as_json(resolved_row),
        "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": updated_at,
        "source": source_name,
        "provider": source_key,
        "market": profile.profile_id,
        "market_type": market or market_family,
        "asset_class": profile.profile_family,
        "snapshot_id": _stable_id("historical_snapshot", stage, profile.profile_id, event_id, market_id, row_id, snapshot_time),
        "lineage_id": _stable_id("historical_lineage", stage, profile.profile_id, event_id, market_id, row_id, snapshot_time),
        "version_id": dataset_version,
        "quality_score": 1.0,
        "completeness_score": 1.0,
    }
    if stage == "selection":
        base["selection_id"] = row_id
    return base


def normalize_historical_market_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: MarketProfileContract | Mapping[str, Any] | None = None,
    batch_id: str,
    dataset_version: str,
    created_at: str | None = None,
    updated_at: str | None = None,
    source_name: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
    source_type: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
    source_key: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    resolved_profile = _ensure_profile(profile)
    now = created_at or _utc_now_iso()
    changed = updated_at or now
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        payload = dict(row)
        resolution = resolve_source_event_links(
            [payload],
            canonical_event_rows=canonical_event_rows,
            event_index=event_index,
            limit=1,
        )
        if resolution.get("rows"):
            row_resolution = resolution["rows"][0]
            if row_resolution.get("resolved") and row_resolution.get("event_id"):
                payload["event_id"] = row_resolution["event_id"]
        event_id = _normalize_text(payload.get("event_id") or payload.get("game_id") or payload.get("source_event_id"))
        market = _normalize_text(payload.get("market") or payload.get("market_type"))
        book = _normalize_text(payload.get("book") or payload.get("bookmaker") or "unknown")
        grouped[(event_id, market, book)].append(payload)
    normalized: list[dict[str, Any]] = []
    for (event_id, market, book), grouped_rows in grouped.items():
        first = grouped_rows[0]
        market_family = _market_family(market, first.get("selection"))
        event_start_time = ""
        if canonical_event_rows:
            for event_row in canonical_event_rows:
                if _normalize_text(event_row.get("event_id")) == event_id:
                    event_start_time = _normalize_text(event_row.get("event_start_time"))
                    break
        selection_count = len(grouped_rows)
        market_id = _stable_id("historical_market_id", resolved_profile.profile_id, event_id, market_family, market, book)
        source_snapshot_time = _to_iso(first.get("source_snapshot_time") or first.get("snapshot_time") or now)
        snapshot_time = _to_iso(first.get("snapshot_time") or source_snapshot_time)
        decision_time = _to_iso(first.get("decision_time") or snapshot_time)
        market_row = {
            "dataset_id": "historical_markets",
            "dataset_name": "historical_markets",
            "market_profile": resolved_profile.profile_id,
            "profile_id": resolved_profile.profile_id,
            "profile_family": resolved_profile.profile_family,
            "stage_name": "historical_markets",
            "batch_id": batch_id,
            "event_id": event_id,
            "event_start_time": event_start_time,
            "market_id": market_id,
            "market_family": market_family,
            "market_type": market or market_family,
            "market_name": _normalize_text(first.get("market_label") or first.get("market_name") or market),
            "book": book,
            "line_value": _normalize_float(first.get("line_value") or first.get("line")),
            "odds": _normalize_float(first.get("odds") or first.get("american_odds")),
            "opening_odds": _normalize_float(first.get("opening_odds") or first.get("odds") or first.get("american_odds")),
            "closing_odds": _normalize_float(first.get("closing_odds") or first.get("odds") or first.get("american_odds")),
            "price_type": _normalize_text(first.get("price_type"), "american"),
            "market_label": _normalize_text(first.get("market_label") or first.get("market_name") or market),
            "selection_count": selection_count,
            "source_name": source_name,
            "source_type": source_type,
            "source_key": source_key,
            "source_snapshot_time": source_snapshot_time,
            "snapshot_time": snapshot_time,
            "decision_time": decision_time,
            "certified_at": now,
            "certification_status": "certified",
            "point_in_time_status": "safe" if event_start_time and snapshot_time <= event_start_time else "needs_review",
            "leakage_status": "none" if event_start_time and snapshot_time <= event_start_time else "possible",
            "status": "certified" if event_start_time and snapshot_time <= event_start_time else "review",
            "source_metadata_json": _as_json(
                {
                    "source_name": source_name,
                    "source_type": source_type,
                    "source_key": source_key,
                    "source_snapshot_time": source_snapshot_time,
                }
            ),
            "context_json": _as_json({"event_id": event_id, "selection_count": selection_count, "book": book, "market": market}),
            "payload_json": _as_json({"rows": grouped_rows}),
            "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
            "created_at": now,
            "updated_at": changed,
            "source": source_name,
            "provider": source_key,
            "market": resolved_profile.profile_id,
            "market_type": market or market_family,
            "asset_class": resolved_profile.profile_family,
            "snapshot_id": _stable_id("historical_market_snapshot", resolved_profile.profile_id, event_id, market_id, snapshot_time),
            "lineage_id": _stable_id("historical_market_lineage", resolved_profile.profile_id, event_id, market_id, snapshot_time),
            "version_id": dataset_version,
            "quality_score": 1.0,
            "completeness_score": 1.0,
        }
        normalized.append(market_row)
    return normalized


def normalize_historical_selection_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: MarketProfileContract | Mapping[str, Any] | None = None,
    batch_id: str,
    dataset_version: str,
    created_at: str | None = None,
    updated_at: str | None = None,
    source_name: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME,
    source_type: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE,
    source_key: str = DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY,
    canonical_event_rows: Sequence[Mapping[str, Any]] | None = None,
    event_index: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    resolved_profile = _ensure_profile(profile)
    now = created_at or _utc_now_iso()
    changed = updated_at or now
    normalized: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        normalized.append(
            _normalize_market_or_selection_source_row(
                payload,
                profile=resolved_profile,
                batch_id=batch_id,
                dataset_version=dataset_version,
                created_at=now,
                updated_at=changed,
                source_name=source_name,
                source_type=source_type,
                source_key=source_key,
                event_rows=canonical_event_rows,
                event_index=event_index,
                stage="selection",
            )
        )
    return normalized


def _store_stage_rows(storage: LocalStorageEngine, stage_name: str, rows: Sequence[Mapping[str, Any]]) -> None:
    contract = HISTORICAL_STAGE_CONTRACTS[stage_name]
    for row in rows:
        storage.upsert(contract.table_name, row, key_columns=(contract.row_id_field,))


def _build_certification_row(
    *,
    profile: MarketProfileContract,
    batch_id: str,
    dataset_version: str,
    stage_name: str,
    validation: Mapping[str, Any],
    source_name: str,
    source_type: str,
    source_key: str,
    created_at: str,
) -> dict[str, Any]:
    contract = HISTORICAL_STAGE_CONTRACTS["historical_certifications"]
    row = {
        "dataset_id": "historical_certifications",
        "dataset_name": "historical_certifications",
        "market_profile": profile.profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": stage_name,
        "batch_id": batch_id,
        "certification_id": _stable_id("historical_certification", profile.profile_id, dataset_version, stage_name, batch_id),
        "row_count": int(validation.get("row_count") or 0),
        "valid_row_count": int(validation.get("row_count") or 0) - int(validation.get("error_count") or 0),
        "invalid_row_count": int(validation.get("error_count") or 0),
        "warning_count": int(validation.get("warning_count") or 0),
        "missing_fields_json": _as_json(validation.get("missing_fields") or []),
        "duplicate_keys_json": _as_json(validation.get("duplicate_keys") or []),
        "join_keys_json": _as_json(validation.get("join_keys") or []),
        "validation_json": _as_json(dict(validation)),
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_snapshot_time": created_at,
        "snapshot_time": created_at,
        "decision_time": created_at,
        "certified_at": created_at,
        "certification_status": "certified" if validation.get("ok") else "rejected",
        "point_in_time_status": "safe" if validation.get("ok") else "blocked",
        "leakage_status": "none" if validation.get("ok") else "suspect",
        "status": "certified" if validation.get("ok") else "rejected",
        "source_metadata_json": _as_json({"source_name": source_name, "source_type": source_type, "source_key": source_key}),
        "context_json": _as_json({"profile": profile.as_dict(), "stage_name": stage_name}),
        "payload_json": _as_json(dict(validation)),
        "schema_version": HISTORICAL_RESEARCH_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": source_name,
        "provider": source_key,
        "market": profile.profile_id,
        "market_type": "certification",
        "asset_class": profile.profile_family,
        "snapshot_id": _stable_id("historical_certification_snapshot", profile.profile_id, dataset_version, stage_name, batch_id),
        "lineage_id": _stable_id("historical_certification_lineage", profile.profile_id, dataset_version, stage_name, batch_id),
        "version_id": dataset_version,
        "quality_score": 1.0 if validation.get("ok") else 0.0,
        "completeness_score": 1.0,
    }
    contract_validation = validate_dataset_rows([row], required_fields=contract.required_fields)
    if not contract_validation["ok"]:
        row["status"] = "rejected"
    return row


class HistoricalResearchDatabase:
    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        backend: str = "sqlite",
        dataset_owner: str = DEFAULT_HISTORICAL_RESEARCH_OWNER,
    ) -> None:
        self.storage_path = Path(storage_path or DEFAULT_HISTORICAL_RESEARCH_STORAGE_PATH).expanduser().resolve()
        self.backend = str(backend or "sqlite").strip().lower()
        self.dataset_owner = _normalize_text(dataset_owner, DEFAULT_HISTORICAL_RESEARCH_OWNER)
        self.store = create_historical_research_storage_engine(self.storage_path, backend=self.backend)
        self.store.ensure_schema()

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "HistoricalResearchDatabase":
        _ = self.store.connection
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def list_rows(self, stage_name: str) -> list[dict[str, Any]]:
        contract = HISTORICAL_STAGE_CONTRACTS[stage_name]
        order_by = contract.row_id_field
        return self.store.fetch(contract.table_name, order_by=order_by)

    def list_events(self) -> list[dict[str, Any]]:
        return self.list_rows("historical_events")

    def list_markets(self) -> list[dict[str, Any]]:
        return self.list_rows("historical_markets")

    def list_selections(self) -> list[dict[str, Any]]:
        return self.list_rows("historical_selections")

    def list_acquisition_batches(self) -> list[dict[str, Any]]:
        return self.list_rows("historical_acquisition_batches")

    def list_certifications(self) -> list[dict[str, Any]]:
        return self.list_rows("historical_certifications")

    def list_research_asset_certifications(self) -> list[dict[str, Any]]:
        return self.list_rows("historical_research_asset_certifications")

    def bootstrap(
        self,
        *,
        profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
        fixture: Mapping[str, Any] | None = None,
        game_count: int = 4,
    ) -> dict[str, Any]:
        profile = get_historical_research_market_profile(profile_id)
        profile_validation = validate_historical_research_profile(profile)
        if not profile_validation["ok"]:
            raise ValueError("; ".join(profile_validation["errors"]) or "historical research profile validation failed")
        fixture_payload = dict(fixture or build_historical_research_fixture(game_count=game_count, profile_id=profile_id))
        version = _normalize_text(fixture_payload.get("dataset_version"), "historical.research.v1")
        created_at = _utc_now_iso()
        source_bundle = dict(fixture_payload.get("source_bundle") or {})
        source_name = _normalize_text(source_bundle.get("source_name"), DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME)
        source_type = _normalize_text(source_bundle.get("source_type"), DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE)
        source_key = _normalize_text(source_bundle.get("source_key"), DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY)
        with HistoricalDatasetAcquisitionRuntime(self.storage_path, backend=self.backend, dataset_owner=self.dataset_owner) as acquisition_runtime:
            raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
                fixture_payload,
                profile_id=profile_id,
            )
        batch_rows = [dict(row) for row in fixture_payload.get("acquisition_batches", [])]
        event_rows = [dict(row) for row in fixture_payload.get("events", [])]
        market_rows = [dict(row) for row in fixture_payload.get("markets", [])]
        selection_rows = [dict(row) for row in fixture_payload.get("selections", [])]

        stage_results: dict[str, dict[str, Any]] = {}
        for stage_name, rows in (
            ("historical_acquisition_batches", batch_rows),
            ("historical_events", event_rows),
            ("historical_markets", market_rows),
            ("historical_selections", selection_rows),
        ):
            validation = validate_historical_stage_rows(stage_name, rows, profile=profile)
            _store_stage_rows(self.store, stage_name, rows)
            stage_results[stage_name] = {
                **validation,
                "stored_row_count": self.store.count(stage_name),
            }

        certification_runtime = HistoricalResearchAssetCertificationRuntime(
            self.storage_path,
            backend=self.backend,
            dataset_owner=self.dataset_owner,
            store=self.store,
        )
        certification_result = certification_runtime.certify(
            fixture=fixture_payload,
            profile_id=profile_id,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=version,
            created_at=created_at,
            batch_id=batch_rows[0]["batch_id"] if batch_rows else f"{version}.batch.001",
        )

        readiness = self.build_readiness_snapshot(
            profile=profile,
            fixture=fixture_payload,
            precomputed_results=stage_results,
            raw_acquisition_result=raw_acquisition_result,
        )
        readiness["bootstrap"] = {
            "dataset_version": version,
            "source_bundle": source_bundle,
            "raw_acquisition_result": {
                "ok": raw_acquisition_result.get("ok"),
                "status": raw_acquisition_result.get("status"),
                "raw_record_count": raw_acquisition_result.get("raw_record_count"),
                "dataset_id": (raw_acquisition_result.get("contract") or {}).get("dataset_id"),
            },
            "stage_results": stage_results,
            "certification_result": certification_result,
        }
        return readiness

    def build_readiness_snapshot(
        self,
        *,
        profile: MarketProfileContract | Mapping[str, Any] | None = None,
        fixture: Mapping[str, Any] | None = None,
        precomputed_results: Mapping[str, Mapping[str, Any]] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_profile = _ensure_profile(profile)
        profile_validation = validate_historical_research_profile(resolved_profile)
        raw_acquisition_result = dict(raw_acquisition_result or {})
        raw_acquisition_snapshot = dict(raw_acquisition_result.get("readiness_snapshot") or raw_acquisition_result)
        if not raw_acquisition_snapshot:
            with HistoricalDatasetAcquisitionRuntime(self.storage_path, backend=self.backend, dataset_owner=self.dataset_owner) as acquisition_runtime:
                raw_acquisition_snapshot = acquisition_runtime.build_readiness_snapshot(
                    profile_id=resolved_profile.profile_id,
                    source_bundle=(fixture or {}).get("source_bundle") or fixture or {},
                )
        certification_runtime = HistoricalResearchAssetCertificationRuntime(
            self.storage_path,
            backend=self.backend,
            dataset_owner=self.dataset_owner,
            store=self.store,
        )
        certification_snapshot = certification_runtime.build_readiness_snapshot(
            profile_id=resolved_profile.profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
        stage_readiness: dict[str, dict[str, Any]] = {}
        ready_stages: list[str] = []
        missing_stages: list[str] = []
        blocked_stages: list[str] = []
        profile_status = "ready" if profile_validation["ok"] else "blocked"
        for stage_name, contract in HISTORICAL_STAGE_CONTRACTS.items():
            exists = self.store.table_exists(contract.table_name)
            rows = self.store.fetch(contract.table_name, order_by=f"{contract.row_id_field} ASC") if exists else []
            validation = dict((precomputed_results or {}).get(contract.table_name) or validate_historical_stage_rows(contract.table_name, rows, profile=resolved_profile))
            stage_status = "ready" if exists and rows and validation.get("ok") else "missing" if not exists or not rows else "blocked"
            stage_readiness[contract.table_name] = {
                "table_name": contract.table_name,
                "exists": exists,
                "row_count": len(rows),
                "status": stage_status,
                "validation": validation,
                "required_fields": list(contract.required_fields),
                "required_timestamps": list(contract.required_timestamps),
                "point_in_time_rules": list(contract.point_in_time_rules),
                "description": contract.description,
            }
            if stage_status == "ready":
                ready_stages.append(contract.table_name)
            elif stage_status == "missing":
                missing_stages.append(contract.table_name)
            else:
                blocked_stages.append(contract.table_name)
        raw_cache_ok = bool(raw_acquisition_snapshot.get("ok"))
        certification_ok = bool(certification_snapshot.get("ok"))
        overall_status = (
            "ready"
            if profile_validation["ok"] and raw_cache_ok and certification_ok and len(ready_stages) == len(HISTORICAL_STAGE_CONTRACTS)
            else "partial"
            if ready_stages and profile_validation["ok"]
            else "blocked"
            if not profile_validation["ok"] or (raw_acquisition_snapshot and not raw_cache_ok) or not certification_ok
            else "missing"
        )
        return {
            "ok": overall_status == "ready",
            "status": overall_status,
            "dataset_name": HISTORICAL_RESEARCH_DATASET_NAME,
            "dataset_version": _normalize_text((fixture or {}).get("dataset_version"), "historical.research.v1"),
            "storage": self.store.health(),
            "market_profile": profile_validation,
            "raw_acquisition_cache": raw_acquisition_snapshot.get("raw_acquisition_cache") if raw_acquisition_snapshot else {},
            "research_asset_certification": certification_snapshot,
            "table_readiness": stage_readiness,
            "ready_tables": ready_stages,
            "missing_tables": missing_stages,
            "blocked_tables": blocked_stages,
            "summary": {
                "table_count": len(HISTORICAL_STAGE_CONTRACTS),
                "ready_table_count": len(ready_stages),
                "missing_table_count": len(missing_stages),
                "blocked_table_count": len(blocked_stages),
                "market_profile_status": profile_status,
                "raw_acquisition_cache_status": raw_acquisition_snapshot.get("status"),
                "raw_acquisition_cache_ready": raw_cache_ok,
                "research_asset_certification_status": certification_snapshot.get("status"),
                "research_asset_certification_ready": certification_ok,
                "row_counts": {name: details.get("row_count", 0) for name, details in stage_readiness.items()},
            },
            "fixture_summary": {
                "source_name": (fixture or {}).get("source_bundle", {}).get("source_name", DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME),
                "source_type": (fixture or {}).get("source_bundle", {}).get("source_type", DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE),
                "provider": (fixture or {}).get("source_bundle", {}).get("provider", DEFAULT_HISTORICAL_RESEARCH_PROVIDER),
            },
        }

    def dashboard_snapshot(
        self,
        *,
        profile: MarketProfileContract | Mapping[str, Any] | None = None,
        fixture: Mapping[str, Any] | None = None,
        precomputed_results: Mapping[str, Mapping[str, Any]] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = self.build_readiness_snapshot(
            profile=profile,
            fixture=fixture,
            precomputed_results=precomputed_results,
            raw_acquisition_result=raw_acquisition_result,
        )
        snapshot["table_counts"] = {name: details.get("row_count", 0) for name, details in snapshot.get("table_readiness", {}).items()}
        snapshot["dataset_readiness"] = {
            "status": snapshot.get("status"),
            "ready_table_count": len(snapshot.get("ready_tables", [])),
            "total_table_count": len(HISTORICAL_STAGE_CONTRACTS),
            "missing_tables": snapshot.get("missing_tables", []),
            "blocked_tables": snapshot.get("blocked_tables", []),
            "raw_acquisition_cache": snapshot.get("raw_acquisition_cache", {}),
        }
        snapshot["research_asset_certification_readiness"] = dict(snapshot.get("research_asset_certification") or {})
        snapshot["readiness_summary"] = {
            "table_readiness_ready": len(snapshot.get("ready_tables", [])),
            "table_readiness_missing": len(snapshot.get("missing_tables", [])),
            "table_readiness_blocked": len(snapshot.get("blocked_tables", [])),
            "raw_acquisition_cache_status": (snapshot.get("raw_acquisition_cache") or {}).get("status"),
            "research_asset_certification_status": (snapshot.get("research_asset_certification") or {}).get("status"),
        }
        return snapshot


def bootstrap_historical_research_database(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    fixture: Mapping[str, Any] | None = None,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
    game_count: int = 4,
) -> dict[str, Any]:
    database = HistoricalResearchDatabase(storage_path, backend=backend)
    try:
        return database.bootstrap(profile_id=profile_id, fixture=fixture, game_count=game_count)
    finally:
        database.close()


def build_historical_research_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    fixture: Mapping[str, Any] | None = None,
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
    game_count: int = 4,
) -> dict[str, Any]:
    database = HistoricalResearchDatabase(storage_path, backend=backend)
    try:
        if fixture is None:
            fixture = build_historical_research_fixture(game_count=game_count, profile_id=profile_id)
        profile = get_historical_research_market_profile(profile_id)
        return database.dashboard_snapshot(profile=profile, fixture=fixture)
    finally:
        database.close()


def get_historical_research_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
    game_count: int = 4,
) -> dict[str, Any]:
    try:
        return build_historical_research_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile_id,
            game_count=game_count,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "historical_research_snapshot_error",
            "storage": {},
            "table_readiness": {},
            "ready_tables": [],
            "missing_tables": [],
            "blocked_tables": [],
            "dataset_readiness": {},
            "readiness_summary": {},
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_HISTORICAL_RESEARCH_OWNER",
    "DEFAULT_HISTORICAL_RESEARCH_DATASET_NAME",
    "DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID",
    "DEFAULT_HISTORICAL_RESEARCH_PROVIDER",
    "DEFAULT_HISTORICAL_RESEARCH_SOURCE_KEY",
    "DEFAULT_HISTORICAL_RESEARCH_SOURCE_NAME",
    "DEFAULT_HISTORICAL_RESEARCH_SOURCE_TYPE",
    "DEFAULT_HISTORICAL_RESEARCH_STORAGE_PATH",
    "HISTORICAL_RESEARCH_DATASET_NAME",
    "HISTORICAL_RESEARCH_SCHEMA_VERSION",
    "HISTORICAL_SHARED_REQUIRED_FIELDS",
    "HISTORICAL_SHARED_REQUIRED_TIMESTAMPS",
    "HISTORICAL_STAGE_CONTRACTS",
    "HistoricalResearchDatabase",
    "HistoricalStageContract",
    "bootstrap_historical_research_database",
    "build_historical_research_dashboard_snapshot",
    "build_historical_research_fixture",
    "create_historical_research_storage_engine",
    "get_historical_research_market_profile",
    "get_historical_research_snapshot_for_dashboard",
    "normalize_historical_event_rows",
    "normalize_historical_market_rows",
    "normalize_historical_selection_rows",
    "validate_historical_research_profile",
    "validate_historical_stage_rows",
]
