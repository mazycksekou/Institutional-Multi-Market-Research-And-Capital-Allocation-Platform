from __future__ import annotations

from typing import Any


def evaluate_input_quality(**kwargs: Any) -> dict[str, Any]:
    missing = int(kwargs.get("missing_inputs", 0))
    malformed = int(kwargs.get("malformed_inputs", 0))
    stale = int(kwargs.get("stale_inputs", 0))
    score = 100 - (missing * 25 + malformed * 40 + stale * 20)
    score = max(0, min(100, score))
    blocked = malformed > 0 or missing > 0
    if stale > 0 and kwargs.get("activation_tier") == "active_scoring_ready":
        blocked = True
    if float(kwargs.get("market_identity_confidence", 100)) < 80 and kwargs.get("is_cross_book", False):
        blocked = True
    return {**kwargs, "input_quality_score": score, "blocked": blocked, "input_quality_gate_result": "blocked_by_governance" if blocked else "approved"}
