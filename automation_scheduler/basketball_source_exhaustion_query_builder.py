from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import SPORTS, basketball_lane_catalog
from .basketball_oxylabs_common import partial_lanes, unresolved_lanes


SPORT_LABELS = {sport: meta["display_name"] for sport, meta in SPORTS.items()}
OFFICIAL_DOMAINS = {
    "basketball_nba": "nba.com",
    "basketball_wnba": "wnba.com",
    "basketball_ncaab": "ncaa.com",
    "basketball_ncaaw": "ncaa.com",
}

LANE_SYNONYMS: dict[str, list[str]] = {
    "schedule_results": ["schedule", "results", "game list", "scoreboard"],
    "team_box_scores": ["team stats", "team boxscore", "team box score"],
    "player_box_scores": ["player stats", "player boxscore", "player box score"],
    "play_by_play": ["pbp", "play by play", "event log", "game log"],
    "advanced_team_player_stats": ["advanced stats", "team player stats", "season stats"],
    "pace_possessions": ["pace", "possessions", "tempo", "possession estimate"],
    "shot_location": ["shot chart", "shot map", "shot coordinates", "shot location"],
    "referee_official_assignments": ["officials", "referees", "crew assignments", "ref crew"],
    "rest_travel_features": ["rest", "travel", "back to back", "fatigue"],
    "arena_venue_features": ["venue", "arena", "neutral site", "home court"],
    "roster_continuity": ["roster continuity", "rotation stability", "roster history"],
    "injuries_availability": ["injuries", "availability", "injury report", "status report"],
    "transaction_availability_volatility": ["transactions", "availability volatility", "roster changes"],
    "optical_tracking_player_location": ["tracking", "player location", "ball tracking", "optical tracking"],
    "restricted_reference_tables": ["basketball reference", "sports reference", "reference tables"],
    "duplicate_box_score_mirror_sources": ["duplicate box score", "mirror source", "redundant source"],
    "lineup_on_off": ["lineup on/off", "lineups", "on off", "plus minus"],
    "strength_of_schedule_context": ["net ranking", "sos", "strength of schedule", "quad records"],
    "conference_tournament_context": ["conference context", "tournament context", "neutral site context"],
}


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    league = SPORT_LABELS.get(lane["sport"], lane["sport"].upper())
    official_domain = OFFICIAL_DOMAINS.get(lane["sport"], "example.com")
    lane_label = lane["lane_name"].replace("_", " ")
    field_group = str(lane.get("field_or_feature_group") or lane_label)
    source_family = str(lane.get("source_family") or field_group)
    synonym_terms = LANE_SYNONYMS.get(lane["lane_name"], [])[:]
    if field_group not in synonym_terms:
        synonym_terms.insert(0, field_group)
    if lane_label not in synonym_terms:
        synonym_terms.insert(1 if synonym_terms else 0, lane_label)
    synonym_terms = [term for term in synonym_terms if term]
    templates = [
        ("exact_field_name", f"{league} {lane['lane_name']}"),
        ("synonym_query", f"{league} {synonym_terms[0]}"),
        ("official_team_league", f"{league} official {field_group}"),
        ("public_api_docs", f"{league} {lane['lane_name']} api docs"),
        ("github_open_source", f"{league} {lane['lane_name']} github"),
        ("csv_parquet_archive", f"{league} {lane['lane_name']} csv parquet"),
        ("public_pdf_media_guide", f"{league} {lane['lane_name']} pdf media guide"),
        ("structured_wiki_supplemental", f"{league} {lane['lane_name']} wikidata wikipedia"),
        ("dataset_catalog_index", f"{league} {lane['lane_name']} dataset catalog"),
        ("source_specific_terminology", f"{league} {source_family} terminology"),
        ("site_exact_official", f"{lane_label} site:{official_domain}"),
        ("site_exact_github", f"{lane_label} site:github.com"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, query) in enumerate(templates, start=1):
        rows.append(
            {
                "sport": lane["sport"],
                "sport_label": league,
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane.get("field_or_feature_group"),
                "query_family": family,
                "query": query,
                "query_index": index,
                "official_domain": official_domain,
                "source_family": source_family,
            }
        )
    for offset, synonym in enumerate(synonym_terms[1:3], start=len(rows) + 1):
        rows.append(
            {
                "sport": lane["sport"],
                "sport_label": league,
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane.get("field_or_feature_group"),
                "query_family": f"synonym_query_{offset - len(templates) + 1}",
                "query": f"{league} {synonym} dataset",
                "query_index": offset,
                "official_domain": official_domain,
                "source_family": source_family,
            }
        )
    return rows


def build_basketball_source_exhaustion_query_plan(*, sport: str | None = None) -> dict[str, Any]:
    target_lanes = unresolved_lanes() + partial_lanes()
    if sport:
        target_lanes = [lane for lane in target_lanes if lane["sport"] == sport]
    query_rows: list[dict[str, Any]] = []
    per_lane: dict[str, list[dict[str, Any]]] = {}
    for lane in target_lanes:
        rows = _query_records_for_lane(lane)
        per_lane[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "basketball_source_exhaustion_query_plan_v1",
        "sport": sport or "all_basketball",
        "sports_included": [sport] if sport else list(SPORTS),
        "query_rows": query_rows,
        "query_count": len(query_rows),
        "lanes_included": sorted(per_lane),
        "lane_query_index": per_lane,
        "query_families": sorted({row["query_family"] for row in query_rows}),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_basketball_source_exhaustion_queries(sport: str | None = None) -> dict[str, Any]:
    plan = build_basketball_source_exhaustion_query_plan(sport=sport)
    return {
        "ok": True,
        "status": "ok",
        "sport": plan["sport"],
        "sports_included": plan["sports_included"],
        "query_count": plan["query_count"],
        "queries": [row["query"] for row in plan["query_rows"]],
        "query_rows": plan["query_rows"],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }

