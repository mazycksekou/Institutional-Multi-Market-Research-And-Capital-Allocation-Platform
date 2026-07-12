from __future__ import annotations

"""Reusable mathematical engine population for the certified NFL feature layer.

This module owns the first deterministic math-engine layer above the certified
feature snapshots. It reads only certified feature evidence, computes reusable
math outputs, persists a queryable math-engine batch, and advances the
associated research asset through certification and lifecycle owners without
creating a parallel framework.
"""

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.core.math_utils import (
    american_to_implied_probability,
    decimal_to_implied_probability,
    fair_decimal_odds_from_probability,
    implied_probability_to_american,
)
from src.core.model_probability import calculate_confidence_score, get_confidence_grade
from src.data.data_paths import get_runtime_data_path
from src.data.feature_registry import (
    CANONICAL_FEATURE_SNAPSHOT_GRAIN_ID,
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
    FEATURE_REGISTRY_SCHEMA_VERSION,
    FEATURE_SNAPSHOT_BATCH_KIND,
    FEATURE_SNAPSHOT_ROW_KIND,
    build_feature_snapshot_population_dashboard_snapshot,
    list_feature_definition_ids,
)
from src.data.historical_research_asset_certification_runtime import (
    HistoricalResearchAssetCertificationRuntime,
    ResearchAssetCertificationContract,
    build_historical_dataset_certification_row,
)
from src.data.historical_research_database import HISTORICAL_DATASET_CUTOFF_POLICY_ID
from src.data.research_asset_lifecycle_runtime import (
    ResearchAssetIdentityContract,
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
    build_time_entity_alignment_certification,
    build_time_entity_alignment_certification_row,
    validate_research_asset_identity_contract,
    validate_time_entity_alignment_certification_row,
)
from src.data.validation import validate_dataset_rows
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine
from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE


MATH_ENGINE_POPULATION_SCHEMA_VERSION = "src.data.math_engine_population.v1"
MATH_ENGINE_DEFINITION_VERSION = "phase5.2.math_engine_definitions.v1"
MATH_ENGINE_TRANSFORMATION_VERSION = "phase5.2.math_engine_population.v1"
MATH_ENGINE_OUTPUT_NAMESPACE = "math.sports.nfl"
DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID = "math.sports.nfl.reusable_mathematical_engines"
DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME = "Reusable Mathematical Engines"
DEFAULT_MATH_ENGINE_STORAGE_PATH = get_runtime_data_path("math_engine_population", "canonical_data.sqlite")
DEFAULT_MATH_ENGINE_DATASET_ID = "dataset.sports.nfl.math_engine_snapshots"
DEFAULT_MATH_ENGINE_DATASET_NAME = "nfl_math_engine_snapshots"
DEFAULT_MATH_ENGINE_OWNER = "src.data.math_engine_population"
DEFAULT_MATH_ENGINE_PROVIDER = "repository"
DEFAULT_MATH_ENGINE_SOURCE_NAME = "feature_snapshot_population"
DEFAULT_MATH_ENGINE_SOURCE_TYPE = "feature_snapshot_population"
DEFAULT_MATH_ENGINE_SOURCE_KEY = "feature_snapshot_population"
DEFAULT_MATH_ENGINE_MARKET = "sports:nfl"
DEFAULT_MATH_ENGINE_MARKET_TYPE = "math_engine"
DEFAULT_MATH_ENGINE_ASSET_CLASS = "math"
DEFAULT_MATH_ENGINE_PROFILE_ID = "sports:nfl"
DEFAULT_MATH_ENGINE_ENGINE_OWNER = "src.core"
DEFAULT_MATH_ENGINE_PORTABILITY_CLASSIFICATION = "cross_market_math_engine"
CANONICAL_MATH_ENGINE_SNAPSHOT_GRAIN_ID = "dataset.sports.nfl.math_engine_snapshot.dataset_row_scope.v1"
MATH_ENGINE_BATCH_KIND = "math_engine_population_summary"
MATH_ENGINE_ROW_KIND = "math_engine_value"
MATH_ENGINE_SUMMARY_ROW_KIND = "dataset_summary"

MATH_ENGINE_ALLOWED_CLASSIFICATIONS = {
    "direct",
    "deterministic_derived",
    "deferred_mathematical_engine_output",
}
MATH_ENGINE_ALLOWED_VALUE_TYPES = {
    "boolean",
    "float",
    "integer",
    "string",
    "timestamp",
}
MATH_ENGINE_ALLOWED_MISSINGNESS_POLICIES = {
    "required",
    "nullable",
    "unavailable",
    "not_applicable",
    "invalid_source",
    "unsupported_context",
}
MATH_ENGINE_ALLOWED_ENTITY_SCOPES = {
    "event",
    "market_context",
    "data_quality_context",
}
MATH_ENGINE_REQUIRED_INPUT_SCOPES = {
    "feature.",
}


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        result = float(value)
        if math.isnan(result) or math.isinf(result):
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
    return parsed.replace(microsecond=0)


def _to_iso8601_utc(value: Any) -> str:
    parsed = _parse_iso(value)
    if parsed is None:
        return _normalize_text(value)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _feature_value(row: Mapping[str, Any]) -> Any:
    value_json = row.get("feature_value_json")
    if value_json not in (None, ""):
        try:
            return json.loads(str(value_json))
        except json.JSONDecodeError:
            pass
    if row.get("feature_value_boolean") not in (None, ""):
        return bool(_normalize_int(row.get("feature_value_boolean"), 0))
    if row.get("feature_value_number") not in (None, ""):
        number = _normalize_float(row.get("feature_value_number"), 0.0)
        value_type = _normalize_text(row.get("value_type")).lower()
        if value_type == "integer":
            return int(round(number))
        return number
    text = row.get("feature_value_text")
    if text not in (None, ""):
        return _normalize_text(text)
    return None


def _feature_missingness(row: Mapping[str, Any]) -> str:
    return _normalize_text(row.get("feature_missingness_state"), "missing_required")


def _feature_freshness_value(row: Mapping[str, Any]) -> float | int | str | None:
    if "freshness_seconds" in _normalize_text(row.get("feature_id")):
        if row.get("feature_value_number") not in (None, ""):
            return _normalize_int(row.get("feature_value_number"), 0)
    value = row.get("feature_value_number")
    if value not in (None, ""):
        return _normalize_float(value, 0.0)
    return _feature_value(row)


@dataclass(slots=True, frozen=True)
class MathEngineDefinition:
    engine_id: str
    engine_name: str
    engine_family: str
    output_feature_id: str
    entity_scope: str
    dataset_grain_compatibility: str
    engine_version: str
    classification: str
    value_type: str
    unit: str
    nullable: bool
    missingness_policy: str
    input_feature_ids: tuple[str, ...]
    transformation_definition: str
    transformation_version: str
    cutoff_semantics: str
    point_in_time_constraints: tuple[str, ...]
    expected_range: str
    allowed_values: tuple[str, ...]
    engine_owner: str = DEFAULT_MATH_ENGINE_ENGINE_OWNER
    lifecycle_state: str = "contract_ready"
    certification_state: str = "definition_only"
    portability_classification: str = DEFAULT_MATH_ENGINE_PORTABILITY_CLASSIFICATION
    lineage_requirements: tuple[str, ...] = (
        "dataset_id",
        "batch_id",
        "dataset_row_id",
        "decision_context_id",
        "decision_cutoff_time",
        "source_feature_snapshot_ids_json",
        "source_feature_lineage_ids_json",
        "source_feature_certification_ids_json",
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "engine_id", _normalize_text(self.engine_id))
        object.__setattr__(self, "engine_name", _normalize_text(self.engine_name))
        object.__setattr__(self, "engine_family", _normalize_text(self.engine_family))
        object.__setattr__(self, "output_feature_id", _normalize_text(self.output_feature_id))
        object.__setattr__(self, "entity_scope", _normalize_text(self.entity_scope))
        object.__setattr__(self, "dataset_grain_compatibility", _normalize_text(self.dataset_grain_compatibility))
        object.__setattr__(self, "engine_version", _normalize_text(self.engine_version))
        object.__setattr__(self, "classification", _normalize_text(self.classification))
        object.__setattr__(self, "value_type", _normalize_text(self.value_type))
        object.__setattr__(self, "unit", _normalize_text(self.unit))
        object.__setattr__(self, "missingness_policy", _normalize_text(self.missingness_policy))
        object.__setattr__(self, "input_feature_ids", tuple(_normalize_text(value) for value in self.input_feature_ids if _normalize_text(value)))
        object.__setattr__(self, "transformation_definition", _normalize_text(self.transformation_definition))
        object.__setattr__(self, "transformation_version", _normalize_text(self.transformation_version))
        object.__setattr__(self, "cutoff_semantics", _normalize_text(self.cutoff_semantics))
        object.__setattr__(self, "point_in_time_constraints", tuple(_normalize_text(value) for value in self.point_in_time_constraints if _normalize_text(value)))
        object.__setattr__(self, "expected_range", _normalize_text(self.expected_range))
        object.__setattr__(self, "allowed_values", tuple(_normalize_text(value) for value in self.allowed_values if _normalize_text(value)))
        object.__setattr__(self, "engine_owner", _normalize_text(self.engine_owner, DEFAULT_MATH_ENGINE_ENGINE_OWNER))
        object.__setattr__(self, "lifecycle_state", _normalize_text(self.lifecycle_state))
        object.__setattr__(self, "certification_state", _normalize_text(self.certification_state))
        object.__setattr__(self, "portability_classification", _normalize_text(self.portability_classification, DEFAULT_MATH_ENGINE_PORTABILITY_CLASSIFICATION))
        object.__setattr__(self, "lineage_requirements", tuple(_normalize_text(value) for value in self.lineage_requirements if _normalize_text(value)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_family": self.engine_family,
            "output_feature_id": self.output_feature_id,
            "entity_scope": self.entity_scope,
            "dataset_grain_compatibility": self.dataset_grain_compatibility,
            "engine_version": self.engine_version,
            "classification": self.classification,
            "value_type": self.value_type,
            "unit": self.unit,
            "nullable": self.nullable,
            "missingness_policy": self.missingness_policy,
            "input_feature_ids": list(self.input_feature_ids),
            "transformation_definition": self.transformation_definition,
            "transformation_version": self.transformation_version,
            "cutoff_semantics": self.cutoff_semantics,
            "point_in_time_constraints": list(self.point_in_time_constraints),
            "expected_range": self.expected_range,
            "allowed_values": list(self.allowed_values),
            "engine_owner": self.engine_owner,
            "lifecycle_state": self.lifecycle_state,
            "certification_state": self.certification_state,
            "portability_classification": self.portability_classification,
            "lineage_requirements": list(self.lineage_requirements),
        }


@dataclass(slots=True, frozen=True)
class MathEngineSnapshotContext:
    dataset_id: str
    batch_id: str
    dataset_row_id: str
    decision_context_id: str
    feature_context_id: str
    event_id: str
    season: int
    week: int
    home_team_id: str
    away_team_id: str
    team_side: str
    target_team_id: str
    opponent_team_id: str
    home_team: str
    away_team: str
    market_type: str
    selection: str
    book: str
    scheduled_kickoff_time: str
    decision_cutoff_time: str
    cutoff_policy_version: str
    point_in_time_status: str
    predictor_outcome_separation_status: str
    decision_readiness_status: str
    source_feature_dataset_id: str
    source_feature_dataset_name: str
    source_feature_batch_id: str
    source_feature_version_id: str
    source_feature_certification_id: str
    source_feature_dataset_certification_id: str
    source_feature_population_summary_id: str
    source_feature_evidence_package_id: str
    source_feature_batch_lineage_id: str
    source_feature_row_count: int
    source_feature_snapshot_count: int
    source_feature_definition_count: int
    source_feature_ids: Mapping[str, Any]
    source_feature_snapshot_ids: Mapping[str, Any]
    source_feature_lineage_ids: Mapping[str, Any]
    source_feature_certification_ids: Mapping[str, Any]
    source_feature_dataset_certification_ids: Mapping[str, Any]
    source_feature_alignment_certification_ids: Mapping[str, Any]
    source_feature_missingness: Mapping[str, Any]
    source_feature_freshness: Mapping[str, Any]
    source_feature_value_types: Mapping[str, Any]
    source_feature_values: Mapping[str, Any]
    missing_required_assets: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "batch_id": self.batch_id,
            "dataset_row_id": self.dataset_row_id,
            "decision_context_id": self.decision_context_id,
            "feature_context_id": self.feature_context_id,
            "event_id": self.event_id,
            "season": self.season,
            "week": self.week,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "team_side": self.team_side,
            "target_team_id": self.target_team_id,
            "opponent_team_id": self.opponent_team_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "market_type": self.market_type,
            "selection": self.selection,
            "book": self.book,
            "scheduled_kickoff_time": self.scheduled_kickoff_time,
            "decision_cutoff_time": self.decision_cutoff_time,
            "cutoff_policy_version": self.cutoff_policy_version,
            "point_in_time_status": self.point_in_time_status,
            "predictor_outcome_separation_status": self.predictor_outcome_separation_status,
            "decision_readiness_status": self.decision_readiness_status,
            "source_feature_dataset_id": self.source_feature_dataset_id,
            "source_feature_dataset_name": self.source_feature_dataset_name,
            "source_feature_batch_id": self.source_feature_batch_id,
            "source_feature_version_id": self.source_feature_version_id,
            "source_feature_certification_id": self.source_feature_certification_id,
            "source_feature_dataset_certification_id": self.source_feature_dataset_certification_id,
            "source_feature_population_summary_id": self.source_feature_population_summary_id,
            "source_feature_evidence_package_id": self.source_feature_evidence_package_id,
            "source_feature_batch_lineage_id": self.source_feature_batch_lineage_id,
            "source_feature_row_count": self.source_feature_row_count,
            "source_feature_snapshot_count": self.source_feature_snapshot_count,
            "source_feature_definition_count": self.source_feature_definition_count,
            "source_feature_ids": dict(self.source_feature_ids),
            "source_feature_snapshot_ids": dict(self.source_feature_snapshot_ids),
            "source_feature_lineage_ids": dict(self.source_feature_lineage_ids),
            "source_feature_certification_ids": dict(self.source_feature_certification_ids),
            "source_feature_dataset_certification_ids": dict(self.source_feature_dataset_certification_ids),
            "source_feature_alignment_certification_ids": dict(self.source_feature_alignment_certification_ids),
            "source_feature_missingness": dict(self.source_feature_missingness),
            "source_feature_freshness": dict(self.source_feature_freshness),
            "source_feature_value_types": dict(self.source_feature_value_types),
            "source_feature_values": dict(self.source_feature_values),
            "missing_required_assets": list(self.missing_required_assets),
        }


