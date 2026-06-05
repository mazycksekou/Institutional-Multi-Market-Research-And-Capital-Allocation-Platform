from __future__ import annotations

from typing import Any

from .golf_free_vs_paid_readiness import golf_lane_catalog


QUERY_FAMILIES = (
    "golf_open_data_tournament_results",
    "pga_tour_results_public_data",
    "dp_world_tour_results_public_data",
    "lpga_results_public_data",
    "golf_strokes_gained_public_data",
    "golf_course_history_public_data",
    "golf_course_scorecard_public_data",
    "golf_player_rankings_historical_data",
    "owgr_public_data_license_terms",
    "golf_weather_wind_course_data",
    "golf_cut_line_historical_data",
    "golf_round_by_round_scoring_public_data",
    "golf_leaderboard_api_docs",
    "golf_player_profile_data",
    "golf_tournament_field_public_data",
    "golf_tee_times_public_data",
    "golf_injuries_withdrawals_public_data",
    "golf_github_dataset",
    "golf_csv_parquet_dataset",
    "golf_source_terms_license_robots",
)


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    label = lane["lane_name"].replace("_", " ")
    templates = [(family, f"{family.replace('_', ' ')} {label}") for family in QUERY_FAMILIES]
    templates += [
        ("source_attribution_rules", f"{lane['candidate_source_name']} attribution commercial use"),
        ("source_automated_access_rules", f"{lane['candidate_source_name']} automated access terms robots"),
        ("exact_domain_policy", f"site:{lane['source_domain']} terms license robots {label}"),
        ("exact_source_name", f"\"{lane['candidate_source_name']}\" golf data license"),
        ("exact_api_docs", f"\"{lane['candidate_source_name']}\" API docs data dictionary"),
    ]
    return [
        {
            "sport": lane["sport"],
            "tour": lane["tour"],
            "lane_name": lane["lane_name"],
            "field_or_feature_group": lane["field_or_feature_group"],
            "query_family": family,
            "query": query,
            "query_index": index,
            "source_family": lane["source_family"],
        }
        for index, (family, query) in enumerate(templates, start=1)
    ]


def build_golf_source_exhaustion_query_plan() -> dict[str, Any]:
    lanes = golf_lane_catalog()
    query_rows = []
    lane_index = {}
    for lane in lanes:
        rows = _query_records_for_lane(lane)
        lane_index[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "GOLF_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "golf_source_exhaustion_query_plan_v1",
        "sport": "golf",
        "tours_included": sorted({lane["tour"] for lane in lanes}),
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


def build_golf_source_exhaustion_queries() -> dict[str, Any]:
    plan = build_golf_source_exhaustion_query_plan()
    return {"ok": True, "status": "ok", "sport": "golf", "query_count": plan["query_count"], "queries": [row["query"] for row in plan["query_rows"]], "query_rows": plan["query_rows"], "provider_write": False, "execution_allowed": False, "raw_payload_included": False, "secrets_included": False}
