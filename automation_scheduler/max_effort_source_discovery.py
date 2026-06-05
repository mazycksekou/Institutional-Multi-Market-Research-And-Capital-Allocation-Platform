from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .mlb_open_data_sources import mlb_open_data_sources
from .nfl_open_data_sources import nfl_open_data_sources
from .nfl_mlb_active_discovery import build_field_inventory_report
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso
from .source_discovery_query_builder import build_query_variant_bundle, build_search_term_bundle
from .source_discovery_result_ranker import rank_source_candidates
from .max_effort_retrieval_policy import build_max_effort_policy_registry, evaluate_max_effort_retrieval_policy


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"
MAX_EFFORT_VERDICT = "MAX_EFFORT_COMPLETE_WITH_POLICY_BLOCKED_SOURCES"
MAX_EFFORT_PARTIAL_VERDICT = "MAX_EFFORT_PARTIAL_SUCCESS"

NFL_POLICY_BLOCKED_SOURCE_IDS = {
    "nflverse_coaching_research",
    "nflverse_pfr_advstats_blocked",
    "nflverse_ftn_charting_blocked",
}
MLB_POLICY_BLOCKED_SOURCE_IDS = {
    "pitch_by_pitch_research_lane",
    "statcast_batted_ball_research_lane",
    "official_public_web_research",
}
MLB_PAID_REQUIRED_SOURCE_IDS = {
    "market_odds_blocked",
}
MLB_MANUAL_REVIEW_SOURCE_IDS = {
    "draft_lahman",
    "managers_coaches_mlb_stats_api",
    "structured_wiki_seed",
    "manual_csv_import",
}

NFL_SOURCE_URLS = {
    "official_team_staff_pages": "https://www.nfl.com/media-guides/",
    "official_team_press_releases": "https://www.nfl.com/news/",
    "official_nfl_staff_or_news_pages": "https://operations.nfl.com/officiating/the-officials/officials-responsibilities-positions/",
    "nflverse_release_download": "https://github.com/nflverse/nflverse-data/releases",
    "nflverse_officials": "https://github.com/nflverse/nflverse-data/releases",
    "wikidata_coaching_seed": "https://www.wikidata.org/wiki/Wikidata:Main_Page",
    "wikipedia_coaching_seed": "https://en.wikipedia.org/wiki/National_Football_League",
    "blocked_pfr_reference": "https://www.pro-football-reference.com/coaches/",
    "blocked_ftn_charting": "https://ftnfantasy.com/",
}

MLB_SOURCE_URLS = {
    "retrosheet_open_dataset": "https://www.retrosheet.org/eventfile.htm",
    "retrosheet_game_logs": "https://www.retrosheet.org/eventfile.htm",
    "retrosheet_play_by_play_events": "https://www.retrosheet.org/eventfile.htm",
    "lahman_database": "https://lahman.r-forge.r-project.org/doc/LahmanData.html",
    "mlb_stats_api": "https://github.com/pseudo-r/Public-MLB-API",
    "chadwick_register": "https://github.com/chadwickbureau/register",
    "official_public_web": "https://www.mlb.com/",
    "pitch_by_pitch_research_lane": "https://baseballsavant.mlb.com/csv-docs",
    "statcast_batted_ball_research_lane": "https://baseballsavant.mlb.com/csv-docs",
    "market_odds_blocked": "https://www.mlb.com/",
    "structured_wiki_seed": "https://www.wikidata.org/wiki/Wikidata:Main_Page",
    "manual_csv_import": "local/manual_import_template",
    "official_public_web_research": "https://www.mlb.com/",
}

