from __future__ import annotations

"""Reusable signal population from certified mathematical-engine outputs.

The signal layer is intentionally observation-only. It reads only persisted
Phase 5.2 mathematical-engine outputs and the math-layer summary metadata,
derives deterministic signal observations, persists a queryable signal batch,
and advances the associated research asset through certification and lifecycle
owners without creating a parallel framework.
"""

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.core.model_probability import get_confidence_grade
from src.data.data_paths import get_runtime_data_path
from src.data.historical_research_asset_certification_runtime import (
    HistoricalResearchAssetCertificationRuntime,
    ResearchAssetCertificationContract,
    build_historical_dataset_certification_row,
)
from src.data.historical_research_database import HISTORICAL_DATASET_CUTOFF_POLICY_ID
from src.data.math_engine_population import (
    DEFAULT_MATH_ENGINE_DATASET_ID,
    DEFAULT_MATH_ENGINE_RESEARCH_ASSET_ID,
    MATH_ENGINE_BATCH_KIND,
    MATH_ENGINE_DEFINITION_VERSION,
    MATH_ENGINE_ROW_KIND,
    MATH_ENGINE_TRANSFORMATION_VERSION,
    build_math_engine_population_dashboard_snapshot,
    list_math_engine_definition_ids,
)
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
from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


SIGNAL_POPULATION_SCHEMA_VERSION = "src.market_intelligence.signal_population.v1"
SIGNAL_DEFINITION_VERSION = "phase5.3.signal_definitions.v1"
SIGNAL_TRANSFORMATION_VERSION = "phase5.3.signal_population.v1"
DEFAULT_SIGNAL_RESEARCH_ASSET_ID = "signal.sports.reusable_signals"
DEFAULT_SIGNAL_RESEARCH_ASSET_NAME = "Reusable Signals"
DEFAULT_SIGNAL_DATASET_ID = "dataset.sports.nfl.signal_snapshots"
DEFAULT_SIGNAL_DATASET_NAME = "nfl_signal_snapshots"
DEFAULT_SIGNAL_STORAGE_PATH = get_runtime_data_path("signal_population", "canonical_data.sqlite")
DEFAULT_SIGNAL_OWNER = "src.market_intelligence"
DEFAULT_SIGNAL_PROVIDER = "repository"
DEFAULT_SIGNAL_SOURCE_NAME = "math_engine_population"
DEFAULT_SIGNAL_SOURCE_TYPE = "math_engine_population"
DEFAULT_SIGNAL_SOURCE_KEY = "math_engine_population"
DEFAULT_SIGNAL_MARKET = "sports:nfl"
DEFAULT_SIGNAL_MARKET_TYPE = "signal"
DEFAULT_SIGNAL_ASSET_CLASS = "signal"
DEFAULT_SIGNAL_PROFILE_ID = "sports:nfl"
DEFAULT_SIGNAL_PORTABILITY_CLASSIFICATION = "cross_market_signal"
CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID = "dataset.sports.nfl.signal_snapshot.dataset_row_scope.v1"
SIGNAL_BATCH_KIND = "signal_population_summary"
SIGNAL_ROW_KIND = "signal_value"
SIGNAL_SUMMARY_ROW_KIND = "dataset_summary"
SIGNAL_USAGE_MODE = "observation_only"

SIGNAL_ALLOWED_CLASSIFICATIONS = {
    "direct",
    "deterministic_derived",
}
SIGNAL_ALLOWED_VALUE_TYPES = {
    "boolean",
    "float",
    "integer",
    "string",
    "timestamp",
}
SIGNAL_ALLOWED_MISSINGNESS_POLICIES = {
    "required",
    "nullable",
    "unavailable",
    "not_applicable",
    "invalid_source",
    "unsupported_context",
}
SIGNAL_ALLOWED_ENTITY_SCOPES = {
    "market_context",
    "data_quality_context",
    "regime_context",
}
SIGNAL_FORBIDDEN_INTENT_TOKENS = {
    "bet",
    "bets",
    "trade",
    "trades",
    "stake",
    "staking",
    "bankroll",
    "portfolio",
    "order",
    "orders",
    "recommend",
    "recommendation",
    "recommendations",
    "execution",
    "wager",
}
DEFAULT_SIGNAL_LINEAGE_REQUIREMENTS = (
    "dataset_id",
    "batch_id",
    "dataset_row_id",
    "decision_context_id",
    "decision_cutoff_time",
    "source_feature_certification_ids_json",
    "source_feature_alignment_certification_ids_json",
    "source_feature_snapshot_ids_json",
    "source_math_output_ids_json",
    "source_math_snapshot_ids_json",
    "source_math_lineage_ids_json",
    "source_math_certification_ids_json",
)
DEFAULT_SIGNAL_POINT_IN_TIME_CONSTRAINTS = (
    "inherit the certified historical dataset decision_cutoff_time",
    "reuse certified math outputs only",
    "no raw or normalized source rereads",
    "no post-cutoff updates",
    "no bets, trades, staking, execution intent, or recommendations",
    "no target-event leakage",
)
DEFAULT_SIGNAL_CUTOFF_SEMANTICS = (
    "inherit decision_cutoff_time from the certified historical dataset row, "
    "where decision_cutoff_time = scheduled_kickoff_time - five minutes"
)


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


def _resolve_target_team_id(payload: Mapping[str, Any]) -> str:
    return _normalize_text(
        payload.get("target_team_id")
        or payload.get("home_team_id")
        or payload.get("away_team_id")
    )


def _resolve_opponent_team_id(
    payload: Mapping[str, Any],
    *,
    target_team_id: str | None = None,
) -> str:
    target = _normalize_text(target_team_id or payload.get("target_team_id"))
    opponent = _normalize_text(payload.get("opponent_team_id"))
    if opponent:
        return opponent
    home_team_id = _normalize_text(payload.get("home_team_id"))
    away_team_id = _normalize_text(payload.get("away_team_id"))
    if target and target == home_team_id and away_team_id:
        return away_team_id
    if target and target == away_team_id and home_team_id:
        return home_team_id
    return _normalize_text(away_team_id or home_team_id)


def _load_math_context(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = _load_json_mapping(row.get("engine_context_json"))
    if not payload:
        payload = dict(row)
    result = dict(payload)
    for field in (
        "dataset_row_id",
        "decision_context_id",
        "feature_context_id",
        "event_id",
        "game_id",
        "season",
        "week",
        "home_team_id",
        "away_team_id",
        "team_side",
        "target_team_id",
        "opponent_team_id",
        "home_team",
        "away_team",
        "market_type",
        "selection",
        "book",
        "scheduled_kickoff_time",
        "decision_cutoff_time",
        "cutoff_policy_version",
        "point_in_time_status",
        "predictor_outcome_separation_status",
        "decision_readiness_status",
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
        "source_math_dataset_id",
        "source_math_dataset_name",
        "source_math_batch_id",
        "source_math_version_id",
        "source_math_certification_id",
        "source_math_dataset_certification_id",
        "source_math_population_summary_id",
        "source_math_evidence_package_id",
        "source_math_batch_lineage_id",
        "source_math_row_count",
        "source_math_snapshot_count",
        "source_math_definition_count",
    ):
        value = row.get(field)
        if field not in result or result.get(field) in (None, ""):
            result[field] = value
    return result


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _contains_forbidden_intent(text: str) -> bool:
    lowered = _normalize_text(text).lower()
    return any(token in lowered for token in SIGNAL_FORBIDDEN_INTENT_TOKENS)


def _math_value(row: Mapping[str, Any]) -> Any:
    value_json = row.get("engine_value_json")
    if value_json not in (None, ""):
        try:
            return json.loads(str(value_json))
        except json.JSONDecodeError:
            pass
    if row.get("engine_value_boolean") not in (None, ""):
        return bool(_normalize_int(row.get("engine_value_boolean"), 0))
    if row.get("engine_value_number") not in (None, ""):
        number = _normalize_float(row.get("engine_value_number"), 0.0)
        value_type = _normalize_text(row.get("value_type")).lower()
        if value_type == "integer":
            return int(round(number))
        return number
    text = row.get("engine_value_text")
    if text not in (None, ""):
        return _normalize_text(text)
    return None


def _math_missingness(row: Mapping[str, Any]) -> str:
    return _normalize_text(row.get("engine_missingness_state"), "missing_required")


def _math_freshness_value(summary_row: Mapping[str, Any]) -> float | int | str | None:
    freshness = _load_json_mapping(summary_row.get("source_feature_freshness_json"))
    values: list[float] = []
    for value in freshness.values():
        if value in (None, ""):
            continue
        number = _normalize_float(value, float("nan"))
        if math.isnan(number) or math.isinf(number):
            continue
        values.append(number)
    if not values:
        return None
    return int(max(values))


def _freshness_state_from_seconds(seconds: float | int | None) -> str:
    if seconds is None:
        return "missing"
    if seconds <= 900:
        return "fresh"
    if seconds <= 3600:
        return "aging"
    return "stale"


def _market_state(consensus_probability: float | None, pricing_gap: float | None, confidence_score: float | None) -> str:
    if consensus_probability is None or pricing_gap is None or confidence_score is None:
        return "uncertain"
    if confidence_score < 40.0 or pricing_gap > 0.10:
        return "uncertain"
    if pricing_gap <= 0.03 and confidence_score >= 75.0:
        return "stable"
    if pricing_gap <= 0.06 and confidence_score >= 55.0:
        return "balanced"
    return "dislocated"


def _regime_state(market_state: str, freshness_state: str, confidence_score: float | None, pricing_gap: float | None) -> str:
    if confidence_score is None or pricing_gap is None:
        return "missing"
    if freshness_state == "stale" or confidence_score < 40.0 or pricing_gap > 0.10:
        return "stressed"
    if market_state == "stable" and freshness_state == "fresh" and confidence_score >= 70.0:
        return "stable"
    if market_state in {"stable", "balanced"} and freshness_state in {"fresh", "aging"} and confidence_score >= 55.0:
        return "balanced"
    return "mixed"


@dataclass(slots=True, frozen=True)
class SignalDefinition:
    signal_id: str
    signal_name: str
    signal_family: str
    market_vertical: str
    entity_scope: str
    dataset_grain_compatibility: str
    signal_version: str
    classification: str
    value_type: str
    unit: str
    nullable: bool
    missingness_policy: str
    source_math_engine_output_refs: tuple[str, ...]
    source_math_summary_refs: tuple[str, ...]
    transformation_definition: str
    transformation_version: str
    cutoff_semantics: str
    point_in_time_constraints: tuple[str, ...]
    expected_range: str
    allowed_values: tuple[str, ...]
    signal_owner: str = DEFAULT_SIGNAL_OWNER
    signal_usage_mode: str = SIGNAL_USAGE_MODE
    lifecycle_state: str = "Signal Ready"
    certification_state: str = "definition_only"
    portability_classification: str = DEFAULT_SIGNAL_PORTABILITY_CLASSIFICATION
    lineage_requirements: tuple[str, ...] = DEFAULT_SIGNAL_LINEAGE_REQUIREMENTS

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_id", _normalize_text(self.signal_id))
        object.__setattr__(self, "signal_name", _normalize_text(self.signal_name))
        object.__setattr__(self, "signal_family", _normalize_text(self.signal_family))
        object.__setattr__(self, "market_vertical", _normalize_text(self.market_vertical))
        object.__setattr__(self, "entity_scope", _normalize_text(self.entity_scope))
        object.__setattr__(self, "dataset_grain_compatibility", _normalize_text(self.dataset_grain_compatibility))
        object.__setattr__(self, "signal_version", _normalize_text(self.signal_version, SIGNAL_DEFINITION_VERSION))
        object.__setattr__(self, "classification", _normalize_text(self.classification))
        object.__setattr__(self, "value_type", _normalize_text(self.value_type))
        object.__setattr__(self, "unit", _normalize_text(self.unit))
        object.__setattr__(self, "missingness_policy", _normalize_text(self.missingness_policy))
        object.__setattr__(
            self,
            "source_math_engine_output_refs",
            tuple(_normalize_text(value) for value in self.source_math_engine_output_refs if _normalize_text(value)),
        )
        object.__setattr__(
            self,
            "source_math_summary_refs",
            tuple(_normalize_text(value) for value in self.source_math_summary_refs if _normalize_text(value)),
        )
        object.__setattr__(self, "transformation_definition", _normalize_text(self.transformation_definition))
        object.__setattr__(self, "transformation_version", _normalize_text(self.transformation_version))
        object.__setattr__(self, "cutoff_semantics", _normalize_text(self.cutoff_semantics))
        object.__setattr__(
            self,
            "point_in_time_constraints",
            tuple(_normalize_text(value) for value in self.point_in_time_constraints if _normalize_text(value)),
        )
        object.__setattr__(self, "expected_range", _normalize_text(self.expected_range))
        object.__setattr__(
            self,
            "allowed_values",
            tuple(_normalize_text(value) for value in self.allowed_values if _normalize_text(value)),
        )
        object.__setattr__(self, "signal_owner", _normalize_text(self.signal_owner, DEFAULT_SIGNAL_OWNER))
        object.__setattr__(self, "signal_usage_mode", _normalize_text(self.signal_usage_mode, SIGNAL_USAGE_MODE))
        object.__setattr__(self, "lifecycle_state", _normalize_text(self.lifecycle_state))
        object.__setattr__(self, "certification_state", _normalize_text(self.certification_state))
        object.__setattr__(
            self,
            "portability_classification",
            _normalize_text(self.portability_classification, DEFAULT_SIGNAL_PORTABILITY_CLASSIFICATION),
        )
        object.__setattr__(
            self,
            "lineage_requirements",
            tuple(_normalize_text(value) for value in self.lineage_requirements if _normalize_text(value)),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_name": self.signal_name,
            "signal_family": self.signal_family,
            "market_vertical": self.market_vertical,
            "entity_scope": self.entity_scope,
            "dataset_grain_compatibility": self.dataset_grain_compatibility,
            "signal_version": self.signal_version,
            "classification": self.classification,
            "value_type": self.value_type,
            "unit": self.unit,
            "nullable": self.nullable,
            "missingness_policy": self.missingness_policy,
            "source_math_engine_output_refs": list(self.source_math_engine_output_refs),
            "source_math_summary_refs": list(self.source_math_summary_refs),
            "transformation_definition": self.transformation_definition,
            "transformation_version": self.transformation_version,
            "cutoff_semantics": self.cutoff_semantics,
            "point_in_time_constraints": list(self.point_in_time_constraints),
            "expected_range": self.expected_range,
            "allowed_values": list(self.allowed_values),
            "signal_owner": self.signal_owner,
            "signal_usage_mode": self.signal_usage_mode,
            "lifecycle_state": self.lifecycle_state,
            "certification_state": self.certification_state,
            "portability_classification": self.portability_classification,
            "lineage_requirements": list(self.lineage_requirements),
        }


@dataclass(slots=True, frozen=True)
class SignalSnapshotContext:
    dataset_id: str
    batch_id: str
    dataset_row_id: str
    decision_context_id: str
    event_id: str
    game_id: str
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
    feature_context_id: str
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
    source_math_dataset_id: str
    source_math_dataset_name: str
    source_math_batch_id: str
    source_math_version_id: str
    source_math_certification_id: str
    source_math_dataset_certification_id: str
    source_math_population_summary_id: str
    source_math_evidence_package_id: str
    source_math_batch_lineage_id: str
    source_math_row_count: int
    source_math_snapshot_count: int
    source_math_definition_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "batch_id": self.batch_id,
            "dataset_row_id": self.dataset_row_id,
            "decision_context_id": self.decision_context_id,
            "event_id": self.event_id,
            "game_id": self.game_id,
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
            "feature_context_id": self.feature_context_id,
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
            "source_math_dataset_id": self.source_math_dataset_id,
            "source_math_dataset_name": self.source_math_dataset_name,
            "source_math_batch_id": self.source_math_batch_id,
            "source_math_version_id": self.source_math_version_id,
            "source_math_certification_id": self.source_math_certification_id,
            "source_math_dataset_certification_id": self.source_math_dataset_certification_id,
            "source_math_population_summary_id": self.source_math_population_summary_id,
            "source_math_evidence_package_id": self.source_math_evidence_package_id,
            "source_math_batch_lineage_id": self.source_math_batch_lineage_id,
            "source_math_row_count": self.source_math_row_count,
            "source_math_snapshot_count": self.source_math_snapshot_count,
            "source_math_definition_count": self.source_math_definition_count,
        }


def _signal(
    signal_id: str,
    *,
    signal_name: str,
    signal_family: str,
    entity_scope: str,
    classification: str,
    value_type: str,
    unit: str,
    source_math_engine_output_refs: Sequence[str],
    transformation_definition: str,
    expected_range: str,
    source_math_summary_refs: Sequence[str] = (),
    allowed_values: Sequence[str] = (),
    nullable: bool = False,
    portability_classification: str = DEFAULT_SIGNAL_PORTABILITY_CLASSIFICATION,
) -> SignalDefinition:
    return SignalDefinition(
        signal_id=signal_id,
        signal_name=signal_name,
        signal_family=signal_family,
        market_vertical="sports",
        entity_scope=entity_scope,
        dataset_grain_compatibility=CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID,
        signal_version=SIGNAL_DEFINITION_VERSION,
        classification=classification,
        value_type=value_type,
        unit=unit,
        nullable=nullable,
        missingness_policy="required" if not nullable else "nullable",
        source_math_engine_output_refs=tuple(source_math_engine_output_refs),
        source_math_summary_refs=tuple(source_math_summary_refs),
        transformation_definition=transformation_definition,
        transformation_version=SIGNAL_TRANSFORMATION_VERSION,
        cutoff_semantics=DEFAULT_SIGNAL_CUTOFF_SEMANTICS,
        point_in_time_constraints=DEFAULT_SIGNAL_POINT_IN_TIME_CONSTRAINTS,
        expected_range=expected_range,
        allowed_values=tuple(allowed_values),
        portability_classification=portability_classification,
    )


