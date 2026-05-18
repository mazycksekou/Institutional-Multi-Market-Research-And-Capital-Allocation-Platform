from __future__ import annotations

from typing import Any

from .kalshi_provider import enrich_with_kalshi
from .sharp_provider import enrich_with_sharp


def enrich_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    return {
        "sharp_api": enrich_with_sharp(ticket),
        "kalshi": enrich_with_kalshi(ticket),
        "notes": [
            "Provider data is enrichment only.",
            "Kalshi is treated as prediction market context, not sportsbook odds.",
        ],
    }

