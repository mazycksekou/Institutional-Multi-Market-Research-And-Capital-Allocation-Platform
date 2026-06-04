"""Compliance-gated NFL coaching/staff adapters.

These adapters NEVER spoof a browser user-agent, NEVER use browser automation,
NEVER bypass robots/terms, and NEVER persist raw HTML or raw provider payloads.
HTML page sources are blocked unless robots.txt and terms clearly allow
automated collection; because none currently do, no page fetch occurs. The only
record-producing path in this phase is the manual CSV importer (explicit
AllowManualImport) and, when explicitly enabled in a future run, the structured
open seed adapters (Wikidata CC0 / Wikipedia API). Coaching facts are normalized
into compact rows; raw page bodies are never stored.
"""

from __future__ import annotations

import argparse
import csv
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


NFL_COACHING_ADAPTER_SCHEMA_VERSION = "nfl_coaching_adapter_v2"
NFL_MODULE = "americanfootball_nfl"

CANONICAL_ROLE_GROUPS = [
    "head_coach",
    "offensive_coordinator",
    "defensive_coordinator",
    "special_teams_coordinator",
    "position_coach",
    "assistant",
    "analyst",
    "executive",
    "unknown",
]

REQUIRED_RECORD_FIELDS = ["team", "season", "staff_name", "staff_role"]
EXECUTIVE_TOKENS = ("general manager", "president", "owner", "executive", "director of", "vice president", "gm")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def classify_coaching_role(staff_role: str) -> dict[str, Any]:
    """Map a free-text staff role to a canonical role group. Ambiguous -> unknown."""
    lower = _clean(staff_role).lower()
    interim = "interim" in lower
    role_group = "unknown"
    if not lower:
        role_group = "unknown"
    elif "head coach" in lower and "assistant head coach" not in lower:
        role_group = "head_coach"
    elif "offensive coordinator" in lower:
        role_group = "offensive_coordinator"
    elif "defensive coordinator" in lower:
        role_group = "defensive_coordinator"
    elif "special teams coordinator" in lower or ("special teams" in lower and "coordinator" in lower):
        role_group = "special_teams_coordinator"
    elif "coordinator" in lower:
        role_group = "unknown"  # ambiguous coordinator (e.g., pass-game coordinator)
    elif "analyst" in lower:
        role_group = "analyst"
    elif any(token in lower for token in EXECUTIVE_TOKENS):
        role_group = "executive"
    elif "assistant head coach" in lower:
        role_group = "assistant"
    elif "coach" in lower:
        role_group = "position_coach"
    elif "assistant" in lower:
        role_group = "assistant"
    return {
        "canonical_role": role_group,
        "role_group": role_group,
        "head_coach_flag": role_group == "head_coach",
        "offensive_coordinator_flag": role_group == "offensive_coordinator",
        "defensive_coordinator_flag": role_group == "defensive_coordinator",
        "special_teams_coordinator_flag": role_group == "special_teams_coordinator",
        "interim_flag": interim,
        "assistant_flag": role_group in {"assistant", "position_coach"},
    }


def validate_record_shape(record: dict[str, Any], *, require_license: bool = False) -> tuple[bool, str | None]:
    for field in REQUIRED_RECORD_FIELDS:
        if not _clean(record.get(field)):
            return False, f"missing_required_field:{field}"
    season = _clean(record.get("season"))
    if not season.isdigit() or not (1920 <= int(season) <= 2100):
        return False, "invalid_season"
    if require_license and not _clean(record.get("source_license")):
        return False, "missing_source_license"
    return True, None


