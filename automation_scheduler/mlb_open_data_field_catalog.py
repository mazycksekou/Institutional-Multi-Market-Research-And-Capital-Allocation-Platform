from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .mlb_open_data_common import MLB_MODULE, mlb_atomic_write_json, mlb_atomic_write_text, mlb_read_json, mlb_rel, mlb_report_root, mlb_validated_root, mlb_safe_payload
from .mlb_open_data_sources import mlb_open_data_sources
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_OPEN_DATA_FIELD_CATALOG_SCHEMA_VERSION = "mlb_open_data_field_catalog_v1"

FEATURE_FAMILIES = [
    "schedule_results",
    "run_scoring_profile",
    "pitching_profile",
    "batting_profile",
    "fielding_profile",
    "bullpen_usage",
    "starting_pitcher_profile",
    "player_availability",
    "roster_continuity",
    "lineup_stability",
    "park_factor",
    "stadium_weather",
    "umpire_officials",
    "pitch_by_pitch",
    "batted_ball_profile",
    "statcast_quality",
    "base_running",
    "defense_alignment",
    "injuries",
    "transactions",
    "postseason_labels",
    "standings_context",
    "managers_coaches",
    "team_identity",
    "people_identifiers",
    "market_odds",
]

LEAKAGE_MARKERS = ("score", "result", "winner", "odds", "moneyline", "spread", "total_line", "postseason", "playoff", "lineup", "injury")

STRUCTURAL_FIELDS = {
    "season",
    "year",
    "yearid",
    "game_id",
    "game_pk",
    "gamepk",
    "play_id",
    "pitch_number",
    "inning",
    "team",
    "team_id",
    "teamid",
    "teamID",
    "player_id",
    "playerid",
    "playerID",
    "person_id",
    "batter",
    "pitcher",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "runs_scored",
    "runs_allowed",
    "park_id",
    "franchid",
    "wikidata_qid",
    "page_id",
}

BASELINE_EXISTING_MLB_FIELDS = {
    "game_id",
    "game_pk",
    "season",
    "event_date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "winner",
    "final_result",
    "final_margin",
    "total_runs",
    "play_id",
    "inning",
    "team",
    "team_id",
    "player_id",
    "pitcher",
    "batter",
    "pitch_type",
    "launch_speed",
    "launch_angle",
    "exit_velocity",
    "park_id",
    "park_name",
    "stadium",
    "temperature",
    "wind_speed",
    "moneyline",
    "spread_line",
    "total_line",
    "manager_name",
    "franchid",
    "wikidata_qid",
    "wikipedia_title",
    "playerID",
    "yearID",
    "teamID",
    "key_mlbam",
    "key_bbref",
    "key_retro",
    "xwoba",
    "barrel_rate",
    "hard_hit_rate",
    "pitch_run_value",
    "starter_fip_proxy",
    "bullpen_quality_score",
    "park_run_environment_score",
    "umpire_zone_modifier",
    "sprint_speed",
    "stolen_base_attempt_rate",
}


def _validated_latest_path(source_id: str, base: Path) -> Path:
    return base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _canonical_field_name(field: str) -> str:
    text = str(field).strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "gameday": "event_date",
        "game_date": "event_date",
        "gamepk": "game_pk",
        "teamid": "team_id",
        "playerid": "player_id",
        "yearid": "season",
        "franchid": "franchise_id",
        "key_mlbam": "player_id",
        "key_bbref": "bbref_id",
        "key_retro": "retrosheet_id",
        "playerID": "player_id",
        "teamID": "team_id",
    }
    return aliases.get(text, text)


