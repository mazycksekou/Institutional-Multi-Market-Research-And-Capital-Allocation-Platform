from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_logbook_ready_row(ticket: dict[str, Any], model_analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sport_key": ticket.get("sport"),
        "event": ticket.get("event"),
        "market": ticket.get("market"),
        "selection": ticket.get("selection"),
        "sportsbook": ticket.get("book"),
        "odds_american": ticket.get("odds_american"),
        "line": ticket.get("line") if ticket.get("line") is not None else ticket.get("total_line"),
        "model_level": model_analysis.get("model_level"),
        "probability_type": model_analysis.get("probability_type"),
        "final_probability": model_analysis.get("true_probability"),
        "implied_probability": model_analysis.get("implied_probability"),
        "edge_percent": model_analysis.get("edge"),
        "decision": "NO_BET",
        "stake": 0,
        "risk_profile": ticket.get("risk_profile"),
        "status": "manual_review_required",
    }

