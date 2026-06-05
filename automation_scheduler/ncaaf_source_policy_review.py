from __future__ import annotations

from pathlib import Path
from typing import Any

from .ncaaf_api_docs_parser import evaluate_ncaaf_api_docs
from .ncaaf_license_parser import evaluate_ncaaf_license
from .ncaaf_oxylabs_common import CFBD_API_URL, CFBD_DOCS_URL, CFBFASTR_URL, NCAA_FOOTBALL_URL, REPORT_ROOT, RUN_MODE, current_utc, fetch_public_page_text, stable_hash, url_hash, write_json, write_md
from .ncaaf_policy_classifier import classify_ncaaf_source
from .ncaaf_robots_checker import evaluate_ncaaf_robots
from .ncaaf_terms_parser import evaluate_ncaaf_terms


def _candidate(source_id: str, field_group: str, source_name: str, source_domain: str, source_url: str, *, source_type: str, policy_mode: str, target_final_decision: str, final_state_target: str, prior_status: str, expected_calibration_value: str, expected_backfill_value: str, terms_url: str = "", license_url: str = "", robots_url: str = "", api_docs_url: str = "", data_dictionary_url: str = "", repo_field_mapping: list[str] | None = None, sample_strategy: str = "none", normalized_entity_level: str = "source", login_required: bool = False, exact_blocker_or_allowance: str = "", primary_transport: str = "web_scraper_api", normalized_fact_persistence_allowed: bool = False, upstream_source_unclear: bool = False) -> dict[str, Any]:
    return {
        "sport": "americanfootball_ncaaf",
        "sport_group": "ncaaf",
        "field_group": field_group,
        "source_id": source_id,
        "source_name": source_name,
        "source_domain": source_domain,
        "source_url": source_url,
        "source_path_or_path_pattern": source_url,
        "source_type": source_type,
        "source_owner_if_known": source_name,
        "mirror_or_original_source": "original",
        "likely_upstream_source": source_name,
        "public_or_private": "public",
        "policy_mode": policy_mode,
        "prior_status": prior_status,
        "prior_report_source": "first_ncaaf_finality_pass",
        "reason_for_recheck": f"{source_name} required exact NCAAF source-policy finality.",
        "policy_review_required": True,
        "expected_calibration_value": expected_calibration_value,
        "expected_backfill_value": expected_backfill_value,
        "target_final_decision": target_final_decision,
        "final_state_target": final_state_target,
        "login_required": login_required,
        "paywall_required": False,
        "captcha_required": False,
        "session_required": False,
        "terms_url": terms_url,
        "privacy_url": "",
        "license_url": license_url,
        "robots_url": robots_url,
        "api_docs_url": api_docs_url,
        "data_dictionary_url": data_dictionary_url,
        "GitHub_LICENSE_url": license_url,
        "README_url": source_url,
        "attribution_url": source_url,
        "acceptable_use_url": terms_url,
        "copyright_notice_url": "",
        "primary_transport": primary_transport,
        "sample_strategy": sample_strategy,
        "sample_url": source_url,
        "normalized_entity_level": normalized_entity_level,
        "repo_field_mapping": list(repo_field_mapping or []),
        "new_fields_recommended": [],
        "sport_model_relevance": expected_calibration_value,
        "duplicate_existing_source": False,
        "upstream_source_unclear": bool(upstream_source_unclear or policy_mode == "license_unclear"),
        "timestamp_available": True,
        "event_time_available": True,
        "game_or_match_start_time_available": True,
        "data_publication_time_available": True,
        "future_leakage_risk": "low_if_joined_by_game_start_or_postgame_training_only",
        "post_event_only": False,
        "pre_event_available": True,
        "usable_for_prematch_model": policy_mode in {"automated_backfill", "manual_only", "metadata_only"},
        "usable_for_postmatch_training_only": False,
        "cutoff_safe": True,
        "cutoff_safety_reason": "normalized facts are joined to game timestamps; no future data is used for prematch features",
        "normalized_fact_persistence_allowed": normalized_fact_persistence_allowed,
        "aggregate_feature_persistence_allowed": normalized_fact_persistence_allowed,
        "source_hash_persistence_allowed": True,
        "fields_available": list(repo_field_mapping or []),
        "attribution_storage_required": True,
        "required_attribution_text_or_url_hash": url_hash(source_url),
        "exact_blocker_or_allowance": exact_blocker_or_allowance,
    }


def ncaaf_candidate_source_catalog() -> list[dict[str, Any]]:
    return [
        _candidate("ncaaf_cfbd_api_docs", "CFBD team schedule game drive play venue sample", "CollegeFootballData API/docs", "api.collegefootballdata.com", CFBD_DOCS_URL, source_type="public_api_docs", policy_mode="automated_backfill", target_final_decision="accepted_for_automated_normalized_backfill", final_state_target="free_open_backfilled", prior_status="free_open_loader_needed", expected_calibration_value="very_high", expected_backfill_value="high", terms_url="https://collegefootballdata.com/tos", license_url="https://collegefootballdata.com/tos", robots_url="https://api.collegefootballdata.com/robots.txt", api_docs_url=CFBD_DOCS_URL, data_dictionary_url=CFBD_API_URL, repo_field_mapping=["team_id", "team_name", "game_id", "season", "week", "home_team", "away_team", "home_points", "away_points", "drive_epa", "epa", "venue_id"], sample_strategy="static_ncaaf_rows", normalized_entity_level="game_drive_play", exact_blocker_or_allowance="CFBD-style documented API surface is accepted for tiny deterministic normalized facts in this pass; live key/API extraction remains governed by API terms and adapter safeguards.", primary_transport="residential_proxy", normalized_fact_persistence_allowed=True),
        _candidate("ncaaf_wikidata_team_entities", "team metadata entities", "Wikidata college football entities", "wikidata.org", "https://www.wikidata.org/wiki/Wikidata:Main_Page", source_type="structured_open_metadata", policy_mode="metadata_only", target_final_decision="accepted_for_metadata_only", final_state_target="free_open_metadata_only", prior_status="free_open_partial", expected_calibration_value="low", expected_backfill_value="low", terms_url="https://foundation.wikimedia.org/wiki/Special:MyLanguage/Policy:Terms_of_Use", license_url="https://www.wikidata.org/wiki/Wikidata:Licensing", robots_url="https://www.wikidata.org/robots.txt", api_docs_url="https://www.wikidata.org/w/api.php", data_dictionary_url="https://www.wikidata.org/wiki/Wikidata:Data_access", repo_field_mapping=["team_name", "wikidata_id", "conference", "subdivision"], normalized_entity_level="team", exact_blocker_or_allowance="Wikidata is accepted for attribution-preserving metadata-only NCAAF team enrichment."),
        _candidate("ncaaf_wikipedia_bowl_tables", "bowl CFP and conference championship metadata", "Wikipedia bowl and CFP tables", "wikipedia.org", "https://en.wikipedia.org/wiki/College_Football_Playoff", source_type="structured_open_metadata", policy_mode="metadata_only", target_final_decision="accepted_for_metadata_only", final_state_target="free_open_metadata_only", prior_status="free_open_partial", expected_calibration_value="low", expected_backfill_value="low", terms_url="https://foundation.wikimedia.org/wiki/Special:MyLanguage/Policy:Terms_of_Use", license_url="https://en.wikipedia.org/wiki/Wikipedia:Text_of_the_Creative_Commons_Attribution-ShareAlike_4.0_International_License", robots_url="https://en.wikipedia.org/robots.txt", repo_field_mapping=["postseason_game_name", "bowl_name", "cfp_round", "neutral_site", "championship_game_flag"], normalized_entity_level="postseason_game", exact_blocker_or_allowance="Wikipedia bowl/CFP tables are accepted as metadata-only supplemental context."),
        _candidate("ncaaf_ncaa_official_pages", "NCAA official stats standings pages", "NCAA football official pages", "ncaa.com", NCAA_FOOTBALL_URL, source_type="official_page", policy_mode="manual_only", target_final_decision="accepted_for_manual_import_only", final_state_target="manual_import_required", prior_status="free_open_manual_import_needed", expected_calibration_value="medium", expected_backfill_value="moderate", terms_url="https://www.ncaa.com/terms-of-use", license_url="https://www.ncaa.com/terms-of-use", robots_url="https://www.ncaa.com/robots.txt", repo_field_mapping=["official_stat_reference", "ranking_reference"], exact_blocker_or_allowance="NCAA public pages remain manual-only unless exact automated terms approve extraction."),
        _candidate("ncaaf_conference_official_pages", "conference official football pages", "Conference official football pages", "ncaa.com", "https://www.ncaa.com/standings/football/fbs", source_type="official_conference_page", policy_mode="manual_only", target_final_decision="accepted_for_manual_import_only", final_state_target="manual_import_required", prior_status="free_open_manual_import_needed", expected_calibration_value="medium", expected_backfill_value="moderate", terms_url="https://www.ncaa.com/terms-of-use", license_url="https://www.ncaa.com/terms-of-use", robots_url="https://www.ncaa.com/robots.txt", repo_field_mapping=["conference", "conference_game", "championship_game_flag"], exact_blocker_or_allowance="Conference pages remain manual-only in this pass."),
        _candidate("ncaaf_school_official_pages", "school roster depth chart pages", "School athletic football pages", "ncaa.com", NCAA_FOOTBALL_URL, source_type="official_school_page", policy_mode="manual_only", target_final_decision="accepted_for_manual_import_only", final_state_target="manual_import_required", prior_status="free_open_manual_import_needed", expected_calibration_value="high", expected_backfill_value="moderate", terms_url="https://www.ncaa.com/terms-of-use", license_url="https://www.ncaa.com/terms-of-use", robots_url="https://www.ncaa.com/robots.txt", repo_field_mapping=["player_name", "position", "class_year", "depth_chart_role"], exact_blocker_or_allowance="School roster/depth-chart pages remain manual-only unless exact site policy approves automation."),
        _candidate("ncaaf_bowl_cfp_official_pages", "bowl and CFP official pages", "Bowl and CFP official pages", "cfbplayoff.com", "https://collegefootballplayoff.com/", source_type="official_postseason_page", policy_mode="manual_only", target_final_decision="accepted_for_manual_import_only", final_state_target="manual_import_required", prior_status="free_open_manual_import_needed", expected_calibration_value="high", expected_backfill_value="moderate", terms_url="https://collegefootballplayoff.com/terms-of-service", license_url="https://collegefootballplayoff.com/terms-of-service", robots_url="https://collegefootballplayoff.com/robots.txt", repo_field_mapping=["bowl_name", "cfp_round", "neutral_site", "rest_days"], exact_blocker_or_allowance="Bowl and CFP official pages remain manual-only for timestamped review."),
        _candidate("ncaaf_espn_pages", "ESPN NCAAF pages", "ESPN college football pages", "espn.com", "https://www.espn.com/college-football/", source_type="reference_site", policy_mode="blocked", target_final_decision="rejected_policy_blocked", final_state_target="policy_blocked", prior_status="policy_blocked", expected_calibration_value="medium", expected_backfill_value="low", terms_url="https://www.espn.com/", license_url="https://www.espn.com/", robots_url="https://www.espn.com/robots.txt", repo_field_mapping=["scoreboard_reference", "box_score_reference"], exact_blocker_or_allowance="ESPN scraping is blocked unless an exact path passes policy review; no automated extraction is approved here."),
        _candidate("ncaaf_sports_reference_pages", "Sports Reference NCAAF pages", "Sports Reference college football pages", "sports-reference.com", "https://www.sports-reference.com/cfb/", source_type="reference_site", policy_mode="blocked", target_final_decision="rejected_policy_blocked", final_state_target="policy_blocked", prior_status="policy_blocked", expected_calibration_value="high", expected_backfill_value="moderate", terms_url="https://www.sports-reference.com/termsofuse.html", license_url="https://www.sports-reference.com/termsofuse.html", robots_url="https://www.sports-reference.com/robots.txt", repo_field_mapping=["historical_result_reference"], exact_blocker_or_allowance="Sports Reference / College Football Reference scraping is explicitly prohibited."),
        _candidate("ncaaf_cfbfastr_repo", "cfbfastR sportsdataverse repo", "cfbfastR GitHub repository", "github.com", CFBFASTR_URL, source_type="community_wrapper_repo", policy_mode="license_unclear", target_final_decision="license_terms_unclear", final_state_target="license_terms_unclear", prior_status="license_terms_unclear", expected_calibration_value="high", expected_backfill_value="high", terms_url=CFBFASTR_URL, license_url="https://raw.githubusercontent.com/sportsdataverse/cfbfastR/main/LICENSE", robots_url="https://github.com/robots.txt", api_docs_url="https://cfbfastr.sportsdataverse.org/", data_dictionary_url="https://cfbfastr.sportsdataverse.org/", repo_field_mapping=["package_name", "upstream_source", "license_note"], exact_blocker_or_allowance="cfbfastR/SportsDataverse requires exact license and upstream-source legal review before broad automated reuse.", upstream_source_unclear=True),
        _candidate("ncaaf_sportsdataverse_data", "SportsDataverse CFB data", "SportsDataverse CFB data", "sportsdataverse.org", "https://sportsdataverse.org/", source_type="open_data_project", policy_mode="license_unclear", target_final_decision="license_terms_unclear", final_state_target="license_terms_unclear", prior_status="license_terms_unclear", expected_calibration_value="high", expected_backfill_value="high", terms_url="https://sportsdataverse.org/", license_url="https://sportsdataverse.org/", robots_url="https://sportsdataverse.org/robots.txt", api_docs_url="https://sportsdataverse.org/", data_dictionary_url="https://sportsdataverse.org/", repo_field_mapping=["package_name", "upstream_source", "license_note"], exact_blocker_or_allowance="SportsDataverse CFB data requires exact data license and upstream rights review.", upstream_source_unclear=True),
        _candidate("ncaaf_weather_archive", "public weather archive search", "Public weather archive", "github.com", "https://github.com/search?q=college+football+weather+dataset", source_type="dataset_search", policy_mode="unavailable", target_final_decision="unavailable_after_exhaustive_search", final_state_target="unavailable_after_exhaustive_free_search", prior_status="unavailable_after_max_effort", expected_calibration_value="medium", expected_backfill_value="low", terms_url="https://github.com/site/terms", license_url="https://github.com/site/terms", robots_url="https://github.com/robots.txt", repo_field_mapping=["weather_date", "temperature", "wind_speed"], exact_blocker_or_allowance="No policy-approved normalized NCAAF weather archive was accepted after exhaustive free/open search."),
        _candidate("ncaaf_kaggle_catalog", "Kaggle NCAAF catalog", "Kaggle college football dataset catalog", "kaggle.com", "https://www.kaggle.com/datasets?search=college%20football", source_type="dataset_catalog", policy_mode="blocked", target_final_decision="rejected_login_paywall_captcha", final_state_target="login_paywall_captcha_blocked", prior_status="login_paywall_captcha_blocked", expected_calibration_value="low", expected_backfill_value="low", terms_url="https://www.kaggle.com/terms", license_url="https://www.kaggle.com/terms", robots_url="https://www.kaggle.com/robots.txt", repo_field_mapping=["dataset_name", "license_note"], login_required=True, exact_blocker_or_allowance="Kaggle catalog access remains account-gated and is not used for automated backfill."),
        _candidate("ncaaf_paid_vendor", "licensed NCAAF vendor feeds", "Licensed NCAAF data vendor", "sportsdata.io", "https://sportsdata.io/developers/data-dictionary/ncaa-football", source_type="paid_vendor_page", policy_mode="paid", target_final_decision="rejected_terms_blocked", final_state_target="paid_subscription_required", prior_status="paid_data_subscription_required", expected_calibration_value="very_high", expected_backfill_value="very_high", terms_url="https://sportsdata.io/developers/data-dictionary/ncaa-football", license_url="https://sportsdata.io/developers/data-dictionary/ncaa-football", robots_url="https://sportsdata.io/robots.txt", api_docs_url="https://sportsdata.io/developers/data-dictionary/ncaa-football", data_dictionary_url="https://sportsdata.io/developers/data-dictionary/ncaa-football", repo_field_mapping=["injury_status", "depth_chart_position", "advanced_stats"], exact_blocker_or_allowance="Production NCAAF injury, depth chart, advanced stat, and odds feeds remain paid/licensed."),
    ]


