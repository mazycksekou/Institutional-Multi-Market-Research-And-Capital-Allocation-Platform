from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.data.data_paths import get_runtime_data_path
from src.data.historical_research_asset_certification_runtime import HistoricalResearchAssetCertificationRuntime
from src.data.historical_dataset_acquisition_runtime import HistoricalDatasetAcquisitionRuntime
from src.data.local_platform import DatasetContract, LocalDataPlatform
from src.data.market_profile_contracts import MarketProfileContract, validate_market_profile_contract
from src.data.market_profile_registry import get_market_profile, register_market_profile
from src.data.research_asset_lifecycle_runtime import ResearchAssetLifecycleRuntime, build_research_asset_identity_contract
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
DEFAULT_NFL_HISTORICAL_DATASET_ID = "dataset.sports.nfl.historical_dataset"
DEFAULT_NFL_HISTORICAL_DATASET_NAME = "nfl_historical_dataset_population"
HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION = "src.data.historical_research_database.population.v1"
HISTORICAL_DATASET_POPULATION_STAGE_NAME = "historical_dataset_population"
HISTORICAL_DATASET_BATCH_TABLE = "historical_dataset_batches"
HISTORICAL_DATASET_ROW_TABLE = "historical_dataset_rows"
HISTORICAL_DATASET_CUTOFF_POLICY_ID = "nfl.minimum_schema.kickoff_minus_five_minutes.v1"
HISTORICAL_DATASET_JOIN_POLICY_ID = "nfl.minimum_schema.event_market_context.v1"
HISTORICAL_DATASET_CONTRACT_VERSION = "nfl.minimum_schema.dataset_contract.v1"
HISTORICAL_DATASET_DECISION_CUTOFF_OFFSET = timedelta(minutes=5)
HISTORICAL_DATASET_ALLOWED_LIFECYCLE_STATES: tuple[str, ...] = (
    "feature_ready",
    "math_ready",
    "signal_ready",
    "backtest_ready",
    "production_ready",
)
HISTORICAL_DATASET_REQUIRED_ASSETS: tuple[dict[str, str], ...] = (
    {
        "research_asset_id": "dataset.sports.nfl.schedule",
        "table_name": "nfl_schedule",
        "row_id_field": "schedule_id",
    },
    {
        "research_asset_id": "dataset.sports.nfl.results",
        "table_name": "nfl_results",
        "row_id_field": "result_id",
    },
    {
        "research_asset_id": "dataset.nfl.odds_snapshots",
        "table_name": "nfl_odds_snapshots",
        "row_id_field": "odds_snapshot_id",
    },
    {
        "research_asset_id": "dataset.nfl.weather_snapshots",
        "table_name": "nfl_weather_snapshots",
        "row_id_field": "weather_snapshot_id",
    },
    {
        "research_asset_id": "dataset.nfl.injury_snapshots",
        "table_name": "nfl_injury_snapshots",
        "row_id_field": "injury_snapshot_id",
    },
    {
        "research_asset_id": "dataset.nfl.team_stats_snapshots",
        "table_name": "nfl_team_stats_snapshots",
        "row_id_field": "team_stats_snapshot_id",
    },
)
HISTORICAL_DATASET_REQUIRED_ASSET_LOOKUP: dict[str, dict[str, str]] = {
    asset["research_asset_id"]: dict(asset) for asset in HISTORICAL_DATASET_REQUIRED_ASSETS
}
HISTORICAL_DATASET_IDENTITY_ASSET_IDS: tuple[str, ...] = (
    "dataset.sports.nfl.schedule",
    "dataset.nfl.odds_snapshots",
    "dataset.nfl.weather_snapshots",
    "dataset.nfl.injury_snapshots",
    "dataset.nfl.team_stats_snapshots",
)
HISTORICAL_DATASET_TEAM_STAT_UNITS: dict[str, str] = {
    "rest_days": "days",
    "travel_distance_miles": "miles",
    "travel_timezone_change": "hours",
    "offensive_efficiency": "rating",
    "defensive_efficiency": "rating",
    "pace": "plays_per_game",
    "play_volume": "plays",
    "scoring_efficiency": "points_per_drive",
    "turnover_rate": "ratio",
    "red_zone_efficiency": "ratio",
    "third_down_efficiency": "ratio",
    "special_teams_efficiency": "rating",
    "coaching_continuity": "ratio",
    "roster_continuity": "ratio",
    "injury_adjusted_availability": "ratio",
    "efficiency_window_games": "games",
}

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


def _load_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value in (None, ""):
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return list(parsed)
    return []


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


def _asset_row_id_field(research_asset_id: str) -> str:
    asset = HISTORICAL_DATASET_REQUIRED_ASSET_LOOKUP.get(research_asset_id) or {}
    return _normalize_text(asset.get("row_id_field"), "record_id")


def _latest_certified_research_asset_row(
    storage: LocalStorageEngine,
    *,
    research_asset_id: str,
) -> dict[str, Any]:
    if not storage.table_exists("historical_research_asset_certifications"):
        return {}
    rows = storage.fetch(
        "historical_research_asset_certifications",
        where="research_asset_id = ? AND certification_status = ?",
        params=[research_asset_id, "certified"],
        order_by="certified_at ASC, created_at ASC, certification_id ASC",
    )
    return dict(rows[-1]) if rows else {}


def _latest_certified_dataset_row_for_batch(
    storage: LocalStorageEngine,
    *,
    batch_id: str,
) -> dict[str, Any]:
    if not storage.table_exists("historical_certifications"):
        return {}
    rows = storage.fetch(
        "historical_certifications",
        where="batch_id = ? AND certification_status = ?",
        params=[batch_id, "certified"],
        order_by="certified_at ASC, created_at ASC, certification_id ASC",
    )
    return dict(rows[-1]) if rows else {}


def _latest_lifecycle_row(
    storage: LocalStorageEngine,
    *,
    asset_id: str,
) -> dict[str, Any]:
    if not storage.table_exists("research_asset_lifecycles"):
        return {}
    rows = storage.fetch(
        "research_asset_lifecycles",
        where="asset_id = ?",
        params=[asset_id],
        order_by="created_at ASC, updated_at ASC, asset_id ASC",
    )
    return dict(rows[-1]) if rows else {}


def _alignment_rows_for_asset(
    storage: LocalStorageEngine,
    *,
    research_asset_id: str,
) -> list[dict[str, Any]]:
    if not storage.table_exists("research_asset_alignment_certifications"):
        return []
    return [
        dict(row)
        for row in storage.fetch(
            "research_asset_alignment_certifications",
            where="research_asset_id = ?",
            params=[research_asset_id],
            order_by="certification_timestamp ASC, alignment_certification_id ASC",
        )
    ]


def _row_collection_for_asset(
    storage: LocalStorageEngine,
    *,
    research_asset_id: str,
    version_id: str,
) -> list[dict[str, Any]]:
    asset = HISTORICAL_DATASET_REQUIRED_ASSET_LOOKUP.get(research_asset_id) or {}
    table_name = _normalize_text(asset.get("table_name"))
    row_id_field = _normalize_text(asset.get("row_id_field"))
    if not table_name or not storage.table_exists(table_name):
        return []
    where = "version_id = ?" if version_id else None
    params: list[Any] = [version_id] if version_id else []
    order_by = f"{row_id_field} ASC" if row_id_field else None
    return [
        dict(row)
        for row in storage.fetch(
            table_name,
            where=where,
            params=params,
            order_by=order_by,
        )
    ]


def _is_allowed_lifecycle_state(value: Any) -> bool:
    return _normalize_text(value).lower() in HISTORICAL_DATASET_ALLOWED_LIFECYCLE_STATES


def _bool_to_int(value: Any) -> int:
    return 1 if bool(value) else 0


def _min_dt() -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _candidate_sort_key(
    row: Mapping[str, Any],
    *,
    row_id_field: str,
    timestamp_fields: Sequence[str],
) -> tuple[Any, ...]:
    values: list[Any] = []
    for field_name in timestamp_fields:
        values.append(_parse_iso(row.get(field_name)) or _min_dt())
    values.append(_normalize_text(row.get(row_id_field)))
    return tuple(values)


def _select_latest_candidate(
    rows: Sequence[Mapping[str, Any]],
    *,
    row_id_field: str,
    timestamp_fields: Sequence[str],
) -> dict[str, Any]:
    if not rows:
        return {}
    ordered = sorted(
        (dict(row) for row in rows),
        key=lambda row: _candidate_sort_key(
            row,
            row_id_field=row_id_field,
            timestamp_fields=timestamp_fields,
        ),
    )
    return ordered[-1]


def _source_row_identifier(research_asset_id: str, row: Mapping[str, Any]) -> str:
    return _normalize_text(row.get(_asset_row_id_field(research_asset_id)))


def _source_row_has_provenance(row: Mapping[str, Any]) -> bool:
    if not _normalize_text(row.get("lineage_id")):
        return False
    if not _normalize_text(row.get("source_metadata_json")):
        return False
    field_provenance = _load_json_mapping(row.get("field_provenance_json"))
    if "field_provenance_json" in row and not field_provenance:
        return False
    return True


def _match_alignment_row(
    research_asset_id: str,
    *,
    alignment_row: Mapping[str, Any],
    source_row: Mapping[str, Any],
) -> bool:
    game_id = _normalize_text(source_row.get("game_id"), _normalize_text(source_row.get("event_id")))
    if game_id and _normalize_text(alignment_row.get("game_id")) != game_id:
        return False
    if research_asset_id == "dataset.sports.nfl.schedule":
        return True
    if research_asset_id == "dataset.sports.nfl.results":
        return True
    if research_asset_id == "dataset.nfl.weather_snapshots":
        return True
    if research_asset_id == "dataset.nfl.odds_snapshots":
        selection = _normalize_text(source_row.get("selection"))
        market_type = _normalize_text(source_row.get("market_type"))
        market_id = _normalize_text(source_row.get("odds_snapshot_id"))
        return (
            _normalize_text(alignment_row.get("selection")) in {"", selection}
            and _normalize_text(alignment_row.get("market_type")) in {"", market_type}
            and _normalize_text(alignment_row.get("market_id")) in {"", market_id}
        )
    if research_asset_id == "dataset.nfl.team_stats_snapshots":
        team_id = _normalize_text(source_row.get("team_id"))
        market_id = _normalize_text(source_row.get("team_stats_snapshot_id"))
        return (
            _normalize_text(alignment_row.get("team_id")) == team_id
            and _normalize_text(alignment_row.get("market_id")) in {"", market_id}
        )
    if research_asset_id == "dataset.nfl.injury_snapshots":
        team_id = _normalize_text(source_row.get("team_id"))
        participant_id = _normalize_text(source_row.get("player_id"))
        market_id = _normalize_text(source_row.get("injury_snapshot_id"))
        return (
            _normalize_text(alignment_row.get("team_id")) == team_id
            and _normalize_text(alignment_row.get("participant_id")) in {"", participant_id}
            and _normalize_text(alignment_row.get("market_id")) in {"", market_id}
        )
    return False


def _matching_alignment_ids(
    research_asset_id: str,
    *,
    alignment_rows: Sequence[Mapping[str, Any]],
    source_row: Mapping[str, Any],
) -> list[str]:
    aligned_rows = [
        alignment_row
        for alignment_row in alignment_rows
        if _normalize_text(alignment_row.get("alignment_status")) == "aligned"
    ]
    matches = []
    for alignment_row in aligned_rows:
        if _match_alignment_row(
            research_asset_id,
            alignment_row=alignment_row,
            source_row=source_row,
        ):
            alignment_id = _normalize_text(alignment_row.get("alignment_certification_id"))
            if alignment_id and alignment_id not in matches:
                matches.append(alignment_id)
    if not matches and research_asset_id == "dataset.nfl.odds_snapshots" and len(aligned_rows) == 1:
        alignment_id = _normalize_text(aligned_rows[0].get("alignment_certification_id"))
        if alignment_id:
            matches.append(alignment_id)
    return matches


