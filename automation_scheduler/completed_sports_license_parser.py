from __future__ import annotations

from typing import Any

from .source_policy_review_common import fetch_public_page_text, normalized_domain, stable_hash


def evaluate_completed_sports_license(candidate: dict[str, Any]) -> dict[str, Any]:
    license_url = str(candidate.get("license_url") or candidate.get("GitHub_LICENSE_url") or "").strip()
    if not license_url:
        return {
            "license_checked": False,
            "license_name_if_any": "",
            "license_confidence": "none",
            "commercial_use_allowed": None,
            "redistribution_allowed": None,
            "derivative_data_allowed": None,
            "license_url_hash": "",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
        }
    domain = normalized_domain(candidate["source_domain"])
    transport = "residential_proxy" if "raw.githubusercontent.com" in license_url or license_url.endswith(".txt") else "web_scraper_api"
    response = fetch_public_page_text(
        source_id=candidate["source_id"],
        domain=domain,
        url=license_url,
        transport=transport,
        headers={"Accept": "text/plain,application/pdf,text/html,*/*"},
        timeout=45,
    )
    lower = (response.get("text") or "").lower()
    if "creative commons" in lower and "by" in lower:
        license_name = "Creative Commons"
        confidence = "medium"
    elif "mit license" in lower:
        license_name = "MIT"
        confidence = "high"
    elif "apache license" in lower:
        license_name = "Apache"
        confidence = "high"
    elif "all rights reserved" in lower:
        license_name = "All rights reserved"
        confidence = "high"
    elif "license" in lower:
        license_name = "Unspecified public license"
        confidence = "low"
    else:
        license_name = ""
        confidence = "none"
    commercial = "non-commercial" not in lower and "personal use only" not in lower
    redistribution = "redistribution prohibited" not in lower and "all rights reserved" not in lower
    derivative = "derivative works prohibited" not in lower and "no derivative" not in lower
    return {
        "license_checked": True,
        "license_name_if_any": license_name,
        "license_confidence": confidence,
        "commercial_use_allowed": commercial,
        "redistribution_allowed": redistribution,
        "derivative_data_allowed": derivative,
        "license_url_hash": stable_hash(license_url),
        "oxylabs_used": True,
        "oxylabs_transport_used": response.get("transport") or transport,
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1 if response.get("ok") else 0,
        "oxylabs_calls_failed": 0 if response.get("ok") else 1,
    }