def _family_for(source: dict[str, Any], field: str) -> str:
    category = str(source.get("data_category") or "")
    lower = str(field).lower()
    if category in {"schedules_results", "game_logs"}:
        if any(token in lower for token in ("game_type", "postseason", "playoff")):
            return "postseason_labels"
        return "schedule_results"
    if category == "play_by_play_events":
        return "pitch_by_pitch"
    if category == "pitch_by_pitch":
        return "pitch_by_pitch"
    if category == "batting_stats":
        return "batting_profile"
    if category == "pitching_stats":
        return "pitching_profile"
    if category == "fielding_stats":
        return "fielding_profile"
    if category == "team_stats":
        return "run_scoring_profile" if any(token in lower for token in ("runs", "score", "win", "loss")) else "standings_context"
    if category == "player_master":
        return "people_identifiers"
    if category in {"rosters", "lineups", "probable_pitchers", "starting_pitchers"}:
        return "roster_continuity" if category == "rosters" else "lineup_stability" if category == "lineups" else "starting_pitcher_profile"
    if category == "transactions":
        return "transactions"
    if category == "injuries":
        return "injuries"
    if category == "bullpen_usage":
        return "bullpen_usage"
    if category == "defensive_positions":
        return "defense_alignment"
    if category == "park_factors":
        return "park_factor"
    if category in {"stadiums", "weather"}:
        return "stadium_weather"
    if category == "umpires_officials":
        return "umpire_officials"
    if category == "postseason_labels":
        return "postseason_labels"
    if category == "standings":
        return "standings_context"
    if category == "awards_allstar":
        return "managers_coaches"
    if category == "draft":
        return "team_identity"
    if category == "minor_league_links":
        return "people_identifiers"
    if category == "statcast_batted_ball":
        return "batted_ball_profile" if any(token in lower for token in ("launch", "hit_distance", "bb_type")) else "statcast_quality"
    if category == "market_odds":
        return "market_odds"
    if category == "managers_coaches":
        return "managers_coaches"
    if category == "franchises":
        return "team_identity"
    if category == "people_identifiers":
        return "people_identifiers"
    if category == "structured_wiki_seed":
        if any(token in lower for token in ("qid", "wikidata", "page_id")):
            return "people_identifiers"
        if any(token in lower for token in ("park", "stadium", "venue")):
            return "stadium_weather"
        if any(token in lower for token in ("manager", "coach")):
            return "managers_coaches"
        return "team_identity"
    if category == "official_public_web_research":
        return "managers_coaches"
    return "team_identity"


def _leakage_risk(field: str, family: str) -> str:
    lower = str(field).lower()
    if family == "market_odds":
        return "market_timing_cutoff_required"
    if any(marker in lower for marker in LEAKAGE_MARKERS):
        return "target_or_postgame_field_requires_cutoff"
    if family in {"pitch_by_pitch", "batted_ball_profile", "statcast_quality", "roster_continuity", "lineup_stability", "player_availability", "bullpen_usage", "starting_pitcher_profile", "injuries", "defense_alignment"}:
        return "in_season_cutoff_required"
    return "low"


