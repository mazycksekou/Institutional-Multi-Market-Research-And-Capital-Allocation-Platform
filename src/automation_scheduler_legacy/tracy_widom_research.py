from __future__ import annotations

from typing import Any

from .security_policy import locked_safety_flags


def _has_optional_tw_dependency() -> bool:
    try:
        import tracywidom  # type: ignore  # noqa: F401
    except Exception:
        return False
    return True


def evaluate_tracy_widom_research(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    row = dict(payload or {})
    largest = row.get("largest_eigenvalue")
    bulk = row.get("bulk_edge_estimate")
    sample = row.get("sample_size")
    dimension = row.get("dimension_count")
    try:
        largest_float = float(largest)
        bulk_float = float(bulk)
        sample_int = int(sample)
        dimension_int = int(dimension)
        valid_setup = largest_float > 0 and bulk_float > 0 and sample_int > 1 and dimension_int > 1
    except (TypeError, ValueError):
        largest_float = None
        bulk_float = None
        sample_int = 0
        dimension_int = 0
        valid_setup = False

    if not valid_setup:
        payload_out = {
            "tracy_widom_status": "not_applicable",
            "tw_applicable": False,
            "tw_score": None,
            "tw_tail_probability": None,
            "edge_exceeds_tw_threshold": False,
            "random_extreme_warning": "no_valid_matrix_edge_setup",
            "extreme_value_confidence": "not_applicable",
            "blocked_reason": "missing_largest_eigenvalue_bulk_edge_sample_or_dimension",
        }
    elif not _has_optional_tw_dependency():
        payload_out = {
            "tracy_widom_status": "blocked_missing_dependency",
            "tw_applicable": True,
            "tw_score": None,
            "tw_tail_probability": None,
            "edge_exceeds_tw_threshold": False,
            "random_extreme_warning": "tracy_widom_dependency_missing_do_not_fabricate_tail_probability",
            "extreme_value_confidence": "blocked_missing_dependency",
            "blocked_reason": "optional_tracy_widom_distribution_dependency_missing",
        }
    else:
        # The dependency is intentionally optional. Even when installed, this
        # scaffold does not fabricate probabilities unless a vetted adapter is added.
        payload_out = {
            "tracy_widom_status": "research_only",
            "tw_applicable": True,
            "tw_score": None,
            "tw_tail_probability": None,
            "edge_exceeds_tw_threshold": bool(largest_float is not None and bulk_float is not None and largest_float > bulk_float),
            "random_extreme_warning": "tw_adapter_not_promoted_to_production",
            "extreme_value_confidence": "research_only",
            "blocked_reason": "tw_probability_adapter_not_validated",
        }
    payload_out.update(locked_safety_flags())
    payload_out["provider_write"] = False
    payload_out["execution_allowed"] = False
    payload_out["live_execution_enabled"] = False
    return payload_out