def _source_asset_status_bundle(
    storage: LocalStorageEngine,
    *,
    research_asset_id: str,
) -> dict[str, Any]:
    asset = HISTORICAL_DATASET_REQUIRED_ASSET_LOOKUP.get(research_asset_id) or {}
    certification_row = _latest_certified_research_asset_row(
        storage,
        research_asset_id=research_asset_id,
    )
    dataset_certification_row = _latest_certified_dataset_row_for_batch(
        storage,
        batch_id=_normalize_text(certification_row.get("batch_id")),
    ) if certification_row else {}
    lifecycle_row = _latest_lifecycle_row(storage, asset_id=research_asset_id)
    alignment_rows = _alignment_rows_for_asset(storage, research_asset_id=research_asset_id)
    version_id = _normalize_text(certification_row.get("version_id"))
    rows = _row_collection_for_asset(
        storage,
        research_asset_id=research_asset_id,
        version_id=version_id,
    ) if version_id else []
    errors: list[str] = []
    if not certification_row:
        errors.append(f"missing_source_certification:{research_asset_id}")
    if certification_row and not dataset_certification_row:
        errors.append(f"missing_source_dataset_certification:{research_asset_id}")
    lifecycle_state = _normalize_text(lifecycle_row.get("lifecycle_state")).lower()
    if certification_row and not _is_allowed_lifecycle_state(lifecycle_state):
        errors.append(f"insufficient_source_lifecycle:{research_asset_id}:{lifecycle_state or 'missing'}")
    if certification_row and not alignment_rows:
        errors.append(f"missing_source_alignment_certification:{research_asset_id}")
    if certification_row and not rows:
        errors.append(f"missing_source_rows:{research_asset_id}")
    return {
        "research_asset_id": research_asset_id,
        "table_name": _normalize_text(asset.get("table_name")),
        "row_id_field": _normalize_text(asset.get("row_id_field")),
        "certification_row": certification_row,
        "dataset_certification_row": dataset_certification_row,
        "lifecycle_row": lifecycle_row,
        "alignment_rows": alignment_rows,
        "rows": rows,
        "errors": errors,
    }


def _target_team_context(
    schedule_row: Mapping[str, Any],
    odds_row: Mapping[str, Any],
) -> dict[str, str]:
    selection = _normalize_text(odds_row.get("selection")).lower()
    if selection == "home":
        return {
            "target_team_id": _normalize_text(schedule_row.get("home_team_id")),
            "target_team": _normalize_text(schedule_row.get("home_team")),
            "opponent_team_id": _normalize_text(schedule_row.get("away_team_id")),
            "opponent_team": _normalize_text(schedule_row.get("away_team")),
            "team_side": "home",
        }
    if selection == "away":
        return {
            "target_team_id": _normalize_text(schedule_row.get("away_team_id")),
            "target_team": _normalize_text(schedule_row.get("away_team")),
            "opponent_team_id": _normalize_text(schedule_row.get("home_team_id")),
            "opponent_team": _normalize_text(schedule_row.get("home_team")),
            "team_side": "away",
        }
    return {
        "target_team_id": "",
        "target_team": "",
        "opponent_team_id": "",
        "opponent_team": "",
        "team_side": "",
    }


def _injury_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    availability_counts: dict[str, int] = {}
    report_status_counts: dict[str, int] = {}
    positions: list[str] = []
    latest_report_time = ""
    for row in rows:
        availability = _normalize_text(row.get("availability_status"), "unknown")
        report_status = _normalize_text(row.get("report_status"), "unknown")
        position = _normalize_text(row.get("position"))
        availability_counts[availability] = availability_counts.get(availability, 0) + 1
        report_status_counts[report_status] = report_status_counts.get(report_status, 0) + 1
        if position and position not in positions:
            positions.append(position)
        report_time = _to_iso(row.get("report_time"))
        if report_time and (not latest_report_time or (_parse_iso(report_time) or _min_dt()) > (_parse_iso(latest_report_time) or _min_dt())):
            latest_report_time = report_time
    return {
        "row_count": len(rows),
        "availability_status_counts": availability_counts,
        "report_status_counts": report_status_counts,
        "positions": positions,
        "latest_report_time": latest_report_time,
        "row_ids": [_source_row_identifier("dataset.nfl.injury_snapshots", row) for row in rows],
    }


def _decision_cutoff_from_kickoff(kickoff: datetime) -> str:
    return (kickoff - HISTORICAL_DATASET_DECISION_CUTOFF_OFFSET).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _asset_availability_time(research_asset_id: str, row: Mapping[str, Any]) -> datetime | None:
    if research_asset_id == "dataset.nfl.odds_snapshots":
        field_names = ("decision_time", "snapshot_time", "source_snapshot_time")
    elif research_asset_id == "dataset.nfl.weather_snapshots":
        field_names = ("forecast_time", "snapshot_time", "source_snapshot_time")
    elif research_asset_id == "dataset.nfl.injury_snapshots":
        field_names = ("report_time", "snapshot_time", "source_snapshot_time")
    elif research_asset_id == "dataset.nfl.team_stats_snapshots":
        field_names = (
            "snapshot_time",
            "source_snapshot_time",
            "source_retrieved_at",
            "team_stats_cutoff_time",
        )
    elif research_asset_id == "dataset.sports.nfl.schedule":
        field_names = ("kickoff_time", "snapshot_time", "source_snapshot_time")
    else:
        field_names = ("snapshot_time", "source_snapshot_time", "decision_time")
    latest: datetime | None = None
    for field_name in field_names:
        candidate = _parse_iso(row.get(field_name))
        if candidate and (latest is None or candidate > latest):
            latest = candidate
    return latest


def _selected_asset_timestamp(research_asset_id: str, row: Mapping[str, Any]) -> str:
    return _to_iso(_asset_availability_time(research_asset_id, row))


def _freshness_seconds(cutoff_time: datetime, research_asset_id: str, row: Mapping[str, Any]) -> int:
    availability_time = _asset_availability_time(research_asset_id, row)
    if availability_time is None:
        return -1
    return max(int((cutoff_time - availability_time).total_seconds()), 0)


def _derive_final_result_label(
    schedule_row: Mapping[str, Any],
    result_row: Mapping[str, Any],
) -> str:
    winner_team_id = _normalize_text(result_row.get("winner_team_id"))
    if winner_team_id and winner_team_id == _normalize_text(schedule_row.get("home_team_id")):
        return "home_win"
    if winner_team_id and winner_team_id == _normalize_text(schedule_row.get("away_team_id")):
        return "away_win"
    if _normalize_text(result_row.get("settlement_status")).lower() == "void":
        return "void"
    return "unknown"


def _expected_team_stat_units(row: Mapping[str, Any]) -> bool:
    units = _load_json_mapping(row.get("metric_units_json"))
    if not units:
        return False
    for field_name, expected_unit in HISTORICAL_DATASET_TEAM_STAT_UNITS.items():
        if _normalize_text(units.get(field_name)) != expected_unit:
            return False
    return True


def _stable_dataset_batch_id(
    dataset_id: str,
    *,
    source_certification_ids: Mapping[str, Any],
    source_dataset_certification_ids: Mapping[str, Any],
    source_asset_version_ids: Mapping[str, Any],
    source_asset_batch_ids: Mapping[str, Any],
    event_scope: Mapping[str, Any],
) -> str:
    digest = _stable_id(
        "historical_dataset_batch",
        dataset_id,
        HISTORICAL_DATASET_CONTRACT_VERSION,
        HISTORICAL_DATASET_CUTOFF_POLICY_ID,
        HISTORICAL_DATASET_JOIN_POLICY_ID,
        _as_json(source_certification_ids),
        _as_json(source_dataset_certification_ids),
        _as_json(source_asset_version_ids),
        _as_json(source_asset_batch_ids),
        _as_json(event_scope),
    )
    return f"{dataset_id}.batch.{digest}"


def _stable_dataset_version_id(dataset_id: str, batch_id: str) -> str:
    return f"{dataset_id}.version.{_stable_id('historical_dataset_version', dataset_id, batch_id)}"


def _base_dataset_contract(storage_path: Path) -> DatasetContract:
    return DatasetContract.create(
        dataset_name=DEFAULT_NFL_HISTORICAL_DATASET_NAME,
        dataset_id=DEFAULT_NFL_HISTORICAL_DATASET_ID,
        source_name="historical_dataset_population_runtime",
        source_type="population_runtime",
        market=DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
        sport="football",
        asset_class="sports",
        provider="repository",
        schema_version=HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
        feature_pack=HISTORICAL_DATASET_CONTRACT_VERSION,
        storage_location=str(storage_path),
        readiness="feature_ready",
        update_frequency="manual",
        validation_state="pending",
        owner="src.data",
        status="registered",
        market_type="historical_dataset_population",
        quality_score=1.0,
        metadata={
            "profile_id": DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
            "minimum_schema": True,
            "cutoff_policy_id": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
            "join_policy_id": HISTORICAL_DATASET_JOIN_POLICY_ID,
        },
    )


def _serialize_source_reference(
    *,
    research_asset_id: str,
    source_row: Mapping[str, Any],
    certification_row: Mapping[str, Any],
    dataset_certification_row: Mapping[str, Any],
    alignment_ids: Sequence[str],
) -> dict[str, Any]:
    return {
        "research_asset_id": research_asset_id,
        "source_row_id": _source_row_identifier(research_asset_id, source_row),
        "version_id": _normalize_text(certification_row.get("version_id")),
        "batch_id": _normalize_text(certification_row.get("batch_id")),
        "certification_id": _normalize_text(certification_row.get("certification_id")),
        "dataset_certification_id": _normalize_text(dataset_certification_row.get("certification_id")),
        "alignment_certification_ids": list(alignment_ids),
        "snapshot_time": _to_iso(source_row.get("snapshot_time")),
        "source_snapshot_time": _to_iso(source_row.get("source_snapshot_time")),
        "decision_time": _to_iso(source_row.get("decision_time")),
    }


def _update_rejected_ids(
    rejected_ids: dict[str, set[str]],
    category: str,
    row_id: str,
) -> None:
    if not row_id:
        return
    rejected_ids.setdefault(category, set()).add(row_id)


def _build_dataset_population_certification_row(
    *,
    profile: MarketProfileContract,
    batch_id: str,
    version_id: str,
    created_at: str,
    validation: Mapping[str, Any],
    evidence_package_id: str,
    source_name: str,
    source_type: str,
    source_key: str,
) -> dict[str, Any]:
    row = _build_certification_row(
        profile=profile,
        batch_id=batch_id,
        dataset_version=version_id,
        stage_name="historical_dataset_population.minimum_schema",
        validation=validation,
        source_name=source_name,
        source_type=source_type,
        source_key=source_key,
        created_at=created_at,
    )
    row["context_json"] = _as_json(
        {
            "dataset_id": DEFAULT_NFL_HISTORICAL_DATASET_ID,
            "evidence_package_id": evidence_package_id,
            "validation": dict(validation),
        }
    )
    row["payload_json"] = _as_json(
        {
            "dataset_id": DEFAULT_NFL_HISTORICAL_DATASET_ID,
            "dataset_name": DEFAULT_NFL_HISTORICAL_DATASET_NAME,
            "batch_id": batch_id,
            "version_id": version_id,
            "evidence_package_id": evidence_package_id,
            "validation": dict(validation),
        }
    )
    row["version_id"] = version_id
    row["schema_version"] = HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION
    return row


