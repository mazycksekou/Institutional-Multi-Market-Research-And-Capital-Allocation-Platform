from __future__ import annotations

"""Reusable decision-row population from certified reusable signal outputs.

The decision-row layer is observational. It reads only persisted Phase 5.3
signal outputs, preserves their upstream dataset / feature / math / signal
references, and materializes deterministic decision records without adding any
execution intent, trade recommendation, or backtesting runtime.
"""

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.data.data_paths import get_runtime_data_path
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
from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE
from src.market_intelligence.signal_population import (
    DEFAULT_SIGNAL_DATASET_ID,
    DEFAULT_SIGNAL_RESEARCH_ASSET_ID,
    SIGNAL_BATCH_KIND,
    SIGNAL_DEFINITION_VERSION,
    SIGNAL_TRANSFORMATION_VERSION,
    SIGNAL_USAGE_MODE,
    SIGNAL_ROW_KIND,
    list_signal_definition_ids,
)
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


DECISION_POPULATION_SCHEMA_VERSION = "src.backtesting.decision_row_population.v1"
DECISION_DEFINITION_VERSION = "phase5.4.decision_definitions.v1"
DECISION_TRANSFORMATION_VERSION = "phase5.4.decision_row_population.v1"
DEFAULT_DECISION_RESEARCH_ASSET_ID = "decision.sports.reusable_decision_rows"
DEFAULT_DECISION_RESEARCH_ASSET_NAME = "Reusable Decision Rows"
DEFAULT_DECISION_DATASET_ID = "dataset.sports.nfl.decision_rows"
DEFAULT_DECISION_DATASET_NAME = "nfl_decision_rows"
DEFAULT_DECISION_STORAGE_PATH = get_runtime_data_path("decision_row_population", "canonical_data.sqlite")
DEFAULT_DECISION_OWNER = "src.backtesting"
DEFAULT_DECISION_PROVIDER = "repository"
DEFAULT_DECISION_SOURCE_NAME = "signal_population"
DEFAULT_DECISION_SOURCE_TYPE = "signal_population"
DEFAULT_DECISION_SOURCE_KEY = "signal_population"
DEFAULT_DECISION_MARKET = "sports:nfl"
DEFAULT_DECISION_MARKET_TYPE = "decision"
DEFAULT_DECISION_ASSET_CLASS = "decision"
DEFAULT_DECISION_PROFILE_ID = "sports:nfl"
DEFAULT_DECISION_PORTABILITY_CLASSIFICATION = "cross_market_decision"
CANONICAL_DECISION_ROW_SNAPSHOT_GRAIN_ID = "dataset.sports.nfl.decision_snapshot.dataset_row_scope.v1"
DECISION_BATCH_KIND = "decision_population_summary"
DECISION_ROW_KIND = "decision_value"
DECISION_SUMMARY_ROW_KIND = "dataset_summary"
DECISION_USAGE_MODE = "backtest_readiness"
DECISION_ALLOWED_CLASSIFICATIONS = {"direct", "deterministic_derived"}
DECISION_ALLOWED_VALUE_TYPES = {"boolean", "float", "integer", "string", "timestamp"}
DECISION_ALLOWED_MISSINGNESS_POLICIES = {
    "required",
    "nullable",
    "unavailable",
    "not_applicable",
    "invalid_source",
    "unsupported_context",
}
DECISION_ALLOWED_ENTITY_SCOPES = {"decision_context"}
DECISION_ALLOWED_VALUES = {
    "BACKTEST_ELIGIBLE",
    "NO_TRADE",
    "EXCLUDED",
    "NEEDS_REVIEW",
}
DECISION_FORBIDDEN_INTENT_TOKENS = {
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
DEFAULT_DECISION_LINEAGE_REQUIREMENTS = (
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
    "source_signal_snapshot_ids_json",
    "source_signal_lineage_ids_json",
    "source_signal_certification_ids_json",
)
DEFAULT_DECISION_POINT_IN_TIME_CONSTRAINTS = (
    "inherit the certified historical dataset decision_cutoff_time",
    "reuse certified signal outputs only",
    "no raw or normalized source rereads",
    "no post-cutoff updates",
    "no bets, trades, staking, execution intent, or recommendations",
    "no target-event leakage",
)
DEFAULT_DECISION_CUTOFF_SEMANTICS = (
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


def _load_signal_context(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = _load_json_mapping(row.get("signal_context_json"))
    if not payload:
        return dict(row)
    result = dict(payload)
    for field in (
        "dataset_row_id",
        "decision_context_id",
        "signal_context_id",
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
        "feature_context_id",
    ):
        if field not in result or result.get(field) in (None, ""):
            result[field] = row.get(field)
    return result


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


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _first_non_empty(values: Sequence[Any], default: Any = "") -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return default


def _contains_forbidden_intent(text: str) -> bool:
    lowered = _normalize_text(text).lower()
    return any(token in lowered for token in DECISION_FORBIDDEN_INTENT_TOKENS)


def _value_to_columns(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {
            "decision_value_json": _as_json(value),
            "decision_value_text": None,
            "decision_value_number": None,
            "decision_value_boolean": int(value),
        }
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {
            "decision_value_json": _as_json(value),
            "decision_value_text": None,
            "decision_value_number": value,
            "decision_value_boolean": None,
        }
    if value is None:
        return {
            "decision_value_json": None,
            "decision_value_text": None,
            "decision_value_number": None,
            "decision_value_boolean": None,
        }
    return {
        "decision_value_json": _as_json(value),
        "decision_value_text": _normalize_text(value),
        "decision_value_number": None,
        "decision_value_boolean": None,
    }


@dataclass(slots=True, frozen=True)
class DecisionDefinition:
    decision_id: str
    decision_name: str
    decision_family: str
    market_vertical: str
    entity_scope: str
    dataset_grain_compatibility: str
    decision_version: str
    classification: str
    value_type: str
    unit: str
    nullable: bool
    missingness_policy: str
    source_signal_ids: tuple[str, ...]
    source_signal_summary_refs: tuple[str, ...]
    transformation_definition: str
    transformation_version: str
    cutoff_semantics: str
    point_in_time_constraints: tuple[str, ...]
    expected_range: str
    allowed_values: tuple[str, ...]
    decision_owner: str = DEFAULT_DECISION_OWNER
    decision_usage_mode: str = DECISION_USAGE_MODE
    lifecycle_state: str = "Decision Ready"
    certification_state: str = "definition_only"
    portability_classification: str = DEFAULT_DECISION_PORTABILITY_CLASSIFICATION
    lineage_requirements: tuple[str, ...] = DEFAULT_DECISION_LINEAGE_REQUIREMENTS

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _normalize_text(self.decision_id))
        object.__setattr__(self, "decision_name", _normalize_text(self.decision_name))
        object.__setattr__(self, "decision_family", _normalize_text(self.decision_family))
        object.__setattr__(self, "market_vertical", _normalize_text(self.market_vertical))
        object.__setattr__(self, "entity_scope", _normalize_text(self.entity_scope))
        object.__setattr__(self, "dataset_grain_compatibility", _normalize_text(self.dataset_grain_compatibility))
        object.__setattr__(self, "decision_version", _normalize_text(self.decision_version, DECISION_DEFINITION_VERSION))
        object.__setattr__(self, "classification", _normalize_text(self.classification))
        object.__setattr__(self, "value_type", _normalize_text(self.value_type))
        object.__setattr__(self, "unit", _normalize_text(self.unit))
        object.__setattr__(self, "missingness_policy", _normalize_text(self.missingness_policy))
        object.__setattr__(self, "source_signal_ids", tuple(_normalize_text(value) for value in self.source_signal_ids if _normalize_text(value)))
        object.__setattr__(self, "source_signal_summary_refs", tuple(_normalize_text(value) for value in self.source_signal_summary_refs if _normalize_text(value)))
        object.__setattr__(self, "transformation_definition", _normalize_text(self.transformation_definition))
        object.__setattr__(self, "transformation_version", _normalize_text(self.transformation_version))
        object.__setattr__(self, "cutoff_semantics", _normalize_text(self.cutoff_semantics))
        object.__setattr__(self, "point_in_time_constraints", tuple(_normalize_text(value) for value in self.point_in_time_constraints if _normalize_text(value)))
        object.__setattr__(self, "expected_range", _normalize_text(self.expected_range))
        object.__setattr__(self, "allowed_values", tuple(_normalize_text(value) for value in self.allowed_values if _normalize_text(value)))
        object.__setattr__(self, "decision_owner", _normalize_text(self.decision_owner, DEFAULT_DECISION_OWNER))
        object.__setattr__(self, "decision_usage_mode", _normalize_text(self.decision_usage_mode, DECISION_USAGE_MODE))
        object.__setattr__(self, "lifecycle_state", _normalize_text(self.lifecycle_state))
        object.__setattr__(self, "certification_state", _normalize_text(self.certification_state))
        object.__setattr__(self, "portability_classification", _normalize_text(self.portability_classification, DEFAULT_DECISION_PORTABILITY_CLASSIFICATION))
        object.__setattr__(self, "lineage_requirements", tuple(_normalize_text(value) for value in self.lineage_requirements if _normalize_text(value)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_name": self.decision_name,
            "decision_family": self.decision_family,
            "market_vertical": self.market_vertical,
            "entity_scope": self.entity_scope,
            "dataset_grain_compatibility": self.dataset_grain_compatibility,
            "decision_version": self.decision_version,
            "classification": self.classification,
            "value_type": self.value_type,
            "unit": self.unit,
            "nullable": self.nullable,
            "missingness_policy": self.missingness_policy,
            "source_signal_ids": list(self.source_signal_ids),
            "source_signal_summary_refs": list(self.source_signal_summary_refs),
            "transformation_definition": self.transformation_definition,
            "transformation_version": self.transformation_version,
            "cutoff_semantics": self.cutoff_semantics,
            "point_in_time_constraints": list(self.point_in_time_constraints),
            "expected_range": self.expected_range,
            "allowed_values": list(self.allowed_values),
            "decision_owner": self.decision_owner,
            "decision_usage_mode": self.decision_usage_mode,
            "lifecycle_state": self.lifecycle_state,
            "certification_state": self.certification_state,
            "portability_classification": self.portability_classification,
            "lineage_requirements": list(self.lineage_requirements),
        }


@dataclass(slots=True, frozen=True)
class DecisionSnapshotContext:
    dataset_id: str
    batch_id: str
    dataset_row_id: str
    decision_context_id: str
    source_signal_context_id: str
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
    source_signal_dataset_id: str
    source_signal_dataset_name: str
    source_signal_batch_id: str
    source_signal_version_id: str
    source_signal_certification_id: str
    source_signal_dataset_certification_id: str
    source_signal_population_summary_id: str
    source_signal_evidence_package_id: str
    source_signal_batch_lineage_id: str
    source_signal_row_count: int
    source_signal_snapshot_count: int
    source_signal_definition_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "batch_id": self.batch_id,
            "dataset_row_id": self.dataset_row_id,
            "decision_context_id": self.decision_context_id,
            "source_signal_context_id": self.source_signal_context_id,
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
            "source_signal_dataset_id": self.source_signal_dataset_id,
            "source_signal_dataset_name": self.source_signal_dataset_name,
            "source_signal_batch_id": self.source_signal_batch_id,
            "source_signal_version_id": self.source_signal_version_id,
            "source_signal_certification_id": self.source_signal_certification_id,
            "source_signal_dataset_certification_id": self.source_signal_dataset_certification_id,
            "source_signal_population_summary_id": self.source_signal_population_summary_id,
            "source_signal_evidence_package_id": self.source_signal_evidence_package_id,
            "source_signal_batch_lineage_id": self.source_signal_batch_lineage_id,
            "source_signal_row_count": self.source_signal_row_count,
            "source_signal_snapshot_count": self.source_signal_snapshot_count,
            "source_signal_definition_count": self.source_signal_definition_count,
        }


def _decision(
    decision_id: str,
    *,
    decision_name: str,
    decision_family: str,
    entity_scope: str,
    classification: str,
    value_type: str,
    unit: str,
    source_signal_ids: Sequence[str],
    transformation_definition: str,
    expected_range: str,
    source_signal_summary_refs: Sequence[str] = (),
    allowed_values: Sequence[str] = (),
    nullable: bool = False,
    portability_classification: str = DEFAULT_DECISION_PORTABILITY_CLASSIFICATION,
) -> DecisionDefinition:
    return DecisionDefinition(
        decision_id=decision_id,
        decision_name=decision_name,
        decision_family=decision_family,
        market_vertical="sports",
        entity_scope=entity_scope,
        dataset_grain_compatibility=CANONICAL_DECISION_ROW_SNAPSHOT_GRAIN_ID,
        decision_version=DECISION_DEFINITION_VERSION,
        classification=classification,
        value_type=value_type,
        unit=unit,
        nullable=nullable,
        missingness_policy="required" if not nullable else "nullable",
        source_signal_ids=tuple(source_signal_ids),
        source_signal_summary_refs=tuple(source_signal_summary_refs),
        transformation_definition=transformation_definition,
        transformation_version=DECISION_TRANSFORMATION_VERSION,
        cutoff_semantics=DEFAULT_DECISION_CUTOFF_SEMANTICS,
        point_in_time_constraints=DEFAULT_DECISION_POINT_IN_TIME_CONSTRAINTS,
        expected_range=expected_range,
        allowed_values=tuple(allowed_values),
        portability_classification=portability_classification,
    )


_DECISION_DEFINITIONS: tuple[DecisionDefinition, ...] = (
    _decision(
        "decision.sports.backtest_eligibility",
        decision_name="Backtest Eligibility",
        decision_family="backtest_readiness",
        entity_scope="decision_context",
        classification="deterministic_derived",
        value_type="string",
        unit="state",
        source_signal_ids=tuple(list_signal_definition_ids()),
        source_signal_summary_refs=("signal.sports.reusable_signals.summary",),
        transformation_definition=(
            "BACKTEST_ELIGIBLE when the certified signal context is complete, point-in-time safe, "
            "and aligned; otherwise EXCLUDED"
        ),
        expected_range="BACKTEST_ELIGIBLE, NO_TRADE, EXCLUDED, or NEEDS_REVIEW",
        allowed_values=("BACKTEST_ELIGIBLE", "NO_TRADE", "EXCLUDED", "NEEDS_REVIEW"),
    ),
)


def list_decision_definitions() -> list[dict[str, Any]]:
    return [definition.as_dict() for definition in _DECISION_DEFINITIONS]


def list_decision_definition_ids() -> list[str]:
    return [definition.decision_id for definition in _DECISION_DEFINITIONS]


def get_decision_definition(decision_id: str) -> dict[str, Any] | None:
    wanted = _normalize_text(decision_id)
    for definition in _DECISION_DEFINITIONS:
        if definition.decision_id == wanted:
            return definition.as_dict()
    return None


def validate_decision_registry(definitions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for definition in definitions:
        decision_id = _normalize_text(definition.get("decision_id"))
        decision_name = _normalize_text(definition.get("decision_name"))
        decision_family = _normalize_text(definition.get("decision_family"))
        classification = _normalize_text(definition.get("classification"))
        value_type = _normalize_text(definition.get("value_type"))
        unit = _normalize_text(definition.get("unit"))
        usage_mode = _normalize_text(definition.get("decision_usage_mode"), DECISION_USAGE_MODE)
        if decision_id in seen_ids:
            errors.append(f"duplicate_decision_id:{decision_id}")
        seen_ids.add(decision_id)
        if decision_name in seen_names:
            errors.append(f"duplicate_decision_name:{decision_name}")
        seen_names.add(decision_name)
        if classification not in DECISION_ALLOWED_CLASSIFICATIONS:
            errors.append(f"invalid_classification:{decision_id}")
        if value_type not in DECISION_ALLOWED_VALUE_TYPES:
            errors.append(f"invalid_value_type:{decision_id}")
        if not unit:
            errors.append(f"missing_unit:{decision_id}")
        if _normalize_text(definition.get("entity_scope")) not in DECISION_ALLOWED_ENTITY_SCOPES:
            errors.append(f"invalid_entity_scope:{decision_id}")
        if _normalize_text(definition.get("missingness_policy")) not in DECISION_ALLOWED_MISSINGNESS_POLICIES:
            errors.append(f"invalid_missingness_policy:{decision_id}")
        if usage_mode != DECISION_USAGE_MODE:
            errors.append(f"invalid_decision_usage_mode:{decision_id}")
        if any(token in decision_id.lower() for token in ("bet", "trade", "stake", "recommend", "order")):
            errors.append(f"forbidden_token_in_decision_id:{decision_id}")
        if _contains_forbidden_intent(decision_name):
            errors.append(f"forbidden_token_in_decision_name:{decision_id}")
        if decision_family == "":
            errors.append(f"missing_decision_family:{decision_id}")
    return {
        "ok": not errors,
        "status": "validated" if not errors else "rejected",
        "definition_count": len(definitions),
        "errors": errors,
    }


def summarize_decision_registry() -> dict[str, Any]:
    definitions = list_decision_definitions()
    return {
        "definition_count": len(definitions),
        "classification_counts": dict(Counter(definition["classification"] for definition in definitions)),
        "value_type_counts": dict(Counter(definition["value_type"] for definition in definitions)),
        "usage_mode_counts": dict(Counter(definition["decision_usage_mode"] for definition in definitions)),
        "families": sorted({definition["decision_family"] for definition in definitions}),
    }


def _required_row_fields() -> tuple[str, ...]:
    return (
        "snapshot_id",
        "dataset_id",
        "dataset_name",
        "owner",
        "sport",
        "decision_pack",
        "storage_location",
        "readiness",
        "update_frequency",
        "validation_state",
        "status",
        "batch_id",
        "snapshot_kind",
        "decision_pack_version",
        "dataset_row_id",
        "decision_context_id",
        "source_signal_context_id",
        "decision_snapshot_context_id",
        "event_id",
        "game_id",
        "season",
        "week",
        "home_team_id",
        "away_team_id",
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
        "decision_usage_mode",
        "decision_id",
        "decision_name",
        "decision_family",
        "decision_version",
        "classification",
        "value_type",
        "unit",
        "decision_owner",
        "entity_scope",
        "dataset_grain_compatibility",
        "transformation_version",
        "missingness_policy",
        "decision_value_json",
        "decision_value_text",
        "decision_missingness_state",
        "decision_definition_json",
        "decision_context_json",
        "decision_snapshot_grain_id",
        "decision_registry_schema_version",
        "decision_lineage_id",
        "decision_evidence_id",
        "source_feature_dataset_id",
        "source_feature_batch_id",
        "source_feature_population_summary_id",
        "source_math_dataset_id",
        "source_math_batch_id",
        "source_math_population_summary_id",
        "source_signal_dataset_id",
        "source_signal_batch_id",
        "source_signal_population_summary_id",
        "source_signal_ids_json",
        "source_signal_snapshot_ids_json",
        "source_signal_lineage_ids_json",
        "source_signal_certification_ids_json",
        "source_signal_dataset_certification_ids_json",
        "source_signal_alignment_certification_ids_json",
        "missing_required_assets_json",
        "evidence_package_id",
        "record_count",
        "decision_count",
        "decision_values_json",
        "summary_json",
        "payload_json",
        "schema_version",
        "created_at",
        "updated_at",
        "source",
        "provider",
        "market",
        "market_type",
        "asset_class",
        "lineage_id",
        "version_id",
        "quality_score",
    )


def validate_decision_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    base = validate_dataset_rows(rows, required_fields=_required_row_fields())
    missing_rows = list(base.get("missing_rows", []))
    missing_fields = [field for row in missing_rows for field in row.get("missing_fields", [])]
    duplicate_snapshot_ids: list[str] = []
    seen_snapshot_ids: set[str] = set()
    duplicate_decision_keys: list[str] = []
    seen_decision_keys: set[str] = set()
    usage_mode_errors: list[str] = []
    readiness_errors: list[str] = []
    intent_errors: list[str] = []
    for row in rows:
        snapshot_id = _normalize_text(row.get("snapshot_id"))
        if snapshot_id:
            if snapshot_id in seen_snapshot_ids and snapshot_id not in duplicate_snapshot_ids:
                duplicate_snapshot_ids.append(snapshot_id)
            seen_snapshot_ids.add(snapshot_id)
        decision_key = "|".join(
            [
                _normalize_text(row.get("dataset_row_id")),
                _normalize_text(row.get("decision_context_id")),
                _normalize_text(row.get("decision_id")),
                _normalize_text(row.get("decision_readiness_status")),
                _normalize_text(row.get("scheduled_kickoff_time")),
                _normalize_text(row.get("decision_cutoff_time")),
            ]
        )
        if decision_key in seen_decision_keys and decision_key not in duplicate_decision_keys:
            duplicate_decision_keys.append(decision_key)
        seen_decision_keys.add(decision_key)
        if _normalize_text(row.get("decision_usage_mode"), DECISION_USAGE_MODE) != DECISION_USAGE_MODE:
            usage_mode_errors.append(_normalize_text(row.get("decision_id")))
        if _normalize_text(row.get("decision_readiness_status")) not in DECISION_ALLOWED_VALUES:
            readiness_errors.append(_normalize_text(row.get("decision_id")))
        if _contains_forbidden_intent(_normalize_text(row.get("decision_id"))) or _contains_forbidden_intent(_normalize_text(row.get("decision_name"))):
            intent_errors.append(_normalize_text(row.get("decision_id")))

    required_fields_missing = list(dict.fromkeys(missing_fields))
    errors = list(
        dict.fromkeys(
            [
                *required_fields_missing,
                *[f"duplicate_snapshot_id:{value}" for value in duplicate_snapshot_ids],
                *[f"duplicate_decision_key:{value}" for value in duplicate_decision_keys],
                *[f"invalid_decision_usage_mode:{value}" for value in usage_mode_errors],
                *[f"invalid_decision_readiness_status:{value}" for value in readiness_errors],
                *[f"forbidden_intent:{value}" for value in intent_errors],
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
        "duplicate_decision_keys": duplicate_decision_keys,
        "errors": errors,
        "base_validation": base,
    }


def _decision_population_batch_signature(context: DecisionSnapshotContext) -> str:
    return _stable_id(
        "decision_context_signature",
        context.dataset_row_id,
        context.decision_context_id,
        context.source_signal_context_id,
        context.event_id,
        context.selection,
        context.book,
        context.scheduled_kickoff_time,
        context.decision_cutoff_time,
        context.source_signal_batch_id,
        context.source_signal_population_summary_id,
        context.source_signal_snapshot_count,
        context.source_signal_definition_count,
        context.source_feature_batch_id,
        context.source_feature_population_summary_id,
        context.source_math_batch_id,
        context.source_math_population_summary_id,
    )


def _decision_population_batch_id(
    dataset_id: str,
    source_signal_batch_id: str,
    *,
    contexts: Sequence[DecisionSnapshotContext],
) -> str:
    signatures = sorted(_decision_population_batch_signature(context) for context in contexts)
    return _stable_id(
        "decision_population_batch",
        dataset_id,
        source_signal_batch_id,
        DECISION_POPULATION_SCHEMA_VERSION,
        DECISION_DEFINITION_VERSION,
        DECISION_TRANSFORMATION_VERSION,
        _as_json(signatures),
    )


def build_decision_snapshot_context_id(context: Mapping[str, Any]) -> str:
    return _stable_id(
        "decision_snapshot_context",
        _normalize_text(context.get("dataset_row_id")),
        _normalize_text(context.get("decision_context_id")),
        _normalize_text(context.get("source_signal_context_id")),
        _normalize_text(context.get("event_id")),
        _normalize_text(context.get("selection")),
        _normalize_text(context.get("book")),
        _normalize_text(context.get("scheduled_kickoff_time")),
        _normalize_text(context.get("decision_cutoff_time")),
        _as_json(_load_json_list(context.get("source_signal_snapshot_ids_json"))),
    )


def build_decision_value_identity(
    definition: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    value: Any,
    source_signal_snapshot_ids: Sequence[str] = (),
) -> str:
    return _stable_id(
        "decision_value_identity",
        _normalize_text(definition.get("decision_id")),
        _normalize_text(context.get("dataset_row_id")),
        _normalize_text(context.get("decision_context_id")),
        _normalize_text(context.get("source_signal_context_id")),
        _normalize_text(context.get("scheduled_kickoff_time")),
        _normalize_text(context.get("decision_cutoff_time")),
        _normalize_text(context.get("decision_readiness_status")),
        _as_json(sorted(_normalize_text(value) for value in (value,))),
        _as_json(sorted(_normalize_text(item) for item in source_signal_snapshot_ids if _normalize_text(item))),
        _normalize_text(definition.get("decision_version"), DECISION_DEFINITION_VERSION),
        _normalize_text(definition.get("transformation_version"), DECISION_TRANSFORMATION_VERSION),
    )


def _collect_source_map(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for row in rows:
        payload = _load_json_mapping(row.get(key))
        for item_key, item_value in payload.items():
            if item_key not in values and item_value not in (None, ""):
                values[item_key] = item_value
    return values


def _collect_source_ids(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    collected: list[str] = []
    for row in rows:
        raw_value = row.get(key)
        if raw_value in (None, ""):
            continue
        values = _load_json_list(raw_value)
        if not values:
            values = [raw_value]
        for value in values:
            text = _normalize_text(value)
            if text and text not in collected:
                collected.append(text)
    return collected


def _signal_row_values(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for row in rows:
        signal_id = _normalize_text(row.get("signal_id"))
        if signal_id and signal_id not in values:
            values[signal_id] = _load_json_value(row.get("signal_value_json"), row.get("signal_value_text"), row.get("signal_value_number"), row.get("signal_value_boolean"))
    return values


def _load_json_value(value_json: Any, value_text: Any, value_number: Any, value_boolean: Any) -> Any:
    if value_json not in (None, ""):
        try:
            return json.loads(str(value_json))
        except json.JSONDecodeError:
            pass
    if value_boolean not in (None, ""):
        return bool(_normalize_int(value_boolean, 0))
    if value_number not in (None, ""):
        return _normalize_float(value_number, 0.0)
    if value_text not in (None, ""):
        return _normalize_text(value_text)
    return None


def build_decision_snapshot_context(
    *,
    dataset_id: str,
    batch_id: str,
    summary_row: Mapping[str, Any],
    signal_rows: Sequence[Mapping[str, Any]],
    context_rows: Sequence[Mapping[str, Any]],
) -> DecisionSnapshotContext:
    if not context_rows:
        raise ValueError("context_rows are required")
    representative_row = dict(context_rows[0])
    representative = _load_signal_context(representative_row)
    source_feature_dataset_id = _normalize_text(representative.get("source_feature_dataset_id"), DEFAULT_SIGNAL_DATASET_ID)
    source_feature_dataset_name = _normalize_text(representative.get("source_feature_dataset_name"), "nfl_feature_snapshots")
    source_feature_batch_id = _normalize_text(representative.get("source_feature_batch_id"))
    source_feature_version_id = _normalize_text(representative.get("source_feature_version_id"), SIGNAL_TRANSFORMATION_VERSION)
    source_feature_certification_id = _normalize_text(representative.get("source_feature_certification_id"))
    source_feature_dataset_certification_id = _normalize_text(representative.get("source_feature_dataset_certification_id"))
    source_feature_population_summary_id = _normalize_text(representative.get("source_feature_population_summary_id"))
    source_feature_evidence_package_id = _normalize_text(representative.get("source_feature_evidence_package_id"))
    source_feature_batch_lineage_id = _normalize_text(representative.get("source_feature_batch_lineage_id"))
    source_feature_row_count = _normalize_int(representative.get("source_feature_row_count"), 0)
    source_feature_snapshot_count = _normalize_int(representative.get("source_feature_snapshot_count"), 0)
    source_feature_definition_count = _normalize_int(representative.get("source_feature_definition_count"), 0)
    source_math_dataset_id = _normalize_text(representative.get("source_math_dataset_id"), DEFAULT_SIGNAL_DATASET_ID)
    source_math_dataset_name = _normalize_text(representative.get("source_math_dataset_name"), "nfl_math_engine_snapshots")
    source_math_batch_id = _normalize_text(representative.get("source_math_batch_id"))
    source_math_version_id = _normalize_text(representative.get("source_math_version_id"), SIGNAL_TRANSFORMATION_VERSION)
    source_math_certification_id = _normalize_text(representative.get("source_math_certification_id"))
    source_math_dataset_certification_id = _normalize_text(representative.get("source_math_dataset_certification_id"))
    source_math_population_summary_id = _normalize_text(representative.get("source_math_population_summary_id"))
    source_math_evidence_package_id = _normalize_text(representative.get("source_math_evidence_package_id"))
    source_math_batch_lineage_id = _normalize_text(representative.get("source_math_batch_lineage_id"))
    source_math_row_count = _normalize_int(representative.get("source_math_row_count"), 0)
    source_math_snapshot_count = _normalize_int(representative.get("source_math_snapshot_count"), 0)
    source_math_definition_count = _normalize_int(representative.get("source_math_definition_count"), 0)
    source_signal_dataset_id = _normalize_text(summary_row.get("dataset_id"), DEFAULT_SIGNAL_DATASET_ID)
    source_signal_dataset_name = _normalize_text(summary_row.get("dataset_name"), "nfl_signal_snapshots")
    source_signal_batch_id = _normalize_text(summary_row.get("batch_id"))
    source_signal_version_id = _normalize_text(summary_row.get("version_id"), SIGNAL_TRANSFORMATION_VERSION)
    source_signal_certification_id = _normalize_text(summary_row.get("certification_id"))
    source_signal_dataset_certification_id = _normalize_text(summary_row.get("dataset_certification_id"))
    source_signal_population_summary_id = _normalize_text(summary_row.get("snapshot_id"))
    source_signal_evidence_package_id = _normalize_text(summary_row.get("evidence_package_id"))
    source_signal_batch_lineage_id = _normalize_text(summary_row.get("lineage_id"))
    source_signal_row_count = _normalize_int(summary_row.get("signal_count"), len(signal_rows))
    source_signal_snapshot_count = _normalize_int(summary_row.get("signal_count"), len(signal_rows))
    source_signal_definition_count = len(list_signal_definition_ids())
    source_signal_context_id = _normalize_text(representative.get("signal_context_id") or representative_row.get("signal_context_id"))
    target_team_id = _resolve_target_team_id(representative)
    opponent_team_id = _resolve_opponent_team_id(
        representative,
        target_team_id=target_team_id,
    )
    return DecisionSnapshotContext(
        dataset_id=dataset_id,
        batch_id=batch_id,
        dataset_row_id=_normalize_text(representative.get("dataset_row_id")),
        decision_context_id=_normalize_text(representative.get("decision_context_id")),
        source_signal_context_id=source_signal_context_id,
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
        decision_readiness_status=_normalize_text(representative.get("decision_readiness_status"), "BACKTEST_ELIGIBLE"),
        source_feature_dataset_id=source_feature_dataset_id,
        source_feature_dataset_name=source_feature_dataset_name,
        source_feature_batch_id=source_feature_batch_id,
        source_feature_version_id=source_feature_version_id,
        source_feature_certification_id=source_feature_certification_id,
        source_feature_dataset_certification_id=source_feature_dataset_certification_id,
        source_feature_population_summary_id=source_feature_population_summary_id,
        source_feature_evidence_package_id=source_feature_evidence_package_id,
        source_feature_batch_lineage_id=source_feature_batch_lineage_id,
        source_feature_row_count=source_feature_row_count,
        source_feature_snapshot_count=source_feature_snapshot_count,
        source_feature_definition_count=source_feature_definition_count,
        source_math_dataset_id=source_math_dataset_id,
        source_math_dataset_name=source_math_dataset_name,
        source_math_batch_id=source_math_batch_id,
        source_math_version_id=source_math_version_id,
        source_math_certification_id=source_math_certification_id,
        source_math_dataset_certification_id=source_math_dataset_certification_id,
        source_math_population_summary_id=source_math_population_summary_id,
        source_math_evidence_package_id=source_math_evidence_package_id,
        source_math_batch_lineage_id=source_math_batch_lineage_id,
        source_math_row_count=source_math_row_count,
        source_math_snapshot_count=source_math_snapshot_count,
        source_math_definition_count=source_math_definition_count,
        source_signal_dataset_id=source_signal_dataset_id,
        source_signal_dataset_name=source_signal_dataset_name,
        source_signal_batch_id=source_signal_batch_id,
        source_signal_version_id=source_signal_version_id,
        source_signal_certification_id=source_signal_certification_id,
        source_signal_dataset_certification_id=source_signal_dataset_certification_id,
        source_signal_population_summary_id=source_signal_population_summary_id,
        source_signal_evidence_package_id=source_signal_evidence_package_id,
        source_signal_batch_lineage_id=source_signal_batch_lineage_id,
        source_signal_row_count=source_signal_row_count,
        source_signal_snapshot_count=source_signal_snapshot_count,
        source_signal_definition_count=source_signal_definition_count,
    )


def _decision_row_record_status(decision_readiness_status: str) -> tuple[str, str, str, float]:
    readiness_state = _normalize_text(decision_readiness_status, "EXCLUDED")
    status = "certified"
    readiness = "backtest_ready" if readiness_state == "BACKTEST_ELIGIBLE" else "blocked"
    validation_state = "validated"
    quality_score = 1.0 if readiness_state == "BACKTEST_ELIGIBLE" else 0.0
    return status, readiness, validation_state, quality_score


def _decision_source_maps(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "source_feature_ids": _collect_source_ids(rows, "source_feature_ids_json"),
        "source_feature_snapshot_ids": _collect_source_ids(rows, "source_feature_snapshot_ids_json"),
        "source_feature_lineage_ids": _collect_source_ids(rows, "source_feature_lineage_ids_json"),
        "source_feature_certification_ids": _collect_source_ids(rows, "source_feature_certification_ids_json"),
        "source_feature_dataset_certification_ids": _collect_source_ids(rows, "source_feature_dataset_certification_ids_json"),
        "source_feature_alignment_certification_ids": _collect_source_ids(rows, "source_feature_alignment_certification_ids_json"),
        "source_feature_missingness": _collect_source_map(rows, "source_feature_missingness_json"),
        "source_feature_freshness": _collect_source_map(rows, "source_feature_freshness_json"),
        "source_feature_value_types": _collect_source_map(rows, "source_feature_value_types_json"),
        "source_feature_values": _collect_source_map(rows, "source_feature_values_json"),
        "source_math_output_ids": _collect_source_ids(rows, "source_math_output_ids_json"),
        "source_math_snapshot_ids": _collect_source_ids(rows, "source_math_snapshot_ids_json"),
        "source_math_lineage_ids": _collect_source_ids(rows, "source_math_lineage_ids_json"),
        "source_math_certification_ids": _collect_source_ids(rows, "source_math_certification_ids_json"),
        "source_math_dataset_certification_ids": _collect_source_ids(rows, "source_math_dataset_certification_ids_json"),
        "source_math_missingness": _collect_source_map(rows, "source_math_missingness_json"),
        "source_math_freshness": _collect_source_map(rows, "source_math_freshness_json"),
        "source_math_value_types": _collect_source_map(rows, "source_math_value_types_json"),
        "source_math_values": _collect_source_map(rows, "source_math_values_json"),
        "source_signal_ids": _collect_source_ids(rows, "signal_id"),
        "source_signal_snapshot_ids": _collect_source_ids(rows, "snapshot_id"),
        "source_signal_lineage_ids": _collect_source_ids(rows, "lineage_id"),
        "source_signal_certification_ids": _collect_source_ids(rows, "certification_id"),
        "source_signal_dataset_certification_ids": _collect_source_ids(rows, "dataset_certification_id"),
        "source_signal_alignment_certification_ids": _collect_source_ids(rows, "alignment_certification_id"),
        "source_signal_missingness": { _normalize_text(row.get("signal_id")): _normalize_text(row.get("signal_missingness_state")) for row in rows if _normalize_text(row.get("signal_id")) },
        "source_signal_freshness": { _normalize_text(row.get("signal_id")): _normalize_text(row.get("signal_freshness_state")) for row in rows if _normalize_text(row.get("signal_id")) },
        "source_signal_value_types": { _normalize_text(row.get("signal_id")): _normalize_text(row.get("value_type")) for row in rows if _normalize_text(row.get("signal_id")) },
        "source_signal_values": { _normalize_text(row.get("signal_id")): _load_json_value(row.get("signal_value_json"), row.get("signal_value_text"), row.get("signal_value_number"), row.get("signal_value_boolean")) for row in rows if _normalize_text(row.get("signal_id")) },
    }


def _decision_alignment_batch_id(row: Mapping[str, Any], fallback_batch_id: str) -> str:
    return _normalize_text(row.get("decision_snapshot_context_id") or row.get("snapshot_id") or fallback_batch_id)


def _decision_row_payload_and_values(
    *,
    definition: DecisionDefinition,
    context: DecisionSnapshotContext,
    context_rows: Sequence[Mapping[str, Any]],
    source_signal_snapshot: Mapping[str, Any],
    source_maps: Mapping[str, Any],
    storage_location: str,
    created_at: str,
    decision_batch_id: str,
    decision_version_id: str,
    decision_evidence_package_id: str,
    decision_row_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    signal_snapshot_ids = list(source_maps["source_signal_snapshot_ids"])
    decision_readiness_status = _normalize_text(context.decision_readiness_status, "BACKTEST_ELIGIBLE")
    if not signal_snapshot_ids:
        decision_readiness_status = "EXCLUDED"
    status, readiness, validation_state, quality_score = _decision_row_record_status(decision_readiness_status)
    decision_snapshot_context_id = build_decision_snapshot_context_id(
        {
            **context.as_dict(),
            "source_signal_snapshot_ids_json": _as_json(signal_snapshot_ids),
            "decision_readiness_status": decision_readiness_status,
        }
    )
    value = decision_readiness_status if decision_readiness_status in DECISION_ALLOWED_VALUES else "EXCLUDED"
    decision_snapshot_id = build_decision_value_identity(
        definition.as_dict(),
        {
            **context.as_dict(),
            "source_signal_context_id": context.source_signal_context_id,
            "decision_snapshot_context_id": decision_snapshot_context_id,
            "decision_readiness_status": decision_readiness_status,
        },
        value=value,
        source_signal_snapshot_ids=signal_snapshot_ids,
    )
    decision_lineage_id = _stable_id(
        "decision_lineage",
        decision_snapshot_id,
        decision_batch_id,
        definition.decision_id,
        _as_json(source_maps["source_signal_snapshot_ids"]),
        _as_json(source_maps["source_signal_lineage_ids"]),
        _as_json(source_maps["source_signal_certification_ids"]),
        _as_json(source_maps["source_feature_snapshot_ids"]),
        _as_json(source_maps["source_math_snapshot_ids"]),
    )
    decision_evidence_id = _stable_id(
        "decision_evidence",
        decision_snapshot_id,
        decision_batch_id,
        definition.decision_id,
        _as_json(source_maps["source_signal_values"]),
        _as_json(source_maps["source_signal_snapshot_ids"]),
        _as_json(value),
        decision_readiness_status,
    )
    representative_signal_context = _load_signal_context(context_rows[0])
    target_team_id = _resolve_target_team_id(representative_signal_context) or context.target_team_id
    opponent_team_id = _resolve_opponent_team_id(
        representative_signal_context,
        target_team_id=target_team_id,
    ) or context.opponent_team_id
    home_team = _normalize_text(representative_signal_context.get("home_team") or context.home_team)
    away_team = _normalize_text(representative_signal_context.get("away_team") or context.away_team)
    decision_context_json = {
        **context.as_dict(),
        "decision_snapshot_context_id": decision_snapshot_context_id,
        "decision_value": value,
        "source_signal_snapshot_ids": signal_snapshot_ids,
        "source_signal_lineage_ids": list(source_maps["source_signal_lineage_ids"]),
        "source_signal_certification_ids": list(source_maps["source_signal_certification_ids"]),
        "source_signal_dataset_certification_ids": list(source_maps["source_signal_dataset_certification_ids"]),
        "source_signal_values": dict(source_maps["source_signal_values"]),
        "source_feature_values": dict(source_maps["source_feature_values"]),
        "source_math_values": dict(source_maps["source_math_values"]),
        "source_signal_context": representative_signal_context,
    }
    decision_definition_json = definition.as_dict()
    payload = {
        "snapshot_id": decision_snapshot_id,
        "decision_id": definition.decision_id,
        "decision_name": definition.decision_name,
        "decision_family": definition.decision_family,
        "decision_version": definition.decision_version,
        "classification": definition.classification,
        "value_type": definition.value_type,
        "unit": definition.unit,
        "decision_owner": definition.decision_owner,
        "entity_scope": definition.entity_scope,
        "dataset_grain_compatibility": definition.dataset_grain_compatibility,
        "transformation_version": definition.transformation_version,
        "missingness_policy": definition.missingness_policy,
        "decision_snapshot_context_id": decision_snapshot_context_id,
        "decision_value": value,
        "decision_readiness_status": decision_readiness_status,
        "decision_definition": decision_definition_json,
        "decision_context": decision_context_json,
        "source_maps": {
            "source_feature_ids": list(source_maps["source_feature_ids"]),
            "source_feature_snapshot_ids": list(source_maps["source_feature_snapshot_ids"]),
            "source_feature_lineage_ids": list(source_maps["source_feature_lineage_ids"]),
            "source_feature_certification_ids": list(source_maps["source_feature_certification_ids"]),
            "source_feature_dataset_certification_ids": list(source_maps["source_feature_dataset_certification_ids"]),
            "source_feature_alignment_certification_ids": list(source_maps["source_feature_alignment_certification_ids"]),
            "source_feature_missingness": dict(source_maps["source_feature_missingness"]),
            "source_feature_freshness": dict(source_maps["source_feature_freshness"]),
            "source_feature_value_types": dict(source_maps["source_feature_value_types"]),
            "source_feature_values": dict(source_maps["source_feature_values"]),
            "source_math_output_ids": list(source_maps["source_math_output_ids"]),
            "source_math_snapshot_ids": list(source_maps["source_math_snapshot_ids"]),
            "source_math_lineage_ids": list(source_maps["source_math_lineage_ids"]),
            "source_math_certification_ids": list(source_maps["source_math_certification_ids"]),
            "source_math_dataset_certification_ids": list(source_maps["source_math_dataset_certification_ids"]),
            "source_math_missingness": dict(source_maps["source_math_missingness"]),
            "source_math_freshness": dict(source_maps["source_math_freshness"]),
            "source_math_value_types": dict(source_maps["source_math_value_types"]),
            "source_math_values": dict(source_maps["source_math_values"]),
            "source_signal_ids": list(source_maps["source_signal_ids"]),
            "source_signal_snapshot_ids": list(source_maps["source_signal_snapshot_ids"]),
            "source_signal_lineage_ids": list(source_maps["source_signal_lineage_ids"]),
            "source_signal_certification_ids": list(source_maps["source_signal_certification_ids"]),
            "source_signal_dataset_certification_ids": list(source_maps["source_signal_dataset_certification_ids"]),
            "source_signal_alignment_certification_ids": list(source_maps["source_signal_alignment_certification_ids"]),
            "source_signal_missingness": dict(source_maps["source_signal_missingness"]),
            "source_signal_freshness": dict(source_maps["source_signal_freshness"]),
            "source_signal_value_types": dict(source_maps["source_signal_value_types"]),
            "source_signal_values": dict(source_maps["source_signal_values"]),
        },
    }
    row = {
        "snapshot_id": decision_snapshot_id,
        "dataset_id": context.dataset_id,
        "dataset_name": DEFAULT_DECISION_DATASET_NAME,
        "owner": DEFAULT_DECISION_OWNER,
        "sport": "football",
        "decision_pack": DEFAULT_DECISION_RESEARCH_ASSET_ID,
        "storage_location": storage_location,
        "readiness": readiness,
        "update_frequency": "manual",
        "validation_state": validation_state,
        "status": status,
        "batch_id": decision_batch_id,
        "snapshot_kind": DECISION_ROW_KIND,
        "decision_pack_version": DECISION_DEFINITION_VERSION,
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
        "source_signal_context_id": context.source_signal_context_id,
        "decision_snapshot_context_id": decision_snapshot_context_id,
        "event_id": context.event_id,
        "game_id": _normalize_text(representative_signal_context.get("game_id") or context.game_id or context.event_id),
        "season": context.season,
        "week": context.week,
        "home_team_id": context.home_team_id,
        "away_team_id": context.away_team_id,
        "team_side": context.team_side,
        "target_team_id": target_team_id,
        "opponent_team_id": opponent_team_id,
        "home_team": home_team,
        "away_team": away_team,
        "market_type": context.market_type,
        "selection": context.selection,
        "book": context.book,
        "scheduled_kickoff_time": context.scheduled_kickoff_time,
        "decision_cutoff_time": context.decision_cutoff_time,
        "cutoff_policy_version": context.cutoff_policy_version,
        "point_in_time_status": context.point_in_time_status,
        "predictor_outcome_separation_status": context.predictor_outcome_separation_status,
        "decision_readiness_status": decision_readiness_status,
        "decision_usage_mode": DECISION_USAGE_MODE,
        "decision_id": definition.decision_id,
        "decision_name": definition.decision_name,
        "decision_family": definition.decision_family,
        "decision_version": definition.decision_version,
        "classification": definition.classification,
        "value_type": definition.value_type,
        "unit": definition.unit,
        "decision_owner": definition.decision_owner,
        "entity_scope": definition.entity_scope,
        "dataset_grain_compatibility": definition.dataset_grain_compatibility,
        "transformation_version": definition.transformation_version,
        "missingness_policy": definition.missingness_policy,
        **_value_to_columns(value),
        "decision_missingness_state": "present",
        "decision_missingness_reason": "",
        "decision_definition_json": _as_json(decision_definition_json),
        "decision_context_json": _as_json(decision_context_json),
        "decision_snapshot_grain_id": CANONICAL_DECISION_ROW_SNAPSHOT_GRAIN_ID,
        "decision_registry_schema_version": DECISION_POPULATION_SCHEMA_VERSION,
        "decision_lineage_id": decision_lineage_id,
        "decision_evidence_id": decision_evidence_id,
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
        "source_signal_context_id": context.source_signal_context_id,
        "source_signal_dataset_id": context.source_signal_dataset_id,
        "source_signal_dataset_name": context.source_signal_dataset_name,
        "source_signal_batch_id": context.source_signal_batch_id,
        "source_signal_version_id": context.source_signal_version_id,
        "source_signal_certification_id": context.source_signal_certification_id,
        "source_signal_dataset_certification_id": context.source_signal_dataset_certification_id,
        "source_signal_population_summary_id": context.source_signal_population_summary_id,
        "source_signal_evidence_package_id": context.source_signal_evidence_package_id,
        "source_signal_batch_lineage_id": context.source_signal_batch_lineage_id,
        "source_signal_row_count": context.source_signal_row_count,
        "source_signal_snapshot_count": context.source_signal_snapshot_count,
        "source_signal_definition_count": context.source_signal_definition_count,
        "source_signal_ids_json": _as_json(source_maps["source_signal_ids"]),
        "source_signal_snapshot_ids_json": _as_json(source_maps["source_signal_snapshot_ids"]),
        "source_signal_lineage_ids_json": _as_json(source_maps["source_signal_lineage_ids"]),
        "source_signal_certification_ids_json": _as_json(source_maps["source_signal_certification_ids"]),
        "source_signal_dataset_certification_ids_json": _as_json(source_maps["source_signal_dataset_certification_ids"]),
        "source_signal_alignment_certification_ids_json": _as_json(source_maps["source_signal_alignment_certification_ids"]),
        "source_signal_missingness_json": _as_json(source_maps["source_signal_missingness"]),
        "source_signal_freshness_json": _as_json(source_maps["source_signal_freshness"]),
        "source_signal_value_types_json": _as_json(source_maps["source_signal_value_types"]),
        "source_signal_values_json": _as_json(source_maps["source_signal_values"]),
        "missing_required_assets_json": _as_json([]),
        "evidence_package_id": decision_evidence_package_id,
        "record_count": 1,
        "decision_count": 1,
        "decision_values_json": _as_json(
            {
                "decision_id": definition.decision_id,
                "decision_name": definition.decision_name,
                "decision_value": value,
                "decision_readiness_status": decision_readiness_status,
                "dataset_row_id": context.dataset_row_id,
                "decision_context_id": context.decision_context_id,
                "decision_snapshot_context_id": decision_snapshot_context_id,
            }
        ),
        "summary_json": _as_json(
            {
                "decision_id": definition.decision_id,
                "decision_family": definition.decision_family,
                "decision_value": value,
                "decision_readiness_status": decision_readiness_status,
                "dataset_row_id": context.dataset_row_id,
                "decision_context_id": context.decision_context_id,
                "decision_snapshot_context_id": decision_snapshot_context_id,
            }
        ),
        "payload_json": _as_json(payload),
        "schema_version": DECISION_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_DECISION_SOURCE_NAME,
        "provider": DEFAULT_DECISION_PROVIDER,
        "market": DEFAULT_DECISION_MARKET,
        "market_type": DEFAULT_DECISION_MARKET_TYPE,
        "asset_class": DEFAULT_DECISION_ASSET_CLASS,
        "lineage_id": decision_lineage_id,
        "version_id": decision_version_id,
        "quality_score": quality_score,
    }
    lineage_edge = create_lineage_record(
        provider_id="decision_row_population_runtime",
        provider_type="decision_row_population",
        payload_schema_version=DECISION_POPULATION_SCHEMA_VERSION,
        snapshot_id=decision_snapshot_id,
        source_type="signal_snapshot",
        schema_version=DECISION_POPULATION_SCHEMA_VERSION,
        lineage_id=decision_lineage_id,
        dataset_id=context.dataset_id,
        dataset_name=DEFAULT_DECISION_DATASET_NAME,
        source_record_id=_normalize_text(context.source_signal_population_summary_id or context.source_signal_batch_id),
        target_record_id=decision_snapshot_id,
        source_stage="signal_snapshot",
        target_stage="decision_row",
        transformation="populate_decision_row",
    )
    lineage_record = {
        "lineage_edge_id": decision_lineage_id,
        "dataset_id": context.dataset_id,
        "dataset_name": DEFAULT_DECISION_DATASET_NAME,
        "owner": DEFAULT_DECISION_OWNER,
        "sport": "football",
        "feature_pack": DEFAULT_DECISION_RESEARCH_ASSET_ID,
        "storage_location": storage_location,
        "readiness": readiness,
        "update_frequency": "manual",
        "validation_state": validation_state,
        "status": status,
        "schema_version": DECISION_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_DECISION_SOURCE_NAME,
        "provider": DEFAULT_DECISION_PROVIDER,
        "market": DEFAULT_DECISION_MARKET,
        "market_type": DEFAULT_DECISION_MARKET_TYPE,
        "asset_class": DEFAULT_DECISION_ASSET_CLASS,
        "snapshot_id": decision_snapshot_id,
        "lineage_id": decision_lineage_id,
        "version_id": decision_version_id,
        "quality_score": quality_score,
        "source_stage": "signal_snapshot",
        "source_id": _normalize_text(context.source_signal_population_summary_id or context.source_signal_batch_id),
        "target_stage": "decision_row",
        "target_id": decision_snapshot_id,
        "transformation": "populate_decision_row",
        "step_index": decision_row_index,
        "payload_json": _as_json(lineage_edge),
    }
    return row, lineage_record


def _decision_summary_row(
    *,
    context_rows: Sequence[Mapping[str, Any]],
    source_signal_snapshot: Mapping[str, Any],
    context: DecisionSnapshotContext,
    batch_id: str,
    storage_location: str,
    created_at: str,
    decision_rows: Sequence[Mapping[str, Any]],
    lineage_edges: Sequence[Mapping[str, Any]],
    decision_definition_count: int,
) -> dict[str, Any]:
    decision_value_counts = Counter(_normalize_text(row.get("decision_readiness_status")) for row in decision_rows)
    summary_value = len(decision_rows)
    source_maps = _decision_source_maps(context_rows)
    summary_snapshot_id = _stable_id(
        "decision_population_summary_snapshot",
        DEFAULT_DECISION_DATASET_ID,
        batch_id,
        DECISION_TRANSFORMATION_VERSION,
    )
    summary_context = {
        **context.as_dict(),
        "decision_snapshot_context_id": summary_snapshot_id,
        "decision_readiness_status": "BACKTEST_ELIGIBLE" if decision_value_counts.get("BACKTEST_ELIGIBLE", 0) == len(decision_rows) else "EXCLUDED",
        "source_signal_snapshot_ids_json": _as_json(source_maps["source_signal_snapshot_ids"]),
    }
    summary_definition = _decision(
        f"{DEFAULT_DECISION_RESEARCH_ASSET_ID}.summary",
        decision_name="Reusable Decision Rows Summary",
        decision_family="summary",
        entity_scope="decision_context",
        classification="direct",
        value_type="integer",
        unit="rows",
        source_signal_ids=(),
        source_signal_summary_refs=("signal.sports.reusable_signals.summary",),
        transformation_definition="summary row representing the reusable decision batch",
        expected_range="row count summary",
    )
    summary_value = _normalize_int(summary_value, 0)
    value_columns = _value_to_columns(summary_value)
    summary_row = {
        "snapshot_id": summary_snapshot_id,
        "dataset_id": DEFAULT_DECISION_DATASET_ID,
        "dataset_name": DEFAULT_DECISION_DATASET_NAME,
        "owner": DEFAULT_DECISION_OWNER,
        "sport": "football",
        "decision_pack": DEFAULT_DECISION_RESEARCH_ASSET_ID,
        "storage_location": storage_location,
        "readiness": "backtest_ready" if decision_value_counts.get("BACKTEST_ELIGIBLE", 0) == len(decision_rows) else "blocked",
        "update_frequency": "manual",
        "validation_state": "validated",
        "status": "certified",
        "batch_id": batch_id,
        "snapshot_kind": DECISION_BATCH_KIND,
        "decision_pack_version": DECISION_DEFINITION_VERSION,
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
        "source_signal_context_id": context.source_signal_context_id,
        "decision_snapshot_context_id": summary_snapshot_id,
        "event_id": context.event_id,
        "game_id": context.game_id or _normalize_text(context.event_id),
        "season": context.season,
        "week": context.week,
        "home_team_id": context.home_team_id,
        "away_team_id": context.away_team_id,
        "team_side": context.team_side,
        "target_team_id": context.target_team_id,
        "opponent_team_id": context.opponent_team_id,
        "home_team": context.home_team,
        "away_team": context.away_team,
        "market_type": context.market_type,
        "selection": context.selection,
        "book": context.book,
        "scheduled_kickoff_time": context.scheduled_kickoff_time,
        "decision_cutoff_time": context.decision_cutoff_time,
        "cutoff_policy_version": context.cutoff_policy_version,
        "point_in_time_status": context.point_in_time_status,
        "predictor_outcome_separation_status": context.predictor_outcome_separation_status,
        "decision_readiness_status": "BACKTEST_ELIGIBLE" if decision_value_counts.get("BACKTEST_ELIGIBLE", 0) == len(decision_rows) else "EXCLUDED",
        "decision_usage_mode": DECISION_USAGE_MODE,
        "decision_id": summary_definition.decision_id,
        "decision_name": summary_definition.decision_name,
        "decision_family": summary_definition.decision_family,
        "decision_version": summary_definition.decision_version,
        "classification": summary_definition.classification,
        "value_type": summary_definition.value_type,
        "unit": summary_definition.unit,
        "decision_owner": summary_definition.decision_owner,
        "entity_scope": summary_definition.entity_scope,
        "dataset_grain_compatibility": summary_definition.dataset_grain_compatibility,
        "transformation_version": summary_definition.transformation_version,
        "missingness_policy": summary_definition.missingness_policy,
        **value_columns,
        "decision_missingness_state": "present",
        "decision_missingness_reason": "",
        "decision_definition_json": _as_json(summary_definition.as_dict()),
        "decision_context_json": _as_json(summary_context),
        "decision_snapshot_grain_id": CANONICAL_DECISION_ROW_SNAPSHOT_GRAIN_ID,
        "decision_registry_schema_version": DECISION_POPULATION_SCHEMA_VERSION,
        "decision_lineage_id": _stable_id("decision_summary_lineage", batch_id, summary_snapshot_id, summary_value),
        "decision_evidence_id": _stable_id("decision_summary_evidence", batch_id, summary_snapshot_id, summary_value),
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
        "source_signal_context_id": context.source_signal_context_id,
        "source_signal_dataset_id": context.source_signal_dataset_id,
        "source_signal_dataset_name": context.source_signal_dataset_name,
        "source_signal_batch_id": context.source_signal_batch_id,
        "source_signal_version_id": context.source_signal_version_id,
        "source_signal_certification_id": context.source_signal_certification_id,
        "source_signal_dataset_certification_id": context.source_signal_dataset_certification_id,
        "source_signal_population_summary_id": context.source_signal_population_summary_id,
        "source_signal_evidence_package_id": context.source_signal_evidence_package_id,
        "source_signal_batch_lineage_id": context.source_signal_batch_lineage_id,
        "source_signal_row_count": context.source_signal_row_count,
        "source_signal_snapshot_count": context.source_signal_snapshot_count,
        "source_signal_definition_count": context.source_signal_definition_count,
        "source_signal_ids_json": _as_json(source_maps["source_signal_ids"]),
        "source_signal_snapshot_ids_json": _as_json(source_maps["source_signal_snapshot_ids"]),
        "source_signal_lineage_ids_json": _as_json(source_maps["source_signal_lineage_ids"]),
        "source_signal_certification_ids_json": _as_json(source_maps["source_signal_certification_ids"]),
        "source_signal_dataset_certification_ids_json": _as_json(source_maps["source_signal_dataset_certification_ids"]),
        "source_signal_alignment_certification_ids_json": _as_json(source_maps["source_signal_alignment_certification_ids"]),
        "source_signal_missingness_json": _as_json(source_maps["source_signal_missingness"]),
        "source_signal_freshness_json": _as_json(source_maps["source_signal_freshness"]),
        "source_signal_value_types_json": _as_json(source_maps["source_signal_value_types"]),
        "source_signal_values_json": _as_json(source_maps["source_signal_values"]),
        "missing_required_assets_json": _as_json([]),
        "evidence_package_id": _stable_id("decision_evidence_package", context.source_signal_evidence_package_id, batch_id, DECISION_TRANSFORMATION_VERSION),
        "record_count": len(decision_rows),
        "decision_count": len(decision_rows),
        "decision_values_json": _as_json(
            {
                "decision_row_count": len(decision_rows),
                "decision_definition_count": decision_definition_count,
                "decision_context_count": len({row.get("decision_context_id") for row in decision_rows}),
                "decision_ids": [row.get("decision_id") for row in decision_rows],
                "decision_values": [row.get("decision_readiness_status") for row in decision_rows],
                "decision_value_counts": dict(decision_value_counts),
            }
        ),
        "summary_json": _as_json(
            {
                "batch_id": batch_id,
                "decision_row_count": len(decision_rows),
                "decision_definition_count": decision_definition_count,
                "decision_context_count": len({row.get("decision_context_id") for row in decision_rows}),
                "source_signal_row_count": context.source_signal_row_count,
                "source_signal_definition_count": context.source_signal_definition_count,
            }
        ),
        "payload_json": _as_json(
            {
                "summary": {
                    "batch_id": batch_id,
                    "decision_row_count": len(decision_rows),
                    "decision_definition_count": decision_definition_count,
                    "decision_context_count": len({row.get("decision_context_id") for row in decision_rows}),
                },
                "source_signal_summary": dict(source_signal_snapshot.get("signal_population_summary") or {}),
                "decision_values": [
                    {
                        "snapshot_id": row.get("snapshot_id"),
                        "decision_id": row.get("decision_id"),
                        "decision_name": row.get("decision_name"),
                        "decision_value": row.get("decision_readiness_status"),
                        "decision_snapshot_context_id": row.get("decision_snapshot_context_id"),
                    }
                    for row in decision_rows
                ],
                "lineage_edges": [dict(row) for row in lineage_edges],
            }
        ),
        "schema_version": DECISION_POPULATION_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": DEFAULT_DECISION_SOURCE_NAME,
        "provider": DEFAULT_DECISION_PROVIDER,
        "market": DEFAULT_DECISION_MARKET,
        "market_type": DEFAULT_DECISION_MARKET_TYPE,
        "asset_class": DEFAULT_DECISION_ASSET_CLASS,
        "lineage_id": _stable_id("decision_summary_lineage", batch_id, summary_snapshot_id, summary_value),
        "version_id": DECISION_TRANSFORMATION_VERSION,
        "quality_score": 1.0 if decision_value_counts.get("BACKTEST_ELIGIBLE", 0) == len(decision_rows) else round(
            decision_value_counts.get("BACKTEST_ELIGIBLE", 0) / max(len(decision_rows), 1), 4
        ),
    }
    return summary_row


def _decision_population_missing_snapshot(
    *,
    storage: LocalStorageEngine,
    dataset_id: str,
    batch_id: str,
    status: str,
    warnings: Sequence[str],
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "readiness": "blocked",
        "lifecycle_state": "missing",
        "dataset_id": dataset_id,
        "dataset_name": DEFAULT_DECISION_DATASET_NAME,
        "batch_id": batch_id,
        "dataset_row_count": 0,
        "decision_context_count": 0,
        "decision_definition_count": len(_DECISION_DEFINITIONS),
        "decision_row_count": 0,
        "decision_rows": [],
        "decision_summary_rows": [],
        "decision_lineage_edges": [],
        "decision_alignment_rows": [],
        "decision_lifecycle_rows": [],
        "decision_validation": {
            "ok": False,
            "status": "rejected",
            "row_count": 0,
            "error_count": len(warnings),
            "warning_count": len(warnings),
            "missing_rows": [],
            "missing_fields": [],
            "duplicate_snapshot_ids": [],
            "duplicate_decision_keys": [],
            "errors": list(warnings),
            "base_validation": {"ok": False, "status": "rejected", "missing_rows": [], "warning_count": len(warnings)},
        },
        "validation": {
            "ok": False,
            "status": "rejected",
            "row_count": 0,
            "error_count": len(warnings),
            "warning_count": len(warnings),
            "missing_rows": [],
            "missing_fields": [],
            "duplicate_snapshot_ids": [],
            "duplicate_decision_keys": [],
            "errors": list(warnings),
            "base_validation": {"ok": False, "status": "rejected", "missing_rows": [], "warning_count": len(warnings)},
        },
        "decision_population_summary": {},
        "decision_population_summary_id": "",
        "decision_evidence_package_id": "",
        "dataset_certification_status": "missing",
        "dataset_certification_id": "",
        "source_signal_snapshot": {},
        "source_signal_summary": {},
        "source_signal_rows": [],
        "source_signal_summary_rows": [],
        "source_signal_row_count": 0,
        "source_signal_definition_count": len(list_signal_definition_ids()),
        "source_signal_context_count": 0,
        "source_signal_population_summary_id": "",
        "source_signal_evidence_package_id": "",
        "source_signal_certification_id": "",
        "source_signal_dataset_certification_id": "",
        "source_signal_batch_id": "",
        "source_signal_batch_lineage_id": "",
        "join_diagnostics": {},
        "registry": summarize_decision_registry(),
        "storage": {
            "backend": storage.backend,
            "path": str(storage.path),
        },
        "unresolved_blockers": list(warnings),
        "warnings": list(warnings),
        "idempotent_reuse": False,
    }


def _load_source_signal_snapshot(
    storage: LocalStorageEngine,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_SIGNAL_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    if not storage.table_exists("signal_snapshots"):
        return {
            "ok": False,
            "status": "missing_signal_table",
            "warnings": ["signal snapshots table is missing"],
            "signal_population_summary": {},
            "signal_population_summary_id": "",
            "signal_rows": [],
            "signal_summary_rows": [],
            "signal_row_count": 0,
            "signal_context_count": 0,
            "signal_definition_count": len(list_signal_definition_ids()),
            "source_feature_batch_id": "",
            "source_math_batch_id": "",
        }
    summary_rows_all = [
        dict(row)
        for row in storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[dataset_id, SIGNAL_BATCH_KIND],
            order_by="created_at ASC, snapshot_id ASC",
        )
    ]
    signal_rows_all = [
        dict(row)
        for row in storage.fetch(
            "signal_snapshots",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[dataset_id, SIGNAL_ROW_KIND],
            order_by="dataset_row_id ASC, decision_context_id ASC, signal_id ASC, snapshot_id ASC",
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
    latest_dataset_certification_row = {}
    if storage.table_exists("historical_certifications"):
        cert_rows = [
            dict(row)
            for row in storage.fetch(
                "historical_certifications",
                where="dataset_id = ? AND batch_id = ?",
                params=["historical_certifications", effective_batch_id],
                order_by="certified_at ASC, certification_id ASC",
            )
        ]
        latest_dataset_certification_row = dict(cert_rows[-1]) if cert_rows else {}
    lifecycle_rows = [
        dict(row)
        for row in storage.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[DEFAULT_SIGNAL_RESEARCH_ASSET_ID],
            order_by="created_at ASC, asset_id ASC",
        )
    ] if storage.table_exists("research_asset_lifecycles") else []
    alignment_rows = [
        dict(row)
        for row in storage.fetch(
            "research_asset_alignment_certifications",
            where="asset_id = ?",
            params=[DEFAULT_SIGNAL_RESEARCH_ASSET_ID],
            order_by="created_at ASC, alignment_certification_id ASC",
        )
    ] if storage.table_exists("research_asset_alignment_certifications") else []
    signal_context_ids = sorted({str(row.get("decision_context_id")) for row in signal_rows if _normalize_text(row.get("decision_context_id"))})
    source_feature_batch_id = _normalize_text(latest_summary_row.get("source_feature_batch_id"))
    source_math_batch_id = _normalize_text(latest_summary_row.get("source_math_batch_id"))
    return {
        "ok": bool(latest_summary_row and signal_rows),
        "status": _normalize_text(latest_summary_row.get("status"), "missing"),
        "signal_population_summary": latest_summary_row,
        "signal_population_summary_id": _normalize_text(latest_summary_row.get("snapshot_id")),
        "signal_rows": signal_rows,
        "signal_summary_rows": summary_rows,
        "signal_row_count": len(signal_rows),
        "signal_context_count": len(signal_context_ids),
        "signal_definition_count": len(list_signal_definition_ids()),
        "source_feature_batch_id": source_feature_batch_id,
        "source_math_batch_id": source_math_batch_id,
        "dataset_certification_status": _normalize_text(latest_dataset_certification_row.get("certification_status"), "missing"),
        "dataset_certification_id": _normalize_text(latest_dataset_certification_row.get("certification_id")),
        "certification_id": _normalize_text(latest_summary_row.get("certification_id")),
        "source_feature_certification_id": _normalize_text(latest_summary_row.get("source_feature_certification_id")),
        "source_feature_dataset_certification_id": _normalize_text(latest_summary_row.get("source_feature_dataset_certification_id")),
        "source_feature_population_summary_id": _normalize_text(latest_summary_row.get("source_feature_population_summary_id")),
        "source_feature_evidence_package_id": _normalize_text(latest_summary_row.get("source_feature_evidence_package_id")),
        "source_feature_batch_lineage_id": _normalize_text(latest_summary_row.get("source_feature_batch_lineage_id")),
        "source_math_certification_id": _normalize_text(latest_summary_row.get("source_math_certification_id")),
        "source_math_dataset_certification_id": _normalize_text(latest_summary_row.get("source_math_dataset_certification_id")),
        "source_math_population_summary_id": _normalize_text(latest_summary_row.get("source_math_population_summary_id")),
        "source_math_evidence_package_id": _normalize_text(latest_summary_row.get("source_math_evidence_package_id")),
        "source_math_batch_lineage_id": _normalize_text(latest_summary_row.get("source_math_batch_lineage_id")),
        "source_signal_certification_id": _normalize_text(latest_summary_row.get("certification_id")),
        "source_signal_dataset_certification_id": _normalize_text(latest_summary_row.get("dataset_certification_id")),
        "source_signal_batch_id": effective_batch_id,
        "source_signal_batch_lineage_id": _normalize_text(latest_summary_row.get("lineage_id")),
        "source_signal_evidence_package_id": _normalize_text(latest_summary_row.get("evidence_package_id")),
        "source_signal_population_summary_id": _normalize_text(latest_summary_row.get("snapshot_id")),
        "source_signal_row_count": len(signal_rows),
        "source_signal_snapshot_count": len(signal_rows),
        "source_signal_definition_count": len(list_signal_definition_ids()),
        "source_signal_summary": latest_summary_row,
        "source_signal_alignment_rows": alignment_rows,
        "source_signal_lifecycle_rows": lifecycle_rows,
        "source_signal_certification_rows": [latest_dataset_certification_row] if latest_dataset_certification_row else [],
        "warnings": [] if latest_summary_row and signal_rows else ["certified signal outputs are required"],
    }


def _load_decision_population_snapshot(
    storage: LocalStorageEngine,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_DECISION_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    if not storage.table_exists("decision_rows"):
        return _decision_population_missing_snapshot(
            storage=storage,
            dataset_id=dataset_id,
            batch_id=_normalize_text(batch_id),
            status="missing_decision_table",
            warnings=["decision rows table is missing"],
        )
    summary_rows_all = [
        dict(row)
        for row in storage.fetch(
            "decision_rows",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[dataset_id, DECISION_BATCH_KIND],
            order_by="created_at ASC, snapshot_id ASC",
        )
    ]
    decision_rows_all = [
        dict(row)
        for row in storage.fetch(
            "decision_rows",
            where="dataset_id = ? AND snapshot_kind = ?",
            params=[dataset_id, DECISION_ROW_KIND],
            order_by="dataset_row_id ASC, decision_id ASC, snapshot_id ASC",
        )
    ]
    effective_batch_id = _normalize_text(batch_id)
    if effective_batch_id:
        summary_rows = [row for row in summary_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id]
        decision_rows = [row for row in decision_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id]
    else:
        summary_rows = summary_rows_all[-1:] if summary_rows_all else []
        effective_batch_id = _normalize_text(summary_rows[-1].get("batch_id")) if summary_rows else ""
        if not effective_batch_id and decision_rows_all:
            effective_batch_id = _normalize_text(decision_rows_all[-1].get("batch_id"))
        decision_rows = [row for row in decision_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else []
        summary_rows = [row for row in summary_rows_all if _normalize_text(row.get("batch_id")) == effective_batch_id] if effective_batch_id else summary_rows
    latest_summary_row = dict(summary_rows[-1]) if summary_rows else {}
    source_signal_batch_id = _normalize_text(latest_summary_row.get("source_signal_batch_id"))
    source_signal_snapshot = _load_source_signal_snapshot(storage, backend=backend, batch_id=source_signal_batch_id or None)
    source_signal_summary = dict(source_signal_snapshot.get("signal_population_summary") or {})
    source_signal_result_timestamp = _normalize_text(
        source_signal_summary.get("created_at")
        or source_signal_summary.get("updated_at")
        or source_signal_snapshot.get("certification_timestamp")
        or source_signal_snapshot.get("created_at")
    )
    source_signal_rows = [dict(row) for row in source_signal_snapshot.get("signal_rows") or []]
    source_signal_summary_rows = [dict(row) for row in source_signal_snapshot.get("signal_summary_rows") or []]
    source_signal_alignment_rows = [dict(row) for row in source_signal_snapshot.get("source_signal_alignment_rows") or []]
    source_signal_lifecycle_rows = [dict(row) for row in source_signal_snapshot.get("source_signal_lifecycle_rows") or []]
    source_signal_certification_rows = [dict(row) for row in source_signal_snapshot.get("source_signal_certification_rows") or []]
    source_signal_certification_status = _normalize_text(source_signal_snapshot.get("dataset_certification_status"), "missing")
    source_signal_dataset_certification_id = _normalize_text(source_signal_snapshot.get("dataset_certification_id"))
    source_signal_definition_ids = list_signal_definition_ids()
    if not source_signal_snapshot.get("ok"):
        return _decision_population_missing_snapshot(
            storage=storage,
            dataset_id=dataset_id,
            batch_id=effective_batch_id,
            status="missing_signal_layer",
            warnings=list(source_signal_snapshot.get("warnings", [])) or ["certified signal outputs are required"],
        )
    if source_signal_certification_status != "certified" or not source_signal_dataset_certification_id:
        return _decision_population_missing_snapshot(
            storage=storage,
            dataset_id=dataset_id,
            batch_id=effective_batch_id,
            status="missing_certified_signal_layer",
            warnings=["certified signal outputs are required"],
        )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_signal_rows:
        grouped[(
            _normalize_text(row.get("dataset_row_id")),
            _normalize_text(row.get("decision_context_id")),
        )].append(dict(row))
    grouped_contexts: list[list[dict[str, Any]]] = []
    for _, rows in sorted(grouped.items()):
        rows.sort(key=lambda row: (_normalize_text(row.get("signal_id")), _normalize_text(row.get("snapshot_id"))))
        grouped_contexts.append(rows)
    provisional_contexts = [
        build_decision_snapshot_context(
            dataset_id=dataset_id,
            batch_id=effective_batch_id or _decision_population_batch_id(dataset_id, source_signal_batch_id, contexts=[]),
            summary_row=source_signal_summary,
            signal_rows=source_signal_rows,
            context_rows=context_rows,
        )
        for context_rows in grouped_contexts
    ]
    decision_batch_id = effective_batch_id or _decision_population_batch_id(dataset_id, source_signal_batch_id, contexts=provisional_contexts)
    decision_contexts = [
        build_decision_snapshot_context(
            dataset_id=dataset_id,
            batch_id=decision_batch_id,
            summary_row=source_signal_summary,
            signal_rows=source_signal_rows,
            context_rows=context_rows,
        )
        for context_rows in grouped_contexts
    ]
    decision_version_id = _stable_id(
        "decision_snapshot_version",
        dataset_id,
        decision_batch_id,
        DECISION_POPULATION_SCHEMA_VERSION,
        DECISION_DEFINITION_VERSION,
        DECISION_TRANSFORMATION_VERSION,
    )
    existing_summary_rows = storage.fetch(
        "decision_rows",
        where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
        params=[dataset_id, decision_batch_id, DECISION_BATCH_KIND],
        limit=1,
    )
    existing_decision_rows = storage.fetch(
        "decision_rows",
        where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
        params=[dataset_id, decision_batch_id, DECISION_ROW_KIND],
    )
    expected_decision_row_count = len(decision_contexts) * len(_DECISION_DEFINITIONS)
    if existing_summary_rows and len(existing_decision_rows) == expected_decision_row_count and expected_decision_row_count > 0:
        return build_decision_row_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=decision_batch_id,
            idempotent_reuse=True,
        )
    decision_rows: list[dict[str, Any]] = []
    lineage_rows: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    for index, (context_rows, context) in enumerate(zip(grouped_contexts, decision_contexts), start=1):
        source_maps = _decision_source_maps(context_rows)
        decision_ready = "BACKTEST_ELIGIBLE" if len(source_maps["source_signal_snapshot_ids"]) == len(source_signal_definition_ids) else "EXCLUDED"
        for definition in _DECISION_DEFINITIONS:
            row, lineage_row = _decision_row_payload_and_values(
                definition=definition,
                context=DecisionSnapshotContext(
                    **{
                        **context.as_dict(),
                        "decision_readiness_status": decision_ready,
                    },
                ),
                context_rows=context_rows,
                source_signal_snapshot=source_signal_snapshot,
                source_maps=source_maps,
                storage_location=str(storage.path),
                created_at=_utc_now_iso(),
                decision_batch_id=decision_batch_id,
                decision_version_id=decision_version_id,
                decision_evidence_package_id=_stable_id(
                    "decision_evidence_package",
                    source_signal_snapshot.get("source_signal_evidence_package_id") or source_signal_snapshot.get("evidence_package_id"),
                    decision_batch_id,
                    DECISION_TRANSFORMATION_VERSION,
                ),
                decision_row_index=len(lineage_rows) + 1,
            )
            row["decision_readiness_status"] = decision_ready
            lineage_row["readiness"] = "backtest_ready" if decision_ready == "BACKTEST_ELIGIBLE" else "blocked"
            lineage_row["status"] = "certified"
            row["readiness"] = "backtest_ready" if decision_ready == "BACKTEST_ELIGIBLE" else "blocked"
            row["status"] = "certified"
            row["validation_state"] = "validated"
            row["quality_score"] = 1.0 if decision_ready == "BACKTEST_ELIGIBLE" else 0.0
            decision_rows.append(row)
            lineage_rows.append(lineage_row)
            validation_rows.append(
                {
                    **row,
                    "provider_timestamp": row.get("decision_cutoff_time"),
                    "snapshot_time": row.get("decision_cutoff_time"),
                    "decision_time": row.get("decision_cutoff_time"),
                    "result_timestamp": source_signal_result_timestamp,
                }
            )
        row_signal_ids = list(source_maps["source_signal_snapshot_ids"])
        alignment_batch_id = _decision_alignment_batch_id(context.as_dict(), decision_batch_id)
        alignment_rows.append(
            build_time_entity_alignment_certification_row(
                identity=build_research_asset_identity_contract(
                    asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
                    asset_family="decision",
                    market_profile=DEFAULT_DECISION_PROFILE_ID,
                    market=DEFAULT_DECISION_MARKET,
                    league="nfl",
                    sport="football",
                    season=str(context.season),
                    week_or_date=str(context.week),
                    event_id=context.event_id,
                    market_id=_normalize_text(context.selection, "decision_backtest_eligibility"),
                    selection=_normalize_text(context.selection, "decision_backtest_eligibility"),
                    provider=DEFAULT_DECISION_PROVIDER,
                    connector="signal_population",
                    schema_version=DECISION_POPULATION_SCHEMA_VERSION,
                    lineage_version=decision_version_id,
                    asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                    asset_type="decision_snapshot",
                    team_id=_normalize_text(context.home_team_id or context.away_team_id),
                    game_id=_normalize_text(context.event_id),
                    market_type=DEFAULT_DECISION_MARKET_TYPE,
                ),
                alignment=build_time_entity_alignment_certification(
                    identity=build_research_asset_identity_contract(
                        asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
                        asset_family="decision",
                        market_profile=DEFAULT_DECISION_PROFILE_ID,
                        market=DEFAULT_DECISION_MARKET,
                        league="nfl",
                        sport="football",
                        season=str(context.season),
                        week_or_date=str(context.week),
                        event_id=context.event_id,
                        market_id=_normalize_text(context.selection, "decision_backtest_eligibility"),
                        selection=_normalize_text(context.selection, "decision_backtest_eligibility"),
                        provider=DEFAULT_DECISION_PROVIDER,
                        connector="signal_population",
                        schema_version=DECISION_POPULATION_SCHEMA_VERSION,
                        lineage_version=decision_version_id,
                        asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                        asset_type="decision_snapshot",
                        team_id=_normalize_text(context.home_team_id or context.away_team_id),
                        game_id=_normalize_text(context.event_id),
                        market_type=DEFAULT_DECISION_MARKET_TYPE,
                    ),
                    rows=[
                        {
                            **dict(row),
                            "asset_id": DEFAULT_DECISION_RESEARCH_ASSET_ID,
                            "asset_family": "decision",
                            "asset_name": DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                            "asset_type": "decision_snapshot",
                            "lineage_version": decision_version_id,
                            "season": str(context.season),
                            "event_id": context.event_id,
                            "game_id": context.event_id,
                            "market_id": _normalize_text(row.get("decision_id")),
                            "provider": DEFAULT_DECISION_PROVIDER,
                            "schema_version": DECISION_POPULATION_SCHEMA_VERSION,
                            "provider_timestamp": _normalize_text(row.get("decision_cutoff_time")),
                            "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                            "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                            "result_timestamp": source_signal_result_timestamp,
                            "market_profile": DEFAULT_DECISION_PROFILE_ID,
                            "market": DEFAULT_DECISION_MARKET,
                            "market_type": DEFAULT_DECISION_MARKET_TYPE,
                            "league": "nfl",
                            "sport": "football",
                            "week_or_date": str(context.week),
                            "team_id": _normalize_text(row.get("home_team_id") or row.get("away_team_id")),
                            "participant_id": "",
                            "selection": _normalize_text(row.get("decision_id")),
                            "connector": "signal_population",
                        }
                        for row in decision_rows[-len(_DECISION_DEFINITIONS):]
                    ],
                    required_fields=(
                        "dataset_id",
                        "dataset_name",
                        "snapshot_id",
                        "batch_id",
                        "decision_id",
                        "decision_name",
                        "decision_readiness_status",
                        "decision_value_json",
                        "decision_context_id",
                        "decision_snapshot_context_id",
                        "source_signal_batch_id",
                        "source_signal_population_summary_id",
                    ),
                    required_timestamps=(
                        "scheduled_kickoff_time",
                        "decision_cutoff_time",
                        "created_at",
                        "updated_at",
                    ),
                    profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                    source_bundle={
                        "source_name": DEFAULT_DECISION_SOURCE_NAME,
                        "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                        "source_key": DEFAULT_DECISION_SOURCE_KEY,
                        "provider": DEFAULT_DECISION_PROVIDER,
                        "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                        "result_timestamp": source_signal_result_timestamp,
                    },
                    raw_acquisition_result={
                        "ok": True,
                        "status": "signal_output_input",
                        "dataset_id": DEFAULT_DECISION_DATASET_ID,
                        "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                    },
                    created_at=_utc_now_iso(),
                    asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                    asset_type="decision_snapshot",
                    lifecycle_state="backtest_ready",
                    batch_id=alignment_batch_id,
                ),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": context.event_id,
                    "source_market_id": _normalize_text(context.selection, "decision_backtest_eligibility"),
                    "source_selection_id": _normalize_text(context.selection, "decision_backtest_eligibility"),
                    "source_snapshot_time": _normalize_text(context.decision_cutoff_time),
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": context.event_id,
                    "source_market_id": _normalize_text(context.selection, "decision_backtest_eligibility"),
                    "source_selection_id": _normalize_text(context.selection, "decision_backtest_eligibility"),
                    "source_snapshot_time": _normalize_text(context.decision_cutoff_time),
                    "snapshot_time": _normalize_text(context.decision_cutoff_time),
                    "decision_time": _normalize_text(context.decision_cutoff_time),
                    "result_timestamp": source_signal_result_timestamp,
                },
                batch_id=alignment_batch_id,
            )
        )
    decision_validation = validate_decision_rows(decision_rows)
    if not decision_validation["ok"]:
        raise ValueError("; ".join(decision_validation.get("errors", [])) or "decision rows failed validation")
    summary_row = _decision_summary_row(
        context_rows=grouped_contexts[0] if grouped_contexts else [],
        source_signal_snapshot=source_signal_snapshot,
        context=decision_contexts[0] if decision_contexts else build_decision_snapshot_context(
            dataset_id=dataset_id,
            batch_id=decision_batch_id,
            summary_row=source_signal_summary,
            signal_rows=source_signal_rows,
            context_rows=grouped_contexts[0] if grouped_contexts else [],
        ),
        batch_id=decision_batch_id,
        storage_location=str(storage.path),
        created_at=_utc_now_iso(),
        decision_rows=decision_rows,
        lineage_edges=lineage_rows,
        decision_definition_count=len(_DECISION_DEFINITIONS),
    )
    decision_asset_contract = ResearchAssetCertificationContract(
        research_asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
        research_asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
        asset_category="decision",
        asset_type="snapshot_batch",
        source_table_name="decision_rows",
        required_fields=_required_row_fields(),
        required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
        point_in_time_rules=(
            "scheduled_kickoff_time must predate the decision cutoff",
            "decision_cutoff_time must remain unchanged from the certified signal layer",
            "decision outputs must remain observation-only and signal-derived",
        ),
        description=(
            "Deterministic reusable decision rows derived only from certified signal outputs and "
            "preserved with explicit provenance, lineage, and point-in-time constraints."
        ),
        priority="P0",
        required=True,
        future_asset=False,
        metadata={
            "market_profile": DEFAULT_DECISION_PROFILE_ID,
            "market_family": "sports",
            "minimum_schema": True,
            "dataset_role": "decision_population",
            "source_signal_batch_id": _normalize_text(source_signal_snapshot.get("signal_population_summary", {}).get("batch_id")),
            "source_signal_certification_id": _normalize_text(source_signal_snapshot.get("certification_id")),
            "source_signal_dataset_certification_id": _normalize_text(source_signal_snapshot.get("dataset_certification_id")),
            "source_signal_evidence_package_id": _normalize_text(source_signal_snapshot.get("source_signal_evidence_package_id")),
            "source_signal_population_summary_id": _normalize_text(source_signal_snapshot.get("signal_population_summary_id")),
            "source_feature_batch_id": _normalize_text(source_signal_snapshot.get("source_feature_batch_id")),
            "source_feature_certification_id": _normalize_text(source_signal_snapshot.get("source_feature_certification_id")),
            "source_feature_dataset_certification_id": _normalize_text(source_signal_snapshot.get("source_feature_dataset_certification_id")),
            "source_feature_evidence_package_id": _normalize_text(source_signal_snapshot.get("source_feature_evidence_package_id")),
            "source_math_batch_id": _normalize_text(source_signal_snapshot.get("source_math_batch_id")),
            "source_math_certification_id": _normalize_text(source_signal_snapshot.get("source_math_certification_id")),
            "source_math_dataset_certification_id": _normalize_text(source_signal_snapshot.get("source_math_dataset_certification_id")),
            "source_math_evidence_package_id": _normalize_text(source_signal_snapshot.get("source_math_evidence_package_id")),
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
            "source_name": DEFAULT_DECISION_SOURCE_NAME,
            "source_type": DEFAULT_DECISION_SOURCE_TYPE,
            "source_key": DEFAULT_DECISION_SOURCE_KEY,
            "provider": DEFAULT_DECISION_PROVIDER,
            "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "result_timestamp": source_signal_result_timestamp,
        }
        raw_acquisition_result = {
            "ok": True,
            "status": "signal_output_input",
            "dataset_id": DEFAULT_DECISION_DATASET_ID,
            "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "result_timestamp": source_signal_result_timestamp,
        }
        decision_result = certification_runtime.certify_research_asset(
            asset_contract=decision_asset_contract,
            rows=decision_rows + [summary_row],
            profile_id=DEFAULT_DECISION_PROFILE_ID,
            validation=decision_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=DECISION_TRANSFORMATION_VERSION,
            created_at=_utc_now_iso(),
            batch_id=decision_batch_id,
        )
        decision_certification_row = dict(decision_result["research_asset_certification"])
        storage.upsert("decision_rows", summary_row, key_columns=("snapshot_id",))
        for row in decision_rows:
            storage.upsert("decision_rows", row, key_columns=("snapshot_id",))
        for lineage_row in lineage_rows:
            storage.upsert("lineage_edges", lineage_row, key_columns=("lineage_edge_id",))
        decision_dataset_row = build_historical_dataset_certification_row(
            profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
            dataset_version=DECISION_TRANSFORMATION_VERSION,
            batch_id=decision_batch_id,
            created_at=_utc_now_iso(),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=[decision_certification_row],
        )
        storage.upsert("historical_certifications", decision_dataset_row, key_columns=("certification_id",))
        decision_identity = build_research_asset_identity_contract(
            asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
            asset_family="decision",
            market_profile=DEFAULT_DECISION_PROFILE_ID,
            market=DEFAULT_DECISION_MARKET,
            league="nfl",
            sport="football",
            season=str(summary_row.get("season") or ""),
            week_or_date=str(summary_row.get("week") or ""),
            event_id=_normalize_text(summary_row.get("event_id")),
            market_id=f"{decision_batch_id}.decision",
            selection="decision_population",
            provider=DEFAULT_DECISION_PROVIDER,
            connector="signal_population",
            schema_version=DECISION_POPULATION_SCHEMA_VERSION,
            lineage_version=decision_batch_id,
            asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
            asset_type="decision_snapshot_batch",
            team_id=_normalize_text(summary_row.get("target_team_id") or summary_row.get("home_team_id") or summary_row.get("away_team_id")),
            game_id=_normalize_text(summary_row.get("game_id") or summary_row.get("event_id")),
            market_type=DEFAULT_DECISION_MARKET_TYPE,
        )
        identity_validation = validate_research_asset_identity_contract(decision_identity)
        if not identity_validation["ok"]:
            raise ValueError("; ".join(identity_validation.get("errors", [])) or "decision identity validation failed")

        decision_alignment_rows_result: list[dict[str, Any]] = []
        for row in decision_rows + [summary_row]:
            alignment_batch_id = _decision_alignment_batch_id(row, decision_batch_id)
            row_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
                asset_family="decision",
                market_profile=DEFAULT_DECISION_PROFILE_ID,
                market=DEFAULT_DECISION_MARKET,
                league="nfl",
                sport="football",
                season=str(row.get("season") or ""),
                week_or_date=str(row.get("week") or ""),
                event_id=_normalize_text(row.get("event_id")),
                market_id=_normalize_text(row.get("decision_id")),
                selection=_normalize_text(row.get("decision_id")),
                provider=DEFAULT_DECISION_PROVIDER,
                connector="signal_population",
                schema_version=DECISION_POPULATION_SCHEMA_VERSION,
                lineage_version=_normalize_text(row.get("version_id"), DECISION_TRANSFORMATION_VERSION),
                asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                asset_type="decision_snapshot",
                team_id=_normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                game_id=_normalize_text(row.get("game_id") or row.get("event_id")),
                market_type=DEFAULT_DECISION_MARKET_TYPE,
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[
                    {
                        **dict(row),
                        "asset_id": DEFAULT_DECISION_RESEARCH_ASSET_ID,
                        "asset_family": "decision",
                        "asset_name": DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                        "asset_type": "decision_snapshot",
                        "lineage_version": _normalize_text(row.get("version_id"), DECISION_TRANSFORMATION_VERSION),
                        "market_id": _normalize_text(row.get("decision_id")),
                        "provider_timestamp": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                        "result_timestamp": source_signal_result_timestamp,
                        "market_profile": DEFAULT_DECISION_PROFILE_ID,
                        "market": DEFAULT_DECISION_MARKET,
                        "league": "nfl",
                        "sport": "football",
                        "week_or_date": str(row.get("week") or ""),
                        "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                        "participant_id": "",
                        "selection": _normalize_text(row.get("decision_id")),
                        "connector": "signal_population",
                    }
                ],
                required_fields=(
                    "dataset_id",
                    "dataset_name",
                    "snapshot_id",
                    "batch_id",
                    "decision_id",
                    "decision_name",
                    "decision_readiness_status",
                    "decision_value_json",
                    "decision_context_id",
                    "decision_snapshot_context_id",
                    "source_signal_batch_id",
                    "source_signal_population_summary_id",
                ),
                required_timestamps=(
                    "scheduled_kickoff_time",
                    "decision_cutoff_time",
                    "created_at",
                    "updated_at",
                ),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                    "result_timestamp": source_signal_result_timestamp,
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                created_at=_utc_now_iso(),
                asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                asset_type="decision_snapshot",
                lifecycle_state="backtest_ready",
                batch_id=alignment_batch_id,
            )
            alignment_validation = validate_time_entity_alignment_certification_row(build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                batch_id=alignment_batch_id,
            ))
            if not alignment_validation["ok"]:
                raise ValueError("; ".join(alignment_validation.get("issues", [])) or "decision alignment validation failed")
            storage.upsert("research_asset_alignment_certifications", build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                batch_id=alignment_batch_id,
            ), key_columns=("alignment_certification_id",))
            decision_alignment_rows_result.append(
                {
                    "ok": alignment_contract.alignment_status == "aligned",
                    "status": alignment_contract.alignment_status,
                    "identity": row_identity.as_dict(),
                    "alignment_certification": alignment_contract.as_dict(),
                    "alignment_certification_row": build_time_entity_alignment_certification_row(
                        identity=row_identity,
                        alignment=alignment_contract,
                        profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                        source_bundle={
                            "source_name": DEFAULT_DECISION_SOURCE_NAME,
                            "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                            "source_key": DEFAULT_DECISION_SOURCE_KEY,
                            "provider": DEFAULT_DECISION_PROVIDER,
                            "source_file": str(storage.path),
                            "source_event_id": _normalize_text(row.get("event_id")),
                            "source_market_id": _normalize_text(row.get("decision_id")),
                            "source_selection_id": _normalize_text(row.get("decision_id")),
                            "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        },
                        raw_acquisition_result={
                            "ok": True,
                            "status": "signal_output_input",
                            "dataset_id": DEFAULT_DECISION_DATASET_ID,
                            "source_name": DEFAULT_DECISION_SOURCE_NAME,
                            "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                            "source_key": DEFAULT_DECISION_SOURCE_KEY,
                            "provider": DEFAULT_DECISION_PROVIDER,
                            "source_file": str(storage.path),
                            "source_event_id": _normalize_text(row.get("event_id")),
                            "source_market_id": _normalize_text(row.get("decision_id")),
                            "source_selection_id": _normalize_text(row.get("decision_id")),
                            "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        },
                        batch_id=alignment_batch_id,
                    ),
                    "validation": alignment_validation,
                }
            )
        lifecycle_rows: list[dict[str, Any]] = [
            lifecycle_runtime.record_lifecycle_state(
                identity=decision_identity,
                lifecycle_state="backtest_ready",
                lifecycle_reason=f"{DEFAULT_DECISION_RESEARCH_ASSET_NAME} promoted to backtest_ready",
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=_utc_now_iso(),
                certification_result=decision_certification_row,
                dataset_result=decision_dataset_row,
                notes={
                    "batch_id": decision_batch_id,
                    "decision_row_count": len(decision_rows),
                    "decision_definition_count": len(_DECISION_DEFINITIONS),
                    "decision_context_count": len(decision_contexts),
                    "source_signal_batch_id": source_signal_batch_id,
                    "previous_states": ["research_asset_certified", "dataset_certified"],
                    "signal_input_only": True,
                },
            )
        ]
        latest_summary_row = dict(summary_row)
        latest_summary_row.setdefault("status", "certified")
        latest_summary_row.setdefault("readiness", "backtest_ready")
        latest_summary_row.setdefault("validation_state", "validated")
        storage.upsert("decision_rows", latest_summary_row, key_columns=("snapshot_id",))
        for row in decision_rows:
            storage.upsert("decision_rows", row, key_columns=("snapshot_id",))
        for lineage_row in lineage_rows:
            storage.upsert("lineage_edges", lineage_row, key_columns=("lineage_edge_id",))
        return build_decision_row_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=DEFAULT_DECISION_DATASET_ID,
            batch_id=decision_batch_id,
            idempotent_reuse=False,
        )
    finally:
        storage.close()


def build_decision_row_population_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_DECISION_DATASET_ID,
    batch_id: str | None = None,
    idempotent_reuse: bool = False,
) -> dict[str, Any]:
    storage = create_local_storage_engine(storage_path or DEFAULT_DECISION_STORAGE_PATH, backend=backend)
    try:
        persisted_snapshot = _load_decision_population_snapshot(storage, backend=backend, dataset_id=dataset_id, batch_id=batch_id)
        if persisted_snapshot.get("ok"):
            persisted_snapshot["idempotent_reuse"] = bool(idempotent_reuse)
            persisted_snapshot.setdefault("registry", summarize_decision_registry())
            persisted_snapshot.setdefault("storage", {"backend": storage.backend, "path": str(storage.path)})
            return persisted_snapshot
        if persisted_snapshot.get("decision_rows") or persisted_snapshot.get("decision_summary_rows"):
            raise ValueError("; ".join(persisted_snapshot.get("unresolved_blockers", [])) or "existing decision batch is incomplete")
        return persisted_snapshot
    finally:
        storage.close()


def build_decision_row_population(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_DECISION_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    storage = create_local_storage_engine(storage_path or DEFAULT_DECISION_STORAGE_PATH, backend=backend)
    try:
        persisted_snapshot = _load_decision_population_snapshot(
            storage,
            backend=backend,
            dataset_id=dataset_id,
            batch_id=batch_id,
        )
        if persisted_snapshot.get("ok"):
            persisted_snapshot["idempotent_reuse"] = True
            persisted_snapshot.setdefault("registry", summarize_decision_registry())
            return persisted_snapshot
        if persisted_snapshot.get("decision_rows") or persisted_snapshot.get("decision_summary_rows"):
            raise ValueError("; ".join(persisted_snapshot.get("unresolved_blockers", [])) or "existing decision batch is incomplete")

        source_signal_snapshot = _load_source_signal_snapshot(storage, backend=backend)
        if not source_signal_snapshot.get("ok"):
            return _decision_population_missing_snapshot(
                storage=storage,
                dataset_id=dataset_id,
                batch_id=_normalize_text(batch_id),
                status=_normalize_text(source_signal_snapshot.get("status"), "missing_signal_layer"),
                warnings=list(source_signal_snapshot.get("warnings", [])) or ["certified signal outputs are required"],
            )

        source_signal_rows = [dict(row) for row in source_signal_snapshot.get("signal_rows") or []]
        if not source_signal_rows:
            return _decision_population_missing_snapshot(
                storage=storage,
                dataset_id=dataset_id,
                batch_id=_normalize_text(batch_id),
                status="missing_signal_rows",
                warnings=["certified signal outputs are required"],
            )

        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in source_signal_rows:
            grouped[(
                _normalize_text(row.get("dataset_row_id")),
                _normalize_text(row.get("decision_context_id")),
            )].append(dict(row))
        grouped_contexts: list[list[dict[str, Any]]] = []
        for _, rows in sorted(grouped.items()):
            rows.sort(key=lambda row: (_normalize_text(row.get("signal_id")), _normalize_text(row.get("snapshot_id"))))
            grouped_contexts.append(rows)

        provisional_contexts = [
            build_decision_snapshot_context(
                dataset_id=dataset_id,
                batch_id=_normalize_text(batch_id) or _decision_population_batch_id(dataset_id, _normalize_text(source_signal_snapshot.get("signal_population_summary", {}).get("batch_id")), contexts=[]),
                summary_row=source_signal_snapshot.get("signal_population_summary") or {},
                signal_rows=source_signal_rows,
                context_rows=context_rows,
            )
            for context_rows in grouped_contexts
        ]
        decision_batch_id = _normalize_text(batch_id) or _decision_population_batch_id(
            dataset_id,
            _normalize_text(source_signal_snapshot.get("signal_population_summary", {}).get("batch_id")),
            contexts=provisional_contexts,
        )
        decision_contexts = [
            build_decision_snapshot_context(
                dataset_id=dataset_id,
                batch_id=decision_batch_id,
                summary_row=source_signal_snapshot.get("signal_population_summary") or {},
                signal_rows=source_signal_rows,
                context_rows=context_rows,
            )
            for context_rows in grouped_contexts
        ]
        decision_version_id = _stable_id(
            "decision_snapshot_version",
            dataset_id,
            decision_batch_id,
            DECISION_POPULATION_SCHEMA_VERSION,
            DECISION_DEFINITION_VERSION,
            DECISION_TRANSFORMATION_VERSION,
        )
        existing_summary_rows = storage.fetch(
            "decision_rows",
            where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
            params=[dataset_id, decision_batch_id, DECISION_BATCH_KIND],
            limit=1,
        )
        existing_decision_rows = storage.fetch(
            "decision_rows",
            where="dataset_id = ? AND batch_id = ? AND snapshot_kind = ?",
            params=[dataset_id, decision_batch_id, DECISION_ROW_KIND],
        )
        expected_decision_row_count = len(decision_contexts) * len(_DECISION_DEFINITIONS)
        if existing_summary_rows and len(existing_decision_rows) == expected_decision_row_count:
            return build_decision_row_population_dashboard_snapshot(
                storage_path=storage.path,
                backend=backend,
                dataset_id=dataset_id,
                batch_id=decision_batch_id,
                idempotent_reuse=True,
            )

        decision_rows: list[dict[str, Any]] = []
        lineage_rows: list[dict[str, Any]] = []
        alignment_rows: list[dict[str, Any]] = []
        validation_rows: list[dict[str, Any]] = []
        source_signal_summary = dict(source_signal_snapshot.get("signal_population_summary") or {})
        source_signal_result_timestamp = _normalize_text(
            source_signal_summary.get("created_at")
            or source_signal_summary.get("updated_at")
            or source_signal_snapshot.get("certification_timestamp")
            or source_signal_snapshot.get("created_at")
        )
        for context_rows, context in zip(grouped_contexts, decision_contexts):
            source_maps = _decision_source_maps(context_rows)
            decision_ready = "BACKTEST_ELIGIBLE" if len(source_maps["source_signal_snapshot_ids"]) == len(list_signal_definition_ids()) else "EXCLUDED"
            context = DecisionSnapshotContext(
                **{
                    **context.as_dict(),
                    "decision_readiness_status": decision_ready,
                }
            )
            for definition in _DECISION_DEFINITIONS:
                row, lineage_row = _decision_row_payload_and_values(
                    definition=definition,
                    context=context,
                    context_rows=context_rows,
                    source_signal_snapshot=source_signal_snapshot,
                    source_maps=source_maps,
                    storage_location=str(storage.path),
                    created_at=_utc_now_iso(),
                    decision_batch_id=decision_batch_id,
                    decision_version_id=decision_version_id,
                    decision_evidence_package_id=_stable_id(
                        "decision_evidence_package",
                        source_signal_snapshot.get("evidence_package_id") or source_signal_snapshot.get("source_signal_evidence_package_id"),
                        decision_batch_id,
                        DECISION_TRANSFORMATION_VERSION,
                    ),
                    decision_row_index=len(lineage_rows) + 1,
                )
                row["decision_readiness_status"] = decision_ready
                row["readiness"] = "backtest_ready" if decision_ready == "BACKTEST_ELIGIBLE" else "blocked"
                row["status"] = "certified"
                row["validation_state"] = "validated"
                row["quality_score"] = 1.0 if decision_ready == "BACKTEST_ELIGIBLE" else 0.0
                lineage_row["readiness"] = row["readiness"]
                lineage_row["status"] = "certified"
                decision_rows.append(row)
                lineage_rows.append(lineage_row)
                validation_rows.append(
                    {
                        **row,
                        "provider_timestamp": row.get("decision_cutoff_time"),
                        "snapshot_time": row.get("decision_cutoff_time"),
                        "decision_time": row.get("decision_cutoff_time"),
                        "result_timestamp": source_signal_result_timestamp,
                    }
                )
            summary_snapshot_id = _stable_id(
                "decision_population_summary_snapshot",
                DEFAULT_DECISION_DATASET_ID,
                decision_batch_id,
                DECISION_TRANSFORMATION_VERSION,
            )
            summary_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
                asset_family="decision",
                market_profile=DEFAULT_DECISION_PROFILE_ID,
                market=DEFAULT_DECISION_MARKET,
                league="nfl",
                sport="football",
                season=str(context.season),
                week_or_date=str(context.week),
                event_id=context.event_id,
                market_id="decision_population_summary",
                selection="decision_population_summary",
                provider=DEFAULT_DECISION_PROVIDER,
                connector="signal_population",
                schema_version=DECISION_POPULATION_SCHEMA_VERSION,
                lineage_version=decision_version_id,
                asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                asset_type="decision_snapshot_batch",
                team_id=_normalize_text(context.home_team_id or context.away_team_id),
                game_id=_normalize_text(context.event_id),
                market_type=DEFAULT_DECISION_MARKET_TYPE,
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=summary_identity,
                rows=[
                    {
                        **dict(summary_row),
                        "asset_id": DEFAULT_DECISION_RESEARCH_ASSET_ID,
                        "asset_family": "decision",
                        "asset_name": DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                        "asset_type": "decision_snapshot_batch",
                        "lineage_version": decision_version_id,
                        "market_id": "decision_population_summary",
                        "provider_timestamp": _normalize_text(summary_row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                        "result_timestamp": source_signal_result_timestamp,
                        "market_profile": DEFAULT_DECISION_PROFILE_ID,
                        "market": DEFAULT_DECISION_MARKET,
                        "league": "nfl",
                        "sport": "football",
                        "week_or_date": str(summary_row.get("week") or ""),
                        "team_id": _normalize_text(summary_row.get("target_team_id") or summary_row.get("home_team_id") or summary_row.get("away_team_id")),
                        "participant_id": "",
                        "selection": "decision_population_summary",
                        "connector": "signal_population",
                    }
                ],
                required_fields=(
                    "dataset_id",
                    "dataset_name",
                    "snapshot_id",
                    "batch_id",
                    "decision_id",
                    "decision_name",
                    "decision_readiness_status",
                    "decision_value_json",
                    "decision_context_id",
                    "decision_snapshot_context_id",
                    "source_signal_batch_id",
                    "source_signal_population_summary_id",
                ),
                required_timestamps=(
                    "scheduled_kickoff_time",
                    "decision_cutoff_time",
                    "created_at",
                    "updated_at",
                ),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "result_timestamp": source_signal_result_timestamp,
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
                    "result_timestamp": source_signal_result_timestamp,
                },
                created_at=_utc_now_iso(),
                asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                asset_type="decision_snapshot_batch",
                lifecycle_state="backtest_ready",
                batch_id=alignment_batch_id,
            )
        decision_validation = validate_decision_rows(decision_rows)
        if not decision_validation["ok"]:
            raise ValueError("; ".join(decision_validation.get("errors", [])) or "decision rows failed validation")
        summary_row = _decision_summary_row(
            context_rows=grouped_contexts[0] if grouped_contexts else [],
            source_signal_snapshot=source_signal_snapshot,
            context=decision_contexts[0] if decision_contexts else build_decision_snapshot_context(
                dataset_id=dataset_id,
                batch_id=decision_batch_id,
                summary_row=source_signal_summary,
                signal_rows=source_signal_rows,
                context_rows=grouped_contexts[0] if grouped_contexts else [],
            ),
            batch_id=decision_batch_id,
            storage_location=str(storage.path),
            created_at=_utc_now_iso(),
            decision_rows=decision_rows,
            lineage_edges=lineage_rows,
            decision_definition_count=len(_DECISION_DEFINITIONS),
        )
        source_bundle = {
            "source_name": DEFAULT_DECISION_SOURCE_NAME,
            "source_type": DEFAULT_DECISION_SOURCE_TYPE,
            "source_key": DEFAULT_DECISION_SOURCE_KEY,
            "provider": DEFAULT_DECISION_PROVIDER,
            "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "result_timestamp": source_signal_result_timestamp,
        }
        raw_acquisition_result = {
            "ok": True,
            "status": "signal_output_input",
            "dataset_id": DEFAULT_DECISION_DATASET_ID,
            "source_snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "snapshot_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "decision_time": _normalize_text(summary_row.get("decision_cutoff_time")),
            "result_timestamp": source_signal_result_timestamp,
        }
        decision_asset_contract = ResearchAssetCertificationContract(
            research_asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
            research_asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
            asset_category="decision",
            asset_type="snapshot_batch",
            source_table_name="decision_rows",
            required_fields=_required_row_fields(),
            required_timestamps=("scheduled_kickoff_time", "decision_cutoff_time", "created_at", "updated_at"),
            point_in_time_rules=(
                "scheduled_kickoff_time must predate the decision cutoff",
                "decision_cutoff_time must remain unchanged from the certified signal layer",
                "decision outputs must remain observation-only and signal-derived",
            ),
            description=(
                "Deterministic reusable decision rows derived only from certified signal outputs and "
                "preserved with explicit provenance, lineage, and point-in-time constraints."
            ),
            priority="P0",
            required=True,
            future_asset=False,
            metadata={
                "market_profile": DEFAULT_DECISION_PROFILE_ID,
                "market_family": "sports",
                "minimum_schema": True,
                "dataset_role": "decision_population",
                "source_signal_batch_id": _normalize_text(source_signal_snapshot.get("signal_population_summary", {}).get("batch_id")),
                "source_signal_certification_id": _normalize_text(source_signal_snapshot.get("certification_id")),
                "source_signal_dataset_certification_id": _normalize_text(source_signal_snapshot.get("dataset_certification_id")),
                "source_signal_evidence_package_id": _normalize_text(source_signal_snapshot.get("evidence_package_id")),
                "source_signal_population_summary_id": _normalize_text(source_signal_snapshot.get("signal_population_summary_id")),
                "source_feature_batch_id": _normalize_text(source_signal_snapshot.get("source_feature_batch_id")),
                "source_feature_certification_id": _normalize_text(source_signal_snapshot.get("source_feature_certification_id")),
                "source_feature_dataset_certification_id": _normalize_text(source_signal_snapshot.get("source_feature_dataset_certification_id")),
                "source_feature_evidence_package_id": _normalize_text(source_signal_snapshot.get("source_feature_evidence_package_id")),
                "source_math_batch_id": _normalize_text(source_signal_snapshot.get("source_math_batch_id")),
                "source_math_certification_id": _normalize_text(source_signal_snapshot.get("source_math_certification_id")),
                "source_math_dataset_certification_id": _normalize_text(source_signal_snapshot.get("source_math_dataset_certification_id")),
                "source_math_evidence_package_id": _normalize_text(source_signal_snapshot.get("source_math_evidence_package_id")),
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
        decision_result = certification_runtime.certify_research_asset(
            asset_contract=decision_asset_contract,
            rows=decision_rows + [summary_row],
            profile_id=DEFAULT_DECISION_PROFILE_ID,
            validation=decision_validation,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            dataset_version=DECISION_TRANSFORMATION_VERSION,
            created_at=_utc_now_iso(),
            batch_id=decision_batch_id,
        )
        decision_certification_row = dict(decision_result["research_asset_certification"])
        storage.upsert("decision_rows", summary_row, key_columns=("snapshot_id",))
        for row in decision_rows:
            storage.upsert("decision_rows", row, key_columns=("snapshot_id",))
        for lineage_row in lineage_rows:
            storage.upsert("lineage_edges", lineage_row, key_columns=("lineage_edge_id",))
        decision_dataset_row = build_historical_dataset_certification_row(
            profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
            dataset_version=DECISION_TRANSFORMATION_VERSION,
            batch_id=decision_batch_id,
            created_at=_utc_now_iso(),
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=[decision_certification_row],
        )
        storage.upsert("historical_certifications", decision_dataset_row, key_columns=("certification_id",))
        decision_identity = build_research_asset_identity_contract(
            asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
            asset_family="decision",
            market_profile=DEFAULT_DECISION_PROFILE_ID,
            market=DEFAULT_DECISION_MARKET,
            league="nfl",
            sport="football",
            season=str(summary_row.get("season") or ""),
            week_or_date=str(summary_row.get("week") or ""),
            event_id=_normalize_text(summary_row.get("event_id")),
            market_id=f"{decision_batch_id}.decision",
            selection="decision_population",
            provider=DEFAULT_DECISION_PROVIDER,
            connector="signal_population",
            schema_version=DECISION_POPULATION_SCHEMA_VERSION,
            lineage_version=decision_batch_id,
            asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
            asset_type="decision_snapshot_batch",
            team_id=_normalize_text(summary_row.get("target_team_id") or summary_row.get("home_team_id") or summary_row.get("away_team_id")),
            game_id=_normalize_text(summary_row.get("game_id") or summary_row.get("event_id")),
            market_type=DEFAULT_DECISION_MARKET_TYPE,
        )
        identity_validation = validate_research_asset_identity_contract(decision_identity)
        if not identity_validation["ok"]:
            raise ValueError("; ".join(identity_validation.get("errors", [])) or "decision identity validation failed")
        decision_alignment_rows_result: list[dict[str, Any]] = []
        for row in decision_rows + [summary_row]:
            alignment_batch_id = _decision_alignment_batch_id(row, decision_batch_id)
            row_identity = build_research_asset_identity_contract(
                asset_id=DEFAULT_DECISION_RESEARCH_ASSET_ID,
                asset_family="decision",
                market_profile=DEFAULT_DECISION_PROFILE_ID,
                market=DEFAULT_DECISION_MARKET,
                league="nfl",
                sport="football",
                season=str(row.get("season") or ""),
                week_or_date=str(row.get("week") or ""),
                event_id=_normalize_text(row.get("event_id")),
                market_id=_normalize_text(row.get("decision_id")),
                selection=_normalize_text(row.get("decision_id")),
                provider=DEFAULT_DECISION_PROVIDER,
                connector="signal_population",
                schema_version=DECISION_POPULATION_SCHEMA_VERSION,
                lineage_version=_normalize_text(row.get("version_id"), DECISION_TRANSFORMATION_VERSION),
                asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                asset_type="decision_snapshot",
                team_id=_normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                game_id=_normalize_text(row.get("game_id") or row.get("event_id")),
                market_type=DEFAULT_DECISION_MARKET_TYPE,
            )
            alignment_contract = build_time_entity_alignment_certification(
                identity=row_identity,
                rows=[
                    {
                        **dict(row),
                        "asset_id": DEFAULT_DECISION_RESEARCH_ASSET_ID,
                        "asset_family": "decision",
                        "asset_name": DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                        "asset_type": "decision_snapshot" if _normalize_text(row.get("snapshot_kind")) == DECISION_ROW_KIND else "decision_snapshot_batch",
                        "lineage_version": _normalize_text(row.get("version_id"), DECISION_TRANSFORMATION_VERSION),
                        "season": str(row.get("season") or ""),
                        "event_id": _normalize_text(row.get("event_id")),
                        "game_id": _normalize_text(row.get("game_id") or row.get("event_id")),
                        "market_id": _normalize_text(row.get("decision_id")),
                        "provider": DEFAULT_DECISION_PROVIDER,
                        "schema_version": DECISION_POPULATION_SCHEMA_VERSION,
                        "provider_timestamp": _normalize_text(row.get("decision_cutoff_time")),
                        "snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                        "decision_time": _normalize_text(row.get("decision_cutoff_time")),
                        "result_timestamp": source_signal_result_timestamp,
                        "market_profile": DEFAULT_DECISION_PROFILE_ID,
                        "market": DEFAULT_DECISION_MARKET,
                        "market_type": DEFAULT_DECISION_MARKET_TYPE,
                        "league": "nfl",
                        "sport": "football",
                        "week_or_date": str(row.get("week") or ""),
                        "team_id": _normalize_text(row.get("target_team_id") or row.get("home_team_id") or row.get("away_team_id")),
                        "participant_id": "",
                        "selection": _normalize_text(row.get("decision_id")),
                        "connector": "signal_population",
                    }
                ],
                required_fields=(
                    "dataset_id",
                    "dataset_name",
                    "snapshot_id",
                    "batch_id",
                    "decision_id",
                    "decision_name",
                    "decision_readiness_status",
                    "decision_value_json",
                    "decision_context_id",
                    "decision_snapshot_context_id",
                    "source_signal_batch_id",
                    "source_signal_population_summary_id",
                ),
                required_timestamps=(
                    "scheduled_kickoff_time",
                    "decision_cutoff_time",
                    "created_at",
                    "updated_at",
                ),
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                created_at=_utc_now_iso(),
                asset_name=DEFAULT_DECISION_RESEARCH_ASSET_NAME,
                asset_type="decision_snapshot" if _normalize_text(row.get("snapshot_kind")) == DECISION_ROW_KIND else "decision_snapshot_batch",
                lifecycle_state="backtest_ready",
                batch_id=alignment_batch_id,
            )
            alignment_row = build_time_entity_alignment_certification_row(
                identity=row_identity,
                alignment=alignment_contract,
                profile=NFL_AS_SPORTS_PROFILE_INSTANCE,
                source_bundle={
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                raw_acquisition_result={
                    "ok": True,
                    "status": "signal_output_input",
                    "dataset_id": DEFAULT_DECISION_DATASET_ID,
                    "source_name": DEFAULT_DECISION_SOURCE_NAME,
                    "source_type": DEFAULT_DECISION_SOURCE_TYPE,
                    "source_key": DEFAULT_DECISION_SOURCE_KEY,
                    "provider": DEFAULT_DECISION_PROVIDER,
                    "source_file": str(storage.path),
                    "source_event_id": _normalize_text(row.get("event_id")),
                    "source_market_id": _normalize_text(row.get("decision_id")),
                    "source_selection_id": _normalize_text(row.get("decision_id")),
                    "source_snapshot_time": _normalize_text(row.get("decision_cutoff_time")),
                },
                batch_id=alignment_batch_id,
            )
            alignment_validation = validate_time_entity_alignment_certification_row(alignment_row)
            if not alignment_validation["ok"]:
                raise ValueError("; ".join(alignment_validation.get("issues", [])) or "decision alignment validation failed")
            storage.upsert("research_asset_alignment_certifications", alignment_row, key_columns=("alignment_certification_id",))
            decision_alignment_rows_result.append(
                {
                    "ok": alignment_contract.alignment_status == "aligned",
                    "status": alignment_contract.alignment_status,
                    "identity": row_identity.as_dict(),
                    "alignment_certification": alignment_contract.as_dict(),
                    "alignment_certification_row": alignment_row,
                    "validation": alignment_validation,
                }
            )
        lifecycle_rows.append(
            lifecycle_runtime.record_lifecycle_state(
                identity=decision_identity,
                lifecycle_state="backtest_ready",
                lifecycle_reason=f"{DEFAULT_DECISION_RESEARCH_ASSET_NAME} promoted to backtest_ready",
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=_utc_now_iso(),
                certification_result=decision_certification_row,
                dataset_result=decision_dataset_row,
                notes={
                    "batch_id": decision_batch_id,
                    "decision_row_count": len(decision_rows),
                    "decision_definition_count": len(_DECISION_DEFINITIONS),
                    "decision_context_count": len(decision_contexts),
                    "source_signal_batch_id": source_signal_batch_id,
                    "previous_states": ["research_asset_certified", "dataset_certified"],
                    "signal_input_only": True,
                },
            )
        )
        persisted_rows = storage.fetch(
            "decision_rows",
            where="dataset_id = ?",
            params=[DEFAULT_DECISION_DATASET_ID],
            order_by="created_at ASC, snapshot_id ASC",
        )
        persisted_summary_rows = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == DECISION_BATCH_KIND]
        persisted_decision_rows = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == DECISION_ROW_KIND]
        latest_summary_row = dict(summary_row)
        latest_summary_row.setdefault("status", "certified")
        latest_summary_row.setdefault("readiness", "backtest_ready")
        latest_summary_row.setdefault("validation_state", "validated")
        storage.upsert("decision_rows", latest_summary_row, key_columns=("snapshot_id",))
        for row in decision_rows:
            storage.upsert("decision_rows", row, key_columns=("snapshot_id",))
        persisted_rows = storage.fetch(
            "decision_rows",
            where="dataset_id = ?",
            params=[DEFAULT_DECISION_DATASET_ID],
            order_by="snapshot_kind ASC, dataset_row_id ASC, decision_id ASC, snapshot_id ASC",
        )
        decision_rows_persisted = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == DECISION_ROW_KIND]
        summary_rows_persisted = [dict(row) for row in persisted_rows if _normalize_text(row.get("snapshot_kind")) == DECISION_BATCH_KIND]
        summary_row = summary_rows_persisted[-1] if summary_rows_persisted else latest_summary_row
        return build_decision_row_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=DEFAULT_DECISION_DATASET_ID,
            batch_id=decision_batch_id,
            idempotent_reuse=False,
        )
    finally:
        storage.close()


def get_decision_row_population_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_DECISION_DATASET_ID,
    batch_id: str | None = None,
) -> dict[str, Any]:
    return build_decision_row_population_dashboard_snapshot(
        storage_path=storage_path,
        backend=backend,
        dataset_id=dataset_id,
        batch_id=batch_id,
    )


def _decision_population_dashboard_row_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(_normalize_text(row.get("decision_readiness_status")) for row in rows)
    return dict(counts)


def _decision_population_snapshot_base(
    *,
    storage: LocalStorageEngine,
    dataset_id: str,
    batch_id: str | None,
) -> dict[str, Any]:
    batch_rows = storage.fetch(
        "decision_rows",
        where="dataset_id = ? AND snapshot_kind = ?" + (" AND batch_id = ?" if batch_id else ""),
        params=[dataset_id, DECISION_BATCH_KIND, *([batch_id] if batch_id else [])],
        order_by="created_at ASC, snapshot_id ASC",
    ) if storage.table_exists("decision_rows") else []
    latest_batch = dict(batch_rows[-1]) if batch_rows else {}
    decision_rows = storage.fetch(
        "decision_rows",
        where="dataset_id = ? AND snapshot_kind = ?" + (" AND batch_id = ?" if batch_id else ""),
        params=[dataset_id, DECISION_ROW_KIND, *([batch_id] if batch_id else [])],
        order_by="dataset_row_id ASC, decision_id ASC, snapshot_id ASC",
    ) if storage.table_exists("decision_rows") else []
    lineage_rows = storage.fetch(
        "lineage_edges",
        where="dataset_id = ? AND feature_pack = ?",
        params=[dataset_id, DEFAULT_DECISION_RESEARCH_ASSET_ID],
        order_by="created_at ASC, lineage_edge_id ASC",
    ) if storage.table_exists("lineage_edges") else []
    alignment_rows = storage.fetch(
        "research_asset_alignment_certifications",
        where="asset_id = ?",
        params=[DEFAULT_DECISION_RESEARCH_ASSET_ID],
        order_by="created_at ASC, alignment_certification_id ASC",
    ) if storage.table_exists("research_asset_alignment_certifications") else []
    lifecycle_rows = storage.fetch(
        "research_asset_lifecycles",
        where="asset_id = ?",
        params=[DEFAULT_DECISION_RESEARCH_ASSET_ID],
        order_by="created_at ASC, asset_id ASC",
    ) if storage.table_exists("research_asset_lifecycles") else []
    decision_population_summary = dict(latest_batch)
    if not decision_population_summary and decision_rows:
        decision_population_summary = dict(decision_rows[-1])
    source_signal_batch_id = _normalize_text(decision_population_summary.get("source_signal_batch_id"))
    source_signal_snapshot = _load_source_signal_snapshot(storage, batch_id=source_signal_batch_id or None)
    return {
        "batch_rows": [dict(row) for row in batch_rows],
        "decision_rows": [dict(row) for row in decision_rows],
        "lineage_rows": [dict(row) for row in lineage_rows],
        "alignment_rows": [dict(row) for row in alignment_rows],
        "lifecycle_rows": [dict(row) for row in lifecycle_rows],
        "decision_population_summary": decision_population_summary,
        "source_signal_snapshot": source_signal_snapshot,
    }


def build_decision_row_population_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_id: str = DEFAULT_DECISION_DATASET_ID,
    batch_id: str | None = None,
    idempotent_reuse: bool = False,
) -> dict[str, Any]:
    storage = create_local_storage_engine(storage_path or DEFAULT_DECISION_STORAGE_PATH, backend=backend)
    try:
        base = _decision_population_snapshot_base(storage=storage, dataset_id=dataset_id, batch_id=batch_id)
        batch_rows = base["batch_rows"]
        decision_rows = base["decision_rows"]
        lineage_rows = base["lineage_rows"]
        alignment_rows = base["alignment_rows"]
        lifecycle_rows = base["lifecycle_rows"]
        summary = dict(base["decision_population_summary"])
        source_signal_snapshot = dict(base["source_signal_snapshot"])
        if not summary and not decision_rows:
            return _decision_population_missing_snapshot(
                storage=storage,
                dataset_id=dataset_id,
                batch_id=_normalize_text(batch_id),
                status="missing_decision_rows",
                warnings=["decision rows are required"],
            )
        source_signal_summary = dict(source_signal_snapshot.get("signal_population_summary") or {})
        source_signal_rows = [dict(row) for row in source_signal_snapshot.get("signal_rows") or []]
        source_signal_summary_rows = [dict(row) for row in source_signal_snapshot.get("signal_summary_rows") or []]
        decision_definition_count = len(_DECISION_DEFINITIONS)
        decision_context_ids = sorted({str(row.get("decision_context_id")) for row in decision_rows if _normalize_text(row.get("decision_context_id"))})
        decision_value_counts = _decision_population_dashboard_row_counts(decision_rows)
        decision_row_count = len(decision_rows)
        decision_context_count = len(decision_context_ids)
        source_signal_row_count = len(source_signal_rows)
        source_signal_context_count = int(source_signal_snapshot.get("signal_context_count") or len({row.get("decision_context_id") for row in source_signal_rows}))
        summary_row = dict(summary or batch_rows[-1] if batch_rows else {})
        decision_population_summary_id = _normalize_text(summary_row.get("snapshot_id"))
        decision_evidence_package_id = _normalize_text(summary_row.get("evidence_package_id"))
        dataset_certification_status = _normalize_text(source_signal_snapshot.get("dataset_certification_status"), "missing")
        dataset_certification_id = _normalize_text(source_signal_snapshot.get("dataset_certification_id"))
        validation = validate_decision_rows(decision_rows)
        if summary_row:
            summary_row.setdefault("decision_population_summary", dict(summary_row))
            summary_row.setdefault("decision_population_summary_id", decision_population_summary_id)
            summary_row.setdefault("decision_population_summary_row", dict(summary_row))
        join_diagnostics = {
            "source_signal_row_count": source_signal_row_count,
            "source_signal_context_count": source_signal_context_count,
            "decision_row_count": decision_row_count,
            "decision_definition_count": decision_definition_count,
            "decision_context_count": decision_context_count,
            "decision_context_ids": decision_context_ids,
            "decision_value_counts": dict(decision_value_counts),
            "duplicate_snapshot_ids": list(validation.get("duplicate_snapshot_ids", [])),
            "duplicate_decision_keys": list(validation.get("duplicate_decision_keys", [])),
            "source_signal_batch_id": _normalize_text(source_signal_snapshot.get("signal_population_summary", {}).get("batch_id")),
        }
        ready = validation["ok"] and decision_value_counts.get("BACKTEST_ELIGIBLE", 0) == decision_row_count and decision_row_count > 0
        result = {
            "ok": bool(decision_rows) and validation["ok"],
            "status": "certified" if validation["ok"] else "blocked",
            "readiness": "backtest_ready" if ready else "blocked",
            "lifecycle_state": "backtest_ready" if ready else "missing",
            "dataset_id": dataset_id,
            "dataset_name": DEFAULT_DECISION_DATASET_NAME,
            "batch_id": _normalize_text(summary_row.get("batch_id")) or _normalize_text(batch_id),
            "dataset_row_count": len(decision_context_ids),
            "decision_context_count": decision_context_count,
            "decision_definition_count": decision_definition_count,
            "decision_row_count": decision_row_count,
            "decision_rows": decision_rows,
            "decision_summary_rows": [summary_row] if summary_row else [],
            "decision_lineage_edges": lineage_rows,
            "decision_alignment_rows": alignment_rows,
            "decision_lifecycle_rows": lifecycle_rows,
            "decision_validation": validation,
            "validation": validation,
            "decision_population_summary": summary_row,
            "decision_population_summary_id": decision_population_summary_id,
            "decision_evidence_package_id": decision_evidence_package_id,
            "dataset_certification_status": dataset_certification_status,
            "dataset_certification_id": dataset_certification_id,
            "source_signal_snapshot": source_signal_snapshot,
            "source_signal_summary": source_signal_summary,
            "source_signal_rows": source_signal_rows,
            "source_signal_summary_rows": source_signal_summary_rows,
            "source_signal_row_count": source_signal_row_count,
            "source_signal_definition_count": len(list_signal_definition_ids()),
            "source_signal_context_count": source_signal_context_count,
            "source_signal_population_summary_id": _normalize_text(source_signal_snapshot.get("signal_population_summary_id")),
            "source_signal_evidence_package_id": _normalize_text(source_signal_snapshot.get("evidence_package_id")),
            "source_signal_certification_id": _normalize_text(source_signal_snapshot.get("certification_id")),
            "source_signal_dataset_certification_id": _normalize_text(source_signal_snapshot.get("dataset_certification_id")),
            "source_signal_batch_id": _normalize_text(source_signal_snapshot.get("signal_population_summary", {}).get("batch_id")),
            "source_signal_batch_lineage_id": _normalize_text(source_signal_snapshot.get("source_signal_batch_lineage_id")),
            "join_diagnostics": join_diagnostics,
            "registry": summarize_decision_registry(),
            "storage": {
                "backend": storage.backend,
                "path": str(storage.path),
            },
            "unresolved_blockers": list(validation.get("errors", [])),
            "warnings": list(validation.get("errors", [])),
            "idempotent_reuse": bool(idempotent_reuse),
        }
        result["decision_population_summary"]["decision_population_summary"] = dict(summary_row)
        result["decision_population_summary"]["decision_population_summary_id"] = decision_population_summary_id
        result["decision_population_summary"]["decision_population_summary_row"] = dict(summary_row)
        return result
    finally:
        storage.close()


__all__ = [
    "CANONICAL_DECISION_ROW_SNAPSHOT_GRAIN_ID",
    "DECISION_BATCH_KIND",
    "DECISION_DEFINITION_VERSION",
    "DECISION_POPULATION_SCHEMA_VERSION",
    "DECISION_ROW_KIND",
    "DECISION_SUMMARY_ROW_KIND",
    "DECISION_TRANSFORMATION_VERSION",
    "DECISION_USAGE_MODE",
    "DEFAULT_DECISION_DATASET_ID",
    "DEFAULT_DECISION_DATASET_NAME",
    "DEFAULT_DECISION_PORTABILITY_CLASSIFICATION",
    "DEFAULT_DECISION_RESEARCH_ASSET_ID",
    "DEFAULT_DECISION_RESEARCH_ASSET_NAME",
    "build_decision_row_population",
    "build_decision_row_population_dashboard_snapshot",
    "build_decision_snapshot_context",
    "build_decision_snapshot_context_id",
    "build_decision_value_identity",
    "get_decision_definition",
    "get_decision_row_population_snapshot_for_dashboard",
    "list_decision_definition_ids",
    "list_decision_definitions",
    "summarize_decision_registry",
    "validate_decision_registry",
    "validate_decision_rows",
]
