from __future__ import annotations

from typing import Any

from ..middle_opportunity_detector import detect_middle_opportunity

_KEY_NUMBERS = (3, 7, 10, 14)


def detect_key_number_middle(left_offer: dict[str, Any], right_offer: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    result = detect_middle_opportunity(left_offer, right_offer, **kwargs)
    if result.get("candidate_found"):
        zone = result.get("middle_zone") or []
        result["key_numbers_hit"] = [number for number in _KEY_NUMBERS if len(zone) == 2 and zone[0] <= number <= zone[1]]
    return result
