from typing import Any

import requests

from sharp_client import get_sharp_event_odds


def lookup_provider_odds(
    *,
    provider_hint: str,
    lookup_id: str,
    sharp_api_key: str,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    if provider_hint.lower() == "kalshi":
        return {
            "ok": False,
            "result_type": "no_data",
            "has_actual_odds": False,
            "message": "Kalshi fallback is disabled for normal sports betting endpoints.",
            "error_type": "KALSHI_DISABLED",
        }

    return get_sharp_event_odds(
        api_key=sharp_api_key,
        event_id=lookup_id,
        session=session,
    )