_SIGNAL_DEFINITIONS: tuple[SignalDefinition, ...] = (
    _signal(
        "signal.sports.market.consensus_probability",
        signal_name="Consensus Probability",
        signal_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="probability",
        source_math_engine_output_refs=("math.sports.nfl.market.break_even_probability",),
        transformation_definition="direct_copy(math_engine_row.engine_value_number from break_even_probability)",
        expected_range="0.0 < p < 1.0",
    ),
    _signal(
        "signal.sports.market.pricing_gap",
        signal_name="Pricing Gap",
        signal_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="probability",
        source_math_engine_output_refs=("math.sports.nfl.market.odds_consistency_delta",),
        transformation_definition="direct_copy(math_engine_row.engine_value_number from odds_consistency_delta)",
        expected_range="0.0 <= gap <= 1.0",
    ),
    _signal(
        "signal.sports.market.fair_american_odds",
        signal_name="Fair American Odds",
        signal_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="integer",
        unit="american_odds",
        source_math_engine_output_refs=("math.sports.nfl.market.fair_american_odds",),
        transformation_definition="direct_copy(math_engine_row.engine_value_number from fair_american_odds)",
        expected_range="finite american odds",
    ),
    _signal(
        "signal.sports.market.fair_decimal_odds",
        signal_name="Fair Decimal Odds",
        signal_family="market_context",
        entity_scope="market_context",
        classification="direct",
        value_type="float",
        unit="decimal_odds",
        source_math_engine_output_refs=("math.sports.nfl.market.fair_decimal_odds",),
        transformation_definition="direct_copy(math_engine_row.engine_value_number from fair_decimal_odds)",
        expected_range="decimal odds greater than 1.0",
    ),
    _signal(
        "signal.sports.market.state",
        signal_name="Market State",
        signal_family="market_context",
        entity_scope="market_context",
        classification="deterministic_derived",
        value_type="string",
        unit="state",
        source_math_engine_output_refs=(
            "math.sports.nfl.market.break_even_probability",
            "math.sports.nfl.market.odds_consistency_delta",
            "math.sports.nfl.data_quality.confidence_score",
        ),
        transformation_definition=(
            "uncertain if confidence < 0.40 or pricing_gap > 0.10; "
            "stable if pricing_gap <= 0.03 and confidence >= 0.75; "
            "balanced if pricing_gap <= 0.06 and confidence >= 0.55; otherwise dislocated"
        ),
        expected_range="stable, balanced, dislocated, or uncertain",
        allowed_values=("stable", "balanced", "dislocated", "uncertain"),
    ),
    _signal(
        "signal.sports.data_quality.score",
        signal_name="Data Quality Score",
        signal_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="direct",
        value_type="float",
        unit="score",
        source_math_engine_output_refs=("math.sports.nfl.data_quality.score",),
        transformation_definition="direct_copy(math_engine_row.engine_value_number from data_quality.score)",
        expected_range="0.0 <= score <= 1.0",
    ),
    _signal(
        "signal.sports.data_quality.confidence_score",
        signal_name="Confidence Score",
        signal_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="direct",
        value_type="float",
        unit="score",
        source_math_engine_output_refs=("math.sports.nfl.data_quality.confidence_score",),
        transformation_definition="direct_copy(math_engine_row.engine_value_number from confidence_score)",
        expected_range="0.0 <= score <= 1.0",
    ),
    _signal(
        "signal.sports.data_quality.confidence_grade",
        signal_name="Confidence Grade",
        signal_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="direct",
        value_type="string",
        unit="grade",
        source_math_engine_output_refs=("math.sports.nfl.data_quality.confidence_grade",),
        transformation_definition="direct_copy(math_engine_row.engine_value_text from confidence_grade)",
        expected_range="A through F",
        allowed_values=("A", "B", "C", "D", "F"),
    ),
    _signal(
        "signal.sports.data_quality.freshness_state",
        signal_name="Freshness State",
        signal_family="data_quality_context",
        entity_scope="data_quality_context",
        classification="deterministic_derived",
        value_type="string",
        unit="state",
        source_math_engine_output_refs=(),
        source_math_summary_refs=("math.sports.nfl.math_engine_population_summary",),
        transformation_definition=(
            "max(feature freshness seconds from the certified math summary; "
            "fresh <= 900 seconds, aging <= 3600 seconds, stale > 3600 seconds)"
        ),
        expected_range="fresh, aging, stale, or missing",
        allowed_values=("fresh", "aging", "stale", "missing"),
        nullable=True,
    ),
    _signal(
        "signal.sports.regime.state",
        signal_name="Regime State",
        signal_family="regime_context",
        entity_scope="regime_context",
        classification="deterministic_derived",
        value_type="string",
        unit="state",
        source_math_engine_output_refs=(
            "math.sports.nfl.market.odds_consistency_delta",
            "math.sports.nfl.data_quality.confidence_score",
        ),
        source_math_summary_refs=("math.sports.nfl.math_engine_population_summary",),
        transformation_definition=(
            "stressed if freshness is stale or confidence < 0.40 or pricing_gap > 0.10; "
            "stable if market is stable, freshness is fresh, and confidence >= 0.70; "
            "balanced if market is stable or balanced, freshness is fresh or aging, and confidence >= 0.55; "
            "otherwise mixed"
        ),
        expected_range="stable, balanced, mixed, stressed, or missing",
        allowed_values=("stable", "balanced", "mixed", "stressed", "missing"),
    ),
)


def list_signal_definitions() -> list[dict[str, Any]]:
    return [definition.as_dict() for definition in _SIGNAL_DEFINITIONS]


def list_signal_definition_ids() -> list[str]:
    return [definition.signal_id for definition in _SIGNAL_DEFINITIONS]


def get_signal_definition(signal_id: str) -> dict[str, Any]:
    for definition in _SIGNAL_DEFINITIONS:
        if definition.signal_id == _normalize_text(signal_id):
            return definition.as_dict()
    raise KeyError(f"Unknown signal definition: {signal_id}")


def list_signal_families() -> list[str]:
    return sorted({definition.signal_family for definition in _SIGNAL_DEFINITIONS})


def summarize_signal_registry() -> dict[str, Any]:
    return {
        "schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
        "definition_version": SIGNAL_DEFINITION_VERSION,
        "transformation_version": SIGNAL_TRANSFORMATION_VERSION,
        "definition_count": len(_SIGNAL_DEFINITIONS),
        "signal_ids": list_signal_definition_ids(),
        "families": list_signal_families(),
        "classification_counts": dict(Counter(definition.classification for definition in _SIGNAL_DEFINITIONS)),
        "value_type_counts": dict(Counter(definition.value_type for definition in _SIGNAL_DEFINITIONS)),
        "usage_mode_counts": dict(Counter(definition.signal_usage_mode for definition in _SIGNAL_DEFINITIONS)),
        "definition_ids": list_signal_definition_ids(),
    }


def validate_signal_registry(definitions: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    candidate_definitions = [dict(definition) for definition in (definitions or list_signal_definitions())]
    errors: list[str] = []
    seen_ids: set[str] = set()
    for definition in candidate_definitions:
        signal_id = _normalize_text(definition.get("signal_id"))
        if not signal_id:
            errors.append("missing_signal_id")
            continue
        if signal_id in seen_ids:
            errors.append(f"duplicate_signal_definition:{signal_id}")
        seen_ids.add(signal_id)
        if _contains_forbidden_intent(signal_id) or _contains_forbidden_intent(definition.get("signal_name")):
            errors.append(f"forbidden_decision_intent_token:{signal_id}")
        if _normalize_text(definition.get("signal_usage_mode"), SIGNAL_USAGE_MODE) != SIGNAL_USAGE_MODE:
            errors.append(f"invalid_signal_usage_mode:{signal_id}")
        if _normalize_text(definition.get("classification")) not in SIGNAL_ALLOWED_CLASSIFICATIONS:
            errors.append(f"invalid_signal_classification:{signal_id}")
        if _normalize_text(definition.get("value_type")) not in SIGNAL_ALLOWED_VALUE_TYPES:
            errors.append(f"invalid_signal_value_type:{signal_id}")
        if _normalize_text(definition.get("missingness_policy")) not in SIGNAL_ALLOWED_MISSINGNESS_POLICIES:
            errors.append(f"invalid_signal_missingness_policy:{signal_id}")
        if _normalize_text(definition.get("entity_scope")) not in SIGNAL_ALLOWED_ENTITY_SCOPES:
            errors.append(f"invalid_signal_entity_scope:{signal_id}")
        if not (_normalize_text(definition.get("source_math_engine_output_refs")) or _normalize_text(definition.get("source_math_summary_refs"))):
            errors.append(f"missing_math_source_refs:{signal_id}")
    return {
        "ok": not errors,
        "status": "validated" if not errors else "rejected",
        "definition_count": len(candidate_definitions),
        "errors": list(dict.fromkeys(errors)),
        "registry": summarize_signal_registry(),
    }


def _signal_snapshot_context_id(context: SignalSnapshotContext | Mapping[str, Any]) -> str:
    payload = context.as_dict() if isinstance(context, SignalSnapshotContext) else dict(context)
    return _stable_id(
        "signal_snapshot_context",
        payload.get("dataset_id"),
        payload.get("batch_id"),
        payload.get("dataset_row_id"),
        payload.get("decision_context_id"),
        payload.get("source_math_batch_id"),
        payload.get("scheduled_kickoff_time"),
        payload.get("decision_cutoff_time"),
    )


def build_signal_snapshot_context(
    *,
    dataset_id: str,
    batch_id: str,
    summary_row: Mapping[str, Any],
    math_rows: Sequence[Mapping[str, Any]],
    context_rows: Sequence[Mapping[str, Any]],
) -> SignalSnapshotContext:
    representative_row = dict(context_rows[0]) if context_rows else dict(math_rows[0])
    representative = _load_math_context(representative_row)
    target_team_id = _resolve_target_team_id(representative)
    opponent_team_id = _resolve_opponent_team_id(
        representative,
        target_team_id=target_team_id,
    )
    return SignalSnapshotContext(
        dataset_id=dataset_id,
        batch_id=batch_id,
        dataset_row_id=_normalize_text(representative.get("dataset_row_id")),
        decision_context_id=_normalize_text(representative.get("decision_context_id")),
        event_id=_normalize_text(representative.get("event_id")),
        game_id=_normalize_text(representative.get("game_id") or representative.get("event_id")),
        season=_normalize_int(representative.get("season")),
        week=_normalize_int(representative.get("week")),
        home_team_id=_normalize_text(representative.get("home_team_id")),
        away_team_id=_normalize_text(representative.get("away_team_id")),
        team_side=_normalize_text(representative.get("team_side")),
        target_team_id=target_team_id,
        opponent_team_id=opponent_team_id,
        home_team=_normalize_text(representative.get("home_team")),
        away_team=_normalize_text(representative.get("away_team")),
        market_type=_normalize_text(representative.get("market_type")),
        selection=_normalize_text(representative.get("selection")),
        book=_normalize_text(representative.get("book"), "consensus"),
        scheduled_kickoff_time=_to_iso8601_utc(representative.get("scheduled_kickoff_time")),
        decision_cutoff_time=_to_iso8601_utc(representative.get("decision_cutoff_time")),
        cutoff_policy_version=_normalize_text(representative.get("cutoff_policy_version"), HISTORICAL_DATASET_CUTOFF_POLICY_ID),
        point_in_time_status=_normalize_text(representative.get("point_in_time_status"), "safe"),
        predictor_outcome_separation_status=_normalize_text(representative.get("predictor_outcome_separation_status"), "separated"),
        decision_readiness_status=_normalize_text(representative.get("decision_readiness_status"), "decision_ready"),
        feature_context_id=_normalize_text(representative.get("feature_context_id")),
        source_feature_dataset_id=_normalize_text(summary_row.get("source_feature_dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID),
        source_feature_dataset_name=_normalize_text(summary_row.get("source_feature_dataset_name"), DEFAULT_SIGNAL_DATASET_NAME),
        source_feature_batch_id=_normalize_text(summary_row.get("source_feature_batch_id")),
        source_feature_version_id=_normalize_text(summary_row.get("source_feature_version_id"), MATH_ENGINE_TRANSFORMATION_VERSION),
        source_feature_certification_id=_normalize_text(summary_row.get("source_feature_certification_id")),
        source_feature_dataset_certification_id=_normalize_text(summary_row.get("source_feature_dataset_certification_id")),
        source_feature_population_summary_id=_normalize_text(summary_row.get("source_feature_population_summary_id")),
        source_feature_evidence_package_id=_normalize_text(summary_row.get("source_feature_evidence_package_id")),
        source_feature_batch_lineage_id=_normalize_text(summary_row.get("source_feature_batch_lineage_id")),
        source_feature_row_count=_normalize_int(summary_row.get("source_feature_row_count"), len(context_rows)),
        source_feature_snapshot_count=_normalize_int(summary_row.get("source_feature_snapshot_count"), len(context_rows)),
        source_feature_definition_count=_normalize_int(summary_row.get("source_feature_definition_count")),
        source_math_dataset_id=_normalize_text(summary_row.get("dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID),
        source_math_dataset_name=_normalize_text(summary_row.get("dataset_name"), "nfl_math_engine_snapshots"),
        source_math_batch_id=_normalize_text(summary_row.get("batch_id")),
        source_math_version_id=_normalize_text(summary_row.get("version_id"), MATH_ENGINE_TRANSFORMATION_VERSION),
        source_math_certification_id=_normalize_text(summary_row.get("certification_id")),
        source_math_dataset_certification_id=_normalize_text(summary_row.get("dataset_certification_id")),
        source_math_population_summary_id=_normalize_text(summary_row.get("snapshot_id")),
        source_math_evidence_package_id=_normalize_text(summary_row.get("evidence_package_id")),
        source_math_batch_lineage_id=_normalize_text(summary_row.get("lineage_id")),
        source_math_row_count=_normalize_int(summary_row.get("record_count"), len(math_rows)),
        source_math_snapshot_count=_normalize_int(summary_row.get("source_math_snapshot_count"), len(math_rows)),
        source_math_definition_count=_normalize_int(summary_row.get("source_math_definition_count"), len(list_math_engine_definition_ids())),
    )


def build_signal_snapshot_context_id(context: SignalSnapshotContext | Mapping[str, Any]) -> str:
    return _signal_snapshot_context_id(context)


def build_signal_value_identity(definition: SignalDefinition | Mapping[str, Any], context: SignalSnapshotContext | Mapping[str, Any], *, value: Any = None, source_math_snapshot_ids: Mapping[str, Any] | None = None) -> str:
    signal_definition = definition.as_dict() if isinstance(definition, SignalDefinition) else dict(definition)
    payload = context.as_dict() if isinstance(context, SignalSnapshotContext) else dict(context)
    return _stable_id(
        "signal_snapshot",
        payload.get("batch_id"),
        payload.get("dataset_row_id"),
        payload.get("decision_context_id"),
        signal_definition.get("signal_id"),
        signal_definition.get("signal_version"),
        signal_definition.get("transformation_version"),
        _as_json(source_math_snapshot_ids or {}),
        _as_json(value),
    )


def _signal_value_type_columns(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {
            "signal_value_json": _as_json(value),
            "signal_value_text": None,
            "signal_value_number": None,
            "signal_value_boolean": int(value),
        }
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {
            "signal_value_json": _as_json(value),
            "signal_value_text": None,
            "signal_value_number": value,
            "signal_value_boolean": None,
        }
    if value is None:
        return {
            "signal_value_json": None,
            "signal_value_text": None,
            "signal_value_number": None,
            "signal_value_boolean": None,
        }
    return {
        "signal_value_json": _as_json(value),
        "signal_value_text": _normalize_text(value),
        "signal_value_number": None,
        "signal_value_boolean": None,
    }


def _signal_freshness_map(summary_row: Mapping[str, Any]) -> dict[str, Any]:
    raw = _load_json_mapping(summary_row.get("source_feature_freshness_json"))
    freshness: dict[str, Any] = {}
    for key, value in raw.items():
        if value in (None, ""):
            continue
        number = _normalize_float(value, float("nan"))
        if math.isnan(number) or math.isinf(number):
            continue
        freshness[str(key)] = int(number)
    return freshness


def _merge_source_mappings(
    rows: Sequence[Mapping[str, Any]],
    column: str,
    *,
    normalize_values: bool = False,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for row in rows:
        mapping = _load_json_mapping(row.get(column))
        for key, value in mapping.items():
            key_text = _normalize_text(key)
            if not key_text:
                continue
            if normalize_values:
                value_text = _normalize_text(value)
                if not value_text:
                    continue
                merged.setdefault(key_text, value_text)
                continue
            if value in (None, ""):
                continue
            merged.setdefault(key_text, value)
    return merged


def _max_freshness_seconds(freshness: Mapping[str, Any]) -> float | int | None:
    values: list[float] = []
    for value in freshness.values():
        if value in (None, ""):
            continue
        number = _normalize_float(value, float("nan"))
        if math.isnan(number) or math.isinf(number):
            continue
        values.append(number)
    if not values:
        return None
    return int(max(values))


def _source_feature_maps_from_math_lookup(
    math_lookup: Mapping[str, Mapping[str, Any]],
    summary_row: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    context_rows = [dict(row) for row in math_lookup.values() if isinstance(row, Mapping)]
    fallback_ids = _load_json_mapping(summary_row.get("source_feature_ids_json")) or _load_json_mapping(summary_row.get("source_feature_snapshot_ids_json"))
    return {
        "source_feature_ids": _merge_source_mappings(context_rows, "source_feature_ids_json", normalize_values=True) or fallback_ids,
        "source_feature_snapshot_ids": _merge_source_mappings(context_rows, "source_feature_snapshot_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_snapshot_ids_json")),
        "source_feature_lineage_ids": _merge_source_mappings(context_rows, "source_feature_lineage_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_lineage_ids_json")),
        "source_feature_certification_ids": _merge_source_mappings(context_rows, "source_feature_certification_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_certification_ids_json")),
        "source_feature_dataset_certification_ids": _merge_source_mappings(context_rows, "source_feature_dataset_certification_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_dataset_certification_ids_json")),
        "source_feature_alignment_certification_ids": _merge_source_mappings(context_rows, "source_feature_alignment_certification_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_alignment_certification_ids_json")),
        "source_feature_missingness": _merge_source_mappings(context_rows, "source_feature_missingness_json") or _load_json_mapping(summary_row.get("source_feature_missingness_json")),
        "source_feature_freshness": _merge_source_mappings(context_rows, "source_feature_freshness_json") or _load_json_mapping(summary_row.get("source_feature_freshness_json")),
        "source_feature_value_types": _merge_source_mappings(context_rows, "source_feature_value_types_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_value_types_json")),
        "source_feature_values": _merge_source_mappings(context_rows, "source_feature_values_json") or _load_json_mapping(summary_row.get("source_feature_values_json")),
    }


def _apply_signal_summary_source_feature_maps(
    summary_row: dict[str, Any],
    signal_rows: Sequence[Mapping[str, Any]],
) -> None:
    fallback_ids = _load_json_mapping(summary_row.get("source_feature_ids_json")) or _load_json_mapping(summary_row.get("source_feature_snapshot_ids_json"))
    summary_row["source_feature_ids_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_ids_json", normalize_values=True) or fallback_ids
    )
    summary_row["source_feature_snapshot_ids_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_snapshot_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_snapshot_ids_json"))
    )
    summary_row["source_feature_lineage_ids_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_lineage_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_lineage_ids_json"))
    )
    summary_row["source_feature_certification_ids_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_certification_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_certification_ids_json"))
    )
    summary_row["source_feature_dataset_certification_ids_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_dataset_certification_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_dataset_certification_ids_json"))
    )
    summary_row["source_feature_alignment_certification_ids_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_alignment_certification_ids_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_alignment_certification_ids_json"))
    )
    summary_row["source_feature_missingness_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_missingness_json") or _load_json_mapping(summary_row.get("source_feature_missingness_json"))
    )
    summary_row["source_feature_freshness_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_freshness_json") or _load_json_mapping(summary_row.get("source_feature_freshness_json"))
    )
    summary_row["source_feature_value_types_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_value_types_json", normalize_values=True) or _load_json_mapping(summary_row.get("source_feature_value_types_json"))
    )
    summary_row["source_feature_values_json"] = _as_json(
        _merge_source_mappings(signal_rows, "source_feature_values_json") or _load_json_mapping(summary_row.get("source_feature_values_json"))
    )


