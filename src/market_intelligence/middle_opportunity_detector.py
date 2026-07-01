from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import normalize_market_name, normalize_offer, normalize_selection_name
from src.data.market_identity_resolver import resolve_market_identity
from src.core.opportunity_scanner import detect_middle_from_normalized_offers


def detect_middle_opportunity(
    left_offer: dict[str, Any],
    right_offer: dict[str, Any],
    *,
    stake_per_side: float = 100.0,
    market_identity_confidence: float | None = None,
    stale_data_risk: bool = False,
    max_timestamp_skew_seconds: int = 120,
    model_distribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    left = normalize_offer(left_offer)
    right = normalize_offer(right_offer)
    market = normalize_market_name(left.get("market"))
    confidence = market_identity_confidence if market_identity_confidence is not None else resolve_market_identity(left, right)["confidence"]
    if left.get("event_name") != right.get("event_name") or normalize_market_name(right.get("market")) != market:
        return {"candidate_found": False, "reason": "watch_recheck_market_identity"}
    if confidence < 85:
        return {"candidate_found": False, "reason": "watch_recheck_market_identity"}
    if stale_data_risk:
        return {"candidate_found": False, "reason": "watch_recheck_stale_data"}
    left_ts = left_offer.get("timestamp")
    right_ts = right_offer.get("timestamp")
    if isinstance(left_ts, (int, float)) and isinstance(right_ts, (int, float)) and abs(int(left_ts) - int(right_ts)) > max_timestamp_skew_seconds:
        return {"candidate_found": False, "reason": "watch_recheck_timestamp_mismatch"}

    left["selection"] = normalize_selection_name(left["selection"])
    right["selection"] = normalize_selection_name(right["selection"])
    return detect_middle_from_normalized_offers(
        left,
        right,
        market=market,
        confidence=float(confidence),
        stake_per_side=stake_per_side,
        model_distribution=model_distribution,
    )