def _math_engine_definition(
    engine_id: str,
    *,
    engine_name: str,
    engine_family: str,
    entity_scope: str,
    classification: str,
    value_type: str,
    unit: str,
    input_feature_ids: Sequence[str],
    transformation_definition: str,
    expected_range: str,
    allowed_values: Sequence[str] = (),
    nullable: bool = False,
    missingness_policy: str = "required",
    output_feature_id: str | None = None,
) -> MathEngineDefinition:
    return MathEngineDefinition(
        engine_id=engine_id,
        engine_name=engine_name,
        engine_family=engine_family,
        output_feature_id=output_feature_id or engine_id,
        entity_scope=entity_scope,
        dataset_grain_compatibility=CANONICAL_MATH_ENGINE_SNAPSHOT_GRAIN_ID,
        engine_version=MATH_ENGINE_DEFINITION_VERSION,
        classification=classification,
        value_type=value_type,
        unit=unit,
        nullable=nullable,
        missingness_policy=missingness_policy,
        input_feature_ids=tuple(input_feature_ids),
        transformation_definition=transformation_definition,
        transformation_version=MATH_ENGINE_TRANSFORMATION_VERSION,
        cutoff_semantics="inherit feature-snapshot decision_cutoff_time from the certified historical dataset row",
        point_in_time_constraints=(
            "inherit certified feature snapshots only",
            "do not reread raw or normalized source tables",
            "results remain label-only and do not alter predictors",
            "preserve the Phase 5.0 decision cutoff",
        ),
        expected_range=expected_range,
        allowed_values=tuple(allowed_values),
    )


_MATH_ENGINE_DEFINITIONS: tuple[MathEngineDefinition, ...] = (
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.market.american_implied_probability",
        engine_name="American Implied Probability",
        engine_family="market_pricing",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="float",
        unit="probability",
        input_feature_ids=("feature.sports.nfl.market.american_odds",),
        transformation_definition="american_to_implied_probability(feature.sports.nfl.market.american_odds)",
        expected_range="0.0 < p < 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.market.decimal_implied_probability",
        engine_name="Decimal Implied Probability",
        engine_family="market_pricing",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="float",
        unit="probability",
        input_feature_ids=("feature.sports.nfl.market.decimal_odds",),
        transformation_definition="decimal_to_implied_probability(feature.sports.nfl.market.decimal_odds)",
        expected_range="0.0 < p < 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.market.break_even_probability",
        engine_name="Break Even Probability",
        engine_family="market_pricing",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="float",
        unit="probability",
        input_feature_ids=(
            "feature.sports.nfl.market.american_odds",
            "feature.sports.nfl.market.decimal_odds",
        ),
        transformation_definition=(
            "average(american_to_implied_probability(american_odds), "
            "decimal_to_implied_probability(decimal_odds))"
        ),
        expected_range="0.0 < p < 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.market.fair_american_odds",
        engine_name="Fair American Odds",
        engine_family="market_pricing",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="integer",
        unit="american_odds",
        input_feature_ids=(
            "feature.sports.nfl.market.american_odds",
            "feature.sports.nfl.market.decimal_odds",
        ),
        transformation_definition=(
            "implied_probability_to_american("
            "average(american_to_implied_probability(american_odds), "
            "decimal_to_implied_probability(decimal_odds)))"
        ),
        expected_range="fair American odds",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.market.fair_decimal_odds",
        engine_name="Fair Decimal Odds",
        engine_family="market_pricing",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="float",
        unit="decimal_odds",
        input_feature_ids=(
            "feature.sports.nfl.market.american_odds",
            "feature.sports.nfl.market.decimal_odds",
        ),
        transformation_definition=(
            "fair_decimal_odds_from_probability("
            "average(american_to_implied_probability(american_odds), "
            "decimal_to_implied_probability(decimal_odds)))"
        ),
        expected_range="decimal odds greater than 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.market.odds_consistency_delta",
        engine_name="Odds Consistency Delta",
        engine_family="market_pricing",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="float",
        unit="probability",
        input_feature_ids=(
            "feature.sports.nfl.market.american_odds",
            "feature.sports.nfl.market.decimal_odds",
        ),
        transformation_definition=(
            "abs(american_to_implied_probability(american_odds) - "
            "decimal_to_implied_probability(decimal_odds))"
        ),
        expected_range="0.0 <= delta <= 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.data_quality.score",
        engine_name="Data Quality Score",
        engine_family="data_quality",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="float",
        unit="score",
        input_feature_ids=(
            "feature.sports.nfl.data_quality.point_in_time_safe_flag",
            "feature.sports.nfl.data_quality.predictor_outcome_separated_flag",
            "feature.sports.nfl.data_quality.decision_ready_flag",
            "feature.sports.nfl.data_quality.missing_required_asset_count",
            "feature.sports.nfl.data_quality.home_injury_present_flag",
            "feature.sports.nfl.data_quality.away_injury_present_flag",
            "feature.sports.nfl.data_quality.home_team_stats_present_flag",
            "feature.sports.nfl.data_quality.away_team_stats_present_flag",
            "feature.sports.nfl.market.odds_freshness_seconds",
            "feature.sports.nfl.weather.freshness_seconds",
            "feature.sports.nfl.injury.home_freshness_seconds",
            "feature.sports.nfl.injury.away_freshness_seconds",
            "feature.sports.nfl.team_stats.home_freshness_seconds",
            "feature.sports.nfl.team_stats.away_freshness_seconds",
        ),
        transformation_definition=(
            "weighted completeness score from point-in-time safety, "
            "predictor/outcome separation, decision readiness, asset presence, "
            "and normalized freshness penalties"
        ),
        expected_range="0.0 <= score <= 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.data_quality.confidence_score",
        engine_name="Confidence Score",
        engine_family="confidence",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="float",
        unit="score",
        input_feature_ids=(
            "feature.sports.nfl.data_quality.point_in_time_safe_flag",
            "feature.sports.nfl.data_quality.predictor_outcome_separated_flag",
            "feature.sports.nfl.data_quality.decision_ready_flag",
            "feature.sports.nfl.data_quality.missing_required_asset_count",
            "feature.sports.nfl.data_quality.home_injury_present_flag",
            "feature.sports.nfl.data_quality.away_injury_present_flag",
            "feature.sports.nfl.data_quality.home_team_stats_present_flag",
            "feature.sports.nfl.data_quality.away_team_stats_present_flag",
            "feature.sports.nfl.market.odds_freshness_seconds",
            "feature.sports.nfl.weather.freshness_seconds",
            "feature.sports.nfl.injury.home_freshness_seconds",
            "feature.sports.nfl.injury.away_freshness_seconds",
            "feature.sports.nfl.team_stats.home_freshness_seconds",
            "feature.sports.nfl.team_stats.away_freshness_seconds",
            "feature.sports.nfl.market.american_odds",
            "feature.sports.nfl.market.decimal_odds",
        ),
        transformation_definition=(
            "calculate_confidence_score(data_quality_score, "
            "probability_volatility=odds_consistency_delta)"
        ),
        expected_range="0.0 <= score <= 1.0",
    ),
    _math_engine_definition(
        f"{MATH_ENGINE_OUTPUT_NAMESPACE}.data_quality.confidence_grade",
        engine_name="Confidence Grade",
        engine_family="confidence",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="string",
        unit="grade",
        input_feature_ids=(
            "feature.sports.nfl.data_quality.point_in_time_safe_flag",
            "feature.sports.nfl.data_quality.predictor_outcome_separated_flag",
            "feature.sports.nfl.data_quality.decision_ready_flag",
            "feature.sports.nfl.data_quality.missing_required_asset_count",
            "feature.sports.nfl.data_quality.home_injury_present_flag",
            "feature.sports.nfl.data_quality.away_injury_present_flag",
            "feature.sports.nfl.data_quality.home_team_stats_present_flag",
            "feature.sports.nfl.data_quality.away_team_stats_present_flag",
            "feature.sports.nfl.market.odds_freshness_seconds",
            "feature.sports.nfl.weather.freshness_seconds",
            "feature.sports.nfl.injury.home_freshness_seconds",
            "feature.sports.nfl.injury.away_freshness_seconds",
            "feature.sports.nfl.team_stats.home_freshness_seconds",
            "feature.sports.nfl.team_stats.away_freshness_seconds",
            "feature.sports.nfl.market.american_odds",
            "feature.sports.nfl.market.decimal_odds",
        ),
        transformation_definition="get_confidence_grade(confidence_score)",
        expected_range="letter grade A, B, C, D, or F",
        allowed_values=("A", "B", "C", "D", "F"),
    ),
)


def list_math_engine_definitions() -> list[dict[str, Any]]:
    return [definition.as_dict() for definition in _MATH_ENGINE_DEFINITIONS]


def list_math_engine_definition_ids() -> list[str]:
    return [definition.engine_id for definition in _MATH_ENGINE_DEFINITIONS]


def get_math_engine_definition(engine_id: str) -> dict[str, Any]:
    target = _normalize_text(engine_id)
    for definition in _MATH_ENGINE_DEFINITIONS:
        if definition.engine_id == target:
            return definition.as_dict()
    raise KeyError(f"Unknown math engine definition: {engine_id}")


def summarize_math_engine_registry() -> dict[str, Any]:
    family_counts = dict(Counter(definition.engine_family for definition in _MATH_ENGINE_DEFINITIONS))
    classification_counts = dict(Counter(definition.classification for definition in _MATH_ENGINE_DEFINITIONS))
    value_type_counts = dict(Counter(definition.value_type for definition in _MATH_ENGINE_DEFINITIONS))
    return {
        "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "definition_version": MATH_ENGINE_DEFINITION_VERSION,
        "transformation_version": MATH_ENGINE_TRANSFORMATION_VERSION,
        "definition_count": len(_MATH_ENGINE_DEFINITIONS),
        "engine_ids": list_math_engine_definition_ids(),
        "family_counts": family_counts,
        "classification_counts": classification_counts,
        "value_type_counts": value_type_counts,
    }


def validate_math_engine_registry() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_engine_ids: set[str] = set()
    seen_output_ids: set[str] = set()
    for definition in _MATH_ENGINE_DEFINITIONS:
        if definition.engine_id in seen_engine_ids:
            errors.append(f"duplicate_engine_id:{definition.engine_id}")
        seen_engine_ids.add(definition.engine_id)
        if definition.output_feature_id in seen_output_ids:
            errors.append(f"duplicate_output_feature_id:{definition.output_feature_id}")
        seen_output_ids.add(definition.output_feature_id)
        if not definition.engine_id.startswith(MATH_ENGINE_OUTPUT_NAMESPACE):
            errors.append(f"invalid_engine_id_namespace:{definition.engine_id}")
        if definition.classification not in MATH_ENGINE_ALLOWED_CLASSIFICATIONS:
            errors.append(f"invalid_classification:{definition.engine_id}:{definition.classification}")
        if definition.value_type not in MATH_ENGINE_ALLOWED_VALUE_TYPES:
            errors.append(f"invalid_value_type:{definition.engine_id}:{definition.value_type}")
        if definition.missingness_policy not in MATH_ENGINE_ALLOWED_MISSINGNESS_POLICIES:
            errors.append(f"invalid_missingness_policy:{definition.engine_id}:{definition.missingness_policy}")
        if definition.entity_scope not in MATH_ENGINE_ALLOWED_ENTITY_SCOPES:
            errors.append(f"invalid_entity_scope:{definition.engine_id}:{definition.entity_scope}")
        if not definition.input_feature_ids:
            errors.append(f"missing_inputs:{definition.engine_id}")
        for feature_id in definition.input_feature_ids:
            if not any(feature_id.startswith(prefix) for prefix in MATH_ENGINE_REQUIRED_INPUT_SCOPES):
                errors.append(f"non_feature_input:{definition.engine_id}:{feature_id}")
    return {
        "ok": not errors,
        "status": "validated" if not errors else "rejected",
        "definition_count": len(_MATH_ENGINE_DEFINITIONS),
        "errors": list(dict.fromkeys(errors)),
        "warnings": warnings,
        "registry": summarize_math_engine_registry(),
    }


def _required_row_fields() -> tuple[str, ...]:
    return (
        "dataset_id",
        "dataset_name",
        "owner",
        "sport",
        "math_pack",
        "storage_location",
        "readiness",
        "update_frequency",
        "validation_state",
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
        "batch_id",
        "snapshot_kind",
        "math_pack_version",
        "source_feature_dataset_id",
        "source_feature_dataset_name",
        "source_feature_batch_id",
        "source_feature_version_id",
        "source_feature_certification_id",
        "source_feature_dataset_certification_id",
        "source_feature_population_summary_id",
        "source_feature_evidence_package_id",
        "source_feature_batch_lineage_id",
        "source_feature_row_count",
        "source_feature_snapshot_count",
        "source_feature_definition_count",
        "dataset_row_id",
        "decision_context_id",
        "feature_context_id",
        "event_id",
        "game_id",
        "season",
        "week",
        "home_team_id",
        "away_team_id",
        "home_team",
        "away_team",
        "selection",
        "book",
        "scheduled_kickoff_time",
        "decision_cutoff_time",
        "cutoff_policy_version",
        "point_in_time_status",
        "predictor_outcome_separation_status",
        "decision_readiness_status",
        "engine_id",
        "engine_name",
        "engine_family",
        "engine_version",
        "classification",
        "value_type",
        "unit",
        "engine_owner",
        "entity_scope",
        "dataset_grain_compatibility",
        "transformation_version",
        "missingness_policy",
        "engine_context_id",
        "output_feature_id",
        "required_input_feature_ids_json",
        "input_feature_count",
        "engine_value_json",
        "engine_missingness_state",
        "engine_definition_json",
        "engine_context_json",
        "math_engine_snapshot_grain_id",
        "math_engine_registry_schema_version",
        "engine_lineage_id",
        "engine_evidence_id",
        "source_feature_ids_json",
        "source_feature_snapshot_ids_json",
        "source_feature_lineage_ids_json",
        "source_feature_certification_ids_json",
        "source_feature_dataset_certification_ids_json",
        "source_feature_alignment_certification_ids_json",
        "source_feature_missingness_json",
        "source_feature_freshness_json",
        "source_feature_value_types_json",
        "source_feature_values_json",
        "missing_required_assets_json",
        "evidence_package_id",
        "record_count",
        "engine_count",
        "engine_values_json",
        "summary_json",
        "payload_json",
    )


