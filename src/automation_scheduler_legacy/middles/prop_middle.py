from __future__ import annotations

from typing import Any

from ..middle_opportunity_detector import detect_middle_opportunity


def detect_prop_middle(left_offer: dict[str, Any], right_offer: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return detect_middle_opportunity(left_offer, right_offer, **kwargs)