def _signal_source_maps(
    *,
    definition: SignalDefinition,
    context: SignalSnapshotContext,
    summary_row: Mapping[str, Any],
    math_lookup: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    source_feature_maps = _source_feature_maps_from_math_lookup(math_lookup, summary_row)
    source_math_snapshot_ids: dict[str, str] = {}
    source_math_lineage_ids: dict[str, str] = {}
    source_math_certification_ids: dict[str, str] = {}
    source_math_dataset_certification_ids: dict[str, str] = {}
    source_math_missingness: dict[str, str] = {}
    source_math_value_types: dict[str, str] = {}
    source_math_values: dict[str, Any] = {}
    source_math_output_ids: dict[str, str] = {}
    for ref in definition.source_math_engine_output_refs:
        row = math_lookup.get(ref)
        if row is None:
            continue
        source_math_output_ids[ref] = _normalize_text(row.get("output_feature_id") or row.get("engine_id"))
        source_math_snapshot_ids[ref] = _normalize_text(row.get("snapshot_id"))
        source_math_lineage_ids[ref] = _normalize_text(row.get("engine_lineage_id"))
        source_math_certification_ids[ref] = _normalize_text(row.get("certification_id"))
        source_math_dataset_certification_ids[ref] = _normalize_text(row.get("dataset_certification_id"))
        source_math_missingness[ref] = _math_missingness(row)
        source_math_value_types[ref] = _normalize_text(row.get("value_type"))
        source_math_values[ref] = _math_value(row)
    if definition.source_math_summary_refs:
        source_math_output_ids["summary"] = _normalize_text(summary_row.get("snapshot_id"))
        source_math_snapshot_ids["summary"] = _normalize_text(summary_row.get("snapshot_id"))
        source_math_lineage_ids["summary"] = _normalize_text(summary_row.get("lineage_id"))
        source_math_certification_ids["summary"] = _normalize_text(summary_row.get("certification_id"))
        source_math_dataset_certification_ids["summary"] = _normalize_text(summary_row.get("dataset_certification_id"))
        source_math_missingness["summary"] = _normalize_text(summary_row.get("validation_state"), "validated")
        source_math_value_types["summary"] = "string"
        source_math_values["summary"] = {
            "freshness_seconds": _signal_freshness_map(summary_row),
        }

    return {
        "source_math_output_ids": source_math_output_ids,
        "source_math_snapshot_ids": source_math_snapshot_ids,
        "source_math_lineage_ids": source_math_lineage_ids,
        "source_math_certification_ids": source_math_certification_ids,
        "source_math_dataset_certification_ids": source_math_dataset_certification_ids,
        "source_math_missingness": source_math_missingness,
        "source_math_freshness": source_feature_maps["source_feature_freshness"],
        "source_math_value_types": source_math_value_types,
        "source_math_values": source_math_values,
        "source_feature_ids": source_feature_maps["source_feature_ids"],
        "source_feature_snapshot_ids": source_feature_maps["source_feature_snapshot_ids"],
        "source_feature_lineage_ids": source_feature_maps["source_feature_lineage_ids"],
        "source_feature_certification_ids": source_feature_maps["source_feature_certification_ids"],
        "source_feature_dataset_certification_ids": source_feature_maps["source_feature_dataset_certification_ids"],
        "source_feature_alignment_certification_ids": source_feature_maps["source_feature_alignment_certification_ids"],
        "source_feature_missingness": source_feature_maps["source_feature_missingness"],
        "source_feature_freshness": source_feature_maps["source_feature_freshness"],
        "source_feature_value_types": source_feature_maps["source_feature_value_types"],
        "source_feature_values": source_feature_maps["source_feature_values"],
    }


def _signal_value_and_missingness(
    definition: SignalDefinition,
    *,
    context: SignalSnapshotContext,
    summary_row: Mapping[str, Any],
    math_lookup: Mapping[str, Mapping[str, Any]],
) -> tuple[Any, str, str, dict[str, Any]]:
    sources = _signal_source_maps(definition=definition, context=context, summary_row=summary_row, math_lookup=math_lookup)
    source_math_values = dict(sources["source_math_values"])
    source_math_snapshot_ids = dict(sources["source_math_snapshot_ids"])
    source_math_missingness = dict(sources["source_math_missingness"])
    source_feature_freshness = dict(sources["source_feature_freshness"])
    direct_values = [value for value in source_math_values.values() if value not in (None, "")]
    if definition.signal_id == "signal.sports.market.consensus_probability":
        row = math_lookup.get("math.sports.nfl.market.break_even_probability")
        if row is None:
            return None, "missing_required", "missing break_even_probability math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.market.pricing_gap":
        row = math_lookup.get("math.sports.nfl.market.odds_consistency_delta")
        if row is None:
            return None, "missing_required", "missing odds_consistency_delta math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.market.fair_american_odds":
        row = math_lookup.get("math.sports.nfl.market.fair_american_odds")
        if row is None:
            return None, "missing_required", "missing fair_american_odds math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.market.fair_decimal_odds":
        row = math_lookup.get("math.sports.nfl.market.fair_decimal_odds")
        if row is None:
            return None, "missing_required", "missing fair_decimal_odds math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.market.state":
        consensus_probability = _normalize_float(_math_value(math_lookup.get("math.sports.nfl.market.break_even_probability")), float("nan"))
        pricing_gap = _normalize_float(_math_value(math_lookup.get("math.sports.nfl.market.odds_consistency_delta")), float("nan"))
        confidence_score = _normalize_float(_math_value(math_lookup.get("math.sports.nfl.data_quality.confidence_score")), float("nan"))
        if any(math.isnan(value) for value in (consensus_probability, pricing_gap, confidence_score)):
            return None, "missing_required", "missing math inputs for market state", sources
        value = _market_state(consensus_probability, pricing_gap, confidence_score)
        return value, "present", "", sources
    if definition.signal_id == "signal.sports.data_quality.score":
        row = math_lookup.get("math.sports.nfl.data_quality.score")
        if row is None:
            return None, "missing_required", "missing data_quality.score math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.data_quality.confidence_score":
        row = math_lookup.get("math.sports.nfl.data_quality.confidence_score")
        if row is None:
            return None, "missing_required", "missing confidence_score math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.data_quality.confidence_grade":
        row = math_lookup.get("math.sports.nfl.data_quality.confidence_grade")
        if row is None:
            return None, "missing_required", "missing confidence_grade math output", sources
        return _math_value(row), _math_missingness(row), "", sources
    if definition.signal_id == "signal.sports.data_quality.freshness_state":
        freshness_seconds = _max_freshness_seconds(source_feature_freshness)
        freshness_state = _freshness_state_from_seconds(freshness_seconds if isinstance(freshness_seconds, (int, float)) else None)
        return freshness_state, "present" if freshness_state != "missing" else "missing_required", "", sources
    if definition.signal_id == "signal.sports.regime.state":
        pricing_gap = _normalize_float(_math_value(math_lookup.get("math.sports.nfl.market.odds_consistency_delta")), float("nan"))
        confidence_score = _normalize_float(_math_value(math_lookup.get("math.sports.nfl.data_quality.confidence_score")), float("nan"))
        market_state = _market_state(
            _normalize_float(_math_value(math_lookup.get("math.sports.nfl.market.break_even_probability")), float("nan")),
            pricing_gap,
            confidence_score,
        )
        freshness_seconds = _max_freshness_seconds(source_feature_freshness)
        freshness_state = _freshness_state_from_seconds(freshness_seconds if isinstance(freshness_seconds, (int, float)) else None)
        if any(math.isnan(value) for value in (pricing_gap, confidence_score)):
            return None, "missing_required", "missing math inputs for regime state", sources
        value = _regime_state(market_state, freshness_state, confidence_score, pricing_gap)
        return value, "present" if value != "missing" else "missing_required", "", sources
    if not direct_values:
        return None, "missing_required", f"missing math inputs for {definition.signal_id}", sources
    if definition.value_type == "integer":
        return int(round(_normalize_float(direct_values[0]))), "present", "", sources
    if definition.value_type == "float":
        return _normalize_float(direct_values[0]), "present", "", sources
    if definition.value_type == "boolean":
        return bool(direct_values[0]), "present", "", sources
    return _normalize_text(direct_values[0]), "present", "", sources


def _required_row_fields() -> tuple[str, ...]:
    return (
        "dataset_id",
        "dataset_name",
        "owner",
        "sport",
        "signal_pack",
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
        "signal_pack_version",
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
        "source_math_dataset_id",
        "source_math_dataset_name",
        "source_math_batch_id",
        "source_math_version_id",
        "source_math_certification_id",
        "source_math_dataset_certification_id",
        "source_math_population_summary_id",
        "source_math_evidence_package_id",
        "source_math_batch_lineage_id",
        "source_math_row_count",
        "source_math_snapshot_count",
        "source_math_definition_count",
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
        "signal_usage_mode",
        "signal_id",
        "signal_name",
        "signal_family",
        "signal_version",
        "classification",
        "value_type",
        "unit",
        "signal_owner",
        "entity_scope",
        "dataset_grain_compatibility",
        "transformation_version",
        "missingness_policy",
        "signal_context_id",
        "signal_value_json",
        "signal_definition_json",
        "signal_context_json",
        "signal_snapshot_grain_id",
        "signal_registry_schema_version",
        "signal_lineage_id",
        "signal_evidence_id",
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
        "source_math_output_ids_json",
        "source_math_snapshot_ids_json",
        "source_math_lineage_ids_json",
        "source_math_certification_ids_json",
        "source_math_dataset_certification_ids_json",
        "source_math_missingness_json",
        "source_math_freshness_json",
        "source_math_value_types_json",
        "source_math_values_json",
        "missing_required_assets_json",
        "evidence_package_id",
        "record_count",
        "signal_count",
        "signal_values_json",
        "summary_json",
        "payload_json",
    )


def validate_signal_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    base = validate_dataset_rows(rows, required_fields=_required_row_fields())
    missing_rows = list(base.get("missing_rows", []))
    missing_fields = [field for row in missing_rows for field in row.get("missing_fields", [])]
    duplicate_snapshot_ids: list[str] = []
    seen_snapshot_ids: set[str] = set()
    duplicate_signal_keys: list[str] = []
    seen_signal_keys: set[str] = set()
    usage_mode_errors: list[str] = []
    for row in rows:
        snapshot_id = _normalize_text(row.get("snapshot_id"))
        if snapshot_id:
            if snapshot_id in seen_snapshot_ids and snapshot_id not in duplicate_snapshot_ids:
                duplicate_snapshot_ids.append(snapshot_id)
            seen_snapshot_ids.add(snapshot_id)
        signal_key = "|".join(
            [
                _normalize_text(row.get("dataset_row_id")),
                _normalize_text(row.get("decision_context_id")),
                _normalize_text(row.get("signal_id")),
                _normalize_text(row.get("scheduled_kickoff_time")),
                _normalize_text(row.get("decision_cutoff_time")),
            ]
        )
        if signal_key in seen_signal_keys and signal_key not in duplicate_signal_keys:
            duplicate_signal_keys.append(signal_key)
        seen_signal_keys.add(signal_key)
        if _normalize_text(row.get("signal_usage_mode"), SIGNAL_USAGE_MODE) != SIGNAL_USAGE_MODE:
            usage_mode_errors.append(_normalize_text(row.get("signal_id")))

    required_fields_missing = list(dict.fromkeys(missing_fields))
    errors = list(
        dict.fromkeys(
            [
                *required_fields_missing,
                *[f"duplicate_snapshot_id:{value}" for value in duplicate_snapshot_ids],
                *[f"duplicate_signal_key:{value}" for value in duplicate_signal_keys],
                *[f"invalid_signal_usage_mode:{value}" for value in usage_mode_errors],
            ]
        )
    )
    return {
        "ok": not errors,
        "status": "validated" if not errors else "rejected",
        "row_count": len(rows),
        "error_count": len(errors),
        "warning_count": int(base.get("warning_count") or 0),
        "missing_rows": missing_rows,
        "missing_fields": required_fields_missing,
        "duplicate_snapshot_ids": duplicate_snapshot_ids,
        "duplicate_signal_keys": duplicate_signal_keys,
        "errors": errors,
        "base_validation": base,
    }


def _signal_population_batch_id(
    dataset_id: str,
    source_math_batch_id: str,
    *,
    contexts: Sequence[SignalSnapshotContext],
) -> str:
    context_signatures = [
        _stable_id(
            "signal_context_signature",
            context.dataset_row_id,
            context.decision_context_id,
            context.event_id,
            context.selection,
            context.book,
            context.scheduled_kickoff_time,
            context.decision_cutoff_time,
            _as_json(context.source_math_batch_id),
            _as_json(context.source_math_population_summary_id),
            _as_json(context.source_feature_batch_id),
            _as_json(context.source_feature_population_summary_id),
        )
        for context in contexts
    ]
    return _stable_id(
        "signal_population_batch",
        dataset_id,
        source_math_batch_id,
        SIGNAL_POPULATION_SCHEMA_VERSION,
        SIGNAL_DEFINITION_VERSION,
        SIGNAL_TRANSFORMATION_VERSION,
        _as_json(sorted(context_signatures)),
    )


def _signal_row_payload_and_values(
    *,
    definition: SignalDefinition,
    context: SignalSnapshotContext,
    summary_row: Mapping[str, Any],
    math_lookup: Mapping[str, Mapping[str, Any]],
    storage_location: str,
    created_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    value, missingness_state, missingness_reason, source_maps = _signal_value_and_missingness(
        definition,
        context=context,
        summary_row=summary_row,
        math_lookup=math_lookup,
    )
    signal_context = context.as_dict()
    signal_context["signal_id"] = definition.signal_id
    signal_context["signal_name"] = definition.signal_name
    signal_context["signal_family"] = definition.signal_family
    signal_context["signal_version"] = definition.signal_version
    signal_context["signal_usage_mode"] = definition.signal_usage_mode
    signal_context["classification"] = definition.classification
    signal_context["value_type"] = definition.value_type
    signal_context["created_at"] = created_at
    signal_context["signal_context_id"] = build_signal_snapshot_context_id(context)
    signal_context["source_math"] = {
        "summary_snapshot_id": context.source_math_population_summary_id,
        "batch_id": context.source_math_batch_id,
        "definition_ids": list(definition.source_math_engine_output_refs),
        "summary_refs": list(definition.source_math_summary_refs),
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

    signal_snapshot_id = build_signal_value_identity(
        definition,
        context,
        value=value,
        source_math_snapshot_ids=source_maps["source_math_snapshot_ids"],
    )
    signal_lineage_id = _stable_id(
        "signal_lineage",
        signal_snapshot_id,
        context.batch_id,
        definition.signal_id,
        _as_json(source_maps["source_math_snapshot_ids"]),
        _as_json(source_maps["source_math_lineage_ids"]),
        _as_json(source_maps["source_math_certification_ids"]),
        _as_json(source_maps["source_feature_snapshot_ids"]),
    )
    signal_evidence_id = _stable_id(
        "signal_evidence",
        signal_snapshot_id,
        context.batch_id,
        definition.signal_id,
        _as_json(source_maps["source_math_values"]),
        _as_json(source_maps["source_math_snapshot_ids"]),
        _as_json(value_json if value_json is not None else value_text),
        missingness_state,
    )
    signal_definition_json = definition.as_dict()
    payload = {
        "snapshot_id": signal_snapshot_id,
        "signal_id": definition.signal_id,
        "signal_name": definition.signal_name,
        "signal_family": definition.signal_family,
        "signal_version": definition.signal_version,
        "classification": definition.classification,
        "value_type": definition.value_type,
        "unit": definition.unit,
        "signal_owner": definition.signal_owner,
        "entity_scope": definition.entity_scope,
        "dataset_grain_compatibility": definition.dataset_grain_compatibility,
        "transformation_version": definition.transformation_version,
        "missingness_policy": definition.missingness_policy,
        "signal_context_id": build_signal_snapshot_context_id(context),
        "signal_value": value,
        "signal_missingness_state": missingness_state,
        "signal_missingness_reason": missingness_reason,
        "signal_definition": signal_definition_json,
        "signal_context": signal_context,
        "source_maps": source_maps,
    }
    row = {
        "snapshot_id": signal_snapshot_id,
        "dataset_id": context.dataset_id,
        "dataset_name": DEFAULT_SIGNAL_DATASET_NAME,
        "owner": DEFAULT_SIGNAL_OWNER,
        "sport": "football",
        "signal_pack": DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
        "storage_location": storage_location,
        "readiness": "signal_ready" if missingness_state == "present" else "blocked",
        "update_frequency": "manual",
        "validation_state": "validated" if missingness_state == "present" else "rejected",
        "status": "certified" if missingness_state == "present" else "blocked",
        "batch_id": context.batch_id,
        "snapshot_kind": SIGNAL_ROW_KIND,
        "signal_pack_version": SIGNAL_DEFINITION_VERSION,
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
        "source_math_dataset_id": context.source_math_dataset_id,
        "source_math_dataset_name": context.source_math_dataset_name,
        "source_math_batch_id": context.source_math_batch_id,
        "source_math_version_id": context.source_math_version_id,
        "source_math_certification_id": context.source_math_certification_id,
        "source_math_dataset_certification_id": context.source_math_dataset_certification_id,
        "source_math_population_summary_id": context.source_math_population_summary_id,
        "source_math_evidence_package_id": context.source_math_evidence_package_id,
        "source_math_batch_lineage_id": context.source_math_batch_lineage_id,
        "source_math_row_count": context.source_math_row_count,
        "source_math_snapshot_count": context.source_math_snapshot_count,
        "source_math_definition_count": context.source_math_definition_count,
        "dataset_row_id": context.dataset_row_id,
        "decision_context_id": context.decision_context_id,
        "feature_context_id": context.feature_context_id,
        "event_id": context.event_id,
        "game_id": context.game_id,
        "season": context.season,
        "week": context.week,
        "home_team_id": context.home_team_id,
        "away_team_id": context.away_team_id,
        "team_side": context.team_side,
        "target_team_id": context.target_team_id or context.home_team_id or context.away_team_id,
        "opponent_team_id": context.opponent_team_id,
        "home_team": context.home_team,
        "away_team": context.away_team,
        "selection": definition.signal_id,
        "book": context.book,
        "scheduled_kickoff_time": context.scheduled_kickoff_time,
        "decision_cutoff_time": context.decision_cutoff_time,
        "cutoff_policy_version": context.cutoff_policy_version,
        "point_in_time_status": context.point_in_time_status,
        "predictor_outcome_separation_status": context.predictor_outcome_separation_status,
        "decision_readiness_status": context.decision_readiness_status,
        "signal_usage_mode": definition.signal_usage_mode,
        "signal_id": definition.signal_id,
        "signal_name": definition.signal_name,
        "signal_family": definition.signal_family,
        "signal_version": definition.signal_version,
        "classification": definition.classification,
        "value_type": definition.value_type,
        "unit": definition.unit,
        "signal_owner": definition.signal_owner,
        "entity_scope": definition.entity_scope,
        "dataset_grain_compatibility": definition.dataset_grain_compatibility,
        "transformation_version": definition.transformation_version,
        "missingness_policy": definition.missingness_policy,
        "signal_context_id": build_signal_snapshot_context_id(context),
        **_signal_value_type_columns(value),
        "signal_missingness_state": missingness_state,
        "signal_missingness_reason": missingness_reason,
        "signal_definition_json": _as_json(signal_definition_json),
        "signal_context_json": _as_json(signal_context),
        "signal_snapshot_grain_id": CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID,
        "signal_registry_schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
        "signal_lineage_id": signal_lineage_id,
        "signal_evidence_id": signal_evidence_id,
        "source_feature_ids_json": _as_json(source_maps["source_feature_ids"]),
        "source_feature_snapshot_ids_json": _as_json(source_maps["source_feature_snapshot_ids"]),
        "source_feature_lineage_ids_json": _as_json(source_maps["source_feature_lineage_ids"]),
        "source_feature_certification_ids_json": _as_json(source_maps["source_feature_certification_ids"]),
        "source_feature_dataset_certification_ids_json": _as_json(source_maps["source_feature_dataset_certification_ids"]),
        "source_feature_alignment_certification_ids_json": _as_json(source_maps["source_feature_alignment_certification_ids"]),
        "source_feature_missingness_json": _as_json(source_maps["source_feature_missingness"]),
        "source_feature_freshness_json": _as_json(source_maps["source_feature_freshness"]),
        "source_feature_value_types_json": _as_json(source_maps["source_feature_value_types"]),
        "source_feature_values_json": _as_json(source_maps["source_feature_values"]),
        "source_math_output_ids_json": _as_json(source_maps["source_math_output_ids"]),
        "source_math_snapshot_ids_json": _as_json(source_maps["source_math_snapshot_ids"]),
        "source_math_lineage_ids_json": _as_json(source_maps["source_math_lineage_ids"]),
        "source_math_certification_ids_json": _as_json(source_maps["source_math_certification_ids"]),
        "source_math_dataset_certification_ids_json": _as_json(source_maps["source_math_dataset_certification_ids"]),
        "source_math_missingness_json": _as_json(source_maps["source_math_missingness"]),
        "source_math_freshness_json": _as_json(source_maps["source_math_freshness"]),
        "source_math_value_types_json": _as_json(source_maps["source_math_value_types"]),
        "source_math_values_json": _as_json(source_maps["source_math_values"]),
        "missing_required_assets_json": _as_json([]),
        "evidence_package_id": _stable_id(
            "signal_evidence_package",
            context.source_math_evidence_package_id,
            context.source_math_population_summary_id,
            context.batch_id,
            SIGNAL_TRANSFORMATION_VERSION,
        ),
        "record_count": 1,
        "signal_count": 1,
        "signal_values_json": _as_json(
            {
                "signal_id": definition.signal_id,
                "signal_name": definition.signal_name,
                "value": value,
                "missingness_state": missingness_state,
                "missingness_reason": missingness_reason,
                "dataset_row_id": context.dataset_row_id,
                "decision_context_id": context.decision_context_id,
                "signal_context_id": build_signal_snapshot_context_id(context),
            }
        ),
        "summary_json": _as_json(
            {
                "signal_id": definition.signal_id,
                "signal_family": definition.signal_family,
                "value": value,
                "missingness_state": missingness_state,
                "dataset_row_id": context.dataset_row_id,
                "decision_context_id": context.decision_context_id,
                "signal_context_id": build_signal_snapshot_context_id(context),
            }
        ),
        "payload_json": _as_json(payload),
        "schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_SIGNAL_SOURCE_NAME,
        "provider": DEFAULT_SIGNAL_PROVIDER,
        "market": DEFAULT_SIGNAL_MARKET,
        "market_type": DEFAULT_SIGNAL_MARKET_TYPE,
        "asset_class": DEFAULT_SIGNAL_ASSET_CLASS,
        "lineage_id": signal_lineage_id,
        "version_id": SIGNAL_TRANSFORMATION_VERSION,
        "quality_score": 1.0 if missingness_state == "present" else 0.0,
    }
    lineage_edge = create_lineage_record(
        provider_id="signal_population_runtime",
        provider_type="signal_population",
        payload_schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
        snapshot_id=signal_snapshot_id,
        source_type="math_engine",
        schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
        lineage_id=signal_lineage_id,
        dataset_id=context.dataset_id,
        dataset_name=DEFAULT_SIGNAL_DATASET_NAME,
        source_record_id=_normalize_text(context.source_math_population_summary_id or context.source_math_batch_id),
        target_record_id=signal_snapshot_id,
        source_stage="math_engine_snapshot",
        target_stage="signal_snapshot",
        transformation="populate_signal_snapshot",
    )
    lineage_record = {
        "lineage_edge_id": signal_lineage_id,
        "dataset_id": context.dataset_id,
        "dataset_name": DEFAULT_SIGNAL_DATASET_NAME,
        "owner": DEFAULT_SIGNAL_OWNER,
        "sport": "football",
        "feature_pack": DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
        "storage_location": storage_location,
        "readiness": "signal_ready" if missingness_state == "present" else "blocked",
        "update_frequency": "manual",
        "validation_state": "validated" if missingness_state == "present" else "rejected",
        "status": "certified" if missingness_state == "present" else "blocked",
        "schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_SIGNAL_SOURCE_NAME,
        "provider": DEFAULT_SIGNAL_PROVIDER,
        "market": DEFAULT_SIGNAL_MARKET,
        "market_type": DEFAULT_SIGNAL_MARKET_TYPE,
        "asset_class": DEFAULT_SIGNAL_ASSET_CLASS,
        "snapshot_id": signal_snapshot_id,
        "lineage_id": signal_lineage_id,
        "version_id": SIGNAL_TRANSFORMATION_VERSION,
        "quality_score": 1.0 if missingness_state == "present" else 0.0,
        "source_stage": "math_engine_snapshot",
        "source_id": _normalize_text(context.source_math_population_summary_id or context.source_math_batch_id),
        "target_stage": "signal_snapshot",
        "target_id": signal_snapshot_id,
        "transformation": "populate_signal_snapshot",
        "step_index": 0,
        "payload_json": _as_json(lineage_edge),
    }
    return row, lineage_record


def _signal_population_missing_snapshot(
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
        "schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
        "dataset_id": DEFAULT_SIGNAL_DATASET_ID,
        "dataset_name": DEFAULT_SIGNAL_DATASET_NAME,
        "batch_id": _normalize_text(batch_id),
        "version_id": SIGNAL_TRANSFORMATION_VERSION,
        "dataset_row_count": 0,
        "signal_definition_count": len(_SIGNAL_DEFINITIONS),
        "signal_row_count": 0,
        "signal_context_count": 0,
        "signal_rows": [],
        "signal_summary_rows": [],
        "signal_population_summary": {},
        "signal_population_summary_id": "",
        "signal_evidence_package_id": "",
        "signal_lineage_edges": [],
        "signal_alignment_rows": [],
        "signal_lifecycle_rows": [],
        "dataset_certification_status": "missing",
        "dataset_certification_id": "",
        "lifecycle_state": "missing",
        "source_math_snapshot": {},
        "source_math_summary": {},
        "source_math_population_snapshot": {},
        "source_math_population_summary": {},
        "source_math_rows": [],
        "source_math_batch_id": "",
        "source_math_certification_id": "",
        "source_math_dataset_certification_id": "",
        "source_math_evidence_package_id": "",
        "source_math_population_summary_id": "",
        "source_math_batch_lineage_id": "",
        "join_diagnostics": {},
        "registry": summarize_signal_registry(),
        "validation": {},
        "signal_validation": {},
        "storage": storage.health(),
        "unresolved_blockers": warning_list,
        "readiness": "blocked",
        "validation_state": "rejected",
        "signal_context_ids": [],
        "signal_definition_ids": list_signal_definition_ids(),
        "warnings": warning_list,
        "idempotent_reuse": False,
    }


def _load_signal_population_snapshot(
    storage: LocalStorageEngine,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_SIGNAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    if not storage.table_exists("signal_snapshots"):
        return _signal_population_missing_snapshot(
            storage=storage,
            dataset_id=dataset_id,
            batch_id=_normalize_text(batch_id),
            status="missing_signal_table",
            warnings=["signal snapshots table is missing"],
        )

    summary_rows_all = [
        dict(row)
        for row in storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[DEFAULT_SIGNAL_DATASET_ID, SIGNAL_BATCH_KIND],
            order_by="created_at ASC, snapshot_id ASC",
        )
    ]
    signal_rows_all = [
        dict(row)
        for row in storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[DEFAULT_SIGNAL_DATASET_ID, SIGNAL_ROW_KIND],
            order_by="dataset_row_id ASC, signal_id ASC, snapshot_id ASC",
        )
    ]
    effective_batch_id = _normalize_text(batch_id)
    if effective_batch_id:
        summary_rows = [row for row in summary_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id]
        signal_rows = [row for row in signal_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id]
    else:
        summary_rows = summary_rows_all[-1:] if summary_rows_all else []
        effective_batch_id = _normalize_text(summary_rows[-1].get("batch_id")) if summary_rows else ""
        if not effective_batch_id and signal_rows_all:
            effective_batch_id = _normalize_text(signal_rows_all[-1].get("batch_id"))
        signal_rows = [row for row in signal_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else []
        summary_rows = [row for row in summary_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else summary_rows

    latest_summary_row = dict(summary_rows[-1]) if summary_rows else {}
    source_math_batch_id = _normalize_text(latest_summary_row.get("source_math_batch_id"))
    source_math_snapshot = build_math_engine_population_dashboard_snapshot(
        storage_path=storage.path,
        backend=backend,
        dataset_id=DEFAULT_MATH_ENGINE_DATASET_ID,
        batch_id=source_math_batch_id or None,
    ) if source_math_batch_id or summary_rows else {}
    source_math_summary = dict(source_math_snapshot.get("math_engine_population_summary") or {})
    if not source_math_summary:
        source_math_summary_rows = source_math_snapshot.get("math_engine_summary_rows") or []
        if source_math_summary_rows:
            source_math_summary = dict(source_math_summary_rows[-1])
        else:
            source_math_summary = dict(source_math_snapshot)

    source_math_rows = [dict(row) for row in source_math_snapshot.get("math_engine_rows") or []]
    if not source_math_rows and source_math_batch_id:
        source_math_rows = [
            dict(row)
            for row in storage.fetch(
                "math_engine_snapshots",
                where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
                params=[DEFAULT_MATH_ENGINE_DATASET_ID, source_math_batch_id, MATH_ENGINE_ROW_KIND],
                order_by="dataset_row_id ASC, engine_id ASC, snapshot_id ASC",
            )
        ]
    signal_snapshot_ids = {str(row.get("snapshot_id")) for row in signal_rows if _normalize_text(row.get("snapshot_id"))}
    signal_context_ids = {str(row.get("signal_context_id")) for row in signal_rows if _normalize_text(row.get("signal_context_id"))}
    signal_dataset_row_ids = {str(row.get("dataset_row_id")) for row in signal_rows if _normalize_text(row.get("dataset_row_id"))}
    grouped_contexts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in signal_rows:
        grouped_contexts[_normalize_text(row.get("signal_context_id"))].append(dict(row))

    alignment_rows_all = [
        dict(row)
        for row in storage.fetch(
            "research_asset_alignment_certifications",
            where="asset_id = ?",
            params=[DEFAULT_SIGNAL_RESEARCH_ASSET_ID],
            order_by="created_at ASC, alignment_certification_id ASC",
        )
    ] if storage.table_exists("research_asset_alignment_certifications") else []
    lifecycle_rows_all = [
        dict(row)
        for row in storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[DEFAULT_SIGNAL_RESEARCH_ASSET_ID],
            order_by="created_at ASC, asset_id ASC",
        )
    ] if storage.table_exists("research_asset_lifecycles") else []
    certification_rows_all = [
        dict(row)
        for row in storage.fetch(
            "historical_certifications",
            where="dataset_id = ?",
            params=["historical_certifications"],
            order_by="certified_at ASC, certification_id ASC",
        )
    ] if storage.table_exists("historical_certifications") else []

    certification_rows = certification_rows_all
    if batch_id:
        certification_rows = [
            row
            for row in certification_rows_all
            if _normalize_text(row.get("batch_id")) == _normalize_text(batch_id)
        ]

    latest_dataset_certification_row = dict(certification_rows[-1]) if certification_rows else {}
    dataset_certification_status = _normalize_text(latest_dataset_certification_row.get("certification_status"), "missing")
    dataset_certification_id = _normalize_text(latest_dataset_certification_row.get("certification_id"))

    signal_definition_count = len(_SIGNAL_DEFINITIONS)
    expected_signal_row_count = len(signal_rows)
    summary_snapshot_id = _stable_id(
        "signal_population_summary_snapshot",
        DEFAULT_SIGNAL_DATASET_ID,
        source_math_batch_id,
        SIGNAL_TRANSFORMATION_VERSION,
    )
    existing_summary_rows = storage.fetch(
        "signal_snapshots",
        where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
        params=[DEFAULT_SIGNAL_DATASET_ID, effective_batch_id, SIGNAL_BATCH_KIND],
        limit=1,
    )
    existing_signal_rows = storage.fetch(
        "signal_snapshots",
        where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
        params=[DEFAULT_SIGNAL_DATASET_ID, effective_batch_id, SIGNAL_ROW_KIND],
    )
    if existing_summary_rows and len(existing_signal_rows) == expected_signal_row_count and expected_signal_row_count > 0:
        return build_signal_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=effective_batch_id,
            include_source_math_snapshot=True,
            idempotent_reuse=True,
        )

    summary_row = dict(latest_summary_row)
    summary_row.setdefault("snapshot_id", summary_snapshot_id)
    summary_row.setdefault("dataset_id", DEFAULT_SIGNAL_DATASET_ID)
    summary_row.setdefault("dataset_name", DEFAULT_SIGNAL_DATASET_NAME)
    summary_row.setdefault("owner", DEFAULT_SIGNAL_OWNER)
    summary_row.setdefault("sport", "football")
    summary_row.setdefault("signal_pack", DEFAULT_SIGNAL_RESEARCH_ASSET_ID)
    summary_row.setdefault("storage_location", str(storage.path))
    summary_row.setdefault("readiness", "signal_ready" if signal_rows else "blocked")
    summary_row.setdefault("update_frequency", "manual")
    summary_row.setdefault("validation_state", "validated" if signal_rows else "rejected")
    summary_row.setdefault("status", "certified" if signal_rows else "blocked")
    summary_row.setdefault("batch_id", effective_batch_id)
    summary_row.setdefault("snapshot_kind", SIGNAL_BATCH_KIND)
    summary_row.setdefault("signal_pack_version", SIGNAL_DEFINITION_VERSION)
    summary_row.setdefault("source_feature_dataset_id", _normalize_text(source_math_summary.get("source_feature_dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID))
    summary_row.setdefault("source_feature_dataset_name", _normalize_text(source_math_summary.get("source_feature_dataset_name"), DEFAULT_SIGNAL_DATASET_NAME))
    summary_row.setdefault("source_feature_batch_id", _normalize_text(source_math_summary.get("source_feature_batch_id")))
    summary_row.setdefault("source_feature_version_id", _normalize_text(source_math_summary.get("source_feature_version_id"), MATH_ENGINE_TRANSFORMATION_VERSION))
    summary_row.setdefault("source_feature_certification_id", _normalize_text(source_math_summary.get("source_feature_certification_id")))
    summary_row.setdefault("source_feature_dataset_certification_id", _normalize_text(source_math_summary.get("source_feature_dataset_certification_id")))
    summary_row.setdefault("source_feature_population_summary_id", _normalize_text(source_math_summary.get("source_feature_population_summary_id")))
    summary_row.setdefault("source_feature_evidence_package_id", _normalize_text(source_math_summary.get("source_feature_evidence_package_id")))
    summary_row.setdefault("source_feature_batch_lineage_id", _normalize_text(source_math_summary.get("source_feature_batch_lineage_id")))
    summary_row.setdefault("source_feature_row_count", _normalize_int(source_math_summary.get("source_feature_row_count"), 0))
    summary_row.setdefault("source_feature_snapshot_count", _normalize_int(source_math_summary.get("source_feature_snapshot_count"), 0))
    summary_row.setdefault("source_feature_definition_count", _normalize_int(source_math_summary.get("source_feature_definition_count"), 0))
    summary_row.setdefault("source_math_dataset_id", _normalize_text(source_math_summary.get("dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID))
    summary_row.setdefault("source_math_dataset_name", _normalize_text(source_math_summary.get("dataset_name"), "nfl_math_engine_snapshots"))
    summary_row.setdefault("source_math_batch_id", source_math_batch_id)
    summary_row.setdefault("source_math_version_id", _normalize_text(source_math_summary.get("version_id"), MATH_ENGINE_TRANSFORMATION_VERSION))
    summary_row.setdefault("source_math_certification_id", _normalize_text(source_math_summary.get("certification_id")))
    summary_row.setdefault("source_math_dataset_certification_id", _normalize_text(source_math_summary.get("dataset_certification_id")))
    summary_row.setdefault("source_math_population_summary_id", _normalize_text(source_math_summary.get("snapshot_id")))
    summary_row.setdefault("source_math_evidence_package_id", _normalize_text(source_math_summary.get("evidence_package_id")))
    summary_row.setdefault("source_math_batch_lineage_id", _normalize_text(source_math_summary.get("lineage_id")))
    summary_row.setdefault("source_math_row_count", _normalize_int(source_math_summary.get("record_count"), len(source_math_rows)))
    summary_row.setdefault("source_math_snapshot_count", _normalize_int(source_math_summary.get("source_math_snapshot_count"), len(source_math_rows)))
    summary_row.setdefault("source_math_definition_count", _normalize_int(source_math_summary.get("source_math_definition_count"), len(list_math_engine_definition_ids())))

    source_math_summary_valid = (
        _normalize_text(source_math_summary.get("status")) == "certified"
        and _normalize_text(source_math_summary.get("dataset_certification_status")) == "certified"
        and _normalize_text(source_math_summary.get("lifecycle_state")) == "math_ready"
    )
    source_math_blockers: list[str] = []
    if not source_math_summary_valid:
        source_math_blockers.append("certified_math_layer_required")
    if not source_math_rows:
        source_math_blockers.append("missing_math_rows")
    if signal_rows and len(signal_rows) != expected_signal_row_count:
        source_math_blockers.append("unexpected_existing_signal_row_count")

    created_at = _normalize_text(summary_row.get("created_at")) or _utc_now_iso()
    if not created_at:
        created_at = _utc_now_iso()

    grouped_signal_contexts: list[SignalSnapshotContext] = []
    for context_rows in grouped_contexts.values():
        first_context_row = dict(context_rows[0])
        context = build_signal_snapshot_context(
            dataset_id=DEFAULT_SIGNAL_DATASET_ID,
            batch_id=effective_batch_id or _signal_population_batch_id(DEFAULT_SIGNAL_DATASET_ID, source_math_batch_id, contexts=[]),
            summary_row=summary_row,
            math_rows=source_math_rows,
            context_rows=context_rows,
        )
        grouped_signal_contexts.append(context)

    if not grouped_signal_contexts and signal_rows:
        grouped_signal_contexts.append(
            build_signal_snapshot_context(
                dataset_id=DEFAULT_SIGNAL_DATASET_ID,
                batch_id=effective_batch_id,
                summary_row=summary_row,
                math_rows=source_math_rows,
                context_rows=[dict(source_math_rows[0])] if source_math_rows else [],
            )
        )

    signal_batch_id = effective_batch_id or _signal_population_batch_id(DEFAULT_SIGNAL_DATASET_ID, source_math_batch_id, contexts=grouped_signal_contexts)
    signal_version_id = _stable_id(
        "signal_snapshot_version",
        DEFAULT_SIGNAL_DATASET_ID,
        signal_batch_id,
        SIGNAL_POPULATION_SCHEMA_VERSION,
        SIGNAL_DEFINITION_VERSION,
        SIGNAL_TRANSFORMATION_VERSION,
    )
    signal_batch_lineage_id = _stable_id(
        "signal_snapshot_population_lineage",
        DEFAULT_SIGNAL_DATASET_ID,
        signal_batch_id,
        signal_version_id,
    )
    signal_evidence_package_id = _stable_id(
        "signal_snapshot_population_evidence",
        DEFAULT_SIGNAL_DATASET_ID,
        signal_batch_id,
        signal_version_id,
    )

    if source_math_blockers:
        return _signal_population_missing_snapshot(
            storage=storage,
            dataset_id=DEFAULT_SIGNAL_DATASET_ID,
            batch_id=signal_batch_id,
            status="blocked_source_math_layer",
            warnings=source_math_blockers,
        )

    signal_rows_payload: list[dict[str, Any]] = []
    lineage_edges: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    signal_context_summaries: list[dict[str, Any]] = []

    math_lookup = {
        _normalize_text(row.get("engine_id") or row.get("output_feature_id")): dict(row)
        for row in source_math_rows
        if _normalize_text(row.get("engine_id") or row.get("output_feature_id"))
    }

    for context in grouped_signal_contexts:
        signal_context_summaries.append(context.as_dict())
        for definition in _SIGNAL_DEFINITIONS:
            row, lineage_row = _signal_row_payload_and_values(
                definition=definition,
                context=context,
                summary_row=summary_row,
                math_lookup=math_lookup,
                storage_location=str(storage.path),
                created_at=created_at,
            )
            signal_rows_payload.append(row)
            lineage_edges.append(lineage_row)
            validation_rows.append(
                {
                    **row,
                    "provider_timestamp": _normalize_text(summary_row.get("decision_cutoff_time"), row.get("decision_cutoff_time")),
                    "snapshot_time": row.get("decision_cutoff_time"),
                    "decision_time": row.get("decision_cutoff_time"),
                    "result_timestamp": "",
                }
            )
            row_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
                asset_family="signal",
                market_profile=DEFAULT_SIGNAL_PROFILE_ID,
                market=DEFAULT_SIGNAL_MARKET,
                league="nfl",
                sport="football",
                season=str(row.get("season") or ""),
                week_or_date=str(row.get("week") or ""),
                event_id=_normalize_text(row.get("event_id")),
                market_id=_normalize_text(row.get("signal_id")),
                selection=_normalize_text(row.get("signal_id")),
                provider=DEFAULT_SIGNAL_PROVIDER,
                connector="math_engine_population",
                schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
                lineage_version=_normalize_text(row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
                asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                asset_type="signal_snapshot",
                team_id=_normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                game_id=_normalize_text(row.get("game_id") or row.get("event_id")),
                market_type=DEFAULT_SIGNAL_MARKET_TYPE,
            )
            identity_validation = validate_research_asset_identity_contract(row_identity)
            if not identity_validation["ok"]:
                raise ValueError("; ".join(identity_validation.get("errors", [])) or "signal identity validation failed")

            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[
                    {
                        **dict(row),
                        "asset_id": DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
                        "asset_family": "signal",
                        "asset_name": DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                        "asset_type": "signal_snapshot",
                        "lineage_version": _normalize_text(row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
                        "market_id": _normalize_text(row.get("signal_id")),
                        "provider_timestamp": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                        "result_timestamp": "",
                        "market_profile": DEFAULT_SIGNAL_PROFILE_ID,
                        "market": DEFAULT_SIGNAL_MARKET,
                        "league": "nfl",
                        "sport": "football",
                        "week_or_date": str(row.get("week") or ""),
                        "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                        "participant_id": "",
                        "selection": _normalize_text(row.get("signal_id")),
                        "connector": "math_engine_population",
                    }
                ],
                required_fields=(
                    "dataset_id",
                    "dataset_name",
                    "snapshot_id",
                    "batch_id",
                    "signal_id",
                    "signal_name",
                    "signal_family",
                    "signal_version",
                    "classification",
                    "value_type",
                    "unit",
                    "signal_owner",
                    "entity_scope",
                    "dataset_grain_compatibility",
                    "transformation_version",
                    "missingness_policy",
                    "signal_context_id",
                    "signal_value_json",
                    "signal_definition_json",
                    "signal_context_json",
                    "signal_snapshot_grain_id",
                    "signal_registry_schema_version",
                    "signal_lineage_id",
                    "signal_evidence_id",
                    "source_feature_ids_json",
                    "source_feature_snapshot_ids_json",
                    "source_feature_lineage_ids_json",
                    "source_feature_certification_ids_json",
                    "source_feature_dataset_certification_ids_json",
                    "source_feature_alignment_certification_ids_json",
                    "source_math_output_ids_json",
                    "source_math_snapshot_ids_json",
                    "source_math_lineage_ids_json",
                    "source_math_certification_ids_json",
                    "source_math_dataset_certification_ids_json",
                    "evidence_package_id",
                    "signal_usage_mode",
                ),
                required_timestamps=("provider_timestamp", "snapshot_time", "decision_time"),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_SIGNAL_SOURCE_NAME,
                    "source_type": DEFAULT_SIGNAL_SOURCE_TYPE,
                    "source_key": DEFAULT_SIGNAL_SOURCE_KEY,
                    "provider": DEFAULT_SIGNAL_PROVIDER,
                    "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "result_timestamp": "",
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "math_output_input",
                    "dataset_id": DEFAULT_SIGNAL_DATASET_ID,
                    "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                },
                created_at=_utc_now_iso(),
                asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                asset_type="signal_snapshot",
                lifecycle_state="signal_ready",
                batch_id=_normalize_text(row.get("snapshot_id")),
            )
            alignment_row = build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_SIGNAL_SOURCE_NAME,
                    "source_type": DEFAULT_SIGNAL_SOURCE_TYPE,
                    "source_key": DEFAULT_SIGNAL_SOURCE_KEY,
                    "provider": DEFAULT_SIGNAL_PROVIDER,
                    "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "result_timestamp": "",
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "math_output_input",
                    "dataset_id": DEFAULT_SIGNAL_DATASET_ID,
                    "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                },
                batch_id=signal_batch_id,
            )
            alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
            if not alignment_validation["ok"]:
                raise ValueError("; ".join(alignment_validation.get("issues", [])) or "signal alignment validation failed")
            storage.upsert("research_asset_alignment_certifications", alignment_row, key_columns=("alignment_certification_id",))
            alignment_rows.append(
                {
                    "ok": alignment_contract.alignment_status == "aligned",
                    "status": alignment_contract.alignment_status,
                    "identity": row_identity.as_dict(),
                    "alignment_certification": alignment_contract.as_dict(),
                    "alignment_certification_row": alignment_row,
                    "validation": alignment_validation,
                }
            )

    signal_validation = validate_signal_rows(signal_rows_payload)
    if not signal_validation["ok"]:
        raise ValueError("; ".join(signal_validation.get("errors", [])) or "signal rows failed validation")

    summary_row["readiness"] = "signal_ready" if not signal_validation["errors"] else "blocked"
    summary_row["validation_state"] = "validated" if not signal_validation["errors"] else "rejected"
    summary_row["status"] = "certified" if not signal_validation["errors"] else "blocked"
    summary_row["schema_version"] = SIGNAL_POPULATION_SCHEMA_VERSION
    summary_row["created_at"] = created_at
    summary_row["updated_at"] = created_at
    summary_row["source"] = DEFAULT_SIGNAL_SOURCE_NAME
    summary_row["provider"] = DEFAULT_SIGNAL_PROVIDER
    summary_row["market"] = DEFAULT_SIGNAL_MARKET
    summary_row["market_type"] = DEFAULT_SIGNAL_MARKET_TYPE
    summary_row["asset_class"] = DEFAULT_SIGNAL_ASSET_CLASS
    summary_row["lineage_id"] = signal_batch_lineage_id
    summary_row["version_id"] = signal_version_id
    summary_row["signal_usage_mode"] = SIGNAL_USAGE_MODE
    summary_row["signal_id"] = f"{DEFAULT_SIGNAL_RESEARCH_ASSET_ID}.summary"
    summary_row["signal_name"] = "Reusable Signals Summary"
    summary_row["signal_family"] = "summary"
    summary_row["signal_version"] = SIGNAL_DEFINITION_VERSION
    summary_row["classification"] = "direct"
    summary_row["value_type"] = "integer"
    summary_row["unit"] = "rows"
    summary_row["signal_owner"] = DEFAULT_SIGNAL_OWNER
    summary_row["entity_scope"] = "data_quality_context"
    summary_row["dataset_grain_compatibility"] = CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID
    summary_row["transformation_version"] = SIGNAL_TRANSFORMATION_VERSION
    summary_row["missingness_policy"] = "required"
    summary_row["signal_context_id"] = _stable_id(
        "signal_snapshot_context",
        signal_batch_id,
        summary_row.get("dataset_row_id"),
        summary_row.get("decision_context_id"),
        "summary",
    )
    summary_row["signal_value_json"] = _as_json(
        {
            "signal_row_count": len(signal_rows_payload),
            "signal_definition_count": signal_definition_count,
            "signal_context_count": len(grouped_signal_contexts),
            "signal_usage_mode": SIGNAL_USAGE_MODE,
        }
    )
    summary_row["signal_value_text"] = None
    summary_row["signal_value_number"] = len(signal_rows_payload)
    summary_row["signal_value_boolean"] = None
    summary_row["signal_missingness_state"] = "present" if signal_rows_payload else "missing_required"
    summary_row["signal_missingness_reason"] = "" if signal_rows_payload else "no_signal_rows_produced"
    summary_row["signal_definition_json"] = _as_json(
        {
            "signal_id": summary_row["signal_id"],
            "signal_name": summary_row["signal_name"],
            "signal_family": summary_row["signal_family"],
            "classification": summary_row["classification"],
            "value_type": summary_row["value_type"],
        }
    )
    summary_row["signal_context_json"] = _as_json(
        {
            "batch_id": signal_batch_id,
            "summary": True,
            "signal_contexts": signal_context_summaries,
            "source_math_summary": dict(source_math_summary),
        }
    )
    summary_row["signal_snapshot_grain_id"] = CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID
    summary_row["signal_registry_schema_version"] = SIGNAL_POPULATION_SCHEMA_VERSION
    summary_row["signal_lineage_id"] = signal_batch_lineage_id
    summary_row["signal_evidence_id"] = _stable_id(
        "signal_population_summary_evidence",
        summary_row["snapshot_id"],
        signal_batch_id,
        _as_json([row["snapshot_id"] for row in signal_rows_payload]),
    )
    _apply_signal_summary_source_feature_maps(summary_row, signal_rows_payload)
    summary_row["source_math_output_ids_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_ids": list(definition.source_math_engine_output_refs),
                "summary_refs": list(definition.source_math_summary_refs),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_snapshot_ids_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_snapshot_ids": [
                    _normalize_text(math_lookup.get(ref, {}).get("snapshot_id"))
                    for ref in definition.source_math_engine_output_refs
                    if math_lookup.get(ref) is not None
                ],
                "summary_snapshot_id": _normalize_text(summary_row.get("source_math_population_summary_id")),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_lineage_ids_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_lineage_ids": [
                    _normalize_text(math_lookup.get(ref, {}).get("engine_lineage_id"))
                    for ref in definition.source_math_engine_output_refs
                    if math_lookup.get(ref) is not None
                ],
                "summary_lineage_id": _normalize_text(summary_row.get("source_math_batch_lineage_id")),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_certification_ids_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_certification_ids": [
                    _normalize_text(math_lookup.get(ref, {}).get("certification_id"))
                    for ref in definition.source_math_engine_output_refs
                    if math_lookup.get(ref) is not None
                ],
                "summary_certification_id": _normalize_text(summary_row.get("source_math_certification_id")),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_dataset_certification_ids_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_dataset_certification_ids": [
                    _normalize_text(math_lookup.get(ref, {}).get("dataset_certification_id"))
                    for ref in definition.source_math_engine_output_refs
                    if math_lookup.get(ref) is not None
                ],
                "summary_dataset_certification_id": _normalize_text(summary_row.get("source_math_dataset_certification_id")),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_missingness_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_missingness": {
                    ref: _math_missingness(math_lookup[ref])
                    for ref in definition.source_math_engine_output_refs
                    if ref in math_lookup
                },
                "summary_missingness": _normalize_text(summary_row.get("validation_state"), "validated"),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_freshness_json"] = _as_json(
        {
            definition.signal_id: {
                "feature_freshness_seconds": _signal_freshness_map(summary_row),
                "summary_snapshot_id": _normalize_text(summary_row.get("source_math_population_summary_id")),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_value_types_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_value_types": {
                    ref: _normalize_text(math_lookup.get(ref, {}).get("value_type"))
                    for ref in definition.source_math_engine_output_refs
                    if ref in math_lookup
                },
                "summary_value_type": "string" if definition.signal_id.endswith("state") else _normalize_text(summary_row.get("value_type"), "integer"),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["source_math_values_json"] = _as_json(
        {
            definition.signal_id: {
                "engine_values": {
                    ref: _math_value(math_lookup[ref])
                    for ref in definition.source_math_engine_output_refs
                    if ref in math_lookup
                },
                "summary_value": len(signal_rows_payload),
            }
            for definition in _SIGNAL_DEFINITIONS
        }
    )
    summary_row["missing_required_assets_json"] = _as_json([])
    summary_row["evidence_package_id"] = signal_evidence_package_id
    summary_row["record_count"] = len(signal_rows_payload)
    summary_row["signal_count"] = len(signal_rows_payload)
    summary_row["signal_values_json"] = _as_json(
        {
            "signal_row_count": len(signal_rows_payload),
            "signal_definition_count": signal_definition_count,
            "signal_context_count": len(grouped_signal_contexts),
            "signal_ids": [row.get("signal_id") for row in signal_rows_payload],
        }
    )
    summary_row["summary_json"] = _as_json(
        {
            "batch_id": signal_batch_id,
            "signal_row_count": len(signal_rows_payload),
            "signal_definition_count": signal_definition_count,
            "signal_context_count": len(grouped_signal_contexts),
            "source_math_row_count": len(source_math_rows),
            "source_feature_row_count": summary_row.get("source_feature_row_count"),
        }
    )
    summary_row["payload_json"] = _as_json(
        {
            "summary": {
                "batch_id": signal_batch_id,
                "signal_row_count": len(signal_rows_payload),
                "signal_definition_count": signal_definition_count,
                "signal_context_count": len(grouped_signal_contexts),
            },
            "source_math_summary": dict(source_math_summary),
            "signal_values": [
                {
                    "snapshot_id": row.get("snapshot_id"),
                    "signal_id": row.get("signal_id"),
                    "signal_name": row.get("signal_name"),
                    "signal_family": row.get("signal_family"),
                    "value_json": row.get("signal_value_json"),
                    "missingness_state": row.get("signal_missingness_state"),
                }
                for row in signal_rows_payload
            ],
            "lineage_edges": [dict(row) for row in lineage_edges],
        }
    )

    signal_asset_contract = ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
        research_asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
        asset_category="signal",
        asset_type="snapshot_batch",
        source_table_name="signal_snapshots",
        required_fields=_required_row_fields(),
        required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
        point_in_time_rules=(
            "scheduled_kickoff_time must predate the decision cutoff",
            "decision_cutoff_time must remain unchanged from the certified historical dataset row",
            "signal outputs must remain observation-only and math-derived",
        ),
        description=(
            "Deterministic reusable signals derived only from certified mathematical-engine outputs "
            "and preserved with explicit provenance, lineage, and point-in-time constraints."
        ),
        priority="P0",
        required=True,
        future_asset=False,
        metadata={
            "market_profile": DEFAULT_SIGNAL_PROFILE_ID,
            "market_family": "sports",
            "minimum_schema": True,
            "dataset_role": "signal_population",
            "source_math_batch_id": source_math_batch_id,
            "source_math_certification_id": _normalize_text(summary_row.get("source_math_certification_id")),
            "source_math_dataset_certification_id": _normalize_text(summary_row.get("source_math_dataset_certification_id")),
            "source_math_evidence_package_id": _normalize_text(summary_row.get("source_math_evidence_package_id")),
            "source_math_population_summary_id": _normalize_text(summary_row.get("source_math_population_summary_id")),
            "source_math_population_batch_id": source_math_batch_id,
            "source_feature_batch_id": _normalize_text(summary_row.get("source_feature_batch_id")),
            "source_feature_certification_id": _normalize_text(summary_row.get("source_feature_certification_id")),
            "source_feature_dataset_certification_id": _normalize_text(summary_row.get("source_feature_dataset_certification_id")),
            "source_feature_evidence_package_id": _normalize_text(summary_row.get("source_feature_evidence_package_id")),
            "source_feature_population_summary_id": _normalize_text(summary_row.get("source_feature_population_summary_id")),
        },
    )

    certification_runtime = HistoricalResearchAssetCertificationRuntime(
        storage_path=storage.path,
        backend=backend,
        store=storage,
    )
    lifecycle_runtime = ResearchAssetLifecycleRuntime(
        storage_path=storage.path,
        backend=backend,
        store=storage,
    )

    try:
        source_bundle = {
            "source_name": DEFAULT_SIGNAL_SOURCE_NAME,
            "source_type": DEFAULT_SIGNAL_SOURCE_TYPE,
            "source_key": DEFAULT_SIGNAL_SOURCE_KEY,
            "provider": DEFAULT_SIGNAL_PROVIDER,
            "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "result_timestamp": "",
        }
        raw_acquisition_result = {
            "ok": True,
            "status": "math_output_input",
            "dataset_id": DEFAULT_SIGNAL_DATASET_ID,
            "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
        }
        signal_result = certification_runtime.certify_research_asset(
            asset_contract=signal_asset_contract,
            rows=signal_rows_payload + [summary_row],
            profile_id=DEFAULT_SIGNAL_PROFILE_ID,
            validation=signal_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=SIGNAL_TRANSFORMATION_VERSION,
            created_at=_utc_now_iso(),
            batch_id=signal_batch_id,
        )
        signal_certification_row = dict(signal_result["research_asset_certification"])
        storage.upsert("signal_snapshots", summary_row, key_columns=("snapshot_id",))
        for row in signal_rows_payload:
            storage.upsert("signal_snapshots", row, key_columns=("snapshot_id",))
        for lineage_row in lineage_edges:
            storage.upsert("lineage_edges", lineage_row, key_columns=("lineage_edge_id",))

        signal_dataset_row = build_historical_dataset_certification_row(
            profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
            dataset_version=SIGNAL_TRANSFORMATION_VERSION,
            batch_id=signal_batch_id,
            created_at=_utc_now_iso(),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=[signal_certification_row],
        )
        storage.upsert("historical_certifications", signal_dataset_row, key_columns=("certification_id",))

        signal_identity = build_research_asset_identity_contract(
            asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
            asset_family="signal",
            market_profile=DEFAULT_SIGNAL_PROFILE_ID,
            market=DEFAULT_SIGNAL_MARKET,
            league="nfl",
            sport="football",
            season=str(summary_row.get("season") or ""),
            week_or_date=str(summary_row.get("week") or ""),
            event_id=_normalize_text(summary_row.get("event_id")),
            market_id=f"{signal_batch_id}.signal",
            selection="signal_population",
            provider=DEFAULT_SIGNAL_PROVIDER,
            connector="math_engine_population",
            schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
            lineage_version=signal_batch_id,
            asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
            asset_type="signal_snapshot_batch",
            team_id=_normalize_text(summary_row.get("target_team_id") or summary_row.get("home_team_id") or summary_row.get("away_team_id")),
            game_id=_normalize_text(summary_row.get("game_id") or summary_row.get("event_id")),
            market_type=DEFAULT_SIGNAL_MARKET_TYPE,
        )
        identity_validation = validate_research_asset_identity_contract(signal_identity)
        if not identity_validation["ok"]:
            raise ValueError("; ".join(identity_validation.get("errors", [])) or "signal identity validation failed")

        signal_alignment_rows_result: list[dict[str, Any]] = []
        for row in signal_rows_payload + [summary_row]:
            row_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
                asset_family="signal",
                market_profile=DEFAULT_SIGNAL_PROFILE_ID,
                market=DEFAULT_SIGNAL_MARKET,
                league="nfl",
                sport="football",
                season=str(row.get("season") or ""),
                week_or_date=str(row.get("week") or ""),
                event_id=_normalize_text(row.get("event_id")),
                market_id=_normalize_text(row.get("signal_id")),
                selection=_normalize_text(row.get("signal_id")),
                provider=DEFAULT_SIGNAL_PROVIDER,
                connector="math_engine_population",
                schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
                lineage_version=_normalize_text(row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
                asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                asset_type="signal_snapshot",
                team_id=_normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                game_id=_normalize_text(row.get("game_id") or row.get("event_id")),
                market_type=DEFAULT_SIGNAL_MARKET_TYPE,
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[
                    {
                        **dict(row),
                        "asset_id": DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
                        "asset_family": "signal",
                        "asset_name": DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                        "asset_type": "signal_snapshot",
                        "lineage_version": _normalize_text(row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
                        "market_id": _normalize_text(row.get("signal_id")),
                        "provider_timestamp": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                        "result_timestamp": "",
                        "market_profile": DEFAULT_SIGNAL_PROFILE_ID,
                        "market": DEFAULT_SIGNAL_MARKET,
                        "league": "nfl",
                        "sport": "football",
                        "week_or_date": str(row.get("week") or ""),
                        "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                        "participant_id": "",
                        "selection": _normalize_text(row.get("signal_id")),
                        "connector": "math_engine_population",
                    }
                ],
                required_fields=(
                    "dataset_id",
                    "dataset_name",
                    "snapshot_id",
                    "batch_id",
                    "signal_id",
                    "signal_name",
                    "signal_family",
                    "signal_version",
                    "classification",
                    "value_type",
                    "unit",
                    "signal_owner",
                    "entity_scope",
                    "dataset_grain_compatibility",
                    "transformation_version",
                    "missingness_policy",
                    "signal_context_id",
                    "signal_value_json",
                    "signal_definition_json",
                    "signal_context_json",
                    "signal_snapshot_grain_id",
                    "signal_registry_schema_version",
                    "signal_lineage_id",
                    "signal_evidence_id",
                    "source_feature_ids_json",
                    "source_feature_snapshot_ids_json",
                    "source_feature_lineage_ids_json",
                    "source_feature_certification_ids_json",
                    "source_feature_dataset_certification_ids_json",
                    "source_feature_alignment_certification_ids_json",
                    "source_math_output_ids_json",
                    "source_math_snapshot_ids_json",
                    "source_math_lineage_ids_json",
                    "source_math_certification_ids_json",
                    "source_math_dataset_certification_ids_json",
                    "evidence_package_id",
                    "signal_usage_mode",
                ),
                required_timestamps=("provider_timestamp", "snapshot_time", "decision_time"),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=_utc_now_iso(),
                asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                asset_type="signal_snapshot",
                lifecycle_state="signal_ready",
                batch_id=_normalize_text(row.get("snapshot_id")),
            )
            alignment_row = build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                batch_id=signal_batch_id,
            )
            alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
            if not alignment_validation["ok"]:
                raise ValueError("; ".join(alignment_validation.get("issues", [])) or "signal alignment validation failed")
            storage.upsert("research_asset_alignment_certifications", alignment_row, key_columns=("alignment_certification_id",))
            signal_alignment_rows_result.append(
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
                identity=signal_identity,
                lifecycle_state="signal_ready",
                lifecycle_reason=f"{DEFAULT_SIGNAL_RESEARCH_ASSET_NAME} promoted to signal_ready",
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=_utc_now_iso(),
                certification_result=signal_certification_row,
                dataset_result=signal_dataset_row,
                notes={
                    "batch_id": signal_batch_id,
                    "signal_row_count": len(signal_rows_payload),
                    "signal_definition_count": signal_definition_count,
                    "signal_context_count": len(grouped_signal_contexts),
                    "source_math_batch_id": source_math_batch_id,
                    "previous_states": ["research_asset_certified", "dataset_certified"],
                    "observation_only": True,
                },
            )
        ]

        persisted_rows = storage.fetch(
            "signal_snapshots",
            where="dataset_id = ?",
            params=[DEFAULT_SIGNAL_DATASET_ID],
            order_by="created_at ASC, snapshot_id ASC",
        )
        persisted_summary_rows = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == SIGNAL_BATCH_KIND]
        persisted_signal_rows = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == SIGNAL_ROW_KIND]
        latest_summary_row = dict(summary_row)
        latest_summary_row.setdefault("status", "certified")
        latest_summary_row.setdefault("readiness", "signal_ready")
        latest_summary_row.setdefault("validation_state", "validated")
        storage.upsert("signal_snapshots", latest_summary_row, key_columns=("snapshot_id",))
        persisted_rows = storage.fetch(
            "signal_snapshots",
            where="dataset_id = ?",
            params=[DEFAULT_SIGNAL_DATASET_ID],
            order_by="snapshot_kind ASC, dataset_row_id ASC, signal_id ASC, snapshot_id ASC",
        )
        signal_rows_persisted = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == SIGNAL_ROW_KIND]
        summary_rows_persisted = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == SIGNAL_BATCH_KIND]
        summary_row = summary_rows_persisted[-1] if summary_rows_persisted else latest_summary_row

        return build_signal_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=DEFAULT_SIGNAL_DATASET_ID,
            batch_id=signal_batch_id,
            include_source_math_snapshot=True,
            idempotent_reuse=False,
        )
    finally:
        storage.close()


