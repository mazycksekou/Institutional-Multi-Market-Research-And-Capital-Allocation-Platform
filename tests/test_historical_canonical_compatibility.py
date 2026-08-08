from __future__ import annotations

from dataclasses import replace

from src.data.historical_canonical_compatibility import (
    DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY,
    GOVERNED_REVISION,
    LEGACY_NULL_EQUIVALENCE,
    LEGACY_NUMERIC_REPRESENTATION,
    LINEAGE_METADATA,
    SEMANTIC_REUSE,
    TRUE_CONFLICT,
    compare_historical_canonical_rows,
)


def test_source_type_drift_is_classified_as_semantic_reuse() -> None:
    existing = {
        "event_id": "historical_event.1",
        "source_event_id": "oddswarehouse|nfl_basic|66",
        "event_key": "20090913|ATL|MIA",
        "event_date": "2009-09-13",
        "home_team_id": "MIA",
        "away_team_id": "ATL",
        "source_type": "controlled_vendor_workbook",
    }
    incoming = {
        **existing,
        "source_type": "controlled_vendor_file",
    }

    result = compare_historical_canonical_rows(existing, incoming)

    assert result["decision"] == SEMANTIC_REUSE
    assert result["semantic_match"] is True
    assert result["differences"] == [
        {
            "field_name": "source_type",
            "existing_value": "controlled_vendor_workbook",
            "incoming_value": "controlled_vendor_file",
            "classification": LINEAGE_METADATA,
        }
    ]


def test_numeric_and_null_representation_drift_reuse_semantics() -> None:
    existing = {
        "selection_id": "selection.1",
        "market_type": "spread",
        "selection": "away",
        "line_value": "0.0",
        "odds": "-110",
        "available_at": None,
    }
    incoming = {
        "selection_id": "selection.1",
        "market_type": "spread",
        "selection": "away",
        "line_value": 0,
        "odds": -110.0,
        "available_at": "",
    }

    result = compare_historical_canonical_rows(existing, incoming)

    classifications = {
        diff["field_name"]: diff["classification"]
        for diff in result["differences"]
    }
    assert result["decision"] == SEMANTIC_REUSE
    assert classifications["line_value"] == LEGACY_NUMERIC_REPRESENTATION
    assert classifications["odds"] == LEGACY_NUMERIC_REPRESENTATION
    assert classifications["available_at"] == LEGACY_NULL_EQUIVALENCE


def test_semantic_value_change_is_true_conflict_without_revision_policy() -> None:
    existing = {
        "market_id": "historical_market.1",
        "event_id": "historical_event.1",
        "market_type": "spread",
        "selection_count": 2,
        "odds": -110.0,
    }
    incoming = {
        **existing,
        "odds": -115.0,
    }

    result = compare_historical_canonical_rows(existing, incoming)

    assert result["decision"] == TRUE_CONFLICT
    assert result["semantic_difference_fields"] == ["odds"]


def test_revision_policy_can_promote_semantic_change_to_governed_revision() -> None:
    policy = replace(
        DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY,
        revision_permitted_fields=frozenset({"odds"}),
    )
    existing = {
        "market_id": "historical_market.1",
        "event_id": "historical_event.1",
        "market_type": "spread",
        "selection_count": 2,
        "odds": -110.0,
    }
    incoming = {
        **existing,
        "odds": -115.0,
    }

    result = compare_historical_canonical_rows(existing, incoming, policy=policy)

    assert result["decision"] == GOVERNED_REVISION
    assert result["semantic_difference_fields"] == ["odds"]
