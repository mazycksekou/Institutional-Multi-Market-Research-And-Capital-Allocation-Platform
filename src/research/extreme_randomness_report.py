from __future__ import annotations

from typing import Any

from src.data.data_paths import get_storage_health, resolve_base_data_dir
from src.security.policy import locked_safety_flags
from .universality_research_lanes import build_universality_research_lane


def build_extreme_randomness_report(
    *,
    recent_events: list[dict[str, Any]] | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    resolve_base_data_dir(base_data_dir)
    events = [row for row in (recent_events or []) if isinstance(row, dict)]
    universality = build_universality_research_lane(events)
    payload = {
        "ok": True,
        "status": "extreme_randomness_report",
        "major_lesson": "Extreme signals need random-baseline and tail-risk comparison.",
        "red_team_only": True,
        "research_only": True,
        "calibration_only": True,
        "advanced_math_status": {
            "random_matrix_theory": "research_only_dependency_light",
            "tracy_widom": "blocked_missing_dependency_until_optional_adapter_validated",
            "airy_edge_behavior": "documentation_only_research_lane",
            "kpz_universality": "documentation_only_research_lane",
            "large_system_extreme_value_behavior": "research_only",
            "surrogate_null_testing": "calibration_only",
        },
        "allowed_uses": [
            "red_team_warnings",
            "fake_edge_detection",
            "tail_risk_classification",
            "review_priority_downgrade",
            "out_of_distribution_flagging",
            "calibration_research",
            "random_baseline_comparison",
            "strategy_promotion_demotion_evidence",
        ],
        "forbidden_uses": [
            "automatic_approval",
            "automatic_execution",
            "order_creation",
            "bet_creation",
            "provider_write",
            "live_trading",
            "live_wagering",
        ],
        "recent_event_count": len(events),
        "universality": universality,
        "storage_backend": "file",
        "storage_health": get_storage_health(),
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    payload["auto_execution"] = False
    return payload