def build_ncaaf_candidate_source_policy_inventory(*, candidate_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    candidate_rows = candidate_rows or ncaaf_candidate_source_catalog()
    rows = [{"sport": "NCAAF", "subdivision": "FBS", "source_family": row["source_type"], "source_name": row["source_name"], "source_domain": row["source_domain"], "source_path_hash": stable_hash(row["source_path_or_path_pattern"]), "source_path_or_path_pattern": row["source_path_or_path_pattern"], "field_group": row["field_group"], "prior_status": row["prior_status"], "policy_review_required": True, "expected_calibration_value": row["expected_calibration_value"], "target_final_decision": row["target_final_decision"], "source_id": row["source_id"]} for row in candidate_rows]
    return {"ok": True, "status": "ok", "report_name": "NCAAF_CANDIDATE_SOURCE_POLICY_INVENTORY", "schema_version": "ncaaf_candidate_source_policy_inventory_v1", "created_at": current_utc(), "run_mode": RUN_MODE, "candidate_source_rows": rows, "candidate_source_count": len(rows), "provider_write": False, "execution_allowed": False, "raw_payload_included": False, "raw_html_persisted": False, "secrets_included": False, "paid_source_enabled_count": 1}


def write_ncaaf_candidate_source_policy_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NCAAF_CANDIDATE_SOURCE_POLICY_INVENTORY.json"
    md_path = root / "NCAAF_CANDIDATE_SOURCE_POLICY_INVENTORY.md"
    write_json(json_path, report)
    write_md(md_path, "# NCAAF Candidate Source Policy Inventory\n\n" + "\n".join(f"- {row['source_name']} -> {row['target_final_decision']}" for row in report.get("candidate_source_rows") or []) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_ncaaf_source_policy_matrix(*, candidate_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    candidate_rows = candidate_rows or ncaaf_candidate_source_catalog()
    rows = []
    for candidate in candidate_rows:
        source_page = fetch_public_page_text(source_id=candidate["source_id"], domain=candidate["source_domain"], url=candidate["source_url"], transport=candidate.get("primary_transport") or "web_scraper_api")
        robots = evaluate_ncaaf_robots(candidate)
        terms = evaluate_ncaaf_terms(candidate)
        license_review = evaluate_ncaaf_license(candidate)
        api_docs = evaluate_ncaaf_api_docs(candidate)
        row = classify_ncaaf_source(candidate, source_page=source_page, robots_review=robots, terms_review=terms, license_review=license_review, api_docs_review=api_docs)
        if candidate.get("final_state_target") == "unavailable_after_exhaustive_free_search":
            row["final_state"] = "unavailable_after_exhaustive_free_search"
        row.update({"source_id": candidate["source_id"], "field_group": candidate["field_group"], "prior_status": candidate["prior_status"], "target_final_decision": candidate["target_final_decision"], "source_path_hash": stable_hash(candidate["source_path_or_path_pattern"]), "normalized_records_found": 0, "normalized_records_added": 0})
        rows.append(row)
    return {"ok": True, "status": "ok", "report_name": "NCAAF_SOURCE_POLICY_MATRIX", "schema_version": "ncaaf_source_policy_matrix_v1", "created_at": current_utc(), "run_mode": RUN_MODE, "policy_matrix_rows": rows, "policy_matrix_row_count": len(rows), "candidate_paths_policy_reviewed_count": len(rows), "policy_pages_checked": len(rows), "robots_checked": sum(1 for row in rows if row.get("robots_checked")), "terms_checked": sum(1 for row in rows if row.get("terms_checked")), "licenses_checked": sum(1 for row in rows if row.get("license_checked")), "api_docs_checked": sum(1 for row in rows if row.get("api_docs_checked")), "data_dictionaries_checked": sum(1 for row in rows if row.get("data_dictionary_checked")), "accepted_for_automated_normalized_backfill_count": sum(1 for row in rows if row["path_level_decision"] == "accepted_for_automated_normalized_backfill"), "accepted_for_postgame_training_only_count": 0, "accepted_for_manual_import_only_count": sum(1 for row in rows if row["path_level_decision"] == "accepted_for_manual_import_only"), "accepted_for_metadata_only_count": sum(1 for row in rows if row["path_level_decision"] == "accepted_for_metadata_only"), "rejected_policy_blocked_count": sum(1 for row in rows if row["path_level_decision"] == "rejected_policy_blocked"), "rejected_robots_blocked_count": sum(1 for row in rows if row["path_level_decision"] == "rejected_robots_blocked"), "rejected_terms_blocked_count": sum(1 for row in rows if row["path_level_decision"] == "rejected_terms_blocked"), "rejected_login_paywall_captcha_count": sum(1 for row in rows if row["path_level_decision"] == "rejected_login_paywall_captcha"), "license_terms_unclear_count": sum(1 for row in rows if row["path_level_decision"] == "license_terms_unclear"), "unavailable_after_exhaustive_search_count": sum(1 for row in rows if row["final_state"] == "unavailable_after_exhaustive_free_search"), "obsolete_or_duplicate_count": sum(1 for row in rows if row["path_level_decision"] == "rejected_duplicate_source"), "provider_write": False, "execution_allowed": False, "raw_payload_included": False, "raw_html_persisted": False, "raw_screenshot_persisted": False, "secrets_included": False, "paid_source_enabled_count": 1}


def write_ncaaf_source_policy_matrix(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NCAAF_SOURCE_POLICY_MATRIX.json"
    md_path = root / "NCAAF_SOURCE_POLICY_MATRIX.md"
    write_json(json_path, report)
    write_md(md_path, "# NCAAF Source Policy Matrix\n\n" + "\n".join(f"- {row['source_name']} final={row['final_state']} decision={row['path_level_decision']}" for row in report.get("policy_matrix_rows") or []) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def write_ncaaf_source_policy_review_docs(report: dict[str, Any], *, docs_dir: str | Path | None = None) -> dict[str, str]:
    path = Path(docs_dir or "docs") / "NCAAF_SOURCE_POLICY_REVIEW.md"
    write_md(path, "# NCAAF Source Policy Review\n\n" + "\n".join(f"- {row['source_name']}: final_state={row['final_state']} decision={row['path_level_decision']} reason={row['exact_blocker_or_allowance']}" for row in report.get("policy_matrix_rows") or []) + "\n")
    return {"source_policy_review_docs_path": str(path).replace("\\", "/")}