def _lineage_edge_row(
    contract: DatasetContract,
    *,
    version_id: str,
    snapshot_id: str,
    batch_lineage_id: str,
    source_stage: str,
    source_id: str,
    target_id: str,
    step_index: int,
    payload: Mapping[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "lineage_edge_id": _stable_id(
            "historical_dataset_lineage_edge",
            contract.dataset_id,
            version_id,
            source_stage,
            source_id,
            target_id,
        ),
        "dataset_id": contract.dataset_id,
        "dataset_name": contract.dataset_name,
        "owner": contract.owner,
        "sport": contract.sport,
        "feature_pack": contract.feature_pack,
        "storage_location": contract.storage_location,
        "readiness": contract.readiness,
        "update_frequency": contract.update_frequency,
        "validation_state": contract.validation_state,
        "status": contract.status,
        "schema_version": contract.schema_version,
        "created_at": created_at,
        "updated_at": created_at,
        "source": contract.source_name,
        "provider": contract.provider,
        "market": contract.market,
        "market_type": contract.market_type,
        "asset_class": contract.asset_class,
        "snapshot_id": snapshot_id,
        "lineage_id": batch_lineage_id,
        "version_id": version_id,
        "quality_score": 1.0,
        "source_stage": source_stage,
        "source_id": source_id,
        "target_stage": "historical_dataset_row",
        "target_id": target_id,
        "transformation": "attach_certified_research_asset_to_historical_dataset_row",
        "step_index": step_index,
        "payload_json": _as_json(dict(payload)),
    }


def build_historical_dataset_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
) -> dict[str, Any]:
    if profile_id != DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID:
        raise NotImplementedError("Historical dataset population currently supports sports:nfl only.")
    profile = _ensure_profile(profile_id=profile_id)
    storage = create_historical_research_storage_engine(storage_path, backend=backend)
    try:
        source_assets = {
            asset["research_asset_id"]: _source_asset_status_bundle(
                storage,
                research_asset_id=asset["research_asset_id"],
            )
            for asset in HISTORICAL_DATASET_REQUIRED_ASSETS
        }
        source_errors = [
            error
            for bundle in source_assets.values()
            for error in bundle.get("errors", [])
        ]
        schedule_rows = list(source_assets["dataset.sports.nfl.schedule"]["rows"])
        event_scope = {
            "season_values": sorted(
                {
                    _normalize_text(row.get("season"))
                    for row in schedule_rows
                    if _normalize_text(row.get("season"))
                }
            ),
            "week_values": sorted(
                {
                    _normalize_text(row.get("week"))
                    for row in schedule_rows
                    if _normalize_text(row.get("week"))
                }
            ),
            "game_ids": sorted(
                {
                    _normalize_text(row.get("game_id"))
                    for row in schedule_rows
                    if _normalize_text(row.get("game_id"))
                }
            ),
        }
        source_certification_ids = {
            asset_id: _normalize_text(bundle.get("certification_row", {}).get("certification_id"))
            for asset_id, bundle in source_assets.items()
        }
        source_dataset_certification_ids = {
            asset_id: _normalize_text(bundle.get("dataset_certification_row", {}).get("certification_id"))
            for asset_id, bundle in source_assets.items()
        }
        source_asset_version_ids = {
            asset_id: _normalize_text(bundle.get("certification_row", {}).get("version_id"))
            for asset_id, bundle in source_assets.items()
        }
        source_asset_batch_ids = {
            asset_id: _normalize_text(bundle.get("certification_row", {}).get("batch_id"))
            for asset_id, bundle in source_assets.items()
        }
        identity_source_certification_ids = {
            asset_id: value
            for asset_id, value in source_certification_ids.items()
            if asset_id in HISTORICAL_DATASET_IDENTITY_ASSET_IDS
        }
        identity_source_dataset_certification_ids = {
            asset_id: value
            for asset_id, value in source_dataset_certification_ids.items()
            if asset_id in HISTORICAL_DATASET_IDENTITY_ASSET_IDS
        }
        identity_source_asset_version_ids = {
            asset_id: value
            for asset_id, value in source_asset_version_ids.items()
            if asset_id in HISTORICAL_DATASET_IDENTITY_ASSET_IDS
        }
        identity_source_asset_batch_ids = {
            asset_id: value
            for asset_id, value in source_asset_batch_ids.items()
            if asset_id in HISTORICAL_DATASET_IDENTITY_ASSET_IDS
        }
        batch_id = _stable_dataset_batch_id(
            DEFAULT_NFL_HISTORICAL_DATASET_ID,
            source_certification_ids=identity_source_certification_ids,
            source_dataset_certification_ids=identity_source_dataset_certification_ids,
            source_asset_version_ids=identity_source_asset_version_ids,
            source_asset_batch_ids=identity_source_asset_batch_ids,
            event_scope=event_scope,
        )
        version_id = _stable_dataset_version_id(DEFAULT_NFL_HISTORICAL_DATASET_ID, batch_id)
        if storage.table_exists(HISTORICAL_DATASET_BATCH_TABLE):
            existing_batch_rows = storage.fetch(
                HISTORICAL_DATASET_BATCH_TABLE,
                where="batch_id = ?",
                params=[batch_id],
                limit=1,
            )
            if existing_batch_rows:
                snapshot = build_historical_dataset_population_dashboard_snapshot(
                    storage_path=storage_path,
                    backend=backend,
                    profile_id=profile_id,
                    dataset_id=DEFAULT_NFL_HISTORICAL_DATASET_ID,
                    batch_id=batch_id,
                )
                snapshot["idempotent_reuse"] = True
                return snapshot

        created_at = _utc_now_iso()
        contract = _base_dataset_contract(Path(storage.path))
        source_name = contract.source_name
        source_type = contract.source_type
        source_key = contract.source_name
        batch_snapshot_id = _stable_id("historical_dataset_batch_snapshot", contract.dataset_id, batch_id)
        batch_lineage_id = _stable_id("historical_dataset_batch_lineage", contract.dataset_id, batch_id)
        batch_source_snapshot_time = max(
            [
                _to_iso(bundle.get("certification_row", {}).get("certified_at"))
                for bundle in source_assets.values()
                if _to_iso(bundle.get("certification_row", {}).get("certified_at"))
            ]
            or [created_at]
        )

        results_by_game: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_assets["dataset.sports.nfl.results"]["rows"]:
            results_by_game[_normalize_text(row.get("game_id"))].append(dict(row))
        odds_by_game: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_assets["dataset.nfl.odds_snapshots"]["rows"]:
            odds_by_game[_normalize_text(row.get("game_id"))].append(dict(row))
        weather_by_game: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_assets["dataset.nfl.weather_snapshots"]["rows"]:
            weather_by_game[_normalize_text(row.get("game_id"))].append(dict(row))
        injuries_by_game_team: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in source_assets["dataset.nfl.injury_snapshots"]["rows"]:
            injuries_by_game_team[
                (
                    _normalize_text(row.get("game_id")),
                    _normalize_text(row.get("team_id")),
                )
            ].append(dict(row))
        team_stats_by_game_team: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in source_assets["dataset.nfl.team_stats_snapshots"]["rows"]:
            team_stats_by_game_team[
                (
                    _normalize_text(row.get("game_id")),
                    _normalize_text(row.get("team_id")),
                )
            ].append(dict(row))

        produced_rows: list[dict[str, Any]] = []
        lineage_edges: list[dict[str, Any]] = []
        build_errors = list(source_errors)
        build_warnings: list[str] = []
        rejected_ids: dict[str, set[str]] = {}
        unmatched_entities: dict[str, set[str]] = {}
        source_selected_unique_ids: dict[str, set[str]] = {
            asset["research_asset_id"]: set() for asset in HISTORICAL_DATASET_REQUIRED_ASSETS
        }
        source_eligible_unique_ids: dict[str, set[str]] = {
            asset["research_asset_id"]: set() for asset in HISTORICAL_DATASET_REQUIRED_ASSETS
        }
        source_attachment_counts: dict[str, int] = {
            asset["research_asset_id"]: 0 for asset in HISTORICAL_DATASET_REQUIRED_ASSETS
        }
        duplicate_row_ids: set[str] = set()
        cardinality_issues: list[str] = []
        expected_market_contexts = 0
        decision_cutoff_by_game: dict[str, str] = {}

        for schedule_row in sorted(
            (dict(row) for row in schedule_rows),
            key=lambda row: _normalize_text(row.get("game_id")),
        ):
            game_id = _normalize_text(schedule_row.get("game_id"))
            kickoff = _parse_iso(schedule_row.get("kickoff_time"))
            if not game_id or kickoff is None:
                build_errors.append(f"missing_schedule_backbone:{game_id or 'unknown'}")
                unmatched_entities.setdefault("schedule", set()).add(game_id or "unknown")
                continue
            decision_cutoff = kickoff - HISTORICAL_DATASET_DECISION_CUTOFF_OFFSET
            decision_cutoff_time = _decision_cutoff_from_kickoff(kickoff)
            decision_cutoff_by_game[game_id] = decision_cutoff_time
            result_rows = list(results_by_game.get(game_id, []))
            if len(result_rows) != 1:
                cardinality_issues.append(f"schedule_to_results:{game_id}:{len(result_rows)}")
                unmatched_entities.setdefault("results", set()).add(game_id)
                continue
            result_row = result_rows[0]
            game_odds_rows = list(odds_by_game.get(game_id, []))
            odds_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
            for odds_row in game_odds_rows:
                key = (
                    _normalize_text(odds_row.get("market_type") or odds_row.get("market")),
                    _normalize_text(odds_row.get("selection")),
                    _normalize_text(odds_row.get("book"), "consensus"),
                )
                odds_groups[key].append(dict(odds_row))
            if not odds_groups:
                unmatched_entities.setdefault("odds", set()).add(game_id)
                continue

            for group_key in sorted(odds_groups):
                expected_market_contexts += 1
                market_rows = odds_groups[group_key]
                eligible_odds_rows: list[dict[str, Any]] = []
                for odds_row in market_rows:
                    row_id = _source_row_identifier("dataset.nfl.odds_snapshots", odds_row)
                    source_eligible_unique_ids["dataset.nfl.odds_snapshots"].add(row_id)
                    row_snapshot = _parse_iso(odds_row.get("snapshot_time"))
                    row_source_snapshot = _parse_iso(odds_row.get("source_snapshot_time"))
                    row_decision = _parse_iso(odds_row.get("decision_time"))
                    malformed = any(
                        odds_row.get(field_name) in (None, "")
                        for field_name in ("decimal_odds", "implied_probability")
                    )
                    if malformed:
                        build_errors.append(f"malformed_odds:{row_id}")
                        _update_rejected_ids(rejected_ids, "malformed_odds_rows", row_id)
                        continue
                    if (
                        row_snapshot is None
                        or row_source_snapshot is None
                        or row_decision is None
                        or row_snapshot > decision_cutoff
                        or row_source_snapshot > decision_cutoff
                        or row_decision > decision_cutoff
                    ):
                        _update_rejected_ids(rejected_ids, "after_cutoff_odds_rows", row_id)
                        continue
                    eligible_odds_rows.append(dict(odds_row))
                if not eligible_odds_rows:
                    unmatched_entities.setdefault("eligible_odds", set()).add(f"{game_id}:{group_key[0]}:{group_key[1]}")
                    continue
                selected_odds = _select_latest_candidate(
                    eligible_odds_rows,
                    row_id_field="odds_snapshot_id",
                    timestamp_fields=("decision_time", "snapshot_time", "source_snapshot_time"),
                )
                selected_odds_time = _asset_availability_time(
                    "dataset.nfl.odds_snapshots",
                    selected_odds,
                )
                if selected_odds_time is None or selected_odds_time > decision_cutoff:
                    _update_rejected_ids(
                        rejected_ids,
                        "after_cutoff_odds_rows",
                        _source_row_identifier("dataset.nfl.odds_snapshots", selected_odds),
                    )
                    continue
                selected_odds_id = _source_row_identifier("dataset.nfl.odds_snapshots", selected_odds)
                source_selected_unique_ids["dataset.nfl.odds_snapshots"].add(selected_odds_id)
                source_attachment_counts["dataset.nfl.odds_snapshots"] += 1

                weather_candidates = list(weather_by_game.get(game_id, []))
                eligible_weather_rows: list[dict[str, Any]] = []
                for weather_row in weather_candidates:
                    row_id = _source_row_identifier("dataset.nfl.weather_snapshots", weather_row)
                    forecast_time = _parse_iso(weather_row.get("forecast_time"))
                    weather_snapshot = _parse_iso(weather_row.get("snapshot_time"))
                    weather_source_snapshot = _parse_iso(weather_row.get("source_snapshot_time"))
                    if (
                        forecast_time is None
                        or weather_snapshot is None
                        or weather_source_snapshot is None
                    ):
                        build_errors.append(f"malformed_weather:{row_id}")
                        _update_rejected_ids(rejected_ids, "malformed_weather_rows", row_id)
                        continue
                    if (
                        forecast_time > decision_cutoff
                        or weather_snapshot > decision_cutoff
                        or weather_source_snapshot > decision_cutoff
                    ):
                        _update_rejected_ids(rejected_ids, "after_cutoff_weather_rows", row_id)
                        continue
                    eligible_weather_rows.append(dict(weather_row))
                    source_eligible_unique_ids["dataset.nfl.weather_snapshots"].add(row_id)
                selected_weather = _select_latest_candidate(
                    eligible_weather_rows,
                    row_id_field="weather_snapshot_id",
                    timestamp_fields=("snapshot_time", "forecast_time", "source_snapshot_time"),
                ) if eligible_weather_rows else {}
                if not selected_weather:
                    unmatched_entities.setdefault("weather", set()).add(game_id)
                    continue
                selected_weather_id = _source_row_identifier("dataset.nfl.weather_snapshots", selected_weather)
                source_selected_unique_ids["dataset.nfl.weather_snapshots"].add(selected_weather_id)
                source_attachment_counts["dataset.nfl.weather_snapshots"] += 1

                team_stats_rows = {}
                missing_team_stats = False
                unsupported_team_stat_unit_rows: list[str] = []
                same_event_team_stat_rows: list[str] = []
                post_cutoff_team_stat_rows: list[str] = []
                rolling_window_leakage_rows: list[str] = []
                for team_side, team_id, opponent_team_id in (
                    ("home", _normalize_text(schedule_row.get("home_team_id")), _normalize_text(schedule_row.get("away_team_id"))),
                    ("away", _normalize_text(schedule_row.get("away_team_id")), _normalize_text(schedule_row.get("home_team_id"))),
                ):
                    candidates = list(team_stats_by_game_team.get((game_id, team_id), []))
                    eligible_candidates: list[dict[str, Any]] = []
                    for team_stats_row in candidates:
                        row_id = _source_row_identifier("dataset.nfl.team_stats_snapshots", team_stats_row)
                        source_eligible_unique_ids["dataset.nfl.team_stats_snapshots"].add(row_id)
                        snapshot_time = _parse_iso(team_stats_row.get("snapshot_time"))
                        source_snapshot_time = _parse_iso(team_stats_row.get("source_snapshot_time"))
                        source_retrieved_at = _parse_iso(team_stats_row.get("source_retrieved_at"))
                        cutoff_time = _parse_iso(team_stats_row.get("team_stats_cutoff_time"))
                        statistic_context = _normalize_text(team_stats_row.get("statistic_context")).lower()
                        measurement_period = _normalize_text(team_stats_row.get("measurement_period")).lower()
                        window_type = _normalize_text(team_stats_row.get("statistic_window_type")).lower()
                        window_excludes_current_event = int(team_stats_row.get("window_excludes_current_event") or 0)
                        if statistic_context in {"live", "in_game", "postgame", "final", "target_event_live", "target_event_final"}:
                            same_event_team_stat_rows.append(row_id)
                            continue
                        if measurement_period not in {
                            "rolling_prior_games",
                            "season_to_date_excluding_current_event",
                            "prior_game_realized",
                        }:
                            rolling_window_leakage_rows.append(row_id)
                            continue
                        if window_type not in {
                            "rolling_prior_games_excluding_current_event",
                            "season_to_date_excluding_current_event",
                            "prior_game_only",
                        } or window_excludes_current_event != 1:
                            rolling_window_leakage_rows.append(row_id)
                            continue
                        if (
                            snapshot_time is None
                            or source_snapshot_time is None
                            or source_retrieved_at is None
                            or cutoff_time is None
                            or snapshot_time > decision_cutoff
                            or source_snapshot_time > decision_cutoff
                            or source_retrieved_at > decision_cutoff
                            or cutoff_time > decision_cutoff
                            or cutoff_time > kickoff
                        ):
                            post_cutoff_team_stat_rows.append(row_id)
                            continue
                        if _normalize_text(team_stats_row.get("opponent_team_id")) != opponent_team_id:
                            build_errors.append(f"team_stats_opponent_mismatch:{row_id}")
                            continue
                        if not _expected_team_stat_units(team_stats_row):
                            unsupported_team_stat_unit_rows.append(row_id)
                            continue
                        eligible_candidates.append(dict(team_stats_row))
                    if not eligible_candidates:
                        unmatched_entities.setdefault("team_stats", set()).add(f"{game_id}:{team_side}")
                        missing_team_stats = True
                        continue
                    selected_team_stats = _select_latest_candidate(
                        eligible_candidates,
                        row_id_field="team_stats_snapshot_id",
                        timestamp_fields=("snapshot_time", "team_stats_cutoff_time", "source_retrieved_at"),
                    )
                    team_stats_rows[team_side] = selected_team_stats
                for row_id in same_event_team_stat_rows:
                    _update_rejected_ids(rejected_ids, "same_event_team_stats_rows", row_id)
                for row_id in post_cutoff_team_stat_rows:
                    _update_rejected_ids(rejected_ids, "post_cutoff_team_stats_rows", row_id)
                for row_id in rolling_window_leakage_rows:
                    _update_rejected_ids(rejected_ids, "rolling_window_leakage_rows", row_id)
                for row_id in unsupported_team_stat_unit_rows:
                    _update_rejected_ids(rejected_ids, "unsupported_team_stat_unit_rows", row_id)
                if missing_team_stats:
                    continue
                for team_side, selected_team_stats in team_stats_rows.items():
                    selected_team_stats_id = _source_row_identifier("dataset.nfl.team_stats_snapshots", selected_team_stats)
                    source_selected_unique_ids["dataset.nfl.team_stats_snapshots"].add(selected_team_stats_id)
                    source_attachment_counts["dataset.nfl.team_stats_snapshots"] += 1

                injury_groups = {}
                for team_side, team_id in (
                    ("home", _normalize_text(schedule_row.get("home_team_id"))),
                    ("away", _normalize_text(schedule_row.get("away_team_id"))),
                ):
                    candidates = list(injuries_by_game_team.get((game_id, team_id), []))
                    eligible_candidates: list[dict[str, Any]] = []
                    for injury_row in candidates:
                        row_id = _source_row_identifier("dataset.nfl.injury_snapshots", injury_row)
                        report_time = _parse_iso(injury_row.get("report_time"))
                        snapshot_time = _parse_iso(injury_row.get("snapshot_time"))
                        source_snapshot_time = _parse_iso(injury_row.get("source_snapshot_time"))
                        if (
                            report_time is None
                            or snapshot_time is None
                            or source_snapshot_time is None
                        ):
                            build_errors.append(f"malformed_injury:{row_id}")
                            _update_rejected_ids(rejected_ids, "malformed_injury_rows", row_id)
                            continue
                        if (
                            report_time > decision_cutoff
                            or snapshot_time > decision_cutoff
                            or source_snapshot_time > decision_cutoff
                        ):
                            _update_rejected_ids(rejected_ids, "post_cutoff_injury_rows", row_id)
                            continue
                        source_eligible_unique_ids["dataset.nfl.injury_snapshots"].add(row_id)
                        eligible_candidates.append(dict(injury_row))
                    ordered = sorted(
                        eligible_candidates,
                        key=lambda row: _candidate_sort_key(
                            row,
                            row_id_field="injury_snapshot_id",
                            timestamp_fields=("report_time", "snapshot_time", "source_snapshot_time"),
                        ),
                    )
                    injury_groups[team_side] = ordered
                    for injury_row in ordered:
                        selected_id = _source_row_identifier("dataset.nfl.injury_snapshots", injury_row)
                        source_selected_unique_ids["dataset.nfl.injury_snapshots"].add(selected_id)
                        source_attachment_counts["dataset.nfl.injury_snapshots"] += 1

                target_context = _target_team_context(schedule_row, selected_odds)
                source_alignment_ids: dict[str, list[str]] = {}
                source_certification_mapping = {
                    asset_id: source_certification_ids.get(asset_id, "")
                    for asset_id in source_assets
                }
                source_dataset_certification_mapping = {
                    asset_id: source_dataset_certification_ids.get(asset_id, "")
                    for asset_id in source_assets
                }

                source_references = {
                    "schedule": _serialize_source_reference(
                        research_asset_id="dataset.sports.nfl.schedule",
                        source_row=schedule_row,
                        certification_row=source_assets["dataset.sports.nfl.schedule"]["certification_row"],
                        dataset_certification_row=source_assets["dataset.sports.nfl.schedule"]["dataset_certification_row"],
                        alignment_ids=_matching_alignment_ids(
                            "dataset.sports.nfl.schedule",
                            alignment_rows=source_assets["dataset.sports.nfl.schedule"]["alignment_rows"],
                            source_row=schedule_row,
                        ),
                    ),
                    "results": _serialize_source_reference(
                        research_asset_id="dataset.sports.nfl.results",
                        source_row=result_row,
                        certification_row=source_assets["dataset.sports.nfl.results"]["certification_row"],
                        dataset_certification_row=source_assets["dataset.sports.nfl.results"]["dataset_certification_row"],
                        alignment_ids=_matching_alignment_ids(
                            "dataset.sports.nfl.results",
                            alignment_rows=source_assets["dataset.sports.nfl.results"]["alignment_rows"],
                            source_row=result_row,
                        ),
                    ),
                    "odds": _serialize_source_reference(
                        research_asset_id="dataset.nfl.odds_snapshots",
                        source_row=selected_odds,
                        certification_row=source_assets["dataset.nfl.odds_snapshots"]["certification_row"],
                        dataset_certification_row=source_assets["dataset.nfl.odds_snapshots"]["dataset_certification_row"],
                        alignment_ids=_matching_alignment_ids(
                            "dataset.nfl.odds_snapshots",
                            alignment_rows=source_assets["dataset.nfl.odds_snapshots"]["alignment_rows"],
                            source_row=selected_odds,
                        ),
                    ),
                    "weather": _serialize_source_reference(
                        research_asset_id="dataset.nfl.weather_snapshots",
                        source_row=selected_weather,
                        certification_row=source_assets["dataset.nfl.weather_snapshots"]["certification_row"],
                        dataset_certification_row=source_assets["dataset.nfl.weather_snapshots"]["dataset_certification_row"],
                        alignment_ids=_matching_alignment_ids(
                            "dataset.nfl.weather_snapshots",
                            alignment_rows=source_assets["dataset.nfl.weather_snapshots"]["alignment_rows"],
                            source_row=selected_weather,
                        ),
                    ),
                    "team_stats": {
                        "home": _serialize_source_reference(
                            research_asset_id="dataset.nfl.team_stats_snapshots",
                            source_row=team_stats_rows["home"],
                            certification_row=source_assets["dataset.nfl.team_stats_snapshots"]["certification_row"],
                            dataset_certification_row=source_assets["dataset.nfl.team_stats_snapshots"]["dataset_certification_row"],
                            alignment_ids=_matching_alignment_ids(
                                "dataset.nfl.team_stats_snapshots",
                                alignment_rows=source_assets["dataset.nfl.team_stats_snapshots"]["alignment_rows"],
                                source_row=team_stats_rows["home"],
                            ),
                        ),
                        "away": _serialize_source_reference(
                            research_asset_id="dataset.nfl.team_stats_snapshots",
                            source_row=team_stats_rows["away"],
                            certification_row=source_assets["dataset.nfl.team_stats_snapshots"]["certification_row"],
                            dataset_certification_row=source_assets["dataset.nfl.team_stats_snapshots"]["dataset_certification_row"],
                            alignment_ids=_matching_alignment_ids(
                                "dataset.nfl.team_stats_snapshots",
                                alignment_rows=source_assets["dataset.nfl.team_stats_snapshots"]["alignment_rows"],
                                source_row=team_stats_rows["away"],
                            ),
                        ),
                    },
                    "injuries": {
                        "home": [
                            _serialize_source_reference(
                                research_asset_id="dataset.nfl.injury_snapshots",
                                source_row=injury_row,
                                certification_row=source_assets["dataset.nfl.injury_snapshots"]["certification_row"],
                                dataset_certification_row=source_assets["dataset.nfl.injury_snapshots"]["dataset_certification_row"],
                                alignment_ids=_matching_alignment_ids(
                                    "dataset.nfl.injury_snapshots",
                                    alignment_rows=source_assets["dataset.nfl.injury_snapshots"]["alignment_rows"],
                                    source_row=injury_row,
                                ),
                            )
                            for injury_row in injury_groups["home"]
                        ],
                        "away": [
                            _serialize_source_reference(
                                research_asset_id="dataset.nfl.injury_snapshots",
                                source_row=injury_row,
                                certification_row=source_assets["dataset.nfl.injury_snapshots"]["certification_row"],
                                dataset_certification_row=source_assets["dataset.nfl.injury_snapshots"]["dataset_certification_row"],
                                alignment_ids=_matching_alignment_ids(
                                    "dataset.nfl.injury_snapshots",
                                    alignment_rows=source_assets["dataset.nfl.injury_snapshots"]["alignment_rows"],
                                    source_row=injury_row,
                                ),
                            )
                            for injury_row in injury_groups["away"]
                        ],
                    },
                }
                missing_alignment_ids = []
                for reference in (
                    source_references["schedule"],
                    source_references["results"],
                    source_references["odds"],
                    source_references["weather"],
                    source_references["team_stats"]["home"],
                    source_references["team_stats"]["away"],
                ):
                    if not reference.get("alignment_certification_ids"):
                        missing_alignment_ids.append(reference.get("source_row_id"))
                for injury_reference in source_references["injuries"]["home"] + source_references["injuries"]["away"]:
                    if not injury_reference.get("alignment_certification_ids"):
                        missing_alignment_ids.append(injury_reference.get("source_row_id"))
                if missing_alignment_ids:
                    for row_id in missing_alignment_ids:
                        _update_rejected_ids(rejected_ids, "missing_alignment_rows", _normalize_text(row_id))
                    continue

                source_rows_for_provenance = [
                    schedule_row,
                    result_row,
                    selected_odds,
                    selected_weather,
                    team_stats_rows["home"],
                    team_stats_rows["away"],
                    *injury_groups["home"],
                    *injury_groups["away"],
                ]
                if not all(_source_row_has_provenance(row) for row in source_rows_for_provenance):
                    for source_row in source_rows_for_provenance:
                        row_id = (
                            _normalize_text(source_row.get("schedule_id"))
                            or _normalize_text(source_row.get("result_id"))
                            or _normalize_text(source_row.get("odds_snapshot_id"))
                            or _normalize_text(source_row.get("weather_snapshot_id"))
                            or _normalize_text(source_row.get("team_stats_snapshot_id"))
                            or _normalize_text(source_row.get("injury_snapshot_id"))
                        )
                        _update_rejected_ids(rejected_ids, "missing_provenance_rows", row_id)
                    continue

                decision_context_id = _stable_id(
                    "historical_dataset_decision_context",
                    contract.dataset_id,
                    game_id,
                    _normalize_text(selected_odds.get("market_type"), _normalize_text(selected_odds.get("market"))),
                    _normalize_text(selected_odds.get("selection")),
                    _normalize_text(selected_odds.get("book"), "consensus"),
                    decision_cutoff_time,
                )
                dataset_row_id = _stable_id(
                    "historical_dataset_row",
                    contract.dataset_id,
                    game_id,
                    _normalize_text(selected_odds.get("market_type"), _normalize_text(selected_odds.get("market"))),
                    _normalize_text(selected_odds.get("selection")),
                    _normalize_text(selected_odds.get("book"), "consensus"),
                    decision_cutoff_time,
                )
                if dataset_row_id in {row["dataset_row_id"] for row in produced_rows}:
                    duplicate_row_ids.add(dataset_row_id)
                    continue
                evidence_package_id = _stable_id(
                    "historical_dataset_row_evidence",
                    contract.dataset_id,
                    batch_id,
                    dataset_row_id,
                )
                predictor_references = {
                    "decision_cutoff_time": decision_cutoff_time,
                    "cutoff_policy_version": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
                    "schedule": source_references["schedule"],
                    "odds": source_references["odds"],
                    "weather": source_references["weather"],
                    "team_stats": source_references["team_stats"],
                    "injuries": {
                        "home": {
                            "summary": _injury_summary(injury_groups["home"]),
                            "references": source_references["injuries"]["home"],
                        },
                        "away": {
                            "summary": _injury_summary(injury_groups["away"]),
                            "references": source_references["injuries"]["away"],
                        },
                    },
                }
                selected_odds_timestamp = _selected_asset_timestamp(
                    "dataset.nfl.odds_snapshots",
                    selected_odds,
                )
                selected_weather_timestamp = _selected_asset_timestamp(
                    "dataset.nfl.weather_snapshots",
                    selected_weather,
                )
                selected_home_injury_timestamp = _selected_asset_timestamp(
                    "dataset.nfl.injury_snapshots",
                    injury_groups["home"][-1],
                ) if injury_groups["home"] else ""
                selected_away_injury_timestamp = _selected_asset_timestamp(
                    "dataset.nfl.injury_snapshots",
                    injury_groups["away"][-1],
                ) if injury_groups["away"] else ""
                selected_home_team_stats_timestamp = _selected_asset_timestamp(
                    "dataset.nfl.team_stats_snapshots",
                    team_stats_rows["home"],
                )
                selected_away_team_stats_timestamp = _selected_asset_timestamp(
                    "dataset.nfl.team_stats_snapshots",
                    team_stats_rows["away"],
                )
                selected_source_row_ids = {
                    "schedule": _normalize_text(schedule_row.get("schedule_id")),
                    "results": _normalize_text(result_row.get("result_id")),
                    "odds": selected_odds_id,
                    "weather": selected_weather_id,
                    "team_stats": {
                        "home": _source_row_identifier("dataset.nfl.team_stats_snapshots", team_stats_rows["home"]),
                        "away": _source_row_identifier("dataset.nfl.team_stats_snapshots", team_stats_rows["away"]),
                    },
                    "injuries": {
                        "home": [_source_row_identifier("dataset.nfl.injury_snapshots", row) for row in injury_groups["home"]],
                        "away": [_source_row_identifier("dataset.nfl.injury_snapshots", row) for row in injury_groups["away"]],
                    },
                }
                source_lineage_ids = {
                    "schedule": _normalize_text(schedule_row.get("lineage_id")),
                    "results": _normalize_text(result_row.get("lineage_id")),
                    "odds": _normalize_text(selected_odds.get("lineage_id")),
                    "weather": _normalize_text(selected_weather.get("lineage_id")),
                    "team_stats": {
                        "home": _normalize_text(team_stats_rows["home"].get("lineage_id")),
                        "away": _normalize_text(team_stats_rows["away"].get("lineage_id")),
                    },
                    "injuries": {
                        "home": [_normalize_text(row.get("lineage_id")) for row in injury_groups["home"]],
                        "away": [_normalize_text(row.get("lineage_id")) for row in injury_groups["away"]],
                    },
                }
                asset_freshness = {
                    "odds": _freshness_seconds(
                        decision_cutoff,
                        "dataset.nfl.odds_snapshots",
                        selected_odds,
                    ),
                    "weather": _freshness_seconds(
                        decision_cutoff,
                        "dataset.nfl.weather_snapshots",
                        selected_weather,
                    ),
                    "home_injuries": _freshness_seconds(
                        decision_cutoff,
                        "dataset.nfl.injury_snapshots",
                        injury_groups["home"][-1],
                    ) if injury_groups["home"] else -1,
                    "away_injuries": _freshness_seconds(
                        decision_cutoff,
                        "dataset.nfl.injury_snapshots",
                        injury_groups["away"][-1],
                    ) if injury_groups["away"] else -1,
                    "home_team_stats": _freshness_seconds(
                        decision_cutoff,
                        "dataset.nfl.team_stats_snapshots",
                        team_stats_rows["home"],
                    ),
                    "away_team_stats": _freshness_seconds(
                        decision_cutoff,
                        "dataset.nfl.team_stats_snapshots",
                        team_stats_rows["away"],
                    ),
                }
                row_source_snapshot_time = max(
                    [
                        _to_iso(row.get("source_snapshot_time"))
                        for row in (
                            schedule_row,
                            selected_odds,
                            selected_weather,
                            team_stats_rows["home"],
                            team_stats_rows["away"],
                            *injury_groups["home"],
                            *injury_groups["away"],
                        )
                        if _to_iso(row.get("source_snapshot_time"))
                    ]
                    or [selected_odds.get("source_snapshot_time") or selected_odds.get("snapshot_time") or created_at]
                )
                row = _historical_row_base(
                    profile=profile,
                    stage_name=HISTORICAL_DATASET_POPULATION_STAGE_NAME,
                    row_id=dataset_row_id,
                    batch_id=batch_id,
                    dataset_version=version_id,
                    source_name=source_name,
                    source_type=source_type,
                    source_key=source_key,
                    source_snapshot_time=row_source_snapshot_time,
                    snapshot_time=_to_iso(selected_odds.get("snapshot_time")),
                    decision_time=decision_cutoff_time,
                    certified_at=created_at,
                    status="certified",
                    point_in_time_status="safe",
                    leakage_status="none",
                    completeness_score=1.0,
                    quality_score=1.0,
                    context={
                        "dataset_id": contract.dataset_id,
                        "evidence_package_id": evidence_package_id,
                    },
                    payload={
                        "dataset_id": contract.dataset_id,
                        "dataset_name": contract.dataset_name,
                    },
                    market_type=_normalize_text(selected_odds.get("market_type"), _normalize_text(selected_odds.get("market"))),
                    market_profile=profile.profile_id,
                    asset_class=profile.profile_family,
                )
                row.update(
                    {
                        "dataset_id": contract.dataset_id,
                        "dataset_name": contract.dataset_name,
                        "dataset_row_id": dataset_row_id,
                        "decision_context_id": decision_context_id,
                        "schedule_id": _normalize_text(schedule_row.get("schedule_id")),
                        "result_id": _normalize_text(result_row.get("result_id")),
                        "odds_snapshot_id": selected_odds_id,
                        "weather_snapshot_id": selected_weather_id,
                        "home_team_stats_snapshot_id": _source_row_identifier("dataset.nfl.team_stats_snapshots", team_stats_rows["home"]),
                        "away_team_stats_snapshot_id": _source_row_identifier("dataset.nfl.team_stats_snapshots", team_stats_rows["away"]),
                        "event_id": game_id,
                        "game_id": game_id,
                        "season": int(schedule_row.get("season") or 0),
                        "season_type": _normalize_text(schedule_row.get("season_type")),
                        "week": int(schedule_row.get("week") or 0),
                        "scheduled_kickoff_time": _to_iso(schedule_row.get("kickoff_time")),
                        "event_start_time": _to_iso(schedule_row.get("kickoff_time")),
                        "decision_cutoff_time": decision_cutoff_time,
                        "cutoff_policy_version": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
                        "home_team_id": _normalize_text(schedule_row.get("home_team_id")),
                        "home_team": _normalize_text(schedule_row.get("home_team")),
                        "away_team_id": _normalize_text(schedule_row.get("away_team_id")),
                        "away_team": _normalize_text(schedule_row.get("away_team")),
                        "neutral_site": int(schedule_row.get("neutral_site") or 0),
                        "target_team_id": target_context["target_team_id"],
                        "target_team": target_context["target_team"],
                        "opponent_team_id": target_context["opponent_team_id"],
                        "opponent_team": target_context["opponent_team"],
                        "team_side": target_context["team_side"],
                        "book": _normalize_text(selected_odds.get("book"), "consensus"),
                        "market_name": _normalize_text(selected_odds.get("market")),
                        "market_type": _normalize_text(selected_odds.get("market_type"), _normalize_text(selected_odds.get("market"))),
                        "selection": _normalize_text(selected_odds.get("selection")),
                        "line_value": selected_odds.get("line_value"),
                        "american_odds": selected_odds.get("american_odds"),
                        "decimal_odds": selected_odds.get("decimal_odds"),
                        "implied_probability": selected_odds.get("implied_probability"),
                        "market_label": _normalize_text(selected_odds.get("market_label")),
                        "price_type": "decision_time_snapshot",
                        "selected_odds_timestamp": selected_odds_timestamp,
                        "weather_forecast_time": _to_iso(selected_weather.get("forecast_time")),
                        "selected_weather_timestamp": selected_weather_timestamp,
                        "selected_home_injury_timestamp": selected_home_injury_timestamp,
                        "selected_away_injury_timestamp": selected_away_injury_timestamp,
                        "selected_home_team_stats_timestamp": selected_home_team_stats_timestamp,
                        "selected_away_team_stats_timestamp": selected_away_team_stats_timestamp,
                        "odds_freshness_seconds": asset_freshness["odds"],
                        "weather_freshness_seconds": asset_freshness["weather"],
                        "home_injury_freshness_seconds": asset_freshness["home_injuries"],
                        "away_injury_freshness_seconds": asset_freshness["away_injuries"],
                        "home_team_stats_freshness_seconds": asset_freshness["home_team_stats"],
                        "away_team_stats_freshness_seconds": asset_freshness["away_team_stats"],
                        "home_injury_record_count": len(injury_groups["home"]),
                        "away_injury_record_count": len(injury_groups["away"]),
                        "home_injury_row_ids_json": _as_json(
                            [_source_row_identifier("dataset.nfl.injury_snapshots", row) for row in injury_groups["home"]]
                        ),
                        "away_injury_row_ids_json": _as_json(
                            [_source_row_identifier("dataset.nfl.injury_snapshots", row) for row in injury_groups["away"]]
                        ),
                        "selected_source_row_ids_json": _as_json(selected_source_row_ids),
                        "source_lineage_ids_json": _as_json(source_lineage_ids),
                        "asset_freshness_json": _as_json(asset_freshness),
                        "missing_required_assets_json": _as_json([]),
                        "source_certification_ids_json": _as_json(source_certification_mapping),
                        "source_dataset_certification_ids_json": _as_json(source_dataset_certification_mapping),
                        "source_alignment_certification_ids_json": _as_json(
                            {
                                "schedule": source_references["schedule"]["alignment_certification_ids"],
                                "results": source_references["results"]["alignment_certification_ids"],
                                "odds": source_references["odds"]["alignment_certification_ids"],
                                "weather": source_references["weather"]["alignment_certification_ids"],
                                "team_stats": {
                                    "home": source_references["team_stats"]["home"]["alignment_certification_ids"],
                                    "away": source_references["team_stats"]["away"]["alignment_certification_ids"],
                                },
                                "injuries": {
                                    "home": [
                                        reference["alignment_certification_ids"]
                                        for reference in source_references["injuries"]["home"]
                                    ],
                                    "away": [
                                        reference["alignment_certification_ids"]
                                        for reference in source_references["injuries"]["away"]
                                    ],
                                },
                            }
                        ),
                        "predictor_references_json": _as_json(predictor_references),
                        "label_final_result": _derive_final_result_label(schedule_row, result_row),
                        "label_final_score_home": int(result_row.get("final_score_home") or 0),
                        "label_final_score_away": int(result_row.get("final_score_away") or 0),
                        "label_winner_team_id": _normalize_text(result_row.get("winner_team_id")),
                        "label_winner_team": _normalize_text(result_row.get("winner_team")),
                        "label_margin": int(result_row.get("margin") or 0),
                        "label_total_points": int(result_row.get("total_points") or 0),
                        "label_settlement_status": _normalize_text(result_row.get("settlement_status"), "settled"),
                        "label_result_recorded_time": _to_iso(result_row.get("final_scored_at")),
                        "predictor_outcome_separation_status": "separated",
                        "evidence_package_id": evidence_package_id,
                        "evidence_package_json": _as_json(
                            {
                                "dataset_row_id": dataset_row_id,
                                "batch_id": batch_id,
                                "scheduled_kickoff_time": _to_iso(schedule_row.get("kickoff_time")),
                                "decision_cutoff_time": decision_cutoff_time,
                                "cutoff_policy_version": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
                                "selected_timestamps": {
                                    "odds": selected_odds_timestamp,
                                    "weather": selected_weather_timestamp,
                                    "home_injuries": selected_home_injury_timestamp,
                                    "away_injuries": selected_away_injury_timestamp,
                                    "home_team_stats": selected_home_team_stats_timestamp,
                                    "away_team_stats": selected_away_team_stats_timestamp,
                                },
                                "asset_freshness": asset_freshness,
                                "predictor_references": predictor_references,
                                "outcome_reference": {
                                    "result_id": _normalize_text(result_row.get("result_id")),
                                    "winner_team_id": _normalize_text(result_row.get("winner_team_id")),
                                    "result_recorded_time": _to_iso(result_row.get("final_scored_at")),
                                },
                            }
                        ),
                        "decision_readiness_status": "ready",
                        "readiness_state": "feature_ready",
                        "unresolved_blockers_json": _as_json([]),
                        "schema_version": HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
                        "source_metadata_json": _as_json(
                            {
                                "source_name": source_name,
                                "source_type": source_type,
                                "source_key": source_key,
                                "batch_id": batch_id,
                                "version_id": version_id,
                            }
                        ),
                    }
                )
                produced_rows.append(row)

                lineage_payloads = [
                    ("dataset.sports.nfl.schedule", schedule_row, source_references["schedule"]),
                    ("dataset.sports.nfl.results", result_row, source_references["results"]),
                    ("dataset.nfl.odds_snapshots", selected_odds, source_references["odds"]),
                    ("dataset.nfl.weather_snapshots", selected_weather, source_references["weather"]),
                    ("dataset.nfl.team_stats_snapshots", team_stats_rows["home"], source_references["team_stats"]["home"]),
                    ("dataset.nfl.team_stats_snapshots", team_stats_rows["away"], source_references["team_stats"]["away"]),
                ]
                for injury_reference, injury_row in zip(source_references["injuries"]["home"], injury_groups["home"], strict=False):
                    lineage_payloads.append(("dataset.nfl.injury_snapshots", injury_row, injury_reference))
                for injury_reference, injury_row in zip(source_references["injuries"]["away"], injury_groups["away"], strict=False):
                    lineage_payloads.append(("dataset.nfl.injury_snapshots", injury_row, injury_reference))

                for step_index, (asset_id, source_row, reference) in enumerate(lineage_payloads):
                    lineage_record = create_lineage_record(
                        provider_id=contract.provider,
                        provider_type=contract.asset_class,
                        payload_schema_version=HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
                        snapshot_id=batch_snapshot_id,
                        source_type=contract.source_type,
                        schema_version=HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
                        lineage_id=batch_lineage_id,
                        dataset_id=contract.dataset_id,
                        dataset_name=contract.dataset_name,
                        source_record_id=_source_row_identifier(asset_id, source_row),
                        target_record_id=dataset_row_id,
                        source_stage=asset_id,
                        target_stage="historical_dataset_row",
                        transformation="attach_source_row_to_dataset_context",
                    )
                    lineage_edges.append(
                        _lineage_edge_row(
                            contract,
                            version_id=version_id,
                            snapshot_id=batch_snapshot_id,
                            batch_lineage_id=batch_lineage_id,
                            source_stage=asset_id,
                            source_id=_source_row_identifier(asset_id, source_row),
                            target_id=dataset_row_id,
                            step_index=len(lineage_edges) + step_index,
                            payload={
                                "reference": reference,
                                "lineage_record": lineage_record,
                                "batch_id": batch_id,
                                "dataset_row_id": dataset_row_id,
                            },
                            created_at=created_at,
                        )
                    )

        predictor_outcome_issues = []
        for row in produced_rows:
            for field_name in row:
                if field_name.startswith("label_"):
                    continue
                if field_name in {"result_id"}:
                    continue
                if any(token in field_name for token in ("winner", "final_score", "settlement_status", "result_recorded_time", "total_points", "margin")):
                    predictor_outcome_issues.append(f"{row['dataset_row_id']}:{field_name}")
        lineage_complete = bool(produced_rows) and len(lineage_edges) == sum(
            6 + len(_load_json_list(row.get("home_injury_row_ids_json"))) + len(_load_json_list(row.get("away_injury_row_ids_json")))
            for row in produced_rows
        )
        provenance_complete = not rejected_ids.get("missing_provenance_rows")
        duplicate_lineage_ids = []
        seen_lineage_edge_ids: set[str] = set()
        for edge in lineage_edges:
            edge_id = _normalize_text(edge.get("lineage_edge_id"))
            if edge_id in seen_lineage_edge_ids and edge_id not in duplicate_lineage_ids:
                duplicate_lineage_ids.append(edge_id)
            seen_lineage_edge_ids.add(edge_id)
        if duplicate_lineage_ids:
            lineage_complete = False
        validation_errors = list(dict.fromkeys([
            *build_errors,
            *[f"cardinality:{issue}" for issue in cardinality_issues],
            *[f"duplicate_dataset_row:{row_id}" for row_id in sorted(duplicate_row_ids)],
            *[f"predictor_outcome_separation:{issue}" for issue in predictor_outcome_issues],
            *[
                f"unmatched_entities:{name}:{','.join(sorted(values))}"
                for name, values in sorted(unmatched_entities.items())
                if values
            ],
            *([f"missing_lineage:{edge_id}" for edge_id in duplicate_lineage_ids] if duplicate_lineage_ids else []),
            *([f"incomplete_lineage:expected_dataset_edges" ] if produced_rows and not lineage_complete else []),
            *(["incomplete_provenance:source_rows"] if not provenance_complete else []),
        ]))
        validation = {
            "ok": bool(
                produced_rows
                and not validation_errors
                and expected_market_contexts == len(produced_rows)
                and not unmatched_entities
                and lineage_complete
                and provenance_complete
            ),
            "status": "validated" if produced_rows and not validation_errors and expected_market_contexts == len(produced_rows) and not unmatched_entities and lineage_complete and provenance_complete else "rejected",
            "row_count": expected_market_contexts,
            "dataset_row_count": len(produced_rows),
            "valid_row_count": len(produced_rows),
            "invalid_row_count": max(expected_market_contexts - len(produced_rows), 0),
            "error_count": len(validation_errors),
            "warning_count": len(build_warnings),
            "missing_fields": [],
            "duplicate_keys": sorted(duplicate_row_ids),
            "join_keys": ["game_id", "market_type", "selection", "decision_time"],
            "errors": validation_errors,
            "warnings": build_warnings,
            "point_in_time_issues": sorted(
                rejected_ids.get("after_cutoff_odds_rows", set())
                | rejected_ids.get("after_cutoff_weather_rows", set())
                | rejected_ids.get("post_cutoff_injury_rows", set())
                | rejected_ids.get("post_cutoff_team_stats_rows", set())
                | rejected_ids.get("same_event_team_stats_rows", set())
                | rejected_ids.get("rolling_window_leakage_rows", set())
            ),
            "cardinality_issues": cardinality_issues,
            "lineage_issues": duplicate_lineage_ids,
            "provenance_issues": sorted(rejected_ids.get("missing_provenance_rows", set())),
            "rejected_evidence": {name: sorted(values) for name, values in rejected_ids.items()},
            "unmatched_entities": {name: sorted(values) for name, values in unmatched_entities.items()},
        }
        evidence_package_id = _stable_id(
            "historical_dataset_batch_evidence",
            contract.dataset_id,
            batch_id,
        )
        join_diagnostics = {
            "source_row_counts": {
                asset_id: len(bundle.get("rows", []))
                for asset_id, bundle in source_assets.items()
            },
            "eligible_record_counts": {
                asset_id: len(source_eligible_unique_ids.get(asset_id, set()))
                for asset_id in source_assets
            },
            "selected_unique_record_counts": {
                asset_id: len(source_selected_unique_ids.get(asset_id, set()))
                for asset_id in source_assets
            },
            "selected_attachment_counts": dict(source_attachment_counts),
            "final_dataset_row_count": len(produced_rows),
            "expected_market_context_count": expected_market_contexts,
            "decision_cutoff_time_by_game": dict(decision_cutoff_by_game),
            "rejected_record_count": sum(len(values) for values in rejected_ids.values()),
            "unmatched_record_count": sum(len(values) for values in unmatched_entities.values()),
            "duplicate_dataset_row_count": len(duplicate_row_ids),
            "duplicate_lineage_edge_count": len(duplicate_lineage_ids),
            "cardinality_contracts": {
                "schedule_to_results": {
                    "expected": "1:1",
                    "violations": [issue for issue in cardinality_issues if issue.startswith("schedule_to_results:")],
                },
                "schedule_to_odds_context": {
                    "expected": "1:N with one selected context row per market/selection/book group",
                    "observed_context_count": expected_market_contexts,
                },
                "event_to_weather": {
                    "expected": "1:1 selected forecast row at or before the decision cutoff",
                    "violations": sorted(unmatched_entities.get("weather", set())),
                },
                "event_team_to_team_stats": {
                    "expected": "1:1 selected team-stat row per game/team",
                    "violations": sorted(unmatched_entities.get("team_stats", set())),
                },
                "event_team_to_injuries": {
                    "expected": "0:N aggregated without row multiplication",
                    "selected_attachment_count": source_attachment_counts.get("dataset.nfl.injury_snapshots", 0),
                },
            },
        }
        evidence_package = {
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "batch_id": batch_id,
            "version_id": version_id,
            "dataset_schema_version": HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
            "dataset_contract_version": HISTORICAL_DATASET_CONTRACT_VERSION,
            "source_asset_ids": list(source_assets),
            "source_asset_batch_ids": source_asset_batch_ids,
            "source_asset_version_ids": source_asset_version_ids,
            "source_certification_ids": source_certification_ids,
            "source_dataset_certification_ids": source_dataset_certification_ids,
            "source_lifecycle_states": {
                asset_id: _normalize_text(bundle.get("lifecycle_row", {}).get("lifecycle_state"))
                for asset_id, bundle in source_assets.items()
            },
            "join_diagnostics": join_diagnostics,
            "validation": validation,
            "rejected_record_summary": {name: len(values) for name, values in rejected_ids.items()},
            "unmatched_record_summary": {name: len(values) for name, values in unmatched_entities.items()},
            "cutoff_policy_id": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
            "selection_policy": {
                "odds": "latest certified and aligned odds snapshot by market_type/selection/book with availability at or before scheduled kickoff minus five minutes",
                "weather": "latest certified and aligned forecast snapshot with availability at or before scheduled kickoff minus five minutes",
                "injuries": "all certified and aligned injury rows with availability at or before scheduled kickoff minus five minutes, aggregated by team without row multiplication",
                "team_stats": "latest certified and aligned pregame team-stat row per game/team excluding the target event and available at or before scheduled kickoff minus five minutes",
            },
            "lineage_summary": {
                "edge_count": len(lineage_edges),
                "dataset_row_count": len(produced_rows),
            },
            "final_row_count": len(produced_rows),
            "readiness_result": "feature_ready" if validation["ok"] else "blocked",
        }

        certification_row = _build_dataset_population_certification_row(
            profile=profile,
            batch_id=batch_id,
            version_id=version_id,
            created_at=created_at,
            validation=validation,
            evidence_package_id=evidence_package_id,
            source_name=source_name,
            source_type=source_type,
            source_key=source_key,
        )

        batch_row = _historical_row_base(
            profile=profile,
            stage_name=HISTORICAL_DATASET_POPULATION_STAGE_NAME,
            row_id=batch_id,
            batch_id=batch_id,
            dataset_version=version_id,
            source_name=source_name,
            source_type=source_type,
            source_key=source_key,
            source_snapshot_time=batch_source_snapshot_time,
            snapshot_time=batch_source_snapshot_time,
            decision_time=batch_source_snapshot_time,
            certified_at=created_at,
            status="certified" if validation["ok"] else "rejected",
            point_in_time_status="safe" if validation["ok"] else "blocked",
            leakage_status="none" if validation["ok"] else "suspect",
            completeness_score=round(len(produced_rows) / max(expected_market_contexts, 1), 4),
            quality_score=1.0 if validation["ok"] else 0.0,
            context={
                "dataset_id": contract.dataset_id,
                "evidence_package_id": evidence_package_id,
            },
            payload={
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
            },
            market_type=contract.market_type,
            market_profile=profile.profile_id,
            asset_class=profile.profile_family,
        )
        batch_row.update(
            {
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
                "dataset_contract_version": HISTORICAL_DATASET_CONTRACT_VERSION,
                "population_version": HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
                "dataset_as_of_time": batch_source_snapshot_time,
                "cutoff_policy_id": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
                "cutoff_policy_version": HISTORICAL_DATASET_CUTOFF_POLICY_ID,
                "join_policy_id": HISTORICAL_DATASET_JOIN_POLICY_ID,
                "event_scope_json": _as_json(event_scope),
                "required_source_asset_ids_json": _as_json(list(source_assets)),
                "source_asset_version_ids_json": _as_json(source_asset_version_ids),
                "source_asset_batch_ids_json": _as_json(source_asset_batch_ids),
                "source_certification_ids_json": _as_json(source_certification_ids),
                "source_dataset_certification_ids_json": _as_json(source_dataset_certification_ids),
                "source_lifecycle_states_json": _as_json(
                    {
                        asset_id: _normalize_text(bundle.get("lifecycle_row", {}).get("lifecycle_state"))
                        for asset_id, bundle in source_assets.items()
                    }
                ),
                "source_alignment_counts_json": _as_json(
                    {
                        asset_id: len(bundle.get("alignment_rows", []))
                        for asset_id, bundle in source_assets.items()
                    }
                ),
                "source_record_counts_json": _as_json(join_diagnostics["source_row_counts"]),
                "eligible_record_counts_json": _as_json(join_diagnostics["eligible_record_counts"]),
                "selected_record_counts_json": _as_json(
                    {
                        "selected_unique_record_counts": join_diagnostics["selected_unique_record_counts"],
                        "selected_attachment_counts": join_diagnostics["selected_attachment_counts"],
                    }
                ),
                "rejected_record_counts_json": _as_json(
                    {name: len(values) for name, values in rejected_ids.items()}
                ),
                "unmatched_record_counts_json": _as_json(
                    {name: len(values) for name, values in unmatched_entities.items()}
                ),
                "join_diagnostics_json": _as_json(join_diagnostics),
                "rejected_evidence_json": _as_json(
                    {name: sorted(values) for name, values in rejected_ids.items()}
                ),
                "unmatched_evidence_json": _as_json(
                    {name: sorted(values) for name, values in unmatched_entities.items()}
                ),
                "cardinality_contract_json": _as_json(join_diagnostics["cardinality_contracts"]),
                "cardinality_validation_status": "validated" if not cardinality_issues else "blocked",
                "point_in_time_validation_status": "safe" if not validation["point_in_time_issues"] else "blocked",
                "predictor_outcome_separation_status": "separated" if not predictor_outcome_issues else "blocked",
                "provenance_completeness": _bool_to_int(provenance_complete),
                "lineage_completeness": _bool_to_int(lineage_complete),
                "dataset_row_count": len(produced_rows),
                "rejected_row_count": sum(len(values) for values in rejected_ids.values()),
                "unmatched_row_count": sum(len(values) for values in unmatched_entities.values()),
                "duplicate_row_count": len(duplicate_row_ids),
                "evidence_package_id": evidence_package_id,
                "evidence_package_json": _as_json(evidence_package),
                "readiness_state": "feature_ready" if validation["ok"] else "blocked",
                "unresolved_blockers_json": _as_json(validation["errors"]),
                "schema_version": HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
            }
        )

        for row in produced_rows:
            storage.upsert(HISTORICAL_DATASET_ROW_TABLE, row, key_columns=("dataset_row_id",))
        for edge in lineage_edges:
            storage.upsert("lineage_edges", edge, key_columns=("lineage_edge_id",))
        storage.upsert(HISTORICAL_DATASET_BATCH_TABLE, batch_row, key_columns=("batch_id",))
        storage.upsert("historical_certifications", certification_row, key_columns=("certification_id",))

        platform = LocalDataPlatform(storage_path=storage.path, backend=backend, dataset_owner="src.data")
        try:
            platform.register_dataset(contract)
            validation_row = platform.store_validation_result(
                contract,
                version_id=version_id,
                snapshot_id=batch_snapshot_id,
                lineage_id=batch_lineage_id,
                validation=validation,
                created_at=created_at,
                updated_at=created_at,
            )
            existing_versions = platform.store.fetch(
                "dataset_versions",
                where="dataset_id = ?",
                params=[contract.dataset_id],
                order_by="version_number ASC",
            )
            existing_version_row = next(
                (dict(row) for row in existing_versions if _normalize_text(row.get("version_id")) == version_id),
                {},
            )
            version_number = int(existing_version_row.get("version_number") or (len(existing_versions) + 1))
            version_row = {
                "version_id": version_id,
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
                "owner": contract.owner,
                "sport": contract.sport,
                "feature_pack": contract.feature_pack,
                "storage_location": contract.storage_location,
                "readiness": "feature_ready" if validation["ok"] else "blocked",
                "update_frequency": contract.update_frequency,
                "validation_state": "validated" if validation["ok"] else "rejected",
                "status": "active" if validation["ok"] else "blocked",
                "version_number": version_number,
                "raw_record_count": sum(join_diagnostics["source_row_counts"].values()),
                "normalized_record_count": len(produced_rows),
                "feature_snapshot_count": 0,
                "validation_id": validation_row["validation_id"],
                "checksum": hashlib.sha256(_as_json(produced_rows).encode("utf-8")).hexdigest(),
                "schema_version": contract.schema_version,
                "created_at": created_at,
                "updated_at": created_at,
                "source": contract.source_name,
                "provider": contract.provider,
                "market": contract.market,
                "market_type": contract.market_type,
                "asset_class": contract.asset_class,
                "snapshot_id": batch_snapshot_id,
                "lineage_id": batch_lineage_id,
                "quality_score": 1.0 if validation["ok"] else 0.0,
                "metadata_json": _as_json(dict(contract.metadata)),
                "payload_json": _as_json(
                    {
                        **contract.as_dict(),
                        "batch_id": batch_id,
                        "version_number": version_number,
                        "evidence_package_id": evidence_package_id,
                        "validation": validation,
                    }
                ),
            }
            platform.store.upsert("dataset_versions", version_row, key_columns=("version_id",))
            registry_contract = DatasetContract.from_mapping(
                {
                    **contract.as_dict(),
                    "readiness": "feature_ready" if validation["ok"] else "blocked",
                    "validation_state": "validated" if validation["ok"] else "rejected",
                    "status": "active" if validation["ok"] else "blocked",
                }
            )
            registry_row = platform._registry_row(
                registry_contract,
                latest_version_number=version_number,
                latest_snapshot_id=batch_snapshot_id,
                latest_feature_snapshot_id=_normalize_text(
                    (platform.read_dataset(contract.dataset_id).get("latest_feature_snapshot_id") or f"{contract.dataset_id}.feature.000")
                ),
                latest_validation_id=validation_row["validation_id"],
                version_count=max(len(existing_versions), version_number),
                validation_state="validated" if validation["ok"] else "rejected",
            )
            platform.store.upsert("dataset_registry", registry_row, key_columns=("dataset_id",))
        finally:
            platform.close()

        lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=storage.path, backend=backend, dataset_owner="src.data")
        try:
            identity = build_research_asset_identity_contract(
                asset_id=contract.dataset_id,
                asset_family="dataset",
                market_profile=profile.profile_id,
                market=profile.market_scope or profile.profile_id,
                league=_normalize_text(profile.metadata.get("league"), "NFL"),
                sport=_normalize_text(profile.metadata.get("sport"), "football"),
                provider=contract.provider,
                connector="historical_dataset_population_runtime",
                schema_version=HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION,
                lineage_version=version_id,
                asset_name="NFL Historical Dataset Population",
                asset_type="historical_dataset_population",
                metadata={
                    "batch_id": batch_id,
                    "version_id": version_id,
                    "dataset_contract_version": HISTORICAL_DATASET_CONTRACT_VERSION,
                    "evidence_package_id": evidence_package_id,
                },
            )
            lifecycle_row = lifecycle_runtime.record_lifecycle_state(
                identity=identity,
                lifecycle_state="feature_ready" if validation["ok"] else "dataset_certified",
                lifecycle_reason="historical_dataset_population_certified" if validation["ok"] else "historical_dataset_population_blocked",
                certification_result={
                    "certification_id": certification_row["certification_id"],
                    "certification_status": certification_row["certification_status"],
                    "certification_state": certification_row["certification_status"],
                    "alignment_status": "aligned" if validation["ok"] else "blocked",
                    "alignment_reason": "dataset_population_validated" if validation["ok"] else "dataset_population_blocked",
                    "alignment_score": 1.0 if validation["ok"] else 0.0,
                    "batch_id": batch_id,
                    "version_id": version_id,
                },
                dataset_result={
                    "certification_id": certification_row["certification_id"],
                    "certification_status": certification_row["certification_status"],
                    "batch_id": batch_id,
                    "version_id": version_id,
                },
                created_at=created_at,
                notes={
                    "dataset_row_count": len(produced_rows),
                    "evidence_package_id": evidence_package_id,
                },
            )
        finally:
            lifecycle_runtime.close()

        snapshot = build_historical_dataset_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            profile_id=profile_id,
            dataset_id=contract.dataset_id,
            batch_id=batch_id,
        )
        snapshot["source_assets"] = source_assets
        snapshot["validation"] = validation
        snapshot["dataset_certification"] = certification_row
        snapshot["dataset_lifecycle"] = lifecycle_row
        snapshot["idempotent_reuse"] = False
        return snapshot
    finally:
        storage.close()


def build_historical_dataset_population_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
    batch_id: str | None = None,
    include_coverage_planner_snapshot: bool = True,
) -> dict[str, Any]:
    storage = create_historical_research_storage_engine(storage_path, backend=backend)
    try:
        batch_rows = storage.fetch(
            HISTORICAL_DATASET_BATCH_TABLE,
            where="dataset_id = ?" + (" AND batch_id = ?" if batch_id else ""),
            params=[dataset_id, *([batch_id] if batch_id else [])],
            order_by="created_at ASC, batch_id ASC",
        ) if storage.table_exists(HISTORICAL_DATASET_BATCH_TABLE) else []
        latest_batch = dict(batch_rows[-1]) if batch_rows else {}
        dataset_rows = storage.fetch(
            HISTORICAL_DATASET_ROW_TABLE,
            where="dataset_id = ?" + (" AND batch_id = ?" if batch_id else ""),
            params=[dataset_id, *([batch_id] if batch_id else [])],
            order_by="event_start_time ASC, market_type ASC, selection ASC",
        ) if storage.table_exists(HISTORICAL_DATASET_ROW_TABLE) else []
        certification_rows = storage.fetch(
            "historical_certifications",
            where="batch_id = ?",
            params=[_normalize_text(latest_batch.get("batch_id"))],
            order_by="certified_at ASC, certification_id ASC",
        ) if latest_batch and storage.table_exists("historical_certifications") else []
        lifecycle_rows = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[dataset_id],
            order_by="created_at ASC, asset_id ASC",
        ) if storage.table_exists("research_asset_lifecycles") else []
        local_platform = LocalDataPlatform(
            storage_path=storage.path,
            backend=backend,
            dataset_owner="src.data",
        )
        try:
            local_platform_snapshot = local_platform.dashboard_snapshot(dataset_id)
        finally:
            local_platform.close()
        source_certification_ids = _load_json_mapping(latest_batch.get("source_certification_ids_json"))
        unresolved_blockers = _load_json_list(latest_batch.get("unresolved_blockers_json"))
        join_diagnostics = _load_json_mapping(latest_batch.get("join_diagnostics_json"))
        coverage_snapshot = {}
        if include_coverage_planner_snapshot:
            try:
                from src.market_intelligence.research_asset_coverage_planner import (
                    build_research_asset_coverage_planner_snapshot,
                )

                coverage_snapshot = build_research_asset_coverage_planner_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                    profile_id=profile_id,
                    include_dataset_population_snapshot=False,
                )
            except Exception as exc:
                coverage_snapshot = {
                    "ok": False,
                    "status": "coverage_planner_snapshot_failed",
                    "warnings": [str(exc)],
                }
        else:
            coverage_snapshot = {
                "ok": False,
                "status": "not_embedded",
                "warnings": [],
            }
        latest_lifecycle = dict(lifecycle_rows[-1]) if lifecycle_rows else {}
        latest_certification = dict(certification_rows[-1]) if certification_rows else {}
        dataset_certification_status = _normalize_text(
            latest_certification.get("certification_status"),
            "missing",
        )
        readiness_state = _normalize_text(latest_batch.get("readiness_state"), "missing")
        join_validation_status = (
            "validated"
            if latest_batch
            and _normalize_text(latest_batch.get("cardinality_validation_status")) == "validated"
            and _normalize_text(latest_batch.get("point_in_time_validation_status")) == "safe"
            and not unresolved_blockers
            else "blocked" if latest_batch else "missing"
        )
        ok = (
            bool(latest_batch)
            and bool(dataset_rows)
            and dataset_certification_status == "certified"
            and readiness_state == "feature_ready"
        )
        return {
            "ok": ok,
            "status": "ready" if ok else "partial" if latest_batch or dataset_rows else "missing",
            "profile_id": profile_id,
            "dataset_id": dataset_id,
            "dataset_name": _normalize_text(latest_batch.get("dataset_name"), DEFAULT_NFL_HISTORICAL_DATASET_NAME),
            "batch_id": _normalize_text(latest_batch.get("batch_id")),
            "version_id": _normalize_text(latest_batch.get("version_id")),
            "dataset_contract_version": _normalize_text(latest_batch.get("dataset_contract_version")),
            "population_version": _normalize_text(latest_batch.get("population_version"), HISTORICAL_DATASET_POPULATION_SCHEMA_VERSION),
            "dataset_as_of_time": _normalize_text(latest_batch.get("dataset_as_of_time")),
            "cutoff_policy_version": _normalize_text(
                latest_batch.get("cutoff_policy_version"),
                HISTORICAL_DATASET_CUTOFF_POLICY_ID,
            ),
            "dataset_row_count": len(dataset_rows),
            "source_asset_count": len(source_certification_ids),
            "required_source_assets": list(HISTORICAL_DATASET_REQUIRED_ASSET_LOOKUP),
            "certified_source_asset_count": len([asset_id for asset_id, cert_id in source_certification_ids.items() if cert_id]),
            "source_record_counts": join_diagnostics.get("source_row_counts", {}),
            "eligible_record_counts": join_diagnostics.get("eligible_record_counts", {}),
            "selected_record_counts": join_diagnostics.get("selected_unique_record_counts", {}),
            "rejected_record_count": int(latest_batch.get("rejected_row_count") or 0),
            "unmatched_record_count": int(latest_batch.get("unmatched_row_count") or 0),
            "join_validation_status": join_validation_status,
            "cardinality_validation_status": _normalize_text(latest_batch.get("cardinality_validation_status"), "missing"),
            "point_in_time_validation_status": _normalize_text(latest_batch.get("point_in_time_validation_status"), "missing"),
            "predictor_outcome_separation_status": _normalize_text(latest_batch.get("predictor_outcome_separation_status"), "missing"),
            "provenance_completeness": bool(int(latest_batch.get("provenance_completeness") or 0)),
            "lineage_completeness": bool(int(latest_batch.get("lineage_completeness") or 0)),
            "dataset_certification_status": dataset_certification_status,
            "lifecycle_state": _normalize_text(latest_lifecycle.get("lifecycle_state"), "missing"),
            "readiness_state": readiness_state,
            "unresolved_blockers": unresolved_blockers,
            "evidence_package_id": _normalize_text(latest_batch.get("evidence_package_id")),
            "join_diagnostics": join_diagnostics,
            "rejected_evidence": _load_json_mapping(latest_batch.get("rejected_evidence_json")),
            "unmatched_evidence": _load_json_mapping(latest_batch.get("unmatched_evidence_json")),
            "dataset_rows": [dict(row) for row in dataset_rows],
            "dataset_batches": [dict(row) for row in batch_rows],
            "dataset_certifications": [dict(row) for row in certification_rows],
            "dataset_lifecycles": [dict(row) for row in lifecycle_rows],
            "local_platform_snapshot": local_platform_snapshot,
            "coverage_planner_snapshot": coverage_snapshot,
            "storage": storage.health(),
            "warnings": [],
        }
    finally:
        storage.close()


