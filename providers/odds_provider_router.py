from __future__ import annotations

from typing import Any

from src.services.enrichment_service import EnrichmentService


def enrich_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    """
    LEGACY COMPATIBILITY WRAPPER.

    Canonical owner: src/services/enrichment_service.py

    Retained only as a compatibility hook while legacy references are retired.
    Deletion is blocked until the remaining compatibility proof is complete.
    """
    return EnrichmentService.enrich_ticket(ticket)