def build_signal_population_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_SIGNAL_DATASET_ID,
    batch_id: str | None = None,
    include_source_math_snapshot: bool = True,
    idempotent_reuse: bool = False,
) -> dict[str, Any]:
    storage = create_local_storage_engine(storage_path or DEFAULT_SIGNAL_STORAGE_PATH, backend=backend)
    try:
        batch_rows = storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?" + (" AND batch_id = ?" if batch_id else ""),
            params=[dataset_id, SIGNAL_BATCH_KIND, *([batch_id] if batch_id else [])],
            order_by="created_at ASC, snapshot_id ASC",
        ) if storage.table_exists("signal_snapshots") else []
        latest_batch = dict(batch_rows[-1]) if batch_rows else {}
        signal_rows = storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?" + (" AND batch_id = ?" if batch_id else ""),
            params=[dataset_id, SIGNAL_ROW_KIND, *([batch_id] if batch_id else [])],
            order_by="dataset_row_id ASC, signal_id ASC, snapshot_id ASC",
        ) if storage.table_exists("signal_snapshots") else []
        lineage_rows = storage.fetch(
            "lineage_edges",
            where="dataset_id = ? AND target_stage IN (?, ?)" + (" AND version_id = ?" if batch_id else ""),
            params=[dataset_id, "signal_snapshot", "signal_population_summary", *([_normalize_text(latest_batch.get("version_id"))] if batch_id else [])],
            order_by="created_at ASC, lineage_edge_id ASC",
        ) if storage.table_exists("lineage_edges") else []
        alignment_rows_all = storage.fetch(
            "research_asset_alignment_certifications",
            where="asset_id = ?",
            params=[DEFAULT_SIGNAL_RESEARCH_ASSET_ID],
            order_by="created_at ASC, alignment_certification_id ASC",
        ) if storage.table_exists("research_asset_alignment_certifications") else []
        lifecycle_rows_all = storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[DEFAULT_SIGNAL_RESEARCH_ASSET_ID],
            order_by="created_at ASC, asset_id ASC",
        ) if storage.table_exists("research_asset_lifecycles") else []
        certification_rows_all = storage.fetch(
            "historical_certifications",
            where="dataset_id = ?",
            params=["historical_certifications"],
            order_by="certified_at ASC, certification_id ASC",
        ) if storage.table_exists("historical_certifications") else []
        certification_rows = certification_rows_all
        if batch_id:
            certification_rows = [
                row
                for row in certification_rows_all
                if _normalize_text(row.get("batch_id")) == _normalize_text(batch_id)
            ]
        latest_dataset_certification_row = dict(certification_rows[-1]) if certification_rows else {}
        dataset_certification_status = _normalize_text(latest_dataset_certification_row.get("certification_status"), "missing")
        dataset_certification_id = _normalize_text(latest_dataset_certification_row.get("certification_id"))

        source_math_snapshot = {}
        if include_source_math_snapshot:
            try:
                source_math_snapshot = build_math_engine_population_dashboard_snapshot(
                    storage_path=storage.path,
                    backend=backend,
                    dataset_id=DEFAULT_MATH_ENGINE_DATASET_ID,
                    batch_id=_normalize_text(latest_batch.get("source_math_batch_id")),
                )
            except Exception as exc:
                source_math_snapshot = {
                    "ok": False,
                    "status": "math_engine_population_snapshot_error",
                    "warnings": [str(exc)],
                }

        source_math_summary = dict(source_math_snapshot.get("math_engine_population_summary") or {})
        if not source_math_summary:
            source_math_summary_rows = source_math_snapshot.get("math_engine_summary_rows") or []
            if source_math_summary_rows:
                source_math_summary = dict(source_math_summary_rows[-1])
            else:
                source_math_summary = dict(source_math_snapshot)

        latest_row = dict(signal_rows[-1]) if signal_rows else {}
        dataset_row_count = len({row.get("dataset_row_id") for row in signal_rows if row.get("dataset_row_id")})
        signal_definition_ids = list_signal_definition_ids()
        signal_definition_count = len(signal_definition_ids)
        signal_row_count = len(signal_rows)
        missingness_counts = dict(Counter(str(row.get("signal_missingness_state") or "unknown") for row in signal_rows))
        family_counts = dict(Counter(str(row.get("signal_family") or "unknown") for row in signal_rows))
        value_type_counts = dict(Counter(str(row.get("value_type") or "unknown") for row in signal_rows))
        status_counts = dict(Counter(str(row.get("status") or "unknown") for row in signal_rows))
        context_count = len({row.get("signal_context_id") for row in signal_rows if row.get("signal_context_id")})
        readiness_state = _normalize_text(latest_batch.get("readiness"), "missing")
        validation_state = _normalize_text(latest_batch.get("validation_state"), "missing")
        status = _normalize_text(latest_batch.get("status"), "missing")
        signal_validation = validate_signal_rows(signal_rows)

        unresolved_blockers: list[str] = []
        if not signal_rows:
            unresolved_blockers.append("no_signal_rows")
        if not batch_rows:
            unresolved_blockers.append("missing_signal_summary")
        if source_math_snapshot and not source_math_snapshot.get("ok", True):
            unresolved_blockers.extend(_load_json_list(source_math_snapshot.get("unresolved_blockers")) or [str(source_math_snapshot.get("warnings", []))])

        if latest_batch.get("status") != "certified":
            unresolved_blockers.append("signal_batch_not_certified")
        if latest_batch.get("readiness") != "signal_ready":
            unresolved_blockers.append("signal_ready_not_reached")
        if not source_math_summary or _normalize_text(source_math_summary.get("status")) != "certified":
            unresolved_blockers.append("source_math_layer_not_certified")
        if not signal_validation.get("ok", False):
            unresolved_blockers.extend([str(error) for error in signal_validation.get("errors", [])])

        source_feature_snapshot = dict(source_math_snapshot.get("source_feature_snapshot") or {})
        source_feature_summary = dict(source_math_snapshot.get("source_feature_summary") or {})
        source_feature_rows = [dict(row) for row in source_math_snapshot.get("source_feature_rows") or []]
        source_math_rows = [dict(row) for row in source_math_snapshot.get("math_engine_rows") or []]
        signal_snapshot_ids = {str(row.get("snapshot_id")) for row in signal_rows if _normalize_text(row.get("snapshot_id"))}
        signal_context_ids = {str(row.get("signal_context_id")) for row in signal_rows if _normalize_text(row.get("signal_context_id"))}
        signal_dataset_row_ids = {str(row.get("dataset_row_id")) for row in signal_rows if _normalize_text(row.get("dataset_row_id"))}

        summary = dict(latest_batch)
        summary.setdefault("dataset_id", dataset_id)
        summary.setdefault("dataset_name", DEFAULT_SIGNAL_DATASET_NAME)
        summary.setdefault("batch_id", _normalize_text(latest_batch.get("batch_id")))
        summary.setdefault("version_id", _normalize_text(latest_batch.get("version_id"), SIGNAL_TRANSFORMATION_VERSION))
        summary.setdefault("signal_definition_count", signal_definition_count)
        summary.setdefault("signal_row_count", signal_row_count)
        summary.setdefault("signal_context_count", context_count)
        summary.setdefault("source_math_batch_id", _normalize_text(latest_batch.get("source_math_batch_id")))
        summary.setdefault("source_math_population_summary_id", _normalize_text(latest_batch.get("source_math_population_summary_id")))
        summary.setdefault("source_math_certification_id", _normalize_text(latest_batch.get("source_math_certification_id")))
        summary.setdefault("source_math_dataset_certification_id", _normalize_text(latest_batch.get("source_math_dataset_certification_id")))
        summary.setdefault("source_math_evidence_package_id", _normalize_text(latest_batch.get("source_math_evidence_package_id")))
        summary.setdefault("source_math_batch_lineage_id", _normalize_text(latest_batch.get("source_math_batch_lineage_id")))
        summary.setdefault("source_math_row_count", _normalize_int(latest_batch.get("source_math_row_count"), len(source_math_rows)))
        summary.setdefault("source_math_snapshot_count", _normalize_int(latest_batch.get("source_math_snapshot_count"), len(source_math_rows)))
        summary.setdefault("source_math_definition_count", _normalize_int(latest_batch.get("source_math_definition_count"), len(list_math_engine_definition_ids())))
        summary.setdefault("source_feature_row_count", _normalize_int(latest_batch.get("source_feature_row_count"), len(source_feature_rows)))
        summary.setdefault("source_feature_snapshot_count", _normalize_int(latest_batch.get("source_feature_snapshot_count"), len(source_feature_rows)))
        summary.setdefault("source_feature_definition_count", _normalize_int(latest_batch.get("source_feature_definition_count"), len(list_math_engine_definition_ids())))
        summary.setdefault("signal_values_json", _as_json([
            {
                "snapshot_id": row.get("snapshot_id"),
                "signal_id": row.get("signal_id"),
                "signal_name": row.get("signal_name"),
                "signal_family": row.get("signal_family"),
                "value_json": row.get("signal_value_json"),
                "missingness_state": row.get("signal_missingness_state"),
            }
            for row in signal_rows
        ]))
        summary.setdefault("summary_json", _as_json(
            {
                "batch_id": _normalize_text(latest_batch.get("batch_id")),
                "signal_row_count": signal_row_count,
                "signal_definition_count": signal_definition_count,
                "signal_context_count": context_count,
                "source_math_batch_id": _normalize_text(latest_batch.get("source_math_batch_id")),
            }
        ))
        summary.setdefault("payload_json", _as_json(
            {
                "summary": {
                    "batch_id": _normalize_text(latest_batch.get("batch_id")),
                    "signal_row_count": signal_row_count,
                    "signal_definition_count": signal_definition_count,
                    "signal_context_count": context_count,
                },
                "source_math_summary": source_math_summary,
                "signal_values": [
                    {
                        "snapshot_id": row.get("snapshot_id"),
                        "signal_id": row.get("signal_id"),
                        "signal_name": row.get("signal_name"),
                        "signal_family": row.get("signal_family"),
                        "value_json": row.get("signal_value_json"),
                        "missingness_state": row.get("signal_missingness_state"),
                    }
                    for row in signal_rows
                ],
                "lineage_edges": [dict(row) for row in lineage_rows],
            }
        ))
        summary.setdefault("source_feature_dataset_id", _normalize_text(latest_batch.get("source_feature_dataset_id")))
        summary.setdefault("source_feature_dataset_name", _normalize_text(latest_batch.get("source_feature_dataset_name")))
        summary.setdefault("source_feature_batch_id", _normalize_text(latest_batch.get("source_feature_batch_id")))
        summary.setdefault("source_feature_version_id", _normalize_text(latest_batch.get("source_feature_version_id")))
        summary.setdefault("source_feature_certification_id", _normalize_text(latest_batch.get("source_feature_certification_id")))
        summary.setdefault("source_feature_dataset_certification_id", _normalize_text(latest_batch.get("source_feature_dataset_certification_id")))
        summary.setdefault("source_feature_population_summary_id", _normalize_text(latest_batch.get("source_feature_population_summary_id")))
        summary.setdefault("source_feature_evidence_package_id", _normalize_text(latest_batch.get("source_feature_evidence_package_id")))
        summary.setdefault("source_feature_batch_lineage_id", _normalize_text(latest_batch.get("source_feature_batch_lineage_id")))
        summary.setdefault("signal_usage_mode", SIGNAL_USAGE_MODE)
        summary.setdefault("signal_id", f"{DEFAULT_SIGNAL_RESEARCH_ASSET_ID}.summary")
        summary.setdefault("signal_name", "Reusable Signals Summary")
        summary.setdefault("signal_family", "summary")
        summary.setdefault("signal_version", SIGNAL_DEFINITION_VERSION)
        summary.setdefault("classification", "direct")
        summary.setdefault("value_type", "integer")
        summary.setdefault("unit", "rows")
        summary.setdefault("signal_owner", DEFAULT_SIGNAL_OWNER)
        summary.setdefault("entity_scope", "data_quality_context")
        summary.setdefault("dataset_grain_compatibility", CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID)
        summary.setdefault("transformation_version", SIGNAL_TRANSFORMATION_VERSION)
        summary.setdefault("missingness_policy", "required")
        summary.setdefault("signal_context_id", _stable_id("signal_snapshot_context", _normalize_text(latest_batch.get("batch_id")), "summary"))
        summary.setdefault("signal_missingness_state", "present" if signal_rows else "missing_required")
        summary.setdefault("signal_missingness_reason", "" if signal_rows else "no_signal_rows_produced")
        summary.setdefault("signal_snapshot_grain_id", CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID)
        summary.setdefault("signal_registry_schema_version", SIGNAL_POPULATION_SCHEMA_VERSION)
        summary.setdefault("signal_lineage_id", _normalize_text(latest_batch.get("lineage_id")))
        summary.setdefault("signal_evidence_id", _normalize_text(latest_batch.get("evidence_package_id")))

        result = {
            "ok": status == "certified" and not unresolved_blockers,
            "status": status,
            "schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "dataset_name": DEFAULT_SIGNAL_DATASET_NAME,
            "batch_id": _normalize_text(latest_batch.get("batch_id")),
            "version_id": _normalize_text(latest_batch.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
            "dataset_row_count": dataset_row_count,
            "signal_definition_count": signal_definition_count,
            "signal_row_count": signal_row_count,
            "signal_context_count": context_count,
            "signal_rows": signal_rows,
            "signal_summary_rows": batch_rows,
            "signal_population_summary": summary,
            "signal_population_summary_id": _normalize_text(summary.get("snapshot_id")),
            "signal_evidence_package_id": _normalize_text(summary.get("evidence_package_id")),
            "signal_lineage_edges": lineage_rows,
            "signal_alignment_rows": [
                row
                for row in alignment_rows_all
                if _normalize_text(row.get("batch_id")) == _normalize_text(latest_batch.get("batch_id"))
            ],
            "signal_lifecycle_rows": [
                row
                for row in lifecycle_rows_all
                if _normalize_text(row.get("batch_id")) == _normalize_text(latest_batch.get("batch_id"))
            ],
            "dataset_certification_status": dataset_certification_status,
            "dataset_certification_id": dataset_certification_id,
            "lifecycle_state": _normalize_text(latest_batch.get("readiness"), "missing"),
            "source_math_snapshot": source_math_snapshot,
            "source_math_summary": source_math_summary,
            "source_math_population_snapshot": source_math_snapshot,
            "source_math_population_summary": source_math_summary,
            "source_math_rows": source_math_rows,
            "source_math_batch_id": _normalize_text(summary.get("source_math_batch_id")),
            "source_math_certification_id": _normalize_text(summary.get("source_math_certification_id")),
            "source_math_dataset_certification_id": _normalize_text(summary.get("source_math_dataset_certification_id")),
            "source_math_evidence_package_id": _normalize_text(summary.get("source_math_evidence_package_id")),
            "source_math_population_summary_id": _normalize_text(summary.get("source_math_population_summary_id")),
            "source_math_batch_lineage_id": _normalize_text(summary.get("source_math_batch_lineage_id")),
            "join_diagnostics": {
                "source_math_row_count": len(source_math_rows),
                "signal_row_count": signal_row_count,
                "signal_definition_count": signal_definition_count,
                "context_count": context_count,
                "signal_snapshot_ids": sorted(signal_snapshot_ids),
                "signal_context_ids": sorted(signal_context_ids),
                "signal_dataset_row_ids": sorted(signal_dataset_row_ids),
            },
            "registry": summarize_signal_registry(),
            "validation": signal_validation,
            "signal_validation": signal_validation,
            "storage": storage.health(),
            "unresolved_blockers": unresolved_blockers,
            "readiness": readiness_state if status == "certified" else "blocked",
            "validation_state": validation_state,
            "signal_context_ids": sorted(signal_context_ids),
            "signal_definition_ids": signal_definition_ids,
            "warnings": unresolved_blockers,
            "idempotent_reuse": idempotent_reuse,
            "source_feature_snapshot": source_feature_snapshot,
            "source_feature_summary": source_feature_summary,
            "source_feature_rows": source_feature_rows,
        }
        result["signal_population_summary"]["summary"] = dict(summary)
        return result
    finally:
        storage.close()


def build_signal_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_SIGNAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    storage = create_local_storage_engine(storage_path or DEFAULT_SIGNAL_STORAGE_PATH, backend=backend)
    try:
        persisted_snapshot = _load_signal_population_snapshot(
            storage,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=batch_id,
        )
        if persisted_snapshot.get("ok"):
            return persisted_snapshot
        if persisted_snapshot.get("signal_rows") or persisted_snapshot.get("signal_summary_rows"):
            raise ValueError("; ".join(persisted_snapshot.get("unresolved_blockers", [])) or "existing signal batch is incomplete")

        math_snapshot = build_math_engine_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=DEFAULT_MATH_ENGINE_DATASET_ID,
            batch_id=None,
        )
        math_summary = dict(math_snapshot.get("math_engine_population_summary") or {})
        math_rows = [dict(row) for row in math_snapshot.get("math_engine_rows") or []]
        if not math_summary and math_snapshot.get("math_engine_summary_rows"):
            math_summary = dict(math_snapshot["math_engine_summary_rows"][-1])
        if not math_summary or not math_rows:
            return _signal_population_missing_snapshot(
                storage=storage,
                dataset_id=dataset_id,
                batch_id=_normalize_text(batch_id),
                status="missing_math_layer",
                warnings=["certified math engine outputs are required"],
            )
        math_dataset_certification_id = _normalize_text(
            math_snapshot.get("dataset_certification_id"),
            math_summary.get("dataset_certification_id"),
        )
        if math_dataset_certification_id:
            math_summary.setdefault("certification_id", math_dataset_certification_id)
            math_summary.setdefault("dataset_certification_id", math_dataset_certification_id)

        grouped_contexts: list[list[dict[str, Any]]] = []
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in math_rows:
            grouped[(
                _normalize_text(row.get("dataset_row_id")),
                _normalize_text(row.get("decision_context_id")),
            )].append(dict(row))
        for (_, _), rows in sorted(grouped.items()):
            rows.sort(key=lambda row: (_normalize_text(row.get("engine_id")), _normalize_text(row.get("snapshot_id"))))
            grouped_contexts.append(rows)

        provisional_signal_contexts = [
            build_signal_snapshot_context(
                dataset_id=dataset_id,
                batch_id=_normalize_text(batch_id) or _signal_population_batch_id(dataset_id, _normalize_text(math_summary.get("batch_id")), contexts=[]),
                summary_row=math_summary,
                math_rows=math_rows,
                context_rows=context_rows,
            )
            for context_rows in grouped_contexts
        ]
        signal_batch_id = _normalize_text(batch_id) or _signal_population_batch_id(dataset_id, _normalize_text(math_summary.get("batch_id")), contexts=provisional_signal_contexts)
        signal_contexts = [
            build_signal_snapshot_context(
                dataset_id=dataset_id,
                batch_id=signal_batch_id,
                summary_row=math_summary,
                math_rows=math_rows,
                context_rows=context_rows,
            )
            for context_rows in grouped_contexts
        ]
        signal_version_id = _stable_id(
            "signal_snapshot_version",
            dataset_id,
            signal_batch_id,
            SIGNAL_POPULATION_SCHEMA_VERSION,
            SIGNAL_DEFINITION_VERSION,
            SIGNAL_TRANSFORMATION_VERSION,
        )
        existing_summary_rows = storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
            params=[dataset_id, signal_batch_id, SIGNAL_BATCH_KIND],
        )
        existing_signal_rows = storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
            params=[dataset_id, signal_batch_id, SIGNAL_ROW_KIND],
        )
        expected_signal_row_count = len(signal_contexts) * len(_SIGNAL_DEFINITIONS)
        if existing_summary_rows and len(existing_signal_rows) == expected_signal_row_count:
            return build_signal_population_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
                dataset_id=dataset_id,
                batch_id=signal_batch_id,
                include_source_math_snapshot=True,
                idempotent_reuse=True,
            )

        signal_rows: list[dict[str, Any]] = []
        lineage_rows: list[dict[str, Any]] = []
        alignment_rows: list[dict[str, Any]] = []
        validation_rows: list[dict[str, Any]] = []
        for context_rows, context in zip(grouped_contexts, signal_contexts):
            math_lookup = {
                _normalize_text(row.get("engine_id") or row.get("output_feature_id")): dict(row)
                for row in context_rows
                if _normalize_text(row.get("engine_id") or row.get("output_feature_id"))
            }
            for definition in _SIGNAL_DEFINITIONS:
                row, lineage_row = _signal_row_payload_and_values(
                    definition=definition,
                    context=context,
                    summary_row=math_summary,
                    math_lookup=math_lookup,
                    storage_location=str(storage.path),
                    created_at=_utc_now_iso(),
                )
                row["version_id"] = signal_version_id
                lineage_row["version_id"] = signal_version_id
                signal_rows.append(row)
                lineage_rows.append(lineage_row)
                validation_rows.append(
                    {
                        **row,
                        "provider_timestamp": _normalize_text(math_summary.get("decision_cutoff_time"), row.get("decision_cutoff_time")),
                        "snapshot_time": row.get("decision_cutoff_time"),
                        "decision_time": row.get("decision_cutoff_time"),
                        "result_timestamp": "",
                    }
                )

        signal_validation = validate_signal_rows(signal_rows)
        if not signal_validation["ok"]:
            raise ValueError("; ".join(signal_validation.get("errors", [])) or "signal rows failed validation")

        summary_row = _signal_row_payload_and_values(
            definition=_signal(
                f"{DEFAULT_SIGNAL_RESEARCH_ASSET_ID}.summary",
                signal_name="Reusable Signals Summary",
                signal_family="summary",
                entity_scope="data_quality_context",
                classification="direct",
                value_type="integer",
                unit="rows",
                source_math_engine_output_refs=(),
                source_math_summary_refs=("math.sports.nfl.math_engine_population_summary",),
                transformation_definition="summary row representing the reusable signal batch",
                expected_range="row count summary",
            ),
            context=signal_contexts[0] if signal_contexts else build_signal_snapshot_context(
                dataset_id=dataset_id,
                batch_id=signal_batch_id,
                summary_row=math_summary,
                math_rows=math_rows,
                context_rows=[dict(math_rows[0])] if math_rows else [],
            ),
            summary_row=math_summary,
            math_lookup={},
            storage_location=str(storage.path),
            created_at=_utc_now_iso(),
        )[0]
        summary_row["snapshot_id"] = _stable_id(
            "signal_population_summary_snapshot",
            dataset_id,
            signal_batch_id,
            SIGNAL_TRANSFORMATION_VERSION,
        )
        summary_row["dataset_id"] = dataset_id
        summary_row["dataset_name"] = DEFAULT_SIGNAL_DATASET_NAME
        summary_row["owner"] = DEFAULT_SIGNAL_OWNER
        summary_row["signal_pack"] = DEFAULT_SIGNAL_RESEARCH_ASSET_ID
        summary_row["readiness"] = "signal_ready"
        summary_row["update_frequency"] = "manual"
        summary_row["validation_state"] = "validated"
        summary_row["status"] = "certified"
        summary_row["batch_id"] = signal_batch_id
        summary_row["snapshot_kind"] = SIGNAL_BATCH_KIND
        summary_row["signal_pack_version"] = SIGNAL_DEFINITION_VERSION
        summary_row["source_feature_dataset_id"] = _normalize_text(math_summary.get("source_feature_dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID)
        summary_row["source_feature_dataset_name"] = _normalize_text(math_summary.get("source_feature_dataset_name"), DEFAULT_SIGNAL_DATASET_NAME)
        summary_row["source_feature_batch_id"] = _normalize_text(math_summary.get("source_feature_batch_id"))
        summary_row["source_feature_version_id"] = _normalize_text(math_summary.get("source_feature_version_id"), MATH_ENGINE_TRANSFORMATION_VERSION)
        summary_row["source_feature_certification_id"] = _normalize_text(math_summary.get("source_feature_certification_id"))
        summary_row["source_feature_dataset_certification_id"] = _normalize_text(math_summary.get("source_feature_dataset_certification_id"))
        summary_row["source_feature_population_summary_id"] = _normalize_text(math_summary.get("source_feature_population_summary_id"))
        summary_row["source_feature_evidence_package_id"] = _normalize_text(math_summary.get("source_feature_evidence_package_id"))
        summary_row["source_feature_batch_lineage_id"] = _normalize_text(math_summary.get("source_feature_batch_lineage_id"))
        summary_row["source_feature_row_count"] = _normalize_int(math_summary.get("source_feature_row_count"), 0)
        summary_row["source_feature_snapshot_count"] = _normalize_int(math_summary.get("source_feature_snapshot_count"), 0)
        summary_row["source_feature_definition_count"] = _normalize_int(math_summary.get("source_feature_definition_count"), 0)
        summary_row["source_math_dataset_id"] = _normalize_text(math_summary.get("dataset_id"), DEFAULT_MATH_ENGINE_DATASET_ID)
        summary_row["source_math_dataset_name"] = _normalize_text(math_summary.get("dataset_name"), "nfl_math_engine_snapshots")
        summary_row["source_math_batch_id"] = _normalize_text(math_summary.get("batch_id"))
        summary_row["source_math_version_id"] = _normalize_text(math_summary.get("version_id"), MATH_ENGINE_TRANSFORMATION_VERSION)
        summary_row["source_math_certification_id"] = _normalize_text(math_summary.get("certification_id"))
        summary_row["source_math_dataset_certification_id"] = _normalize_text(math_summary.get("dataset_certification_id"))
        summary_row["source_math_population_summary_id"] = _normalize_text(math_summary.get("snapshot_id"))
        summary_row["source_math_evidence_package_id"] = _normalize_text(math_summary.get("evidence_package_id"))
        summary_row["source_math_batch_lineage_id"] = _normalize_text(math_summary.get("lineage_id"))
        summary_row["source_math_row_count"] = _normalize_int(math_summary.get("record_count"), len(math_rows))
        summary_row["source_math_snapshot_count"] = _normalize_int(math_summary.get("source_math_snapshot_count"), len(math_rows))
        summary_row["source_math_definition_count"] = _normalize_int(math_summary.get("source_math_definition_count"), len(list_math_engine_definition_ids()))
        summary_row["record_count"] = len(signal_rows)
        summary_row["signal_count"] = len(signal_rows)
        summary_row["signal_values_json"] = _as_json(
            {
                "signal_row_count": len(signal_rows),
                "signal_definition_count": len(_SIGNAL_DEFINITIONS),
                "signal_context_count": len(signal_contexts),
            }
        )
        summary_row["summary_json"] = _as_json(
            {
                "batch_id": signal_batch_id,
                "signal_row_count": len(signal_rows),
                "signal_definition_count": len(_SIGNAL_DEFINITIONS),
                "signal_context_count": len(signal_contexts),
                "source_math_row_count": len(math_rows),
            }
        )
        summary_row["payload_json"] = _as_json(
            {
                "summary": {
                    "batch_id": signal_batch_id,
                    "signal_row_count": len(signal_rows),
                    "signal_definition_count": len(_SIGNAL_DEFINITIONS),
                    "signal_context_count": len(signal_contexts),
                },
                "source_math_summary": dict(math_summary),
                "signal_values": [
                    {
                        "snapshot_id": row.get("snapshot_id"),
                        "signal_id": row.get("signal_id"),
                        "signal_name": row.get("signal_name"),
                        "signal_family": row.get("signal_family"),
                        "value_json": row.get("signal_value_json"),
                        "missingness_state": row.get("signal_missingness_state"),
                    }
                    for row in signal_rows
                ],
                "lineage_edges": [dict(row) for row in lineage_rows],
            }
        )
        summary_row["schema_version"] = SIGNAL_POPULATION_SCHEMA_VERSION
        summary_row["created_at"] = _utc_now_iso()
        summary_row["updated_at"] = summary_row["created_at"]
        summary_row["source"] = DEFAULT_SIGNAL_SOURCE_NAME
        summary_row["provider"] = DEFAULT_SIGNAL_PROVIDER
        summary_row["market"] = DEFAULT_SIGNAL_MARKET
        summary_row["market_type"] = DEFAULT_SIGNAL_MARKET_TYPE
        summary_row["asset_class"] = DEFAULT_SIGNAL_ASSET_CLASS
        summary_row["lineage_id"] = _stable_id(
            "signal_snapshot_population_lineage",
            dataset_id,
            signal_batch_id,
            summary_row["snapshot_id"],
        )
        summary_row["version_id"] = signal_version_id
        summary_row["quality_score"] = 1.0 if signal_rows else 0.0
        summary_row["signal_id"] = f"{DEFAULT_SIGNAL_RESEARCH_ASSET_ID}.summary"
        summary_row["signal_name"] = "Reusable Signals Summary"
        summary_row["signal_family"] = "summary"
        summary_row["signal_version"] = SIGNAL_DEFINITION_VERSION
        summary_row["classification"] = "direct"
        summary_row["value_type"] = "integer"
        summary_row["unit"] = "rows"
        summary_row["signal_owner"] = DEFAULT_SIGNAL_OWNER
        summary_row["entity_scope"] = "data_quality_context"
        summary_row["dataset_grain_compatibility"] = CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID
        summary_row["transformation_version"] = SIGNAL_TRANSFORMATION_VERSION
        summary_row["missingness_policy"] = "required"
        summary_row["signal_context_id"] = _stable_id("signal_snapshot_context", signal_batch_id, "summary")
        summary_row["signal_usage_mode"] = SIGNAL_USAGE_MODE
        summary_row["signal_value_json"] = _as_json(
            {
                "signal_row_count": len(signal_rows),
                "signal_definition_count": len(_SIGNAL_DEFINITIONS),
                "signal_context_count": len(signal_contexts),
                "signal_usage_mode": SIGNAL_USAGE_MODE,
            }
        )
        summary_row["signal_value_text"] = None
        summary_row["signal_value_number"] = len(signal_rows)
        summary_row["signal_value_boolean"] = None
        summary_row["signal_missingness_state"] = "present" if signal_rows else "missing_required"
        summary_row["signal_missingness_reason"] = "" if signal_rows else "no_signal_rows_produced"
        summary_row["signal_definition_json"] = _as_json(
            {
                "signal_id": summary_row["signal_id"],
                "signal_name": summary_row["signal_name"],
                "signal_family": summary_row["signal_family"],
                "classification": summary_row["classification"],
                "value_type": summary_row["value_type"],
            }
        )
        summary_row["signal_context_json"] = _as_json(
            {
                "batch_id": signal_batch_id,
                "summary": True,
                "signal_contexts": [context.as_dict() for context in signal_contexts],
                "source_math_summary": dict(math_summary),
            }
        )
        summary_row["signal_snapshot_grain_id"] = CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID
        summary_row["signal_registry_schema_version"] = SIGNAL_POPULATION_SCHEMA_VERSION
        summary_row["signal_lineage_id"] = _stable_id(
            "signal_population_summary_lineage",
            signal_batch_id,
            summary_row["snapshot_id"],
            summary_row["version_id"],
        )
        summary_row["signal_evidence_id"] = _stable_id(
            "signal_population_summary_evidence",
            summary_row["snapshot_id"],
            signal_batch_id,
            _as_json([row.get("snapshot_id") for row in signal_rows]),
        )
        _apply_signal_summary_source_feature_maps(summary_row, signal_rows)
        summary_row["source_math_output_ids_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_ids": list(definition.source_math_engine_output_refs),
                    "summary_refs": list(definition.source_math_summary_refs),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_snapshot_ids_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_snapshot_ids": [
                        _normalize_text(math_lookup.get(ref, {}).get("snapshot_id"))
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    ],
                    "summary_snapshot_id": _normalize_text(summary_row.get("source_math_population_summary_id")),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_lineage_ids_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_lineage_ids": [
                        _normalize_text(math_lookup.get(ref, {}).get("engine_lineage_id"))
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    ],
                    "summary_lineage_id": _normalize_text(summary_row.get("source_math_batch_lineage_id")),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_certification_ids_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_certification_ids": [
                        _normalize_text(math_lookup.get(ref, {}).get("certification_id"))
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    ],
                    "summary_certification_id": _normalize_text(summary_row.get("source_math_certification_id")),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_dataset_certification_ids_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_dataset_certification_ids": [
                        _normalize_text(math_lookup.get(ref, {}).get("dataset_certification_id"))
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    ],
                    "summary_dataset_certification_id": _normalize_text(summary_row.get("source_math_dataset_certification_id")),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_missingness_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_missingness": {
                        ref: _math_missingness(math_lookup[ref])
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    },
                    "summary_missingness": _normalize_text(summary_row.get("validation_state"), "validated"),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_freshness_json"] = _as_json(
            {
                definition.signal_id: {
                    "feature_freshness_seconds": _signal_freshness_map(math_summary),
                    "summary_snapshot_id": _normalize_text(summary_row.get("source_math_population_summary_id")),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_value_types_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_value_types": {
                        ref: _normalize_text(math_lookup.get(ref, {}).get("value_type"))
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    },
                    "summary_value_type": "string" if definition.signal_id.endswith("state") else _normalize_text(summary_row.get("value_type"), "integer"),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["source_math_values_json"] = _as_json(
            {
                definition.signal_id: {
                    "engine_values": {
                        ref: _math_value(math_lookup[ref])
                        for ref in definition.source_math_engine_output_refs
                        if ref in math_lookup
                    },
                    "summary_value": len(signal_rows),
                }
                for definition in _SIGNAL_DEFINITIONS
            }
        )
        summary_row["missing_required_assets_json"] = _as_json([])
        summary_row["evidence_package_id"] = _stable_id(
            "signal_population_summary_evidence_package",
            math_summary.get("evidence_package_id"),
            signal_batch_id,
            SIGNAL_TRANSFORMATION_VERSION,
        )
        summary_row["record_count"] = len(signal_rows)
        summary_row["signal_count"] = len(signal_rows)

        source_bundle = {
            "source_name": DEFAULT_SIGNAL_SOURCE_NAME,
            "source_type": DEFAULT_SIGNAL_SOURCE_TYPE,
            "source_key": DEFAULT_SIGNAL_SOURCE_KEY,
            "provider": DEFAULT_SIGNAL_PROVIDER,
            "source_file": _normalize_text(math_summary.get("storage_location")),
            "source_snapshot_time": _normalize_text(math_summary.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(math_summary.get("decision_cutoff_time")),
            "decision_time": _normalize_text(math_summary.get("decision_cutoff_time")),
            "result_timestamp": _normalize_text(math_summary.get("created_at") or math_summary.get("updated_at")),
        }
        raw_acquisition_result = {
            "ok": True,
            "status": "math_output_input",
            "dataset_id": DEFAULT_SIGNAL_DATASET_ID,
            "source_file": _normalize_text(math_summary.get("storage_location")),
            "source_snapshot_time": _normalize_text(math_summary.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(math_summary.get("decision_cutoff_time")),
            "decision_time": _normalize_text(math_summary.get("decision_cutoff_time")),
            "result_timestamp": _normalize_text(math_summary.get("created_at") or math_summary.get("updated_at")),
        }

        signal_asset_contract = ResearchAssetCertificationContract(
            research_asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
            research_asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
            asset_category="signal",
            asset_type="snapshot_batch",
            source_table_name="signal_snapshots",
            required_fields=_required_row_fields(),
            required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
            point_in_time_rules=(
                "scheduled_kickoff_time must predate the decision cutoff",
                "decision_cutoff_time must remain unchanged from the certified historical dataset row",
                "signal outputs must remain observation-only and math-derived",
            ),
            description=(
                "Deterministic reusable signals derived only from certified mathematical-engine outputs "
                "and preserved with explicit provenance, lineage, and point-in-time constraints."
            ),
            priority="P0",
            required=True,
            future_asset=False,
            metadata={
                "market_profile": DEFAULT_SIGNAL_PROFILE_ID,
                "market_family": "sports",
                "minimum_schema": True,
                "dataset_role": "signal_population",
                "source_math_batch_id": signal_batch_id,
                "source_math_certification_id": _normalize_text(summary_row.get("source_math_certification_id")),
                "source_math_dataset_certification_id": _normalize_text(summary_row.get("source_math_dataset_certification_id")),
                "source_math_evidence_package_id": _normalize_text(summary_row.get("source_math_evidence_package_id")),
                "source_math_population_summary_id": _normalize_text(summary_row.get("source_math_population_summary_id")),
                "source_feature_batch_id": _normalize_text(summary_row.get("source_feature_batch_id")),
                "source_feature_certification_id": _normalize_text(summary_row.get("source_feature_certification_id")),
                "source_feature_dataset_certification_id": _normalize_text(summary_row.get("source_feature_dataset_certification_id")),
                "source_feature_evidence_package_id": _normalize_text(summary_row.get("source_feature_evidence_package_id")),
                "source_feature_population_summary_id": _normalize_text(summary_row.get("source_feature_population_summary_id")),
            },
        )

        certification_runtime = HistoricalResearchAssetCertificationRuntime(
            storage_path=storage.path,
            backend=backend,
            store=storage,
        )
        lifecycle_runtime = ResearchAssetLifecycleRuntime(
            storage_path=storage.path,
            backend=backend,
            store=storage,
        )
        signal_result = certification_runtime.certify_research_asset(
            asset_contract=signal_asset_contract,
            rows=signal_rows + [summary_row],
            profile_id=DEFAULT_SIGNAL_PROFILE_ID,
            validation=signal_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=SIGNAL_TRANSFORMATION_VERSION,
            created_at=_utc_now_iso(),
            batch_id=signal_batch_id,
        )
        signal_certification_row = dict(signal_result["research_asset_certification"])
        storage.upsert("signal_snapshots", summary_row, key_columns=("snapshot_id",))
        for row in signal_rows:
            storage.upsert("signal_snapshots", row, key_columns=("snapshot_id",))
        for lineage_row in lineage_rows:
            storage.upsert("lineage_edges", lineage_row, key_columns=("lineage_edge_id",))

        signal_dataset_row = build_historical_dataset_certification_row(
            profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
            dataset_version=SIGNAL_TRANSFORMATION_VERSION,
            batch_id=signal_batch_id,
            created_at=_utc_now_iso(),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=[signal_certification_row],
        )
        storage.upsert("historical_certifications", signal_dataset_row, key_columns=("certification_id",))

        signal_identity = build_research_asset_identity_contract(
            asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
            asset_family="signal",
            market_profile=DEFAULT_SIGNAL_PROFILE_ID,
            market=DEFAULT_SIGNAL_MARKET,
            league="nfl",
            sport="football",
            season=str(summary_row.get("season") or ""),
            week_or_date=str(summary_row.get("week") or ""),
            event_id=_normalize_text(summary_row.get("event_id")),
            market_id=f"{signal_batch_id}.signal",
            selection="signal_population",
            provider=DEFAULT_SIGNAL_PROVIDER,
            connector="math_engine_population",
            schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
            lineage_version=signal_batch_id,
            asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
            asset_type="signal_snapshot_batch",
            team_id=_normalize_text(summary_row.get("target_team_id") or summary_row.get("home_team_id") or summary_row.get("away_team_id")),
            game_id=_normalize_text(summary_row.get("game_id") or summary_row.get("event_id")),
            market_type=DEFAULT_SIGNAL_MARKET_TYPE,
        )
        identity_validation = validate_research_asset_identity_contract(signal_identity)
        if not identity_validation["ok"]:
            raise ValueError("; ".join(identity_validation.get("errors", [])) or "signal identity validation failed")

        signal_alignment_rows_result: list[dict[str, Any]] = []
        for row in signal_rows + [summary_row]:
            row_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
                asset_family="signal",
                market_profile=DEFAULT_SIGNAL_PROFILE_ID,
                market=DEFAULT_SIGNAL_MARKET,
                league="nfl",
                sport="football",
                season=str(row.get("season") or ""),
                week_or_date=str(row.get("week") or ""),
                event_id=_normalize_text(row.get("event_id")),
                market_id=_normalize_text(row.get("signal_id")),
                selection=_normalize_text(row.get("signal_id")),
                provider=DEFAULT_SIGNAL_PROVIDER,
                connector="math_engine_population",
                schema_version=SIGNAL_POPULATION_SCHEMA_VERSION,
                lineage_version=_normalize_text(row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
                asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                asset_type="signal_snapshot",
                team_id=_normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                game_id=_normalize_text(row.get("game_id") or row.get("event_id")),
                market_type=DEFAULT_SIGNAL_MARKET_TYPE,
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[
                    {
                        **dict(row),
                        "asset_id": DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
                        "asset_family": "signal",
                        "asset_name": DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                        "asset_type": "signal_snapshot",
                        "lineage_version": _normalize_text(row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION),
                        "market_id": _normalize_text(row.get("signal_id")),
                        "provider_timestamp": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                        "result_timestamp": "",
                        "market_profile": DEFAULT_SIGNAL_PROFILE_ID,
                        "market": DEFAULT_SIGNAL_MARKET,
                        "league": "nfl",
                        "sport": "football",
                        "week_or_date": str(row.get("week") or ""),
                        "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                        "participant_id": "",
                        "selection": _normalize_text(row.get("signal_id")),
                        "connector": "math_engine_population",
                    }
                ],
                required_fields=(
                    "dataset_id",
                    "dataset_name",
                    "snapshot_id",
                    "batch_id",
                    "signal_id",
                    "signal_name",
                    "signal_family",
                    "signal_version",
                    "classification",
                    "value_type",
                    "unit",
                    "signal_owner",
                    "entity_scope",
                    "dataset_grain_compatibility",
                    "transformation_version",
                    "missingness_policy",
                    "signal_context_id",
                    "signal_value_json",
                    "signal_definition_json",
                    "signal_context_json",
                    "signal_snapshot_grain_id",
                    "signal_registry_schema_version",
                    "signal_lineage_id",
                    "signal_evidence_id",
                    "source_feature_ids_json",
                    "source_feature_snapshot_ids_json",
                    "source_feature_lineage_ids_json",
                    "source_feature_certification_ids_json",
                    "source_feature_dataset_certification_ids_json",
                    "source_feature_alignment_certification_ids_json",
                    "source_math_output_ids_json",
                    "source_math_snapshot_ids_json",
                    "source_math_lineage_ids_json",
                    "source_math_certification_ids_json",
                    "source_math_dataset_certification_ids_json",
                    "evidence_package_id",
                    "signal_usage_mode",
                ),
                required_timestamps=("provider_timestamp", "snapshot_time", "decision_time"),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=_utc_now_iso(),
                asset_name=DEFAULT_SIGNAL_RESEARCH_ASSET_NAME,
                asset_type="signal_snapshot",
                lifecycle_state="signal_ready",
                batch_id=_normalize_text(row.get("snapshot_id")),
            )
            alignment_row = build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                batch_id=signal_batch_id,
            )
            alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
            if not alignment_validation["ok"]:
                raise ValueError("; ".join(alignment_validation.get("issues", [])) or "signal alignment validation failed")
            storage.upsert("research_asset_alignment_certifications", alignment_row, key_columns=("alignment_certification_id",))
            signal_alignment_rows_result.append(
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
                identity=signal_identity,
                lifecycle_state="signal_ready",
                lifecycle_reason=f"{DEFAULT_SIGNAL_RESEARCH_ASSET_NAME} promoted to signal_ready",
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=_utc_now_iso(),
                certification_result=signal_certification_row,
                dataset_result=signal_dataset_row,
                notes={
                    "batch_id": signal_batch_id,
                    "signal_row_count": len(signal_rows),
                    "signal_definition_count": len(_SIGNAL_DEFINITIONS),
                    "signal_context_count": len(signal_contexts),
                    "source_math_batch_id": signal_batch_id,
                    "previous_states": ["research_asset_certified", "dataset_certified"],
                    "observation_only": True,
                },
            )
        ]

        return build_signal_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=signal_batch_id,
            include_source_math_snapshot=True,
            idempotent_reuse=False,
        )
    finally:
        storage.close()


