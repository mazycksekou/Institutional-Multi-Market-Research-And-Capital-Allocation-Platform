from __future__ import annotations

from typing import Any

from .soccer_free_vs_paid_readiness import soccer_lane_catalog


LANE_SYNONYMS: dict[str, list[str]] = {
    "schedule_results": ["fixtures", "results", "scores", "historical schedule csv"],
    "first_half_scoring_context": ["first half goals", "halftime scores", "first-half totals"],
    "shots_corners_cards_context": ["match stats", "shots on target", "corners", "cards"],
    "referee_history_context": ["referee stats", "official history", "cards by referee"],
    "statsbomb_match_metadata": ["match metadata", "stadium", "manager", "referee"],
    "statsbomb_event_xg_shots": ["expected goals", "shot events", "xg event data"],
    "statsbomb_lineups_minutes": ["lineups", "minutes played", "starting xi"],
    "team_strength_ratings": ["team ratings", "form rating", "attack strength", "defense strength"],
    "rest_travel_fixture_congestion": ["rest days", "fixture congestion", "travel context"],
    "competition_context": ["competition stage", "league context", "knockout context"],
    "stadium_timezone_context": ["stadium timezone", "home advantage", "neutral site"],
    "player_prop_feature_candidates": ["player prop data", "player shots", "player xg"],
    "injuries_availability": ["injury report", "availability", "team news"],
    "upcoming_referee_assignments": ["referee assignments", "match officials", "upcoming referees"],
    "broad_public_xg_mirror_coverage": ["public xg mirror", "understat xg", "shot quality public"],
    "tracking_360_context": ["tracking data", "360 data", "freeze frame"],
    "restricted_reference_tables": ["fbref", "sports reference", "reference tables"],
    "openfootball_historical_results_mirror": ["openfootball", "football.db", "historical results github"],
}


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    league = "Bundesliga soccer"
    lane_label = lane["lane_name"].replace("_", " ")
    field_group = str(lane.get("field_or_feature_group") or lane_label)
    synonym_terms = list(LANE_SYNONYMS.get(lane["lane_name"], []))
    if field_group not in synonym_terms:
        synonym_terms.insert(0, field_group)
    if lane_label not in synonym_terms:
        synonym_terms.insert(1 if synonym_terms else 0, lane_label)
    official_domain = "bundesliga.com"
    templates = [
        ("exact_field_name", f"{league} {lane['lane_name']}"),
        ("synonym_query", f"{league} {synonym_terms[0]}"),
        ("official_league_team", f"{league} official {field_group}"),
        ("public_api_docs", f"{league} public API docs {field_group}"),
        ("github_open_source", f"{league} {lane_label} github"),
        ("csv_parquet_archive", f"{league} {lane_label} csv parquet archive"),
        ("public_pdf_media_guide", f"{league} {lane_label} pdf handbook"),
        ("structured_wiki_supplemental", f"{league} {lane_label} wikidata wikipedia"),
        ("dataset_catalog_index", f"{league} {lane_label} dataset catalog"),
        ("source_specific_terminology", f"{league} {lane_label} football-data statsbomb openfootball"),
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
    for extra_index, synonym in enumerate(synonym_terms[1:4], start=len(rows) + 1):
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


def build_soccer_source_exhaustion_query_plan() -> dict[str, Any]:
    lanes = soccer_lane_catalog()
    query_rows: list[dict[str, Any]] = []
    lane_index: dict[str, list[dict[str, Any]]] = {}
    for lane in lanes:
        rows = _query_records_for_lane(lane)
        lane_index[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "SOCCER_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "soccer_source_exhaustion_query_plan_v1",
        "sport": "soccer",
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


def build_soccer_source_exhaustion_queries() -> dict[str, Any]:
    plan = build_soccer_source_exhaustion_query_plan()
    return {
        "ok": True,
        "status": "ok",
        "sport": "soccer",
        "query_count": plan["query_count"],
        "queries": [row["query"] for row in plan["query_rows"]],
        "query_rows": plan["query_rows"],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
