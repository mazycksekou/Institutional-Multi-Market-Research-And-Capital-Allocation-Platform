from __future__ import annotations

from typing import Any

TIERS = (
    "research_only",
    "backtest_ready",
    "paper_trade_ready",
    "review_queue_ready",
    "active_scoring_ready",
    "production_candidate",
)

TIER_POLICIES: dict[str, dict[str, Any]] = {
    "research_only": {
        "description": "Model exists for reference only.",
        "can_affect_scoring": False,
        "can_affect_stake_sizing": False,
        "can_create_alerts": False,
    },
    "backtest_ready": {
        "description": "Inputs are defined and local backtests are allowed.",
        "can_affect_scoring": False,
        "can_affect_stake_sizing": False,
        "can_create_alerts": False,
    },
    "paper_trade_ready": {
        "description": "Model can run on live-style placeholder data for tracking only.",
        "can_affect_scoring": False,
        "can_affect_stake_sizing": False,
        "can_create_alerts": False,
    },
    "review_queue_ready": {
        "description": "Model can add context to the review queue but cannot decide final action alone.",
        "can_affect_scoring": False,
        "can_affect_stake_sizing": False,
        "can_create_alerts": True,
    },
    "active_scoring_ready": {
        "description": "Model can influence opportunity score without bypassing human approval.",
        "can_affect_scoring": True,
        "can_affect_stake_sizing": False,
        "can_create_alerts": True,
    },
    "production_candidate": {
        "description": "Model can influence score and stake recommendation but not auto-execute.",
        "can_affect_scoring": True,
        "can_affect_stake_sizing": True,
        "can_create_alerts": True,
    },
}


def default_activation_tier() -> str:
    return "research_only"


def tier_rank(tier: str) -> int:
    return TIERS.index(tier)


def can_promote_one_tier(current_tier: str, target_tier: str) -> bool:
    return tier_rank(target_tier) - tier_rank(current_tier) == 1


def tier_allows_review_queue(tier: str) -> bool:
    return tier_rank(tier) >= tier_rank("review_queue_ready")


def tier_allows_active_scoring(tier: str) -> bool:
    return tier_rank(tier) >= tier_rank("active_scoring_ready")


def tier_allows_stake_sizing(tier: str) -> bool:
    return tier_rank(tier) >= tier_rank("production_candidate")