def get_historical_dataset_population_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_RESEARCH_PROFILE_ID,
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
) -> dict[str, Any]:
    try:
        return build_historical_dataset_population_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile_id,
            dataset_id=dataset_id,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "historical_dataset_population_snapshot_error",
            "profile_id": profile_id,
            "dataset_id": dataset_id,
            "dataset_name": DEFAULT_NFL_HISTORICAL_DATASET_NAME,
            "batch_id": "",
            "version_id": "",
            "dataset_row_count": 0,
            "source_asset_count": 0,
            "required_source_assets": list(HISTORICAL_DATASET_REQUIRED_ASSET_LOOKUP),
            "certified_source_asset_count": 0,
            "source_record_counts": {},
            "eligible_record_counts": {},
            "selected_record_counts": {},
            "rejected_record_count": 0,
            "unmatched_record_count": 0,
            "join_validation_status": "missing",
            "cardinality_validation_status": "missing",
            "point_in_time_validation_status": "missing",
            "predictor_outcome_separation_status": "missing",
            "provenance_completeness": False,
            "lineage_completeness": False,
            "dataset_certification_status": "missing",
            "lifecycle_state": "missing",
            "readiness_state": "missing",
            "unresolved_blockers": [str(exc)],
            "evidence_package_id": "",
            "join_diagnostics": {},
            "rejected_evidence": {},
            "unmatched_evidence": {},
            "dataset_rows": [],
            "dataset_batches": [],
            "dataset_certifications": [],
            "dataset_lifecycles": [],
            "local_platform_snapshot": {},
            "coverage_planner_snapshot": {},
            "storage": {},
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_HISTORICAL_RESEARCH_OWNER",
    "DEFAULT_HISTORICAL_RESEARCH_DATASET_NAME",
    "DEFAULT_NFL_HISTORICAL_DATASET_ID",
    "DEFAULT_NFL_HISTORICAL_DATASET_NAME",
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
    "build_historical_dataset_population",
    "build_historical_dataset_population_dashboard_snapshot",
    "build_historical_research_dashboard_snapshot",
    "build_historical_research_fixture",
    "create_historical_research_storage_engine",
    "get_historical_dataset_population_snapshot_for_dashboard",
    "get_historical_research_market_profile",
    "get_historical_research_snapshot_for_dashboard",
    "normalize_historical_event_rows",
    "normalize_historical_market_rows",
    "normalize_historical_selection_rows",
    "validate_historical_research_profile",
    "validate_historical_stage_rows",
]