def validate_math_engine_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    base = validate_dataset_rows(rows, required_fields=_required_row_fields())
    missing_rows = list(base.get("missing_rows", []))
    missing_fields = [field for row in missing_rows for field in row.get("missing_fields", [])]
    duplicate_snapshot_ids: list[str] = []
    seen_snapshot_ids: set[str] = set()
    duplicate_engine_keys: list[str] = []
    seen_engine_keys: set[str] = set()
    for row in rows:
        snapshot_id = _normalize_text(row.get("snapshot_id"))
        if snapshot_id:
            if snapshot_id in seen_snapshot_ids and snapshot_id not in duplicate_snapshot_ids:
                duplicate_snapshot_ids.append(snapshot_id)
            seen_snapshot_ids.add(snapshot_id)
        engine_key = "|".join(
            [
                _normalize_text(row.get("dataset_row_id")),
                _normalize_text(row.get("decision_context_id")),
                _normalize_text(row.get("engine_id")),
                _normalize_text(row.get("scheduled_kickoff_time")),
                _normalize_text(row.get("decision_cutoff_time")),
            ]
        )
        if engine_key in seen_engine_keys and engine_key not in duplicate_engine_keys:
            duplicate_engine_keys.append(engine_key)
        seen_engine_keys.add(engine_key)

    required_fields_missing = list(dict.fromkeys(missing_fields))
    errors = list(dict.fromkeys(
        [
            *required_fields_missing,
            *[f"duplicate_snapshot_id:{value}" for value in duplicate_snapshot_ids],
            *[f"duplicate_engine_key:{value}" for value in duplicate_engine_keys],
        ]
    ))
    return {
        "ok": not errors,
        "status": "validated" if not errors else "rejected",
        "row_count": len(rows),
        "error_count": len(errors),
        "warning_count": int(base.get("warning_count") or 0),
        "missing_rows": missing_rows,
        "missing_fields": required_fields_missing,
        "duplicate_snapshot_ids": duplicate_snapshot_ids,
        "duplicate_engine_keys": duplicate_engine_keys,
        "errors": errors,
        "base_validation": base,
    }


def _select_feature_population_snapshot(
    storage: LocalStorageEngine,
    *,
    dataset_id: str,
    batch_id: str | None = None,
) -> dict[str, Any]:
    if not storage.table_exists("feature_snapshots"):
        raise ValueError("feature snapshots table is missing")
    where = "dataset_id = ? AND snapshot_kind = ?"
    params: list[Any] = [dataset_id, FEATURE_SNAPSHOT_BATCH_KIND]
    if batch_id:
        where += " AND batch_id = ?"
        params.append(batch_id)
    summaries = storage.fetch(
        "feature_snapshots",
        where=where,
        params=params,
        order_by="created_at DESC, snapshot_id DESC",
        limit=1,
    )
    if not summaries:
        raise ValueError("no certified feature snapshot batch is available")
    summary = dict(summaries[0])
    selected_batch_id = _normalize_text(summary.get("batch_id"))
    rows = storage.fetch(
        "feature_snapshots",
        where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
        params=[dataset_id, selected_batch_id, FEATURE_SNAPSHOT_ROW_KIND],
        order_by="dataset_row_id ASC, decision_context_id ASC, feature_id ASC, snapshot_id ASC",
    )
    if not rows:
        raise ValueError("certified feature rows are missing for the selected batch")
    normalized_rows = [dict(row) for row in rows]
    summary["feature_rows"] = normalized_rows
    summary["feature_snapshot_rows"] = normalized_rows
    return summary