def _field_entry(source: dict[str, Any], field_name: str, *, verified: bool, data_type: str | None = None, seasons_available: list[str] | None = None) -> dict[str, Any]:
    family = _family_for(source, field_name)
    canonical = _canonical_field_name(field_name)
    structural = canonical in STRUCTURAL_FIELDS or str(field_name).lower() in STRUCTURAL_FIELDS
    leakage = _leakage_risk(field_name, family)
    verified_and_allowed = bool(verified and source.get("current_phase_allowed"))
    if family == "market_odds":
        target_leakage_safe = False
        cutoff_required = True
    elif structural:
        target_leakage_safe = True
        cutoff_required = False
    else:
        target_leakage_safe = leakage == "low"
        cutoff_required = leakage != "low"
    blocker = None
    if not verified:
        blocker = "field_not_verified_by_sample"
    elif not verified_and_allowed:
        blocker = "source_not_current_phase_allowed"
    return {
        "field_name": str(field_name),
        "canonical_field_name": canonical,
        "source_id": source["source_id"],
        "source_family": source.get("source_family"),
        "data_category": source.get("data_category"),
        "module": MLB_MODULE,
        "description": "verified source field" if verified else "expected candidate field pending source sample verification",
        "granularity": source.get("expected_granularity"),
        "join_keys": list(source.get("expected_join_keys") or []),
        "seasons_available": list(seasons_available or []),
        "nullable": True,
        "data_type": data_type or "unknown",
        "raw_field_allowed": bool(verified),
        "normalized_field_supported": bool(verified_and_allowed),
        "model_feature_family": family,
        "pattern_feature_family": family,
        "validation_use_case": "coverage_and_ingestion_only",
        "leakage_risk": leakage,
        "target_leakage_safe": target_leakage_safe,
        "requires_season_cutoff": cutoff_required,
        "source_status": "verified" if verified else "unverified",
        "implementation_status": "available" if verified_and_allowed else "research_required",
        "current_phase_allowed": bool(verified_and_allowed),
        "blocker": blocker,
        "structural_or_join_key": structural,
        "derived_feature_candidate": bool(verified and not structural and family not in {"market_odds"}),
        "pattern_feature_candidate": bool(verified and not structural and family not in {"market_odds"}),
        "validation_feature_candidate": bool(verified and not structural and family in {"team_identity", "people_identifiers", "park_factor", "stadium_weather", "standings_context"}),
    }


def build_mlb_open_data_field_catalog(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else None
    entries: list[dict[str, Any]] = []
    verified_sources: list[str] = []
    for source in mlb_open_data_sources():
        latest = _read_json(_validated_latest_path(source["source_id"], base or Path(".")))
        verified_fields = list((latest or {}).get("fields_available") or [])
        field_types = dict((latest or {}).get("field_types") or {})
        seasons = [str(item) for item in list((latest or {}).get("seasons_available") or [])]
        if verified_fields:
            verified_sources.append(source["source_id"])
            for field in verified_fields:
                entries.append(_field_entry(source, str(field), verified=True, data_type=str(field_types.get(field) or "unknown"), seasons_available=seasons))
        else:
            expected_fields = list(source.get("expected_fields") or [])
            for field in expected_fields:
                entries.append(_field_entry(source, str(field), verified=False))
    families = sorted({entry["model_feature_family"] for entry in entries})
    verified = sum(1 for entry in entries if entry["source_status"] == "verified")
    unverified = sum(1 for entry in entries if entry["source_status"] == "unverified")
    cutoff_sensitive = sum(1 for entry in entries if entry["source_status"] == "verified" and entry["requires_season_cutoff"])
    leakage_sensitive = sum(1 for entry in entries if entry["source_status"] == "verified" and entry["leakage_risk"] != "low")
    target_leakage_safe = sum(1 for entry in entries if entry["source_status"] == "verified" and entry["target_leakage_safe"])
    fields_by_feature_family: dict[str, int] = {}
    for entry in entries:
        if entry["source_status"] != "verified":
            continue
        family = str(entry["model_feature_family"])
        fields_by_feature_family[family] = fields_by_feature_family.get(family, 0) + 1
    derived_candidates = sum(1 for entry in entries if entry["derived_feature_candidate"])
    pattern_candidates = sum(1 for entry in entries if entry["pattern_feature_candidate"])
    validation_candidates = sum(1 for entry in entries if entry["validation_feature_candidate"])
    join_keys = sorted({str(key) for source in mlb_open_data_sources() for key in (source.get("expected_join_keys") or [])})
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_OPEN_DATA_FIELD_CATALOG_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"mlb_open_data_field_catalog_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
            "module": MLB_MODULE,
            "runtime_data_dir": str(base_data_dir) if base_data_dir is not None else None,
            "field_entries_created": len(entries),
            "total_field_count": len(entries),
            "verified_field_count": verified,
            "verified_source_count": len(verified_sources),
            "verified_sources": verified_sources,
            "unverified_field_count": unverified,
            "cutoff_sensitive_field_count": cutoff_sensitive,
            "leakage_sensitive_field_count": leakage_sensitive,
            "target_leakage_safe_field_count": target_leakage_safe,
            "derived_feature_candidate_count": derived_candidates,
            "pattern_feature_candidate_count": pattern_candidates,
            "validation_feature_candidate_count": validation_candidates,
            "fields_by_feature_family": dict(sorted(fields_by_feature_family.items())),
            "join_keys": join_keys,
            "feature_families_covered": families,
            "entries": entries,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "provider_write": False,
            "execution_allowed": False,
        }
    )


