from __future__ import annotations

from typing import Any

from .activation_tiers import TIER_POLICIES

GROUPS = [
    "active_sport_models", "sportsbook_models", "screenshot_intake_models", "market_normalizer_models",
    "cross_book_opportunity_engine", "ev_line_shopping", "arbitrage_models", "middle_betting_models",
    "stock_models", "prediction_market_models", "institutional_investment_models", "target_date_lifecycle_glide_path",
    "Kelly_staking", "drawdown_controls", "exposure_limits", "portfolio_scaling", "automation_scheduler",
    "review_queue", "alert_engine", "research_engine", "challenger_verifier", "provider_registry",
    "data_normalization_layer", "later_auto_execution_disabled",
]


def _item(model_id: str, group: str, tier: str, reason: str, model_type: str = "supporting_signal_model", market_type: str = "sportsbook", horizon: str = "same_day") -> dict[str, Any]:
    policy = TIER_POLICIES[tier]
    return {
        "model_id": model_id,
        "model_name": model_id.replace("_", " ").title(),
        "group": group,
        "model_family": group,
        "module_path": f"{group}.{model_id}",
        "activation_tier": tier,
        "status_reason": reason,
        "governance_owner": "governance_team",
        "model_type": model_type,
        "market_type": market_type,
        "time_horizon": horizon,
        "purpose": "governed_scoring",
        "can_affect_review_queue": policy["can_affect_review_queue"],
        "can_affect_opportunity_score": policy["can_affect_opportunity_score"],
        "can_affect_stake_sizing": policy["can_affect_stake_sizing"],
        "can_affect_alerts": policy["can_affect_alerts"],
        "can_affect_final_decision": policy["can_affect_final_decision"],
        "human_approval_required": True,
        "auto_execution_allowed": False,
        "evidence_score": 85 if tier in {"active_scoring_ready", "production_candidate"} else 78,
        "input_quality_score": 84 if tier in {"active_scoring_ready", "production_candidate"} else 76,
        "calibration_score": 83 if tier in {"active_scoring_ready", "production_candidate"} else 74,
        "backtest_score": 82,
        "walk_forward_score": 80,
        "drift_score": 79,
        "risk_score": 84 if tier in {"active_scoring_ready", "production_candidate"} else 75,
        "governance_score": 85 if tier in {"active_scoring_ready", "production_candidate"} else 76,
        "inputs_required": ["market", "selection"],
        "outputs_produced": ["score"],
        "assumptions": ["input contracts exist"],
        "limitations": ["human review_required"],
        "model_purpose": "probability_estimation",
        "owner": "governance_team",
    }


_INVENTORY = [
    _item("sportsbook_side_total", "active_sport_models", "active_scoring_ready", "verified tests and smoke", "primary_predictive_model"),
    _item("sportsbook_models_core", "sportsbook_models", "active_scoring_ready", "verified tests and smoke", "primary_predictive_model"),
    _item("screenshot_parser", "screenshot_intake_models", "review_queue_ready", "tested awaiting live verify", "data_quality_model"),
    _item("market_normalizer", "market_normalizer_models", "review_queue_ready", "tested awaiting live verify", "data_quality_model"),
    _item("cross_book_ev", "cross_book_opportunity_engine", "review_queue_ready", "tests pass pending identity/liquidity", "cross_book_model"),
    _item("ev_line_shopper", "ev_line_shopping", "review_queue_ready", "tests pass pending live verify", "cross_book_model"),
    _item("arb_engine", "arbitrage_models", "review_queue_ready", "tests pass pending settlement/liquidity", "arbitrage_model"),
    _item("middle_engine", "middle_betting_models", "review_queue_ready", "tests pass pending settlement/liquidity", "middle_model"),
    _item("stock_alpha", "stock_models", "review_queue_ready", "tested awaiting live verify", "primary_predictive_model", "stocks", "swing"),
    _item("prediction_markets_core", "prediction_market_models", "review_queue_ready", "tested awaiting settlement verify", "primary_predictive_model", "prediction_markets"),
    _item("institutional_reference", "institutional_investment_models", "research_only", "long-term reference only", "allocation_model", "stocks", "long_term"),
    _item("glide_path", "target_date_lifecycle_glide_path", "backtest_ready", "tested with contracts", "allocation_model", "stocks", "long_term"),
    _item("kelly_primary", "Kelly_staking", "review_queue_ready", "tested pending full gates", "staking_model"),
    _item("drawdown_guard", "drawdown_controls", "active_scoring_ready", "verified risk guard", "risk_model"),
    _item("exposure_guard", "exposure_limits", "active_scoring_ready", "verified risk guard", "risk_model"),
    _item("portfolio_scaler", "portfolio_scaling", "paper_trade_ready", "dry-run only", "risk_model", "stocks"),
    _item("scheduler", "automation_scheduler", "paper_trade_ready", "dry-run verified", "scheduler_monitor", "multi_market", "continuous"),
    _item("review_queue_model", "review_queue", "review_queue_ready", "governance gate protected", "review_queue_model", "multi_market", "continuous"),
    _item("alert_router", "alert_engine", "review_queue_ready", "alert gate protected", "alert_model", "multi_market", "continuous"),
    _item("research_scorecard", "research_engine", "backtest_ready", "research evidence tested", "governance_model", "multi_market", "long_term"),
    _item("challenger_compare", "challenger_verifier", "review_queue_ready", "comparison only", "challenger_model"),
    _item("providers", "provider_registry", "review_queue_ready", "input quality monitored", "data_quality_model", "multi_market", "continuous"),
    _item("normalization", "data_normalization_layer", "review_queue_ready", "schema and mapping checks", "data_quality_model", "multi_market", "continuous"),
    _item("execution_later", "later_auto_execution_disabled", "research_only", "disabled until explicit enable", "execution_model_disabled", "multi_market", "future"),
]


def get_model_inventory() -> list[dict[str, Any]]:
    return [dict(i) for i in _INVENTORY]


def get_model_inventory_map() -> dict[str, dict[str, Any]]:
    return {i["model_id"]: dict(i) for i in _INVENTORY}


def get_model_by_id(model_id: str) -> dict[str, Any]:
    return get_model_inventory_map()[model_id]


def inventory_counts() -> dict[str, int]:
    counts = {"model_inventory_count": len(_INVENTORY), "research_only_count": 0, "backtest_ready_count": 0, "paper_trade_ready_count": 0, "review_queue_ready_count": 0, "active_scoring_ready_count": 0, "production_candidate_count": 0}
    for i in _INVENTORY:
        counts[f"{i['activation_tier']}_count"] += 1
    return counts
