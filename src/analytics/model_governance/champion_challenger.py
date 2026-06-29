from __future__ import annotations

from typing import Any


def compare_champion_challenger(*, champion: dict[str, float], challenger: dict[str, float], minimum_samples: int = 100) -> dict[str, Any]:
    samples = min(int(champion.get("sample_size", 0)), int(challenger.get("sample_size", 0)))
    if samples < minimum_samples:
        outcome = "needs_more_data"
    elif challenger.get("settlement_failures", 0) > champion.get("settlement_failures", 0) or challenger.get("liquidity_failures", 0) > champion.get("liquidity_failures", 0):
        outcome = "governance_blocked"
    elif challenger.get("calibration", 0) > champion.get("calibration", 0) and challenger.get("risk_adjusted", 0) > champion.get("risk_adjusted", 0):
        outcome = "challenger_promoted_to_review"
    elif challenger.get("risk_adjusted", 0) < champion.get("risk_adjusted", 0):
        outcome = "challenger_rejected"
    else:
        outcome = "champion_kept"
    return {"decision": outcome, "champion": champion, "challenger": challenger, "promotion_requires_gate": True}
