from __future__ import annotations

import importlib.util
from typing import Any, Mapping

from .secret_safety import redact_sensitive
from .security_policy import locked_safety_flags


def _dependency_available() -> bool:
    return bool(importlib.util.find_spec("ripser") or importlib.util.find_spec("gudhi"))


def run_topological_red_team(
    candidate: Mapping[str, Any] | None = None,
    *,
    historical_records: list[Mapping[str, Any]] | None = None,
    dependency_available: bool | None = None,
) -> dict[str, Any]:
    redact_sensitive(dict(candidate or {}))
    records = [row for row in (historical_records or []) if isinstance(row, Mapping)]
    available = _dependency_available() if dependency_available is None else bool(dependency_available)
    if not available:
        return {
            "ok": True,
            "status": "blocked_missing_dependency",
            "topological_risk": "data_insufficient",
            "persistence_feature_count": 0,
            "persistent_homology_status": "blocked_missing_dependency",
            "barcode_summary": {},
            "wasserstein_distance_to_profitable_region": None,
            "topology_confidence_score": 0.0,
            "topology_no_bet_reasons": ["persistent_homology_dependency_missing"],
            "insufficient_sample": len(records) < 25,
            "blocked_reason": "blocked_missing_dependency:persistent_homology_library",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    if len(records) < 25:
        return {
            "ok": True,
            "status": "blocked_insufficient_data",
            "topological_risk": "data_insufficient",
            "persistence_feature_count": 0,
            "persistent_homology_status": "blocked_insufficient_data",
            "barcode_summary": {},
            "wasserstein_distance_to_profitable_region": None,
            "topology_confidence_score": 0.0,
            "topology_no_bet_reasons": ["insufficient_sample_for_persistent_homology"],
            "insufficient_sample": True,
            "blocked_reason": "historical_record_count_below_25",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    return {
        "ok": True,
        "status": "research_only_not_computed",
        "topological_risk": "data_insufficient",
        "persistence_feature_count": 0,
        "persistent_homology_status": "research_only_not_computed",
        "barcode_summary": {},
        "wasserstein_distance_to_profitable_region": None,
        "topology_confidence_score": 0.0,
        "topology_no_bet_reasons": ["persistent_homology_not_enabled_without_explicit_approval"],
        "insufficient_sample": False,
        "blocked_reason": "heavy_topology_computation_not_enabled",
        "red_team_only": True,
        **locked_safety_flags(),
    }
