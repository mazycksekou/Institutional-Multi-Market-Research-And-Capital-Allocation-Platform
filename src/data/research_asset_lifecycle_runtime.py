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
from src.data.validation import validate_dataset_rows
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine

RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION = "src.data.research_asset_lifecycle_runtime.v1"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_STORAGE_PATH = get_runtime_data_path("research_asset_lifecycle", "canonical_data.sqlite")
DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME = "research_asset_lifecycles"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_NAME = "research_asset_lifecycle_runtime"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_TYPE = "lifecycle_runtime"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_KEY = "research_asset_lifecycle_runtime"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER = "repository"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_OWNER = "src.data"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID = "sports:nfl"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET = "historical"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET_TYPE = "research_asset_lifecycle"
DEFAULT_RESEARCH_ASSET_LIFECYCLE_ASSET_CLASS = "historical"

RESEARCH_ASSET_LIFECYCLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "asset_id",
    "research_asset_id",
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
    "source_metadata_json",
    "context_json",
    "payload_json",
)

TIME_ENTITY_ALIGNMENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "asset_id",
    "research_asset_id",
    "research_asset_name",
    "asset_family",
    "asset_type",
    "market_profile",
    "market",
    "market_type",
    "league",
    "sport",
    "season",
    "week_or_date",
    "event_id",
    "game_id",
    "market_id",
    "selection",
    "team_id",
    "provider_timestamp",
    "snapshot_time",
    "decision_time",
    "result_timestamp",
    "alignment_status",
    "alignment_reason",
    "alignment_score",
    "row_count",
    "source_row_count",
    "source_name",
    "source_type",
    "source_key",
    "provider",
    "connector",
    "schema_version",
    "lineage_version",
    "certification_timestamp",
)

TIME_ENTITY_ALIGNMENT_ROW_REQUIRED_FIELDS: tuple[str, ...] = (
    "dataset_id",
    "dataset_name",
    "market_profile",
    "profile_id",
    "profile_family",
    "stage_name",
    "batch_id",
    "alignment_certification_id",
    *TIME_ENTITY_ALIGNMENT_REQUIRED_FIELDS,
    "source_file",
    "source_event_id",
    "source_market_id",
    "source_selection_id",
    "certified_at",
    "certification_status",
    "point_in_time_status",
    "leakage_status",
    "status",
    "source_metadata_json",
    "context_json",
    "payload_json",
    "created_at",
    "updated_at",
    "source",
    "market",
    "asset_class",
    "snapshot_id",
    "lineage_id",
    "version_id",
    "quality_score",
    "completeness_score",
)

RESEARCH_ASSET_LIFECYCLE_STATES: tuple[str, ...] = (
    "discovered",
    "source_identified",
    "connector_mapped",
    "raw_acquired",
    "integrity_verified",
    "normalized",
    "research_asset_certified",
    "dataset_certified",
    "feature_ready",
    "math_ready",
    "signal_ready",
    "backtest_ready",
    "production_ready",
)

TIME_ENTITY_ALIGNMENT_FAILURE_REASONS: tuple[str, ...] = (
    "entity_mismatch",
    "team_mismatch",
    "event_mismatch",
    "game_mismatch",
    "league_mismatch",
    "market_mismatch",
    "selection_mismatch",
    "season_mismatch",
    "week_mismatch",
    "decision_time_mismatch",
    "snapshot_after_decision",
    "result_before_decision",
    "source_timestamp_missing",
    "point_in_time_violation",
)

_IDENTITY_FIELDS: tuple[str, ...] = (
    "asset_id",
    "asset_family",
    "market_profile",
    "market",
    "league",
    "sport",
    "season",
    "week_or_date",
    "event_id",
    "market_id",
    "selection",
    "provider",
    "connector",
    "schema_version",
    "lineage_version",
    "asset_name",
    "asset_type",
    "participant_id",
    "team_id",
    "game_id",
    "market_type",
)

_ALIGNMENT_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "market_profile": ("market_profile", "profile_id"),
    "market": ("market", "market_scope"),
    "league": ("league",),
    "sport": ("sport",),
    "season": ("season",),
    "week_or_date": ("week_or_date", "week", "game_date", "event_date"),
    "event_id": ("event_id",),
    "game_id": ("game_id",),
    "market_id": ("market_id",),
    "selection": ("selection", "selection_name"),
    "team_id": ("team_id", "home_team_id", "away_team_id"),
    "participant_id": ("participant_id", "player_id"),
    "market_type": ("market_type",),
    "provider_timestamp": ("provider_timestamp", "source_snapshot_time", "acquisition_timestamp"),
    "snapshot_time": ("snapshot_time",),
    "decision_time": ("decision_time",),
    "result_timestamp": ("result_timestamp", "final_scored_at", "certified_at"),
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


def _resolve_market_profile(profile_id: str) -> MarketProfileContract:
    profile = get_market_profile(profile_id)
    if profile is not None:
        return profile
    if profile_id == DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID:
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


def _first_non_empty(values: Sequence[Any], default: str = "") -> str:
    for value in values:
        text = _normalize_text(value)
        if text:
            return text
    return default


def _unique_non_empty_values(rows: Sequence[Mapping[str, Any]], field_name: str, aliases: Sequence[str] = ()) -> tuple[str, ...]:
    values: list[str] = []
    for row in rows:
        for candidate_name in (field_name, *aliases):
            candidate = _normalize_text(row.get(candidate_name))
            if candidate:
                values.append(candidate)
                break
    return tuple(dict.fromkeys(values))


def _row_values_by_aliases(row: Mapping[str, Any], field_name: str, aliases: Sequence[str] = ()) -> str:
    for candidate_name in (field_name, *aliases):
        value = _normalize_text(row.get(candidate_name))
        if value:
            return value
    return ""


def _is_lowercase_dotted_identifier(value: str) -> bool:
    return bool(value) and value == value.lower() and "." in value and " " not in value


def _state_index(state: str) -> int:
    normalized = _normalize_text(state).lower()
    try:
        return RESEARCH_ASSET_LIFECYCLE_STATES.index(normalized)
    except ValueError:
        return 0


def _normalize_state(state: Any, default: str = "discovered") -> str:
    normalized = _normalize_text(state, default).lower().replace("-", "_").replace(" ", "_")
    return normalized if normalized in RESEARCH_ASSET_LIFECYCLE_STATES else default


def _normalize_failure_reason(reason: Any, default: str = "") -> str:
    normalized = _normalize_text(reason, default).lower().replace("-", "_").replace(" ", "_")
    return normalized if normalized in TIME_ENTITY_ALIGNMENT_FAILURE_REASONS else default


def _identity_core_dict(identity: ResearchAssetIdentityContract) -> dict[str, Any]:
    return {
        "asset_id": identity.asset_id,
        "asset_family": identity.asset_family,
        "market_profile": identity.market_profile,
        "market": identity.market,
        "league": identity.league,
        "sport": identity.sport,
        "season": identity.season,
        "week_or_date": identity.week_or_date,
        "event_id": identity.event_id,
        "market_id": identity.market_id,
        "selection": identity.selection,
        "provider": identity.provider,
        "connector": identity.connector,
        "schema_version": identity.schema_version,
        "lineage_version": identity.lineage_version,
        "asset_name": identity.asset_name,
        "asset_type": identity.asset_type,
        "participant_id": identity.participant_id,
        "team_id": identity.team_id,
        "game_id": identity.game_id,
        "market_type": identity.market_type,
    }


@dataclass(slots=True, frozen=True)
class ResearchAssetIdentityContract:
    asset_id: str
    asset_family: str
    market_profile: str
    market: str = ""
    league: str = ""
    sport: str = ""
    season: str = ""
    week_or_date: str = ""
    event_id: str = ""
    market_id: str = ""
    selection: str = ""
    provider: str = ""
    connector: str = ""
    schema_version: str = ""
    lineage_version: str = ""
    asset_name: str = ""
    asset_type: str = ""
    participant_id: str = ""
    team_id: str = ""
    game_id: str = ""
    market_type: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "asset_id", _normalize_text(self.asset_id))
        object.__setattr__(self, "asset_family", _normalize_text(self.asset_family))
        object.__setattr__(self, "market_profile", _normalize_text(self.market_profile))
        object.__setattr__(self, "market", _normalize_text(self.market))
        object.__setattr__(self, "league", _normalize_text(self.league))
        object.__setattr__(self, "sport", _normalize_text(self.sport))
        object.__setattr__(self, "season", _normalize_text(self.season))
        object.__setattr__(self, "week_or_date", _normalize_text(self.week_or_date))
        object.__setattr__(self, "event_id", _normalize_text(self.event_id))
        object.__setattr__(self, "market_id", _normalize_text(self.market_id))
        object.__setattr__(self, "selection", _normalize_text(self.selection))
        object.__setattr__(self, "provider", _normalize_text(self.provider))
        object.__setattr__(self, "connector", _normalize_text(self.connector))
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version))
        object.__setattr__(self, "lineage_version", _normalize_text(self.lineage_version))
        object.__setattr__(self, "asset_name", _normalize_text(self.asset_name))
        object.__setattr__(self, "asset_type", _normalize_text(self.asset_type))
        object.__setattr__(self, "participant_id", _normalize_text(self.participant_id))
        object.__setattr__(self, "team_id", _normalize_text(self.team_id))
        object.__setattr__(self, "game_id", _normalize_text(self.game_id))
        object.__setattr__(self, "market_type", _normalize_text(self.market_type))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ResearchAssetIdentityContract":
        return cls(
            asset_id=str(data.get("asset_id") or data.get("research_asset_id") or data.get("id") or ""),
            asset_family=str(data.get("asset_family") or data.get("asset_category") or data.get("family") or ""),
            market_profile=str(data.get("market_profile") or data.get("profile_id") or ""),
            market=str(data.get("market") or ""),
            league=str(data.get("league") or ""),
            sport=str(data.get("sport") or ""),
            season=str(data.get("season") or ""),
            week_or_date=str(data.get("week_or_date") or data.get("week") or data.get("game_date") or data.get("event_date") or ""),
            event_id=str(data.get("event_id") or ""),
            market_id=str(data.get("market_id") or ""),
            selection=str(data.get("selection") or ""),
            provider=str(data.get("provider") or ""),
            connector=str(data.get("connector") or ""),
            schema_version=str(data.get("schema_version") or ""),
            lineage_version=str(data.get("lineage_version") or data.get("version_id") or ""),
            asset_name=str(data.get("asset_name") or data.get("research_asset_name") or ""),
            asset_type=str(data.get("asset_type") or ""),
            participant_id=str(data.get("participant_id") or data.get("player_id") or ""),
            team_id=str(data.get("team_id") or ""),
            game_id=str(data.get("game_id") or ""),
            market_type=str(data.get("market_type") or ""),
            metadata=dict(data.get("metadata") or {}),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_family": self.asset_family,
            "market_profile": self.market_profile,
            "market": self.market,
            "league": self.league,
            "sport": self.sport,
            "season": self.season,
            "week_or_date": self.week_or_date,
            "event_id": self.event_id,
            "market_id": self.market_id,
            "selection": self.selection,
            "provider": self.provider,
            "connector": self.connector,
            "schema_version": self.schema_version,
            "lineage_version": self.lineage_version,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "participant_id": self.participant_id,
            "team_id": self.team_id,
            "game_id": self.game_id,
            "market_type": self.market_type,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class TimeEntityAlignmentCertificationContract:
    alignment_certification_id: str
    asset_id: str
    research_asset_id: str
    research_asset_name: str
    asset_family: str
    asset_type: str
    market_profile: str
    market: str
    market_type: str
    league: str
    sport: str
    season: str
    week_or_date: str
    event_id: str
    game_id: str
    market_id: str
    selection: str
    participant_id: str
    team_id: str
    provider_timestamp: str
    snapshot_time: str
    decision_time: str
    result_timestamp: str
    alignment_status: str
    alignment_reason: str
    failure_reason: str
    alignment_score: float
    missing_fields: tuple[str, ...] = ()
    mismatched_fields: tuple[str, ...] = ()
    timing_issues: tuple[str, ...] = ()
    row_count: int = 0
    source_row_count: int = 0
    source_name: str = ""
    source_type: str = ""
    source_key: str = ""
    provider: str = ""
    connector: str = ""
    schema_version: str = ""
    lineage_version: str = ""
    certification_timestamp: str = ""
    certification_notes: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "alignment_certification_id", _normalize_text(self.alignment_certification_id))
        object.__setattr__(self, "asset_id", _normalize_text(self.asset_id))
        object.__setattr__(self, "research_asset_id", _normalize_text(self.research_asset_id))
        object.__setattr__(self, "research_asset_name", _normalize_text(self.research_asset_name))
        object.__setattr__(self, "asset_family", _normalize_text(self.asset_family))
        object.__setattr__(self, "asset_type", _normalize_text(self.asset_type))
        object.__setattr__(self, "market_profile", _normalize_text(self.market_profile))
        object.__setattr__(self, "market", _normalize_text(self.market))
        object.__setattr__(self, "market_type", _normalize_text(self.market_type))
        object.__setattr__(self, "league", _normalize_text(self.league))
        object.__setattr__(self, "sport", _normalize_text(self.sport))
        object.__setattr__(self, "season", _normalize_text(self.season))
        object.__setattr__(self, "week_or_date", _normalize_text(self.week_or_date))
        object.__setattr__(self, "event_id", _normalize_text(self.event_id))
        object.__setattr__(self, "game_id", _normalize_text(self.game_id))
        object.__setattr__(self, "market_id", _normalize_text(self.market_id))
        object.__setattr__(self, "selection", _normalize_text(self.selection))
        object.__setattr__(self, "participant_id", _normalize_text(self.participant_id))
        object.__setattr__(self, "team_id", _normalize_text(self.team_id))
        object.__setattr__(self, "provider_timestamp", _to_iso(self.provider_timestamp))
        object.__setattr__(self, "snapshot_time", _to_iso(self.snapshot_time))
        object.__setattr__(self, "decision_time", _to_iso(self.decision_time))
        object.__setattr__(self, "result_timestamp", _to_iso(self.result_timestamp))
        object.__setattr__(self, "alignment_status", _normalize_text(self.alignment_status))
        object.__setattr__(self, "alignment_reason", _normalize_text(self.alignment_reason))
        object.__setattr__(self, "failure_reason", _normalize_failure_reason(self.failure_reason))
        object.__setattr__(self, "missing_fields", _normalize_items(self.missing_fields))
        object.__setattr__(self, "mismatched_fields", _normalize_items(self.mismatched_fields))
        object.__setattr__(self, "timing_issues", _normalize_items(self.timing_issues))
        object.__setattr__(self, "source_name", _normalize_text(self.source_name))
        object.__setattr__(self, "source_type", _normalize_text(self.source_type))
        object.__setattr__(self, "source_key", _normalize_text(self.source_key))
        object.__setattr__(self, "provider", _normalize_text(self.provider))
        object.__setattr__(self, "connector", _normalize_text(self.connector))
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version))
        object.__setattr__(self, "lineage_version", _normalize_text(self.lineage_version))
        object.__setattr__(self, "certification_timestamp", _to_iso(self.certification_timestamp))
        object.__setattr__(self, "certification_notes", dict(self.certification_notes))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return {
            "alignment_certification_id": self.alignment_certification_id,
            "asset_id": self.asset_id,
            "research_asset_id": self.research_asset_id,
            "research_asset_name": self.research_asset_name,
            "asset_family": self.asset_family,
            "asset_type": self.asset_type,
            "market_profile": self.market_profile,
            "market": self.market,
            "market_type": self.market_type,
            "league": self.league,
            "sport": self.sport,
            "season": self.season,
            "week_or_date": self.week_or_date,
            "event_id": self.event_id,
            "game_id": self.game_id,
            "market_id": self.market_id,
            "selection": self.selection,
            "participant_id": self.participant_id,
            "team_id": self.team_id,
            "provider_timestamp": self.provider_timestamp,
            "snapshot_time": self.snapshot_time,
            "decision_time": self.decision_time,
            "result_timestamp": self.result_timestamp,
            "alignment_status": self.alignment_status,
            "alignment_reason": self.alignment_reason,
            "failure_reason": self.failure_reason,
            "alignment_score": self.alignment_score,
            "missing_fields": list(self.missing_fields),
            "mismatched_fields": list(self.mismatched_fields),
            "timing_issues": list(self.timing_issues),
            "row_count": self.row_count,
            "source_row_count": self.source_row_count,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_key": self.source_key,
            "provider": self.provider,
            "connector": self.connector,
            "schema_version": self.schema_version,
            "lineage_version": self.lineage_version,
            "certification_timestamp": self.certification_timestamp,
            "certification_notes": dict(self.certification_notes),
            "metadata": dict(self.metadata),
        }


def build_research_asset_identity_contract(data: Mapping[str, Any] | None = None, /, **overrides: Any) -> ResearchAssetIdentityContract:
    payload = dict(data or {})
    payload.update(overrides)
    return ResearchAssetIdentityContract.from_mapping(payload)


def validate_research_asset_identity_contract(contract: ResearchAssetIdentityContract | Mapping[str, Any]) -> dict[str, Any]:
    identity = contract if isinstance(contract, ResearchAssetIdentityContract) else ResearchAssetIdentityContract.from_mapping(contract)
    errors: list[str] = []
    warnings: list[str] = []

    if not identity.asset_id:
        errors.append("asset_id is required")
    elif not _is_lowercase_dotted_identifier(identity.asset_id):
        errors.append("asset_id must be a stable lowercase dotted identifier")
    if not identity.asset_family:
        errors.append("asset_family is required")
    if not identity.market_profile:
        errors.append("market_profile is required")
    if not identity.schema_version:
        errors.append("schema_version is required")
    if not identity.lineage_version:
        errors.append("lineage_version is required")
    if not identity.provider:
        warnings.append("provider should be supplied when known")
    if not identity.connector:
        warnings.append("connector should be supplied when known")

    return {
        "ok": not errors,
        "identity": identity,
        "errors": errors,
        "warnings": warnings,
    }