def build_existing_mlb_field_index(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else Path(".")
    catalog = build_mlb_open_data_field_catalog(base_data_dir=base_data_dir)
    source_field_names: set[str] = {field.lower() for field in BASELINE_EXISTING_MLB_FIELDS}
    canonical_field_names: set[str] = {_canonical_field_name(field) for field in BASELINE_EXISTING_MLB_FIELDS}
    by_source: dict[str, set[str]] = {}
    seasons_by_canonical: dict[str, set[str]] = {}
    join_keys: set[str] = set()
    for entry in catalog.get("entries") or []:
        if entry.get("source_status") != "verified":
            continue
        field_name = str(entry.get("field_name"))
        canonical = str(entry.get("canonical_field_name"))
        source_field_names.add(field_name.lower())
        canonical_field_names.add(canonical)
        by_source.setdefault(str(entry.get("source_id")), set()).add(field_name.lower())
        seasons_by_canonical.setdefault(canonical, set()).update(str(s) for s in entry.get("seasons_available") or [])
        if entry.get("structural_or_join_key"):
            join_keys.add(canonical)
    return {
        "source_field_names": source_field_names,
        "canonical_field_names": canonical_field_names,
        "by_source": by_source,
        "seasons_by_canonical": seasons_by_canonical,
        "join_keys": join_keys,
        "verified_field_count": int(catalog.get("verified_field_count", 0) or 0),
    }


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = Path(base_data_dir) if base_data_dir is not None else None
    root = (base / "data_sources" / "mlb_open_data" / "field_catalog") if base is not None else mlb_report_root(subdir="field_catalog")
    root.mkdir(parents=True, exist_ok=True)
    return root


def compare_candidate_fields_to_existing_catalog(candidate_fields: list[dict[str, Any]], *, base_data_dir: str | Path | None = None, existing_index: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    index = existing_index if existing_index is not None else build_existing_mlb_field_index(base_data_dir=base_data_dir)
    results: list[dict[str, Any]] = []
    for field in candidate_fields:
        field_name = str(field.get("field_name") or "")
        canonical = _canonical_field_name(field_name)
        lower = field_name.lower()
        candidate_seasons = {str(season) for season in field.get("seasons_available") or []}
        is_join_key = bool(field.get("join_key"))
        exact_duplicate = lower in index.get("source_field_names", set())
        canonical_duplicate = (not exact_duplicate) and canonical in index.get("canonical_field_names", set())
        existing_seasons = index.get("seasons_by_canonical", {}).get(canonical, set())
        new_season_coverage = bool(candidate_seasons - existing_seasons) if (exact_duplicate or canonical_duplicate) else False
        new_join_key = is_join_key and canonical not in index.get("join_keys", set())
        new_entity_coverage = bool(field.get("new_entity_coverage"))
        higher_quality_replacement = bool(field.get("higher_quality_replacement"))
        new_granularity = bool(field.get("new_granularity"))
        if exact_duplicate:
            novelty = "exact_duplicate"
        elif canonical_duplicate:
            novelty = "canonical_duplicate"
        elif higher_quality_replacement:
            novelty = "higher_quality_replacement"
        elif new_season_coverage:
            novelty = "new_season_coverage"
        elif new_join_key:
            novelty = "new_join_key"
        elif new_entity_coverage:
            novelty = "new_entity_coverage"
        elif new_granularity:
            novelty = "new_granularity"
        else:
            novelty = "new_field"
        ingestible = novelty not in {"exact_duplicate", "canonical_duplicate"}
        results.append(
            {
                "field_name": field_name,
                "canonical_field_name": canonical,
                "exact_duplicate": exact_duplicate,
                "canonical_duplicate": canonical_duplicate,
                "equivalent_existing_field": canonical_duplicate,
                "new_field": novelty == "new_field",
                "new_granularity": new_granularity,
                "new_join_key": new_join_key,
                "new_season_coverage": new_season_coverage,
                "new_entity_coverage": new_entity_coverage,
                "higher_quality_replacement": higher_quality_replacement,
                "novelty": novelty,
                "ingestible": ingestible,
                "blocker": None if ingestible else "redundant_with_existing_fields",
            }
        )
    return results


def build_source_field_diff_report(*, source_id: str, candidate_fields: list[dict[str, Any]], base_data_dir: str | Path | None = None, existing_index: dict[str, Any] | None = None) -> dict[str, Any]:
    classifications = compare_candidate_fields_to_existing_catalog(candidate_fields, base_data_dir=base_data_dir, existing_index=existing_index)
    ingestible = [row["field_name"] for row in classifications if row["ingestible"]]
    duplicates = [row["field_name"] for row in classifications if not row["ingestible"]]
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_OPEN_DATA_FIELD_CATALOG_SCHEMA_VERSION,
            "source_id": source_id,
            "candidate_field_count": len(candidate_fields),
            "ingestible_field_count": len(ingestible),
            "ingestible_fields": ingestible,
            "duplicate_field_count": len(duplicates),
            "duplicate_fields": duplicates,
            "field_classifications": classifications,
        }
    )


