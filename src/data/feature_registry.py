from __future__ import annotations

"""Canonical reusable feature contracts for Phase 5.1A.

This module defines the registry and snapshot-grain contracts for reusable
feature population from the certified Phase 5.0 historical dataset layer.
It does not populate feature snapshots, persist feature batches, run math
engines, or reread raw asset tables.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.data.historical_research_database import (
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
    HISTORICAL_DATASET_CUTOFF_POLICY_ID,
)


FEATURE_REGISTRY_SCHEMA_VERSION = "src.data.feature_registry.v1"
FEATURE_DEFINITION_VERSION = "phase5.1a.feature_definitions.v1"
FEATURE_SNAPSHOT_TRANSFORMATION_VERSION = "phase5.1b.snapshot_population.pending"
CANONICAL_DATASET_ROW_GRAIN_ID = "dataset.sports.nfl.historical_dataset.event_market_context.v1"
CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID = "dataset.sports.nfl.feature_snapshot.dataset_row_scope.v1"
CANONICAL_FEATURE_REGISTRY_DOC = "docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md"
CANONICAL_FEATURE_STORE_CONTRACT_DOC = "docs/contracts/NFL_FEATURE_STORE_CONTRACT.md"
CANONICAL_FEATURE_SNAPSHOT_CONTRACT_DOC = "docs/contracts/FEATURE_SNAPSHOT_CONTRACT.md"
CANONICAL_FEATURE_STORE_ARCHITECTURE_DOC = "docs/architecture/FEATURE_STORE_ARCHITECTURE.md"
DEFAULT_FEATURE_OWNER = "src.data.feature_registry"
DEFAULT_MARKET_VERTICAL = "sports"
DEFAULT_PORTABILITY_CLASSIFICATION = "nfl_minimum_schema_dataset"
DEFAULT_LINEAGE_REQUIREMENTS = (
    "dataset_id",
    "batch_id",
    "dataset_row_id",
    "decision_context_id",
    "decision_cutoff_time",
    "source_certification_ids_json",
    "source_alignment_certification_ids_json",
    "selected_source_row_ids_json",
    "source_lineage_ids_json",
)
DEFAULT_POINT_IN_TIME_CONSTRAINTS = (
    "inherit_phase50_decision_cutoff",
    "reuse_certified_phase50_selected_evidence_only",
    "no_raw_or_normalized_source_table_rereads",
    "no_post_cutoff_updates",
    "no_target_event_live_or_final_statistics",
    "no_outcome_fields_in_predictor_namespace",
)
DEFAULT_CUTOFF_SEMANTICS = (
    "inherit decision_cutoff_time from the certified historical dataset row, "
    "where decision_cutoff_time = scheduled_kickoff_time - five minutes"
)

FEATURE_CLASSIFICATIONS = {
    "direct",
    "deterministic_derived",
    "deferred_mathematical_engine_output",
}
FEATURE_VALUE_TYPES = {
    "boolean",
    "float",
    "integer",
    "string",
    "timestamp",
}
FEATURE_MISSINGNESS_POLICIES = {
    "required",
    "nullable",
    "not_applicable_for_event_scope_markets",
    "not_applicable_for_non_line_markets",
    "unavailable_when_source_evidence_missing",
    "invalid_source",
    "unsupported_context",
}
FEATURE_ENTITY_SCOPES = {
    "event",
    "market_context",
    "weather_context",
    "home_team_context",
    "away_team_context",
    "data_quality_context",
}
OUTCOME_FIELD_PREFIXES = ("label_",)
OUTCOME_FIELD_NAMES = {
    "result_id",
    "label_final_result",
    "label_final_score_home",
    "label_final_score_away",
    "label_winner_team_id",
    "label_winner_team",
    "label_margin",
    "label_total_points",
    "label_settlement_status",
    "label_result_recorded_time",
}
RAW_SOURCE_FIELD_MARKERS = {
    "raw_payload",
    "raw_record",
    "provider_payload",
    "nfl_schedule",
    "nfl_results",
    "nfl_odds_snapshots",
    "nfl_weather_snapshots",
    "nfl_injury_snapshots",
    "nfl_team_stats_snapshots",
}
ACTIVE_FEATURE_FAMILIES = (
    "event_context",
    "market_context",
    "weather_context",
    "injury_context",
    "team_statistics_context",
    "data_quality_context",
)
ACTIVE_DATASET_FIELD_ROOTS = {
    "season",
    "week",
    "team_side",
    "home_team_id",
    "away_team_id",
    "scheduled_kickoff_time",
    "decision_cutoff_time",
    "neutral_site",
    "market_type",
    "selection",
    "book",
    "line_value",
    "american_odds",
    "decimal_odds",
    "implied_probability",
    "odds_freshness_seconds",
    "weather_forecast_time",
    "weather_freshness_seconds",
    "home_injury_record_count",
    "away_injury_record_count",
    "home_injury_freshness_seconds",
    "away_injury_freshness_seconds",
    "home_team_stats_freshness_seconds",
    "away_team_stats_freshness_seconds",
    "selected_weather_timestamp",
    "selected_home_injury_timestamp",
    "selected_away_injury_timestamp",
    "home_team_stats_snapshot_id",
    "away_team_stats_snapshot_id",
    "point_in_time_status",
    "predictor_outcome_separation_status",
    "decision_readiness_status",
    "predictor_references_json",
    "missing_required_assets_json",
    "source_certification_ids_json",
    "source_alignment_certification_ids_json",
    "selected_source_row_ids_json",
    "source_lineage_ids_json",
}

DEFERRED_MATHEMATICAL_FEATURE_IDS = (
    "feature.sports.nfl.market.edge",
    "feature.sports.nfl.market.expected_value",
    "feature.sports.nfl.market.kelly_fraction",
    "feature.sports.nfl.model.win_probability",
)
DEFERRED_UNSUPPORTED_DATASET_FEATURE_IDS = (
    "feature.sports.nfl.weather.temperature_f",
    "feature.sports.nfl.weather.wind_speed_mph",
    "feature.sports.nfl.weather.precipitation_probability",
    "feature.sports.nfl.injury.home_practice_dnp_count",
    "feature.sports.nfl.injury.away_practice_dnp_count",
    "feature.sports.nfl.team_stats.home_metric_value",
    "feature.sports.nfl.team_stats.away_metric_value",
    "feature.sports.nfl.team_stats.home_away_difference",
    "feature.sports.nfl.team_stats.measurement_window",
)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


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

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _load_json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    text = _normalize_text(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _load_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    text = _normalize_text(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    return list(parsed) if isinstance(parsed, list) else []


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _split_root(field_ref: str) -> str:
    return _normalize_text(field_ref).split(".", 1)[0]


@dataclass(slots=True, frozen=True)
class FeatureDefinition:
    feature_id: str
    feature_name: str
    feature_family: str
    market_vertical: str
    entity_scope: str
    dataset_grain_compatibility: str
    feature_version: str
    classification: str
    value_type: str
    unit: str
    nullable: bool
    missingness_policy: str
    source_dataset_field_refs: tuple[str, ...]
    transformation_definition: str
    transformation_version: str
    cutoff_semantics: str
    point_in_time_constraints: tuple[str, ...]
    expected_range: str
    allowed_values: tuple[str, ...]
    feature_owner: str = DEFAULT_FEATURE_OWNER
    lifecycle_state: str = "Historical Dataset Ready"
    certification_state: str = "definition_only"
    portability_classification: str = DEFAULT_PORTABILITY_CLASSIFICATION
    lineage_requirements: tuple[str, ...] = DEFAULT_LINEAGE_REQUIREMENTS
    predictor_namespace: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_id", _normalize_text(self.feature_id))
        object.__setattr__(self, "feature_name", _normalize_text(self.feature_name))
        object.__setattr__(self, "feature_family", _normalize_text(self.feature_family))
        object.__setattr__(self, "market_vertical", _normalize_text(self.market_vertical))
        object.__setattr__(self, "entity_scope", _normalize_text(self.entity_scope))
        object.__setattr__(self, "dataset_grain_compatibility", _normalize_text(self.dataset_grain_compatibility))
        object.__setattr__(self, "feature_version", _normalize_text(self.feature_version, FEATURE_DEFINITION_VERSION))
        object.__setattr__(self, "classification", _normalize_text(self.classification))
        object.__setattr__(self, "value_type", _normalize_text(self.value_type))
        object.__setattr__(self, "unit", _normalize_text(self.unit))
        object.__setattr__(self, "missingness_policy", _normalize_text(self.missingness_policy))
        object.__setattr__(
            self,
            "source_dataset_field_refs",
            tuple(
                _normalize_text(value)
                for value in self.source_dataset_field_refs
                if _normalize_text(value)
            ),
        )
        object.__setattr__(self, "transformation_definition", _normalize_text(self.transformation_definition))
        object.__setattr__(self, "transformation_version", _normalize_text(self.transformation_version))
        object.__setattr__(self, "cutoff_semantics", _normalize_text(self.cutoff_semantics))
        object.__setattr__(
            self,
            "point_in_time_constraints",
            tuple(
                _normalize_text(value)
                for value in self.point_in_time_constraints
                if _normalize_text(value)
            ),
        )
        object.__setattr__(self, "expected_range", _normalize_text(self.expected_range))
        object.__setattr__(
            self,
            "allowed_values",
            tuple(_normalize_text(value) for value in self.allowed_values if _normalize_text(value)),
        )
        object.__setattr__(self, "feature_owner", _normalize_text(self.feature_owner, DEFAULT_FEATURE_OWNER))
        object.__setattr__(self, "lifecycle_state", _normalize_text(self.lifecycle_state))
        object.__setattr__(self, "certification_state", _normalize_text(self.certification_state))
        object.__setattr__(
            self,
            "portability_classification",
            _normalize_text(self.portability_classification, DEFAULT_PORTABILITY_CLASSIFICATION),
        )
        object.__setattr__(
            self,
            "lineage_requirements",
            tuple(_normalize_text(value) for value in self.lineage_requirements if _normalize_text(value)),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "feature_family": self.feature_family,
            "market_vertical": self.market_vertical,
            "entity_scope": self.entity_scope,
            "dataset_grain_compatibility": self.dataset_grain_compatibility,
            "feature_version": self.feature_version,
            "classification": self.classification,
            "value_type": self.value_type,
            "unit": self.unit,
            "nullable": self.nullable,
            "missingness_policy": self.missingness_policy,
            "source_dataset_field_refs": list(self.source_dataset_field_refs),
            "transformation_definition": self.transformation_definition,
            "transformation_version": self.transformation_version,
            "cutoff_semantics": self.cutoff_semantics,
            "point_in_time_constraints": list(self.point_in_time_constraints),
            "expected_range": self.expected_range,
            "allowed_values": list(self.allowed_values),
            "feature_owner": self.feature_owner,
            "lifecycle_state": self.lifecycle_state,
            "certification_state": self.certification_state,
            "portability_classification": self.portability_classification,
            "lineage_requirements": list(self.lineage_requirements),
            "predictor_namespace": self.predictor_namespace,
        }


@dataclass(slots=True, frozen=True)
class FeatureSnapshotContext:
    dataset_id: str
    batch_id: str
    dataset_row_id: str
    decision_context_id: str
    event_id: str
    season: int
    week: int
    home_team_id: str
    away_team_id: str
    team_side: str
    market_type: str
    selection: str
    book: str
    scheduled_kickoff_time: str
    decision_cutoff_time: str
    cutoff_policy_version: str
    point_in_time_status: str
    predictor_outcome_separation_status: str
    decision_readiness_status: str
    selected_source_row_ids: Mapping[str, Any]
    source_certification_ids: Mapping[str, Any]
    source_alignment_certification_ids: Mapping[str, Any]
    source_lineage_ids: Mapping[str, Any]
    missing_required_assets: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "batch_id": self.batch_id,
            "dataset_row_id": self.dataset_row_id,
            "decision_context_id": self.decision_context_id,
            "event_id": self.event_id,
            "season": self.season,
            "week": self.week,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "team_side": self.team_side,
            "market_type": self.market_type,
            "selection": self.selection,
            "book": self.book,
            "scheduled_kickoff_time": self.scheduled_kickoff_time,
            "decision_cutoff_time": self.decision_cutoff_time,
            "cutoff_policy_version": self.cutoff_policy_version,
            "point_in_time_status": self.point_in_time_status,
            "predictor_outcome_separation_status": self.predictor_outcome_separation_status,
            "decision_readiness_status": self.decision_readiness_status,
            "selected_source_row_ids": dict(self.selected_source_row_ids),
            "source_certification_ids": dict(self.source_certification_ids),
            "source_alignment_certification_ids": dict(self.source_alignment_certification_ids),
            "source_lineage_ids": dict(self.source_lineage_ids),
            "missing_required_assets": list(self.missing_required_assets),
        }


def _feature(
    feature_id: str,
    *,
    feature_name: str,
    feature_family: str,
    entity_scope: str,
    classification: str,
    value_type: str,
    unit: str,
    source_refs: Sequence[str],
    transformation_definition: str,
    missingness_policy: str,
    expected_range: str,
    nullable: bool = False,
    allowed_values: Sequence[str] = (),
    portability_classification: str = DEFAULT_PORTABILITY_CLASSIFICATION,
) -> FeatureDefinition:
    return FeatureDefinition(
        feature_id=feature_id,
        feature_name=feature_name,
        feature_family=feature_family,
        market_vertical=DEFAULT_MARKET_VERTICAL,
        entity_scope=entity_scope,
        dataset_grain_compatibility=CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID,
        feature_version=FEATURE_DEFINITION_VERSION,
        classification=classification,
        value_type=value_type,
        unit=unit,
        nullable=nullable,
        missingness_policy=missingness_policy,
        source_dataset_field_refs=tuple(source_refs),
        transformation_definition=transformation_definition,
        transformation_version=FEATURE_SNAPSHOT_TRANSFORMATION_VERSION,
        cutoff_semantics=DEFAULT_CUTOFF_SEMANTICS,
        point_in_time_constraints=DEFAULT_POINT_IN_TIME_CONSTRAINTS,
        expected_range=expected_range,
        allowed_values=tuple(allowed_values),
        portability_classification=portability_classification,
    )


_ACTIVE_FEATURE_DEFINITIONS: tuple[FeatureDefinition, ...] = (
    _feature(
        "feature.sports.nfl.event.season",
        feature_name="Season",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="integer",
        unit="season",
        source_refs=("season",),
        transformation_definition="direct_copy(row.season)",
        missingness_policy="required",
        expected_range="positive integer season identifier",
        portability_classification="cross_sport_event_context",
    ),
    _feature(
        "feature.sports.nfl.event.week",
        feature_name="Week",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="integer",
        unit="week",
        source_refs=("week",),
        transformation_definition="direct_copy(row.week)",
        missingness_policy="required",
        expected_range="positive regular-season or postseason week number",
        portability_classification="cross_sport_event_context",
    ),
    _feature(
        "feature.sports.nfl.event.team_side",
        feature_name="Team Side",
        feature_family="event_context",
        entity_scope="market_context",
        classification="direct",
        value_type="string",
        unit="category",
        source_refs=("team_side",),
        transformation_definition="direct_copy(row.team_side)",
        missingness_policy="not_applicable_for_event_scope_markets",
        expected_range="home, away, or blank for event-scope contexts such as totals",
        nullable=True,
        allowed_values=("home", "away"),
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.event.home_team_id",
        feature_name="Home Team ID",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="string",
        unit="team_id",
        source_refs=("home_team_id",),
        transformation_definition="direct_copy(row.home_team_id)",
        missingness_policy="required",
        expected_range="non-empty canonical team identifier",
    ),
    _feature(
        "feature.sports.nfl.event.away_team_id",
        feature_name="Away Team ID",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="string",
        unit="team_id",
        source_refs=("away_team_id",),
        transformation_definition="direct_copy(row.away_team_id)",
        missingness_policy="required",
        expected_range="non-empty canonical team identifier",
    ),
    _feature(
        "feature.sports.nfl.event.scheduled_kickoff_time",
        feature_name="Scheduled Kickoff Time",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="timestamp",
        unit="iso8601_utc",
        source_refs=("scheduled_kickoff_time",),
        transformation_definition="direct_copy(row.scheduled_kickoff_time)",
        missingness_policy="required",
        expected_range="ISO-8601 UTC timestamp",
        portability_classification="cross_sport_event_context",
    ),
    _feature(
        "feature.sports.nfl.event.decision_cutoff_time",
        feature_name="Decision Cutoff Time",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="timestamp",
        unit="iso8601_utc",
        source_refs=("decision_cutoff_time",),
        transformation_definition="direct_copy(row.decision_cutoff_time)",
        missingness_policy="required",
        expected_range="ISO-8601 UTC timestamp",
        portability_classification="cross_sport_event_context",
    ),
    _feature(
        "feature.sports.nfl.event.cutoff_buffer_seconds",
        feature_name="Cutoff Buffer Seconds",
        feature_family="event_context",
        entity_scope="event",
        classification="deterministic_derived",
        value_type="integer",
        unit="seconds",
        source_refs=("scheduled_kickoff_time", "decision_cutoff_time"),
        transformation_definition="seconds_between(row.scheduled_kickoff_time, row.decision_cutoff_time)",
        missingness_policy="required",
        expected_range="300 for the canonical kickoff-minus-five policy",
        portability_classification="cross_sport_event_context",
    ),
    _feature(
        "feature.sports.nfl.event.neutral_site_flag",
        feature_name="Neutral Site Flag",
        feature_family="event_context",
        entity_scope="event",
        classification="direct",
        value_type="boolean",
        unit="flag",
        source_refs=("neutral_site",),
        transformation_definition="bool(row.neutral_site)",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="cross_sport_event_context",
    ),
    _feature(
        "feature.sports.nfl.market.market_type",
        feature_name="Market Type",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="string",
        unit="category",
        source_refs=("market_type",),
        transformation_definition="direct_copy(row.market_type)",
        missingness_policy="required",
        expected_range="moneyline, spread, total, or another canonical market type",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.selection",
        feature_name="Selection",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="string",
        unit="category",
        source_refs=("selection",),
        transformation_definition="direct_copy(row.selection)",
        missingness_policy="required",
        expected_range="canonical selection key such as home or over",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.book",
        feature_name="Book",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="string",
        unit="book",
        source_refs=("book",),
        transformation_definition="direct_copy(row.book)",
        missingness_policy="required",
        expected_range="canonical book key such as consensus",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.line_value",
        feature_name="Line Value",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="points",
        source_refs=("line_value",),
        transformation_definition="direct_copy(row.line_value)",
        missingness_policy="not_applicable_for_non_line_markets",
        expected_range="numeric line for spread and total markets; blank for moneyline",
        nullable=True,
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.american_odds",
        feature_name="American Odds",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="american_odds",
        source_refs=("american_odds",),
        transformation_definition="direct_copy(row.american_odds)",
        missingness_policy="required",
        expected_range="numeric American odds",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.decimal_odds",
        feature_name="Decimal Odds",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="decimal_odds",
        source_refs=("decimal_odds",),
        transformation_definition="direct_copy(row.decimal_odds)",
        missingness_policy="required",
        expected_range="decimal odds greater than 1",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.implied_probability",
        feature_name="Implied Probability",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="probability",
        source_refs=("implied_probability",),
        transformation_definition=(
            "direct_copy(row.implied_probability); upstream odds-to-probability math owner remains src.data.odds_math"
        ),
        missingness_policy="required",
        expected_range="0.0 to 1.0 inclusive",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.market.odds_freshness_seconds",
        feature_name="Odds Freshness Seconds",
        feature_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="integer",
        unit="seconds",
        source_refs=("odds_freshness_seconds",),
        transformation_definition="direct_copy(row.odds_freshness_seconds)",
        missingness_policy="required",
        expected_range="non-negative integer seconds between odds availability and decision cutoff",
        portability_classification="sports_market_context",
    ),
    _feature(
        "feature.sports.nfl.weather.forecast_time",
        feature_name="Weather Forecast Time",
        feature_family="weather_context",
        entity_scope="weather_context",
        classification="direct",
        value_type="timestamp",
        unit="iso8601_utc",
        source_refs=("weather_forecast_time",),
        transformation_definition="direct_copy(row.weather_forecast_time)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="ISO-8601 UTC forecast issuance timestamp",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.weather.freshness_seconds",
        feature_name="Weather Freshness Seconds",
        feature_family="weather_context",
        entity_scope="weather_context",
        classification="direct",
        value_type="integer",
        unit="seconds",
        source_refs=("weather_freshness_seconds",),
        transformation_definition="direct_copy(row.weather_freshness_seconds)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer seconds between weather availability and decision cutoff",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.weather.available_flag",
        feature_name="Weather Evidence Available Flag",
        feature_family="weather_context",
        entity_scope="weather_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("selected_weather_timestamp",),
        transformation_definition="bool(row.selected_weather_timestamp)",
        missingness_policy="required",
        expected_range="0 or 1",
    ),
    _feature(
        "feature.sports.nfl.injury.home_reported_player_count",
        feature_name="Home Reported Player Count",
        feature_family="injury_context",
        entity_scope="home_team_context",
        classification="direct",
        value_type="integer",
        unit="players",
        source_refs=("home_injury_record_count",),
        transformation_definition="direct_copy(row.home_injury_record_count)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer count of selected home injury rows",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.away_reported_player_count",
        feature_name="Away Reported Player Count",
        feature_family="injury_context",
        entity_scope="away_team_context",
        classification="direct",
        value_type="integer",
        unit="players",
        source_refs=("away_injury_record_count",),
        transformation_definition="direct_copy(row.away_injury_record_count)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer count of selected away injury rows",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.home_freshness_seconds",
        feature_name="Home Injury Freshness Seconds",
        feature_family="injury_context",
        entity_scope="home_team_context",
        classification="direct",
        value_type="integer",
        unit="seconds",
        source_refs=("home_injury_freshness_seconds",),
        transformation_definition="direct_copy(row.home_injury_freshness_seconds)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer seconds between home injury availability and decision cutoff",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.away_freshness_seconds",
        feature_name="Away Injury Freshness Seconds",
        feature_family="injury_context",
        entity_scope="away_team_context",
        classification="direct",
        value_type="integer",
        unit="seconds",
        source_refs=("away_injury_freshness_seconds",),
        transformation_definition="direct_copy(row.away_injury_freshness_seconds)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer seconds between away injury availability and decision cutoff",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.home_availability_limited_count",
        feature_name="Home Availability Limited Count",
        feature_family="injury_context",
        entity_scope="home_team_context",
        classification="deterministic_derived",
        value_type="integer",
        unit="players",
        source_refs=("predictor_references_json.injuries.home.summary.availability_status_counts.limited",),
        transformation_definition=(
            "count_from_json(row.predictor_references_json, path='injuries.home.summary.availability_status_counts.limited', "
            "default=0 only when home injury evidence exists)"
        ),
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer count of limited home injury statuses",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.home_availability_unavailable_count",
        feature_name="Home Availability Unavailable Count",
        feature_family="injury_context",
        entity_scope="home_team_context",
        classification="deterministic_derived",
        value_type="integer",
        unit="players",
        source_refs=("predictor_references_json.injuries.home.summary.availability_status_counts.unavailable",),
        transformation_definition=(
            "count_from_json(row.predictor_references_json, path='injuries.home.summary.availability_status_counts.unavailable', "
            "default=0 only when home injury evidence exists)"
        ),
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer count of unavailable home injury statuses",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.away_availability_limited_count",
        feature_name="Away Availability Limited Count",
        feature_family="injury_context",
        entity_scope="away_team_context",
        classification="deterministic_derived",
        value_type="integer",
        unit="players",
        source_refs=("predictor_references_json.injuries.away.summary.availability_status_counts.limited",),
        transformation_definition=(
            "count_from_json(row.predictor_references_json, path='injuries.away.summary.availability_status_counts.limited', "
            "default=0 only when away injury evidence exists)"
        ),
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer count of limited away injury statuses",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.injury.away_availability_unavailable_count",
        feature_name="Away Availability Unavailable Count",
        feature_family="injury_context",
        entity_scope="away_team_context",
        classification="deterministic_derived",
        value_type="integer",
        unit="players",
        source_refs=("predictor_references_json.injuries.away.summary.availability_status_counts.unavailable",),
        transformation_definition=(
            "count_from_json(row.predictor_references_json, path='injuries.away.summary.availability_status_counts.unavailable', "
            "default=0 only when away injury evidence exists)"
        ),
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer count of unavailable away injury statuses",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.team_stats.home_freshness_seconds",
        feature_name="Home Team Stats Freshness Seconds",
        feature_family="team_statistics_context",
        entity_scope="home_team_context",
        classification="direct",
        value_type="integer",
        unit="seconds",
        source_refs=("home_team_stats_freshness_seconds",),
        transformation_definition="direct_copy(row.home_team_stats_freshness_seconds)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer seconds between selected home team-stat evidence and decision cutoff",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.team_stats.away_freshness_seconds",
        feature_name="Away Team Stats Freshness Seconds",
        feature_family="team_statistics_context",
        entity_scope="away_team_context",
        classification="direct",
        value_type="integer",
        unit="seconds",
        source_refs=("away_team_stats_freshness_seconds",),
        transformation_definition="direct_copy(row.away_team_stats_freshness_seconds)",
        missingness_policy="unavailable_when_source_evidence_missing",
        expected_range="non-negative integer seconds between selected away team-stat evidence and decision cutoff",
        nullable=True,
    ),
    _feature(
        "feature.sports.nfl.data_quality.point_in_time_safe_flag",
        feature_name="Point In Time Safe Flag",
        feature_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("point_in_time_status",),
        transformation_definition="row.point_in_time_status == 'safe'",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.predictor_outcome_separated_flag",
        feature_name="Predictor Outcome Separated Flag",
        feature_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("predictor_outcome_separation_status",),
        transformation_definition="row.predictor_outcome_separation_status == 'separated'",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.decision_ready_flag",
        feature_name="Decision Ready Flag",
        feature_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("decision_readiness_status",),
        transformation_definition="row.decision_readiness_status == 'ready'",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.missing_required_asset_count",
        feature_name="Missing Required Asset Count",
        feature_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="integer",
        unit="assets",
        source_refs=("missing_required_assets_json",),
        transformation_definition="len(json_list(row.missing_required_assets_json))",
        missingness_policy="required",
        expected_range="non-negative integer count of missing required predictor assets",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.home_injury_present_flag",
        feature_name="Home Injury Evidence Present Flag",
        feature_family="data_quality_context",
        entity_scope="home_team_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("selected_home_injury_timestamp",),
        transformation_definition="bool(row.selected_home_injury_timestamp)",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.away_injury_present_flag",
        feature_name="Away Injury Evidence Present Flag",
        feature_family="data_quality_context",
        entity_scope="away_team_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("selected_away_injury_timestamp",),
        transformation_definition="bool(row.selected_away_injury_timestamp)",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.home_team_stats_present_flag",
        feature_name="Home Team Stats Evidence Present Flag",
        feature_family="data_quality_context",
        entity_scope="home_team_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("home_team_stats_snapshot_id",),
        transformation_definition="bool(row.home_team_stats_snapshot_id)",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
    _feature(
        "feature.sports.nfl.data_quality.away_team_stats_present_flag",
        feature_name="Away Team Stats Evidence Present Flag",
        feature_family="data_quality_context",
        entity_scope="away_team_context",
        classification="deterministic_derived",
        value_type="boolean",
        unit="flag",
        source_refs=("away_team_stats_snapshot_id",),
        transformation_definition="bool(row.away_team_stats_snapshot_id)",
        missingness_policy="required",
        expected_range="0 or 1",
        portability_classification="dataset_quality_context",
    ),
)


def list_feature_definitions(
    *,
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
) -> list[dict[str, Any]]:
    if _normalize_text(dataset_id) != DEFAULT_NFL_HISTORICAL_DATASET_ID:
        return []
    return [definition.as_dict() for definition in _ACTIVE_FEATURE_DEFINITIONS]


def get_feature_definition(
    feature_id: str,
    *,
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
) -> dict[str, Any]:
    if _normalize_text(dataset_id) != DEFAULT_NFL_HISTORICAL_DATASET_ID:
        return {}
    for definition in _ACTIVE_FEATURE_DEFINITIONS:
        if definition.feature_id == _normalize_text(feature_id):
            return definition.as_dict()
    return {}


def list_feature_definition_ids(
    *,
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
) -> list[str]:
    return [item["feature_id"] for item in list_feature_definitions(dataset_id=dataset_id)]


def list_feature_families() -> list[str]:
    return sorted({definition.feature_family for definition in _ACTIVE_FEATURE_DEFINITIONS})


def list_deferred_feature_ids() -> dict[str, list[str]]:
    return {
        "deferred_mathematical_engine_output": list(DEFERRED_MATHEMATICAL_FEATURE_IDS),
        "deferred_unsupported_dataset_fields": list(DEFERRED_UNSUPPORTED_DATASET_FEATURE_IDS),
    }


def dataset_row_identity_components(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "dataset_id": _normalize_text(row.get("dataset_id"), DEFAULT_NFL_HISTORICAL_DATASET_ID),
        "game_id": _normalize_text(row.get("game_id") or row.get("event_id")),
        "market_type": _normalize_text(row.get("market_type")),
        "selection": _normalize_text(row.get("selection")),
        "book": _normalize_text(row.get("book"), "consensus"),
        "decision_cutoff_time": _normalize_text(row.get("decision_cutoff_time")),
    }


def summarize_dataset_row_contexts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    contexts: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, ...]] = set()
    for row in rows:
        identity = dataset_row_identity_components(row)
        key = (
            identity["dataset_id"],
            identity["game_id"],
            identity["market_type"],
            identity["selection"],
            identity["book"],
            identity["decision_cutoff_time"],
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        contexts.append(
            {
                **identity,
                "dataset_row_id": _normalize_text(row.get("dataset_row_id")),
                "decision_context_id": _normalize_text(row.get("decision_context_id")),
                "team_side": _normalize_text(row.get("team_side")),
                "home_team_id": _normalize_text(row.get("home_team_id")),
                "away_team_id": _normalize_text(row.get("away_team_id")),
            }
        )
    return {
        "dataset_row_grain_id": CANONICAL_DATASET_ROW_GRAIN_ID,
        "identity_fields": [
            "dataset_id",
            "game_id",
            "market_type",
            "selection",
            "book",
            "decision_cutoff_time",
        ],
        "context_count": len(contexts),
        "contexts": contexts,
    }


def build_feature_snapshot_context(dataset_row: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(dataset_row)
    context = FeatureSnapshotContext(
        dataset_id=_normalize_text(row.get("dataset_id"), DEFAULT_NFL_HISTORICAL_DATASET_ID),
        batch_id=_normalize_text(row.get("batch_id")),
        dataset_row_id=_normalize_text(row.get("dataset_row_id")),
        decision_context_id=_normalize_text(row.get("decision_context_id")),
        event_id=_normalize_text(row.get("event_id") or row.get("game_id")),
        season=int(row.get("season") or 0),
        week=int(row.get("week") or 0),
        home_team_id=_normalize_text(row.get("home_team_id")),
        away_team_id=_normalize_text(row.get("away_team_id")),
        team_side=_normalize_text(row.get("team_side")),
        market_type=_normalize_text(row.get("market_type")),
        selection=_normalize_text(row.get("selection")),
        book=_normalize_text(row.get("book"), "consensus"),
        scheduled_kickoff_time=_normalize_text(row.get("scheduled_kickoff_time")),
        decision_cutoff_time=_normalize_text(row.get("decision_cutoff_time")),
        cutoff_policy_version=_normalize_text(
            row.get("cutoff_policy_version"),
            HISTORICAL_DATASET_CUTOFF_POLICY_ID,
        ),
        point_in_time_status=_normalize_text(row.get("point_in_time_status")),
        predictor_outcome_separation_status=_normalize_text(row.get("predictor_outcome_separation_status")),
        decision_readiness_status=_normalize_text(row.get("decision_readiness_status")),
        selected_source_row_ids=_load_json_mapping(row.get("selected_source_row_ids_json")),
        source_certification_ids=_load_json_mapping(row.get("source_certification_ids_json")),
        source_alignment_certification_ids=_load_json_mapping(row.get("source_alignment_certification_ids_json")),
        source_lineage_ids=_load_json_mapping(row.get("source_lineage_ids_json")),
        missing_required_assets=tuple(_load_json_list(row.get("missing_required_assets_json"))),
    )
    return context.as_dict()


def build_feature_snapshot_context_id(context: Mapping[str, Any]) -> str:
    return _stable_id(
        "feature_snapshot_context",
        context.get("dataset_id"),
        context.get("batch_id"),
        context.get("dataset_row_id"),
        context.get("decision_context_id"),
        context.get("event_id"),
        context.get("market_type"),
        context.get("selection"),
        context.get("book"),
        context.get("team_side"),
        context.get("decision_cutoff_time"),
    )


def build_feature_value_identity(
    feature_definition: Mapping[str, Any] | FeatureDefinition,
    context: Mapping[str, Any],
) -> str:
    definition = (
        feature_definition.as_dict()
        if isinstance(feature_definition, FeatureDefinition)
        else dict(feature_definition)
    )
    return _stable_id(
        "feature_value",
        definition.get("feature_id"),
        definition.get("feature_version"),
        context.get("dataset_row_id"),
        definition.get("entity_scope"),
        context.get("market_type"),
        context.get("selection"),
        context.get("book"),
        context.get("team_side"),
        context.get("decision_cutoff_time"),
        definition.get("transformation_version"),
    )


def summarize_feature_registry() -> dict[str, Any]:
    definitions = list_feature_definitions()
    by_family: dict[str, int] = {}
    by_classification: dict[str, int] = {}
    for definition in definitions:
        family = str(definition.get("feature_family"))
        classification = str(definition.get("classification"))
        by_family[family] = by_family.get(family, 0) + 1
        by_classification[classification] = by_classification.get(classification, 0) + 1
    return {
        "schema_version": FEATURE_REGISTRY_SCHEMA_VERSION,
        "feature_definition_version": FEATURE_DEFINITION_VERSION,
        "input_dataset_id": DEFAULT_NFL_HISTORICAL_DATASET_ID,
        "dataset_row_grain_id": CANONICAL_DATASET_ROW_GRAIN_ID,
        "feature_snapshot_grain_id": CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID,
        "feature_count": len(definitions),
        "feature_families": by_family,
        "classifications": by_classification,
        "deferred_feature_ids": list_deferred_feature_ids(),
    }


def validate_feature_registry(
    definitions: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    items = [dict(item) for item in (definitions or list_feature_definitions())]
    errors: list[str] = []
    warnings: list[str] = []
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        feature_id = _normalize_text(item.get("feature_id"))
        feature_version = _normalize_text(item.get("feature_version"))
        key = (feature_id, feature_version)
        if key in seen_keys:
            errors.append(f"duplicate_feature_definition:{feature_id}:{feature_version}")
        seen_keys.add(key)
        if _normalize_text(item.get("classification")) not in FEATURE_CLASSIFICATIONS:
            errors.append(f"invalid_classification:{feature_id}")
        if _normalize_text(item.get("value_type")) not in FEATURE_VALUE_TYPES:
            errors.append(f"invalid_value_type:{feature_id}")
        if _normalize_text(item.get("missingness_policy")) not in FEATURE_MISSINGNESS_POLICIES:
            errors.append(f"invalid_missingness_policy:{feature_id}")
        if _normalize_text(item.get("entity_scope")) not in FEATURE_ENTITY_SCOPES:
            errors.append(f"invalid_entity_scope:{feature_id}")
        if _normalize_text(item.get("dataset_grain_compatibility")) != CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID:
            errors.append(f"invalid_dataset_grain_compatibility:{feature_id}")
        if _normalize_text(item.get("cutoff_semantics")) != DEFAULT_CUTOFF_SEMANTICS:
            errors.append(f"invalid_cutoff_semantics:{feature_id}")
        refs = tuple(
            _normalize_text(value)
            for value in item.get("source_dataset_field_refs") or ()
            if _normalize_text(value)
        )
        if not refs:
            errors.append(f"missing_source_refs:{feature_id}")
        for field_ref in refs:
            root = _split_root(field_ref)
            if root not in ACTIVE_DATASET_FIELD_ROOTS:
                errors.append(f"unsupported_source_root:{feature_id}:{field_ref}")
            if root in OUTCOME_FIELD_NAMES or any(root.startswith(prefix) for prefix in OUTCOME_FIELD_PREFIXES):
                errors.append(f"predictor_outcome_leakage:{feature_id}:{field_ref}")
            if root in RAW_SOURCE_FIELD_MARKERS:
                errors.append(f"raw_source_reread_reference:{feature_id}:{field_ref}")
        if _normalize_text(item.get("classification")) == "deferred_mathematical_engine_output":
            warnings.append(f"deferred_math_definition:{feature_id}")
    return {
        "ok": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


__all__ = [
    "ACTIVE_FEATURE_FAMILIES",
    "CANONICAL_DATASET_ROW_GRAIN_ID",
    "CANONICAL_FEATURE_REGISTRY_DOC",
    "CANONICAL_FEATURE_SNAPSHOT_CONTRACT_DOC",
    "CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID",
    "CANONICAL_FEATURE_STORE_ARCHITECTURE_DOC",
    "CANONICAL_FEATURE_STORE_CONTRACT_DOC",
    "DEFAULT_CUTOFF_SEMANTICS",
    "DEFAULT_NFL_HISTORICAL_DATASET_ID",
    "DEFERRED_MATHEMATICAL_FEATURE_IDS",
    "DEFERRED_UNSUPPORTED_DATASET_FEATURE_IDS",
    "FEATURE_CLASSIFICATIONS",
    "FEATURE_DEFINITION_VERSION",
    "FEATURE_ENTITY_SCOPES",
    "FEATURE_MISSINGNESS_POLICIES",
    "FEATURE_REGISTRY_SCHEMA_VERSION",
    "FEATURE_SNAPSHOT_TRANSFORMATION_VERSION",
    "FEATURE_VALUE_TYPES",
    "FeatureDefinition",
    "FeatureSnapshotContext",
    "build_feature_snapshot_context",
    "build_feature_snapshot_context_id",
    "build_feature_value_identity",
    "dataset_row_identity_components",
    "get_feature_definition",
    "list_deferred_feature_ids",
    "list_feature_definition_ids",
    "list_feature_definitions",
    "list_feature_families",
    "summarize_dataset_row_contexts",
    "summarize_feature_registry",
    "validate_feature_registry",
]