def _group_feature_rows(
    feature_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        if _normalize_text(row.get("snapshot_kind")) != FEATURE_SNAPSHOT_ROW_KIND:
            continue
        grouped[(
            _normalize_text(row.get("dataset_row_id")),
            _normalize_text(row.get("decision_context_id")),
        )].append(dict(row))
    contexts: list[dict[str, Any]] = []
    for (dataset_row_id, decision_context_id), rows in sorted(grouped.items()):
        rows.sort(key=lambda row: (_normalize_text(row.get("feature_id")), _normalize_text(row.get("snapshot_id"))))
        contexts.append(
            {
                "dataset_row_id": dataset_row_id,
                "decision_context_id": decision_context_id,
                "feature_rows": rows,
            }
        )
    return contexts


def _build_feature_lookups(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return { _normalize_text(row.get("feature_id")): dict(row) for row in rows if _normalize_text(row.get("feature_id")) }


def _engine_freshness_map(feature_lookup: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    freshness: dict[str, Any] = {}
    for feature_id, row in feature_lookup.items():
        if feature_id.endswith("freshness_seconds") or feature_id.endswith("freshness_seconds_flag"):
            freshness[feature_id] = _feature_freshness_value(row)
    return freshness


def _engine_input_values(definition: MathEngineDefinition, feature_lookup: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    for feature_id in definition.input_feature_ids:
        row = feature_lookup.get(feature_id)
        if row is None:
            inputs[feature_id] = None
            continue
        inputs[feature_id] = _feature_value(row)
    return inputs


def _engine_missingness(definition: MathEngineDefinition, inputs: Mapping[str, Any], feature_lookup: Mapping[str, Mapping[str, Any]]) -> tuple[Any, str, str]:
    missing_inputs = [feature_id for feature_id, value in inputs.items() if value in (None, "")]
    if missing_inputs:
        return None, "missing_required", f"missing feature inputs: {', '.join(missing_inputs)}"

    def _required(feature_id: str) -> Any:
        return inputs[feature_id]

    american_odds = _required("feature.sports.nfl.market.american_odds") if "feature.sports.nfl.market.american_odds" in inputs else None
    decimal_odds = _required("feature.sports.nfl.market.decimal_odds") if "feature.sports.nfl.market.decimal_odds" in inputs else None

    if definition.engine_id.endswith("american_implied_probability"):
        return american_to_implied_probability(american_odds), "present", ""
    if definition.engine_id.endswith("decimal_implied_probability"):
        return decimal_to_implied_probability(decimal_odds), "present", ""
    if definition.engine_id.endswith("break_even_probability"):
        american_probability = american_to_implied_probability(american_odds)
        decimal_probability = decimal_to_implied_probability(decimal_odds)
        return (american_probability + decimal_probability) / 2.0, "present", ""
    if definition.engine_id.endswith("fair_american_odds"):
        american_probability = american_to_implied_probability(american_odds)
        decimal_probability = decimal_to_implied_probability(decimal_odds)
        break_even = (american_probability + decimal_probability) / 2.0
        return implied_probability_to_american(break_even), "present", ""
    if definition.engine_id.endswith("fair_decimal_odds"):
        american_probability = american_to_implied_probability(american_odds)
        decimal_probability = decimal_to_implied_probability(decimal_odds)
        break_even = (american_probability + decimal_probability) / 2.0
        return fair_decimal_odds_from_probability(break_even), "present", ""
    if definition.engine_id.endswith("odds_consistency_delta"):
        american_probability = american_to_implied_probability(american_odds)
        decimal_probability = decimal_to_implied_probability(decimal_odds)
        return abs(american_probability - decimal_probability), "present", ""

    point_in_time_safe = bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.point_in_time_safe_flag"), 0))
    predictor_outcome_separated = bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.predictor_outcome_separated_flag"), 0))
    decision_ready = bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.decision_ready_flag"), 0))
    missing_required_asset_count = _normalize_int(inputs.get("feature.sports.nfl.data_quality.missing_required_asset_count"), 0)

    presence_flags = [
        bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.home_injury_present_flag"), 0)),
        bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.away_injury_present_flag"), 0)),
        bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.home_team_stats_present_flag"), 0)),
        bool(_normalize_int(inputs.get("feature.sports.nfl.data_quality.away_team_stats_present_flag"), 0)),
    ]
    freshness_values = []
    for feature_id in (
        "feature.sports.nfl.market.odds_freshness_seconds",
        "feature.sports.nfl.weather.freshness_seconds",
        "feature.sports.nfl.injury.home_freshness_seconds",
        "feature.sports.nfl.injury.away_freshness_seconds",
        "feature.sports.nfl.team_stats.home_freshness_seconds",
        "feature.sports.nfl.team_stats.away_freshness_seconds",
    ):
        freshness = inputs.get(feature_id)
        if freshness in (None, ""):
            continue
        seconds = max(0.0, float(_normalize_float(freshness, 0.0)))
        freshness_values.append(max(0.0, 1.0 - min(seconds, 86400.0) / 86400.0))
    freshness_component = sum(freshness_values) / len(freshness_values) if freshness_values else 1.0
    presence_component = sum(1.0 if flag else 0.0 for flag in presence_flags) / len(presence_flags)
    base_component = (
        (1.0 if point_in_time_safe else 0.0)
        + (1.0 if predictor_outcome_separated else 0.0)
        + (1.0 if decision_ready else 0.0)
    ) / 3.0
    missing_penalty = min(0.5, missing_required_asset_count * 0.1)
    data_quality = max(0.0, min(1.0, round(base_component * 0.45 + presence_component * 0.25 + freshness_component * 0.30 - missing_penalty, 4)))

    if definition.engine_id.endswith("data_quality.score"):
        return data_quality, "present", ""
    if definition.engine_id.endswith("confidence_score"):
        american_probability = american_to_implied_probability(american_odds)
        decimal_probability = decimal_to_implied_probability(decimal_odds)
        odds_consistency_delta = abs(american_probability - decimal_probability)
        return calculate_confidence_score(data_quality, probability_volatility=odds_consistency_delta), "present", ""
    if definition.engine_id.endswith("confidence_grade"):
        american_probability = american_to_implied_probability(american_odds)
        decimal_probability = decimal_to_implied_probability(decimal_odds)
        odds_consistency_delta = abs(american_probability - decimal_probability)
        confidence = calculate_confidence_score(data_quality, probability_volatility=odds_consistency_delta)
        return get_confidence_grade(confidence), "present", ""

    return None, "missing_required", "unsupported engine definition"


def build_math_engine_snapshot_context(
    *,
    source_feature_summary: Mapping[str, Any],
    feature_rows: Sequence[Mapping[str, Any]],
    context_rows: Sequence[Mapping[str, Any]],
    batch_id: str,
    math_engine_registry_schema_version: str = MATH_ENGINE_POPULATION_SCHEMA_VERSION,
    math_engine_transformation_version: str = MATH_ENGINE_TRANSFORMATION_VERSION,
) -> MathEngineSnapshotContext:
    if not context_rows:
        raise ValueError("no feature context rows were supplied")
    representative_row = dict(context_rows[0])
    feature_lookup = _build_feature_lookups(context_rows)
    source_feature_ids = {feature_id: feature_id for feature_id in feature_lookup}
    source_feature_snapshot_ids = {feature_id: _normalize_text(row.get("snapshot_id")) for feature_id, row in feature_lookup.items()}
    source_feature_lineage_ids = {feature_id: _normalize_text(row.get("feature_lineage_id")) for feature_id, row in feature_lookup.items()}
    source_feature_certification_ids = {feature_id: _normalize_text(row.get("certification_id")) for feature_id, row in feature_lookup.items()}
    source_feature_dataset_certification_ids = {feature_id: _normalize_text(row.get("dataset_certification_id")) for feature_id, row in feature_lookup.items()}
    source_feature_alignment_certification_ids = {feature_id: _normalize_text(row.get("feature_alignment_certification_id")) for feature_id, row in feature_lookup.items()}
    source_feature_missingness = {feature_id: _feature_missingness(row) for feature_id, row in feature_lookup.items()}
    source_feature_freshness = _engine_freshness_map(feature_lookup)
    source_feature_value_types = {feature_id: _normalize_text(row.get("value_type")) for feature_id, row in feature_lookup.items()}
    source_feature_values = {feature_id: _feature_value(row) for feature_id, row in feature_lookup.items()}
    missing_required_assets = tuple(_load_json_list(source_feature_summary.get("missing_required_assets_json")))
    return MathEngineSnapshotContext(
        dataset_id=_normalize_text(source_feature_summary.get("dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID),
        batch_id=batch_id,
        dataset_row_id=_normalize_text(representative_row.get("dataset_row_id")),
        decision_context_id=_normalize_text(representative_row.get("decision_context_id")),
        feature_context_id=_normalize_text(representative_row.get("feature_context_id")),
        event_id=_normalize_text(representative_row.get("event_id")),
        season=_normalize_int(representative_row.get("season"), 0),
        week=_normalize_int(representative_row.get("week"), 0),
        home_team_id=_normalize_text(representative_row.get("home_team_id")),
        away_team_id=_normalize_text(representative_row.get("away_team_id")),
        team_side=_normalize_text(representative_row.get("team_side")),
        target_team_id=_normalize_text(representative_row.get("target_team_id")),
        opponent_team_id=_normalize_text(representative_row.get("opponent_team_id")),
        home_team=_normalize_text(representative_row.get("home_team")),
        away_team=_normalize_text(representative_row.get("away_team")),
        market_type=_normalize_text(representative_row.get("market_type")),
        selection=_normalize_text(representative_row.get("selection")),
        book=_normalize_text(representative_row.get("book"), "consensus"),
        scheduled_kickoff_time=_to_iso8601_utc(representative_row.get("scheduled_kickoff_time")),
        decision_cutoff_time=_to_iso8601_utc(representative_row.get("decision_cutoff_time")),
        cutoff_policy_version=_normalize_text(representative_row.get("cutoff_policy_version"), HISTORICAL_DATASET_CUTOFF_POLICY_ID),
        point_in_time_status=_normalize_text(representative_row.get("point_in_time_status"), "safe"),
        predictor_outcome_separation_status=_normalize_text(representative_row.get("predictor_outcome_separation_status"), "separated"),
        decision_readiness_status=_normalize_text(representative_row.get("decision_readiness_status"), "decision_ready"),
        source_feature_dataset_id=_normalize_text(source_feature_summary.get("dataset_id"), DEFAULT_NFL_HISTORICAL_DATASET_ID),
        source_feature_dataset_name=_normalize_text(source_feature_summary.get("dataset_name"), DEFAULT_MATH_ENGINE_DATASET_NAME),
        source_feature_batch_id=_normalize_text(source_feature_summary.get("batch_id")),
        source_feature_version_id=_normalize_text(source_feature_summary.get("version_id")),
        source_feature_certification_id=_normalize_text(source_feature_summary.get("certification_id")),
        source_feature_dataset_certification_id=_normalize_text(source_feature_summary.get("dataset_certification_id")),
        source_feature_population_summary_id=_normalize_text(source_feature_summary.get("snapshot_id")),
        source_feature_evidence_package_id=_normalize_text(source_feature_summary.get("evidence_package_id")),
        source_feature_batch_lineage_id=_normalize_text(source_feature_summary.get("lineage_id")),
        source_feature_row_count=_normalize_int(source_feature_summary.get("dataset_row_count"), len(feature_rows)),
        source_feature_snapshot_count=_normalize_int(source_feature_summary.get("feature_snapshot_count"), len(context_rows)),
        source_feature_definition_count=_normalize_int(source_feature_summary.get("feature_definition_count"), len(list_feature_definition_ids())),
        source_feature_ids=source_feature_ids,
        source_feature_snapshot_ids=source_feature_snapshot_ids,
        source_feature_lineage_ids=source_feature_lineage_ids,
        source_feature_certification_ids=source_feature_certification_ids,
        source_feature_dataset_certification_ids=source_feature_dataset_certification_ids,
        source_feature_alignment_certification_ids=source_feature_alignment_certification_ids,
        source_feature_missingness=source_feature_missingness,
        source_feature_freshness=source_feature_freshness,
        source_feature_value_types=source_feature_value_types,
        source_feature_values=source_feature_values,
        missing_required_assets=missing_required_assets,
    )


def build_math_engine_snapshot_context_id(context: MathEngineSnapshotContext | Mapping[str, Any], engine_id: str | None = None) -> str:
    payload = context if isinstance(context, Mapping) else context.as_dict()
    seed = _as_json(payload)
    if engine_id:
        seed = _as_json({"engine_id": engine_id, "context": payload})
    return _stable_id("math_engine_snapshot_context", seed)


def build_math_engine_value_identity(
    engine_definition: Mapping[str, Any] | MathEngineDefinition,
    context: MathEngineSnapshotContext | Mapping[str, Any],
) -> str:
    definition = engine_definition if isinstance(engine_definition, Mapping) else engine_definition.as_dict()
    payload = context.as_dict() if isinstance(context, MathEngineSnapshotContext) else dict(context)
    seed = (
        _normalize_text(definition.get("engine_id") or definition.get("output_feature_id")),
        _normalize_text(definition.get("engine_version"), MATH_ENGINE_DEFINITION_VERSION),
        _normalize_text(payload.get("batch_id")),
        _normalize_text(payload.get("dataset_row_id")),
        _normalize_text(payload.get("decision_context_id")),
        _normalize_text(payload.get("entity_scope")),
        _normalize_text(payload.get("scheduled_kickoff_time")),
        _normalize_text(payload.get("decision_cutoff_time")),
        _normalize_text(definition.get("transformation_version"), MATH_ENGINE_TRANSFORMATION_VERSION),
        _as_json(payload.get("source_feature_snapshot_ids", {})),
        _as_json(payload.get("source_feature_lineage_ids", {})),
        _as_json(payload.get("source_feature_certification_ids", {})),
        _as_json(payload.get("source_feature_dataset_certification_ids", {})),
        _as_json(payload.get("source_feature_alignment_certification_ids", {})),
        _as_json(payload.get("missing_required_assets", [])),
    )
    return _stable_id("math_engine_snapshot", *seed)


def _row_payload_and_values(
    *,
    definition: MathEngineDefinition,
    context: MathEngineSnapshotContext,
    feature_lookup: Mapping[str, Mapping[str, Any]],
    storage_location: str,
    created_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    input_values = _engine_input_values(definition, feature_lookup)
    value, missingness_state, missingness_reason = _engine_missingness(definition, input_values, feature_lookup)
    engine_context = context.as_dict()
    engine_context["engine_id"] = definition.engine_id
    engine_context["engine_name"] = definition.engine_name
    engine_context["engine_family"] = definition.engine_family
    engine_context["engine_version"] = definition.engine_version
    engine_context["output_feature_id"] = definition.output_feature_id
    engine_context["input_values"] = input_values
    engine_context["created_at"] = created_at
    engine_context["source_feature_rows"] = {
        feature_id: {
            "snapshot_id": row.get("snapshot_id"),
            "feature_name": row.get("feature_name"),
            "feature_missingness_state": row.get("feature_missingness_state"),
        }
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }

    if isinstance(value, bool):
        value_json = _as_json(value)
        value_text = None
        value_number = None
        value_boolean = int(value)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        value_json = _as_json(value)
        value_text = None
        value_number = value
        value_boolean = None
    elif value is None:
        value_json = None
        value_text = None
        value_number = None
        value_boolean = None
    else:
        value_json = _as_json(value)
        value_text = _normalize_text(value)
        value_number = None
        value_boolean = None

    source_feature_values = {
        feature_id: _feature_value(row)
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_snapshot_ids = {
        feature_id: _normalize_text(row.get("snapshot_id"))
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_lineage_ids = {
        feature_id: _normalize_text(row.get("feature_lineage_id"))
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_certification_ids = {
        feature_id: _normalize_text(row.get("certification_id"))
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_dataset_certification_ids = {
        feature_id: _normalize_text(row.get("dataset_certification_id"))
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_alignment_certification_ids = {
        feature_id: _normalize_text(row.get("feature_alignment_certification_id"))
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_missingness = {
        feature_id: _feature_missingness(row)
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_value_types = {
        feature_id: _normalize_text(row.get("value_type"))
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_freshness = {
        feature_id: _feature_freshness_value(row)
        for feature_id, row in feature_lookup.items()
        if feature_id in definition.input_feature_ids
    }
    source_feature_ids = {feature_id: feature_id for feature_id in definition.input_feature_ids}

    payload = {
        "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
        "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
        "owner": DEFAULT_MATH_ENGINE_OWNER,
        "sport": "football",
        "math_pack": DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
        "storage_location": _normalize_text(storage_location),
        "readiness": "math_ready",
        "update_frequency": "manual",
        "validation_state": "validated" if missingness_state == "present" else "rejected",
        "status": "certified" if missingness_state == "present" else "blocked",
        "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_MATH_ENGINE_SOURCE_NAME,
        "provider": DEFAULT_MATH_ENGINE_PROVIDER,
        "market": DEFAULT_MATH_ENGINE_MARKET,
        "market_type": DEFAULT_MATH_ENGINE_MARKET_TYPE,
        "asset_class": DEFAULT_MATH_ENGINE_ASSET_CLASS,
        "batch_id": context.batch_id,
        "snapshot_kind": MATH_ENGINE_ROW_KIND,
        "math_pack_version": MATH_ENGINE_TRANSFORMATION_VERSION,
        "source_feature_dataset_id": context.source_feature_dataset_id,
        "source_feature_dataset_name": context.source_feature_dataset_name,
        "source_feature_batch_id": context.source_feature_batch_id,
        "source_feature_version_id": context.source_feature_version_id,
        "source_feature_certification_id": context.source_feature_certification_id,
        "source_feature_dataset_certification_id": context.source_feature_dataset_certification_id,
        "source_feature_population_summary_id": context.source_feature_population_summary_id,
        "source_feature_evidence_package_id": context.source_feature_evidence_package_id,
        "source_feature_batch_lineage_id": context.source_feature_batch_lineage_id,
        "source_feature_row_count": context.source_feature_row_count,
        "source_feature_snapshot_count": context.source_feature_snapshot_count,
        "source_feature_definition_count": context.source_feature_definition_count,
        "dataset_row_id": context.dataset_row_id,
        "decision_context_id": context.decision_context_id,
        "feature_context_id": context.feature_context_id,
        "event_id": context.event_id,
        "game_id": context.event_id,
        "season": context.season,
        "week": context.week,
        "home_team_id": context.home_team_id,
        "away_team_id": context.away_team_id,
        "team_side": context.team_side,
        "target_team_id": context.target_team_id,
        "opponent_team_id": context.opponent_team_id,
        "home_team": context.home_team,
        "away_team": context.away_team,
        "selection": context.selection,
        "book": context.book,
        "scheduled_kickoff_time": context.scheduled_kickoff_time,
        "decision_cutoff_time": context.decision_cutoff_time,
        "cutoff_policy_version": context.cutoff_policy_version,
        "point_in_time_status": context.point_in_time_status,
        "predictor_outcome_separation_status": context.predictor_outcome_separation_status,
        "decision_readiness_status": context.decision_readiness_status,
        "engine_id": definition.engine_id,
        "engine_name": definition.engine_name,
        "engine_family": definition.engine_family,
        "engine_version": definition.engine_version,
        "classification": definition.classification,
        "value_type": definition.value_type,
        "unit": definition.unit,
        "engine_owner": definition.engine_owner,
        "entity_scope": definition.entity_scope,
        "dataset_grain_compatibility": definition.dataset_grain_compatibility,
        "transformation_version": definition.transformation_version,
        "missingness_policy": definition.missingness_policy,
        "engine_context_id": build_math_engine_snapshot_context_id(context, definition.engine_id),
        "output_feature_id": definition.output_feature_id,
        "required_input_feature_ids_json": _as_json(list(definition.input_feature_ids)),
        "input_feature_count": len(definition.input_feature_ids),
        "engine_value_json": value_json,
        "engine_value_text": value_text,
        "engine_value_number": value_number,
        "engine_value_boolean": value_boolean,
        "engine_missingness_state": missingness_state,
        "engine_missingness_reason": missingness_reason,
        "engine_definition_json": _as_json(definition.as_dict()),
        "engine_context_json": _as_json(engine_context),
        "math_engine_snapshot_grain_id": CANONICAL_MATH_ENGINE_SNAPSHOT_GRAIN_ID,
        "math_engine_registry_schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "engine_lineage_id": _stable_id(
            "math_engine_lineage",
            context.batch_id,
            definition.engine_id,
            context.dataset_row_id,
            context.decision_context_id,
            _as_json(source_feature_snapshot_ids),
            _as_json(source_feature_lineage_ids),
            _as_json(source_feature_certification_ids),
        ),
        "engine_evidence_id": _stable_id(
            "math_engine_evidence",
            context.batch_id,
            definition.engine_id,
            context.dataset_row_id,
            context.decision_context_id,
            _as_json(source_feature_snapshot_ids),
            _as_json(source_feature_values),
            _as_json(value_json if value_json is not None else value_text),
            missingness_state,
        ),
        "source_feature_ids_json": _as_json(source_feature_ids),
        "source_feature_snapshot_ids_json": _as_json(source_feature_snapshot_ids),
        "source_feature_lineage_ids_json": _as_json(source_feature_lineage_ids),
        "source_feature_certification_ids_json": _as_json(source_feature_certification_ids),
        "source_feature_dataset_certification_ids_json": _as_json(source_feature_dataset_certification_ids),
        "source_feature_alignment_certification_ids_json": _as_json(source_feature_alignment_certification_ids),
        "source_feature_missingness_json": _as_json(source_feature_missingness),
        "source_feature_freshness_json": _as_json(source_feature_freshness),
        "source_feature_value_types_json": _as_json(source_feature_value_types),
        "source_feature_values_json": _as_json(source_feature_values),
        "missing_required_assets_json": _as_json(list(context.missing_required_assets)),
        "evidence_package_id": _stable_id(
            "math_engine_evidence_package",
            context.source_feature_evidence_package_id,
            context.source_feature_population_summary_id,
            context.batch_id,
            MATH_ENGINE_TRANSFORMATION_VERSION,
        ),
        "record_count": 1,
        "engine_count": 1,
        "engine_values_json": _as_json(
            {
                "engine_id": definition.engine_id,
                "engine_name": definition.engine_name,
                "value": value,
                "missingness_state": missingness_state,
                "missingness_reason": missingness_reason,
                "dataset_row_id": context.dataset_row_id,
                "decision_context_id": context.decision_context_id,
                "feature_context_id": context.feature_context_id,
            }
        ),
        "summary_json": _as_json(
            {
                "engine_id": definition.engine_id,
                "engine_family": definition.engine_family,
                "value": value,
                "missingness_state": missingness_state,
            }
        ),
        "payload_json": _as_json(
            {
                "definition": definition.as_dict(),
                "context": context.as_dict(),
                "input_values": input_values,
                "output": {
                    "value": value,
                    "missingness_state": missingness_state,
                    "missingness_reason": missingness_reason,
                },
            }
        ),
        "snapshot_id": _stable_id(
            "math_engine_snapshot",
            context.batch_id,
            definition.engine_id,
            context.dataset_row_id,
            context.decision_context_id,
            context.scheduled_kickoff_time,
            context.decision_cutoff_time,
            _as_json(source_feature_snapshot_ids),
            _as_json(source_feature_lineage_ids),
            _as_json(source_feature_certification_ids),
            _as_json(source_feature_dataset_certification_ids),
            _as_json(source_feature_alignment_certification_ids),
        ),
        "lineage_id": _stable_id(
            "math_engine_lineage",
            context.batch_id,
            definition.engine_id,
            context.dataset_row_id,
            context.decision_context_id,
            _as_json(source_feature_snapshot_ids),
            _as_json(source_feature_lineage_ids),
            _as_json(source_feature_certification_ids),
        ),
        "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
        "quality_score": 1.0 if missingness_state == "present" else 0.0,
    }
    return payload, {
        "value": value,
        "missingness_state": missingness_state,
        "missingness_reason": missingness_reason,
        "source_feature_values": source_feature_values,
        "source_feature_snapshot_ids": source_feature_snapshot_ids,
        "source_feature_lineage_ids": source_feature_lineage_ids,
        "source_feature_certification_ids": source_feature_certification_ids,
        "source_feature_dataset_certification_ids": source_feature_dataset_certification_ids,
        "source_feature_alignment_certification_ids": source_feature_alignment_certification_ids,
        "source_feature_missingness": source_feature_missingness,
        "source_feature_freshness": source_feature_freshness,
        "source_feature_value_types": source_feature_value_types,
        "source_feature_ids": source_feature_ids,
    }


def _build_math_engine_alignment_row(
    *,
    identity: ResearchAssetIdentityContract,
    row: Mapping[str, Any],
    source_feature_summary: Mapping[str, Any],
    source_feature_rows: Sequence[Mapping[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    alignment_row = build_time_entity_alignment_certification_row(
        identity=identity,
        alignment=build_time_entity_alignment_certification(
            identity=identity,
            rows=[row],
            required_fields=(
                "dataset_id",
                "dataset_name",
                "batch_id",
                "snapshot_kind",
                "snapshot_id",
                "lineage_id",
                "version_id",
                "engine_id",
                "engine_name",
                "engine_family",
                "engine_version",
                "classification",
                "value_type",
                "unit",
                "engine_owner",
                "entity_scope",
                "dataset_grain_compatibility",
                "transformation_version",
                "missingness_policy",
                "engine_context_id",
                "output_feature_id",
                "required_input_feature_ids_json",
                "input_feature_count",
                "engine_value_json",
                "engine_missingness_state",
                "engine_definition_json",
                "engine_context_json",
                "math_engine_snapshot_grain_id",
                "math_engine_registry_schema_version",
                "engine_lineage_id",
                "engine_evidence_id",
                "source_feature_ids_json",
                "source_feature_snapshot_ids_json",
                "source_feature_lineage_ids_json",
                "source_feature_certification_ids_json",
                "source_feature_dataset_certification_ids_json",
                "source_feature_alignment_certification_ids_json",
                "source_feature_missingness_json",
                "source_feature_freshness_json",
                "source_feature_value_types_json",
                "source_feature_values_json",
                "missing_required_assets_json",
                "evidence_package_id",
                "record_count",
                "engine_count",
                "engine_values_json",
                "summary_json",
                "payload_json",
            ),
            required_timestamps=("provider_timestamp", "snapshot_time", "decision_time"),
            profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
            source_bundle={
                "source_name": DEFAULT_MATH_ENGINE_SOURCE_NAME,
                "source_type": DEFAULT_MATH_ENGINE_SOURCE_TYPE,
                "source_key": DEFAULT_MATH_ENGINE_SOURCE_KEY,
                "provider": DEFAULT_MATH_ENGINE_PROVIDER,
                "source_file": _normalize_text(source_feature_summary.get("storage_location")),
                "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or created_at),
            },
            raw_acquisition_result={
                "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or created_at),
                "source_snapshot_time": _normalize_text(source_feature_summary.get("created_at") or created_at),
                "source_file": _normalize_text(source_feature_summary.get("storage_location")),
            },
            created_at=created_at,
            asset_name=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
            asset_type="math_engine_snapshot",
            lifecycle_state="math_ready",
            batch_id=_normalize_text(row.get("batch_id")),
        ),
        profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
        source_bundle={
            "source_name": DEFAULT_MATH_ENGINE_SOURCE_NAME,
            "source_type": DEFAULT_MATH_ENGINE_SOURCE_TYPE,
            "source_key": DEFAULT_MATH_ENGINE_SOURCE_KEY,
            "provider": DEFAULT_MATH_ENGINE_PROVIDER,
            "source_file": _normalize_text(source_feature_summary.get("storage_location")),
            "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or created_at),
        },
        raw_acquisition_result={
            "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or created_at),
            "source_snapshot_time": _normalize_text(source_feature_summary.get("created_at") or created_at),
            "source_file": _normalize_text(source_feature_summary.get("storage_location")),
        },
        batch_id=_normalize_text(row.get("snapshot_id")),
    )
    return alignment_row


def _build_math_engine_row_identity(
    *,
    context: MathEngineSnapshotContext,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "asset_id": DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
        "asset_family": "mathematical_engine",
        "market_profile": DEFAULT_MATH_ENGINE_PROFILE_ID,
        "market": DEFAULT_MATH_ENGINE_MARKET,
        "league": "nfl",
        "sport": "football",
        "season": _normalize_text(row.get("season") or context.season),
        "week_or_date": _normalize_text(row.get("week") or context.week),
        "event_id": _normalize_text(row.get("event_id") or context.event_id),
        "market_id": _normalize_text(row.get("engine_id")),
        "selection": _normalize_text(row.get("output_feature_id")),
        "provider": DEFAULT_MATH_ENGINE_PROVIDER,
        "connector": "feature_snapshot_population",
        "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "lineage_version": _normalize_text(row.get("version_id"), MATH_ENGINE_TRANSFORMATION_VERSION),
        "asset_name": DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
        "asset_type": "math_engine_snapshot",
        "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
        "game_id": _normalize_text(row.get("game_id") or row.get("event_id")),
        "market_type": "math_engine",
        "metadata": {
            "dataset_row_id": _normalize_text(row.get("dataset_row_id")),
            "decision_context_id": _normalize_text(row.get("decision_context_id")),
            "engine_id": _normalize_text(row.get("engine_id")),
            "engine_version": _normalize_text(row.get("engine_version")),
            "output_feature_id": _normalize_text(row.get("output_feature_id")),
        },
    }


def _build_math_engine_population_summary_row(
    *,
    context_rows: Sequence[Mapping[str, Any]],
    source_feature_summary: Mapping[str, Any],
    batch_id: str,
    storage_location: str,
    created_at: str,
    math_rows: Sequence[Mapping[str, Any]],
    lineage_edges: Sequence[Mapping[str, Any]],
    engine_definition_count: int,
) -> dict[str, Any]:
    representative_row = dict(context_rows[0])
    source_feature_snapshot_ids = {
        _normalize_text(row.get("feature_id")): _normalize_text(row.get("snapshot_id"))
        for row in context_rows
    }
    source_feature_lineage_ids = {
        _normalize_text(row.get("feature_id")): _normalize_text(row.get("feature_lineage_id"))
        for row in context_rows
    }
    source_feature_certification_ids = {
        _normalize_text(row.get("feature_id")): _normalize_text(row.get("certification_id"))
        for row in context_rows
    }
    summary_snapshot_id = _stable_id(
        "math_engine_population_summary_snapshot",
        batch_id,
        source_feature_summary.get("snapshot_id"),
        source_feature_summary.get("batch_id"),
        MATH_ENGINE_TRANSFORMATION_VERSION,
    )
    summary_lineage_id = _stable_id(
        "math_engine_population_summary_lineage",
        summary_snapshot_id,
        source_feature_summary.get("lineage_id"),
        source_feature_summary.get("evidence_package_id"),
    )
    engine_values = [
        {
            "snapshot_id": row.get("snapshot_id"),
            "engine_id": row.get("engine_id"),
            "engine_name": row.get("engine_name"),
            "engine_family": row.get("engine_family"),
            "value_json": row.get("engine_value_json"),
            "missingness_state": row.get("engine_missingness_state"),
        }
        for row in math_rows
    ]
    summary = {
        "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
        "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
        "owner": DEFAULT_MATH_ENGINE_OWNER,
        "sport": "football",
        "math_pack": DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
        "storage_location": _normalize_text(storage_location),
        "readiness": "math_ready",
        "update_frequency": "manual",
        "validation_state": "validated",
        "status": "certified",
        "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_MATH_ENGINE_SOURCE_NAME,
        "provider": DEFAULT_MATH_ENGINE_PROVIDER,
        "market": DEFAULT_MATH_ENGINE_MARKET,
        "market_type": DEFAULT_MATH_ENGINE_MARKET_TYPE,
        "asset_class": DEFAULT_MATH_ENGINE_ASSET_CLASS,
        "snapshot_id": summary_snapshot_id,
        "lineage_id": summary_lineage_id,
        "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
        "quality_score": 1.0 if math_rows else 0.0,
        "batch_id": batch_id,
        "snapshot_kind": MATH_ENGINE_BATCH_KIND,
        "math_pack_version": MATH_ENGINE_TRANSFORMATION_VERSION,
        "source_feature_dataset_id": _normalize_text(source_feature_summary.get("dataset_id"), DEFAULT_NFL_HISTORICAL_DATASET_ID),
        "source_feature_dataset_name": _normalize_text(source_feature_summary.get("dataset_name"), DEFAULT_MATH_ENGINE_DATASET_NAME),
        "source_feature_batch_id": _normalize_text(source_feature_summary.get("batch_id")),
        "source_feature_version_id": _normalize_text(source_feature_summary.get("version_id")),
        "source_feature_certification_id": _normalize_text(source_feature_summary.get("certification_id")),
        "source_feature_dataset_certification_id": _normalize_text(source_feature_summary.get("dataset_certification_id")),
        "source_feature_population_summary_id": _normalize_text(source_feature_summary.get("snapshot_id")),
        "source_feature_evidence_package_id": _normalize_text(source_feature_summary.get("evidence_package_id")),
        "source_feature_batch_lineage_id": _normalize_text(source_feature_summary.get("lineage_id")),
        "source_feature_row_count": _normalize_int(source_feature_summary.get("dataset_row_count"), len(context_rows)),
        "source_feature_snapshot_count": _normalize_int(source_feature_summary.get("feature_snapshot_count"), len(context_rows)),
        "source_feature_definition_count": _normalize_int(source_feature_summary.get("feature_definition_count"), len(list_feature_definition_ids())),
        "dataset_row_id": _normalize_text(representative_row.get("dataset_row_id"), batch_id),
        "decision_context_id": _normalize_text(representative_row.get("decision_context_id"), batch_id),
        "feature_context_id": _normalize_text(representative_row.get("feature_context_id")),
        "event_id": _normalize_text(representative_row.get("event_id")),
        "game_id": _normalize_text(representative_row.get("game_id") or representative_row.get("event_id")),
        "season": _normalize_int(representative_row.get("season"), 0),
        "week": _normalize_int(representative_row.get("week"), 0),
        "home_team_id": _normalize_text(representative_row.get("home_team_id")),
        "away_team_id": _normalize_text(representative_row.get("away_team_id")),
        "team_side": _normalize_text(representative_row.get("team_side")),
        "target_team_id": _normalize_text(representative_row.get("target_team_id")),
        "opponent_team_id": _normalize_text(representative_row.get("opponent_team_id")),
        "home_team": _normalize_text(representative_row.get("home_team")),
        "away_team": _normalize_text(representative_row.get("away_team")),
        "selection": _normalize_text(representative_row.get("selection")),
        "book": _normalize_text(representative_row.get("book"), "consensus"),
        "scheduled_kickoff_time": _to_iso8601_utc(representative_row.get("scheduled_kickoff_time")),
        "decision_cutoff_time": _to_iso8601_utc(representative_row.get("decision_cutoff_time")),
        "cutoff_policy_version": _normalize_text(representative_row.get("cutoff_policy_version"), HISTORICAL_DATASET_CUTOFF_POLICY_ID),
        "point_in_time_status": _normalize_text(representative_row.get("point_in_time_status"), "safe"),
        "predictor_outcome_separation_status": _normalize_text(representative_row.get("predictor_outcome_separation_status"), "separated"),
        "decision_readiness_status": _normalize_text(representative_row.get("decision_readiness_status"), "decision_ready"),
        "engine_id": f"{DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID}.summary",
        "engine_name": "Math Engine Population Summary",
        "engine_family": "summary",
        "engine_version": MATH_ENGINE_DEFINITION_VERSION,
        "classification": "deterministic_derived",
        "value_type": "integer",
        "unit": "rows",
        "engine_owner": DEFAULT_MATH_ENGINE_ENGINE_OWNER,
        "entity_scope": "data_quality_context",
        "dataset_grain_compatibility": CANONICAL_MATH_ENGINE_SNAPSHOT_GRAIN_ID,
        "transformation_version": MATH_ENGINE_TRANSFORMATION_VERSION,
        "missingness_policy": "required",
        "engine_context_id": _stable_id(
            "math_engine_snapshot_context",
            batch_id,
            representative_row.get("dataset_row_id"),
            representative_row.get("decision_context_id"),
            "summary",
        ),
        "output_feature_id": f"{DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID}.summary",
        "required_input_feature_ids_json": _as_json(list(list_feature_definition_ids())),
        "input_feature_count": len(list_feature_definition_ids()),
        "engine_value_json": _as_json(len(math_rows)),
        "engine_value_text": None,
        "engine_value_number": len(math_rows),
        "engine_value_boolean": None,
        "engine_missingness_state": "present" if math_rows else "missing_required",
        "engine_missingness_reason": "" if math_rows else "no_math_rows_produced",
        "engine_definition_json": _as_json(
            {
                "engine_id": f"{DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID}.summary",
                "engine_name": "Math Engine Population Summary",
                "engine_family": "summary",
                "classification": "deterministic_derived",
                "value_type": "integer",
            }
        ),
        "engine_context_json": _as_json(
            {
                "batch_id": batch_id,
                "source_feature_summary": dict(source_feature_summary),
                "source_feature_snapshot_ids": source_feature_snapshot_ids,
                "source_feature_lineage_ids": source_feature_lineage_ids,
                "source_feature_certification_ids": source_feature_certification_ids,
                "engine_count": len(math_rows),
                "engine_definition_count": engine_definition_count,
            }
        ),
        "math_engine_snapshot_grain_id": CANONICAL_MATH_ENGINE_SNAPSHOT_GRAIN_ID,
        "math_engine_registry_schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "engine_lineage_id": summary_lineage_id,
        "engine_evidence_id": _stable_id(
            "math_engine_population_summary_evidence",
            summary_snapshot_id,
            batch_id,
            _as_json(source_feature_snapshot_ids),
            _as_json([row.get("snapshot_id") for row in math_rows]),
        ),
        "source_feature_ids_json": _as_json(list(list_feature_definition_ids())),
        "source_feature_snapshot_ids_json": _as_json(source_feature_snapshot_ids),
        "source_feature_lineage_ids_json": _as_json(source_feature_lineage_ids),
        "source_feature_certification_ids_json": _as_json(source_feature_certification_ids),
        "source_feature_dataset_certification_ids_json": _as_json(
            {
                _normalize_text(source_feature_summary.get("dataset_id"), DEFAULT_NFL_HISTORICAL_DATASET_ID): _normalize_text(
                    source_feature_summary.get("dataset_certification_id")
                )
            }
        ),
        "source_feature_alignment_certification_ids_json": _as_json(
            {
                _normalize_text(row.get("feature_id")): _normalize_text(row.get("feature_alignment_certification_id"))
                for row in context_rows
            }
        ),
        "source_feature_missingness_json": _as_json(
            {
                _normalize_text(row.get("feature_id")): _normalize_text(row.get("feature_missingness_state"))
                for row in context_rows
            }
        ),
        "source_feature_freshness_json": _as_json(
            {
                _normalize_text(row.get("feature_id")): _feature_freshness_value(row)
                for row in context_rows
            }
        ),
        "source_feature_value_types_json": _as_json(
            {
                _normalize_text(row.get("feature_id")): _normalize_text(row.get("value_type"))
                for row in context_rows
            }
        ),
        "source_feature_values_json": _as_json(
            {
                _normalize_text(row.get("feature_id")): _feature_value(row)
                for row in context_rows
            }
        ),
        "missing_required_assets_json": _as_json(_load_json_list(source_feature_summary.get("missing_required_assets_json"))),
        "evidence_package_id": _stable_id(
            "math_engine_population_evidence_package",
            source_feature_summary.get("evidence_package_id"),
            batch_id,
            MATH_ENGINE_TRANSFORMATION_VERSION,
        ),
        "record_count": len(math_rows),
        "engine_count": len(math_rows),
        "engine_values_json": _as_json(engine_values),
        "summary_json": _as_json(
            {
                "batch_id": batch_id,
                "dataset_row_count": len({row.get("dataset_row_id") for row in math_rows if row.get("dataset_row_id")}),
                "engine_row_count": len(math_rows),
                "engine_definition_count": engine_definition_count,
                "source_feature_snapshot_count": source_feature_summary.get("feature_snapshot_count"),
                "source_feature_definition_count": source_feature_summary.get("feature_definition_count"),
            }
        ),
        "payload_json": _as_json(
            {
                "summary": {
                    "batch_id": batch_id,
                    "engine_row_count": len(math_rows),
                    "engine_definition_count": engine_definition_count,
                },
                "source_feature_summary": dict(source_feature_summary),
                "engine_values": engine_values,
                "lineage_edges": [dict(row) for row in lineage_edges],
            }
        ),
    }
    return summary


def _default_storage(storage_path: str | Path | None = None, *, backend: str = "sqlite") -> LocalStorageEngine:
    path = Path(storage_path or DEFAULT_MATH_ENGINE_STORAGE_PATH)
    return create_local_storage_engine(path, backend=backend)


def _math_engine_population_missing_snapshot(
    *,
    storage: LocalStorageEngine,
    dataset_id: str,
    batch_id: str,
    status: str,
    warnings: Sequence[str],
) -> dict[str, Any]:
    warning_list = [str(item) for item in warnings if _normalize_text(item)]
    return {
        "ok": False,
        "status": status,
        "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
        "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
        "batch_id": _normalize_text(batch_id),
        "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
        "dataset_row_count": 0,
        "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
        "engine_row_count": 0,
        "math_engine_rows": [],
        "math_engine_summary_rows": [],
        "math_engine_population_summary": {},
        "math_engine_population_summary_id": "",
        "math_engine_evidence_package_id": "",
        "math_engine_lineage_edges": [],
        "math_engine_alignment_rows": [],
        "math_engine_lifecycle_rows": [],
        "dataset_certification_status": "missing",
        "dataset_certification_id": "",
        "lifecycle_state": "missing",
        "source_feature_snapshot": {},
        "source_feature_summary": {},
        "source_feature_population_snapshot": {},
        "source_feature_population_summary": {},
        "source_feature_rows": [],
        "source_feature_batch_id": "",
        "source_feature_certification_id": "",
        "source_feature_dataset_certification_id": "",
        "source_feature_evidence_package_id": "",
        "source_feature_population_summary_id": "",
        "source_feature_batch_lineage_id": "",
        "join_diagnostics": {},
        "registry": summarize_math_engine_registry(),
        "validation": {},
        "math_engine_validation": {},
        "storage": storage.health(),
        "unresolved_blockers": warning_list,
        "readiness": "blocked",
        "validation_state": "rejected",
        "source_feature_snapshot_count": 0,
        "feature_context_count": 0,
        "math_engine_context_count": 0,
        "math_engine_definition_ids": list_math_engine_definition_ids(),
        "warnings": warning_list,
        "idempotent_reuse": False,
    }


def _load_math_engine_population_snapshot(
    storage: LocalStorageEngine,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    if not storage.table_exists("math_engine_snapshots"):
        return _math_engine_population_missing_snapshot(
            storage=storage,
            dataset_id=dataset_id,
            batch_id=_normalize_text(batch_id),
            status="missing_math_engine_table",
            warnings=["math engine snapshots table is missing"],
        )

    summary_rows_all = [
        dict(row)
        for row in storage.fetch(
            "math_engine_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[DEFAULT_MATH_ENGINE_DATASET_ID, MATH_ENGINE_BATCH_KIND],
            order_by="created_at ASC, snapshot_id ASC",
        )
    ]
    engine_rows_all = [
        dict(row)
        for row in storage.fetch(
            "math_engine_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[DEFAULT_MATH_ENGINE_DATASET_ID, MATH_ENGINE_ROW_KIND],
            order_by="dataset_row_id ASC, engine_id ASC, snapshot_id ASC",
        )
    ]

    effective_batch_id = _normalize_text(batch_id)
    if effective_batch_id:
        summary_rows = [row for row in summary_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id]
        engine_rows = [row for row in engine_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id]
    else:
        summary_rows = summary_rows_all[-1:] if summary_rows_all else []
        effective_batch_id = _normalize_text(summary_rows[-1].get("batch_id")) if summary_rows else ""
        if not effective_batch_id and engine_rows_all:
            effective_batch_id = _normalize_text(engine_rows_all[-1].get("batch_id"))
        engine_rows = [row for row in engine_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else []
        summary_rows = [row for row in summary_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else summary_rows

    latest_summary_row = dict(summary_rows[-1]) if summary_rows else {}
    engine_snapshot_ids = {str(row.get("snapshot_id")) for row in engine_rows if _normalize_text(row.get("snapshot_id"))}
    engine_context_ids = {str(row.get("feature_context_id")) for row in engine_rows if _normalize_text(row.get("feature_context_id"))}
    engine_dataset_row_ids = {str(row.get("dataset_row_id")) for row in engine_rows if _normalize_text(row.get("dataset_row_id"))}
    grouped_contexts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in engine_rows:
        grouped_contexts[_normalize_text(row.get("feature_context_id"))].append(dict(row))

    source_feature_batch_id = _normalize_text(latest_summary_row.get("source_feature_batch_id"))
    source_feature_snapshot = build_feature_snapshot_population_dashboard_snapshot(
        storage_path=storage.path,
        backend=backend,
        dataset_id=dataset_id,
        batch_id=source_feature_batch_id or None,
        include_source_dataset_snapshot=False,
    ) if source_feature_batch_id or summary_rows else {}
    source_feature_summary = dict(source_feature_snapshot.get("feature_population_summary") or {})
    if not source_feature_summary:
        feature_batches = source_feature_snapshot.get("feature_batches") or []
        if feature_batches:
            source_feature_summary = dict(feature_batches[-1])
        else:
            source_feature_summary = dict(source_feature_snapshot)

    alignment_rows_all = [
        dict(row)
        for row in storage.fetch(
            "research_asset_alignment_certifications",
            where="asset_id = ?",
            params=[DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID],
            order_by="certification_timestamp ASC, alignment_certification_id ASC",
        )
    ] if storage.table_exists("research_asset_alignment_certifications") else []
    alignment_rows = [row for row in alignment_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else alignment_rows_all

    lifecycle_rows_all = [
        dict(row)
        for row in storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID],
            order_by="created_at ASC, snapshot_id ASC",
        )
    ] if storage.table_exists("research_asset_lifecycles") else []
    lifecycle_rows = [row for row in lifecycle_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else lifecycle_rows_all

    certification_rows_all = [
        dict(row)
        for row in storage.fetch(
            "historical_certifications",
            where="batch_id = ?",
            params=[effective_batch_id],
            order_by="certified_at ASC, certification_id ASC",
        )
    ] if effective_batch_id and storage.table_exists("historical_certifications") else []
    certification_row = certification_rows_all[-1] if certification_rows_all else {}

    lineage_rows_all = [
        dict(row)
        for row in storage.fetch(
            "lineage_edges",
            where="dataset_id = ?",
            params=[DEFAULT_MATH_ENGINE_DATASET_ID],
            order_by="step_index ASC, lineage_edge_id ASC",
        )
    ] if storage.table_exists("lineage_edges") else []
    lineage_rows = [row for row in lineage_rows_all if _normalize_text(row.get("target_id")) in engine_snapshot_ids]

    math_engine_validation = validate_math_engine_rows(engine_rows)
    validation_state = _normalize_text(latest_summary_row.get("validation_state"), "missing")
    status = _normalize_text(latest_summary_row.get("status"), "missing")
    readiness = _normalize_text(latest_summary_row.get("readiness"), "missing")
    dataset_certification_status = _normalize_text(certification_row.get("certification_status"), "missing")
    dataset_certification_id = _normalize_text(certification_row.get("certification_id"))
    lifecycle_state = _normalize_text((lifecycle_rows[-1] if lifecycle_rows else {}).get("lifecycle_state"), "missing")
    alignment_statuses = [_normalize_text(row.get("alignment_status"), "missing") for row in alignment_rows]
    all_alignment_ok = bool(alignment_rows) and all(status_name == "aligned" for status_name in alignment_statuses)

    missing_fields: list[str] = []
    if not summary_rows:
        missing_fields.append("math_engine_population_summary")
    if not engine_rows:
        missing_fields.append("math_engine_rows")
    if not certification_rows_all:
        missing_fields.append("historical_certifications")
    if not lifecycle_rows:
        missing_fields.append("research_asset_lifecycles")
    if not all_alignment_ok:
        missing_fields.append("alignment_certifications")
    if validation_state != "validated":
        missing_fields.append("validation_state")
    if status != "certified":
        missing_fields.append("status")
    if readiness != "math_ready":
        missing_fields.append("readiness")
    if dataset_certification_status != "certified":
        missing_fields.append("dataset_certification_status")
    if lifecycle_state != "math_ready":
        missing_fields.append("lifecycle_state")
    if not math_engine_validation["ok"]:
        missing_fields.extend(math_engine_validation.get("errors", []))

    source_feature_definition_count = _normalize_int(source_feature_summary.get("feature_definition_count"), len(list_feature_definition_ids()))
    source_feature_snapshot_count = _normalize_int(source_feature_summary.get("feature_snapshot_count"), len(source_feature_snapshot.get("feature_rows", [])))
    expected_engine_row_count = len(engine_context_ids) * len(_MATH_ENGINE_DEFINITIONS)
    context_sizes = dict(Counter(len(rows) for rows in grouped_contexts.values()))
    ready = (
        not missing_fields and len(engine_rows) == expected_engine_row_count
    ) if expected_engine_row_count else bool(engine_rows)

    source_feature_population_summary = dict(source_feature_summary)
    source_feature_population_snapshot = dict(source_feature_snapshot)
    source_feature_batch_lineage_id = _normalize_text(source_feature_summary.get("lineage_id"))
    math_evidence_package_id = _normalize_text(latest_summary_row.get("evidence_package_id"))
    if not math_evidence_package_id:
        math_evidence_package_id = _stable_id(
            "math_engine_population_evidence_package",
            source_feature_summary.get("evidence_package_id"),
            effective_batch_id,
            MATH_ENGINE_TRANSFORMATION_VERSION,
        )
    if not source_feature_snapshot:
        source_feature_population_snapshot = {}
        source_feature_population_summary = {}

    source_feature_rows = [dict(row) for row in source_feature_snapshot.get("feature_rows", [])]
    return {
        "ok": bool(ready),
        "status": "ready" if ready else "partial" if (summary_rows or engine_rows) else "missing",
        "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
        "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
        "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
        "batch_id": effective_batch_id,
        "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
        "dataset_row_count": len(engine_dataset_row_ids),
        "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
        "engine_row_count": len(engine_rows),
        "math_engine_row_count": len(engine_rows),
        "math_engine_rows": engine_rows,
        "math_engine_summary_rows": summary_rows,
        "math_engine_population_summary": latest_summary_row,
        "math_engine_population_summary_id": _normalize_text(latest_summary_row.get("snapshot_id")),
        "math_engine_evidence_package_id": math_evidence_package_id,
        "math_engine_lineage_edges": lineage_rows,
        "math_engine_alignment_rows": alignment_rows,
        "math_engine_lifecycle_rows": lifecycle_rows,
        "dataset_certification_status": dataset_certification_status,
        "dataset_certification_id": dataset_certification_id,
        "lifecycle_state": lifecycle_state,
        "source_feature_snapshot": source_feature_population_snapshot,
        "source_feature_summary": source_feature_population_summary,
        "source_feature_population_snapshot": source_feature_population_snapshot,
        "source_feature_population_summary": source_feature_population_summary,
        "source_feature_rows": source_feature_rows,
        "source_feature_batch_id": _normalize_text(source_feature_summary.get("batch_id")),
        "source_feature_certification_id": _normalize_text(source_feature_summary.get("certification_id")),
        "source_feature_dataset_certification_id": _normalize_text(source_feature_summary.get("dataset_certification_id")),
        "source_feature_evidence_package_id": _normalize_text(source_feature_summary.get("evidence_package_id")),
        "source_feature_population_summary_id": _normalize_text(source_feature_summary.get("snapshot_id")),
        "source_feature_batch_lineage_id": source_feature_batch_lineage_id,
        "join_diagnostics": {
            "feature_context_count": len(engine_context_ids),
            "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
            "engine_row_count": len(engine_rows),
            "summary_row_count": len(summary_rows),
            "missing_engine_row_count": max(expected_engine_row_count - len(engine_rows), 0),
            "source_feature_row_count": len(source_feature_rows),
            "source_feature_snapshot_count": source_feature_snapshot_count,
            "source_feature_definition_count": source_feature_definition_count,
            "context_sizes": context_sizes,
        },
        "registry": summarize_math_engine_registry(),
        "validation": math_engine_validation,
        "math_engine_validation": math_engine_validation,
        "storage": storage.health(),
        "unresolved_blockers": missing_fields,
        "readiness": "math_ready" if ready else "blocked",
        "validation_state": validation_state if ready else "rejected",
        "source_feature_snapshot_count": source_feature_snapshot_count,
        "feature_context_count": len(engine_context_ids),
        "math_engine_context_count": len(engine_context_ids),
        "math_engine_definition_ids": list_math_engine_definition_ids(),
        "idempotent_reuse": bool(summary_rows and engine_rows),
        "warnings": [] if ready else missing_fields,
    }


def build_math_engine_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    storage = _default_storage(storage_path, backend=backend)
    close_storage = True
    try:
        storage.ensure_schema()
        registry_validation = validate_math_engine_registry()
        if not registry_validation["ok"]:
            raise ValueError("; ".join(registry_validation["errors"]) or "math engine registry validation failed")

        feature_snapshot = build_feature_snapshot_population_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            dataset_id=dataset_id,
            include_source_dataset_snapshot=False,
        )
        if not feature_snapshot.get("ok"):
            raise ValueError("; ".join(feature_snapshot.get("warnings", [])) or "feature snapshot population snapshot is not ready")
        source_feature_summary = dict(feature_snapshot.get("feature_population_summary") or {})
        if not source_feature_summary:
            feature_batches = feature_snapshot.get("feature_batches") or []
            if feature_batches:
                source_feature_summary = dict(feature_batches[-1])
            else:
                source_feature_summary = dict(feature_snapshot)
        source_feature_rows = [dict(row) for row in feature_snapshot.get("feature_rows", []) if _normalize_text(row.get("snapshot_kind")) == FEATURE_SNAPSHOT_ROW_KIND]
        if not source_feature_rows:
            raise ValueError("no certified feature rows were returned")

        grouped_contexts = _group_feature_rows(source_feature_rows)
        if not grouped_contexts:
            raise ValueError("no feature contexts were found")

        batch_id = _normalize_text(
            batch_id,
            _stable_id(
                "math_engine_population_batch",
                source_feature_summary.get("batch_id"),
                source_feature_summary.get("snapshot_id"),
                MATH_ENGINE_TRANSFORMATION_VERSION,
                FEATURE_REGISTRY_SCHEMA_VERSION,
            ),
        )

        persisted_snapshot = _load_math_engine_population_snapshot(
            storage,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=batch_id,
        )
        if persisted_snapshot.get("ok"):
            return persisted_snapshot
        if persisted_snapshot.get("math_engine_rows") or persisted_snapshot.get("math_engine_summary_rows"):
            raise ValueError("; ".join(persisted_snapshot.get("unresolved_blockers", [])) or "existing math engine batch is incomplete")

        engine_rows: list[dict[str, Any]] = []
        lineage_edges: list[dict[str, Any]] = []
        alignment_rows: list[dict[str, Any]] = []
        validation_rows: list[dict[str, Any]] = []
        context_summaries: list[dict[str, Any]] = []

        for context_entry in grouped_contexts:
            context_rows = context_entry["feature_rows"]
            feature_lookup = _build_feature_lookups(context_rows)
            context = build_math_engine_snapshot_context(
                source_feature_summary=source_feature_summary,
                feature_rows=source_feature_rows,
                context_rows=context_rows,
                batch_id=batch_id,
            )
            context_summaries.append(context.as_dict())
            for definition in _MATH_ENGINE_DEFINITIONS:
                row, row_summary = _row_payload_and_values(
                    definition=definition,
                    context=context,
                    feature_lookup=feature_lookup,
                    storage_location=str(storage.path),
                    created_at=_utc_now_iso(),
                )
                engine_rows.append(row)
                validation_rows.append(
                    {
                        **row,
                        "provider_timestamp": _normalize_text(source_feature_summary.get("created_at"), row.get("decision_cutoff_time")),
                        "snapshot_time": row.get("decision_cutoff_time"),
                        "decision_time": row.get("decision_cutoff_time"),
                        "result_timestamp": "",
                    }
                )
                source_feature_rows_for_lineage = [feature_lookup[feature_id] for feature_id in definition.input_feature_ids if feature_id in feature_lookup]
                lineage_row = create_lineage_record(
                    provider_id=DEFAULT_MATH_ENGINE_PROVIDER,
                    provider_type="math_engine_population",
                    payload_schema_version=MATH_ENGINE_POPULATION_SCHEMA_VERSION,
                    snapshot_id=_normalize_text(row.get("snapshot_id")),
                    source_type=DEFAULT_MATH_ENGINE_SOURCE_TYPE,
                    schema_version=MATH_ENGINE_POPULATION_SCHEMA_VERSION,
                    lineage_id=_normalize_text(row.get("engine_lineage_id")),
                    dataset_id=DEFAULT_MATH_ENGINE_DATASET_ID,
                    dataset_name=DEFAULT_MATH_ENGINE_DATASET_NAME,
                    source_record_id=_normalize_text(row.get("feature_context_id")),
                    target_record_id=_normalize_text(row.get("snapshot_id")),
                    source_stage="feature_snapshot",
                    target_stage="math_engine_snapshot",
                    transformation="populate_math_engine_snapshot",
                )
                lineage_edges.append(
                    {
                        "lineage_edge_id": _normalize_text(row.get("engine_lineage_id")),
                        "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
                        "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
                        "owner": DEFAULT_MATH_ENGINE_OWNER,
                        "sport": "football",
                        "feature_pack": MATH_ENGINE_DEFINITION_VERSION,
                        "storage_location": str(storage.path),
                        "readiness": "math_ready",
                        "update_frequency": "manual",
                        "validation_state": "validated" if row.get("engine_missingness_state") == "present" else "rejected",
                        "status": "certified" if row.get("engine_missingness_state") == "present" else "blocked",
                        "source_stage": "feature_snapshot",
                        "source_id": _normalize_text(row.get("feature_context_id")),
                        "target_stage": "math_engine_snapshot",
                        "target_id": _normalize_text(row.get("snapshot_id")),
                        "transformation": "populate_math_engine_snapshot",
                        "step_index": len(lineage_edges) + 1,
                        "payload_json": _as_json(
                            {
                                "lineage_record": lineage_row,
                                "definition": definition.as_dict(),
                                "context": context.as_dict(),
                                "source_feature_rows": [dict(feature_lookup[feature_id]) for feature_id in definition.input_feature_ids if feature_id in feature_lookup],
                                "output": row_summary,
                            }
                        ),
                    }
                )
                if row.get("engine_missingness_state") == "present":
                    row["quality_score"] = 1.0

        missing_engine_rows = [row for row in engine_rows if _normalize_text(row.get("engine_missingness_state")) != "present"]
        row_validation = validate_math_engine_rows(engine_rows)
        validation_rows_payload = [dict(row) for row in validation_rows]
        if not row_validation["ok"]:
            raise ValueError("; ".join(row_validation.get("errors", [])) or "math engine rows failed validation")

        summary_row = _build_math_engine_population_summary_row(
            context_rows=source_feature_rows,
            source_feature_summary=source_feature_summary,
            batch_id=batch_id,
            storage_location=str(storage.path),
            created_at=_utc_now_iso(),
            math_rows=engine_rows,
            lineage_edges=lineage_edges,
            engine_definition_count=len(_MATH_ENGINE_DEFINITIONS),
        )

        math_asset_contract = ResearchAssetCertificationContract(
            research_asset_id=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
            research_asset_name=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
            asset_category="math_engine",
            asset_type="snapshot_batch",
            source_table_name="math_engine_snapshots",
            required_fields=_required_row_fields(),
            required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
            point_in_time_rules=(
                "scheduled_kickoff_time must predate the decision cutoff",
                "decision_cutoff_time must remain unchanged from the certified feature layer",
                "engine outputs must remain feature-derived and label-free",
            ),
            description=(
                "Deterministic reusable mathematical engines derived from certified NFL "
                "feature snapshots and preserved with explicit provenance, lineage, and "
                "point-in-time constraints."
            ),
            priority="P0",
            required=True,
            future_asset=False,
            metadata={
                "market_profile": DEFAULT_MATH_ENGINE_PROFILE_ID,
                "market_family": "sports",
                "minimum_schema": True,
                "dataset_role": "math_engine_population",
                "source_feature_batch_id": _normalize_text(source_feature_summary.get("batch_id")),
                "source_feature_certification_id": _normalize_text(source_feature_summary.get("certification_id")),
                "source_feature_dataset_certification_id": _normalize_text(source_feature_summary.get("dataset_certification_id")),
                "source_feature_evidence_package_id": _normalize_text(source_feature_summary.get("evidence_package_id")),
                "source_feature_population_summary_id": _normalize_text(source_feature_summary.get("snapshot_id")),
            },
        )

        certification_runtime = HistoricalResearchAssetCertificationRuntime(
            storage_path=storage_path,
            backend=backend,
            store=storage,
        )
        lifecycle_runtime = ResearchAssetLifecycleRuntime(
            storage_path=storage_path,
            backend=backend,
            store=storage,
        )
        try:
            source_bundle = {
                "source_name": DEFAULT_MATH_ENGINE_SOURCE_NAME,
                "source_type": DEFAULT_MATH_ENGINE_SOURCE_TYPE,
                "source_key": DEFAULT_MATH_ENGINE_SOURCE_KEY,
                "provider": DEFAULT_MATH_ENGINE_PROVIDER,
                "source_snapshot_time": _utc_now_iso(),
                "snapshot_time": _utc_now_iso(),
                "decision_time": _normalize_text(source_feature_summary.get("decision_cutoff_time")),
                "result_timestamp": "",
            }
            raw_acquisition_result = {
                "ok": True,
                "status": "feature_snapshot_input",
                "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
                "source_snapshot_time": _normalize_text(source_feature_summary.get("created_at")),
                "snapshot_time": _normalize_text(source_feature_summary.get("created_at")),
                "decision_time": _normalize_text(source_feature_summary.get("decision_cutoff_time")),
            }
            math_result = certification_runtime.certify_research_asset(
                asset_contract=math_asset_contract,
                rows=engine_rows,
                profile_id=DEFAULT_MATH_ENGINE_PROFILE_ID,
                validation=row_validation,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                dataset_version=MATH_ENGINE_TRANSFORMATION_VERSION,
                created_at=_utc_now_iso(),
                batch_id=batch_id,
            )
            math_certification_row = dict(math_result["research_asset_certification"])
            storage.upsert("math_engine_snapshots", summary_row, key_columns=("snapshot_id",))
            for row in engine_rows:
                storage.upsert("math_engine_snapshots", row, key_columns=("snapshot_id",))
            for lineage_row in lineage_edges:
                storage.upsert("lineage_edges", lineage_row, key_columns=("lineage_edge_id",))
            math_dataset_row = build_historical_dataset_certification_row(
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                dataset_version=MATH_ENGINE_TRANSFORMATION_VERSION,
                batch_id=batch_id,
                created_at=_utc_now_iso(),
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                asset_rows=[math_certification_row],
            )
            storage.upsert("historical_certifications", math_dataset_row, key_columns=("certification_id",))

            representative_row = dict(source_feature_rows[0])

            math_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
                asset_family="mathematical_engine",
                market_profile=DEFAULT_MATH_ENGINE_PROFILE_ID,
                market=DEFAULT_MATH_ENGINE_MARKET,
                league="nfl",
                sport="football",
                season=str(source_feature_summary.get("season") or representative_row.get("season") or ""),
                week_or_date=str(representative_row.get("week") or ""),
                event_id=_normalize_text(representative_row.get("event_id")),
                market_id=f"{batch_id}.math",
                selection="math_engine_population",
                provider=DEFAULT_MATH_ENGINE_PROVIDER,
                connector="feature_snapshot_population",
                schema_version=MATH_ENGINE_POPULATION_SCHEMA_VERSION,
                lineage_version=batch_id,
                asset_name=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
                asset_type="math_engine_snapshot_batch",
                team_id=_normalize_text(representative_row.get("target_team_id") or representative_row.get("home_team_id") or representative_row.get("away_team_id")),
                game_id=_normalize_text(representative_row.get("game_id") or representative_row.get("event_id")),
                market_type=DEFAULT_MATH_ENGINE_MARKET_TYPE,
            )
            identity_validation = validate_research_asset_identity_contract(math_identity)
            if not identity_validation["ok"]:
                raise ValueError("; ".join(identity_validation["errors"]) or "math engine identity validation failed")

            alignment_rows_result: list[dict[str, Any]] = []
            for row in engine_rows:
                row_identity = build_research_asset_identity_contract(
                    asset_id=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
                    asset_family="mathematical_engine",
                    market_profile=DEFAULT_MATH_ENGINE_PROFILE_ID,
                    market=DEFAULT_MATH_ENGINE_MARKET,
                    league="nfl",
                    sport="football",
                    season=str(row.get("season") or ""),
                    week_or_date=str(row.get("week") or ""),
                    event_id=_normalize_text(row.get("event_id")),
                    market_id=_normalize_text(row.get("engine_id")),
                    selection=_normalize_text(row.get("output_feature_id")),
                    provider=DEFAULT_MATH_ENGINE_PROVIDER,
                    connector="feature_snapshot_population",
                    schema_version=MATH_ENGINE_POPULATION_SCHEMA_VERSION,
                    lineage_version=_normalize_text(row.get("version_id"), MATH_ENGINE_TRANSFORMATION_VERSION),
                    asset_name=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
                    asset_type="math_engine_snapshot",
                    team_id=_normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                    game_id=_normalize_text(row.get("game_id") or row.get("event_id")),
                    market_type=DEFAULT_MATH_ENGINE_MARKET_TYPE,
                )
                alignment_contract = build_time_entity_alignment_certification(
                    identity=row_identity,
                    rows=[
                        {
                            **dict(row),
                            "asset_id": DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
                            "asset_family": "mathematical_engine",
                            "asset_name": DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
                            "asset_type": "math_engine_snapshot",
                            "lineage_version": _normalize_text(row.get("version_id"), MATH_ENGINE_TRANSFORMATION_VERSION),
                            "market_id": _normalize_text(row.get("engine_id")),
                            "provider_timestamp": _normalize_text(
                                source_feature_summary.get("decision_cutoff_time"),
                                _normalize_text(row.get("decision_cutoff_time")),
                            ),
                            "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                            "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                            "result_timestamp": "",
                            "market_profile": DEFAULT_MATH_ENGINE_PROFILE_ID,
                            "market": DEFAULT_MATH_ENGINE_MARKET,
                            "league": "nfl",
                            "sport": "football",
                            "week_or_date": str(row.get("week") or ""),
                            "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                            "participant_id": "",
                            "selection": _normalize_text(row.get("output_feature_id")),
                            "connector": "feature_snapshot_population",
                        }
                    ],
                    required_fields=(
                        "dataset_id",
                        "dataset_name",
                        "snapshot_id",
                        "batch_id",
                        "engine_id",
                        "engine_name",
                        "engine_family",
                        "engine_version",
                        "classification",
                        "value_type",
                        "unit",
                        "engine_owner",
                        "entity_scope",
                        "dataset_grain_compatibility",
                        "transformation_version",
                        "missingness_policy",
                        "engine_context_id",
                        "output_feature_id",
                        "engine_value_json",
                        "engine_missingness_state",
                        "engine_definition_json",
                        "engine_context_json",
                        "math_engine_snapshot_grain_id",
                        "math_engine_registry_schema_version",
                        "engine_lineage_id",
                        "engine_evidence_id",
                        "source_feature_ids_json",
                        "source_feature_snapshot_ids_json",
                        "source_feature_lineage_ids_json",
                        "source_feature_certification_ids_json",
                        "source_feature_dataset_certification_ids_json",
                        "source_feature_alignment_certification_ids_json",
                        "missing_required_assets_json",
                        "evidence_package_id",
                    ),
                    required_timestamps=("provider_timestamp", "snapshot_time", "decision_time"),
                    profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                    source_bundle={
                        **source_bundle,
                        "source_file": _normalize_text(source_feature_summary.get("storage_location")),
                        "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or row.get("created_at") or _utc_now_iso()),
                    },
                    raw_acquisition_result={
                        **raw_acquisition_result,
                        "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or row.get("created_at") or _utc_now_iso()),
                        "source_file": _normalize_text(source_feature_summary.get("storage_location")),
                    },
                    created_at=_utc_now_iso(),
                    asset_name=DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME,
                    asset_type="math_engine_snapshot",
                    lifecycle_state="math_ready",
                    batch_id=_normalize_text(row.get("snapshot_id")),
                )
                alignment_row = build_time_entity_alignment_certification_row(
                    identity=row_identity,
                    alignment=alignment_contract,
                    profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                    source_bundle={
                        **source_bundle,
                        "source_file": _normalize_text(source_feature_summary.get("storage_location")),
                        "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or row.get("created_at") or _utc_now_iso()),
                    },
                    raw_acquisition_result={
                        **raw_acquisition_result,
                        "result_timestamp": _normalize_text(source_feature_summary.get("created_at") or row.get("created_at") or _utc_now_iso()),
                        "source_file": _normalize_text(source_feature_summary.get("storage_location")),
                    },
                    batch_id=batch_id,
                )
                alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
                if not alignment_validation["ok"]:
                    raise ValueError("; ".join(alignment_validation.get("issues", [])) or "math engine alignment validation failed")
                storage.upsert("research_asset_alignment_certifications", alignment_row, key_columns=("alignment_certification_id",))
                alignment_rows_result.append(
                    {
                        "ok": alignment_contract.alignment_status == "aligned",
                        "status": alignment_contract.alignment_status,
                        "identity": row_identity.as_dict(),
                        "alignment_certification": alignment_contract.as_dict(),
                        "alignment_certification_row": alignment_row,
                        "validation": alignment_validation,
                    }
                )

            lifecycle_rows: list[dict[str, Any]] = [
                lifecycle_runtime.record_lifecycle_state(
                    identity=math_identity,
                    lifecycle_state="math_ready",
                    lifecycle_reason=f"{DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME} promoted to math_ready",
                    source_bundle=source_bundle,
                    raw_acquisition_result=raw_acquisition_result,
                    created_at=_utc_now_iso(),
                    certification_result=math_certification_row,
                    dataset_result=math_dataset_row,
                    notes={
                        "batch_id": batch_id,
                        "engine_row_count": len(engine_rows),
                        "feature_context_count": len(grouped_contexts),
                        "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
                        "previous_states": ["research_asset_certified", "dataset_certified"],
                    },
                )
            ]

            persisted_rows = storage.fetch(
                "math_engine_snapshots",
                where="dataset_id = ?",
                params=[DEFAULT_MATH_ENGINE_DATASET_ID],
                order_by="created_at ASC, snapshot_id ASC",
            )
            persisted_summary_rows = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == MATH_ENGINE_BATCH_KIND]
            persisted_engine_rows = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == MATH_ENGINE_ROW_KIND]
            latest_summary_row = dict(summary_row)
            latest_summary_row.setdefault("status", "certified")
            latest_summary_row.setdefault("readiness", "math_ready")
            latest_summary_row.setdefault("validation_state", "validated")
            storage.upsert("math_engine_snapshots", latest_summary_row, key_columns=("snapshot_id",))
            persisted_rows = storage.fetch(
                "math_engine_snapshots",
                where="dataset_id = ?",
                params=[DEFAULT_MATH_ENGINE_DATASET_ID],
                order_by="snapshot_kind ASC, dataset_row_id ASC, engine_id ASC, snapshot_id ASC",
            )
            engine_rows_persisted = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == MATH_ENGINE_ROW_KIND]
            summary_rows_persisted = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == MATH_ENGINE_BATCH_KIND]
            summary_row = summary_rows_persisted[-1] if summary_rows_persisted else latest_summary_row

            math_evidence_package_id = _normalize_text(summary_row.get("evidence_package_id"))
            if not math_evidence_package_id:
                math_evidence_package_id = _stable_id(
                    "math_engine_population_evidence_package",
                    source_feature_summary.get("evidence_package_id"),
                    batch_id,
                    MATH_ENGINE_TRANSFORMATION_VERSION,
                )

            math_dataset_summary = {
                "ok": True,
                "status": "certified",
                "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
                "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
                "batch_id": batch_id,
                "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
                "dataset_row_count": len({row.get("dataset_row_id") for row in engine_rows_persisted if row.get("dataset_row_id")}),
                "engine_row_count": len(engine_rows_persisted),
                "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
                "feature_context_count": len(grouped_contexts),
                "math_engine_population_summary_id": _normalize_text(summary_row.get("snapshot_id")),
                "math_engine_evidence_package_id": math_evidence_package_id,
                "dataset_certification_status": _normalize_text(math_dataset_row.get("certification_status"), "missing"),
                "dataset_certification_id": _normalize_text(math_dataset_row.get("certification_id")),
                "lifecycle_state": _normalize_text(
                    lifecycle_rows[-1].get("lifecycle_state") if lifecycle_rows and lifecycle_rows[-1].get("lifecycle_state") else "math_ready",
                    "missing" if not lifecycle_rows else "math_ready",
                ),
                "source_feature_population_summary_id": _normalize_text(source_feature_summary.get("snapshot_id")),
                "source_feature_batch_id": _normalize_text(source_feature_summary.get("batch_id")),
                "source_feature_certification_id": _normalize_text(source_feature_summary.get("certification_id")),
                "source_feature_dataset_certification_id": _normalize_text(source_feature_summary.get("dataset_certification_id")),
                "source_feature_evidence_package_id": _normalize_text(source_feature_summary.get("evidence_package_id")),
                "source_feature_batch_lineage_id": _normalize_text(source_feature_summary.get("lineage_id")),
                "math_engine_rows": engine_rows_persisted,
                "math_engine_summary_rows": summary_rows_persisted,
                "math_engine_lineage_edges": [dict(row) for row in lineage_edges],
                "math_engine_alignment_rows": alignment_rows_result,
                "math_engine_lifecycle_rows": lifecycle_rows,
                "validation": row_validation,
                "source_feature_population_snapshot": feature_snapshot,
                "source_feature_summary": source_feature_summary,
                "source_feature_rows": source_feature_rows,
                "registry": summarize_math_engine_registry(),
                "idempotent_reuse": bool(
                    summary_rows_persisted
                    and _normalize_text(summary_rows_persisted[-1].get("snapshot_id")) == _normalize_text(summary_row.get("snapshot_id"))
                ),
                "storage": storage.health(),
                "unresolved_blockers": [] if row_validation["ok"] else list(row_validation.get("errors", [])),
                "join_diagnostics": {
                    "feature_context_count": len(grouped_contexts),
                    "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
                    "engine_row_count": len(engine_rows_persisted),
                    "summary_row_count": len(summary_rows_persisted),
                    "missing_engine_row_count": len(missing_engine_rows),
                    "source_feature_row_count": len(source_feature_rows),
                    "source_feature_snapshot_count": _normalize_int(source_feature_summary.get("feature_snapshot_count"), len(source_feature_rows)),
                    "source_feature_definition_count": _normalize_int(source_feature_summary.get("feature_definition_count"), len(list_feature_definition_ids())),
                    "context_sizes": dict(Counter(len(context["feature_rows"]) for context in grouped_contexts)),
                },
            }
            return {
                **math_dataset_summary,
                "math_engine_rows": engine_rows_persisted,
                "math_engine_lineage_edges": [dict(row) for row in lineage_edges],
                "math_engine_summary_rows": summary_rows_persisted,
                "math_engine_population_summary": summary_row,
                "math_engine_population_summary_id": _normalize_text(summary_row.get("snapshot_id")),
                "math_engine_evidence_package_id": math_evidence_package_id,
                "math_engine_alignment_rows": alignment_rows_result,
                "math_engine_lifecycle_rows": lifecycle_rows,
                "math_engine_definition_ids": list_math_engine_definition_ids(),
                "math_engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
                "math_engine_row_count": len(engine_rows_persisted),
                "engine_row_count": len(engine_rows_persisted),
                "math_engine_context_count": len(grouped_contexts),
                "math_engine_dataset_row_count": len({row.get("dataset_row_id") for row in engine_rows_persisted if row.get("dataset_row_id")}),
                "math_engine_validation": row_validation,
                "source_feature_snapshot": feature_snapshot,
                "source_feature_population_summary": source_feature_summary,
                "source_feature_rows": source_feature_rows,
            }
        finally:
            certification_runtime.close()
            lifecycle_runtime.close()
    finally:
        if close_storage:
            storage.close()


def build_math_engine_population_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    try:
        storage = _default_storage(storage_path, backend=backend)
        try:
            return _load_math_engine_population_snapshot(
                storage,
                backend=backend,
                dataset_id=dataset_id,
                batch_id=batch_id,
            )
        finally:
            storage.close()
    except Exception as exc:
        return {
            "ok": False,
            "status": "math_engine_population_snapshot_error",
            "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
            "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
            "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
            "batch_id": _normalize_text(batch_id),
            "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
            "dataset_row_count": 0,
            "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
            "engine_row_count": 0,
            "math_engine_row_count": 0,
            "math_engine_rows": [],
            "math_engine_summary_rows": [],
            "math_engine_population_summary": {},
            "math_engine_population_summary_id": "",
            "math_engine_evidence_package_id": "",
            "math_engine_lineage_edges": [],
            "math_engine_alignment_rows": [],
            "math_engine_lifecycle_rows": [],
            "dataset_certification_status": "missing",
            "dataset_certification_id": "",
            "lifecycle_state": "missing",
            "source_feature_population_snapshot": {},
            "source_feature_population_summary": {},
            "source_feature_rows": [],
            "source_feature_batch_id": "",
            "source_feature_certification_id": "",
            "source_feature_dataset_certification_id": "",
            "source_feature_evidence_package_id": "",
            "source_feature_population_summary_id": "",
            "join_diagnostics": {},
            "registry": summarize_math_engine_registry(),
            "validation": {},
            "storage": {},
            "unresolved_blockers": [str(exc)],
            "readiness": "blocked",
            "validation_state": "rejected",
            "source_feature_snapshot_count": 0,
            "feature_context_count": 0,
            "warnings": [str(exc)],
        }


def get_math_engine_population_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_NFL_HISTORICAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    try:
        return build_math_engine_population_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=batch_id,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "math_engine_population_snapshot_error",
            "schema_version": MATH_ENGINE_POPULATION_SCHEMA_VERSION,
            "dataset_id": DEFAULT_MATH_ENGINE_DATASET_ID,
            "dataset_name": DEFAULT_MATH_ENGINE_DATASET_NAME,
            "batch_id": _normalize_text(batch_id),
            "version_id": MATH_ENGINE_TRANSFORMATION_VERSION,
            "dataset_row_count": 0,
            "engine_definition_count": len(_MATH_ENGINE_DEFINITIONS),
            "engine_row_count": 0,
            "math_engine_row_count": 0,
            "math_engine_rows": [],
            "math_engine_summary_rows": [],
            "math_engine_population_summary": {},
            "math_engine_population_summary_id": "",
            "math_engine_evidence_package_id": "",
            "math_engine_lineage_edges": [],
            "math_engine_alignment_rows": [],
            "math_engine_lifecycle_rows": [],
            "dataset_certification_status": "missing",
            "dataset_certification_id": "",
            "lifecycle_state": "missing",
            "source_feature_population_snapshot": {},
            "source_feature_population_summary": {},
            "source_feature_rows": [],
            "source_feature_batch_id": "",
            "source_feature_certification_id": "",
            "source_feature_dataset_certification_id": "",
            "source_feature_evidence_package_id": "",
            "source_feature_population_summary_id": "",
            "join_diagnostics": {},
            "registry": summarize_math_engine_registry(),
            "validation": {},
            "storage": {},
            "unresolved_blockers": [str(exc)],
            "readiness": "blocked",
            "validation_state": "rejected",
            "source_feature_snapshot_count": 0,
            "feature_context_count": 0,
            "warnings": [str(exc)],
        }


__all__ = [
    "CANONICAL_MATH_ENGINE_SNAPSHOT_GRAIN_ID",
    "DEFAULT_MATH_ENGINE_ASSET_CLASS",
    "DEFAULT_MATH_ENGINE_DATASET_ID",
    "DEFAULT_MATH_ENGINE_DATASET_NAME",
    "DEFAULT_MATH_ENGINE_ENGINE_OWNER",
    "DEFAULT_MATH_ENGINE_MARKET",
    "DEFAULT_MATH_ENGINE_MARKET_TYPE",
    "DEFAULT_MATH_ENGINE_OWNER",
    "DEFAULT_MATH_ENGINE_OUTPUT_NAMESPACE",
    "DEFAULT_MATH_ENGINE_PORTABILITY_CLASSIFICATION",
    "DEFAULT_MATH_ENGINE_PROVIDER",
    "DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID",
    "DEFAULT_MATH_ENGINE_RESEARCH_ASSET_NAME",
    "DEFAULT_MATH_ENGINE_SOURCE_KEY",
    "DEFAULT_MATH_ENGINE_SOURCE_NAME",
    "DEFAULT_MATH_ENGINE_SOURCE_TYPE",
    "DEFAULT_MATH_ENGINE_STORAGE_PATH",
    "MATH_ENGINE_BATCH_KIND",
    "MATH_ENGINE_DEFINITION_VERSION",
    "MATH_ENGINE_POPULATION_SCHEMA_VERSION",
    "MATH_ENGINE_ROW_KIND",
    "MATH_ENGINE_SUMMARY_ROW_KIND",
    "MATH_ENGINE_TRANSFORMATION_VERSION",
    "MathEngineDefinition",
    "MathEngineSnapshotContext",
    "build_math_engine_population",
    "build_math_engine_population_dashboard_snapshot",
    "build_math_engine_snapshot_context",
    "build_math_engine_snapshot_context_id",
    "build_math_engine_value_identity",
    "get_math_engine_definition",
    "get_math_engine_population_snapshot_for_dashboard",
    "list_math_engine_definition_ids",
    "list_math_engine_definitions",
    "summarize_math_engine_registry",
    "validate_math_engine_registry",
    "validate_math_engine_rows",
]
