from __future__ import annotations

from typing import Any

from .combat_free_vs_paid_readiness import combat_lane_catalog


LANE_SYNONYMS: dict[str, list[str]] = {
    "boxing_bout_results": ["boxing public bout result dataset", "boxing results csv", "boxing open data bouts"],
    "boxing_fighter_identity_birthdates": ["boxing fighter metadata dataset", "boxing champions csv", "boxing boxer birthdate data"],
    "boxing_finish_round_context": ["boxing finish method data", "boxing scheduled rounds csv", "boxing stoppage context"],
    "boxing_title_reign_context": ["boxing title reign dataset", "boxing champions reigns csv", "boxing sanctioning body data"],
    "boxing_location_context": ["boxing venue location csv", "boxing location dataset", "boxing event geography data"],
    "mma_bout_results_context": ["mma public fight result dataset", "ufc result data", "mma bout result csv"],
    "mma_fighter_physical_profile": ["mma fighter physical profile data", "ufc fighter reach height stance data", "mma fighter age data"],
    "mma_striking_summary_stats": ["ufc significant strikes public data", "mma striking stats public data", "fight stats striking data"],
    "mma_grappling_control_stats": ["mma grappling statistics public data", "mma takedown defense public data", "mma control time data"],
    "mma_finish_history_context": ["mma finish history public data", "fight method finish public data", "mma round time finish data"],
    "mma_weighin_weight_miss_context": ["ufc weigh in results public data", "mma missed weight public pages", "ufc official weigh in results"],
    "mma_injury_withdrawal_availability": ["mma injuries withdrawals public data", "ufc fighter availability news", "mma cancellation news"],
    "mma_medical_suspension_context": ["medical suspensions public data mma boxing", "athletic commission suspension pdf", "fighter suspension list combat sports"],
    "mma_referee_judging_assignments": ["mma referee assignments public data", "boxing judge assignments public records", "combat officials assignments"],
    "mma_cancellation_short_notice_context": ["fight cancellations public data", "mma short notice fight data", "opponent replacement public pages"],
    "opponent_strength_rankings_context": ["fighter rankings public data", "mma rankings pages", "combat opponent strength data"],
    "boxing_record_depth_context": ["BoxRec official record database", "boxing public record archive", "boxing bout record source"],
    "fighter_metadata_entities": ["Wikidata MMA fighters", "Wikidata boxing fighters", "combat sports structured entities"],
    "promotion_roster_metadata": ["Wikipedia UFC roster", "Wikipedia current boxers list", "combat roster metadata"],
    "community_api_wrapper_context": ["ufc stats api wrapper github", "mma public api wrapper repo", "combat sports github api"],
    "community_scraper_bundle_context": ["mma data scraper github", "ufc scraping repository", "combat sports scraper bundle"],
    "tracking_punch_pattern_context": ["mma tracking vendor", "boxing punch tracking vendor", "combat paid data feed"],
}