def get_signal_population_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_SIGNAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    try:
        return build_signal_population_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=batch_id,
            include_source_math_snapshot=True,
            idempotent_reuse=False,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "signal_population_snapshot_error",
            "schema_version": SIGNAL_POPULATION_SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "dataset_name": DEFAULT_SIGNAL_DATASET_NAME,
            "batch_id": _normalize_text(batch_id),
            "version_id": "",
            "dataset_row_count": 0,
            "signal_definition_count": len(_SIGNAL_DEFINITIONS),
            "signal_row_count": 0,
            "signal_context_count": 0,
            "signal_rows": [],
            "signal_summary_rows": [],
            "signal_population_summary": {},
            "signal_population_summary_id": "",
            "signal_evidence_package_id": "",
            "signal_lineage_edges": [],
            "signal_alignment_rows": [],
            "signal_lifecycle_rows": [],
            "dataset_certification_status": "missing",
            "dataset_certification_id": "",
            "lifecycle_state": "missing",
            "source_math_snapshot": {},
            "source_math_summary": {},
            "source_math_population_snapshot": {},
            "source_math_population_summary": {},
            "source_math_rows": [],
            "source_math_batch_id": "",
            "source_math_certification_id": "",
            "source_math_dataset_certification_id": "",
            "source_math_evidence_package_id": "",
            "source_math_population_summary_id": "",
            "source_math_batch_lineage_id": "",
            "join_diagnostics": {},
            "registry": {},
            "validation": {},
            "signal_validation": {},
            "storage": {},
            "unresolved_blockers": [str(exc)],
            "readiness": "blocked",
            "validation_state": "rejected",
            "signal_context_ids": [],
            "signal_definition_ids": list_signal_definition_ids(),
            "warnings": [str(exc)],
            "idempotent_reuse": False,
        }


