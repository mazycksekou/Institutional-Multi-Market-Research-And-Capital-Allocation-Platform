from __future__ import annotations

from typing import Any

from .source_policy_review_common import fetch_public_page_text, normalized_domain, stable_hash


def _path_allowed(robots_text: str, target_path: str) -> tuple[bool | None, str]:
    lines = [line.strip() for line in robots_text.splitlines() if line.strip()]
    if not lines:
        return None, "robots_not_found_or_empty"
    in_wildcard = False
    disallow_rules: list[str] = []
    allow_rules: list[str] = []
    crawl_delay_present = False
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            in_wildcard = value == "*" or not value
        elif not in_wildcard:
            continue
        elif key == "disallow":
            disallow_rules.append(value)
        elif key == "allow":
            allow_rules.append(value)
        elif key == "crawl-delay":
            crawl_delay_present = True
    if any(rule and target_path.startswith(rule) for rule in allow_rules):
        return True, "explicit_allow_rule"
    if any(rule and target_path.startswith(rule) for rule in disallow_rules):
        return False, "explicit_disallow_rule"
    if crawl_delay_present:
        return True, "crawl_delay_present_but_not_disallowed"
    return True, "no_matching_disallow_rule"


def evaluate_completed_sports_robots(candidate: dict[str, Any]) -> dict[str, Any]:
    robots_url = str(candidate.get("robots_url") or "").strip()
    if not robots_url:
        return {
            "robots_txt_found": False,
            "robots_allows_target_path": None,
            "robots_disallows_target_path": None,
            "crawl_delay_present": False,
            "sitemap_found": False,
            "user_agent_rules_relevant": False,
            "robots_decision": "not_checked",
            "robots_decision_reason": "robots_url_missing",
            "robots_checked": False,
            "robots_url_hash": "",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
        }
    response = fetch_public_page_text(
        source_id=candidate["source_id"],
        domain=normalized_domain(candidate["source_domain"]),
        url=robots_url,
        transport="residential_proxy",
        headers={"Accept": "text/plain,*/*"},
        timeout=30,
    )
    text = response.get("text") or ""
    allow_value, reason = _path_allowed(text, str(candidate.get("source_path_or_path_pattern") or "/"))
    robots_found = bool(response.get("ok") and text.strip())
    lower = text.lower()
    return {
        "robots_txt_found": robots_found,
        "robots_allows_target_path": allow_value if allow_value is True else False if allow_value is False else None,
        "robots_disallows_target_path": allow_value is False,
        "crawl_delay_present": "crawl-delay:" in lower,
        "sitemap_found": "sitemap:" in lower,
        "user_agent_rules_relevant": "user-agent:" in lower,
        "robots_decision": "allow" if allow_value is True else "block" if allow_value is False else "not_checked",
        "robots_decision_reason": reason,
        "robots_checked": True,
        "robots_url_hash": stable_hash(robots_url),
        "oxylabs_used": True,
        "oxylabs_transport_used": response.get("transport") or "residential_proxy",
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1 if response.get("ok") else 0,
        "oxylabs_calls_failed": 0 if response.get("ok") else 1,
    }

