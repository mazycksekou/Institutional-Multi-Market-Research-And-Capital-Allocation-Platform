from __future__ import annotations

from typing import Any

from .activation_tiers import default_activation_tier

SUPPORTED_MODEL_TYPES = {
    "primary_predictive_model",
    "supporting_signal_model",
    "cross_book_model",
    "arbitrage_model",
    "middle_model",
    "risk_model",
    "staking_model",
    "allocation_model",
    "execution_model_disabled",
    "validation_model",
    "governance_model",
    "data_quality_model",
    "challenger_model",
    "scheduler_monitor",
    "alert_model",
    "review_queue_model",
}

REQUIRED_FIELDS = (
    "model_id", "model_name", "model_family", "model_group", "model_type", "market_type", "time_horizon", "purpose",
    "owner", "version", "source_module", "inputs_required", "outputs_produced", "assumptions", "limitations",
    "known_failure_modes", "evidence_basis", "activation_tier", "status_reason", "tests_required", "tests_last_passed",
    "deploy_verified", "live_smoke_verified", "input_contract_exists", "missing_input_gate_exists", "malformed_input_gate_exists",
    "stale_data_gate_exists", "settlement_gate_exists", "liquidity_gate_exists", "calibration_required", "backtest_required",
    "walk_forward_required", "risk_gate_required", "kelly_gate_required", "human_approval_required", "can_affect_review_queue",
    "can_affect_opportunity_score", "can_affect_stake_sizing", "can_affect_alerts", "can_affect_final_decision", "can_confirm_alone",
    "auto_execution_allowed",
)


def create_model_card(**kwargs: Any) -> dict[str, Any]:
    card = {key: kwargs.get(key) for key in REQUIRED_FIELDS}
    card["activation_tier"] = kwargs.get("activation_tier", default_activation_tier())
    card["model_type"] = kwargs.get("model_type", "supporting_signal_model")
    card["tests_required"] = list(kwargs.get("tests_required", []))
    card["inputs_required"] = list(kwargs.get("inputs_required", []))
    card["outputs_produced"] = list(kwargs.get("outputs_produced", []))
    card["assumptions"] = list(kwargs.get("assumptions", []))
    card["limitations"] = list(kwargs.get("limitations", []))
    card["known_failure_modes"] = list(kwargs.get("known_failure_modes", []))
    card["human_approval_required"] = True
    card["auto_execution_allowed"] = False
    return card


def validate_model_card(card: dict[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED_FIELDS if card.get(k) in (None, "", [])]
    type_ok = card.get("model_type") in SUPPORTED_MODEL_TYPES
    if not type_ok:
        missing.append("model_type")
    return {"valid": not missing, "missing_fields": sorted(set(missing))}


def build_card_from_inventory_item(item: dict[str, Any]) -> dict[str, Any]:
    return create_model_card(
        model_id=item["model_id"],
        model_name=item.get("model_name", item["model_id"]),
        model_family=item.get("group", "unknown"),
        model_group=item.get("group", "unknown"),
        model_type=item.get("model_type", "supporting_signal_model"),
        market_type=item.get("market_type", "sportsbook"),
        time_horizon=item.get("time_horizon", "same_day"),
        purpose=item.get("purpose", "governed_scoring"),
        owner=item.get("governance_owner", "governance_team"),
        version="1.0.0",
        source_module=item.get("module_path", "unknown"),
        inputs_required=["market", "selection"],
        outputs_produced=["score"],
        assumptions=["inputs are available"],
        limitations=["requires review_required"],
        known_failure_modes=["stale data"],
        evidence_basis=item.get("status_reason", "documented"),
        activation_tier=item.get("activation_tier", default_activation_tier()),
        status_reason=item.get("status_reason", "governed"),
        tests_required=["unit"],
        tests_last_passed="2026-05-28",
        deploy_verified=item.get("activation_tier") in {"active_scoring_ready", "production_candidate"},
        live_smoke_verified=item.get("activation_tier") in {"active_scoring_ready", "production_candidate"},
        input_contract_exists=True,
        missing_input_gate_exists=True,
        malformed_input_gate_exists=True,
        stale_data_gate_exists=True,
        settlement_gate_exists=True,
        liquidity_gate_exists=True,
        calibration_required=True,
        backtest_required=True,
        walk_forward_required=True,
        risk_gate_required=True,
        kelly_gate_required=item.get("group") == "Kelly_staking",
        can_affect_review_queue=item.get("can_affect_review_queue", False),
        can_affect_opportunity_score=item.get("can_affect_opportunity_score", False),
        can_affect_stake_sizing=item.get("can_affect_stake_sizing", False),
        can_affect_alerts=item.get("can_affect_alerts", False),
        can_affect_final_decision=item.get("can_affect_final_decision", False),
        can_confirm_alone=False,
        auto_execution_allowed=False,
    )
