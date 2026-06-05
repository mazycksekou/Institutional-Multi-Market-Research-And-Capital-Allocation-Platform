from __future__ import annotations

from typing import Any

from .tennis_free_vs_paid_readiness import tennis_lane_catalog


LANE_SYNONYMS: dict[str, list[str]] = {
    "atp_match_results": ["tennis open data match results", "ATP match data CSV", "historical ATP results csv"],
    "wta_match_results": ["WTA match data CSV", "historical WTA results csv", "women tennis results dataset"],
    "player_identity_crosswalk": ["tennis player ids", "tennis player crosswalk", "tennis player metadata dataset"],
    "tournament_surface_round_context": ["tennis tournament draw data", "surface dataset", "round context dataset"],
    "serve_return_match_stats": ["tennis serve return stats public data", "serve percentage dataset", "return points won dataset"],
    "break_hold_derivations": ["tennis break hold stats public data", "break points saved dataset", "hold rate tennis data"],
    "ranking_snapshot_history": ["tennis player rankings historical data", "ATP rankings history csv", "WTA rankings history csv"],
    "recent_form_rest_fatigue": ["tennis recent form dataset", "rest days tennis data", "fatigue tennis model features"],
    "head_to_head_context": ["tennis head to head open dataset", "head-to-head tennis csv", "tennis rivalry dataset"],
    "retirement_walkover_context": ["tennis retirement walkover data", "retirement scorelines tennis", "walkover tennis data"],
    "grand_slam_best_of_context": ["Grand Slam draw data", "best-of-five tennis data", "Grand Slam format context"],
    "point_by_point_charting_context": ["Match Charting Project tennis", "tennis point by point data", "tennis rally data github"],
    "player_metadata_handedness_country": ["Wikidata tennis players", "Wikipedia tennis player list", "tennis handedness metadata"],
    "official_rankings_stats_pages": ["tennis API docs", "official ATP stats page", "official WTA rankings page"],
    "injury_withdrawal_availability": ["tennis injuries withdrawals public data", "ITF withdrawals public pages", "tennis player availability news"],
    "chair_umpire_assignments": ["tennis umpire assignments public pages", "Grand Slam officials assignments", "chair umpire tennis"],
    "court_speed_environment_context": ["tennis surface court speed data", "tennis indoor outdoor context", "roof status tennis data"],
    "historical_odds_context": ["tennis-data.co.uk odds history", "tennis historical odds csv", "tennis market archive"],
    "tracking_shot_pattern_context": ["tennis tracking data vendor", "tennis shot pattern paid feed", "tennis player prop features vendor"],
    "unofficial_reference_tables": ["Tennis Abstract terms", "Ultimate Tennis Statistics terms", "tennis reference tables"],
    "community_duplicate_mirror": ["Jeff Sackmann mirror github", "duplicate tennis data mirror", "community tennis dataset mirror"],
}

QUERY_FAMILIES = (
    "open_data_match_results",
    "atp_match_data_csv",
    "wta_match_data_csv",
    "serve_return_stats_public_data",
    "break_hold_stats_public_data",
    "rankings_historical_data",
    "injuries_withdrawals_public_data",
    "retirement_walkover_data",
    "tournament_draw_data",
    "surface_court_speed_data",
    "head_to_head_open_dataset",
    "odds_free_model_features_github",
    "public_data_dictionary",
    "public_api_docs",
    "source_terms_license_robots",
    "source_attribution_rules",
    "source_commercial_use_rules",
)


def _query_records_for_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
    tour_label = str(lane.get("tour") or "Tennis")
    lane_label = lane["lane_name"].replace("_", " ")
    field_group = str(lane.get("field_or_feature_group") or lane_label)
    synonym_terms = list(LANE_SYNONYMS.get(lane["lane_name"], []))
    if field_group not in synonym_terms:
        synonym_terms.insert(0, field_group)
    if lane_label not in synonym_terms:
        synonym_terms.insert(1 if synonym_terms else 0, lane_label)
    official_domain = "atptour.com" if "ATP" in tour_label else "wtatennis.com" if "WTA" in tour_label else "wimbledon.com"
    templates = [
        ("open_data_match_results", f"{tour_label} tennis open data match results {lane_label}"),
        ("atp_match_data_csv", f"ATP match data CSV {lane_label}"),
        ("wta_match_data_csv", f"WTA match data CSV {lane_label}"),
        ("serve_return_stats_public_data", f"tennis serve return stats public data {lane_label}"),
        ("break_hold_stats_public_data", f"tennis break hold stats public data {lane_label}"),
        ("rankings_historical_data", f"tennis player rankings historical data {lane_label}"),
        ("injuries_withdrawals_public_data", f"tennis injuries withdrawals public data {lane_label}"),
        ("retirement_walkover_data", f"tennis retirement walkover data {lane_label}"),
        ("tournament_draw_data", f"tennis tournament draw data {lane_label}"),
        ("surface_court_speed_data", f"tennis surface court speed data {lane_label}"),
        ("head_to_head_open_dataset", f"tennis head-to-head open dataset {lane_label}"),
        ("odds_free_model_features_github", f"tennis odds-free model features GitHub {lane_label}"),
        ("public_data_dictionary", f"tennis public data dictionary {lane_label}"),
        ("public_api_docs", f"tennis API docs {lane_label}"),
        ("source_terms_license_robots", f"{field_group} terms license robots"),
        ("source_attribution_rules", f"{field_group} attribution requirement tennis data"),
        ("source_commercial_use_rules", f"{field_group} commercial use tennis data"),
        ("site_exact_official", f"{lane_label} site:{official_domain}"),
        ("site_exact_github", f"{lane_label} site:github.com"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, query) in enumerate(templates, start=1):
        rows.append(
            {
                "sport": lane["sport"],
                "tour": lane["tour"],
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


def build_tennis_source_exhaustion_query_plan() -> dict[str, Any]:
    lanes = tennis_lane_catalog()
    query_rows: list[dict[str, Any]] = []
    lane_index: dict[str, list[dict[str, Any]]] = {}
    for lane in lanes:
        rows = _query_records_for_lane(lane)
        lane_index[f"{lane['sport']}::{lane['lane_name']}"] = rows
        query_rows.extend(rows)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "TENNIS_SOURCE_EXHAUSTION_QUERY_PLAN",
        "schema_version": "tennis_source_exhaustion_query_plan_v1",
        "sport": "tennis",
        "tours_included": sorted({lane["tour"] for lane in lanes}),
        "query_rows": query_rows,
        "query_count": len(query_rows),
        "minimum_query_count_satisfied": len(query_rows) >= 100,
        "lanes_included": sorted(lane_index),
        "lane_query_index": lane_index,
        "query_families": sorted({row["query_family"] for row in query_rows}),
        "required_query_families": list(QUERY_FAMILIES),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_tennis_source_exhaustion_queries() -> dict[str, Any]:
    plan = build_tennis_source_exhaustion_query_plan()
    return {
        "ok": True,
        "status": "ok",
        "sport": "tennis",
        "query_count": plan["query_count"],
        "queries": [row["query"] for row in plan["query_rows"]],
        "query_rows": plan["query_rows"],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
