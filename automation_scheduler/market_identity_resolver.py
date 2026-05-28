from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import (
    normalize_entity_name,
    normalize_event_name,
    normalize_line_value,
    normalize_market_name,
    normalize_selection_name,
)


def resolve_market_identity(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_event = normalize_event_name(left.get("event_name") or left.get("event"))
    right_event = normalize_event_name(right.get("event_name") or right.get("event"))
    left_market = normalize_market_name(left.get("market"))
    right_market = normalize_market_name(right.get("market"))
    left_selection = normalize_selection_name(left.get("selection"))
    right_selection = normalize_selection_name(right.get("selection"))
    left_participant = normalize_entity_name(left.get("participant") or left.get("team") or left.get("player") or left_selection)
    right_participant = normalize_entity_name(right.get("participant") or right.get("team") or right.get("player") or right_selection)
    left_line = normalize_line_value(left.get("line"))
    right_line = normalize_line_value(right.get("line"))

    reasons: list[str] = []
    score = 0

    event_match = bool(left_event and left_event == right_event)
    market_match = bool(left_market and left_market == right_market)
    selection_match = bool(left_selection == right_selection and left_participant == right_participant)

    if event_match:
        score += 40
    else:
        reasons.append("event_mismatch")
    if market_match:
        score += 30
    else:
        reasons.append("market_mismatch")
    if selection_match:
        score += 20
    elif left_market == right_market == "total" and {left_selection, right_selection} <= {"over", "under"}:
        score += 10
        reasons.append("opposing_total_selections")
    elif left_market == right_market == "spread":
        if left_participant != right_participant:
            score += 10
            reasons.append("opposing_spread_sides")
        else:
            reasons.append("selection_mismatch")
    else:
        reasons.append("selection_mismatch")

    line_delta = None
    if left_line is not None and right_line is not None:
        line_delta = abs(float(left_line) - float(right_line))
        if line_delta == 0:
            score += 10
        elif left_market in {"spread", "total"} and line_delta <= 4:
            score += 5
        else:
            reasons.append("line_gap")

    same_market_identity = score >= 85 and event_match and market_match and (
        selection_match or left_market in {"spread", "total"}
    )
    if not same_market_identity and score >= 85:
        reasons.append("confidence_without_identity")

    return {
        "same_event": event_match,
        "same_market": market_match,
        "same_selection": selection_match,
        "confidence": max(0, min(100, score)),
        "same_market_identity": same_market_identity,
        "line_delta": line_delta,
        "reasons": reasons,
    }
