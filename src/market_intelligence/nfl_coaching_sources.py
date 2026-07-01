"""Compliance-gated NFL coaching/staff source registry (disabled by default).

This registry describes coaching/staff data source families and their
compliance posture. The registry itself performs NO network calls, NO HTML
scraping, and NO user-agent spoofing. Every source is disabled by default.

Sources only become ingestion-eligible when one of the following holds:
- a structured open source (e.g., Wikidata CC0 / Wikipedia API) whose
  license/terms clearly permit automated structured access, or
- a verified open-licensed dataset, or
- a manual CSV import explicitly supplied by the user.

Public HTML pages (team staff pages, press releases, sitemaps) are blocked
unless their robots.txt and terms clearly allow automated collection. Sports
Reference / Pro Football Reference and FTN are blocked. If crawling were ever
permitted, only a truthful research user-agent, a crawl delay of at least 3
seconds, and a bounded page budget would be used, and only compact normalized
coaching facts (never raw HTML) would be stored.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from src.data.open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_COACHING_SOURCE_SCHEMA_VERSION = "nfl_coaching_sources_v2"
NFL_MODULE = "americanfootball_nfl"
COACHING_DATA_CATEGORY = "coaching_staff"

RESEARCH_USER_AGENT = "betting-stock-api-research-bot/0.1"
MIN_CRAWL_DELAY_SECONDS = 3
DEFAULT_MAX_PAGES_PER_DOMAIN = 25
DEFAULT_MAX_DOMAINS_PER_RUN = 32

COACHING_TARGET_FIELDS = [
    "team",
    "season",
    "head_coach",
    "offensive_coordinator",
    "defensive_coordinator",
    "special_teams_coordinator",
    "interim_head_coach",
    "coaching_start_date",
    "coaching_end_date",
    "staff_role",
    "staff_name",
    "role_group",
    "source_effective_date",
    "source_updated_date",
    "coaching_continuity_candidate",
    "coordinator_continuity_candidate",
    "staff_turnover_candidate",
]

COACHING_SOURCE_FAMILIES = [
    "official_team_staff_pages",
    "official_team_press_releases",
    "official_nfl_staff_or_news_pages",
    "team_sitemaps",
    "wikidata_coaching_seed",
    "wikidata_entity_api",
    "wikidata_local_dump",
    "wikipedia_coaching_seed",
    "wikipedia_coaching_tables",
    "open_github_coaching_dataset",
    "manual_csv_import",
    "blocked_pfr_reference",
    "blocked_ftn_charting",
]


def _coaching_source(
    *,
    source_id: str,
    source_name: str,
    source_family: str,
    source_access_type: str,
    source_kind: str,
    terms_review_status: str,
    robots_review_status: str = "not_applicable",
    license_status: str = "not_applicable",
    requires_auth: bool = False,
    requires_api_key: bool = False,
    requires_budget_approval: bool = False,
    paid_or_freemium: bool = False,
    automation_allowed: bool = False,
    structured_data_available: bool = False,
    structured_seed_supported: bool = False,
    attribution_required: bool = False,
    supplemental_only: bool = False,
    raw_html_required: bool = False,
    spoofing_required: bool = False,
    crawl_supported: bool = False,
    live_download_supported: bool = False,
    manual_import_supported: bool = False,
    sports_reference_derivative: bool = False,
    forced_blocker: str | None = None,
    crawl_delay_seconds: int = MIN_CRAWL_DELAY_SECONDS,
    max_pages_per_domain: int = DEFAULT_MAX_PAGES_PER_DOMAIN,
    expected_formats: list[str] | None = None,
    expected_granularity: str = "coach_team_season",
    expected_join_keys: list[str] | None = None,
    likely_supported_features: list[str] | None = None,
    blocked_features: list[str] | None = None,
    target_fields: list[str] | None = None,
    safety_notes: str = "",
) -> dict[str, Any]:
    source = {
        "source_id": source_id,
        "source_name": source_name,
        "source_family": source_family,
        "module": NFL_MODULE,
        "data_category": COACHING_DATA_CATEGORY,
        "source_access_type": source_access_type,
        "source_kind": source_kind,
        "enabled": False,
        "no_call_supported": True,
        "metadata_only_supported": True,
        "crawl_supported": bool(crawl_supported),
        "live_download_supported": bool(live_download_supported),
        "manual_import_supported": bool(manual_import_supported),
        "requires_api_key": bool(requires_api_key),
        "requires_auth": bool(requires_auth),
        "requires_budget_approval": bool(requires_budget_approval),
        "paid_or_freemium": bool(paid_or_freemium),
        "terms_review_status": terms_review_status,
        "robots_review_status": robots_review_status,
        "license_status": license_status,
        "automation_allowed": bool(automation_allowed),
        "structured_data_available": bool(structured_data_available),
        "structured_seed_supported": bool(structured_seed_supported),
        "attribution_required": bool(attribution_required),
        "supplemental_only": bool(supplemental_only),
        "raw_html_required": bool(raw_html_required),
        "raw_html_persisted": False,
        "spoofing_required": bool(spoofing_required),
        "browser_impersonation_used": False,
        "sports_reference_derivative": bool(sports_reference_derivative),
        "forced_blocker": forced_blocker,
        "user_agent": RESEARCH_USER_AGENT,
        "crawl_delay_seconds": max(int(crawl_delay_seconds), MIN_CRAWL_DELAY_SECONDS),
        "max_pages_per_domain": int(max_pages_per_domain),
        "persists_raw_html": False,
        "stores_compact_facts_only": True,
        "expected_formats": list(expected_formats or []),
        "expected_granularity": expected_granularity,
        "expected_join_keys": list(expected_join_keys or ["season", "team", "staff_name"]),
        "likely_supported_features": list(likely_supported_features or ["coaching_staff"]),
        "blocked_features": list(blocked_features or []),
        "target_fields": list(target_fields or COACHING_TARGET_FIELDS),
        "safety_notes": safety_notes,
    }
    source.update(classify_coaching_source(source))
    source["blockers"] = [source["blocker"]] if source.get("blocker") else []
    return source


def classify_coaching_source(source: dict[str, Any]) -> dict[str, Any]:
    """Compliance gate for a coaching source. Disabled-by-default; blocked unless clearly safe."""
    blocker: str | None = None
    approval = "blocked"
    if source.get("forced_blocker"):
        blocker = source["forced_blocker"]
    elif source.get("spoofing_required"):
        blocker = "spoofing_or_bypass_required"
    elif source.get("sports_reference_derivative"):
        blocker = "sports_reference_scraping_blocked"
    elif source.get("paid_or_freemium") or source.get("requires_budget_approval"):
        blocker = "paid_or_budget_required"
    elif source.get("requires_auth") or source.get("requires_api_key"):
        blocker = "auth_or_api_key_required"
    elif source.get("manual_import_supported") and source.get("source_kind") == "manual_csv":
        approval = "approved_manual_import"
    elif source.get("robots_review_status") == "disallows_automated_collection":
        blocker = "robots_disallows_automation"
    elif source.get("raw_html_required") and source.get("terms_review_status") != "reviewed_open_allowed":
        blocker = "html_scraping_terms_unclear"
    elif source.get("source_kind") == "open_data_file" and source.get("license_status") not in {"open_verified"}:
        blocker = "license_unverified"
    elif not source.get("automation_allowed"):
        blocker = "automation_not_confirmed"
    elif not source.get("structured_data_available"):
        blocker = "structured_data_not_available"
    else:
        approval = "approved_open_structured"

    if blocker is not None:
        return {
            "current_phase_allowed": False,
            "approval_status": "blocked",
            "blocker": blocker,
            "next_safe_action": f"keep source disabled; {blocker}",
        }
    return {
        "current_phase_allowed": True,
        "approval_status": approval,
        "blocker": None,
        "next_safe_action": (
            "supply a validated CSV with source_license then run manual_import with -AllowManualImport"
            if approval == "approved_manual_import"
            else "run no-call metadata_check then bounded structured seed with explicit enable"
        ),
    }


def nfl_coaching_sources() -> list[dict[str, Any]]:
    return [
        _coaching_source(
            source_id="official_team_staff_pages",
            source_name="Official team staff directory pages",
            source_family="official_team_staff_pages",
            source_access_type="public_web",
            source_kind="html_pages",
            terms_review_status="terms_unclear",
            robots_review_status="disallows_automated_collection",
            raw_html_required=True,
            crawl_supported=True,
            safety_notes="public team staff pages; robots/terms do not clearly allow automated collection",
        ),
        _coaching_source(
            source_id="official_team_press_releases",
            source_name="Official team press-release / news pages",
            source_family="official_team_press_releases",
            source_access_type="public_web",
            source_kind="html_pages",
            terms_review_status="terms_unclear",
            robots_review_status="review_required",
            raw_html_required=True,
            crawl_supported=True,
            likely_supported_features=["coaching_staff", "coaching_change_event"],
            safety_notes="press-release pages; terms unclear for automated collection",
        ),
        _coaching_source(
            source_id="official_nfl_staff_or_news_pages",
            source_name="Official NFL.com staff/news pages",
            source_family="official_nfl_staff_or_news_pages",
            source_access_type="public_web",
            source_kind="html_pages",
            terms_review_status="terms_unclear",
            robots_review_status="review_required",
            raw_html_required=True,
            crawl_supported=True,
            safety_notes="NFL.com pages; terms unclear for automated collection",
        ),
        _coaching_source(
            source_id="team_sitemaps",
            source_name="Official team XML sitemaps",
            source_family="team_sitemaps",
            source_access_type="public_web",
            source_kind="sitemap_xml",
            terms_review_status="terms_unclear",
            robots_review_status="review_required",
            raw_html_required=True,
            crawl_supported=True,
            structured_data_available=True,
            safety_notes="sitemaps only enumerate URLs; terms unclear and no coaching facts without page fetch",
        ),
        _coaching_source(
            source_id="wikidata_coaching_seed",
            source_name="Wikidata NFL coaching/staff seed (CC0)",
            source_family="wikidata_coaching_seed",
            source_access_type="structured_open_api",
            source_kind="structured_open_data",
            terms_review_status="reviewed_open_allowed",
            license_status="cc0",
            automation_allowed=True,
            structured_data_available=True,
            structured_seed_supported=True,
            live_download_supported=True,
            attribution_required=False,
            expected_formats=["json", "sparql_json"],
            likely_supported_features=["coaching_staff", "head_coach_by_team_season"],
            safety_notes="Wikidata is CC0; bounded no-auth structured query permitted; disabled by default until explicit AllowStructuredSeed",
        ),
        _coaching_source(
            source_id="wikidata_entity_api",
            source_name="Wikidata Entity/REST API direct fallback (CC0)",
            source_family="wikidata_entity_api",
            source_access_type="structured_open_api",
            source_kind="structured_open_data",
            terms_review_status="reviewed_open_allowed",
            license_status="cc0",
            automation_allowed=True,
            structured_data_available=True,
            structured_seed_supported=True,
            live_download_supported=True,
            attribution_required=False,
            expected_formats=["json"],
            likely_supported_features=["coaching_staff", "head_coach_by_team_season"],
            safety_notes="direct Wikidata entity API by QID (no SPARQL); bounded, no-auth, CC0; disabled by default",
        ),
        _coaching_source(
            source_id="wikidata_local_dump",
            source_name="Wikidata local JSON/RDF dump streaming fallback (CC0)",
            source_family="wikidata_local_dump",
            source_access_type="local_dump_file",
            source_kind="local_dump",
            terms_review_status="reviewed_open_allowed",
            license_status="cc0",
            automation_allowed=True,
            structured_data_available=True,
            structured_seed_supported=True,
            live_download_supported=False,
            attribution_required=False,
            expected_formats=["json", "ndjson", "nt", "bz2", "gz"],
            likely_supported_features=["coaching_staff"],
            safety_notes="streams a locally-supplied Wikidata dump; avoids WDQS entirely; requires AllowLocalDump and a dump path",
        ),
        _coaching_source(
            source_id="wikipedia_coaching_tables",
            source_name="Wikipedia structured-table supplemental fallback (CC BY-SA, API)",
            source_family="wikipedia_coaching_tables",
            source_access_type="structured_open_api",
            source_kind="structured_open_data",
            terms_review_status="reviewed_open_allowed",
            license_status="cc_by_sa",
            automation_allowed=True,
            structured_data_available=True,
            structured_seed_supported=True,
            live_download_supported=True,
            attribution_required=True,
            expected_formats=["json"],
            likely_supported_features=["coaching_staff"],
            safety_notes="Wikipedia API structured tables only (no prose parsing); CC BY-SA attribution required; disabled by default",
        ),
        _coaching_source(
            source_id="wikipedia_coaching_seed",
            source_name="Wikipedia NFL coaching seed (CC BY-SA, API, supplemental)",
            source_family="wikipedia_coaching_seed",
            source_access_type="structured_open_api",
            source_kind="structured_api",
            terms_review_status="reviewed_open_allowed",
            license_status="cc_by_sa",
            automation_allowed=True,
            structured_data_available=True,
            structured_seed_supported=False,
            live_download_supported=True,
            attribution_required=True,
            supplemental_only=True,
            expected_formats=["json"],
            likely_supported_features=["coaching_staff_provenance"],
            safety_notes="Wikipedia is CC BY-SA; attribution required; used ONLY for supplemental page-title/provenance metadata, never prose parsing",
        ),
        _coaching_source(
            source_id="open_github_coaching_dataset",
            source_name="Open GitHub NFL coaching/staff dataset",
            source_family="open_github_coaching_dataset",
            source_access_type="open_github_file",
            source_kind="open_data_file",
            terms_review_status="research_required",
            license_status="license_unverified",
            automation_allowed=True,
            structured_data_available=True,
            live_download_supported=True,
            expected_formats=["csv", "json"],
            safety_notes="structured candidate; license/provenance must be verified open before ingestion",
        ),
        _coaching_source(
            source_id="manual_csv_import",
            source_name="Manual coaching CSV import (user-supplied)",
            source_family="manual_csv_import",
            source_access_type="manual_local_file",
            source_kind="manual_csv",
            terms_review_status="user_supplied",
            license_status="user_declared",
            manual_import_supported=True,
            structured_data_available=True,
            expected_formats=["csv"],
            expected_granularity="coach_team_season",
            likely_supported_features=["coaching_staff", "coaching_continuity_candidate"],
            safety_notes="user-supplied CSV with declared source/license; requires explicit AllowManualImport",
        ),
        _coaching_source(
            source_id="blocked_pfr_reference",
            source_name="Pro Football Reference coaching pages (blocked)",
            source_family="blocked_pfr_reference",
            source_access_type="public_web",
            source_kind="html_pages",
            terms_review_status="terms_disallow_scraping",
            robots_review_status="disallows_automated_collection",
            sports_reference_derivative=True,
            raw_html_required=True,
            forced_blocker="sports_reference_scraping_blocked",
            blocked_features=["coaching_staff"],
            safety_notes="Sports Reference family; scraping not permitted",
        ),
        _coaching_source(
            source_id="blocked_ftn_charting",
            source_name="FTN charting coaching/staff (blocked)",
            source_family="blocked_ftn_charting",
            source_access_type="third_party_release",
            source_kind="charting_release",
            terms_review_status="research_required",
            forced_blocker="ftn_terms_not_proven_open",
            blocked_features=["coaching_staff"],
            safety_notes="not proven free/open/terms-safe; remains blocked",
        ),
    ]


def coaching_source_by_id(source_id: str) -> dict[str, Any] | None:
    for source in nfl_coaching_sources():
        if source["source_id"] == source_id:
            return source
    return None


def build_nfl_coaching_source_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    sources = nfl_coaching_sources()
    approved = [s["source_id"] for s in sources if s["approval_status"] in {"approved_open_structured", "approved_manual_import"}]
    blocked = [{"source_id": s["source_id"], "blocker": s["blocker"]} for s in sources if s["approval_status"] == "blocked"]
    blocker_counts = Counter(str(s["blocker"]) for s in sources if s["blocker"])
    # Availability requires actual validated coaching rows; structured/manual approval
    # only means a source MAY be ingested with explicit enable, not that data is present.
    coaching_available = False
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_COACHING_SOURCE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_coaching_sources_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "research_user_agent": RESEARCH_USER_AGENT,
        "min_crawl_delay_seconds": MIN_CRAWL_DELAY_SECONDS,
        "max_pages_per_domain_default": DEFAULT_MAX_PAGES_PER_DOMAIN,
        "max_domains_per_run_default": DEFAULT_MAX_DOMAINS_PER_RUN,
        "coaching_target_fields": COACHING_TARGET_FIELDS,
        "coaching_source_families": COACHING_SOURCE_FAMILIES,
        "coaching_sources_audited": len(sources),
        "nfl_coaching_data_available": coaching_available,
        "nfl_coaching_data_blocked_reason": "no_coaching_rows_ingested_yet_sources_disabled_by_default",
        "approved_coaching_sources": approved,
        "blocked_coaching_sources": blocked,
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "sources": sources,
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
    root = base / "nfl_open_data" / "coaching_sources"
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


def render_nfl_coaching_source_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Coaching/Staff Source Audit",
        "",
        f"1. coaching_sources_audited: {report.get('coaching_sources_audited')}",
        f"2. nfl_coaching_data_available: {str(report.get('nfl_coaching_data_available')).lower()}",
        f"3. nfl_coaching_data_blocked_reason: {report.get('nfl_coaching_data_blocked_reason')}",
        f"4. research_user_agent: {report.get('research_user_agent')}",
        f"5. min_crawl_delay_seconds: {report.get('min_crawl_delay_seconds')}",
        f"6. approved_coaching_sources: {', '.join(report.get('approved_coaching_sources') or []) if report.get('approved_coaching_sources') else 'none'}",
        f"7. blocker_counts: {json.dumps(report.get('blocker_counts') or {}, sort_keys=True)}",
        "8. spoofing_used=false; browser_impersonation_used=false; raw_html_persisted=false",
        "9. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Sources",
    ]
    for source in report.get("sources") or []:
        lines.append(
            f"- {source.get('source_id')} [{source.get('source_family')}]: approval={source.get('approval_status')}; "
            f"blocker={source.get('blocker')}; enabled={str(source.get('enabled')).lower()}; "
            f"crawl_delay={source.get('crawl_delay_seconds')}s"
        )
    return "\n".join(lines) + "\n"


def write_nfl_coaching_source_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_coaching_sources_{uuid4().hex[:8]}"))
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
    markdown = render_nfl_coaching_source_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_coaching_source_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_coaching_source_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "nfl_coaching_data_available": report.get("nfl_coaching_data_available"),
                "nfl_coaching_data_blocked_reason": report.get("nfl_coaching_data_blocked_reason"),
                "coaching_sources_audited": report.get("coaching_sources_audited"),
                "approved_coaching_sources": report.get("approved_coaching_sources"),
                "blocker_counts": report.get("blocker_counts"),
                "spoofing_used": False,
                "raw_html_persisted": False,
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
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
