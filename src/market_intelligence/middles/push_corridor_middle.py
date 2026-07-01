from __future__ import annotations

from typing import Any

from ..middle_opportunity_detector import detect_middle_opportunity


def detect_push_corridor_middle(left_offer: dict[str, Any], right_offer: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    result = detect_middle_opportunity(left_offer, right_offer, **kwargs)
    if result.get("candidate_found"):
        zone = result.get("middle_zone") or []
        result["push_corridor"] = bool(any(float(value).is_integer() for value in zone))
    return result
