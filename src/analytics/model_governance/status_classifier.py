from __future__ import annotations

from typing import Any


def classify_model_status(*, is_existing_verified_sport_model: bool = False, tests_passed: bool = False, input_contract_exists: bool = False, deploy_verified: bool = False, live_smoke_verified: bool = False, evidence_score: float = 0, is_scheduler_model: bool = False, has_dry_run_evidence: bool = False, is_institutional_allocation_model: bool = False, as_short_term: bool = False, supporting_signal: bool = False) -> dict[str, Any]:
    if is_existing_verified_sport_model and tests_passed and input_contract_exists and deploy_verified and live_smoke_verified:
        tier = "active_scoring_ready"
    elif is_scheduler_model:
        tier = "review_queue_ready" if tests_passed and has_dry_run_evidence else "paper_trade_ready"
    elif is_institutional_allocation_model:
        tier = "review_queue_ready" if tests_passed and input_contract_exists and not as_short_term else "research_only"
    elif tests_passed and input_contract_exists:
        tier = "review_queue_ready" if not live_smoke_verified else "active_scoring_ready"
    else:
        tier = "research_only"
    return {"activation_tier": tier, "can_confirm_alone": False if supporting_signal else tier == "production_candidate"}
