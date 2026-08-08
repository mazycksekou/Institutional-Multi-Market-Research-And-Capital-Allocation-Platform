from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


SEMANTIC_REUSE = "SEMANTIC_REUSE"
GOVERNED_REVISION = "GOVERNED_REVISION"
TRUE_CONFLICT = "TRUE_CONFLICT"

SEMANTIC_IDENTITY = "SEMANTIC_IDENTITY"
SEMANTIC_VALUE = "SEMANTIC_VALUE"
LEGACY_NULL_EQUIVALENCE = "LEGACY_NULL_EQUIVALENCE"
LEGACY_NUMERIC_REPRESENTATION = "LEGACY_NUMERIC_REPRESENTATION"
LEGACY_STRING_REPRESENTATION = "LEGACY_STRING_REPRESENTATION"
SCHEMA_VERSION_METADATA = "SCHEMA_VERSION_METADATA"
PARSER_VERSION_METADATA = "PARSER_VERSION_METADATA"
RUNTIME_METADATA = "RUNTIME_METADATA"
LINEAGE_METADATA = "LINEAGE_METADATA"
PROCESSING_TIMESTAMP = "PROCESSING_TIMESTAMP"
DERIVED_METADATA = "DERIVED_METADATA"
UNKNOWN = "UNKNOWN"


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _normalize_text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _observed_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (Mapping, list, tuple, set)):
        return _stable_json(value)
    return value


def _canonical_numeric_token(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return "1" if value else "0"
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None
    normalized = parsed.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


@dataclass(frozen=True, slots=True)
class HistoricalCanonicalCompatibilityPolicy:
    semantic_fingerprint_excluded_fields: frozenset[str] = field(default_factory=frozenset)
    runtime_metadata_fields: frozenset[str] = field(default_factory=frozenset)
    lineage_metadata_fields: frozenset[str] = field(default_factory=frozenset)
    processing_timestamp_fields: frozenset[str] = field(default_factory=frozenset)
    derived_metadata_fields: frozenset[str] = field(default_factory=frozenset)
    schema_version_fields: frozenset[str] = field(default_factory=lambda: frozenset({"schema_version"}))
    parser_version_fields: frozenset[str] = field(default_factory=lambda: frozenset({"parser_version"}))
    numeric_fields: frozenset[str] = field(default_factory=frozenset)
    identity_fields: frozenset[str] = field(default_factory=frozenset)
    revision_permitted_fields: frozenset[str] = field(default_factory=frozenset)
    value_aliases: Mapping[str, Mapping[str, str]] = field(default_factory=dict)

    @property
    def metadata_only_fields(self) -> frozenset[str]:
        return frozenset(
            set(self.semantic_fingerprint_excluded_fields)
            | set(self.runtime_metadata_fields)
            | set(self.lineage_metadata_fields)
            | set(self.processing_timestamp_fields)
            | set(self.derived_metadata_fields)
            | set(self.schema_version_fields)
            | set(self.parser_version_fields)
        )


DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY = HistoricalCanonicalCompatibilityPolicy(
    semantic_fingerprint_excluded_fields=frozenset(
        {
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
            "source_file",
            "source_snapshot_time",
            "snapshot_time",
            "decision_time",
            "certified_at",
            "certification_status",
            "point_in_time_status",
            "leakage_status",
            "status",
            "completeness_score",
            "source_metadata_json",
            "context_json",
            "payload_json",
            "created_at",
            "updated_at",
            "snapshot_id",
            "lineage_id",
            "version_id",
        }
    ),
    runtime_metadata_fields=frozenset(
        {
            "dataset_id",
            "dataset_name",
            "market_profile",
            "profile_id",
            "profile_family",
            "stage_name",
            "batch_id",
        }
    ),
    lineage_metadata_fields=frozenset(
        {
            "source_name",
            "source_type",
            "source_key",
            "source_file",
            "source_metadata_json",
            "context_json",
            "payload_json",
            "snapshot_id",
            "lineage_id",
            "version_id",
        }
    ),
    processing_timestamp_fields=frozenset(
        {
            "source_snapshot_time",
            "snapshot_time",
            "decision_time",
            "certified_at",
            "created_at",
            "updated_at",
        }
    ),
    derived_metadata_fields=frozenset(
        {
            "certification_status",
            "point_in_time_status",
            "leakage_status",
            "status",
            "completeness_score",
        }
    ),
    numeric_fields=frozenset(
        {
            "season",
            "week",
            "neutral_site",
            "final_score_home",
            "final_score_away",
            "margin",
            "total_points",
            "line_value",
            "odds",
            "american_odds",
            "implied_probability",
            "opening_odds",
            "closing_odds",
            "selection_count",
            "mapping_confidence",
            "confidence",
            "home_score",
            "away_score",
            "score_differential",
            "open_line_value",
            "close_line_value",
            "line_movement",
            "open_american_odds",
            "close_american_odds",
            "open_implied_probability",
            "close_implied_probability",
            "open_no_vig_probability",
            "close_no_vig_probability",
            "close_line_movement",
            "win_margin",
            "open_win_margin",
            "close_win_margin",
            "result_margin",
        }
    ),
    identity_fields=frozenset(
        {
            "source_event_id",
            "source_market_id",
            "source_selection_id",
            "event_key",
            "game_id",
            "event_date",
            "home_team_id",
            "away_team_id",
            "team_id",
            "team_role",
            "provider_id",
            "product_id",
            "market_family",
            "market_type",
            "selection",
            "selection_side",
            "book",
            "sportsbook_id",
            "source_stage",
        }
    ),
)


def _semantic_value(field_name: str, value: Any, policy: HistoricalCanonicalCompatibilityPolicy) -> Any:
    if value in (None, ""):
        return ""
    observed = _observed_value(value)
    aliases = policy.value_aliases.get(field_name) or {}
    if isinstance(observed, str) and observed in aliases:
        return aliases[observed]
    if field_name in policy.numeric_fields:
        numeric = _canonical_numeric_token(observed)
        if numeric is not None:
            return numeric
    if isinstance(observed, str):
        return observed
    if isinstance(observed, (Mapping, list, tuple, set)):
        return _stable_json(observed)
    return observed


def _field_classification(field_name: str, policy: HistoricalCanonicalCompatibilityPolicy) -> str:
    if field_name in policy.schema_version_fields:
        return SCHEMA_VERSION_METADATA
    if field_name in policy.parser_version_fields:
        return PARSER_VERSION_METADATA
    if field_name in policy.lineage_metadata_fields:
        return LINEAGE_METADATA
    if field_name in policy.processing_timestamp_fields:
        return PROCESSING_TIMESTAMP
    if field_name in policy.runtime_metadata_fields:
        return RUNTIME_METADATA
    if field_name in policy.derived_metadata_fields:
        return DERIVED_METADATA
    if field_name in policy.identity_fields:
        return SEMANTIC_IDENTITY
    return SEMANTIC_VALUE


def _semantic_row(
    row: Mapping[str, Any],
    policy: HistoricalCanonicalCompatibilityPolicy,
) -> dict[str, Any]:
    return {
        str(field_name): _semantic_value(str(field_name), value, policy)
        for field_name, value in dict(row).items()
        if str(field_name) not in policy.metadata_only_fields
    }


def build_historical_canonical_semantic_fingerprint(
    row: Mapping[str, Any],
    *,
    policy: HistoricalCanonicalCompatibilityPolicy = DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY,
) -> str:
    semantic_row = _semantic_row(row, policy)
    payload = _stable_json(semantic_row)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compare_historical_canonical_rows(
    existing_row: Mapping[str, Any],
    incoming_row: Mapping[str, Any],
    *,
    policy: HistoricalCanonicalCompatibilityPolicy = DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY,
) -> dict[str, Any]:
    differences: list[dict[str, Any]] = []
    semantic_difference_fields: list[str] = []
    metadata_difference_fields: list[str] = []

    all_fields = sorted(set(dict(existing_row)) | set(dict(incoming_row)))
    for field_name in all_fields:
        existing_observed = _observed_value(existing_row.get(field_name))
        incoming_observed = _observed_value(incoming_row.get(field_name))
        if existing_observed == incoming_observed:
            continue

        field_classification = _field_classification(field_name, policy)
        if field_name in policy.metadata_only_fields:
            classification = field_classification
            metadata_difference_fields.append(field_name)
        else:
            existing_semantic = _semantic_value(field_name, existing_row.get(field_name), policy)
            incoming_semantic = _semantic_value(field_name, incoming_row.get(field_name), policy)
            if existing_semantic == incoming_semantic:
                if existing_row.get(field_name) in (None, "") or incoming_row.get(field_name) in (None, ""):
                    classification = LEGACY_NULL_EQUIVALENCE
                elif field_name in policy.numeric_fields:
                    classification = LEGACY_NUMERIC_REPRESENTATION
                else:
                    classification = LEGACY_STRING_REPRESENTATION
            else:
                classification = field_classification
                semantic_difference_fields.append(field_name)

        differences.append(
            {
                "field_name": field_name,
                "existing_value": existing_row.get(field_name),
                "incoming_value": incoming_row.get(field_name),
                "classification": classification,
            }
        )

    existing_fingerprint = build_historical_canonical_semantic_fingerprint(existing_row, policy=policy)
    incoming_fingerprint = build_historical_canonical_semantic_fingerprint(incoming_row, policy=policy)
    semantic_match = existing_fingerprint == incoming_fingerprint

    if semantic_match:
        decision = SEMANTIC_REUSE
    elif semantic_difference_fields and set(semantic_difference_fields).issubset(policy.revision_permitted_fields):
        decision = GOVERNED_REVISION
    else:
        decision = TRUE_CONFLICT

    return {
        "decision": decision,
        "semantic_match": semantic_match,
        "existing_semantic_fingerprint": existing_fingerprint,
        "incoming_semantic_fingerprint": incoming_fingerprint,
        "differences": differences,
        "semantic_difference_fields": semantic_difference_fields,
        "metadata_difference_fields": metadata_difference_fields,
    }


__all__ = [
    "DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY",
    "DERIVED_METADATA",
    "GOVERNED_REVISION",
    "HistoricalCanonicalCompatibilityPolicy",
    "LEGACY_NULL_EQUIVALENCE",
    "LEGACY_NUMERIC_REPRESENTATION",
    "LEGACY_STRING_REPRESENTATION",
    "LINEAGE_METADATA",
    "PARSER_VERSION_METADATA",
    "PROCESSING_TIMESTAMP",
    "RUNTIME_METADATA",
    "SCHEMA_VERSION_METADATA",
    "SEMANTIC_IDENTITY",
    "SEMANTIC_REUSE",
    "SEMANTIC_VALUE",
    "TRUE_CONFLICT",
    "UNKNOWN",
    "build_historical_canonical_semantic_fingerprint",
    "compare_historical_canonical_rows",
]
