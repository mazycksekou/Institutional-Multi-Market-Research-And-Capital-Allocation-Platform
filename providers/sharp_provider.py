from __future__ import annotations

from typing import Any

from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)


ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "providers.sharp_provider"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


def _disabled_sharp_enrichment() -> dict[str, Any]:
    return {
        "provider": "sharp",
        "provider_status": "disabled",
        "message": "Sharp enrichment is disabled; connector metadata only",
        "provider_notes": [
            "Sharp live odds access has been retired in favor of the connector boundary.",
            "Legacy compatibility shell returns metadata only.",
        ],
        "data": [],
        "connector_configuration": ODDS_DATA_CONNECTOR_CONFIGURATION.describe(),
        "connector_readiness": dict(ODDS_DATA_CONNECTOR_READINESS),
    }


def enrich_with_sharp(ticket: dict[str, Any]) -> dict[str, Any]:
    payload = _disabled_sharp_enrichment()
    payload["ticket_fields"] = sorted(str(key) for key in ticket.keys()) if isinstance(ticket, dict) else []
    return payload
