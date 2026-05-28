from __future__ import annotations

TIERS = (
    "research_only",
    "backtest_ready",
    "paper_trade_ready",
    "review_queue_ready",
    "active_scoring_ready",
    "production_candidate",
)

TIER_POLICIES = {
    "research_only": {
        "can_affect_review_queue": False,
        "can_affect_opportunity_score": False,
        "can_affect_stake_sizing": False,
        "can_affect_alerts": False,
        "can_affect_final_decision": False,
    },
    "backtest_ready": {
        "can_affect_review_queue": False,
        "can_affect_opportunity_score": False,
        "can_affect_stake_sizing": False,
        "can_affect_alerts": False,
        "can_affect_final_decision": False,
    },
    "paper_trade_ready": {
        "can_affect_review_queue": False,
        "can_affect_opportunity_score": False,
        "can_affect_stake_sizing": False,
        "can_affect_alerts": False,
        "can_affect_final_decision": False,
    },
    "review_queue_ready": {
        "can_affect_review_queue": True,
        "can_affect_opportunity_score": False,
        "can_affect_stake_sizing": False,
        "can_affect_alerts": True,
        "can_affect_final_decision": False,
    },
    "active_scoring_ready": {
        "can_affect_review_queue": True,
        "can_affect_opportunity_score": True,
        "can_affect_stake_sizing": False,
        "can_affect_alerts": True,
        "can_affect_final_decision": False,
    },
    "production_candidate": {
        "can_affect_review_queue": True,
        "can_affect_opportunity_score": True,
        "can_affect_stake_sizing": True,
        "can_affect_alerts": True,
        "can_affect_final_decision": True,
    },
}


def default_activation_tier() -> str:
    return "research_only"


def tier_rank(tier: str) -> int:
    return TIERS.index(tier)


def can_promote_one_tier(current_tier: str, target_tier: str) -> bool:
    return current_tier in TIERS and target_tier in TIERS and tier_rank(target_tier) - tier_rank(current_tier) == 1


def tier_allows_review_queue(tier: str) -> bool:
    return bool(TIER_POLICIES.get(tier, {}).get("can_affect_review_queue"))


def tier_allows_active_scoring(tier: str) -> bool:
    return bool(TIER_POLICIES.get(tier, {}).get("can_affect_opportunity_score"))


def tier_allows_stake_sizing(tier: str) -> bool:
    return bool(TIER_POLICIES.get(tier, {}).get("can_affect_stake_sizing"))
