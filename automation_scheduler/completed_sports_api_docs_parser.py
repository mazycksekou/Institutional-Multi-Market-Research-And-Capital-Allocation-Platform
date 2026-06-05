from __future__ import annotations

from typing import Any

from .source_policy_review_common import fetch_public_json, fetch_public_page_text, normalized_domain, stable_hash


def evaluate_completed_sports_api_docs(candidate: dict[str, Any]) -> dict[str, Any]:
    api_docs_url = str(candidate.get("api_docs_url") or "").strip()
    data_dictionary_url = str(candidate.get("data_dictionary_url") or "").strip()
    docs_checked = bool(api_docs_url)
    dict_checked = bool(data_dictionary_url)
    api_response = {"ok": False, "transport": "hard_blocked", "blocked_reason": "api_docs_url_missing"}
    dict_response = {"ok": False, "transport": "hard_blocked", "blocked_reason": "data_dictionary_url_missing"}
    if api_docs_url:
        api_response = fetch_public_page_text(
            source_id=candidate["source_id"],
            domain=normalized_domain(candidate["source_domain"]),
            url=api_docs_url,
            transport="web_scraper_api",
            timeout=45,
        )
    if data_dictionary_url:
        if data_dictionary_url.endswith(".json") or "/api/" in data_dictionary_url:
            dict_response = fetch_public_json(
                source_id=candidate["source_id"],
                domain=normalized_domain(candidate["source_domain"]),
                url=data_dictionary_url,
                transport="residential_proxy",
                timeout=45,
            )
        else:
            dict_response = fetch_public_page_text(
                source_id=candidate["source_id"],
                domain=normalized_domain(candidate["source_domain"]),
                url=data_dictionary_url,
                transport="web_scraper_api",
                timeout=45,
            )
    source_url = str(candidate.get("source_url") or "")
    public_json = source_url.endswith(".json") or "api" in source_url
    public_csv = source_url.endswith(".csv") or "csv" in source_url
    public_api = candidate.get("source_type") in {"public_json_api", "developer_docs_page"}
    return {
        "api_docs_checked": docs_checked,
        "data_dictionary_checked": dict_checked,
        "api_docs_found": bool(api_response.get("ok")),
        "data_dictionary_available": bool(dict_response.get("ok")),
        "endpoint_or_page_exists": bool(api_response.get("ok") or dict_response.get("ok") or candidate.get("source_url")),
        "static_html_available": bool(api_response.get("ok")),
        "public_json_available": public_json,
        "public_csv_available": public_csv,
        "public_parquet_available": source_url.endswith(".parquet"),
        "public_api_available": public_api,
        "requires_browser_rendering": candidate.get("primary_transport") == "web_scraper_api" and candidate.get("source_type") not in {"public_json_api", "open_csv_docs_page"},
        "requires_auth_headers": False,
        "requires_cookies": bool(candidate.get("session_required")),
        "requires_captcha": bool(candidate.get("captcha_required")),
        "rate_limit_observed": False,
        "stable_schema_detected": bool(candidate.get("repo_field_mapping")),
        "data_dictionary_url_hash": stable_hash(data_dictionary_url) if data_dictionary_url else "",
        "api_docs_url_hash": stable_hash(api_docs_url) if api_docs_url else "",
        "oxylabs_used": docs_checked or dict_checked,
        "oxylabs_transport_used": api_response.get("transport") if api_response.get("ok") else dict_response.get("transport"),
        "oxylabs_calls_attempted": (1 if docs_checked else 0) + (1 if dict_checked else 0),
        "oxylabs_calls_successful": (1 if api_response.get("ok") else 0) + (1 if dict_response.get("ok") else 0),
        "oxylabs_calls_failed": (1 if docs_checked and not api_response.get("ok") else 0) + (1 if dict_checked and not dict_response.get("ok") else 0),
    }

