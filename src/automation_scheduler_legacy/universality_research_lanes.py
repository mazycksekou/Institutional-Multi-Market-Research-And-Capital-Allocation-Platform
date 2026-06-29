from __future__ import annotations

from collections import defaultdict
from typing import Any

from .security_policy import locked_safety_flags


SUPPORTED_UNIVERSALITY_ASSETS = (
    "prediction_market",
    "sportsbook",
    "stock",
    "crypto",
    "etf",
    "bond_rate",
    "major_asset",
)


def build_universality_research_lane(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (events or []) if isinstance(row, dict)]
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        asset = str(row.get("asset_type") or row.get("asset_class") or "unknown")
        tail = str(row.get("tail_event_type") or row.get("event_type") or "unknown")
        grouped[asset].append(tail)
    similar: dict[str, dict[str, int]] = {}
    for asset, values in grouped.items():
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        similar[asset] = counts
    shared_patterns = {
        tail
        for counts in similar.values()
        for tail, count in counts.items()
        if count > 0 and sum(1 for other in similar.values() if other.get(tail, 0) > 0) >= 2
    }
    cross_asset = bool(shared_patterns)
    confidence = 0.0 if not rows else min(0.75, len(shared_patterns) / max(1, len(SUPPORTED_UNIVERSALITY_ASSETS)))
    payload = {
        "ok": True,
        "status": "universality_research_lane",
        "universality_status": "research_only",
        "cross_asset_pattern_detected": cross_asset,
        "similar_tail_events_by_asset_type": similar,
        "shared_structure_hypothesis": (
            "similar_tail_or_fake_edge_structures_observed_across_assets"
            if cross_asset
            else "insufficient_cross_asset_tail_pattern_overlap"
        ),
        "universality_confidence": round(confidence, 6),
        "research_only": True,
        "red_team_only": True,
        "affects_review_queue": False,
        "affects_execution": False,
        "training_enabled": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload
