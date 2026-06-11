from __future__ import annotations

from typing import Any

from src.services.enrichment_service import EnrichmentService


def enrich_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    """
    LEGACY COMPATIBILITY WRAPPER.

    Canonical owner: src/services/enrichment_service.py

    Retained because screenshot_intake.py imports this function and multiple
    tests patch providers.odds_provider_router.enrich_ticket.

    Planned deletion condition:
    delete only after screenshot_intake.py and tests migrate to the canonical
    enrichment service path.
    """
    return EnrichmentService.enrich_ticket(ticket)
