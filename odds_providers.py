from typing import Any

import requests

from kalshi_client import get_kalshi_market_snapshot
from sharp_client import get_sharp_event_odds


def lookup_provider_odds(
    *,
    provider_hint: str,
    lookup_id: str,
    sharp_api_key: str,
    session: requests.Session | None = None
) -> dict[str, Any]:
    provider = provider_hint.lower()

    if provider == "kalshi":
        return get_kalshi_market_snapshot(lookup_id)

    return get_sharp_event_odds(
        api_key=sharp_api_key,
        event_id=lookup_id,
        session=session
    )
