from __future__ import annotations

from typing import Any

from providers.kalshi_provider import enrich_with_kalshi
from providers.sharp_provider import enrich_with_sharp
from src.core.entity_resolver import normalize_ticket_fields


class EnrichmentService:
    """
    Canonical screenshot/ticket provider-enrichment service.

    This service is the migration target for the legacy synchronous
    providers/odds_provider_router.py path. It preserves the existing
    enrichment contract: sharp context, Kalshi/prediction-market context,
    and explanatory notes.
    """

    @staticmethod
    def enrich_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
        normalized_ticket = normalize_ticket_fields(ticket)
        return {
            "sharp": enrich_with_sharp(normalized_ticket),
            "kalshi": enrich_with_kalshi(normalized_ticket),
            "notes": [
                "Provider data is enrichment only.",
                "Kalshi is treated as prediction market context, not sportsbook odds.",
            ],
        }

    @staticmethod
    async def enrich_ticket_async(ticket: dict[str, Any]) -> dict[str, Any]:
        return EnrichmentService.enrich_ticket(ticket)