class NflCoachingAdapter:
    """Base compliance-gated coaching adapter. No spoofing, no raw HTML, no bypass."""

    def __init__(self, source: dict[str, Any]):
        self.source = source

    # --- description / compliance ---
    def describe_source(self) -> dict[str, Any]:
        return {
            "source_id": self.source.get("source_id"),
            "source_family": self.source.get("source_family"),
            "source_kind": self.source.get("source_kind"),
            "approval_status": self.source.get("approval_status"),
            "blocker": self.source.get("blocker"),
            "user_agent": RESEARCH_USER_AGENT,
            "crawl_delay_seconds": self.crawl_delay_seconds,
            "max_pages_per_domain": int(self.source.get("max_pages_per_domain", 25)),
            "spoofs_user_agent": False,
            "browser_impersonation_used": False,
            "persists_raw_html": False,
        }

    @property
    def user_agent(self) -> str:
        return RESEARCH_USER_AGENT

    @property
    def crawl_delay_seconds(self) -> int:
        return max(int(self.source.get("crawl_delay_seconds", MIN_CRAWL_DELAY_SECONDS)), MIN_CRAWL_DELAY_SECONDS)

    @property
    def spoofs_user_agent(self) -> bool:
        return False

    @property
    def browser_impersonation_used(self) -> bool:
        return False

    @property
    def persists_raw_html(self) -> bool:
        return False

    def check_robots_txt(self) -> dict[str, Any]:
        # Static recorded status only; no network fetch in this phase.
        status = self.source.get("robots_review_status")
        allowed = status == "allows_automated_collection"
        return {"robots_review_status": status, "robots_allows_automation": allowed, "fetched": False}

    def check_terms_status(self) -> dict[str, Any]:
        status = self.source.get("terms_review_status")
        allowed = status in {"reviewed_open_allowed", "user_supplied"}
        return {"terms_review_status": status, "terms_allows_automation": allowed}

    def validate_source_allowed(self, *, allow_crawl: bool = False, allow_manual_import: bool = False) -> dict[str, Any]:
        robots = self.check_robots_txt()
        terms = self.check_terms_status()
        kind = self.source.get("source_kind")
        if self.source.get("approval_status") == "blocked":
            return {"allowed": False, "reason": self.source.get("blocker"), "robots": robots, "terms": terms}
        if kind == "manual_csv":
            if not allow_manual_import:
                return {"allowed": False, "reason": "manual_import_not_authorized", "robots": robots, "terms": terms}
            return {"allowed": True, "reason": None, "robots": robots, "terms": terms}
        if kind == "structured_api":
            if not self.source.get("enabled") and not allow_crawl:
                return {"allowed": False, "reason": "structured_seed_disabled_by_default", "robots": robots, "terms": terms}
            return {"allowed": True, "reason": None, "robots": robots, "terms": terms}
        # HTML/page/sitemap crawl path
        if not allow_crawl:
            return {"allowed": False, "reason": "crawl_not_authorized", "robots": robots, "terms": terms}
        if not robots["robots_allows_automation"]:
            return {"allowed": False, "reason": "robots_disallows_automation", "robots": robots, "terms": terms}
        if not terms["terms_allows_automation"]:
            return {"allowed": False, "reason": "terms_disallows_or_unclear", "robots": robots, "terms": terms}
        return {"allowed": True, "reason": None, "robots": robots, "terms": terms}

    def list_seed_urls(self) -> list[str]:
        # No live URLs persisted in reports; seed enumeration is a future explicit step.
        return []

    # --- extraction (never parses raw HTML; never fabricates) ---
    def extract_coaching_facts_from_page(self, *, structured_fragments: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        # This phase never fetches or parses raw HTML pages. Only pre-extracted
        # structured fragments (if ever provided by an allowed path) are accepted.
        return list(structured_fragments or [])

    def extract_coaching_facts_from_structured_source(self, rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        return [row for row in (rows or []) if isinstance(row, dict)]

    def normalize_coaching_records(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for row in rows:
            role_info = classify_coaching_role(row.get("staff_role"))
            normalized.append(
                {
                    "source_id": self.source.get("source_id"),
                    "source_family": self.source.get("source_family"),
                    "source_kind": self.source.get("source_kind"),
                    "team": _clean(row.get("team")),
                    "team_id": _clean(row.get("team_id")) or None,
                    "season": _clean(row.get("season")),
                    "staff_name": _clean(row.get("staff_name")),
                    "staff_role": _clean(row.get("staff_role")),
                    "canonical_role": role_info["canonical_role"],
                    "role_group": role_info["role_group"],
                    "head_coach_flag": role_info["head_coach_flag"],
                    "offensive_coordinator_flag": role_info["offensive_coordinator_flag"],
                    "defensive_coordinator_flag": role_info["defensive_coordinator_flag"],
                    "special_teams_coordinator_flag": role_info["special_teams_coordinator_flag"],
                    "interim_flag": role_info["interim_flag"],
                    "assistant_flag": role_info["assistant_flag"],
                    "start_date": _clean(row.get("start_date")) or None,
                    "end_date": _clean(row.get("end_date")) or None,
                    "source_effective_date": _clean(row.get("source_effective_date")) or None,
                    "source_updated_date": _clean(row.get("source_updated_date")) or None,
                    "retrieved_at": utc_now_iso(),
                    "provenance_label": _clean(row.get("source_label")) or self.source.get("source_name"),
                    "source_license": _clean(row.get("source_license")) or self.source.get("license_status"),
                    "confidence": _clean(row.get("confidence")) or "source_reported",
                    "validation_status": "available",
                    "blocker": None,
                    "raw_html_persisted": False,
                    "source_data_kind": "coaching_staff_open_or_manual",
                }
            )
        return normalized

    def crawl_allowed_pages(self, *, allow_crawl: bool = False) -> dict[str, Any]:
        decision = self.validate_source_allowed(allow_crawl=allow_crawl)
        # No network fetch occurs; if a future allowed run crawled, it would use a
        # truthful user-agent, crawl_delay>=3s, and a bounded page budget, and would
        # persist only compact extracted facts, never raw HTML.
        return {
            "allowed": decision["allowed"],
            "reason": decision["reason"],
            "pages_fetched": 0,
            "fetch_attempted": False,
            "user_agent": RESEARCH_USER_AGENT,
            "crawl_delay_seconds": self.crawl_delay_seconds,
            "max_pages_per_domain": int(self.source.get("max_pages_per_domain", 25)),
            "spoofs_user_agent": False,
            "browser_impersonation_used": False,
            "raw_html_persisted": False,
            "extracted_facts": [],
        }

    def run_metadata_check(self) -> dict[str, Any]:
        decision = self.validate_source_allowed()
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "metadata_ready",
            "gate": "metadata_check",
            "source_id": self.source.get("source_id"),
            "describe": self.describe_source(),
            "robots": decision["robots"],
            "terms": decision["terms"],
            "allowed": decision["allowed"],
            "blocked_reason": decision["reason"],
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    def run_tiny_sample(self, *, allow_crawl: bool = False) -> dict[str, Any]:
        crawl = self.crawl_allowed_pages(allow_crawl=allow_crawl)
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "sample_ready" if crawl["allowed"] else "blocked",
            "gate": "tiny_sample",
            "source_id": self.source.get("source_id"),
            "blocked_reason": crawl["reason"],
            "records_validated": 0,
            "sample_rows": [],
            "crawl": crawl,
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
        }

    def write_compact_validated_rows(self, rows: list[dict[str, Any]], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
        root = _validated_root(self.source["source_id"], base_data_dir)
        run_id = sanitize_filename(f"nfl_coaching_validated_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}")
        latest_json = root / "latest.json"
        item_json = root / "items" / f"{run_id}.json"
        payload = {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "ok",
            "schema_version": NFL_COACHING_ADAPTER_SCHEMA_VERSION,
            "source_id": self.source["source_id"],
            "data_category": "coaching_staff",
            "created_at": utc_now_iso(),
            "records_validated": len(rows),
            "sample_rows": rows[:200],
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }
        paths = {
            "latest_json_path": _rel(latest_json, base_data_dir),
            "item_json_path": _rel(item_json, base_data_dir),
        }
        _atomic_write_json(latest_json, {**payload, **paths})
        _atomic_write_json(item_json, {**payload, **paths})
        return paths

    def build_compact_report(self, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        metadata = self.run_metadata_check()
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "blocked" if not metadata["allowed"] else "ready",
            "schema_version": NFL_COACHING_ADAPTER_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "source_id": self.source.get("source_id"),
            "source_family": self.source.get("source_family"),
            "runtime_data_dir": str(base),
            "target_fields": list(COACHING_TARGET_FIELDS),
            "metadata": metadata,
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


class OfficialTeamStaffPageCrawler(NflCoachingAdapter):
    pass


class OfficialTeamPressReleaseCrawler(NflCoachingAdapter):
    pass


class WikidataCoachingSeedAdapter(NflCoachingAdapter):
    pass


class WikipediaCoachingSeedAdapter(NflCoachingAdapter):
    pass


class OpenLicensedDatasetAdapter(NflCoachingAdapter):
    pass


class BlockedReferenceSourceAdapter(NflCoachingAdapter):
    pass


class ManualCsvCoachingImportAdapter(NflCoachingAdapter):
    def manual_import_dir(self, base: Path) -> Path:
        return base / "manual_imports" / "nfl_coaching"

    def run_manual_import(
        self,
        *,
        input_csv: str | Path | None = None,
        allow_manual_import: bool = False,
        max_records: int | None = None,
        persist_preview: bool = False,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        decision = self.validate_source_allowed(allow_manual_import=allow_manual_import)
        if not decision["allowed"]:
            return self._blocked_import(base, decision["reason"])
        csv_paths: list[Path] = []
        if input_csv:
            csv_paths = [Path(input_csv)]
        else:
            import_dir = self.manual_import_dir(base)
            if import_dir.exists():
                csv_paths = sorted(import_dir.glob("*.csv"))
        validated: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for path in csv_paths:
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    for raw in reader:
                        ok, reason = validate_record_shape(raw, require_license=True)
                        if not ok:
                            rejected.append({"reason": reason, "team": _clean(raw.get("team")), "season": _clean(raw.get("season"))})
                            continue
                        validated.extend(self.normalize_coaching_records([raw]))
                        if max_records is not None and len(validated) >= max_records:
                            break
            except (csv.Error, OSError, UnicodeDecodeError) as exc:
                rejected.append({"reason": "csv_read_error", "detail": type(exc).__name__})
        paths: dict[str, str] = {}
        if persist_preview and validated:
            paths = self.write_compact_validated_rows(validated, base_data_dir=base)
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "ok" if validated else "no_records",
            "gate": "manual_import",
            "source_id": self.source.get("source_id"),
            "records_validated": len(validated),
            "records_rejected": len(rejected),
            "rejected": rejected[:50],
            "sample_rows": validated[:50],
            "coaching_fields_ingested": sorted({field for row in validated for field in row}) if validated else [],
            "teams_covered": sorted({row["team"] for row in validated}),
            "seasons_covered": sorted({row["season"] for row in validated}),
            "role_groups_covered": sorted({row["role_group"] for row in validated}),
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
            **paths,
        }

    def _blocked_import(self, base: Path, reason: str | None) -> dict[str, Any]:
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "blocked",
            "gate": "manual_import",
            "source_id": self.source.get("source_id"),
            "blocked_reason": reason or "manual_import_not_authorized",
            "records_validated": 0,
            "records_rejected": 0,
            "coaching_fields_ingested": [],
            "teams_covered": [],
            "seasons_covered": [],
            "role_groups_covered": [],
            "fetch_attempted": False,
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
        }


_ADAPTER_BY_FAMILY = {
    "official_team_staff_pages": OfficialTeamStaffPageCrawler,
    "official_team_press_releases": OfficialTeamPressReleaseCrawler,
    "official_nfl_staff_or_news_pages": OfficialTeamPressReleaseCrawler,
    "team_sitemaps": OfficialTeamStaffPageCrawler,
    "wikidata_coaching_seed": WikidataCoachingSeedAdapter,
    "wikipedia_coaching_seed": WikipediaCoachingSeedAdapter,
    "open_github_coaching_dataset": OpenLicensedDatasetAdapter,
    "manual_csv_import": ManualCsvCoachingImportAdapter,
    "blocked_pfr_reference": BlockedReferenceSourceAdapter,
    "blocked_ftn_charting": BlockedReferenceSourceAdapter,
}


def adapter_for_source(source: dict[str, Any]) -> NflCoachingAdapter:
    cls = _ADAPTER_BY_FAMILY.get(str(source.get("source_family")), NflCoachingAdapter)
    return cls(source)


def adapter_by_id(source_id: str) -> NflCoachingAdapter | None:
    source = coaching_source_by_id(source_id)
    return adapter_for_source(source) if source else None


def _validated_root(source_id: str, base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "coaching" / "validated" / sanitize_filename(source_id)
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


def load_validated_coaching_rows(*, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    base = resolve_base_data_dir(base_data_dir)
    root = base / "data_sources" / "nfl_open_data" / "coaching" / "validated"
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for latest in root.glob("*/latest.json"):
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in payload.get("sample_rows") or []:
            if isinstance(row, dict):
                rows.append(row)
    return rows


def build_nfl_coaching_ingestion_report(
    *,
    allow_crawl: bool = False,
    allow_manual_import: bool = False,
    input_csv: str | Path | None = None,
    persist_preview: bool = False,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    sources = nfl_coaching_sources()
    runs: list[dict[str, Any]] = []
    validated_total = 0
    rejected_total = 0
    teams: set[str] = set()
    seasons: set[str] = set()
    role_groups: set[str] = set()
    robots_allowed = robots_blocked = terms_allowed = terms_blocked = 0
    for source in sources:
        adapter = adapter_for_source(source)
        metadata = adapter.run_metadata_check()
        if metadata["robots"]["robots_allows_automation"]:
            robots_allowed += 1
        else:
            robots_blocked += 1
        if metadata["terms"]["terms_allows_automation"]:
            terms_allowed += 1
        else:
            terms_blocked += 1
        if isinstance(adapter, ManualCsvCoachingImportAdapter):
            run = adapter.run_manual_import(
                input_csv=input_csv,
                allow_manual_import=allow_manual_import,
                persist_preview=persist_preview,
                base_data_dir=base,
            )
            validated_total += int(run.get("records_validated", 0) or 0)
            rejected_total += int(run.get("records_rejected", 0) or 0)
            teams.update(run.get("teams_covered") or [])
            seasons.update(run.get("seasons_covered") or [])
            role_groups.update(run.get("role_groups_covered") or [])
            runs.append(run)
        else:
            runs.append(adapter.build_compact_report(base_data_dir=base))
    allowed_sources = [s["source_id"] for s in sources if s["approval_status"] in {"approved_open_structured", "approved_manual_import"}]
    blocked_sources = [{"source_id": s["source_id"], "blocker": s["blocker"]} for s in sources if s["approval_status"] == "blocked"]
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_COACHING_ADAPTER_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_coaching_ingestion_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "sources_checked": len(sources),
        "sources_allowed": allowed_sources,
        "sources_blocked": blocked_sources,
        "robots_allowed_count": robots_allowed,
        "robots_blocked_count": robots_blocked,
        "terms_allowed_count": terms_allowed,
        "terms_blocked_count": terms_blocked,
        "records_validated": validated_total,
        "records_rejected": rejected_total,
        "teams_covered": sorted(teams),
        "seasons_covered": sorted(seasons),
        "role_groups_covered": sorted(role_groups),
        "nfl_coaching_data_available": validated_total > 0,
        "nfl_coaching_data_blocked_reason": None if validated_total > 0 else "no_coaching_rows_ingested_yet_sources_disabled_by_default",
        "coaching_runs": runs,
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
    parser.add_argument("--allow-crawl", action="store_true")
    parser.add_argument("--allow-manual-import", action="store_true")
    parser.add_argument("--input-csv", default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    if args.source_id:
        adapter = adapter_by_id(args.source_id)
        if adapter is None:
            report = {"ok": False, "status": "unknown_source", "source_id": args.source_id}
        elif isinstance(adapter, ManualCsvCoachingImportAdapter):
            report = adapter.run_manual_import(input_csv=args.input_csv, allow_manual_import=args.allow_manual_import, persist_preview=args.persist)
        else:
            report = adapter.build_compact_report()
    else:
        report = build_nfl_coaching_ingestion_report(
            allow_crawl=args.allow_crawl,
            allow_manual_import=args.allow_manual_import,
            input_csv=args.input_csv,
            persist_preview=args.persist,
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