__all__ = [
    "CANONICAL_SIGNAL_SNAPSHOT_GRAIN_ID",
    "DEFAULT_SIGNAL_ASSET_CLASS",
    "DEFAULT_SIGNAL_DATASET_ID",
    "DEFAULT_SIGNAL_DATASET_NAME",
    "DEFAULT_SIGNAL_MARKET",
    "DEFAULT_SIGNAL_MARKET_TYPE",
    "DEFAULT_SIGNAL_OWNER",
    "DEFAULT_SIGNAL_PORTABILITY_CLASSIFICATION",
    "DEFAULT_SIGNAL_PROFILE_ID",
    "DEFAULT_SIGNAL_PROVIDER",
    "DEFAULT_SIGNAL_RESEARCH_ASSET_ID",
    "DEFAULT_SIGNAL_RESEARCH_ASSET_NAME",
    "DEFAULT_SIGNAL_SOURCE_KEY",
    "DEFAULT_SIGNAL_SOURCE_NAME",
    "DEFAULT_SIGNAL_SOURCE_TYPE",
    "DEFAULT_SIGNAL_STORAGE_PATH",
    "SIGNAL_ALLOWED_CLASSIFICATIONS",
    "SIGNAL_ALLOWED_ENTITY_SCOPES",
    "SIGNAL_ALLOWED_MISSINGNESS_POLICIES",
    "SIGNAL_ALLOWED_VALUE_TYPES",
    "SIGNAL_BATCH_KIND",
    "SIGNAL_DEFINITION_VERSION",
    "SIGNAL_POPULATION_SCHEMA_VERSION",
    "SIGNAL_ROW_KIND",
    "SIGNAL_SUMMARY_ROW_KIND",
    "SIGNAL_TRANSFORMATION_VERSION",
    "SIGNAL_USAGE_MODE",
    "SignalDefinition",
    "SignalSnapshotContext",
    "build_signal_population",
    "build_signal_population_dashboard_snapshot",
    "build_signal_snapshot_context",
    "build_signal_snapshot_context_id",
    "build_signal_value_identity",
    "get_signal_definition",
    "get_signal_population_snapshot_for_dashboard",
    "list_signal_definition_ids",
    "list_signal_definitions",
    "list_signal_families",
    "summarize_signal_registry",
    "validate_signal_registry",
    "validate_signal_rows",
]