def build_mlb_open_data_source_field_catalog(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    return build_mlb_open_data_field_catalog(base_data_dir=base_data_dir)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Open Data Field Catalog",
        "",
        f"1. field_entries_created: {report.get('field_entries_created')}",
        f"2. verified_field_count: {report.get('verified_field_count')}; verified_source_count: {report.get('verified_source_count')}",
        f"3. unverified_field_count: {report.get('unverified_field_count')}",
        f"4. cutoff_sensitive_field_count: {report.get('cutoff_sensitive_field_count')}; leakage_sensitive_field_count: {report.get('leakage_sensitive_field_count')}",
        f"5. fields_by_feature_family: {json.dumps(report.get('fields_by_feature_family') or {}, sort_keys=True)}",
        f"6. feature_families_covered: {', '.join(report.get('feature_families_covered') or []) if report.get('feature_families_covered') else 'none'}",
        "7. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Fields",
    ]
    for entry in list(report.get("entries") or [])[:400]:
        lines.append(
            f"- {entry.get('source_id')}.{entry.get('field_name')}: status={entry.get('source_status')}; implementation={entry.get('implementation_status')}; family={entry.get('model_feature_family')}; leakage={entry.get('leakage_risk')}"
        )
    return "\n".join(lines) + "\n"


def write_mlb_open_data_field_catalog(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_open_data_field_catalog_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "latest_json_path": mlb_rel(latest_json, base_data_dir),
        "latest_markdown_path": mlb_rel(latest_md, base_data_dir),
        "item_json_path": mlb_rel(item_json, base_data_dir),
        "item_markdown_path": mlb_rel(item_md, base_data_dir),
    }
    payload = mlb_safe_payload({**report, **paths})
    mlb_atomic_write_json(latest_json, payload)
    mlb_atomic_write_text(latest_md, _render_markdown(payload))
    mlb_atomic_write_json(item_json, payload)
    mlb_atomic_write_text(item_md, _render_markdown(payload))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_mlb_open_data_field_catalog()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_mlb_open_data_field_catalog(report)
        report.update(paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
