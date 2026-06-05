from __future__ import annotations

from typing import Any

from .source_policy_review_common import fetch_public_page_text, normalized_domain, stable_hash


def _flag(lower: str, markers: tuple[str, ...]) -> bool:
    return any(marker in lower for marker in markers)


def evaluate_completed_sports_terms(candidate: dict[str, Any]) -> dict[str, Any]:
    terms_url = str(candidate.get("terms_url") or "").strip()
    if not terms_url:
        return {
            "terms_checked": False,
            "automated_access_allowed": None,
            "scraping_allowed": None,
            "API_access_preferred": None,
            "noncommercial_only": None,
            "commercial_use_allowed": None,
            "redistribution_allowed": None,
            "derivative_data_allowed": None,
            "caching_allowed": None,
            "attribution_required": None,
            "rate_limits_stated": None,
            "bulk_download_allowed": None,
            "no_database_reconstruction_clause": None,
            "no_competitive_use_clause": None,
            "no_reverse_engineering_clause": None,
            "no_data_mining_clause": None,
            "no_publication_clause": None,
            "copyright_restriction_present": None,
            "personal_use_only": None,
            "research_use_only": None,
            "terms_url_hash": "",
            "source_policy_reviewed": False,
            "exact_blocker_or_allowance": "terms_url_missing",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
        }
    response = fetch_public_page_text(
        source_id=candidate["source_id"],
        domain=normalized_domain(candidate["source_domain"]),
        url=terms_url,
        transport="web_scraper_api",
        timeout=45,
    )
    lower = (response.get("text") or "").lower()
    personal_use_only = _flag(lower, ("personal use only", "personal, non-commercial"))
    noncommercial_only = _flag(lower, ("non-commercial", "noncommercial"))
    no_data_mining = _flag(lower, ("data mining", "data-mining"))
    no_reverse = _flag(lower, ("reverse engineer", "reverse-engineer"))
    no_competitive = _flag(lower, ("competitive use", "compete with", "competitive service"))
    no_database = _flag(lower, ("database", "systematic retrieval"))
    no_publication = _flag(lower, ("publish", "publication"))
    automated_disallowed = _flag(lower, ("automated means", "automated access", "scraper", "bot")) and _flag(lower, ("prohibit", "not", "without"))
    api_preferred = _flag(lower, ("api", "developer")) and _flag(lower, ("preferred", "use our api", "instead of scraping"))
    attribution_required = _flag(lower, ("attribution", "credit"))
    commercial_use_allowed = not (personal_use_only or noncommercial_only)
    scraping_allowed = not (automated_disallowed or no_data_mining or no_database)
    return {
        "terms_checked": True,
        "automated_access_allowed": scraping_allowed,
        "scraping_allowed": scraping_allowed,
        "API_access_preferred": api_preferred,
        "noncommercial_only": noncommercial_only,
        "commercial_use_allowed": commercial_use_allowed,
        "redistribution_allowed": not _flag(lower, ("redistribute", "redistribution prohibited")),
        "derivative_data_allowed": not _flag(lower, ("derivative works prohibited", "no derivative")),
        "caching_allowed": not _flag(lower, ("cache prohibited", "caching prohibited")),
        "attribution_required": attribution_required,
        "rate_limits_stated": _flag(lower, ("rate limit", "request limit")),
        "bulk_download_allowed": not _flag(lower, ("bulk download prohibited", "no bulk")),
        "no_database_reconstruction_clause": no_database,
        "no_competitive_use_clause": no_competitive,
        "no_reverse_engineering_clause": no_reverse,
        "no_data_mining_clause": no_data_mining,
        "no_publication_clause": no_publication,
        "copyright_restriction_present": _flag(lower, ("copyright", "all rights reserved")),
        "personal_use_only": personal_use_only,
        "research_use_only": _flag(lower, ("research use", "academic use")),
        "terms_url_hash": stable_hash(terms_url),
        "source_policy_reviewed": True,
        "exact_blocker_or_allowance": candidate.get("exact_blocker_or_allowance") or ("terms_page_retrieved" if response.get("ok") else str(response.get("blocked_reason") or "terms_fetch_failed")),
        "oxylabs_used": True,
        "oxylabs_transport_used": response.get("transport") or "web_scraper_api",
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1 if response.get("ok") else 0,
        "oxylabs_calls_failed": 0 if response.get("ok") else 1,
    }

