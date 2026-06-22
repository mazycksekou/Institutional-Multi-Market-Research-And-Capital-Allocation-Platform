from __future__ import annotations

from typing import Any

from src.connectors.errors import ConnectorDisabledError
from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)

SHARP_BASE_URL = "https://api.sharpapi.io/api/v1"
REQUEST_TIMEOUT = 8

ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "sharp_client"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


def _disabled_message(action: str) -> str:
    return f"Sharp odds client {action} is disabled; use src.connectors.odds_data metadata only"


def get_sharp_active_events(
    *,
    api_key: str,
    sport: str,
    league: str,
    session: Any | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    raise ConnectorDisabledError(_disabled_message("active events lookup"))


def get_sharp_event_odds(
    *,
    api_key: str,
    event_id: str,
    session: Any | None = None,
) -> dict[str, Any]:
    raise ConnectorDisabledError(_disabled_message("event odds lookup"))
