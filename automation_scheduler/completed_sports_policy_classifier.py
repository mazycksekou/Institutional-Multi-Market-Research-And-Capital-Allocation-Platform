from __future__ import annotations

from typing import Any

from .source_policy_review_common import FINAL_POLICY_DECISIONS, FINAL_SOURCE_STATES, stable_hash, url_hash


def map_policy_decision_to_final_state(candidate: dict[str, Any], decision: str) -> str:
    if decision == "accepted_for_automated_normalized_backfill":
        return "free_open_backfilled"
    if decision == "accepted_for_postmatch_training_only":
        return "free_open_postmatch_training_only"
    if decision in {"accepted_for_metadata_only", "accepted_for_attribution_only"}:
        return "free_open_metadata_only"
    if decision == "accepted_for_manual_import_only":
        return "manual_import_required"
    if decision == "rejected_policy_blocked":
        if candidate.get("policy_mode") == "paid":
            return "paid_subscription_required"
        return "policy_blocked"
    if decision == "rejected_robots_blocked":
        return "robots_blocked"
    if decision == "rejected_terms_blocked":
        if candidate.get("policy_mode") == "paid":
            return "paid_subscription_required"
        return "terms_blocked"
    if decision == "rejected_login_paywall_captcha":
        return "login_paywall_captcha_blocked"
    if decision == "license_terms_unclear":
        return "license_terms_unclear"
    if decision == "unavailable_after_exhaustive_search":
        return "unavailable_after_exhaustive_search"
    if decision == "rejected_duplicate_source":
        return "obsolete_or_duplicate"
    if decision == "rejected_upstream_source_unclear":
        return "license_terms_unclear"
    if decision == "rejected_unstable_schema":
        return "policy_blocked"
    return "policy_blocked"


