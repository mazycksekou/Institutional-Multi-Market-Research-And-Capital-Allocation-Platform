from __future__ import annotations

from typing import Any


def default_governance_config() -> dict[str, Any]:
    return {
        "human_approval_required": True,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "auto_execution_enabled": False,
        "paper_execution_only": True,
        "full_kelly_auto_execution_allowed": False,
        "roi_target_is_filter_only": True,
        "minimum_scores": {
            "evidence": 70,
            "input_quality_review": 75,
            "input_quality_active": 80,
            "risk_review": 70,
            "risk_active": 80,
            "governance_active": 80,
            "calibration_active": 80,
        },
        "schema_version": "model_governance.v1",
    }