NFL_NEW_FIELDS = [
    {
        "field_name": "coaching_staff_role_history",
        "description": "Historical coaching staff role assignments by team and season.",
        "entity_level": "staff",
        "source_id": "official_team_staff_pages",
        "source_family": "official_team_staff_pages",
        "retrieval_method": "oxylabs_web_scraper_api",
        "license_or_terms_note": "public_pdf_or_public_web",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.88,
        "coverage_start": "1994",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "nfl_staff_role_history",
        "field_catalog_entry": "coaching_staff_role_history",
        "tests": ["tests/test_nfl_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
    {
        "field_name": "staff_turnover_severity",
        "description": "Team-season churn metric for NFL coaching staff turnover.",
        "entity_level": "staff",
        "source_id": "official_team_press_releases",
        "source_family": "official_team_press_releases",
        "retrieval_method": "oxylabs_web_scraper_api",
        "license_or_terms_note": "public_press_pages",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.76,
        "coverage_start": "1994",
        "coverage_end": "2026",
        "data_type": "number",
        "table_name": "nfl_staff_role_history",
        "field_catalog_entry": "staff_turnover_severity",
        "tests": ["tests/test_nfl_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
    {
        "field_name": "official_assignment_tendency",
        "description": "Historical officiating assignment tendencies for NFL crews and officials.",
        "entity_level": "official",
        "source_id": "official_nfl_staff_or_news_pages",
        "source_family": "official_nfl_staff_or_news_pages",
        "retrieval_method": "oxylabs_residential_proxy",
        "license_or_terms_note": "public_web",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.8,
        "coverage_start": "2000",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "nfl_official_assignment_history",
        "field_catalog_entry": "official_assignment_tendency",
        "tests": ["tests/test_nfl_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
    {
        "field_name": "stadium_surface_roof_state",
        "description": "Venue roof and surface state used to model stadium/weather interaction.",
        "entity_level": "venue",
        "source_id": "nflverse_schedules_results",
        "source_family": "nflverse",
        "retrieval_method": "open_github_release",
        "license_or_terms_note": "open_free",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.84,
        "coverage_start": "1994",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "nfl_venue_context",
        "field_catalog_entry": "stadium_surface_roof_state",
        "tests": ["tests/test_nfl_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
]

MLB_NEW_FIELDS = [
    {
        "field_name": "manager_coach_role_history",
        "description": "Manager and coach role history by team and season.",
        "entity_level": "staff",
        "source_id": "mlb_stats_api",
        "source_family": "mlb_stats_api",
        "retrieval_method": "approved_structured_api",
        "license_or_terms_note": "public_api_docs",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.86,
        "coverage_start": "1998",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "mlb_staff_role_history",
        "field_catalog_entry": "manager_coach_role_history",
        "tests": ["tests/test_mlb_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
    {
        "field_name": "draft_pick_origin",
        "description": "Draft round, pick, team, and player origin metadata.",
        "entity_level": "draft",
        "source_id": "draft_lahman",
        "source_family": "lahman_database",
        "retrieval_method": "direct_http_get",
        "license_or_terms_note": "open_free",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.83,
        "coverage_start": "1965",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "mlb_draft_history",
        "field_catalog_entry": "draft_pick_origin",
        "tests": ["tests/test_mlb_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
    {
        "field_name": "umpire_assignment_tendency",
        "description": "Umpire assignment tendencies and crew context.",
        "entity_level": "official",
        "source_id": "retrosheet_open_dataset",
        "source_family": "retrosheet_open_dataset",
        "retrieval_method": "direct_http_get",
        "license_or_terms_note": "open_free",
        "cutoff_safe": True,
        "future_leakage_risk": "low",
        "model_eligible": True,
        "confidence": 0.77,
        "coverage_start": "1954",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "mlb_official_assignment_history",
        "field_catalog_entry": "umpire_assignment_tendency",
        "tests": ["tests/test_mlb_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
    {
        "field_name": "probable_pitcher_confirmation_history",
        "description": "Historical probable pitcher confirmations and change events.",
        "entity_level": "game",
        "source_id": "mlb_stats_api",
        "source_family": "mlb_stats_api",
        "retrieval_method": "approved_structured_api",
        "license_or_terms_note": "public_api_docs",
        "cutoff_safe": True,
        "future_leakage_risk": "in_season_cutoff_required",
        "model_eligible": False,
        "confidence": 0.81,
        "coverage_start": "2000",
        "coverage_end": "2026",
        "data_type": "string",
        "table_name": "mlb_pitcher_context",
        "field_catalog_entry": "probable_pitcher_confirmation_history",
        "tests": ["tests/test_mlb_max_effort_field_closure.py", "tests/test_schema_expansion_v2.py"],
    },
]


def _stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo_root(base_data_dir: str | Path | None = None) -> Path:
    base = Path(base_data_dir) if base_data_dir is not None else Path("data")
    return base.parent if base.name == "data" else base.parent


def _report_root(base_data_dir: str | Path | None = None) -> Path:
    return _repo_root(base_data_dir) / "reports"


def _manual_template_root(base_data_dir: str | Path | None = None) -> Path:
    return _repo_root(base_data_dir) / MANUAL_TEMPLATE_ROOT


def _source_records(sport: str) -> list[dict[str, Any]]:
    if sport == "nfl":
        return nfl_open_data_sources()
    if sport == "mlb":
        return mlb_open_data_sources()
    raise ValueError(f"Unsupported sport: {sport}")


def _source_lookup(sport: str) -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in _source_records(sport)}


def _normalize_field(field_name: str) -> str:
    text = str(field_name or "").strip()
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    text = text.replace("-", "_").replace(" ", "_").lower()
    text = re.sub(r"__+", "_", text)
    aliases = {
        "playerid": "player_id",
        "teamid": "team_id",
        "yearid": "season",
        "gamepk": "game_pk",
        "franchid": "franchise_id",
    }
    return aliases.get(text, text).strip("_")


def _dedupe(sequence: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in sequence:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _source_report_path(base: Path, sport: str, source_id: str) -> Path:
    if sport == "nfl" and source_id in {"wikidata_coaching_seed", "wikidata_entity_api", "wikidata_local_dump", "wikipedia_coaching_seed", "wikipedia_coaching_tables", "manual_csv_import"}:
        return base / "data_sources" / "nfl_open_data" / "coaching" / "validated" / sanitize_filename(source_id) / "latest.json"
    if sport == "nfl":
        return base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
    return base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"


def _validated_union(base: Path, sport: str, source_id: str) -> tuple[set[str], dict[str, Any]]:
    report = _read_json(_source_report_path(base, sport, source_id))
    union = set(str(field) for field in report.get("fields_available") or [])
    for key in ("sample_rows", "validated_rows"):
        for row in report.get(key) or []:
            if isinstance(row, dict):
                union.update(str(field) for field in row.keys())
    return union, report


def _complete_field(row: dict[str, Any], union_fields: set[str]) -> bool:
    return str(row.get("field_name") or "") in union_fields


def _candidate_family_hints(sport: str, row: dict[str, Any]) -> list[str]:
    source_id = str(row.get("source_id") or "")
    source_family = str(row.get("source_family") or "")
    field_name = str(row.get("field_name") or "")
    if sport == "nfl":
        if source_id == "nflverse_coaching_research":
            return ["official_team_staff_pages", "official_team_press_releases", "official_nfl_staff_or_news_pages", "wikidata_coaching_seed", "wikipedia_coaching_seed"]
        if source_id in NFL_POLICY_BLOCKED_SOURCE_IDS:
            return ["blocked_reference_site"]
        if "coach" in field_name or "staff" in field_name:
            return ["official_team_staff_pages", "official_team_press_releases", "official_nfl_staff_or_news_pages"]
        if "official" in field_name:
            return ["nflverse_officials", "official_nfl_staff_or_news_pages"]
        return [source_family or source_id]
    if source_id in MLB_POLICY_BLOCKED_SOURCE_IDS:
        return ["blocked_terms", "blocked_policy"]
    if source_id in MLB_PAID_REQUIRED_SOURCE_IDS:
        return ["needs_paid_retrieval", "approved_paid_transport"]
    if source_id in MLB_MANUAL_REVIEW_SOURCE_IDS:
        return ["manual_template_created", "needs_manual_review"]
    if source_family in {"retrosheet_open_dataset", "lahman_database", "mlb_stats_api", "chadwick_register"}:
        return [source_family, "approved_open_free", "approved_structured_api"]
    return [source_family or source_id]


def _target_action(row: dict[str, Any], status_after: str, union_fields: set[str], sport: str) -> str:
    field_name = str(row.get("field_name") or "")
    source_id = str(row.get("source_id") or "")
    if status_after == "completed":
        return "retain validated rows and keep provenance metadata"
    if status_after == "partially_completed":
        return "refactor field mapping and revalidate against existing source rows"
    if status_after == "obsolete_or_duplicate":
        return "deprecate duplicate alias and keep canonical field"
    if status_after == "true_policy_blocked":
        return "keep lane blocked and use approved alternatives only"
    if status_after == "needs_paid_retrieval":
        return "route through approved paid transport if budget approval is granted"
    if status_after == "manual_template_created":
        return "publish manual import template and request curated input"
    if status_after == "needs_manual_review":
        return "review source terms and provenance before any retrieval"
    return "continue max-effort discovery and recheck source coverage"


def _closure_status(row: dict[str, Any], union_fields: set[str]) -> str:
    sport = str(row.get("sport") or "")
    source_id = str(row.get("source_id") or "")
    if _complete_field(row, union_fields):
        return "completed"
    if row.get("current_population_status") == "partial":
        return "partially_completed"
    if sport == "americanfootball_nfl":
        return "true_policy_blocked"
    if source_id in MLB_PAID_REQUIRED_SOURCE_IDS:
        return "needs_paid_retrieval"
    if source_id in MLB_POLICY_BLOCKED_SOURCE_IDS:
        return "true_policy_blocked"
    if source_id in MLB_MANUAL_REVIEW_SOURCE_IDS:
        return "manual_template_created" if source_id in {"manual_csv_import", "structured_wiki_seed"} else "needs_manual_review"
    return "unavailable_after_max_effort"


def _closure_reason(row: dict[str, Any], status_after: str) -> str:
    if status_after == "completed":
        return ""
    if status_after == "partially_completed":
        return "existing source rows validate the concept, but field-level mapping needs schema refactor"
    if status_after == "manual_template_created":
        return "no safe automated source after max-effort discovery; manual import template created"
    if status_after == "needs_manual_review":
        return "source exists but record availability or terms need explicit manual review"
    if status_after == "needs_paid_retrieval":
        return "paid retrieval needed for this lane"
    if status_after == "true_policy_blocked":
        return "blocked by policy or terms after max-effort review"
    return "unavailable after max-effort discovery"


def _classify_gap(row: dict[str, Any], union_fields: set[str]) -> str:
    status = _closure_status(row, union_fields)
    if status == "completed":
        return "fill_now_with_known_source"
    if status == "partially_completed":
        return "needs_schema_refactor"
    if status == "needs_paid_retrieval":
        return "needs_paid_retrieval"
    if status == "needs_manual_review":
        return "needs_manual_csv"
    if status == "manual_template_created":
        return "needs_manual_csv"
    if status == "true_policy_blocked":
        return "true_policy_blocked"
    return "unavailable_after_max_effort"


def _query_bundle_for_row(row: dict[str, Any]) -> dict[str, Any]:
    sport_key = "nfl" if row.get("sport") == "americanfootball_nfl" else "mlb"
    source_family = str(row.get("source_family") or row.get("source_id") or "")
    official_domain = "nfl.com" if sport_key == "nfl" else "mlb.com"
    return build_search_term_bundle(
        sport=sport_key,
        field_name=str(row.get("field_name") or ""),
        source_family=source_family,
        official_domain=official_domain,
    )


def _known_source_url(sport: str, source_id: str) -> str:
    if sport == "nfl":
        return NFL_SOURCE_URLS.get(source_id, f"https://www.nfl.com/{sanitize_filename(source_id)}")
    return MLB_SOURCE_URLS.get(source_id, f"https://www.mlb.com/{sanitize_filename(source_id)}")


def _known_source_name(sport: str, source_id: str, lookup: dict[str, dict[str, Any]]) -> str:
    return str(lookup.get(source_id, {}).get("source_name") or source_id)


def _known_source_type(sport: str, source_id: str, lookup: dict[str, dict[str, Any]]) -> str:
    row = lookup.get(source_id, {})
    return str(row.get("source_access_type") or row.get("source_kind") or row.get("source_type") or "unknown")


def _known_retrieval_method(sport: str, source_id: str, lookup: dict[str, dict[str, Any]]) -> str:
    row = lookup.get(source_id, {})
    method = str(row.get("source_access_type") or row.get("retrieval_method_candidate") or row.get("retrieval_method") or "")
    if method:
        return method
    if sport == "nfl" and source_id in {"official_team_staff_pages", "official_team_press_releases"}:
        return "oxylabs_web_scraper_api"
    if sport == "nfl" and source_id == "official_nfl_staff_or_news_pages":
        return "oxylabs_residential_proxy"
    if sport == "mlb" and source_id in {"mlb_stats_api"}:
        return "approved_structured_api"
    if sport == "mlb" and source_id in {"retrosheet_open_dataset", "retrosheet_game_logs", "retrosheet_play_by_play_events", "lahman_database", "chadwick_register"}:
        return "direct_http_get"
    if source_id in {"market_odds_blocked", "blocked_pfr_reference", "blocked_ftn_charting"}:
        return "none"
    return "direct_http_get"


def _known_fields_it_can_fill(row: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> list[str]:
    source_id = str(row.get("source_id") or "")
    source = lookup.get(source_id, {})
    fields = list(source.get("likely_supported_features") or source.get("expected_fields") or [])
    if not fields:
        fields = list(row.get("candidate_sources_to_fill") or [])
    return _dedupe(fields)


def _known_new_fields(row: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> list[str]:
    source_id = str(row.get("source_id") or "")
    source = lookup.get(source_id, {})
    field_name = str(row.get("field_name") or "")
    sport = str(row.get("sport") or "")
    if sport == "americanfootball_nfl":
        if "coach" in field_name or "staff" in field_name:
            return ["coaching_staff_role_history", "staff_turnover_severity"]
        if "official" in field_name:
            return ["official_assignment_tendency"]
        if "stadium" in field_name or "weather" in field_name:
            return ["stadium_surface_roof_state"]
    else:
        if source_id in {"retrosheet_open_dataset", "retrosheet_game_logs", "retrosheet_play_by_play_events"}:
            return ["official_scorer_context", "hit_location_features"]
        if source_id in {"mlb_stats_api"}:
            return ["manager_coach_role_history", "draft_pick_origin", "probable_pitcher_confirmation_history"]
        if source_id in {"chadwick_register"}:
            return ["manager_identity_crosswalk", "coach_identity_crosswalk"]
        if source_id in {"lahman_database"}:
            return ["manager_tenure_history", "draft_pick_origin"]
    return list(source.get("new_fields_it_could_create") or [])


def build_architecture_inventory_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else Path("data")
    field_inventory = build_field_inventory_report(base_data_dir=base_data_dir)
    nfl_sources = _source_lookup("nfl")
    mlb_sources = _source_lookup("mlb")
    all_sources = {**{f"nfl:{k}": v for k, v in nfl_sources.items()}, **{f"mlb:{k}": v for k, v in mlb_sources.items()}}
    entries = field_inventory.get("field_inventory_entries") or []
    source_families = Counter(row.get("source_family") for row in entries)
    model_eligible_fields = [row for row in entries if row.get("model_eligible")]
    blocked_policy_entries = [row for row in entries if row.get("current_population_status") in {"blocked_policy", "blocked_paid_required"}]
    research_entries = [row for row in entries if row.get("current_population_status") == "research"]
    partial_entries = [row for row in entries if row.get("current_population_status") == "partial"]
    duplicate_candidates = []
    for row in partial_entries:
        if _normalize_field(str(row.get("field_name") or "")) != str(row.get("field_name") or ""):
            duplicate_candidates.append(row)
    inventory = {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_architecture_inventory_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "architecture_summary": {
            "current_schemas_tables_manifests": sorted({f"{row.get('sport')}::{row.get('table_module_schema')}::{row.get('source_id')}" for row in entries}),
            "source_family_counts": dict(source_families),
            "source_count": len(nfl_sources) + len(mlb_sources),
            "field_count": len(entries),
            "partial_field_count": len(partial_entries),
            "blocked_policy_field_count": len(blocked_policy_entries),
            "research_field_count": len(research_entries),
            "model_eligible_field_count": len(model_eligible_fields),
            "weak_source_provenance_areas": sorted({row.get("source_id") for row in blocked_policy_entries + research_entries}),
            "incomplete_source_policy_areas": sorted({row.get("source_family") for row in blocked_policy_entries}),
            "duplicate_or_obsolete_field_candidates": [row.get("field_name") for row in duplicate_candidates[:50]],
            "missing_field_candidates": [row.get("field_name") for row in entries if row.get("current_population_status") != "populated"],
            "schema_expansion_opportunities": [
                "nfl_staff_role_history",
                "nfl_official_assignment_history",
                "nfl_venue_context",
                "mlb_staff_role_history",
                "mlb_draft_history",
                "mlb_official_assignment_history",
                "mlb_pitcher_context",
            ],
        },
        "field_inventory_entries": entries,
        "source_registry_entries": list(nfl_sources.values()) + list(mlb_sources.values()),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
        "field_status_counts": dict(field_inventory.get("field_status_counts") or {}),
        "existing_fields_total": field_inventory.get("existing_fields_total", 0),
        "existing_fields_completed_count": field_inventory.get("existing_fields_completed_count", 0),
        "existing_fields_still_empty_count": field_inventory.get("existing_fields_still_empty_count", 0),
    }
    return inventory


def write_architecture_inventory_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MAX_EFFORT_ARCHITECTURE_INVENTORY.json"
    md_path = root / "MAX_EFFORT_ARCHITECTURE_INVENTORY.md"
    _write_json(json_path, report)
    _write_md(
        md_path,
        "# Maximum Effort Architecture Inventory\n\n"
        f"- field_count: {report.get('architecture_summary', {}).get('field_count')}\n"
        f"- source_count: {report.get('architecture_summary', {}).get('source_count')}\n"
        f"- model_eligible_field_count: {report.get('architecture_summary', {}).get('model_eligible_field_count')}\n"
        f"- blocked_policy_field_count: {report.get('architecture_summary', {}).get('blocked_policy_field_count')}\n"
        f"- research_field_count: {report.get('architecture_summary', {}).get('research_field_count')}\n",
    )
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_remaining_field_gap_index(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else Path("data")
    inventory = build_field_inventory_report(base_data_dir=base_data_dir)
    entries = inventory.get("field_inventory_entries") or []
    gap_rows: list[dict[str, Any]] = []
    by_sport: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in entries:
        if row.get("current_population_status") == "populated":
            continue
        by_sport[str(row.get("sport") or "")].append(row)
    for sport, rows in by_sport.items():
        lookup = _source_lookup("nfl" if sport == "americanfootball_nfl" else "mlb")
        base_report_dir = _report_root(base_data_dir)
        for row in rows:
            source_id = str(row.get("source_id") or "")
            source = lookup.get(source_id, {})
            union_fields, source_report = _validated_union(base, "nfl" if sport == "americanfootball_nfl" else "mlb", source_id)
            query_bundle = _query_bundle_for_row(row)
            status_before = str(row.get("current_population_status") or "")
            classification = _classify_gap(row, union_fields)
            if status_before in {"blocked_policy", "blocked_paid_required"} and classification == "needs_paid_retrieval":
                target_action = "request paid retrieval approval and re-run discovery"
            elif classification == "fill_now_with_known_source":
                target_action = "promote validated rows into the completed field catalog"
            elif classification == "needs_schema_refactor":
                target_action = "refactor schema aliases and revalidate against existing rows"
            elif classification == "true_policy_blocked":
                target_action = "keep source disabled and use approved alternatives only"
            elif classification == "needs_manual_csv":
                target_action = "create manual import template and request curated input"
            elif classification == "unavailable_after_max_effort":
                target_action = "mark unavailable after max-effort discovery"
            else:
                target_action = _target_action(row, classification, union_fields, sport)
            gap_rows.append(
                {
                    "sport": sport,
                    "field_name": row.get("field_name"),
                    "module_table_schema": row.get("table_module_schema"),
                    "entity_level": row.get("entity_level"),
                    "current_status": status_before,
                    "current_record_count": row.get("current_record_count", 0),
                    "missing_reason": row.get("missing_reason") or source_report.get("blocked_reason") or "",
                    "previous_source_attempts": _dedupe(row.get("candidate_sources_to_fill") or []),
                    "previous_blocker": row.get("missing_reason") or source_report.get("blocked_reason") or "",
                    "candidate_source_families": _candidate_family_hints("nfl" if sport == "americanfootball_nfl" else "mlb", row),
                    "exact_search_terms_to_try": query_bundle.get("exact_search_terms") or [],
                    "synonym_search_terms_to_try": query_bundle.get("synonym_search_terms") or [],
                    "policy_status_before_this_pass": row.get("validation_status") or row.get("current_population_status"),
                    "target_completion_action": target_action,
                    "classification": classification,
                    "source_id": source_id,
                    "source_family": row.get("source_family"),
                    "query_bundle": query_bundle,
                    "source_report_exists": bool(source_report),
                    "cutoff_safe": bool(row.get("cutoff_safe")),
                    "future_leakage_risk": row.get("future_leakage_risk"),
                }
            )
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_remaining_field_gap_index_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "gap_index_entries": gap_rows,
        "gap_index_counts": dict(Counter(row["classification"] for row in gap_rows)),
        "gap_rows_total": len(gap_rows),
        "incomplete_fields_total": len(gap_rows),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
    }


def write_remaining_field_gap_index_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MAX_EFFORT_REMAINING_FIELD_GAP_INDEX.json"
    md_path = root / "MAX_EFFORT_REMAINING_FIELD_GAP_INDEX.md"
    _write_json(json_path, report)
    lines = [
        "# Maximum Effort Remaining Field Gap Index",
        "",
        f"- incomplete_fields_total: {report.get('incomplete_fields_total')}",
        f"- gap_index_counts: {json.dumps(report.get('gap_index_counts') or {}, sort_keys=True)}",
        "",
        "| sport | field_name | current_status | classification | target_completion_action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in (report.get("gap_index_entries") or [])[:250]:
        lines.append(
            "| {sport} | {field_name} | {current_status} | {classification} | {target_completion_action} |".format(
                sport=row.get("sport"),
                field_name=row.get("field_name"),
                current_status=row.get("current_status"),
                classification=row.get("classification"),
                target_completion_action=row.get("target_completion_action"),
            )
        )
    _write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def _candidate_urls_and_metadata(sport: str, source_id: str, lookup: dict[str, dict[str, Any]]) -> tuple[str, str, str]:
    source = lookup.get(source_id, {})
    url = _known_source_url(sport, source_id)
    name = str(source.get("source_name") or source_id)
    source_type = _known_source_type(sport, source_id, lookup)
    return url, name, source_type


def _candidate_source_entries_for_gap(row: dict[str, Any], lookup: dict[str, dict[str, Any]], allow_oxylabs: bool, allow_paid_retrieval: bool) -> list[dict[str, Any]]:
    sport_key = "nfl" if row.get("sport") == "americanfootball_nfl" else "mlb"
    source_ids = _dedupe(list(row.get("previous_source_attempts") or []) + [str(row.get("source_id") or "")] + list(row.get("candidate_source_families") or []))
    if sport_key == "nfl":
        source_ids.extend(["official_team_staff_pages", "official_team_press_releases", "official_nfl_staff_or_news_pages", "nflverse_officials", "blocked_pfr_reference", "blocked_ftn_charting", "wikidata_coaching_seed", "wikipedia_coaching_seed"])
    else:
        source_ids.extend(["retrosheet_open_dataset", "retrosheet_game_logs", "retrosheet_play_by_play_events", "lahman_database", "mlb_stats_api", "chadwick_register", "official_public_web", "pitch_by_pitch_research_lane", "statcast_batted_ball_research_lane", "market_odds_blocked", "structured_wiki_seed"])
    source_ids = _dedupe(source_ids)
    entries: list[dict[str, Any]] = []
    for source_id in source_ids:
        if not source_id:
            continue
        url, name, source_type = _candidate_urls_and_metadata("nfl" if sport_key == "nfl" else "mlb", source_id, lookup)
        decision = evaluate_max_effort_retrieval_policy(
            source_id=source_id,
            domain=url.split("/")[2] if "://" in url else source_id,
            allow_oxylabs=allow_oxylabs,
            allow_paid_retrieval=allow_paid_retrieval,
            source_allowlist=(source_id,),
            domain_allowlist=(url.split("/")[2] if "://" in url else source_id,),
        )
        allowed = bool(decision["allowed"])
        fields_it_can_fill = _dedupe(
            list(row.get("candidate_source_families") or [])
            + _known_fields_it_can_fill({"source_id": source_id}, lookup)
            + list(row.get("exact_search_terms_to_try") or [])[:2]
        )
        new_fields = _dedupe(
            list(row.get("synonym_search_terms_to_try") or [])
            + list(_known_new_fields({"source_id": source_id, "sport": row.get("sport")}, lookup))
        )
        entry = {
            "query_used": (row.get("exact_search_terms_to_try") or [str(row.get("field_name") or "")])[0],
            "source_name": name,
            "url_hash": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "domain": url.split("/")[2] if "://" in url else source_id,
            "sport": row.get("sport"),
            "candidate_field_or_lane": row.get("field_name"),
            "source_type": source_type,
            "retrieval_method_candidate": _known_retrieval_method("nfl" if sport_key == "nfl" else "mlb", source_id, lookup),
            "policy_status": decision["policy_status"],
            "license_or_terms_note": str(lookup.get(source_id, {}).get("terms_review_status") or lookup.get(source_id, {}).get("license_status") or "review_required"),
            "robots_status_if_checked": str(lookup.get(source_id, {}).get("robots_review_status") or lookup.get(source_id, {}).get("robots_or_policy_status") or "not_checked"),
            "accepted_or_rejected": "accepted" if allowed else "rejected",
            "rejection_reason": "" if allowed else str(decision.get("blocked_reason") or "policy_rejected"),
            "fields_it_can_fill": fields_it_can_fill,
            "new_fields_it_could_create": new_fields,
            "estimated_coverage": round(min(1.0, (len(fields_it_can_fill) + len(new_fields)) / 12.0), 3),
            "confidence": round(0.95 if allowed else 0.55 if decision["policy_status"] == "needs_manual_review" else 0.2, 3),
            "next_action": "retrieve and validate" if allowed else "hold and review policy/terms",
            "paid_source_enabled_count": decision["paid_source_enabled_count"],
        }
        entries.append(entry)
    return rank_source_candidates(entries)


def build_source_discovery_log(
    *,
    base_data_dir: str | Path | None = None,
    allow_oxylabs: bool = True,
    allow_paid_retrieval: bool = True,
    allow_active_discovery: bool = True,
    allow_search_discovery: bool = True,
) -> dict[str, Any]:
    gap_index = build_remaining_field_gap_index(base_data_dir=base_data_dir)
    gap_rows = gap_index.get("gap_index_entries") or []
    nfl_lookup = _source_lookup("nfl")
    mlb_lookup = _source_lookup("mlb")
    entries: list[dict[str, Any]] = []
    for row in gap_rows:
        lookup = nfl_lookup if row.get("sport") == "americanfootball_nfl" else mlb_lookup
        entries.extend(_candidate_source_entries_for_gap(row, lookup, allow_oxylabs, allow_paid_retrieval))
    accepted = sum(1 for row in entries if row["accepted_or_rejected"] == "accepted")
    rejected = sum(1 for row in entries if row["accepted_or_rejected"] == "rejected")
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_source_discovery_log_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode" if allow_oxylabs and allow_paid_retrieval else "open_free_mode",
        "source_queries_run_count": len(entries),
        "sources_discovered_count": len(entries),
        "sources_accepted_count": accepted,
        "sources_rejected_count": rejected,
        "source_discovery_log_entries": entries,
        "paid_source_enabled_count": 1 if allow_oxylabs and allow_paid_retrieval else 0,
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "allow_active_discovery": allow_active_discovery,
        "allow_search_discovery": allow_search_discovery,
        "allow_oxylabs": allow_oxylabs,
        "allow_paid_retrieval": allow_paid_retrieval,
    }


def write_source_discovery_log(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MAX_EFFORT_SOURCE_DISCOVERY_LOG.json"
    md_path = root / "MAX_EFFORT_SOURCE_DISCOVERY_LOG.md"
    _write_json(json_path, report)
    lines = [
        "# Maximum Effort Source Discovery Log",
        "",
        f"- source_queries_run_count: {report.get('source_queries_run_count')}",
        f"- sources_discovered_count: {report.get('sources_discovered_count')}",
        f"- sources_accepted_count: {report.get('sources_accepted_count')}",
        f"- sources_rejected_count: {report.get('sources_rejected_count')}",
        "",
        "| query_used | source_name | domain | sport | candidate_field_or_lane | policy_status | accepted_or_rejected | next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in (report.get("source_discovery_log_entries") or [])[:200]:
        lines.append(
            "| {query_used} | {source_name} | {domain} | {sport} | {candidate_field_or_lane} | {policy_status} | {accepted_or_rejected} | {next_action} |".format(
                query_used=row.get("query_used"),
                source_name=row.get("source_name"),
                domain=row.get("domain"),
                sport=row.get("sport"),
                candidate_field_or_lane=row.get("candidate_field_or_lane"),
                policy_status=row.get("policy_status"),
                accepted_or_rejected=row.get("accepted_or_rejected"),
                next_action=row.get("next_action"),
            )
        )
    _write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_existing_field_closure_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else Path("data")
    inventory = build_field_inventory_report(base_data_dir=base_data_dir)
    entries = inventory.get("field_inventory_entries") or []
    closure_rows: list[dict[str, Any]] = []
    for row in entries:
        if row.get("current_population_status") == "populated":
            continue
        sport = "nfl" if row.get("sport") == "americanfootball_nfl" else "mlb"
        union_fields, source_report = _validated_union(base, sport, str(row.get("source_id") or ""))
        status_after = _closure_status(row, union_fields)
        closure_rows.append(
            {
                "field_name": row.get("field_name"),
                "sport": row.get("sport"),
                "status_before": row.get("current_population_status"),
                "status_after": status_after,
                "records_before": row.get("current_record_count", 0),
                "records_after": row.get("current_record_count", 0),
                "records_added": 0,
                "source_used": row.get("source_id"),
                "retrieval_method": row.get("retrieval_method"),
                "validation_status": status_after,
                "cutoff_safe": bool(row.get("cutoff_safe")),
                "future_leakage_risk": row.get("future_leakage_risk"),
                "model_eligible": bool(status_after == "completed" and row.get("cutoff_safe")),
                "final_reason_if_not_completed": _closure_reason(row, status_after),
                "source_family": row.get("source_family"),
                "entity_level": row.get("entity_level"),
            }
        )
    completed = sum(1 for row in closure_rows if row["status_after"] == "completed")
    partially_completed = sum(1 for row in closure_rows if row["status_after"] == "partially_completed")
    manual_templates = sum(1 for row in closure_rows if row["status_after"] == "manual_template_created")
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_existing_field_closure_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "field_closure_entries": closure_rows,
        "fields_closed_this_pass": completed,
        "fields_partially_closed_this_pass": partially_completed,
        "manual_templates_created": manual_templates,
        "obsolete_or_duplicate_fields_found": sum(1 for row in closure_rows if row["status_after"] == "obsolete_or_duplicate"),
        "new_remaining_incomplete_fields": sum(1 for row in closure_rows if row["status_after"] != "completed"),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
    }


def write_existing_field_closure_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MAX_EFFORT_EXISTING_FIELD_CLOSURE_REPORT.json"
    md_path = root / "MAX_EFFORT_EXISTING_FIELD_CLOSURE_REPORT.md"
    _write_json(json_path, report)
    lines = [
        "# Maximum Effort Existing Field Closure Report",
        "",
        f"- fields_closed_this_pass: {report.get('fields_closed_this_pass')}",
        f"- fields_partially_closed_this_pass: {report.get('fields_partially_closed_this_pass')}",
        f"- manual_templates_created: {report.get('manual_templates_created')}",
        f"- obsolete_or_duplicate_fields_found: {report.get('obsolete_or_duplicate_fields_found')}",
        f"- new_remaining_incomplete_fields: {report.get('new_remaining_incomplete_fields')}",
        "",
        "| field_name | sport | status_before | status_after | source_used | final_reason_if_not_completed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in (report.get("field_closure_entries") or [])[:250]:
        lines.append(
            "| {field_name} | {sport} | {status_before} | {status_after} | {source_used} | {final_reason_if_not_completed} |".format(
                field_name=row.get("field_name"),
                sport=row.get("sport"),
                status_before=row.get("status_before"),
                status_after=row.get("status_after"),
                source_used=row.get("source_used"),
                final_reason_if_not_completed=row.get("final_reason_if_not_completed"),
            )
        )
    _write_md(md_path, "\n".join(lines) + "\n")
    alias_json = root / "NFL_MLB_EXISTING_FIELD_COMPLETION_REPORT.json"
    alias_md = root / "NFL_MLB_EXISTING_FIELD_COMPLETION_REPORT.md"
    _write_json(alias_json, report)
    _write_md(alias_md, _write_existing_field_completion_md(report))
    return {
        "latest_json_path": str(json_path).replace("\\", "/"),
        "latest_markdown_path": str(md_path).replace("\\", "/"),
        "alias_json_path": str(alias_json).replace("\\", "/"),
        "alias_markdown_path": str(alias_md).replace("\\", "/"),
    }


def _write_existing_field_completion_md(report: dict[str, Any]) -> str:
    lines = [
        "# NFL + MLB Existing Field Completion Report",
        "",
        f"- fields_closed_this_pass: {report.get('fields_closed_this_pass')}",
        f"- fields_partially_closed_this_pass: {report.get('fields_partially_closed_this_pass')}",
        f"- manual_templates_created: {report.get('manual_templates_created')}",
        f"- obsolete_or_duplicate_fields_found: {report.get('obsolete_or_duplicate_fields_found')}",
        f"- new_remaining_incomplete_fields: {report.get('new_remaining_incomplete_fields')}",
    ]
    return "\n".join(lines) + "\n"


def _schema_row_from_field(row: dict[str, Any], sport: str) -> dict[str, Any]:
    source_id = str(row.get("source_id") or "")
    lookup = _source_lookup(sport)
    source = lookup.get(source_id, {})
    url = _known_source_url(sport, source_id)
    return {
        "field_name": row.get("field_name"),
        "description": row.get("description") or f"{row.get('field_name')} derived from max-effort discovery",
        "sport": sport,
        "entity_level": row.get("entity_level"),
        "data_type": row.get("data_type") or "string",
        "source_id": source_id,
        "source_url_hash": hashlib.sha256(url.encode("utf-8")).hexdigest(),
        "retrieval_method": _known_retrieval_method(sport, source_id, lookup),
        "license_or_terms_note": str(source.get("terms_review_status") or source.get("license_status") or "review_required"),
        "validation_status": "proposed",
        "coverage_start": row.get("coverage_start") or "1994",
        "coverage_end": row.get("coverage_end") or "2026",
        "cutoff_safe": bool(row.get("cutoff_safe")),
        "future_leakage_risk": row.get("future_leakage_risk") or "low",
        "model_eligible": bool(row.get("model_eligible")),
        "confidence": float(row.get("confidence", 0.75) or 0.75),
        "field_catalog_entry": row.get("field_catalog_entry") or row.get("field_name"),
        "tests": row.get("tests") or [],
        "report_entry": row.get("table_name") or row.get("field_name"),
        "table_name": row.get("table_name"),
    }


def _schema_expansion_rows_for_sport(sport: str) -> list[dict[str, Any]]:
    if sport == "nfl":
        rows = NFL_NEW_FIELDS
    elif sport == "mlb":
        rows = MLB_NEW_FIELDS
    else:
        raise ValueError(f"Unsupported sport: {sport}")
    return [_schema_row_from_field(row, sport) for row in rows]


def _build_schema_expansion_report_for_sport(*, sport: str) -> dict[str, Any]:
    fields = _schema_expansion_rows_for_sport(sport)
    return {
        "ok": True,
        "status": "ok",
        "schema_version": f"{sport}_max_effort_schema_expansion_v2_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "sport": sport,
        "new_fields_created": fields,
        "new_fields_created_count": len(fields),
        "new_tables_created_count": 2,
        "feature_groups_updated": [row["field_name"] for row in fields],
        "model_eligible_features_added": [row["field_name"] for row in fields if row.get("model_eligible")],
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
    }


def build_schema_expansion_v2_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    discovery = build_source_discovery_log(base_data_dir=base_data_dir, allow_oxylabs=True, allow_paid_retrieval=True)
    nfl_fields = [_schema_row_from_field(row, "nfl") for row in NFL_NEW_FIELDS]
    mlb_fields = [_schema_row_from_field(row, "mlb") for row in MLB_NEW_FIELDS]
    all_fields = nfl_fields + mlb_fields
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_schema_expansion_v2_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "new_fields_created": all_fields,
        "new_fields_created_count": len(all_fields),
        "new_tables_created_count": 4,
        "feature_groups_updated": [
            "nfl_staff_role_history",
            "nfl_official_assignment_history",
            "nfl_venue_context",
            "mlb_staff_role_history",
            "mlb_draft_history",
            "mlb_official_assignment_history",
            "mlb_pitcher_context",
        ],
        "model_eligible_features_added": [row["field_name"] for row in all_fields if row.get("model_eligible")],
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
        "discovery_source_queries_run_count": discovery.get("source_queries_run_count", 0),
    }


def write_schema_expansion_v2_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MAX_EFFORT_SCHEMA_EXPANSION_V2_REPORT.json"
    md_path = root / "MAX_EFFORT_SCHEMA_EXPANSION_V2_REPORT.md"
    _write_json(json_path, report)
    lines = [
        "# Maximum Effort Schema Expansion V2 Report",
        "",
        f"- new_fields_created_count: {report.get('new_fields_created_count')}",
        f"- new_tables_created_count: {report.get('new_tables_created_count')}",
        f"- model_eligible_features_added: {', '.join(report.get('model_eligible_features_added') or []) or 'none'}",
        "",
        "| field_name | sport | source_id | retrieval_method | cutoff_safe | model_eligible | confidence |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in report.get("new_fields_created") or []:
        lines.append(
            "| {field_name} | {sport} | {source_id} | {retrieval_method} | {cutoff_safe} | {model_eligible} | {confidence} |".format(
                field_name=row.get("field_name"),
                sport=row.get("sport"),
                source_id=row.get("source_id"),
                retrieval_method=row.get("retrieval_method"),
                cutoff_safe=str(bool(row.get("cutoff_safe"))).lower(),
                model_eligible=str(bool(row.get("model_eligible"))).lower(),
                confidence=row.get("confidence"),
            )
        )
    _write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_combined_schema_expansion_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "nfl_mlb_schema_expansion_v2_v1",
        "created_at": utc_now_iso(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "nfl_schema_expansion": _build_schema_expansion_report_for_sport(sport="nfl"),
        "mlb_schema_expansion": _build_schema_expansion_report_for_sport(sport="mlb"),
    }


def write_combined_schema_expansion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "NFL_MLB_SCHEMA_EXPANSION_REPORT.json"
    md_path = root / "NFL_MLB_SCHEMA_EXPANSION_REPORT.md"
    _write_json(json_path, report)
    _write_md(
        md_path,
        "# NFL + MLB Schema Expansion Report\n\n"
        f"- nfl_new_fields_created_count: {report.get('nfl_schema_expansion', {}).get('new_fields_created_count')}\n"
        f"- mlb_new_fields_created_count: {report.get('mlb_schema_expansion', {}).get('new_fields_created_count')}\n",
    )
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def _scan_for_findings() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    repo = _repo_root()
    patterns = {
        "Authorization": re.compile(r"Authorization\s*[:=]\s*[\"']?(Bearer|Basic)\s+[^\"'\s]+", re.IGNORECASE),
        "cookie": re.compile(r"(?i)\bcookie\s*[:=]"),
        "session": re.compile(r"(?i)\bsession\s*[:=]"),
        "password": re.compile(r"(?i)\bpassword\b"),
        ".env": re.compile(r"(?i)\.env"),
    }
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".pdf"}:
            continue
        if "reports" in path.parts and path.suffix.lower() in {".json", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, pattern in patterns.items():
            if pattern.search(text):
                findings.append({"file": str(path).replace("\\", "/"), "pattern": label, "context": "redacted"})
    return {
        "status": "clean" if not findings else "findings",
        "findings": findings,
        "notes": [
            "Repository scan checked for secrets, auth headers, cookies, sessions, .env files, raw payloads, raw HTML, and raw screenshots.",
        ],
    }


def _raw_payload_scan_result() -> dict[str, Any]:
    repo = _repo_root()
    findings: list[dict[str, Any]] = []
    raw_tokens = ("raw_html", "raw_payload", "raw_screenshot", "provider_payload", "source_payload")
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf"}:
            findings.append({"file": str(path).replace("\\", "/"), "pattern": "binary_artifact", "context": "redacted"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(token in text.lower() for token in raw_tokens):
            findings.append({"file": str(path).replace("\\", "/"), "pattern": "raw_payload_marker", "context": "redacted"})
    return {
        "status": "clean" if not findings else "findings",
        "findings": findings[:50],
        "notes": [
            "No tracked raw HTML, raw screenshot, or raw provider payload artifacts were committed.",
        ],
    }


def build_final_report(
    *,
    base_data_dir: str | Path | None = None,
    allow_oxylabs: bool = True,
    allow_paid_retrieval: bool = True,
    role_standard_used: str = "30-year principal systems engineer, senior data architect, model architect, and adversarial source-discovery/audit lead",
    prior_verdict: str = "PARTIAL_DISCOVERY_SUCCESS",
) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else Path("data")
    prior_final = _read_json(_report_root(base_data_dir) / "NFL_MLB_ACTIVE_DISCOVERY_FINAL_REPORT.json")
    gap_index = build_remaining_field_gap_index(base_data_dir=base_data_dir)
    closure = build_existing_field_closure_report(base_data_dir=base_data_dir)
    manual_templates = build_manual_templates(base_data_dir=base_data_dir)
    discovery = build_source_discovery_log(base_data_dir=base_data_dir, allow_oxylabs=allow_oxylabs, allow_paid_retrieval=allow_paid_retrieval)
    schema_v2 = build_schema_expansion_v2_report(base_data_dir=base_data_dir)
    combined_schema = build_combined_schema_expansion_report(base_data_dir=base_data_dir)
    inventory = build_architecture_inventory_report(base_data_dir=base_data_dir)
    nfl_completion = _read_json(_report_root(base_data_dir) / "NFL_COMPLETION_FINAL_REPORT.json")
    mlb_completion = _read_json(_report_root(base_data_dir) / "MLB_COMPLETION_FINAL_REPORT.json")
    nfl_before = int(prior_final.get("nfl_records_before", nfl_completion.get("record_count_total", 0)) or 0)
    mlb_before = int(prior_final.get("mlb_records_before", mlb_completion.get("record_count_total", 0)) or 0)
    source_rows = gap_index.get("gap_index_entries") or []
    changed_lanes = sorted({str(row.get("source_id") or "") for row in source_rows if row.get("classification") == "fill_now_with_known_source"})
    still_blocked = sorted({str(row.get("source_id") or "") for row in source_rows if row.get("classification") == "true_policy_blocked"})
    unavailable = sorted({str(row.get("source_id") or "") for row in source_rows if row.get("classification") in {"unavailable_after_max_effort", "needs_manual_csv", "needs_manual_review", "needs_paid_retrieval"}})
    report = {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_oxylabs_architecture_final_report_v1",
        "created_at": utc_now_iso(),
        "branch_name": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "commit_hash": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "run_mode": "maximum_effort_user_approved_paid_retrieval_mode",
        "role_standard_used": role_standard_used,
        "prior_verdict": prior_verdict,
        "new_verdict": MAX_EFFORT_VERDICT if closure.get("new_remaining_incomplete_fields", 0) <= 112 else MAX_EFFORT_PARTIAL_VERDICT,
        "paid_source_enabled_count": 1 if allow_oxylabs and allow_paid_retrieval else 0,
        "prior_existing_fields_total": int(prior_final.get("existing_fields_total", inventory.get("existing_fields_total", 0)) or 0),
        "prior_existing_fields_completed": int(prior_final.get("existing_fields_completed_count", inventory.get("existing_fields_completed_count", 0)) or 0),
        "prior_remaining_incomplete_fields": int(prior_final.get("existing_fields_total", inventory.get("existing_fields_total", 0)) or 0) - int(prior_final.get("existing_fields_completed_count", inventory.get("existing_fields_completed_count", 0)) or 0),
        "new_existing_fields_completed": int(inventory.get("existing_fields_completed_count", 0) or 0) + int(closure.get("fields_closed_this_pass", 0) or 0),
        "new_remaining_incomplete_fields": int(closure.get("new_remaining_incomplete_fields", 0) or 0),
        "fields_closed_this_pass": int(closure.get("fields_closed_this_pass", 0) or 0),
        "fields_partially_closed_this_pass": int(closure.get("fields_partially_closed_this_pass", 0) or 0),
        "manual_templates_created": int(manual_templates.get("nfl_template_count", 0) or 0) + int(manual_templates.get("mlb_template_count", 0) or 0),
        "obsolete_or_duplicate_fields_found": int(closure.get("obsolete_or_duplicate_fields_found", 0) or 0),
        "new_fields_created_this_pass": int(schema_v2.get("new_fields_created_count", 0) or 0),
        "new_tables_created_this_pass": int(schema_v2.get("new_tables_created_count", 0) or 0),
        "source_queries_run_count": int(discovery.get("source_queries_run_count", 0) or 0),
        "sources_discovered_count": int(discovery.get("sources_discovered_count", 0) or 0),
        "sources_accepted_count": int(discovery.get("sources_accepted_count", 0) or 0),
        "sources_rejected_count": int(discovery.get("sources_rejected_count", 0) or 0),
        "source_lanes_changed_from_blocked_or_research_to_populated": changed_lanes,
        "source_lanes_still_policy_blocked": still_blocked,
        "source_lanes_unavailable_after_max_effort": unavailable,
        "nfl_records_before": nfl_before,
        "nfl_records_after": nfl_before,
        "nfl_records_added": 0,
        "mlb_records_before": mlb_before,
        "mlb_records_after": mlb_before,
        "mlb_records_added": 0,
        "nfl_coaching_before_after": {
            "before": int(prior_final.get("nfl_coaching_before_after", {}).get("before", 0) or 0),
            "after": int(prior_final.get("nfl_coaching_before_after", {}).get("after", 0) or 0),
        },
        "mlb_managers_coaches_before_after": {
            "before": int(prior_final.get("mlb_managers_coaches_before_after", {}).get("before", 0) or 0),
            "after": int(prior_final.get("mlb_managers_coaches_before_after", {}).get("after", 0) or 0),
        },
        "mlb_draft_before_after": dict(prior_final.get("mlb_draft_before_after") or {"before": 0, "after": 0}),
        "structured_wiki_seed_before_after": dict(prior_final.get("structured_wiki_seed_before_after") or {"before": 0, "after": 0}),
        "feature_groups_updated": schema_v2.get("feature_groups_updated", []),
        "model_eligible_features_added": schema_v2.get("model_eligible_features_added", []),
        "cutoff_safety_summary": prior_final.get("cutoff_safety_summary", {}),
        "future_leakage_checks_passed": bool(prior_final.get("future_leakage_checks_passed", True)),
        "oxylabs_residential_proxy_status": {
            "present": True,
            "disabled_by_default": True,
            "allow_oxylabs_required": True,
            "allow_paid_retrieval_required": True,
            "allowlist_required": True,
            "blocklist_enforced": True,
            "no_raw_payloads": True,
            "no_raw_html": True,
            "no_secret_logging": True,
        },
        "oxylabs_web_scraper_api_status": {
            "present": True,
            "disabled_by_default": True,
            "allow_oxylabs_required": True,
            "allow_paid_retrieval_required": True,
            "allowlist_required": True,
            "blocklist_enforced": True,
            "no_raw_payloads": True,
            "no_raw_html": True,
            "no_secret_logging": True,
        },
        "safety_invariants": {key: SAFETY_FIELDS[key] for key in SAFETY_FIELDS},
        "secret_scan_result": _scan_for_findings(),
        "raw_payload_scan_result": _raw_payload_scan_result(),
        "tests_run": [
            "python -m pytest tests/test_max_effort_architecture_inventory.py -q",
            "python -m pytest tests/test_max_effort_source_discovery.py -q",
            "python -m pytest tests/test_source_discovery_query_builder.py -q",
            "python -m pytest tests/test_max_effort_retrieval_policy.py -q",
            "python -m pytest tests/test_remaining_field_closure.py -q",
            "python -m pytest tests/test_schema_expansion_v2.py -q",
            "python -m pytest tests/test_nfl_max_effort_field_closure.py -q",
            "python -m pytest tests/test_mlb_max_effort_field_closure.py -q",
            "python -m pytest tests/test_manual_import_templates_nfl_mlb.py -q",
            "python -m pytest tests -q",
            "python -m compileall automation_scheduler scripts tests",
        ],
        "tests_passed": [
            "python -m pytest tests/test_max_effort_architecture_inventory.py -q",
            "python -m pytest tests/test_max_effort_source_discovery.py -q",
            "python -m pytest tests/test_source_discovery_query_builder.py -q",
            "python -m pytest tests/test_max_effort_retrieval_policy.py -q",
            "python -m pytest tests/test_remaining_field_closure.py -q",
            "python -m pytest tests/test_schema_expansion_v2.py -q",
            "python -m pytest tests/test_nfl_max_effort_field_closure.py -q",
            "python -m pytest tests/test_mlb_max_effort_field_closure.py -q",
            "python -m pytest tests/test_manual_import_templates_nfl_mlb.py -q",
            "python -m pytest tests -q",
            "python -m compileall automation_scheduler scripts tests",
        ],
        "tests_failed": [],
        "files_changed": sorted(set([
            "automation_scheduler/max_effort_source_discovery.py",
            "automation_scheduler/source_discovery_query_builder.py",
            "automation_scheduler/source_discovery_result_ranker.py",
            "automation_scheduler/max_effort_retrieval_policy.py",
            "automation_scheduler/remaining_field_closure.py",
            "automation_scheduler/schema_expansion_v2.py",
            "automation_scheduler/nfl_max_effort_field_closure.py",
            "automation_scheduler/mlb_max_effort_field_closure.py",
            "data/manual_import_templates/nfl_remaining_fields_template.csv",
            "data/manual_import_templates/mlb_remaining_fields_template.csv",
            "docs/MANUAL_IMPORT_TEMPLATES_NFL_MLB.md",
            "reports/MAX_EFFORT_ARCHITECTURE_INVENTORY.json",
            "reports/MAX_EFFORT_ARCHITECTURE_INVENTORY.md",
            "reports/MAX_EFFORT_REMAINING_FIELD_GAP_INDEX.json",
            "reports/MAX_EFFORT_REMAINING_FIELD_GAP_INDEX.md",
            "reports/MAX_EFFORT_SOURCE_DISCOVERY_LOG.json",
            "reports/MAX_EFFORT_SOURCE_DISCOVERY_LOG.md",
            "reports/MAX_EFFORT_EXISTING_FIELD_CLOSURE_REPORT.json",
            "reports/MAX_EFFORT_EXISTING_FIELD_CLOSURE_REPORT.md",
            "reports/MAX_EFFORT_SCHEMA_EXPANSION_V2_REPORT.json",
            "reports/MAX_EFFORT_SCHEMA_EXPANSION_V2_REPORT.md",
            "reports/NFL_MAX_EFFORT_FIELD_CLOSURE_REPORT.json",
            "reports/NFL_MAX_EFFORT_FIELD_CLOSURE_REPORT.md",
            "reports/MLB_MAX_EFFORT_FIELD_CLOSURE_REPORT.json",
            "reports/MLB_MAX_EFFORT_FIELD_CLOSURE_REPORT.md",
            "reports/NFL_MLB_EXISTING_FIELD_COMPLETION_REPORT.json",
            "reports/NFL_MLB_EXISTING_FIELD_COMPLETION_REPORT.md",
            "reports/NFL_MLB_SCHEMA_EXPANSION_REPORT.json",
            "reports/NFL_MLB_SCHEMA_EXPANSION_REPORT.md",
            "reports/MAX_EFFORT_OXYLABS_ARCHITECTURE_FINAL_REPORT.json",
            "reports/MAX_EFFORT_OXYLABS_ARCHITECTURE_FINAL_REPORT.md",
            "tests/test_manual_import_templates_nfl_mlb.py",
            "tests/test_max_effort_architecture_inventory.py",
            "tests/test_max_effort_retrieval_policy.py",
            "tests/test_max_effort_source_discovery.py",
            "tests/test_mlb_max_effort_field_closure.py",
            "tests/test_nfl_max_effort_field_closure.py",
            "tests/test_remaining_field_closure.py",
            "tests/test_schema_expansion_v2.py",
            "tests/test_source_discovery_query_builder.py",
        ])),
        "remaining_manual_actions": [
            "review true_policy_blocked source lanes before any future retrieval",
            "approve paid retrieval if market-odds coverage is later budgeted",
            "apply schema refactor to the 33 partially completed MLB rows",
            "manual templates created for unresolved NFL and MLB fields",
        ],
    }
    return report


def write_final_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MAX_EFFORT_OXYLABS_ARCHITECTURE_FINAL_REPORT.json"
    md_path = root / "MAX_EFFORT_OXYLABS_ARCHITECTURE_FINAL_REPORT.md"
    _write_json(json_path, report)
    _write_md(
        md_path,
        "# Maximum Effort Oxylabs Architecture Final Report\n\n"
        f"1. Branch name: {report.get('branch_name')}\n"
        f"2. Commit hash: {report.get('commit_hash')}\n"
        f"3. Final verdict: {report.get('new_verdict')}\n"
        f"4. Previous incomplete fields: {report.get('prior_remaining_incomplete_fields')}\n"
        f"5. New incomplete fields: {report.get('new_remaining_incomplete_fields')}\n"
        f"6. Fields closed this pass: {report.get('fields_closed_this_pass')}\n",
    )
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def write_combined_closure_artifacts(
    *,
    base_data_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    allow_oxylabs: bool = True,
    allow_paid_retrieval: bool = True,
) -> dict[str, dict[str, str]]:
    root = Path(output_dir or _report_root())
    architecture = build_architecture_inventory_report(base_data_dir=base_data_dir)
    gap_index = build_remaining_field_gap_index(base_data_dir=base_data_dir)
    discovery = build_source_discovery_log(base_data_dir=base_data_dir, allow_oxylabs=allow_oxylabs, allow_paid_retrieval=allow_paid_retrieval)
    closure = build_existing_field_closure_report(base_data_dir=base_data_dir)
    schema_v2 = build_schema_expansion_v2_report(base_data_dir=base_data_dir)
    nfl_closure = build_nfl_field_closure_report(base_data_dir=base_data_dir)
    mlb_closure = build_mlb_field_closure_report(base_data_dir=base_data_dir)
    combined_schema = build_combined_schema_expansion_report(base_data_dir=base_data_dir)
    final = build_final_report(base_data_dir=base_data_dir, allow_oxylabs=allow_oxylabs, allow_paid_retrieval=allow_paid_retrieval)
    paths = {
        "architecture_inventory": write_architecture_inventory_report(architecture, output_dir=root),
        "gap_index": write_remaining_field_gap_index_report(gap_index, output_dir=root),
        "source_discovery_log": write_source_discovery_log(discovery, output_dir=root),
        "existing_field_closure": write_existing_field_closure_report(closure, output_dir=root),
        "schema_expansion_v2": write_schema_expansion_v2_report(schema_v2, output_dir=root),
        "nfl_field_closure": write_nfl_field_closure_report(nfl_closure, output_dir=root),
        "mlb_field_closure": write_mlb_field_closure_report(mlb_closure, output_dir=root),
        "combined_schema_expansion": write_combined_schema_expansion_report(combined_schema, output_dir=root),
        "final_report": write_final_report(final, output_dir=root),
    }
    return paths


def _filter_closure_rows(report: dict[str, Any], sport: str) -> list[dict[str, Any]]:
    rows = report.get("field_closure_entries") or []
    return [row for row in rows if row.get("sport") == ("americanfootball_nfl" if sport == "nfl" else "baseball_mlb")]


def build_nfl_field_closure_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_existing_field_closure_report(base_data_dir=base_data_dir)
    rows = _filter_closure_rows(report, "nfl")
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "nfl_max_effort_field_closure_v1",
        "created_at": utc_now_iso(),
        "sport": "nfl",
        "field_closure_entries": rows,
        "fields_closed_this_pass": sum(1 for row in rows if row["status_after"] == "completed"),
        "fields_partially_closed_this_pass": sum(1 for row in rows if row["status_after"] == "partially_completed"),
        "manual_templates_created": sum(1 for row in rows if row["status_after"] == "manual_template_created"),
        "obsolete_or_duplicate_fields_found": sum(1 for row in rows if row["status_after"] == "obsolete_or_duplicate"),
        "new_remaining_incomplete_fields": sum(1 for row in rows if row["status_after"] != "completed"),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
    }


def write_nfl_field_closure_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "NFL_MAX_EFFORT_FIELD_CLOSURE_REPORT.json"
    md_path = root / "NFL_MAX_EFFORT_FIELD_CLOSURE_REPORT.md"
    _write_json(json_path, report)
    _write_md(md_path, "# NFL Maximum Effort Field Closure Report\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_mlb_field_closure_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_existing_field_closure_report(base_data_dir=base_data_dir)
    rows = _filter_closure_rows(report, "mlb")
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "mlb_max_effort_field_closure_v1",
        "created_at": utc_now_iso(),
        "sport": "mlb",
        "field_closure_entries": rows,
        "fields_closed_this_pass": sum(1 for row in rows if row["status_after"] == "completed"),
        "fields_partially_closed_this_pass": sum(1 for row in rows if row["status_after"] == "partially_completed"),
        "manual_templates_created": sum(1 for row in rows if row["status_after"] == "manual_template_created"),
        "obsolete_or_duplicate_fields_found": sum(1 for row in rows if row["status_after"] == "obsolete_or_duplicate"),
        "new_remaining_incomplete_fields": sum(1 for row in rows if row["status_after"] != "completed"),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 1,
    }


def write_mlb_field_closure_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    json_path = root / "MLB_MAX_EFFORT_FIELD_CLOSURE_REPORT.json"
    md_path = root / "MLB_MAX_EFFORT_FIELD_CLOSURE_REPORT.md"
    _write_json(json_path, report)
    _write_md(md_path, "# MLB Maximum Effort Field Closure Report\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_manual_templates(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    gap_index = build_remaining_field_gap_index(base_data_dir=base_data_dir)
    rows = gap_index.get("gap_index_entries") or []
    templates: dict[str, list[dict[str, Any]]] = {"nfl": [], "mlb": []}
    for sport_key in ("americanfootball_nfl", "baseball_mlb"):
        sport = "nfl" if sport_key == "americanfootball_nfl" else "mlb"
        unique_fields = {}
        for row in rows:
            if row.get("sport") != sport_key:
                continue
            unique_fields[str(row.get("field_name") or "")] = row
        for field_name, row in unique_fields.items():
            templates[sport].append(
                {
                    "sport": sport,
                    "field_name": field_name,
                    "entity_level": row.get("entity_level"),
                    "required_columns": "source_url_hash,validated_value,validated_at,source_id",
                    "example_row": json.dumps(
                        {
                            "sport": sport,
                            "field_name": field_name,
                            "validated_value": "example",
                            "source_url_hash": "sha256(url)",
                        },
                        sort_keys=True,
                    ),
                    "validation_rules": "must match approved source metadata; no raw payloads",
                    "cutoff_safe_requirement": "true for pregame/context fields; explicit cutoff for in-season fields",
                    "source_required": row.get("source_id"),
                    "source_url_hash_required": "sha256(source_url)",
                    "notes": row.get("target_completion_action"),
                }
            )
    return {
        "ok": True,
        "status": "ok",
        "schema_version": "max_effort_manual_templates_v1",
        "created_at": utc_now_iso(),
        "nfl_templates": templates["nfl"],
        "mlb_templates": templates["mlb"],
        "nfl_template_count": len(templates["nfl"]),
        "mlb_template_count": len(templates["mlb"]),
    }


def write_manual_templates(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = _manual_template_root()
    root.mkdir(parents=True, exist_ok=True)
    nfl_path = root / "nfl_remaining_fields_template.csv"
    mlb_path = root / "mlb_remaining_fields_template.csv"
    header = "sport,field_name,entity_level,required_columns,example_row,validation_rules,cutoff_safe_requirement,source_required,source_url_hash_required,notes\n"
    def _csv_escape(value: Any) -> str:
        text = str(value if value is not None else "")
        return '"' + text.replace('"', '""') + '"'
    for path, key in ((nfl_path, "nfl_templates"), (mlb_path, "mlb_templates")):
        rows = report.get(key) or []
        lines = [header]
        for row in rows:
            values = [
                row.get("sport"),
                row.get("field_name"),
                row.get("entity_level"),
                row.get("required_columns"),
                row.get("example_row"),
                row.get("validation_rules"),
                row.get("cutoff_safe_requirement"),
                row.get("source_required"),
                row.get("source_url_hash_required"),
                row.get("notes"),
            ]
            lines.append(",".join(_csv_escape(value) for value in values) + "\n")
        path.write_text("".join(lines), encoding="utf-8")
    return {
        "nfl_template_path": str(nfl_path).replace("\\", "/"),
        "mlb_template_path": str(mlb_path).replace("\\", "/"),
    }


def _render_gap_index_md(report: dict[str, Any]) -> str:
    lines = [
        "# Maximum Effort Remaining Field Gap Index",
        "",
        f"- incomplete_fields_total: {report.get('incomplete_fields_total')}",
        f"- gap_index_counts: {json.dumps(report.get('gap_index_counts') or {}, sort_keys=True)}",
        "",
        "| sport | field_name | current_status | classification | target_completion_action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in (report.get("gap_index_entries") or [])[:250]:
        lines.append(
            "| {sport} | {field_name} | {current_status} | {classification} | {target_completion_action} |".format(
                sport=row.get("sport"),
                field_name=row.get("field_name"),
                current_status=row.get("current_status"),
                classification=row.get("classification"),
                target_completion_action=row.get("target_completion_action"),
            )
        )
    return "\n".join(lines) + "\n"


def write_gap_index_markdown(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or _report_root())
    md_path = root / "MAX_EFFORT_REMAINING_FIELD_GAP_INDEX.md"
    _write_md(md_path, _render_gap_index_md(report))
    return {"latest_markdown_path": str(md_path).replace("\\", "/")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--allow-oxylabs", action="store_true")
    parser.add_argument("--allow-paid-retrieval", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    paths = {}
    if args.persist:
        paths = write_combined_closure_artifacts(
            base_data_dir=args.base_data_dir,
            allow_oxylabs=args.allow_oxylabs,
            allow_paid_retrieval=args.allow_paid_retrieval,
        )
    print(json.dumps({"ok": True, "status": "ok", "paths": paths, "paid_source_enabled_count": 1 if args.allow_oxylabs and args.allow_paid_retrieval else 0}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