QUERY_FAMILIES = (
    "ufc_open_data_fight_results",
    "mma_public_fight_result_dataset",
    "boxing_public_bout_result_dataset",
    "fighter_statistics_open_data",
    "ufc_significant_strikes_public_data",
    "mma_takedown_defense_public_data",
    "mma_grappling_statistics_public_data",
    "fight_method_finish_public_data",
    "fight_round_time_public_data",
    "weigh_in_results_public_data",
    "reach_height_stance_age_fighter_data",
    "medical_suspensions_public_data",
    "fight_cancellations_public_data",
    "opponent_strength_public_data",
    "fighter_rankings_public_data",
    "combat_sports_github_dataset",
    "combat_sports_csv_dataset",
    "combat_sports_api_docs",
    "source_terms_license_robots",
    "boxing_official_commission_records",
)


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    combat_type = str(lane.get("combat_type") or "Combat")
    lane_label = lane["lane_name"].replace("_", " ")
    field_group = str(lane.get("field_or_feature_group") or lane_label)
    official_domain = "ufc.com" if "UFC" in combat_type or "MMA" in combat_type else "openboxing.org"
    templates = [
        ("ufc_open_data_fight_results", f"{combat_type} open data fight results {lane_label}"),
        ("mma_public_fight_result_dataset", f"MMA public fight result dataset {lane_label}"),
        ("boxing_public_bout_result_dataset", f"boxing public bout result dataset {lane_label}"),
        ("fighter_statistics_open_data", f"fighter statistics open data {lane_label}"),
        ("ufc_significant_strikes_public_data", f"UFC significant strikes public data {lane_label}"),
        ("mma_takedown_defense_public_data", f"MMA takedown defense public data {lane_label}"),
        ("mma_grappling_statistics_public_data", f"MMA grappling statistics public data {lane_label}"),
        ("fight_method_finish_public_data", f"fight method finish public data {lane_label}"),
        ("fight_round_time_public_data", f"fight round time public data {lane_label}"),
        ("weigh_in_results_public_data", f"weigh-in results public data {lane_label}"),
        ("reach_height_stance_age_fighter_data", f"reach height stance age fighter data {lane_label}"),
        ("medical_suspensions_public_data", f"medical suspensions public data {lane_label}"),
        ("fight_cancellations_public_data", f"fight cancellations public data {lane_label}"),
        ("opponent_strength_public_data", f"opponent strength public data {lane_label}"),
        ("fighter_rankings_public_data", f"fighter rankings public data {lane_label}"),
        ("combat_sports_github_dataset", f"combat sports GitHub dataset {lane_label}"),
        ("combat_sports_csv_dataset", f"combat sports CSV dataset {lane_label}"),
        ("combat_sports_api_docs", f"combat sports API docs {lane_label}"),
        ("source_terms_license_robots", f"{field_group} terms license robots"),
        ("boxing_official_commission_records", f"boxing official commission records {lane_label}"),
        ("source_attribution_rules", f"{field_group} attribution requirement combat sports"),
        ("source_commercial_use_rules", f"{field_group} commercial use combat sports"),
        ("source_automated_access_rules", f"{field_group} automated access combat sports"),
        ("site_exact_official", f"{lane_label} site:{official_domain}"),
        ("site_exact_github", f"{lane_label} site:github.com"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, query) in enumerate(templates, start=1):
        rows.append(
            {
                "sport": lane["sport"],
                "combat_type": lane["combat_type"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane.get("field_or_feature_group"),
                "query_family": family,
                "query": query,
                "query_index": index,
                "official_domain": official_domain,
                "source_family": lane.get("source_family"),
            }
        )
    return rows


def build_combat_source_exhaustion_query_plan() -> dict[str, Any]:
    lanes = combat_lane_catalog()
    query_rows: list[dict[str, Any]] = []
    lane_index: dict[str, list[dict[str, Any]]] = {}
    for lane in lanes:
        rows = _query_records_for_lane(lane)
        lane_index[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMBAT_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "combat_source_exhaustion_query_plan_v1",
        "sport": "combat",
        "combat_types_included": sorted({lane["combat_type"] for lane in lanes}),
        "query_rows": query_rows,
        "query_count": len(query_rows),
        "minimum_query_count_satisfied": len(query_rows) >= 125,
        "lanes_included": sorted(lane_index),
        "lane_query_index": lane_index,
        "query_families": sorted({row["query_family"] for row in query_rows}),
        "required_query_families": list(QUERY_FAMILIES),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_combat_source_exhaustion_queries() -> dict[str, Any]:
    plan = build_combat_source_exhaustion_query_plan()
    return {
        "ok": True,
        "status": "ok",
        "sport": "combat",
        "query_count": plan["query_count"],
        "queries": [row["query"] for row in plan["query_rows"]],
        "query_rows": plan["query_rows"],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
