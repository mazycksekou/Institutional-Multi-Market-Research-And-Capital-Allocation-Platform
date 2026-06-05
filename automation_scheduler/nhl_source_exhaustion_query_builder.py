from __future__ import annotations

from typing import Any

from .nhl_free_vs_paid_readiness import nhl_lane_catalog


LANE_SYNONYMS: dict[str, list[str]] = {
    "schedule_results": ["schedule", "results", "scoreboard", "game list"],
    "team_box_scores": ["team box score", "team stats", "team game stats"],
    "player_box_scores": ["player box score", "skater game stats", "player game stats"],
    "goalie_box_scores": ["goalie box score", "goalie game stats", "goalie stats"],
    "play_by_play": ["play by play", "event log", "gamecenter events"],
    "shot_events": ["shot location", "shot events", "shot coordinates"],
    "penalty_events": ["penalty events", "penalties", "special teams events"],
    "power_play_penalty_kill_stats": ["power play stats", "penalty kill stats", "special teams stats"],
    "goalie_starts": ["goalie starts", "starting goalie", "goalie starter"],
    "goalie_workload_rest": ["goalie workload", "goalie rest", "goalie fatigue"],
    "rest_travel_features": ["rest", "travel", "back to back"],
    "venue_rink_timezone_features": ["venue", "rink", "timezone"],
    "roster_records": ["roster", "team roster", "player roster"],
    "overtime_shootout_context": ["overtime context", "shootout context", "regulation versus overtime"],
    "first_period_scoring_context": ["first period scoring", "first period shots", "1st period"],
    "team_totals_context": ["team totals", "team scoring context", "goal totals"],
    "player_prop_feature_candidates": ["player prop data", "shots on goal", "points prop"],
    "injuries_availability": ["injury report", "player availability", "goalie availability"],
    "officials_referee_assignments": ["officials", "referee assignments", "referees and linesmen"],
    "lineup_line_combinations": ["line combinations", "defensive pairings", "confirmed lines"],
    "public_expected_goals_dataset": ["expected goals", "xg dataset", "shot quality"],
    "goalie_gsaax_dataset": ["goals saved above expected", "gsaax", "advanced goalie metrics"],
    "restricted_reference_tables": ["hockey reference", "sports reference", "reference tables"],
    "community_open_mirror_datasets": ["github nhl dataset", "open mirror", "community dataset"],
}


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    league = "NHL"
    lane_label = lane["lane_name"].replace("_", " ")
    field_group = str(lane.get("field_or_feature_group") or lane_label)
    synonym_terms = list(LANE_SYNONYMS.get(lane["lane_name"], []))
    if field_group not in synonym_terms:
        synonym_terms.insert(0, field_group)
    if lane_label not in synonym_terms:
        synonym_terms.insert(1 if synonym_terms else 0, lane_label)
    official_domain = "nhl.com"
    templates = [
        ("exact_field_name", f"{league} {lane['lane_name']}"),
        ("synonym_query", f"{league} {synonym_terms[0]}"),
        ("official_league_team", f"{league} official {field_group}"),
        ("public_api_docs", f"{league} official API {field_group}"),
        ("github_open_source", f"{league} {lane_label} github"),
        ("csv_parquet_archive", f"{league} {lane_label} csv parquet"),
        ("public_pdf_media_guide", f"{league} {lane_label} pdf game report"),
        ("structured_wiki_supplemental", f"{league} {lane_label} wikidata wikipedia"),
        ("dataset_catalog_index", f"{league} {lane_label} dataset catalog"),
        ("source_specific_terminology", f"{league} gamecenter {lane_label}"),
        ("site_exact_official", f"{lane_label} site:{official_domain}"),
        ("site_exact_github", f"{lane_label} site:github.com"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, query) in enumerate(templates, start=1):
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane.get("field_or_feature_group"),
                "query_family": family,
                "query": query,
                "query_index": index,
                "official_domain": official_domain,
                "source_family": lane.get("source_family"),
            }
        )
    for extra_index, synonym in enumerate(synonym_terms[1:3], start=len(rows) + 1):
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane.get("field_or_feature_group"),
                "query_family": f"synonym_query_{extra_index - len(templates)}",
                "query": f"{league} {synonym} public data",
                "query_index": extra_index,
                "official_domain": official_domain,
                "source_family": lane.get("source_family"),
            }
        )
    return rows


def build_nhl_source_exhaustion_query_plan() -> dict[str, Any]:
    lanes = [lane for lane in nhl_lane_catalog() if lane["free_or_paid_category"] != "obsolete_or_duplicate" or lane["lane_name"] == "community_open_mirror_datasets"]
    query_rows: list[dict[str, Any]] = []
    lane_index: dict[str, list[dict[str, Any]]] = {}
    for lane in lanes:
        rows = _query_records_for_lane(lane)
        lane_index[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "nhl_source_exhaustion_query_plan_v1",
        "sport": "icehockey_nhl",
        "query_rows": query_rows,
        "query_count": len(query_rows),
        "lanes_included": sorted(lane_index),
        "lane_query_index": lane_index,
        "query_families": sorted({row["query_family"] for row in query_rows}),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_nhl_source_exhaustion_queries() -> dict[str, Any]:
    plan = build_nhl_source_exhaustion_query_plan()
    return {
        "ok": True,
        "status": "ok",
        "sport": "icehockey_nhl",
        "query_count": plan["query_count"],
        "queries": [row["query"] for row in plan["query_rows"]],
        "query_rows": plan["query_rows"],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
