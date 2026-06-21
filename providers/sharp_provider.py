from __future__ import annotations

import os
from typing import Any

import requests

from src.providers.compat import available, provider_error, unavailable


def enrich_with_sharp(ticket: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("SHARP_API_KEY", "").strip()
    base_url = os.getenv("SHARP_API_BASE_URL", "").strip().rstrip("/")
    if not api_key or not base_url:
        return unavailable("sharp")

    params = {
        "sport": ticket.get("sport"),
        "league": ticket.get("league"),
        "event": ticket.get("event"),
        "market": ticket.get("market"),
        "selection": ticket.get("selection"),
    }
    try:
        response = requests.get(
            f"{base_url}/odds",
            headers={"X-API-Key": api_key},
            params={k: v for k, v in params.items() if v not in (None, "")},
            timeout=8,
        )
        response.raise_for_status()
        raw = response.json()
    except Exception as exc:
        return provider_error(
            "sharp",
            f"Sharp API call failed: {type(exc).__name__}",
            ["Sharp provider failed but analysis continued"],
        )

    data = raw.get("data") if isinstance(raw, dict) else raw
    return available("sharp", data or [], source="sharp")
