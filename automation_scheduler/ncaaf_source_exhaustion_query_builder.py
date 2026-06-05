from __future__ import annotations

from typing import Any

from .ncaaf_free_vs_paid_readiness import ncaaf_lane_catalog


QUERY_FAMILIES = (
    "ncaaf_open_data_game_results",
    "college_football_play_by_play_public_dataset",
    "college_football_drive_data_public_dataset",
    "college_football_epa_public_data",
    "college_football_team_stats_public_data",
    "college_football_roster_public_data",
    "college_football_depth_chart_public_data",
    "college_football_injuries_availability_public_data",
    "college_football_weather_stadium_public_data",
    "college_football_coaching_data_public_dataset",
    "college_football_recruiting_transfer_public_dataset",
    "collegefootballdata_api_docs_terms_license",
    "cfbfastr_sportsdataverse_license_terms",
    "ncaa_football_public_data_terms_robots",
    "conference_official_football_data_terms_robots",
    "school_athletic_site_football_data_terms_robots",
    "college_football_box_score_public_data",
    "college_football_gamebook_pdf_public_data",
    "college_football_github_dataset",
    "college_football_csv_parquet_dataset",
    "college_football_data_dictionary",
    "college_football_source_terms_license_robots",
)


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    label = lane["lane_name"].replace("_", " ")
    templates = [(family, f"{family.replace('_', ' ')} {label}") for family in QUERY_FAMILIES]
    templates += [
        ("source_attribution_rules", f"{lane['candidate_source_name']} attribution commercial use"),
        ("source_automated_access_rules", f"{lane['candidate_source_name']} automated access terms robots"),
        ("source_api_storage_rules", f"{lane['candidate_source_name']} API storage caching data dictionary"),
        ("exact_domain_policy", f"site:{lane['source_domain']} terms license robots {label}"),
        ("exact_source_name", f"\"{lane['candidate_source_name']}\" NCAAF data license"),
        ("exact_api_docs", f"\"{lane['candidate_source_name']}\" API docs data dictionary"),
    ]
    return [
        {
            "sport": lane["sport"],
            "subdivision": lane["subdivision"],
            "lane_name": lane["lane_name"],
            "field_or_feature_group": lane["field_or_feature_group"],
            "query_family": family,
            "query": query,
            "query_index": index,
            "source_family": lane["source_family"],
        }
        for index, (family, query) in enumerate(templates, start=1)
    ]


def build_ncaaf_source_exhaustion_query_plan() -> dict[str, Any]:
    lanes = ncaaf_lane_catalog()
    query_rows = []
    lane_index = {}
    for lane in lanes:
        rows = _query_records_for_lane(lane)
        lane_index[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    source_policy_queries = [row for row in query_rows if any(token in row["query_family"] for token in ("terms", "license", "robots", "api", "dictionary", "policy"))]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NCAAF_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "ncaaf_source_exhaustion_query_plan_v1",
        "sport": "americanfootball_ncaaf",
        "subdivisions_included": sorted({lane["subdivision"] for lane in lanes}),
        "query_rows": query_rows,
        "query_count": len(query_rows),
        "source_policy_query_count": len(source_policy_queries),
        "minimum_query_count_satisfied": len(query_rows) >= 150,
        "minimum_source_policy_query_count_satisfied": len(source_policy_queries) >= 30,
        "lanes_included": sorted(lane_index),
        "lane_query_index": lane_index,
        "query_families": sorted({row["query_family"] for row in query_rows}),
        "required_query_families": list(QUERY_FAMILIES),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_ncaaf_source_exhaustion_queries() -> dict[str, Any]:
    plan = build_ncaaf_source_exhaustion_query_plan()
    return {"ok": True, "status": "ok", "sport": "americanfootball_ncaaf", "query_count": plan["query_count"], "queries": [row["query"] for row in plan["query_rows"]], "query_rows": plan["query_rows"], "provider_write": False, "execution_allowed": False, "raw_payload_included": False, "secrets_included": False}