def _field_value(row: Mapping[str, Any], field_name: str) -> str:
    aliases = _ALIGNMENT_FIELD_ALIASES.get(field_name, ())
    return _row_values_by_aliases(row, field_name, aliases)


def _collect_time_issues(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        provider_timestamp = _parse_iso(_field_value(row, "provider_timestamp"))
        snapshot_time = _parse_iso(_field_value(row, "snapshot_time"))
        decision_time = _parse_iso(_field_value(row, "decision_time"))
        result_timestamp = _parse_iso(_field_value(row, "result_timestamp"))
        if provider_timestamp is None and snapshot_time is not None:
            issues.append("source_timestamp_missing")
        if snapshot_time is not None and decision_time is not None and snapshot_time > decision_time:
            issues.append("snapshot_after_decision")
        if decision_time is not None and result_timestamp is not None and result_timestamp < decision_time:
            issues.append("result_before_decision")
        if provider_timestamp is not None and snapshot_time is not None and provider_timestamp > snapshot_time:
            issues.append("point_in_time_violation")
    return list(dict.fromkeys(issues))


def _classify_alignment_failure(
    *,
    missing_fields: Sequence[str],
    mismatched_fields: Sequence[str],
    timing_issues: Sequence[str],
) -> str:
    if "source_timestamp_missing" in timing_issues:
        return "source_timestamp_missing"
    if "snapshot_after_decision" in timing_issues:
        return "snapshot_after_decision"
    if "result_before_decision" in timing_issues:
        return "result_before_decision"
    if "point_in_time_violation" in timing_issues:
        return "point_in_time_violation"
    normalized_mismatches = {field.lower() for field in mismatched_fields}
    if "league" in normalized_mismatches:
        return "league_mismatch"
    if "season" in normalized_mismatches:
        return "season_mismatch"
    if "week_or_date" in normalized_mismatches:
        return "week_mismatch"
    if "event_id" in normalized_mismatches:
        return "event_mismatch"
    if "game_id" in normalized_mismatches:
        return "game_mismatch"
    if "team_id" in normalized_mismatches or "participant_id" in normalized_mismatches:
        return "team_mismatch"
    if "market_id" in normalized_mismatches or "market_type" in normalized_mismatches:
        return "market_mismatch"
    if "selection" in normalized_mismatches:
        return "selection_mismatch"
    if "decision_time" in normalized_mismatches:
        return "decision_time_mismatch"
    if missing_fields:
        return "source_timestamp_missing"
    if mismatched_fields:
        return "entity_mismatch"
    if timing_issues:
        return timing_issues[0]
    return ""


def build_time_entity_alignment_certification(
    *,
    identity: ResearchAssetIdentityContract,
    rows: Sequence[Mapping[str, Any]],
    required_fields: Sequence[str] = TIME_ENTITY_ALIGNMENT_REQUIRED_FIELDS,
    required_timestamps: Sequence[str] = (),
    profile: MarketProfileContract | None = None,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
    created_at: str | None = None,
    asset_name: str = "",
    asset_type: str = "",
    lifecycle_state: str = "integrity_verified",
    batch_id: str = "",
) -> TimeEntityAlignmentCertificationContract:
    source_bundle = dict(source_bundle or {})
    raw_acquisition_result = dict(raw_acquisition_result or {})
    created_at = _normalize_text(created_at, _utc_now_iso())
    profile = profile or _resolve_market_profile(identity.market_profile or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID)
    required_fields = tuple(_normalize_text(field) for field in required_fields if _normalize_text(field))
    required_timestamps = tuple(_normalize_text(field) for field in required_timestamps if _normalize_text(field))
    row_count = len(rows)
    field_order = tuple(dict.fromkeys((*_IDENTITY_FIELDS, *required_fields, *required_timestamps, *tuple(_ALIGNMENT_FIELD_ALIASES.keys()))))

    missing_fields: list[str] = []
    mismatched_fields: list[str] = []
    field_values: dict[str, tuple[str, ...]] = {}

    for field_name in field_order:
        aliases = _ALIGNMENT_FIELD_ALIASES.get(field_name, ())
        values = _unique_non_empty_values(rows, field_name, aliases)
        field_values[field_name] = values
        expected = _normalize_text(getattr(identity, field_name, ""))
        if expected and values and any(value != expected for value in values):
            mismatched_fields.append(field_name)
        elif expected and not values:
            missing_fields.append(field_name)
        elif not expected and len(values) > 1:
            mismatched_fields.append(field_name)

    timing_issues = _collect_time_issues(rows)
    if not timing_issues and any(field in required_timestamps for field in ("provider_timestamp", "snapshot_time", "decision_time")):
        provider_value = _first_non_empty(field_values.get("provider_timestamp", ()), _field_value(rows[0], "provider_timestamp") if rows else "")
        snapshot_value = _first_non_empty(field_values.get("snapshot_time", ()), _field_value(rows[0], "snapshot_time") if rows else "")
        decision_value = _first_non_empty(field_values.get("decision_time", ()), _field_value(rows[0], "decision_time") if rows else "")
        if provider_value and snapshot_value and _parse_iso(provider_value) and _parse_iso(snapshot_value) and _parse_iso(provider_value) > _parse_iso(snapshot_value):
            timing_issues.append("point_in_time_violation")
        if snapshot_value and decision_value and _parse_iso(snapshot_value) and _parse_iso(decision_value) and _parse_iso(snapshot_value) > _parse_iso(decision_value):
            timing_issues.append("snapshot_after_decision")

    validation = validate_dataset_rows(rows, required_fields=required_fields or TIME_ENTITY_ALIGNMENT_REQUIRED_FIELDS)
    validation_errors = list(validation.get("missing_rows", []))
    if not validation.get("ok"):
        for entry in validation_errors:
            for missing_field in entry.get("missing_fields", []):
                if missing_field not in missing_fields:
                    missing_fields.append(missing_field)

    failure_reason = _classify_alignment_failure(
        missing_fields=missing_fields,
        mismatched_fields=mismatched_fields,
        timing_issues=timing_issues,
    )
    ok = not (missing_fields or mismatched_fields or timing_issues or not validation.get("ok"))
    alignment_status = "aligned" if ok else "blocked"
    certification_timestamp = created_at
    source_name = _normalize_text(source_bundle.get("source_name") or raw_acquisition_result.get("source_name"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_NAME)
    source_type = _normalize_text(source_bundle.get("source_type") or raw_acquisition_result.get("source_type"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_TYPE)
    source_key = _normalize_text(source_bundle.get("source_key") or raw_acquisition_result.get("source_key"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_KEY)
    provider = _normalize_text(source_bundle.get("provider") or raw_acquisition_result.get("provider"), identity.provider or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER)
    alignment_certification_id = _stable_id(
        "research_asset_alignment_certification",
        identity.asset_id,
        identity.market_profile,
        batch_id or source_key or source_name,
        _first_non_empty((field_values.get("snapshot_time", ()) or ()), created_at),
        _first_non_empty((field_values.get("decision_time", ()) or ()), created_at),
    )
    source_snapshot_time = _first_non_empty(field_values.get("provider_timestamp", ()), _first_non_empty(field_values.get("snapshot_time", ()), created_at))
    snapshot_time = _first_non_empty(field_values.get("snapshot_time", ()), source_snapshot_time or created_at)
    decision_time = _first_non_empty(field_values.get("decision_time", ()), snapshot_time or created_at)
    result_timestamp = _first_non_empty(field_values.get("result_timestamp", ()), source_bundle.get("result_timestamp") or raw_acquisition_result.get("result_timestamp") or "")
    source_row_ids = [
        _stable_id("alignment_row", identity.asset_id, index, _as_json(dict(row)))
        for index, row in enumerate(rows)
    ]
    lineage_record = create_lineage_record(
        provider_id=provider,
        provider_type=profile.profile_family,
        payload_schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        snapshot_id=_stable_id("alignment_snapshot", identity.asset_id, alignment_certification_id),
        source_type=source_type,
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_id=_stable_id("alignment_lineage", identity.asset_id, alignment_certification_id),
        dataset_id=DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        dataset_name=DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        source_record_id=";".join(source_row_ids) or identity.asset_id,
        target_record_id=alignment_certification_id,
        source_stage="normalized",
        target_stage="time_entity_alignment_certification",
        transformation="certify_time_entity_alignment",
    )
    alignment_score = 1.0 if ok else round(max(0.0, 1.0 - ((len(missing_fields) + len(mismatched_fields) + len(timing_issues)) / max(len(field_order), 1))), 4)
    return TimeEntityAlignmentCertificationContract(
        alignment_certification_id=alignment_certification_id,
        asset_id=identity.asset_id,
        research_asset_id=identity.asset_id,
        research_asset_name=asset_name or identity.asset_name or identity.asset_id,
        asset_family=identity.asset_family,
        asset_type=asset_type or identity.asset_type,
        market_profile=identity.market_profile or profile.profile_id,
        market=identity.market or profile.market_scope or profile.profile_id,
        market_type=identity.market_type or DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET_TYPE,
        league=identity.league,
        sport=identity.sport,
        season=identity.season,
        week_or_date=identity.week_or_date,
        event_id=identity.event_id,
        game_id=identity.game_id,
        market_id=identity.market_id,
        selection=identity.selection,
        participant_id=identity.participant_id,
        team_id=identity.team_id,
        provider_timestamp=source_snapshot_time,
        snapshot_time=snapshot_time,
        decision_time=decision_time,
        result_timestamp=result_timestamp,
        alignment_status=alignment_status,
        alignment_reason="time_and_entity_alignment_checked" if ok else "time_and_entity_alignment_blocked",
        failure_reason=failure_reason,
        alignment_score=alignment_score,
        missing_fields=tuple(dict.fromkeys(missing_fields)),
        mismatched_fields=tuple(dict.fromkeys(mismatched_fields)),
        timing_issues=tuple(dict.fromkeys(timing_issues)),
        row_count=row_count,
        source_row_count=row_count,
        source_name=source_name,
        source_type=source_type,
        source_key=source_key,
        provider=provider,
        connector=identity.connector,
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_version=identity.lineage_version or "v1",
        certification_timestamp=certification_timestamp,
        certification_notes={
            "required_fields": list(required_fields),
            "required_timestamps": list(required_timestamps),
            "field_values": {field_name: list(values) for field_name, values in field_values.items() if values},
            "validation_errors": list(validation.get("errors", [])),
            "validation_missing_rows": list(validation.get("missing_rows", [])),
            "profile": profile.as_dict(),
            "lifecycle_state": lifecycle_state,
        },
        metadata={
            "validation": dict(validation),
            "lineage_record": lineage_record,
            "source_bundle": source_bundle,
            "raw_acquisition_result": raw_acquisition_result,
            "required_fields": list(required_fields),
            "required_timestamps": list(required_timestamps),
            "lifecycle_state": lifecycle_state,
        },
    )


def validate_time_entity_alignment_certification_row(row: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_dataset_rows([row], required_fields=TIME_ENTITY_ALIGNMENT_ROW_REQUIRED_FIELDS)
    issues: list[str] = []
    for field_name in ("provider_timestamp", "snapshot_time", "decision_time", "result_timestamp", "certification_timestamp", "created_at", "updated_at"):
        if _normalize_text(row.get(field_name)) and _parse_iso(row.get(field_name)) is None:
            issues.append(f"{field_name}:invalid_iso")
    return {
        "ok": bool(validation["ok"]) and not issues,
        "status": "validated" if bool(validation["ok"]) and not issues else "rejected",
        "validation": validation,
        "issues": issues,
    }


def build_time_entity_alignment_certification_row(
    *,
    identity: ResearchAssetIdentityContract,
    alignment: TimeEntityAlignmentCertificationContract,
    profile: MarketProfileContract,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
    batch_id: str = "",
) -> dict[str, Any]:
    source_bundle = dict(source_bundle or {})
    raw_acquisition_result = dict(raw_acquisition_result or {})
    source_name = _normalize_text(source_bundle.get("source_name") or raw_acquisition_result.get("source_name"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_NAME)
    source_type = _normalize_text(source_bundle.get("source_type") or raw_acquisition_result.get("source_type"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_TYPE)
    source_key = _normalize_text(source_bundle.get("source_key") or raw_acquisition_result.get("source_key"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_KEY)
    provider = _normalize_text(source_bundle.get("provider") or raw_acquisition_result.get("provider"), identity.provider or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER)
    source_snapshot_time = _first_non_empty(
        (
            alignment.provider_timestamp,
            alignment.snapshot_time,
            raw_acquisition_result.get("source_snapshot_time"),
            raw_acquisition_result.get("snapshot_time"),
        ),
        alignment.certification_timestamp,
    )
    snapshot_time = _first_non_empty((alignment.snapshot_time, raw_acquisition_result.get("snapshot_time"), source_snapshot_time), alignment.certification_timestamp)
    decision_time = _first_non_empty((alignment.decision_time, raw_acquisition_result.get("decision_time"), snapshot_time), alignment.certification_timestamp)
    result_timestamp = _first_non_empty((alignment.result_timestamp, raw_acquisition_result.get("result_timestamp"), source_bundle.get("result_timestamp")), "")
    source_row_ids = [
        _stable_id("alignment_source_row", identity.asset_id, index, _as_json(dict(row)))
        for index, row in enumerate((raw_acquisition_result.get("rows") or []))
        if isinstance(row, Mapping)
    ]
    checksum = _stable_id("alignment_checksum", identity.asset_id, alignment.alignment_certification_id, _as_json(alignment.as_dict()))
    lineage_record = create_lineage_record(
        provider_id=provider,
        provider_type=profile.profile_family,
        payload_schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        snapshot_id=_stable_id("alignment_snapshot", identity.asset_id, alignment.alignment_certification_id),
        source_type=source_type,
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_id=_stable_id("alignment_lineage", identity.asset_id, alignment.alignment_certification_id),
        dataset_id=DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        dataset_name=DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        source_record_id=";".join(source_row_ids) or identity.asset_id,
        target_record_id=alignment.alignment_certification_id,
        source_stage="normalized",
        target_stage="time_entity_alignment_certifications",
        transformation="certify_time_entity_alignment",
    )
    row = {
        "dataset_id": DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        "dataset_name": DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        "market_profile": profile.profile_id,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "stage_name": "time_entity_alignment_certifications",
        "batch_id": _normalize_text(batch_id, alignment.alignment_certification_id),
        "alignment_certification_id": alignment.alignment_certification_id,
        "asset_id": identity.asset_id,
        "research_asset_id": identity.asset_id,
        "research_asset_name": alignment.research_asset_name or identity.asset_name or identity.asset_id,
        "asset_family": alignment.asset_family or identity.asset_family,
        "asset_type": alignment.asset_type or identity.asset_type,
        "connector": alignment.connector or identity.connector,
        "market": alignment.market or identity.market or profile.market_scope or profile.profile_id,
        "market_type": alignment.market_type or identity.market_type or DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET_TYPE,
        "league": alignment.league or identity.league,
        "sport": alignment.sport or identity.sport,
        "season": alignment.season or identity.season,
        "week_or_date": alignment.week_or_date or identity.week_or_date,
        "event_id": alignment.event_id or identity.event_id,
        "game_id": alignment.game_id or identity.game_id,
        "market_id": alignment.market_id or identity.market_id,
        "selection": alignment.selection or identity.selection,
        "participant_id": alignment.participant_id or identity.participant_id,
        "team_id": alignment.team_id or identity.team_id,
        "provider_timestamp": alignment.provider_timestamp,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "result_timestamp": result_timestamp,
        "alignment_status": alignment.alignment_status,
        "alignment_reason": alignment.alignment_reason,
        "failure_reason": alignment.failure_reason,
        "alignment_score": alignment.alignment_score,
        "missing_fields_json": _as_json(list(alignment.missing_fields)),
        "mismatched_fields_json": _as_json(list(alignment.mismatched_fields)),
        "timing_issues_json": _as_json(list(alignment.timing_issues)),
        "validation_json": _as_json(dict(alignment.metadata.get("validation") or {})),
        "lineage_json": _as_json(lineage_record),
        "provenance_json": _as_json(
            {
                "identity": identity.as_dict(),
                "alignment": alignment.as_dict(),
                "source_bundle": source_bundle,
                "raw_acquisition_result": raw_acquisition_result,
                "profile": profile.as_dict(),
            }
        ),
        "certification_notes_json": _as_json(dict(alignment.certification_notes)),
        "row_count": alignment.row_count,
        "source_row_count": alignment.source_row_count,
        "checksum": checksum,
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_file": _normalize_text(source_bundle.get("source_file") or raw_acquisition_result.get("source_file")),
        "source_event_id": _normalize_text(source_bundle.get("source_event_id") or raw_acquisition_result.get("source_event_id") or alignment.event_id),
        "source_market_id": _normalize_text(source_bundle.get("source_market_id") or raw_acquisition_result.get("source_market_id") or alignment.market_id),
        "source_selection_id": _normalize_text(source_bundle.get("source_selection_id") or raw_acquisition_result.get("source_selection_id") or alignment.selection),
        "source_snapshot_time": source_snapshot_time,
        "certified_at": alignment.certification_timestamp,
        "certification_timestamp": alignment.certification_timestamp,
        "certification_status": alignment.alignment_status,
        "point_in_time_status": "safe" if alignment.alignment_status == "aligned" else "blocked",
        "leakage_status": "none" if alignment.alignment_status == "aligned" else "suspect",
        "status": alignment.alignment_status,
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "provider": provider,
                "connector": identity.connector,
                "profile_family": profile.profile_family,
            }
        ),
        "context_json": _as_json(
            {
                "identity": identity.as_dict(),
                "alignment": alignment.as_dict(),
                "profile": profile.as_dict(),
            }
        ),
        "payload_json": _as_json(alignment.as_dict()),
        "schema_version": RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        "lineage_version": alignment.lineage_version or identity.lineage_version or "v1",
        "created_at": alignment.certification_timestamp,
        "updated_at": alignment.certification_timestamp,
        "source": source_name,
        "provider": provider,
        "market": alignment.market or identity.market or profile.market_scope or profile.profile_id,
        "asset_class": identity.asset_family or DEFAULT_RESEARCH_ASSET_LIFECYCLE_ASSET_CLASS,
        "snapshot_id": _stable_id("alignment_snapshot", identity.asset_id, alignment.alignment_certification_id),
        "lineage_id": _stable_id("alignment_lineage", identity.asset_id, alignment.alignment_certification_id),
        "version_id": identity.lineage_version or alignment.lineage_version or "v1",
        "quality_score": alignment.alignment_score,
        "completeness_score": 1.0 if alignment.alignment_status == "aligned" else alignment.alignment_score,
    }
    return row


def _resolve_row_identity(
    *,
    identity: ResearchAssetIdentityContract,
    alignment: TimeEntityAlignmentCertificationContract | None = None,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
) -> ResearchAssetIdentityContract:
    source_bundle = dict(source_bundle or {})
    raw_acquisition_result = dict(raw_acquisition_result or {})
    payload = identity.as_dict()
    if alignment is not None:
        payload.update(
            {
                "market_profile": alignment.market_profile or payload.get("market_profile"),
                "market": alignment.market or payload.get("market"),
                "league": alignment.league or payload.get("league"),
                "sport": alignment.sport or payload.get("sport"),
                "season": alignment.season or payload.get("season"),
                "week_or_date": alignment.week_or_date or payload.get("week_or_date"),
                "event_id": alignment.event_id or payload.get("event_id"),
                "market_id": alignment.market_id or payload.get("market_id"),
                "selection": alignment.selection or payload.get("selection"),
                "participant_id": alignment.participant_id or payload.get("participant_id"),
                "team_id": alignment.team_id or payload.get("team_id"),
                "game_id": alignment.game_id or payload.get("game_id"),
                "market_type": alignment.market_type or payload.get("market_type"),
                "provider": alignment.provider or payload.get("provider"),
                "connector": alignment.connector or payload.get("connector"),
                "asset_name": alignment.research_asset_name or payload.get("asset_name"),
                "asset_type": alignment.asset_type or payload.get("asset_type"),
            }
        )
    if source_bundle:
        payload.setdefault("provider", _normalize_text(source_bundle.get("provider"), payload.get("provider", "")))
        payload.setdefault("connector", _normalize_text(source_bundle.get("connector"), payload.get("connector", "")))
    if raw_acquisition_result:
        payload.setdefault("provider", _normalize_text(raw_acquisition_result.get("provider"), payload.get("provider", "")))
        payload.setdefault("connector", _normalize_text(raw_acquisition_result.get("connector"), payload.get("connector", "")))
    return ResearchAssetIdentityContract.from_mapping(payload)


def build_research_asset_lifecycle_row(
    *,
    identity: ResearchAssetIdentityContract,
    lifecycle_state: str,
    created_at: str,
    source_bundle: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
    profile: MarketProfileContract | None = None,
    alignment_certification: TimeEntityAlignmentCertificationContract | None = None,
    certification_result: Mapping[str, Any] | None = None,
    dataset_result: Mapping[str, Any] | None = None,
    lifecycle_reason: str = "",
    notes: Mapping[str, Any] | None = None,
    state_history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source_bundle = dict(source_bundle or {})
    raw_acquisition_result = dict(raw_acquisition_result or {})
    certification_result = dict(certification_result or {})
    dataset_result = dict(dataset_result or {})
    created_at = _normalize_text(created_at, _utc_now_iso())
    lifecycle_state = _normalize_state(lifecycle_state)
    profile = profile or _resolve_market_profile(identity.market_profile or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID)
    identity = _resolve_row_identity(
        identity=identity,
        alignment=alignment_certification,
        source_bundle=source_bundle,
        raw_acquisition_result=raw_acquisition_result,
    )
    alignment_certification_id = alignment_certification.alignment_certification_id if alignment_certification else _normalize_text(certification_result.get("alignment_certification_id"))
    alignment_status = alignment_certification.alignment_status if alignment_certification else _normalize_text(certification_result.get("alignment_status"))
    alignment_reason = alignment_certification.alignment_reason if alignment_certification else _normalize_text(certification_result.get("alignment_reason"))
    alignment_score = alignment_certification.alignment_score if alignment_certification else _normalize_float(certification_result.get("alignment_score"), 0.0)
    certification_id = _normalize_text(certification_result.get("certification_id") or dataset_result.get("certification_id"))
    certification_status = _normalize_text(certification_result.get("certification_state") or certification_result.get("certification_status") or dataset_result.get("certification_status") or lifecycle_state)
    lifecycle_state_index = _state_index(lifecycle_state)
    state_history_list = list(state_history or [])
    if not state_history_list:
        state_history_list.append(
            {
                "state": lifecycle_state,
                "state_index": lifecycle_state_index,
                "changed_at": created_at,
                "reason": lifecycle_reason,
                "alignment_status": alignment_status,
                "certification_status": certification_status,
            }
        )
    source_name = _normalize_text(source_bundle.get("source_name") or raw_acquisition_result.get("source_name"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_NAME)
    source_type = _normalize_text(source_bundle.get("source_type") or raw_acquisition_result.get("source_type"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_TYPE)
    source_key = _normalize_text(source_bundle.get("source_key") or raw_acquisition_result.get("source_key"), DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_KEY)
    provider = _normalize_text(source_bundle.get("provider") or raw_acquisition_result.get("provider"), identity.provider or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER)
    source_snapshot_time = _first_non_empty(
        (
            alignment_certification.provider_timestamp if alignment_certification else "",
            alignment_certification.snapshot_time if alignment_certification else "",
            raw_acquisition_result.get("source_snapshot_time"),
            raw_acquisition_result.get("snapshot_time"),
        ),
        created_at,
    )
    snapshot_time = _first_non_empty(
        (
            alignment_certification.snapshot_time if alignment_certification else "",
            raw_acquisition_result.get("snapshot_time"),
            source_snapshot_time,
        ),
        created_at,
    )
    decision_time = _first_non_empty(
        (
            alignment_certification.decision_time if alignment_certification else "",
            raw_acquisition_result.get("decision_time"),
            snapshot_time,
        ),
        created_at,
    )
    lineage_record = create_lineage_record(
        provider_id=provider,
        provider_type=profile.profile_family,
        payload_schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        snapshot_id=_stable_id("research_asset_lifecycle_snapshot", identity.asset_id, lifecycle_state, certification_id or alignment_certification_id or created_at),
        source_type=source_type,
        schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        lineage_id=_stable_id("research_asset_lifecycle_lineage", identity.asset_id, lifecycle_state, certification_id or alignment_certification_id or created_at),
        dataset_id=DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        dataset_name=DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        source_record_id=identity.asset_id,
        target_record_id=certification_id or alignment_certification_id or identity.asset_id,
        source_stage="time_entity_alignment_certification" if alignment_certification else "research_asset_lifecycle",
        target_stage="research_asset_lifecycle",
        transformation="record_research_asset_lifecycle",
    )
    row = {
        "dataset_id": DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        "dataset_name": DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME,
        "market_profile": identity.market_profile,
        "profile_id": identity.market_profile,
        "profile_family": profile.profile_family,
        "stage_name": "research_asset_lifecycle",
        "batch_id": _normalize_text((raw_acquisition_result or {}).get("batch_id") or certification_result.get("batch_id") or dataset_result.get("batch_id") or lifecycle_state),
        "asset_id": identity.asset_id,
        "research_asset_id": identity.asset_id,
        "research_asset_name": identity.asset_name or identity.asset_id,
        "asset_family": identity.asset_family,
        "asset_type": identity.asset_type,
        "asset_name": identity.asset_name or identity.asset_id,
        "league": identity.league,
        "sport": identity.sport,
        "season": identity.season,
        "week_or_date": identity.week_or_date,
        "event_id": identity.event_id,
        "game_id": identity.game_id,
        "market_id": identity.market_id,
        "selection": identity.selection,
        "participant_id": identity.participant_id,
        "team_id": identity.team_id,
        "connector": identity.connector,
        "lifecycle_state": lifecycle_state,
        "lifecycle_state_index": lifecycle_state_index,
        "lifecycle_reason": _normalize_text(lifecycle_reason),
        "alignment_status": alignment_status,
        "alignment_reason": alignment_reason,
        "alignment_score": alignment_score,
        "alignment_certification_id": alignment_certification_id,
        "certification_id": certification_id,
        "state_history_json": _as_json(state_history_list),
        "transition_history_json": _as_json(state_history_list),
        "identity_json": _as_json(identity.as_dict()),
        "alignment_json": _as_json(alignment_certification.as_dict() if alignment_certification else dict(certification_result)),
        "notes_json": _as_json(dict(notes or {})),
        "source_name": source_name,
        "source_type": source_type,
        "source_key": source_key,
        "source_file": _normalize_text((source_bundle or {}).get("source_file") or (raw_acquisition_result or {}).get("source_file")),
        "source_event_id": _normalize_text((source_bundle or {}).get("source_event_id") or (raw_acquisition_result or {}).get("source_event_id")),
        "source_market_id": _normalize_text((source_bundle or {}).get("source_market_id") or (raw_acquisition_result or {}).get("source_market_id")),
        "source_selection_id": _normalize_text((source_bundle or {}).get("source_selection_id") or (raw_acquisition_result or {}).get("source_selection_id")),
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": created_at,
        "certification_status": certification_status,
        "point_in_time_status": "safe" if alignment_status == "aligned" else "blocked",
        "leakage_status": "none" if alignment_status == "aligned" else "suspect",
        "status": lifecycle_state,
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_key": source_key,
                "provider": provider,
                "connector": identity.connector,
            }
        ),
        "context_json": _as_json(
            {
                "identity": identity.as_dict(),
                "alignment": alignment_certification.as_dict() if alignment_certification else dict(certification_result),
                "certification_result": dict(certification_result),
                "dataset_result": dict(dataset_result),
            }
        ),
        "payload_json": _as_json(
            {
                "identity": identity.as_dict(),
                "alignment_certification_id": alignment_certification_id,
                "lifecycle_state": lifecycle_state,
                "alignment_status": alignment_status,
                "certification_status": certification_status,
                "lineage_record": lineage_record,
            }
        ),
        "schema_version": RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": source_name,
        "provider": provider,
        "market": identity.market or identity.market_profile,
        "market_type": identity.market_type or DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET_TYPE,
        "asset_class": identity.asset_family or DEFAULT_RESEARCH_ASSET_LIFECYCLE_ASSET_CLASS,
        "snapshot_id": _stable_id("research_asset_lifecycle_snapshot", identity.asset_id, lifecycle_state, created_at),
        "lineage_id": _stable_id("research_asset_lifecycle_lineage", identity.asset_id, lifecycle_state, created_at),
        "version_id": _normalize_text(identity.lineage_version or certification_result.get("version_id") or dataset_result.get("version_id"), "v1"),
        "quality_score": alignment_score,
        "completeness_score": 1.0 if alignment_status == "aligned" else alignment_score,
    }
    return row


def validate_research_asset_lifecycle_row(row: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_dataset_rows([row], required_fields=RESEARCH_ASSET_LIFECYCLE_REQUIRED_FIELDS)
    issues = []
    for field_name in ("created_at", "updated_at", "snapshot_time", "decision_time", "source_snapshot_time", "certified_at"):
        if _normalize_text(row.get(field_name)):
            if _parse_iso(row.get(field_name)) is None:
                issues.append(f"{field_name}:invalid_iso")
    return {
        "ok": bool(validation["ok"]) and not issues,
        "status": "validated" if bool(validation["ok"]) and not issues else "rejected",
        "validation": validation,
        "issues": issues,
    }


class ResearchAssetLifecycleRuntime:
    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        backend: str = "sqlite",
        dataset_owner: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_OWNER,
        store: LocalStorageEngine | None = None,
    ) -> None:
        self.storage_path = Path(storage_path or DEFAULT_RESEARCH_ASSET_LIFECYCLE_STORAGE_PATH).expanduser().resolve()
        self.backend = str(backend or "sqlite").strip().lower()
        self.dataset_owner = _normalize_text(dataset_owner, DEFAULT_RESEARCH_ASSET_LIFECYCLE_OWNER)
        self.store = store or create_local_storage_engine(self.storage_path, backend=self.backend)
        self._owns_store = store is None
        self.store.ensure_schema()

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> "ResearchAssetLifecycleRuntime":
        _ = self.store.connection
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def build_required_identity_catalog(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID) -> list[ResearchAssetIdentityContract]:
        profile = _resolve_market_profile(profile_id)
        profile_validation = _validate_market_profile(profile)
        if not profile_validation["ok"]:
            raise ValueError("; ".join(profile_validation["errors"]) or "research asset lifecycle profile validation failed")
        if profile.profile_id != DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID:
            return []
        from src.data.historical_research_asset_certification_runtime import HistoricalResearchAssetCertificationRuntime

        certification_runtime = HistoricalResearchAssetCertificationRuntime(
            self.storage_path,
            backend=self.backend,
            dataset_owner=self.dataset_owner,
            store=self.store,
        )
        contracts = certification_runtime.build_required_asset_catalog(profile_id=profile.profile_id)
        identities: list[ResearchAssetIdentityContract] = []
        for contract in contracts:
            identities.append(
                build_research_asset_identity_contract(
                    asset_id=contract.research_asset_id,
                    asset_family=contract.asset_category,
                    market_profile=profile.profile_id,
                    market=profile.market_scope or profile.profile_id,
                    league=_normalize_text(profile.metadata.get("league"), "NFL" if profile.profile_family == "sports" else profile.profile_id),
                    sport=_normalize_text(profile.metadata.get("sport"), "football" if profile.profile_family == "sports" else profile.profile_family),
                    asset_name=contract.research_asset_name,
                    asset_type=contract.asset_type,
                    provider=DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER,
                    connector=_normalize_text(contract.metadata.get("connector")),
                    schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
                    lineage_version="v1",
                    metadata={
                        "research_asset_contract": contract.as_dict(),
                        "required": contract.required,
                        "future_asset": contract.future_asset,
                        "priority": contract.priority,
                    },
                )
            )
        return identities

    def build_discovered_identity_catalog(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID) -> list[ResearchAssetIdentityContract]:
        profile = _resolve_market_profile(profile_id)
        if profile.profile_id != DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID:
            return []
        from src.data.historical_research_asset_certification_runtime import HistoricalResearchAssetCertificationRuntime

        certification_runtime = HistoricalResearchAssetCertificationRuntime(
            self.storage_path,
            backend=self.backend,
            dataset_owner=self.dataset_owner,
            store=self.store,
        )
        contracts = certification_runtime.build_discovered_future_asset_catalog(profile_id=profile.profile_id)
        identities: list[ResearchAssetIdentityContract] = []
        for contract in contracts:
            identities.append(
                build_research_asset_identity_contract(
                    asset_id=contract.research_asset_id,
                    asset_family=contract.asset_category,
                    market_profile=profile.profile_id,
                    market=profile.market_scope or profile.profile_id,
                    league=_normalize_text(profile.metadata.get("league"), "NFL" if profile.profile_family == "sports" else profile.profile_id),
                    sport=_normalize_text(profile.metadata.get("sport"), "football" if profile.profile_family == "sports" else profile.profile_family),
                    asset_name=contract.research_asset_name,
                    asset_type=contract.asset_type,
                    provider=DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER,
                    connector=_normalize_text(contract.metadata.get("connector")),
                    schema_version=RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION,
                    lineage_version="v1",
                    metadata={
                        "research_asset_contract": contract.as_dict(),
                        "required": contract.required,
                        "future_asset": contract.future_asset,
                        "priority": contract.priority,
                    },
                )
            )
        return identities

    def build_identity_catalog(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID) -> list[ResearchAssetIdentityContract]:
        return [
            *self.build_required_identity_catalog(profile_id=profile_id),
            *self.build_discovered_identity_catalog(profile_id=profile_id),
        ]

    def _existing_lifecycle_row(self, asset_id: str) -> dict[str, Any] | None:
        rows = self.store.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[asset_id],
            limit=1,
        ) if self.store.table_exists("research_asset_lifecycles") else []
        return rows[0] if rows else None

    def _state_history(self, existing_row: Mapping[str, Any] | None, *, lifecycle_state: str, lifecycle_reason: str, alignment_status: str, certification_status: str, created_at: str) -> list[dict[str, Any]]:
        history = []
        if existing_row and _normalize_text(existing_row.get("state_history_json")):
            try:
                parsed = json.loads(_normalize_text(existing_row.get("state_history_json")))
                if isinstance(parsed, list):
                    history.extend([entry for entry in parsed if isinstance(entry, Mapping)])
            except json.JSONDecodeError:
                pass
        if not history or _normalize_text(history[-1].get("state")) != lifecycle_state:
            history.append(
                {
                    "state": lifecycle_state,
                    "state_index": _state_index(lifecycle_state),
                    "changed_at": created_at,
                    "reason": lifecycle_reason,
                    "alignment_status": alignment_status,
                    "certification_status": certification_status,
                }
            )
        return history

    def record_lifecycle_state(
        self,
        *,
        identity: ResearchAssetIdentityContract | Mapping[str, Any],
        lifecycle_state: str,
        lifecycle_reason: str = "",
        alignment_certification: TimeEntityAlignmentCertificationContract | Mapping[str, Any] | None = None,
        certification_result: Mapping[str, Any] | None = None,
        dataset_result: Mapping[str, Any] | None = None,
        source_bundle: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
        created_at: str | None = None,
        notes: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity_contract = identity if isinstance(identity, ResearchAssetIdentityContract) else ResearchAssetIdentityContract.from_mapping(identity)
        identity_validation = validate_research_asset_identity_contract(identity_contract)
        if not identity_validation["ok"]:
            raise ValueError("; ".join(identity_validation["errors"]) or "invalid research asset identity")
        alignment_contract = None
        if alignment_certification is not None:
            alignment_contract = (
                alignment_certification
                if isinstance(alignment_certification, TimeEntityAlignmentCertificationContract)
                else TimeEntityAlignmentCertificationContract(
                    alignment_certification_id=str(alignment_certification.get("alignment_certification_id") or ""),
                    asset_id=str(alignment_certification.get("asset_id") or alignment_certification.get("research_asset_id") or identity_contract.asset_id),
                    research_asset_id=str(alignment_certification.get("research_asset_id") or identity_contract.asset_id),
                    research_asset_name=str(alignment_certification.get("research_asset_name") or identity_contract.asset_name or identity_contract.asset_id),
                    asset_family=str(alignment_certification.get("asset_family") or identity_contract.asset_family),
                    asset_type=str(alignment_certification.get("asset_type") or identity_contract.asset_type),
                    market_profile=str(alignment_certification.get("market_profile") or identity_contract.market_profile),
                    market=str(alignment_certification.get("market") or identity_contract.market),
                    market_type=str(alignment_certification.get("market_type") or identity_contract.market_type),
                    league=str(alignment_certification.get("league") or identity_contract.league),
                    sport=str(alignment_certification.get("sport") or identity_contract.sport),
                    season=str(alignment_certification.get("season") or identity_contract.season),
                    week_or_date=str(alignment_certification.get("week_or_date") or identity_contract.week_or_date),
                    event_id=str(alignment_certification.get("event_id") or identity_contract.event_id),
                    game_id=str(alignment_certification.get("game_id") or identity_contract.game_id),
                    market_id=str(alignment_certification.get("market_id") or identity_contract.market_id),
                    selection=str(alignment_certification.get("selection") or identity_contract.selection),
                    participant_id=str(alignment_certification.get("participant_id") or identity_contract.participant_id),
                    team_id=str(alignment_certification.get("team_id") or identity_contract.team_id),
                    provider_timestamp=str(alignment_certification.get("provider_timestamp") or ""),
                    snapshot_time=str(alignment_certification.get("snapshot_time") or ""),
                    decision_time=str(alignment_certification.get("decision_time") or ""),
                    result_timestamp=str(alignment_certification.get("result_timestamp") or ""),
                    alignment_status=str(alignment_certification.get("alignment_status") or ""),
                    alignment_reason=str(alignment_certification.get("alignment_reason") or ""),
                    failure_reason=str(alignment_certification.get("failure_reason") or ""),
                    alignment_score=_normalize_float(alignment_certification.get("alignment_score"), 0.0),
                    missing_fields=alignment_certification.get("missing_fields") or (),
                    mismatched_fields=alignment_certification.get("mismatched_fields") or (),
                    timing_issues=alignment_certification.get("timing_issues") or (),
                    row_count=int(alignment_certification.get("row_count") or 0),
                    source_row_count=int(alignment_certification.get("source_row_count") or 0),
                    source_name=str(alignment_certification.get("source_name") or ""),
                    source_type=str(alignment_certification.get("source_type") or ""),
                    source_key=str(alignment_certification.get("source_key") or ""),
                    provider=str(alignment_certification.get("provider") or identity_contract.provider),
                    connector=str(alignment_certification.get("connector") or identity_contract.connector),
                    schema_version=str(alignment_certification.get("schema_version") or RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION),
                    lineage_version=str(alignment_certification.get("lineage_version") or identity_contract.lineage_version or "v1"),
                    certification_timestamp=str(alignment_certification.get("certification_timestamp") or ""),
                    certification_notes=alignment_certification.get("certification_notes") or {},
                    metadata=alignment_certification.get("metadata") or {},
                )
            )
        certification_result = dict(certification_result or {})
        dataset_result = dict(dataset_result or {})
        source_bundle = dict(source_bundle or {})
        raw_acquisition_result = dict(raw_acquisition_result or {})
        created_at = _normalize_text(created_at, _utc_now_iso())
        lifecycle_state = _normalize_state(lifecycle_state)
        existing_row = self._existing_lifecycle_row(identity_contract.asset_id)
        existing_identity = ResearchAssetIdentityContract.from_mapping(existing_row) if existing_row else identity_contract
        if existing_row is not None:
            existing_contract_validation = validate_research_asset_identity_contract(existing_identity)
            if not existing_contract_validation["ok"]:
                raise ValueError("existing research asset lifecycle row is corrupt")
            if _identity_core_dict(existing_identity) != _identity_core_dict(identity_contract):
                raise ValueError("research asset identity is immutable and cannot change once recorded")
        existing_state = _normalize_text(existing_row.get("lifecycle_state"), "discovered") if existing_row else "discovered"
        if _state_index(lifecycle_state) < _state_index(existing_state):
            lifecycle_state = existing_state
        alignment_status = _normalize_text(alignment_contract.alignment_status if alignment_contract else certification_result.get("alignment_status"))
        alignment_reason = _normalize_text(alignment_contract.alignment_reason if alignment_contract else certification_result.get("alignment_reason"))
        alignment_score = _normalize_float(alignment_contract.alignment_score if alignment_contract else certification_result.get("alignment_score"), 0.0)
        certification_status = _normalize_text(certification_result.get("certification_state") or certification_result.get("certification_status") or dataset_result.get("certification_status") or lifecycle_state)
        state_history = self._state_history(
            existing_row,
            lifecycle_state=lifecycle_state,
            lifecycle_reason=lifecycle_reason,
            alignment_status=alignment_status,
            certification_status=certification_status,
            created_at=created_at,
        )
        transition_history = list(state_history)
        row = build_research_asset_lifecycle_row(
            identity=identity_contract,
            lifecycle_state=lifecycle_state,
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            profile=_resolve_market_profile(identity_contract.market_profile or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID),
            alignment_certification=alignment_contract,
            certification_result=certification_result,
            dataset_result=dataset_result,
            lifecycle_reason=lifecycle_reason or alignment_reason,
            notes=notes or {},
            state_history=state_history,
        )
        row["alignment_status"] = alignment_status or row.get("alignment_status") or "blocked"
        row["alignment_reason"] = alignment_reason or row.get("alignment_reason") or "time_entity_alignment_checked"
        row["alignment_score"] = alignment_score or row.get("alignment_score") or 0.0
        row["certification_status"] = certification_status or row.get("certification_status") or lifecycle_state
        row["status"] = lifecycle_state
        row["lifecycle_state"] = lifecycle_state
        row["lifecycle_state_index"] = _state_index(lifecycle_state)
        row["state_history_json"] = _as_json(state_history)
        row["transition_history_json"] = _as_json(transition_history)
        row["identity_json"] = _as_json(identity_contract.as_dict())
        row["alignment_json"] = _as_json(alignment_contract.as_dict() if alignment_contract else certification_result)
        row["notes_json"] = _as_json(dict(notes or {}))
        row["updated_at"] = created_at
        validation = validate_research_asset_lifecycle_row(row)
        if not validation["ok"]:
            raise ValueError("; ".join(validation.get("validation", {}).get("errors", [])) or "research asset lifecycle row validation failed")
        self.store.upsert("research_asset_lifecycles", row, key_columns=("asset_id",))
        alignment_row = None
        if alignment_contract is not None:
            alignment_row = build_time_entity_alignment_certification_row(
                identity=identity_contract,
                alignment=alignment_contract,
                profile=_resolve_market_profile(identity_contract.market_profile or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID),
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                batch_id=row.get("batch_id", ""),
            )
            alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
            if not alignment_validation["ok"]:
                raise ValueError("; ".join(alignment_validation.get("validation", {}).get("errors", [])) or "time entity alignment row validation failed")
            self.store.upsert("research_asset_alignment_certifications", alignment_row, key_columns=("alignment_certification_id",))
        return {
            "ok": validation["ok"],
            "status": "recorded" if validation["ok"] else "blocked",
            "identity": identity_contract.as_dict(),
            "research_asset_lifecycle": row,
            "validation": validation,
            "alignment_certification_row": alignment_row,
            "alignment_certification": alignment_contract.as_dict() if alignment_contract else {},
        }

    def certify_time_entity_alignment(
        self,
        *,
        identity: ResearchAssetIdentityContract | Mapping[str, Any],
        rows: Sequence[Mapping[str, Any]],
        required_fields: Sequence[str] = (),
        required_timestamps: Sequence[str] = (),
        profile: MarketProfileContract | Mapping[str, Any] | None = None,
        source_bundle: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
        created_at: str | None = None,
        lifecycle_state: str = "integrity_verified",
    ) -> dict[str, Any]:
        identity_contract = identity if isinstance(identity, ResearchAssetIdentityContract) else ResearchAssetIdentityContract.from_mapping(identity)
        profile_contract = _resolve_market_profile(identity_contract.market_profile or DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID)
        if profile is not None:
            profile_contract = profile if isinstance(profile, MarketProfileContract) else MarketProfileContract.from_mapping(profile)
        alignment_contract = build_time_entity_alignment_certification(
            identity=identity_contract,
            rows=rows,
            required_fields=required_fields,
            required_timestamps=required_timestamps,
            profile=profile_contract,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            asset_name=identity_contract.asset_name,
            asset_type=identity_contract.asset_type,
            lifecycle_state=lifecycle_state,
        )
        row = self.record_lifecycle_state(
            identity=identity_contract,
            lifecycle_state=_normalize_state(lifecycle_state),
            lifecycle_reason=alignment_contract.alignment_reason,
            alignment_certification=alignment_contract,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes=alignment_contract.certification_notes,
        )
        return {
            "ok": alignment_contract.alignment_status == "aligned",
            "status": alignment_contract.alignment_status,
            "identity": identity_contract.as_dict(),
            "alignment_certification": alignment_contract.as_dict(),
            "research_asset_lifecycle": row["research_asset_lifecycle"],
            "alignment_certification_row": row["alignment_certification_row"],
            "validation": row["validation"],
        }

    def record_research_asset_certified(
        self,
        *,
        identity: ResearchAssetIdentityContract | Mapping[str, Any],
        certification_result: Mapping[str, Any],
        source_bundle: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        return self.record_lifecycle_state(
            identity=identity,
            lifecycle_state="research_asset_certified",
            lifecycle_reason=_normalize_text(certification_result.get("certification_reason"), "research asset certified"),
            alignment_certification=certification_result.get("alignment_certification"),
            certification_result=certification_result,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes=certification_result.get("summary") or {},
        )

    def record_dataset_certified(
        self,
        *,
        identity: ResearchAssetIdentityContract | Mapping[str, Any],
        certification_result: Mapping[str, Any],
        source_bundle: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        return self.record_lifecycle_state(
            identity=identity,
            lifecycle_state="dataset_certified",
            lifecycle_reason=_normalize_text(certification_result.get("certification_reason"), "dataset certified"),
            certification_result=certification_result,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            created_at=created_at,
            notes=certification_result.get("summary") or {},
        )

    def build_readiness_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID,
        fixture: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = _resolve_market_profile(profile_id)
        profile_validation = _validate_market_profile(profile)
        identity_catalog = self.build_identity_catalog(profile_id=profile.profile_id)
        lifecycle_rows = self.store.fetch("research_asset_lifecycles", order_by="asset_id ASC") if self.store.table_exists("research_asset_lifecycles") else []
        alignment_rows = self.store.fetch("research_asset_alignment_certifications", order_by="alignment_certification_id ASC") if self.store.table_exists("research_asset_alignment_certifications") else []
        lifecycle_states = [ _normalize_text(row.get("lifecycle_state"), "discovered") for row in lifecycle_rows ]
        alignment_statuses = [ _normalize_text(row.get("alignment_status")) for row in alignment_rows ]
        certified_assets = [row for row in lifecycle_rows if _normalize_text(row.get("lifecycle_state")) in {"research_asset_certified", "dataset_certified", "feature_ready", "math_ready", "signal_ready", "backtest_ready", "production_ready"}]
        blocked_assets = [row for row in lifecycle_rows if _normalize_text(row.get("alignment_status")) == "blocked" or _normalize_text(row.get("lifecycle_state")) in {"discovered", "source_identified"}]
        missing_assets = [identity.asset_id for identity in identity_catalog if identity.asset_id not in {str(row.get("asset_id")) for row in lifecycle_rows}]
        state_counts = {state: lifecycle_states.count(state) for state in RESEARCH_ASSET_LIFECYCLE_STATES if lifecycle_states.count(state)}
        alignment_counts = {status: alignment_statuses.count(status) for status in sorted(set(alignment_statuses)) if status}
        ready = bool(profile_validation["ok"] and not blocked_assets and len(certified_assets) >= len(identity_catalog) and identity_catalog)
        return {
            "ok": ready,
            "status": "ready" if ready else "partial" if lifecycle_rows or alignment_rows else "missing",
            "profile": profile.as_dict(),
            "profile_validation": profile_validation,
            "identity_catalog": [identity.as_dict() for identity in identity_catalog],
            "research_asset_lifecycles": lifecycle_rows,
            "time_entity_alignment_certifications": alignment_rows,
            "state_counts": state_counts,
            "alignment_status_counts": alignment_counts,
            "certified_assets": certified_assets,
            "blocked_assets": blocked_assets,
            "missing_assets": missing_assets,
            "alignment_failures": [
                {
                    "alignment_certification_id": row.get("alignment_certification_id"),
                    "research_asset_id": row.get("research_asset_id"),
                    "alignment_status": row.get("alignment_status"),
                    "failure_reason": row.get("failure_reason"),
                    "alignment_reason": row.get("alignment_reason"),
                }
                for row in alignment_rows
                if _normalize_text(row.get("alignment_status")) != "aligned"
            ],
            "summary": {
                "identity_count": len(identity_catalog),
                "lifecycle_count": len(lifecycle_rows),
                "alignment_count": len(alignment_rows),
                "certified_count": len(certified_assets),
                "blocked_count": len(blocked_assets),
                "missing_count": len(missing_assets),
                "state_counts": state_counts,
                "alignment_status_counts": alignment_counts,
            },
            "storage": self.store.health(),
            "fixture_summary": {
                "source_name": (fixture or {}).get("source_bundle", {}).get("source_name", DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_NAME),
                "source_type": (fixture or {}).get("source_bundle", {}).get("source_type", DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_TYPE),
                "provider": (fixture or {}).get("source_bundle", {}).get("provider", DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER),
                "raw_acquisition_ok": bool(raw_acquisition_result.get("ok")) if raw_acquisition_result else None,
            },
        }

    def dashboard_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID,
        fixture: Mapping[str, Any] | None = None,
        raw_acquisition_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = self.build_readiness_snapshot(
            profile_id=profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
        snapshot["lifecycle_readiness"] = {
            "status": snapshot.get("status"),
            "state_counts": snapshot.get("state_counts", {}),
            "alignment_status_counts": snapshot.get("alignment_status_counts", {}),
            "missing_assets": snapshot.get("missing_assets", []),
            "blocked_assets": snapshot.get("blocked_assets", []),
            "certified_assets": [row.get("asset_id") for row in snapshot.get("certified_assets", [])],
        }
        snapshot["alignment_readiness"] = {
            "status": "ready" if not snapshot.get("alignment_failures") else "blocked",
            "failures": snapshot.get("alignment_failures", []),
            "alignment_status_counts": snapshot.get("alignment_status_counts", {}),
        }
        snapshot["dataset_readiness"] = {
            "status": snapshot.get("status"),
            "missing_assets": snapshot.get("missing_assets", []),
            "blocked_assets": snapshot.get("blocked_assets", []),
        }
        snapshot["readiness_summary"] = {
            "lifecycle_state_count": len(snapshot.get("state_counts", {})),
            "alignment_failure_count": len(snapshot.get("alignment_failures", [])),
            "certified_asset_count": len(snapshot.get("certified_assets", [])),
            "missing_asset_count": len(snapshot.get("missing_assets", [])),
        }
        return snapshot


def build_research_asset_lifecycle_runtime_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID,
    fixture: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path, backend=backend)
    try:
        return runtime.dashboard_snapshot(
            profile_id=profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
    finally:
        runtime.close()


def get_research_asset_lifecycle_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID,
    fixture: Mapping[str, Any] | None = None,
    raw_acquisition_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return build_research_asset_lifecycle_runtime_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile_id,
            fixture=fixture,
            raw_acquisition_result=raw_acquisition_result,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "research_asset_lifecycle_snapshot_error",
            "profile": {},
            "profile_validation": {},
            "identity_catalog": [],
            "research_asset_lifecycles": [],
            "time_entity_alignment_certifications": [],
            "state_counts": {},
            "alignment_status_counts": {},
            "certified_assets": [],
            "blocked_assets": [],
            "missing_assets": [],
            "alignment_failures": [],
            "summary": {},
            "lifecycle_readiness": {},
            "alignment_readiness": {},
            "dataset_readiness": {},
            "readiness_summary": {},
            "storage": {},
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_ASSET_CLASS",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_DATASET_NAME",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_MARKET_TYPE",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_OWNER",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROFILE_ID",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_PROVIDER",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_KEY",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_NAME",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_SOURCE_TYPE",
    "DEFAULT_RESEARCH_ASSET_LIFECYCLE_STORAGE_PATH",
    "RESEARCH_ASSET_LIFECYCLE_RUNTIME_SCHEMA_VERSION",
    "RESEARCH_ASSET_LIFECYCLE_STATES",
    "RESEARCH_ASSET_LIFECYCLE_REQUIRED_FIELDS",
    "ResearchAssetIdentityContract",
    "ResearchAssetLifecycleRuntime",
    "TimeEntityAlignmentCertificationContract",
    "TIME_ENTITY_ALIGNMENT_FAILURE_REASONS",
    "TIME_ENTITY_ALIGNMENT_REQUIRED_FIELDS",
    "TIME_ENTITY_ALIGNMENT_ROW_REQUIRED_FIELDS",
    "build_research_asset_identity_contract",
    "build_research_asset_lifecycle_runtime_dashboard_snapshot",
    "build_research_asset_lifecycle_row",
    "build_time_entity_alignment_certification",
    "build_time_entity_alignment_certification_row",
    "get_research_asset_lifecycle_snapshot_for_dashboard",
    "validate_research_asset_identity_contract",
    "validate_research_asset_lifecycle_row",
    "validate_time_entity_alignment_certification_row",
]
