"""Compliance-gated NFL coaching/staff source registry (disabled by default).

This registry describes candidate coaching/staff data sources and their
compliance posture. It performs NO network calls, NO HTML scraping, and NO
user-agent spoofing. Every source is disabled by default and only becomes
ingestion-eligible when it is a structured, free/open, terms-safe source whose
license/robots/terms clearly permit automated collection. If crawling a public
page were ever permitted, only a truthful research user-agent, a crawl delay of
at least 3 seconds, and a bounded page budget would be used, and only compact
normalized coaching facts (never raw HTML) would be stored.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


NFL_COACHING_SOURCE_SCHEMA_VERSION = "nfl_coaching_sources_v1"
NFL_MODULE = "americanfootball_nfl"

RESEARCH_USER_AGENT = "betting-stock-api-research-bot/0.1"
MIN_CRAWL_DELAY_SECONDS = 3
DEFAULT_MAX_PAGES_PER_DOMAIN = 25

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
    automation_allowed: bool = False,
    structured_data_available: bool = False,
    raw_html_required: bool = False,
    spoofing_required: bool = False,
    crawl_delay_seconds: int = MIN_CRAWL_DELAY_SECONDS,
    max_pages_per_domain: int = DEFAULT_MAX_PAGES_PER_DOMAIN,
    target_fields: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    source = {
        "source_id": source_id,
        "source_name": source_name,
        "source_family": source_family,
        "module": NFL_MODULE,
        "source_access_type": source_access_type,
        "source_kind": source_kind,
        "terms_review_status": terms_review_status,
        "robots_review_status": robots_review_status,
        "license_status": license_status,
        "requires_auth": bool(requires_auth),
        "automation_allowed": bool(automation_allowed),
        "structured_data_available": bool(structured_data_available),
        "raw_html_required": bool(raw_html_required),
        "spoofing_required": bool(spoofing_required),
        "user_agent": RESEARCH_USER_AGENT,
        "crawl_delay_seconds": max(int(crawl_delay_seconds), MIN_CRAWL_DELAY_SECONDS),
        "max_pages_per_domain": int(max_pages_per_domain),
        "persists_raw_html": False,
        "stores_compact_facts_only": True,
        "enabled": False,
        "target_fields": list(target_fields or COACHING_TARGET_FIELDS),
        "notes": notes,
    }
    source.update(classify_coaching_source(source))
    return source


def classify_coaching_source(source: dict[str, Any]) -> dict[str, Any]:
    """Compliance gate for a coaching source. Disabled-by-default; blocked unless clearly safe."""
    blocker: str | None = None
    if source.get("spoofing_required"):
        blocker = "spoofing_or_bypass_required"
    elif source.get("requires_auth"):
        blocker = "auth_required"
    elif source.get("robots_review_status") in {"disallows_automated_collection"}:
        blocker = "robots_disallows_automation"
    elif source.get("raw_html_required") and source.get("terms_review_status") != "reviewed_open_allowed":
        blocker = "html_scraping_terms_unclear"
    elif not source.get("automation_allowed"):
        blocker = "automation_not_confirmed"
    elif source.get("source_kind") == "open_data_file" and source.get("license_status") not in {"open_verified"}:
        blocker = "license_unverified"
    elif not source.get("structured_data_available"):
        blocker = "structured_data_not_available"

    if blocker is not None:
        return {
            "current_phase_allowed": False,
            "approval_status": "blocked",
            "blocker": blocker,
            "next_safe_action": f"keep coaching lane disabled; {blocker}",
        }
    return {
        "current_phase_allowed": True,
        "approval_status": "approved_open_structured",
        "blocker": None,
        "next_safe_action": "run no-call metadata_check then bounded compliant import with explicit enable",
    }


def nfl_coaching_sources() -> list[dict[str, Any]]:
    return [
        _coaching_source(
            source_id="open_github_coaching_dataset",
            source_name="Open GitHub NFL coaching/staff dataset",
            source_family="open_github_dataset",
            source_access_type="open_github_file",
            source_kind="open_data_file",
            terms_review_status="research_required",
            license_status="license_unverified",
            automation_allowed=True,
            structured_data_available=True,
            notes="structured candidate; license/provenance must be verified open before ingestion",
        ),
        _coaching_source(
            source_id="official_team_staff_pages",
            source_name="Official team staff directory pages",
            source_family="official_public_web",
            source_access_type="public_web",
            source_kind="html_pages",
            terms_review_status="terms_unclear",
            robots_review_status="disallows_automated_collection",
            raw_html_required=True,
            structured_data_available=False,
            notes="public team pages; robots/terms do not clearly allow automated collection",
        ),
        _coaching_source(
            source_id="nflverse_coaching_release_candidate",
            source_name="nflverse coaching release candidate",
            source_family="nflverse",
            source_access_type="open_github_release",
            source_kind="open_data_release",
            terms_review_status="research_required",
            license_status="open_verified",
            automation_allowed=False,
            structured_data_available=True,
            notes="no confirmed nflverse coaching release; remains blocked until a release is verified",
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
    approved = [s["source_id"] for s in sources if s["approval_status"] == "approved_open_structured"]
    blocked = [{"source_id": s["source_id"], "blocker": s["blocker"]} for s in sources if s["approval_status"] == "blocked"]
    blocker_counts = Counter(str(s["blocker"]) for s in sources if s["blocker"])
    coaching_available = len(approved) > 0
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
        "coaching_target_fields": COACHING_TARGET_FIELDS,
        "coaching_sources_audited": len(sources),
        "nfl_coaching_data_available": coaching_available,
        "nfl_coaching_data_blocked_reason": None if coaching_available else "no_confirmed_open_terms_safe_coaching_source",
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
        f"6. blocker_counts: {json.dumps(report.get('blocker_counts') or {}, sort_keys=True)}",
        "7. spoofing_used=false; browser_impersonation_used=false; raw_html_persisted=false",
        "8. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
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
