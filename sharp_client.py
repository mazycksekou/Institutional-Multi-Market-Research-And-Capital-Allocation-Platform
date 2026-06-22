from typing import Any

import requests

from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)

SHARP_BASE_URL = "https://api.sharpapi.io/api/v1"
REQUEST_TIMEOUT = 8

# Canonical odds connector metadata for delete-proof redirection.
ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "sharp_client"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


def _safe_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"text": response.text}


def _provider_response(
    *,
    lookup_id: str,
    url: str,
    response: requests.Response | None = None,
    error: Exception | None = None
) -> dict[str, Any]:
    if error is not None:
        return {
            "ok": False,
            "provider": "sharpapi",
            "lookup_id": lookup_id,
            "result_type": "error",
            "has_actual_odds": False,
            "market": None,
            "orderbook": None,
            "odds": None,
            "raw_response": None,
            "status_code": None,
            "url": url,
            "message": "SharpAPI request failed",
            "error_type": type(error).__name__,
            "error": str(error),
        }

    raw_response = _safe_json(response)
    status_code = response.status_code

    if status_code == 429:
        message = "Provider rate limit reached"
    elif status_code in {401, 403}:
        message = "Provider authentication failed"
    elif status_code == 404:
        message = "Provider resource not found"
    elif status_code >= 500:
        message = "Provider server error"
    elif isinstance(raw_response, dict) and raw_response.get("data") is None:
        message = "Provider returned null data"
    elif response.ok:
        message = "SharpAPI odds lookup completed"
    else:
        message = f"SharpAPI returned HTTP {status_code}"

    odds_data = None
    if isinstance(raw_response, dict):
        odds_data = (
            raw_response.get("data")
            or raw_response.get("odds")
            or raw_response.get("markets")
            or raw_response.get("sportsbooks")
            or raw_response.get("books")
        )
    elif isinstance(raw_response, list):
        odds_data = raw_response

    has_actual_odds = bool(odds_data)

    return {
        "ok": bool(response.ok and has_actual_odds),
        "provider": "sharpapi",
        "lookup_id": lookup_id,
        "result_type": "odds" if has_actual_odds else "no_data",
        "has_actual_odds": has_actual_odds,
        "market": None,
        "orderbook": None,
        "odds": odds_data,
        "raw_response": raw_response,
        "status_code": status_code,
        "url": response.url,
        "message": message,
        "error_type": None if response.ok else "HTTPError",
        "error": None if response.ok else str(raw_response),
    }


def get_sharp_active_events(
    *,
    api_key: str,
    sport: str,
    league: str,
    session: requests.Session | None = None,
    limit: int = 20
) -> dict[str, Any]:
    url = f"{SHARP_BASE_URL}/events"
    params = {
        "sport": sport,
        "league": league,
        "limit": limit,
    }
    headers = {"X-API-Key": api_key}
    http = session or requests.Session()

    try:
        response = http.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        raw_response = _safe_json(response)
    except Exception as error:
        return {
            "ok": False,
            "provider": "sharpapi",
            "status_code": None,
            "url": url,
            "raw_response": None,
            "data": [],
            "message": "SharpAPI active events request failed",
            "error_type": type(error).__name__,
            "error": str(error),
        }

    data = raw_response.get("data") if isinstance(raw_response, dict) else raw_response
    if not isinstance(data, list):
        data = []

    if response.status_code == 429:
        message = "Provider rate limit reached"
    elif response.ok:
        message = "SharpAPI active events lookup completed"
    else:
        message = f"SharpAPI returned HTTP {response.status_code}"

    return {
        "ok": response.ok,
        "provider": "sharpapi",
        "status_code": response.status_code,
        "url": response.url,
        "raw_response": raw_response,
        "data": data,
        "message": message,
        "error_type": None if response.ok else "HTTPError",
        "error": None if response.ok else str(raw_response),
    }


def get_sharp_event_odds(
    *,
    api_key: str,
    event_id: str,
    session: requests.Session | None = None
) -> dict[str, Any]:
    url = f"{SHARP_BASE_URL}/events/{event_id}/odds"
    headers = {"X-API-Key": api_key}
    params = {
        "sportsbook": "draftkings,fanduel,betmgm",
        "market": "moneyline",
        "limit": 50,
    }
    http = session or requests.Session()

    try:
        response = http.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        return _provider_response(lookup_id=event_id, url=url, response=response)
    except Exception as error:
        return _provider_response(lookup_id=event_id, url=url, error=error)