def classify_completed_sports_source(
    candidate: dict[str, Any],
    *,
    source_page: dict[str, Any],
    robots_review: dict[str, Any],
    terms_review: dict[str, Any],
    license_review: dict[str, Any],
    api_docs_review: dict[str, Any],
) -> dict[str, Any]:
    policy_mode = str(candidate.get("policy_mode") or "metadata_only")
    if policy_mode == "blocked":
        decision = "rejected_policy_blocked"
    elif policy_mode == "paid":
        decision = "rejected_terms_blocked"
    elif policy_mode == "manual_only":
        decision = "accepted_for_manual_import_only"
    elif policy_mode == "metadata_only":
        decision = "accepted_for_metadata_only"
    elif policy_mode == "automated_backfill":
        decision = "accepted_for_automated_normalized_backfill"
    elif policy_mode == "postmatch_only":
        decision = "accepted_for_postmatch_training_only"
    elif policy_mode == "license_unclear":
        decision = "license_terms_unclear"
    elif policy_mode == "duplicate":
        decision = "rejected_duplicate_source"
    elif policy_mode == "unavailable":
        decision = "unavailable_after_exhaustive_search"
    elif policy_mode == "upstream_unclear":
        decision = "rejected_upstream_source_unclear"
    else:
        decision = "rejected_unstable_schema"
    if robots_review.get("robots_decision") == "block" and decision not in {
        "rejected_policy_blocked",
        "license_terms_unclear",
        "rejected_duplicate_source",
        "unavailable_after_exhaustive_search",
    }:
        decision = "rejected_robots_blocked"
    if terms_review.get("scraping_allowed") is False and decision in {
        "accepted_for_automated_normalized_backfill",
        "accepted_for_postmatch_training_only",
        "accepted_for_metadata_only",
    }:
        decision = "rejected_terms_blocked"
    if candidate.get("login_required") or candidate.get("paywall_required") or candidate.get("captcha_required") or candidate.get("session_required"):
        decision = "rejected_login_paywall_captcha"
    final_state = map_policy_decision_to_final_state(candidate, decision)
    if decision not in FINAL_POLICY_DECISIONS:
        raise ValueError(f"Unsupported completed-sports policy decision: {decision}")
    if final_state not in FINAL_SOURCE_STATES:
        raise ValueError(f"Unsupported completed-sports final state: {final_state}")
    exact_reason = (
        candidate.get("exact_blocker_or_allowance")
        or terms_review.get("exact_blocker_or_allowance")
        or robots_review.get("robots_decision_reason")
        or source_page.get("blocked_reason")
        or "policy_review_complete"
    )
    source_url = str(candidate.get("source_url") or "")
    return {
        "sport": candidate["sport"],
        "source_name": candidate["source_name"],
        "source_domain": candidate["source_domain"],
        "source_path": candidate["source_path_or_path_pattern"],
        "source_type": candidate["source_type"],
        "source_owner_if_known": candidate.get("source_owner_if_known"),
        "mirror_or_original_source": candidate.get("mirror_or_original_source"),
        "likely_upstream_source": candidate.get("likely_upstream_source"),
        "public_or_private": candidate.get("public_or_private"),
        "login_required": bool(candidate.get("login_required")),
        "paywall_required": bool(candidate.get("paywall_required")),
        "captcha_required": bool(candidate.get("captcha_required")),
        "session_required": bool(candidate.get("session_required")),
        "terms_url": candidate.get("terms_url"),
        "privacy_url": candidate.get("privacy_url"),
        "license_url": candidate.get("license_url"),
        "robots_url": candidate.get("robots_url"),
        "api_docs_url": candidate.get("api_docs_url"),
        "data_dictionary_url": candidate.get("data_dictionary_url"),
        "GitHub_LICENSE_url": candidate.get("GitHub_LICENSE_url"),
        "README_url": candidate.get("README_url"),
        "attribution_url": candidate.get("attribution_url"),
        "acceptable_use_url": candidate.get("acceptable_use_url"),
        "copyright_notice_url": candidate.get("copyright_notice_url"),
        **robots_review,
        **terms_review,
        **license_review,
        **api_docs_review,
        "fields_available": list(candidate.get("fields_available") or []),
        "source_field_names": list(candidate.get("fields_available") or []),
        "repo_field_mapping": list(candidate.get("repo_field_mapping") or []),
        "new_fields_recommended": list(candidate.get("new_fields_recommended") or []),
        "entity_level": candidate.get("normalized_entity_level"),
        "sport_model_relevance": candidate.get("sport_model_relevance"),
        "duplicate_existing_source": bool(candidate.get("duplicate_existing_source")),
        "upstream_source_unclear": bool(candidate.get("upstream_source_unclear")),
        "timestamp_available": bool(candidate.get("timestamp_available")),
        "event_time_available": bool(candidate.get("event_time_available")),
        "game_or_match_start_time_available": bool(candidate.get("game_or_match_start_time_available")),
        "data_publication_time_available": bool(candidate.get("data_publication_time_available")),
        "future_leakage_risk": candidate.get("future_leakage_risk"),
        "post_event_only": bool(candidate.get("post_event_only")),
        "pre_event_available": bool(candidate.get("pre_event_available")),
        "usable_for_prematch_model": bool(candidate.get("usable_for_prematch_model")),
        "usable_for_postmatch_training_only": bool(candidate.get("usable_for_postmatch_training_only")),
        "cutoff_safe": bool(candidate.get("cutoff_safe")),
        "cutoff_safety_reason": candidate.get("cutoff_safety_reason"),
        "raw_html_persistence_allowed": False,
        "raw_payload_persistence_allowed": False,
        "normalized_fact_persistence_allowed": bool(candidate.get("normalized_fact_persistence_allowed")),
        "aggregate_feature_persistence_allowed": bool(candidate.get("aggregate_feature_persistence_allowed")),
        "source_hash_persistence_allowed": True,
        "attribution_storage_required": bool(candidate.get("attribution_storage_required")),
        "required_attribution_text_or_url_hash": candidate.get("required_attribution_text_or_url_hash") or url_hash(source_url),
        "path_level_decision": decision,
        "final_state": final_state,
        "exact_blocker_or_allowance": exact_reason,
        "source_url_hash": url_hash(source_url) if source_url else "",
        "policy_hash": stable_hash(
            {
                "source_id": candidate["source_id"],
                "decision": decision,
                "robots": robots_review.get("robots_decision"),
                "terms": terms_review.get("scraping_allowed"),
                "license": license_review.get("license_name_if_any"),
            }
        ),
        "schema_hash": stable_hash(candidate.get("repo_field_mapping") or []),
        "source_policy_reviewed": True,
        "oxylabs_used": True,
        "oxylabs_transport_used": source_page.get("transport") or candidate.get("primary_transport"),
        "oxylabs_calls_attempted": 1 + int(robots_review.get("oxylabs_calls_attempted", 0) or 0) + int(terms_review.get("oxylabs_calls_attempted", 0) or 0) + int(license_review.get("oxylabs_calls_attempted", 0) or 0) + int(api_docs_review.get("oxylabs_calls_attempted", 0) or 0),
        "oxylabs_calls_successful": (1 if source_page.get("ok") else 0) + int(robots_review.get("oxylabs_calls_successful", 0) or 0) + int(terms_review.get("oxylabs_calls_successful", 0) or 0) + int(license_review.get("oxylabs_calls_successful", 0) or 0) + int(api_docs_review.get("oxylabs_calls_successful", 0) or 0),
        "oxylabs_calls_failed": (0 if source_page.get("ok") else 1) + int(robots_review.get("oxylabs_calls_failed", 0) or 0) + int(terms_review.get("oxylabs_calls_failed", 0) or 0) + int(license_review.get("oxylabs_calls_failed", 0) or 0) + int(api_docs_review.get("oxylabs_calls_failed", 0) or 0),
    }

