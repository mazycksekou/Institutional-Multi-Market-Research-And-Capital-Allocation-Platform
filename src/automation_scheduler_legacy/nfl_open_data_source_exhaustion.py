"""NFL free/open source exhaustion audit (no-call, metadata-only).

Audits remaining candidate NFL data source families for new, legal, free/open
fields not already covered by the project. This is a classification-only
registry: it performs NO provider calls, NO downloads, NO HTML scraping, and NO
user-agent spoofing. Sources are disabled by default and only advanced to
ingestion gates when they are structured, free/open, terms-safe, automation
allowed, and add non-redundant fields.

Compliance rules encoded here:
- Spoofing/bot-bypass required -> blocked.
- Raw-HTML scraping required with unclear terms/robots -> blocked.
- Paid/freemium -> blocked (budget approval required).
- Auth/API-key required -> blocked.
- Sports Reference / Pro Football Reference scraping -> blocked.
- FTN charting -> blocked unless proven free/open/terms-safe.
- Duplicate of existing fields -> redundant, not ingested.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_SOURCE_EXHAUSTION_SCHEMA_VERSION = "nfl_open_data_source_exhaustion_v1"
NFL_MODULE = "americanfootball_nfl"

CANDIDATE_SOURCE_FAMILIES = [
    "nflverse",
    "sportsdataverse",
    "official_nfl_endpoint",
    "official_team_endpoint",
    "official_public_web",
    "open_github_dataset",
    "public_open_data",
    "open_market_archive",
    "coaching_staff",
]


def _candidate(
    *,
    source_id: str,
    source_name: str,
    source_family: str,
    source_access_type: str,
    source_kind: str,
    candidate_data_categories: list[str],
    terms_review_status: str,
    robots_review_status: str = "not_applicable",
    license_status: str = "not_applicable",
    requires_auth: bool = False,
    requires_api_key: bool = False,
    requires_budget_approval: bool = False,
    paid_or_freemium: bool = False,
    automation_allowed: bool = True,
    structured_data_available: bool = True,
    raw_html_required: bool = False,
    spoofing_required: bool = False,
    sports_reference_derivative: bool = False,
    overlap_with_existing_fields: bool = False,
    new_fields_candidate: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    candidate = {
        "source_id": source_id,
        "source_name": source_name,
        "source_family": source_family,
        "module": NFL_MODULE,
        "source_access_type": source_access_type,
        "source_kind": source_kind,
        "candidate_data_categories": list(candidate_data_categories),
        "terms_review_status": terms_review_status,
        "robots_review_status": robots_review_status,
        "license_status": license_status,
        "requires_auth": bool(requires_auth),
        "requires_api_key": bool(requires_api_key),
        "requires_budget_approval": bool(requires_budget_approval),
        "paid_or_freemium": bool(paid_or_freemium),
        "automation_allowed": bool(automation_allowed),
        "structured_data_available": bool(structured_data_available),
        "raw_html_required": bool(raw_html_required),
        "spoofing_required": bool(spoofing_required),
        "sports_reference_derivative": bool(sports_reference_derivative),
        "overlap_with_existing_fields": bool(overlap_with_existing_fields),
        "new_fields_candidate": list(new_fields_candidate or []),
        "notes": notes,
        "enabled": False,
        "metadata_only_supported": True,
    }
    candidate.update(classify_candidate_source(candidate))
    return candidate


def classify_candidate_source(candidate: dict[str, Any]) -> dict[str, Any]:
    """Derive blocker / approval / gate eligibility from compliance attributes."""
    blocker: str | None = None
    if candidate.get("spoofing_required"):
        blocker = "spoofing_or_bypass_required"
    elif candidate.get("sports_reference_derivative"):
        blocker = "sports_reference_scraping_blocked"
    elif candidate.get("paid_or_freemium") or candidate.get("requires_budget_approval"):
        blocker = "paid_or_budget_required"
    elif candidate.get("requires_auth") or candidate.get("requires_api_key"):
        blocker = "auth_or_api_key_required"
    elif candidate.get("raw_html_required") and candidate.get("terms_review_status") not in {"reviewed_open_allowed"}:
        blocker = "html_scraping_terms_unclear"
    elif not candidate.get("automation_allowed"):
        blocker = "automation_not_allowed_by_terms"
    elif candidate.get("terms_review_status") in {"terms_unclear", "research_required"}:
        blocker = "terms_unclear_research_required"
    elif not candidate.get("structured_data_available"):
        blocker = "structured_data_not_available"

    redundant = bool(candidate.get("overlap_with_existing_fields")) and not candidate.get("new_fields_candidate")

    if blocker is not None:
        approval_status = "blocked"
        current_phase_allowed = False
        next_safe_action = f"keep disabled; {blocker}"
        tiny_sample_supported = False
        full_backfill_supported = False
    elif redundant:
        approval_status = "redundant_skip"
        current_phase_allowed = False
        next_safe_action = "skip ingestion; fields already covered by existing lanes"
        tiny_sample_supported = False
        full_backfill_supported = False
    else:
        approval_status = "approved_open_metadata"
        current_phase_allowed = True
        next_safe_action = "run no-call metadata_check then tiny_sample with explicit AllowDownload"
        tiny_sample_supported = True
        full_backfill_supported = True
    return {
        "blocker": blocker,
        "redundant": redundant,
        "approval_status": approval_status,
        "current_phase_allowed": current_phase_allowed,
        "tiny_sample_supported": tiny_sample_supported,
        "full_backfill_supported": full_backfill_supported,
        "next_safe_action": next_safe_action,
    }


def nfl_candidate_sources() -> list[dict[str, Any]]:
    return [
        _candidate(
            source_id="nflverse_nflfastr_pbp_release",
            source_name="nflverse/nflfastR play-by-play release",
            source_family="nflverse",
            source_access_type="open_github_release",
            source_kind="open_data_release",
            candidate_data_categories=["play_by_play", "pace_or_play_volume"],
            terms_review_status="reviewed_open_allowed",
            license_status="open_cc_by_like",
            overlap_with_existing_fields=True,
            notes="already ingested via nflverse_play_by_play / nflverse_pace_or_play_volume",
        ),
        _candidate(
            source_id="sportsdataverse_nfl_open",
            source_name="SportsDataverse NFL open datasets",
            source_family="sportsdataverse",
            source_access_type="open_package",
            source_kind="open_data_package",
            candidate_data_categories=["play_by_play", "team_stats", "player_stats"],
            terms_review_status="reviewed_open_allowed",
            license_status="open_mit_like",
            overlap_with_existing_fields=True,
            notes="wraps the same nflverse/ESPN open data already covered; redundant",
        ),
        _candidate(
            source_id="nfl_nextgen_official_endpoint",
            source_name="NFL Next Gen Stats public endpoint",
            source_family="official_nfl_endpoint",
            source_access_type="undocumented_endpoint",
            source_kind="unofficial_json_endpoint",
            candidate_data_categories=["advanced_efficiency"],
            terms_review_status="terms_unclear",
            automation_allowed=False,
            overlap_with_existing_fields=True,
            notes="NGS public site is not a documented open API; automation terms unclear",
        ),
        _candidate(
            source_id="espn_nfl_hidden_api",
            source_name="ESPN NFL undocumented JSON endpoints",
            source_family="official_nfl_endpoint",
            source_access_type="undocumented_endpoint",
            source_kind="unofficial_json_endpoint",
            candidate_data_categories=["schedules_results", "team_stats", "depth_charts"],
            terms_review_status="terms_unclear",
            automation_allowed=False,
            overlap_with_existing_fields=True,
            notes="undocumented; terms of use do not clearly permit automated collection",
        ),
        _candidate(
            source_id="pro_football_reference_web",
            source_name="Pro Football Reference (Sports Reference)",
            source_family="official_public_web",
            source_access_type="public_web",
            source_kind="html_pages",
            candidate_data_categories=["coaching", "advanced_efficiency"],
            terms_review_status="terms_disallow_scraping",
            robots_review_status="disallows_automated_collection",
            sports_reference_derivative=True,
            raw_html_required=True,
            structured_data_available=False,
            overlap_with_existing_fields=False,
            new_fields_candidate=["coach_name", "coordinator_name"],
            notes="Sports Reference family; scraping not permitted",
        ),
        _candidate(
            source_id="ftn_charting_open_candidate",
            source_name="FTN charting data",
            source_family="open_market_archive",
            source_access_type="third_party_release",
            source_kind="charting_release",
            candidate_data_categories=["advanced_efficiency"],
            terms_review_status="research_required",
            structured_data_available=True,
            overlap_with_existing_fields=False,
            new_fields_candidate=["charting_metric"],
            notes="not proven free/open/terms-safe; remains blocked",
        ),
        _candidate(
            source_id="the_odds_api_market",
            source_name="The Odds API market archive",
            source_family="open_market_archive",
            source_access_type="rest_api",
            source_kind="rest_api",
            candidate_data_categories=["betting_lines_or_market_odds"],
            terms_review_status="reviewed_open_allowed",
            requires_api_key=True,
            paid_or_freemium=True,
            requires_budget_approval=True,
            overlap_with_existing_fields=True,
            notes="freemium/paid with API key; out of scope for no-spend",
        ),
        _candidate(
            source_id="open_meteo_stadium_weather",
            source_name="Open-Meteo historical weather (stadium coordinates)",
            source_family="public_open_data",
            source_access_type="rest_api",
            source_kind="rest_api",
            candidate_data_categories=["weather", "stadiums"],
            terms_review_status="reviewed_open_allowed",
            license_status="open_cc_by_like",
            overlap_with_existing_fields=True,
            notes="game temp/wind/roof already covered by nflverse schedules; redundant for now",
        ),
        _candidate(
            source_id="open_github_nfl_coaches_dataset",
            source_name="Open GitHub NFL coaching/staff dataset (license-gated)",
            source_family="open_github_dataset",
            source_access_type="open_github_file",
            source_kind="open_data_file",
            candidate_data_categories=["coaching"],
            terms_review_status="research_required",
            license_status="license_unverified",
            structured_data_available=True,
            overlap_with_existing_fields=False,
            new_fields_candidate=["head_coach", "offensive_coordinator", "defensive_coordinator"],
            notes="candidate coaching dataset; license/provenance must be verified before ingestion",
        ),
    ]


def build_nfl_source_exhaustion_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    candidates = nfl_candidate_sources()
    families_audited = sorted({str(candidate["source_family"]) for candidate in candidates})
    new_safe = [c["source_id"] for c in candidates if c["approval_status"] == "approved_open_metadata"]
    redundant = [c["source_id"] for c in candidates if c["approval_status"] == "redundant_skip"]
    blocked = [
        {"source_id": c["source_id"], "blocker": c["blocker"]}
        for c in candidates
        if c["approval_status"] == "blocked"
    ]
    blocker_counts = Counter(str(c["blocker"]) for c in candidates if c["blocker"])
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_SOURCE_EXHAUSTION_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_source_exhaustion_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "nfl_source_exhaustion_checked": True,
        "candidate_source_families_audited": CANDIDATE_SOURCE_FAMILIES,
        "candidate_source_families_present": families_audited,
        "candidate_sources_found": len(candidates),
        "nfl_new_safe_sources_found": new_safe,
        "nfl_new_safe_source_count": len(new_safe),
        "nfl_redundant_sources_skipped": redundant,
        "nfl_redundant_source_count": len(redundant),
        "nfl_blocked_sources": blocked,
        "nfl_blocked_source_count": len(blocked),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "candidates": candidates,
        "spoofing_used": False,
        "browser_impersonation_used": False,
        "raw_html_persisted": False,
        "no_predictive_claim": True,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "source_exhaustion"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def render_nfl_source_exhaustion_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Open Data Source Exhaustion Audit",
        "",
        f"1. candidate_sources_found: {report.get('candidate_sources_found')}",
        f"2. new_safe_sources_found: {', '.join(report.get('nfl_new_safe_sources_found') or []) if report.get('nfl_new_safe_sources_found') else 'none'}",
        f"3. redundant_sources_skipped: {', '.join(report.get('nfl_redundant_sources_skipped') or []) if report.get('nfl_redundant_sources_skipped') else 'none'}",
        f"4. blocked_sources: {report.get('nfl_blocked_source_count')}",
        f"5. blocker_counts: {json.dumps(report.get('blocker_counts') or {}, sort_keys=True)}",
        "6. spoofing_used=false; browser_impersonation_used=false; raw_html_persisted=false",
        "7. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Candidates",
    ]
    for candidate in report.get("candidates") or []:
        lines.append(
            f"- {candidate.get('source_id')} [{candidate.get('source_family')}]: approval={candidate.get('approval_status')}; "
            f"blocker={candidate.get('blocker')}; overlap={str(candidate.get('overlap_with_existing_fields')).lower()}; "
            f"next={candidate.get('next_safe_action')}"
        )
    return "\n".join(lines) + "\n"


def write_nfl_source_exhaustion_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_source_exhaustion_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_nfl_source_exhaustion_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_source_exhaustion_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_source_exhaustion_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "candidate_sources_found": report.get("candidate_sources_found"),
                "nfl_new_safe_sources_found": report.get("nfl_new_safe_sources_found"),
                "nfl_redundant_sources_skipped": report.get("nfl_redundant_sources_skipped"),
                "nfl_blocked_source_count": report.get("nfl_blocked_source_count"),
                "spoofing_used": False,
                "raw_html_persisted": False,
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "latest_json_path": paths.get("latest_json_path"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
