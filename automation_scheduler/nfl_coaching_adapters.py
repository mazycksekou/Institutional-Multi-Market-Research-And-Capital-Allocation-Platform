"""NFL coaching/staff adapter (compliance gate only; no scraping, no network).

This adapter intentionally performs NO network calls, NO HTML scraping, and NO
user-agent spoofing. It is a compliance gate that decides whether a coaching
source is ingestion-eligible and, if so, how a compact, raw-HTML-free import
would be structured. Because no confirmed open/terms-safe coaching source
exists yet, every adapter run returns a blocked report with a precise reason
rather than fetching anything.

If a source is ever verified open/terms-safe and a structured open file becomes
available, ingestion would reuse the existing open-data import path and persist
only compact normalized coaching facts (never raw HTML, never raw payloads).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_coaching_sources import (
    COACHING_TARGET_FIELDS,
    MIN_CRAWL_DELAY_SECONDS,
    RESEARCH_USER_AGENT,
    coaching_source_by_id,
    nfl_coaching_sources,
)
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


NFL_COACHING_ADAPTER_SCHEMA_VERSION = "nfl_coaching_adapter_v1"
NFL_MODULE = "americanfootball_nfl"


class NflCoachingAdapter:
    """Compliance-gated coaching adapter. Never scrapes, spoofs, or persists raw HTML."""

    def __init__(self, source: dict[str, Any]):
        self.source = source

    @property
    def user_agent(self) -> str:
        return RESEARCH_USER_AGENT

    @property
    def crawl_delay_seconds(self) -> int:
        return max(int(self.source.get("crawl_delay_seconds", MIN_CRAWL_DELAY_SECONDS)), MIN_CRAWL_DELAY_SECONDS)

    @property
    def persists_raw_html(self) -> bool:
        return False

    @property
    def spoofs_user_agent(self) -> bool:
        return False

    def compliance_gate(self) -> dict[str, Any]:
        return {
            "enabled": False,
            "current_phase_allowed": bool(self.source.get("current_phase_allowed")),
            "approval_status": self.source.get("approval_status"),
            "blocker": self.source.get("blocker"),
            "robots_review_status": self.source.get("robots_review_status"),
            "terms_review_status": self.source.get("terms_review_status"),
            "license_status": self.source.get("license_status"),
            "user_agent": self.user_agent,
            "crawl_delay_seconds": self.crawl_delay_seconds,
            "max_pages_per_domain": int(self.source.get("max_pages_per_domain", 25)),
            "spoofs_user_agent": False,
            "persists_raw_html": False,
            "stores_compact_facts_only": True,
        }

    def run_ingestion(self, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        gate = self.compliance_gate()
        # Disabled-by-default and gate-blocked: no fetch occurs, ever, in this phase.
        blocked_reason = gate.get("blocker") or "coaching_lane_disabled_by_default"
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "blocked",
            "schema_version": NFL_COACHING_ADAPTER_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"nfl_coaching_adapter_{self.source['source_id']}_{uuid4().hex[:8]}"),
            "module": NFL_MODULE,
            "runtime_data_dir": str(base),
            "source_id": self.source.get("source_id"),
            "source_family": self.source.get("source_family"),
            "target_fields": list(COACHING_TARGET_FIELDS),
            "compliance_gate": gate,
            "blocked_reason": blocked_reason,
            "coaching_fields_ingested": [],
            "records_validated": 0,
            "records_rejected": 0,
            "fetch_attempted": False,
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


def adapter_by_id(source_id: str) -> NflCoachingAdapter | None:
    source = coaching_source_by_id(source_id)
    return NflCoachingAdapter(source) if source else None


def build_nfl_coaching_ingestion_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    runs = [NflCoachingAdapter(source).run_ingestion(base_data_dir=base) for source in nfl_coaching_sources()]
    ingested = [row for row in runs if row.get("coaching_fields_ingested")]
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_COACHING_ADAPTER_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_coaching_ingestion_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "coaching_runs": runs,
        "coaching_fields_ingested": sorted({field for row in ingested for field in row.get("coaching_fields_ingested") or []}),
        "nfl_coaching_data_available": bool(ingested),
        "nfl_coaching_data_blocked_reason": None if ingested else "no_confirmed_open_terms_safe_coaching_source",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", default=None)
    args = parser.parse_args(argv)
    if args.source_id:
        adapter = adapter_by_id(args.source_id)
        report = adapter.run_ingestion() if adapter else {"ok": False, "status": "unknown_source", "source_id": args.source_id}
    else:
        report = build_nfl_coaching_ingestion_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
