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
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_coaching_sources import (
    COACHING_TARGET_FIELDS,
    MIN_CRAWL_DELAY_SECONDS,
    RESEARCH_USER_AGENT,
    coaching_source_by_id,
    nfl_coaching_sources,
)
from .open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


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

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_DEFAULT_TIMEOUT_SECONDS = 15
WIKIDATA_MAX_RETRIES = 1
# Descriptive contact appended to the truthful research user-agent per the
# Wikidata user-agent policy. This is project provenance, not browser spoofing.
WIKIDATA_CONTACT_URL = "https://github.com/mazycksekou/betting-stock-api-code-integration"
WIKIDATA_USER_AGENT = f"{RESEARCH_USER_AGENT} (+{WIKIDATA_CONTACT_URL})"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _parse_iso_date(value: Any) -> date | None:
    text = _clean(value)
    if not text:
        return None
    text = text.lstrip("+")  # Wikidata times look like +2013-01-01T00:00:00Z
    try:
        return datetime.fromisoformat(text[:10]).date()
    except ValueError:
        return None


def _date_to_nfl_season(value: date) -> int:
    # NFL season year = season starting year; games Jan-July belong to prior year's season.
    return value.year if value.month >= 8 else value.year - 1


def expand_coaching_dates_to_team_seasons(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a coaching fact to team-season rows using only clear date bounds.

    Never fabricates a season. With start+end dates, emits all overlapping NFL
    seasons. With only an effective date, emits a single point-in-time record.
    With no usable dates, emits one row flagged requires_season_expansion.
    """
    start = _parse_iso_date(row.get("start_date"))
    end = _parse_iso_date(row.get("end_date"))
    effective = _parse_iso_date(row.get("source_effective_date"))
    existing_season = _clean(row.get("season"))
    if existing_season.isdigit():
        return [{**row, "season": existing_season, "season_resolution_status": "source_supplied"}]
    if start and end and _date_to_nfl_season(end) >= _date_to_nfl_season(start):
        first, last = _date_to_nfl_season(start), _date_to_nfl_season(end)
        return [
            {**row, "season": str(season), "season_resolution_status": "expanded_from_date_interval"}
            for season in range(first, last + 1)
        ]
    if start and not end:
        return [{**row, "season": str(_date_to_nfl_season(start)), "season_resolution_status": "open_interval_start_season_only"}]
    if effective:
        return [{**row, "season": str(_date_to_nfl_season(effective)), "season_resolution_status": "point_in_time"}]
    return [{**row, "season": "", "season_resolution_status": "requires_season_expansion"}]


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


def validate_record_shape(
    record: dict[str, Any],
    *,
    require_license: bool = False,
    require_season: bool = True,
) -> tuple[bool, str | None]:
    for field in REQUIRED_RECORD_FIELDS:
        if field == "season" and not require_season:
            continue
        if not _clean(record.get(field)):
            return False, f"missing_required_field:{field}"
    season = _clean(record.get("season"))
    if require_season:
        if not season.isdigit() or not (1920 <= int(season) <= 2100):
            return False, "invalid_season"
    elif season and (not season.isdigit() or not (1920 <= int(season) <= 2100)):
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

    def validate_source_allowed(
        self,
        *,
        allow_crawl: bool = False,
        allow_manual_import: bool = False,
        allow_structured_seed: bool = False,
    ) -> dict[str, Any]:
        robots = self.check_robots_txt()
        terms = self.check_terms_status()
        kind = self.source.get("source_kind")
        if self.source.get("approval_status") == "blocked":
            return {"allowed": False, "reason": self.source.get("blocker"), "robots": robots, "terms": terms}
        if kind == "manual_csv":
            if not allow_manual_import:
                return {"allowed": False, "reason": "manual_import_not_authorized", "robots": robots, "terms": terms}
            return {"allowed": True, "reason": None, "robots": robots, "terms": terms}
        if kind in {"structured_open_data", "structured_api"}:
            if self.source.get("supplemental_only"):
                return {"allowed": False, "reason": "supplemental_only_no_record_ingestion", "robots": robots, "terms": terms}
            if not (allow_structured_seed or self.source.get("enabled")):
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
        latest_md = root / "latest.md"
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
            "sample_rows": rows[:500],
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }
        by_team_paths: list[str] = []
        by_season_paths: list[str] = []
        by_team: dict[str, list[dict[str, Any]]] = {}
        by_season: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            team = _clean(row.get("team"))
            season = _clean(row.get("season"))
            if team:
                by_team.setdefault(team, []).append(row)
            if season:
                by_season.setdefault(season, []).append(row)
        paths = {
            "latest_json_path": _rel(latest_json, base_data_dir),
            "latest_markdown_path": _rel(latest_md, base_data_dir),
            "item_json_path": _rel(item_json, base_data_dir),
        }
        _atomic_write_json(latest_json, {**payload, **paths})
        _atomic_write_text(latest_md, _coaching_validated_markdown(payload))
        _atomic_write_json(item_json, {**payload, **paths})
        for team, team_rows in sorted(by_team.items()):
            path = root / "by_team" / f"{sanitize_filename(team)}.json"
            _atomic_write_json(path, {**payload, "scope": "team", "scope_value": team, "records_validated": len(team_rows), "sample_rows": team_rows[:500]})
            by_team_paths.append(_rel(path, base_data_dir))
        for season, season_rows in sorted(by_season.items()):
            path = root / "by_season" / f"{sanitize_filename(season)}.json"
            _atomic_write_json(path, {**payload, "scope": "season", "scope_value": season, "records_validated": len(season_rows), "sample_rows": season_rows[:500]})
            by_season_paths.append(_rel(path, base_data_dir))
        paths["by_team_paths"] = by_team_paths
        paths["by_season_paths"] = by_season_paths
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


def _default_wikidata_fetch(query: str, *, timeout: int = WIKIDATA_DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Bounded, no-auth GET against the public Wikidata SPARQL endpoint.

    Returns parsed JSON. The raw response is parsed in memory and never written
    to disk. Uses a truthful research user-agent (no browser spoofing).
    """
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    url = f"{WIKIDATA_SPARQL_ENDPOINT}?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": WIKIDATA_USER_AGENT,
            "Accept": "application/sparql-results+json",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (no-auth public endpoint)
        return json.loads(response.read().decode("utf-8"))


class WikidataCoachingSeedAdapter(NflCoachingAdapter):
    def build_wikidata_query(self, *, max_records: int = 500) -> str:
        limit = max(1, min(int(max_records), 5000))
        # Bounded SPARQL: NFL teams (P118 = American football league NFL via team),
        # head coach (P286) statements with optional start/end qualifiers.
        return (
            "SELECT ?team ?teamLabel ?coach ?coachLabel ?start ?end WHERE {\n"
            "  ?team wdt:P118 wd:Q1215884 .\n"
            "  ?team p:P286 ?stmt .\n"
            "  ?stmt ps:P286 ?coach .\n"
            "  OPTIONAL { ?stmt pq:P580 ?start . }\n"
            "  OPTIONAL { ?stmt pq:P582 ?end . }\n"
            "  SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". }\n"
            "}\n"
            f"LIMIT {limit}"
        )

    def normalize_wikidata_records(self, bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raw_rows: list[dict[str, Any]] = []
        for binding in bindings or []:
            if not isinstance(binding, dict):
                continue
            team = _binding_value(binding, "teamLabel") or _binding_value(binding, "team")
            coach = _binding_value(binding, "coachLabel") or _binding_value(binding, "coach")
            if not team or not coach:
                continue
            raw_rows.append(
                {
                    "team": team,
                    "season": "",
                    "staff_name": coach,
                    "staff_role": "Head Coach",
                    "start_date": _binding_value(binding, "start"),
                    "end_date": _binding_value(binding, "end"),
                    "source_label": "Wikidata",
                    "source_license": "CC0",
                    "source_entity_id": _binding_qid(binding, "team"),
                    "source_statement_id": _binding_qid(binding, "coach"),
                    "confidence": "structured_open_data",
                }
            )
        expanded: list[dict[str, Any]] = []
        for raw in raw_rows:
            for row in expand_coaching_dates_to_team_seasons(raw):
                normalized = self.normalize_coaching_records([row])[0]
                normalized["season_resolution_status"] = row.get("season_resolution_status")
                normalized["source_entity_id"] = raw.get("source_entity_id")
                normalized["source_statement_id"] = raw.get("source_statement_id")
                expanded.append(normalized)
        return expanded

    def run_structured_seed_import(
        self,
        *,
        allow_structured_seed: bool = False,
        max_records: int | None = None,
        persist_preview: bool = False,
        season_start: int | None = None,
        season_end: int | None = None,
        fetch_fn: Callable[[str], dict[str, Any]] | None = None,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        decision = self.validate_source_allowed(allow_structured_seed=allow_structured_seed)
        cap = int(max_records) if max_records is not None else 500
        if not decision["allowed"]:
            return self._seed_result(status="blocked", blocked_reason=decision["reason"], cap=cap)
        query = self.build_wikidata_query(max_records=cap)
        fetcher = fetch_fn or _default_wikidata_fetch
        provider_calls = 0
        downloads_attempted = 0
        downloads_succeeded = 0
        bindings: list[dict[str, Any]] = []
        fetch_error: str | None = None
        for attempt in range(WIKIDATA_MAX_RETRIES + 1):
            provider_calls += 1
            downloads_attempted += 1
            try:
                payload = fetcher(query)
                downloads_succeeded += 1
                bindings = list((payload or {}).get("results", {}).get("bindings", []))
                break
            except urllib.error.HTTPError as exc:
                fetch_error = f"structured_seed_fetch_failed:HTTP_{exc.code}"
                bindings = []
                # Respect rate limits / bot blocks: never retry-spam a 429/403.
                if exc.code in (403, 429):
                    fetch_error = (
                        "structured_seed_rate_limited_HTTP_429"
                        if exc.code == 429
                        else "structured_seed_forbidden_HTTP_403"
                    )
                    break
            except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError, OSError) as exc:
                fetch_error = "structured_seed_fetch_failed:" + type(exc).__name__
                bindings = []
        normalized = self.normalize_wikidata_records(bindings)[:cap]
        validated: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for row in normalized:
            ok, reason = validate_record_shape(row, require_license=True, require_season=False)
            if not ok:
                rejected.append({"reason": reason, "team": row.get("team")})
                continue
            if season_start is not None and row.get("season") and int(row["season"]) < int(season_start):
                continue
            if season_end is not None and row.get("season") and int(row["season"]) > int(season_end):
                continue
            validated.append(row)
        paths: dict[str, Any] = {}
        if persist_preview and validated:
            paths = self.write_compact_validated_rows(validated, base_data_dir=base)
        result = self._seed_result(
            status="ok" if validated else ("blocked" if fetch_error else "no_records"),
            blocked_reason=fetch_error,
            cap=cap,
            validated=validated,
            rejected=rejected,
            provider_calls=provider_calls,
            downloads_attempted=downloads_attempted,
            downloads_succeeded=downloads_succeeded,
        )
        result.update(paths)
        return result

    def _seed_result(
        self,
        *,
        status: str,
        blocked_reason: str | None,
        cap: int,
        validated: list[dict[str, Any]] | None = None,
        rejected: list[dict[str, Any]] | None = None,
        provider_calls: int = 0,
        downloads_attempted: int = 0,
        downloads_succeeded: int = 0,
    ) -> dict[str, Any]:
        validated = validated or []
        rejected = rejected or []
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": status,
            "gate": "structured_seed_import",
            "source_id": self.source.get("source_id"),
            "source_kind": self.source.get("source_kind"),
            "license_status": "cc0",
            "max_records": cap,
            "blocked_reason": blocked_reason,
            "records_validated": len(validated),
            "records_rejected": len(rejected),
            "rejected": rejected[:50],
            "sample_rows": validated[:50],
            "coaching_fields_ingested": sorted({field for row in validated for field in row}) if validated else [],
            "teams_covered": sorted({row["team"] for row in validated if row.get("team")}),
            "seasons_covered": sorted({row["season"] for row in validated if row.get("season")}),
            "role_groups_covered": sorted({row["role_group"] for row in validated if row.get("role_group")}),
            "fetch_attempted": downloads_attempted > 0,
            "spoofing_used": False,
            "browser_impersonation_used": False,
            "raw_html_persisted": False,
            "raw_payload_persisted": False,
            "no_predictive_claim": True,
            "provider_calls_attempted": provider_calls,
            "downloads_attempted": downloads_attempted,
            "downloads_succeeded": downloads_succeeded,
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    def run_tiny_sample(self, *, allow_structured_seed: bool = False, allow_crawl: bool = False, max_records: int | None = None, fetch_fn: Callable[[str], dict[str, Any]] | None = None, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        cap = int(max_records) if max_records is not None else 25
        return self.run_structured_seed_import(
            allow_structured_seed=allow_structured_seed or allow_crawl,
            max_records=cap,
            persist_preview=False,
            fetch_fn=fetch_fn,
            base_data_dir=base_data_dir,
        )

    def run_structured_seed_import_scheduled(
        self,
        *,
        allow_structured_seed: bool = False,
        max_records: int | None = None,
        request_interval_seconds: int = 65,
        stop_on_429: bool = True,
        persist_preview: bool = False,
        resume: bool = True,
        fetch_fn: Callable[[str], dict[str, Any]] | None = None,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Polite, single-request WDQS run. Honors Retry-After; never retry-spams."""
        base = resolve_base_data_dir(base_data_dir)
        cap = int(max_records) if max_records is not None else 500
        decision = self.validate_source_allowed(allow_structured_seed=allow_structured_seed)
        if not decision["allowed"]:
            result = self._seed_result(status="blocked", blocked_reason=decision["reason"], cap=cap)
            result["mode"] = "structured_seed_import_scheduled"
            return result
        ledger = _read_resume_ledger(self.source["source_id"], base)
        now = datetime.now(tz=timezone.utc)
        if resume and ledger.get("next_safe_run_time"):
            next_dt = _parse_iso_datetime(ledger.get("next_safe_run_time"))
            if next_dt is not None and now < next_dt:
                result = self._seed_result(status="blocked", blocked_reason="scheduled_wait_window_active", cap=cap)
                result.update({
                    "mode": "structured_seed_import_scheduled",
                    "request_interval_seconds": request_interval_seconds,
                    "next_safe_run_time": ledger.get("next_safe_run_time"),
                    "retry_after_seconds": max(0, int((next_dt - now).total_seconds())),
                })
                return result
        query = self.build_wikidata_query(max_records=cap)
        fetcher = fetch_fn or _default_wikidata_fetch
        provider_calls = 1
        downloads_attempted = 1
        downloads_succeeded = 0
        bindings: list[dict[str, Any]] = []
        blocked_reason: str | None = None
        retry_after = request_interval_seconds
        try:
            payload = fetcher(query)
            downloads_succeeded = 1
            bindings = list((payload or {}).get("results", {}).get("bindings", []))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                blocked_reason = "structured_seed_rate_limited_HTTP_429"
                retry_after = _retry_after_seconds(exc, default=request_interval_seconds)
            elif exc.code == 403:
                blocked_reason = "structured_seed_forbidden_HTTP_403"
            else:
                blocked_reason = f"structured_seed_fetch_failed:HTTP_{exc.code}"
        except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError, OSError) as exc:
            blocked_reason = "structured_seed_fetch_failed:" + type(exc).__name__
        next_safe = (now + timedelta(seconds=retry_after)).isoformat()
        _write_resume_ledger(self.source["source_id"], base, {"last_run_at": now.isoformat(), "next_safe_run_time": next_safe, "last_blocked_reason": blocked_reason})
        if blocked_reason:
            result = self._seed_result(status="blocked", blocked_reason=blocked_reason, cap=cap, provider_calls=provider_calls, downloads_attempted=downloads_attempted, downloads_succeeded=downloads_succeeded)
            result.update({"mode": "structured_seed_import_scheduled", "request_interval_seconds": request_interval_seconds, "retry_after_seconds": retry_after, "next_safe_run_time": next_safe, "stop_on_429": stop_on_429})
            return result
        normalized = self.normalize_wikidata_records(bindings)[:cap]
        validated, rejected = _validate_seed_rows(normalized)
        paths = self.write_compact_validated_rows(validated, base_data_dir=base) if (persist_preview and validated) else {}
        result = self._seed_result(status="ok" if validated else "no_records", blocked_reason=None, cap=cap, validated=validated, rejected=rejected, provider_calls=provider_calls, downloads_attempted=downloads_attempted, downloads_succeeded=downloads_succeeded)
        result.update({"mode": "structured_seed_import_scheduled", "request_interval_seconds": request_interval_seconds, "next_safe_run_time": next_safe})
        result.update(paths)
        return result


class WikipediaCoachingSeedAdapter(NflCoachingAdapter):
    """Supplemental provenance only. Never parses article prose; ingests no rows."""

    def build_attribution_note(self) -> dict[str, Any]:
        return {
            "source_id": self.source.get("source_id"),
            "license_status": "cc_by_sa",
            "attribution_required": True,
            "attribution_text": "Content derived from Wikipedia, licensed CC BY-SA.",
            "usage": "supplemental_page_title_and_provenance_only",
            "parses_article_prose": False,
            "persists_raw_text": False,
        }

    def run_structured_seed_import(self, **kwargs: Any) -> dict[str, Any]:
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "blocked",
            "gate": "structured_seed_import",
            "source_id": self.source.get("source_id"),
            "blocked_reason": "supplemental_only_no_record_ingestion",
            "records_validated": 0,
            "records_rejected": 0,
            "attribution": self.build_attribution_note(),
            "parses_article_prose": False,
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "no_predictive_claim": True,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "secrets_included": False,
        }


NFL_TEAMS = [
    ("Buffalo Bills", "BUF"), ("Miami Dolphins", "MIA"), ("New England Patriots", "NE"), ("New York Jets", "NYJ"),
    ("Baltimore Ravens", "BAL"), ("Cincinnati Bengals", "CIN"), ("Cleveland Browns", "CLE"), ("Pittsburgh Steelers", "PIT"),
    ("Houston Texans", "HOU"), ("Indianapolis Colts", "IND"), ("Jacksonville Jaguars", "JAX"), ("Tennessee Titans", "TEN"),
    ("Denver Broncos", "DEN"), ("Kansas City Chiefs", "KC"), ("Las Vegas Raiders", "LV"), ("Los Angeles Chargers", "LAC"),
    ("Dallas Cowboys", "DAL"), ("New York Giants", "NYG"), ("Philadelphia Eagles", "PHI"), ("Washington Commanders", "WAS"),
    ("Chicago Bears", "CHI"), ("Detroit Lions", "DET"), ("Green Bay Packers", "GB"), ("Minnesota Vikings", "MIN"),
    ("Atlanta Falcons", "ATL"), ("Carolina Panthers", "CAR"), ("New Orleans Saints", "NO"), ("Tampa Bay Buccaneers", "TB"),
    ("Arizona Cardinals", "ARI"), ("Los Angeles Rams", "LAR"), ("San Francisco 49ers", "SF"), ("Seattle Seahawks", "SEA"),
]

WIKIDATA_ENTITY_DATA_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
HEAD_COACH_PROPERTY = "P286"
START_TIME_QUALIFIER = "P580"
END_TIME_QUALIFIER = "P582"


def team_qid_manifest_path(base: Path) -> Path:
    return base / "manual_imports" / "nfl_coaching" / "team_wikidata_qids.csv"


def generate_team_qid_manifest_template(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    path = team_qid_manifest_path(base)
    created = False
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["team", "team_abbr", "wikidata_qid", "source_label", "source_license", "notes"])
            writer.writeheader()
            for team, abbr in NFL_TEAMS:
                writer.writerow({"team": team, "team_abbr": abbr, "wikidata_qid": "", "source_label": "Wikidata", "source_license": "CC0", "notes": "needs_manual_qid"})
        created = True
    return {"manifest_path": _rel(path, base_data_dir), "created": created, "teams": len(NFL_TEAMS)}


def read_team_qid_manifest(*, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    base = resolve_base_data_dir(base_data_dir)
    path = team_qid_manifest_path(base)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                rows.append({k: _clean(v) for k, v in raw.items()})
    except (csv.Error, OSError, UnicodeDecodeError):
        return []
    return rows


def _default_entity_fetch(qid: str, *, timeout: int = WIKIDATA_DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Bounded no-auth GET of a single Wikidata entity by QID (not SPARQL)."""
    url = WIKIDATA_ENTITY_DATA_URL.format(qid=urllib.parse.quote(qid))
    request = urllib.request.Request(url, headers={"User-Agent": WIKIDATA_USER_AGENT, "Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _extract_head_coach_claims(entity: dict[str, Any], qid: str) -> list[dict[str, Any]]:
    """Extract head-coach (P286) statements from a Wikidata entity JSON. No raw payload kept."""
    entities = entity.get("entities") if isinstance(entity, dict) else None
    node = (entities or {}).get(qid) if isinstance(entities, dict) else entity
    claims = (node or {}).get("claims", {}) if isinstance(node, dict) else {}
    out: list[dict[str, Any]] = []
    for statement in claims.get(HEAD_COACH_PROPERTY, []) or []:
        mainsnak = statement.get("mainsnak", {}) if isinstance(statement, dict) else {}
        datavalue = mainsnak.get("datavalue", {}) if isinstance(mainsnak, dict) else {}
        coach_qid = (datavalue.get("value", {}) or {}).get("id") if isinstance(datavalue.get("value"), dict) else None
        qualifiers = statement.get("qualifiers", {}) if isinstance(statement, dict) else {}
        out.append(
            {
                "coach_qid": coach_qid,
                "statement_id": statement.get("id"),
                "start_date": _qualifier_time(qualifiers, START_TIME_QUALIFIER),
                "end_date": _qualifier_time(qualifiers, END_TIME_QUALIFIER),
            }
        )
    return out


def _qualifier_time(qualifiers: dict[str, Any], prop: str) -> str:
    for q in qualifiers.get(prop, []) or []:
        value = (q.get("datavalue", {}) or {}).get("value", {})
        if isinstance(value, dict) and value.get("time"):
            return str(value["time"])
    return ""


def _entity_label(entity: dict[str, Any], qid: str, lang: str = "en") -> str:
    entities = entity.get("entities") if isinstance(entity, dict) else None
    node = (entities or {}).get(qid) if isinstance(entities, dict) else entity
    labels = (node or {}).get("labels", {}) if isinstance(node, dict) else {}
    return _clean((labels.get(lang, {}) or {}).get("value"))


class WikidataEntityApiCoachingAdapter(NflCoachingAdapter):
    """Direct Wikidata entity API fallback (no SPARQL). Respects rate limits."""

    def team_qid_manifest_check(self, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        template = generate_team_qid_manifest_template(base_data_dir=base)
        manifest = read_team_qid_manifest(base_data_dir=base)
        with_qid = [r for r in manifest if r.get("wikidata_qid")]
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": "ok",
            "gate": "team_qid_manifest_check",
            "source_id": self.source.get("source_id"),
            "manifest_path": template["manifest_path"],
            "manifest_template_created": template["created"],
            "teams_in_manifest": len(manifest),
            "teams_with_qid": len(with_qid),
            "teams_needing_qid": len(manifest) - len(with_qid),
            "uses_sparql": False,
            "raw_payload_included": False,
            "raw_html_persisted": False,
            "secrets_included": False,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
        }

    def run_entity_seed_import(
        self,
        *,
        allow_structured_seed: bool = False,
        max_entities: int | None = None,
        max_requests: int | None = None,
        persist_preview: bool = False,
        entity_fetch_fn: Callable[[str], dict[str, Any]] | None = None,
        label_fetch_fn: Callable[[str], dict[str, Any]] | None = None,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        if not allow_structured_seed:
            return self._entity_result(status="blocked", blocked_reason="structured_seed_disabled_by_default")
        generate_team_qid_manifest_template(base_data_dir=base)
        manifest = [r for r in read_team_qid_manifest(base_data_dir=base) if r.get("wikidata_qid")]
        if not manifest:
            return self._entity_result(status="blocked", blocked_reason="team_qid_manifest_empty_needs_manual_qid")
        entity_fetcher = entity_fetch_fn or _default_entity_fetch
        label_fetcher = label_fetch_fn or _default_entity_fetch
        max_e = int(max_entities) if max_entities is not None else 32
        max_r = int(max_requests) if max_requests is not None else 64
        provider_calls = downloads_attempted = downloads_succeeded = 0
        raw_rows: list[dict[str, Any]] = []
        label_cache: dict[str, str] = {}
        blocked_reason: str | None = None
        for entry in manifest[:max_e]:
            if provider_calls >= max_r:
                break
            qid = entry["wikidata_qid"]
            provider_calls += 1
            downloads_attempted += 1
            try:
                entity = entity_fetcher(qid)
                downloads_succeeded += 1
            except urllib.error.HTTPError as exc:
                if exc.code in (403, 429):
                    blocked_reason = "entity_api_rate_limited_HTTP_429" if exc.code == 429 else "entity_api_forbidden_HTTP_403"
                    break
                blocked_reason = f"entity_api_fetch_failed:HTTP_{exc.code}"
                continue
            except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError, OSError) as exc:
                blocked_reason = "entity_api_fetch_failed:" + type(exc).__name__
                continue
            for claim in _extract_head_coach_claims(entity, qid):
                coach_qid = claim.get("coach_qid")
                coach_name = ""
                if coach_qid:
                    if coach_qid in label_cache:
                        coach_name = label_cache[coach_qid]
                    elif provider_calls < max_r:
                        provider_calls += 1
                        downloads_attempted += 1
                        try:
                            coach_entity = label_fetcher(coach_qid)
                            downloads_succeeded += 1
                            coach_name = _entity_label(coach_entity, coach_qid)
                            label_cache[coach_qid] = coach_name
                        except Exception:  # noqa: BLE001 - label resolution is best-effort, never fabricated
                            coach_name = ""
                if not coach_name:
                    continue
                raw_rows.append(
                    {
                        "team": entry.get("team"),
                        "team_abbr": entry.get("team_abbr"),
                        "season": "",
                        "staff_name": coach_name,
                        "staff_role": "Head Coach",
                        "start_date": claim.get("start_date"),
                        "end_date": claim.get("end_date"),
                        "source_label": "Wikidata Entity API",
                        "source_license": "CC0",
                        "source_entity_id": qid,
                        "source_statement_id": claim.get("statement_id"),
                        "source_property_id": HEAD_COACH_PROPERTY,
                    }
                )
        normalized: list[dict[str, Any]] = []
        for raw in raw_rows:
            for row in expand_coaching_dates_to_team_seasons(raw):
                rec = self.normalize_coaching_records([row])[0]
                rec["season_resolution_status"] = row.get("season_resolution_status")
                rec["source_entity_id"] = raw.get("source_entity_id")
                rec["source_statement_id"] = raw.get("source_statement_id")
                rec["source_property_id"] = raw.get("source_property_id")
                normalized.append(rec)
        validated, rejected = _validate_seed_rows(normalized)
        paths = self.write_compact_validated_rows(validated, base_data_dir=base) if (persist_preview and validated) else {}
        status = "ok" if validated else ("blocked" if blocked_reason else "no_records")
        result = self._entity_result(status=status, blocked_reason=blocked_reason, validated=validated, rejected=rejected, provider_calls=provider_calls, downloads_attempted=downloads_attempted, downloads_succeeded=downloads_succeeded)
        result.update(paths)
        return result

    def run_entity_tiny_sample(self, *, allow_structured_seed: bool = False, entity_fetch_fn: Callable[[str], dict[str, Any]] | None = None, label_fetch_fn: Callable[[str], dict[str, Any]] | None = None, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        return self.run_entity_seed_import(allow_structured_seed=allow_structured_seed, max_entities=2, max_requests=6, persist_preview=False, entity_fetch_fn=entity_fetch_fn, label_fetch_fn=label_fetch_fn, base_data_dir=base_data_dir)

    def _entity_result(self, *, status: str, blocked_reason: str | None, validated: list[dict[str, Any]] | None = None, rejected: list[dict[str, Any]] | None = None, provider_calls: int = 0, downloads_attempted: int = 0, downloads_succeeded: int = 0) -> dict[str, Any]:
        validated = validated or []
        rejected = rejected or []
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": status,
            "gate": "entity_seed_import",
            "source_id": self.source.get("source_id"),
            "license_status": "cc0",
            "uses_sparql": False,
            "blocked_reason": blocked_reason,
            "records_validated": len(validated),
            "records_rejected": len(rejected),
            "rejected": rejected[:50],
            "sample_rows": validated[:50],
            "teams_covered": sorted({r["team"] for r in validated if r.get("team")}),
            "seasons_covered": sorted({r["season"] for r in validated if r.get("season")}),
            "role_groups_covered": sorted({r["role_group"] for r in validated if r.get("role_group")}),
            "fetch_attempted": downloads_attempted > 0,
            "spoofing_used": False,
            "browser_impersonation_used": False,
            "raw_html_persisted": False,
            "raw_payload_persisted": False,
            "no_predictive_claim": True,
            "provider_calls_attempted": provider_calls,
            "downloads_attempted": downloads_attempted,
            "downloads_succeeded": downloads_succeeded,
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }


class WikidataDumpCoachingAdapter(NflCoachingAdapter):
    """Local Wikidata dump streaming fallback. Avoids live query endpoints entirely."""

    def _open_dump(self, path: Path):
        if path.suffix == ".gz":
            import gzip

            return gzip.open(path, "rt", encoding="utf-8")
        if path.suffix == ".bz2":
            import bz2

            return bz2.open(path, "rt", encoding="utf-8")
        return path.open("r", encoding="utf-8")

    def run_dump_import(
        self,
        *,
        dump_path: str | Path | None = None,
        allow_local_dump: bool = False,
        max_entities: int | None = None,
        max_records: int | None = None,
        persist_preview: bool = False,
        tiny_scan: bool = False,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        if not allow_local_dump:
            return self._dump_result(status="blocked", blocked_reason="local_dump_not_authorized")
        if not dump_path:
            return self._dump_result(status="blocked", blocked_reason="dump_path_missing", instructions=self._dump_instructions(base))
        path = Path(dump_path)
        if not path.exists():
            return self._dump_result(status="blocked", blocked_reason="dump_file_not_found", instructions=self._dump_instructions(base))
        manifest = {r["wikidata_qid"]: r for r in read_team_qid_manifest(base_data_dir=base) if r.get("wikidata_qid")}
        max_e = int(max_entities) if max_entities is not None else (50 if tiny_scan else 5000)
        raw_rows: list[dict[str, Any]] = []
        entities_scanned = 0
        try:
            with self._open_dump(path) as handle:
                for line in handle:  # stream; never load whole dump
                    line = line.strip().rstrip(",")
                    if not line or line in ("[", "]"):
                        continue
                    entities_scanned += 1
                    if entities_scanned > max_e:
                        break
                    try:
                        entity = json.loads(line)
                    except ValueError:
                        continue
                    qid = entity.get("id")
                    if manifest and qid not in manifest:
                        continue
                    for claim in _extract_head_coach_claims({"entities": {qid: entity}}, qid):
                        if not claim.get("coach_qid"):
                            continue
                        team = manifest.get(qid, {}).get("team") if manifest else qid
                        raw_rows.append(
                            {
                                "team": team,
                                "season": "",
                                "staff_name": claim["coach_qid"],  # label resolution not available offline without person entities
                                "staff_role": "Head Coach",
                                "start_date": claim.get("start_date"),
                                "end_date": claim.get("end_date"),
                                "source_label": "Wikidata Dump",
                                "source_license": "CC0",
                                "source_entity_id": qid,
                                "source_statement_id": claim.get("statement_id"),
                            }
                        )
        except OSError as exc:
            return self._dump_result(status="blocked", blocked_reason="dump_read_error:" + type(exc).__name__)
        normalized: list[dict[str, Any]] = []
        for raw in raw_rows:
            for row in expand_coaching_dates_to_team_seasons(raw):
                rec = self.normalize_coaching_records([row])[0]
                rec["season_resolution_status"] = row.get("season_resolution_status")
                normalized.append(rec)
        validated, rejected = _validate_seed_rows(normalized)
        paths = self.write_compact_validated_rows(validated, base_data_dir=base) if (persist_preview and validated) else {}
        result = self._dump_result(status="ok" if validated else "no_records", blocked_reason=None, validated=validated, rejected=rejected, entities_scanned=entities_scanned)
        result.update(paths)
        return result

    def _dump_instructions(self, base: Path) -> dict[str, Any]:
        target = base / "manual_imports" / "nfl_coaching" / "wikidata_dump"
        return {
            "place_dump_under": _rel(target, base),
            "expected_filename_patterns": ["latest-all.json.gz", "wikidata-*.json.bz2", "*.ndjson"],
            "rerun_command": ".\\scripts\\run_nfl_coaching_import.ps1 -Mode dump_structured_seed_import -AllowLocalDump -WikidataDumpPath <path> -PersistPreview",
        }

    def _dump_result(self, *, status: str, blocked_reason: str | None, validated: list[dict[str, Any]] | None = None, rejected: list[dict[str, Any]] | None = None, entities_scanned: int = 0, instructions: dict[str, Any] | None = None) -> dict[str, Any]:
        validated = validated or []
        rejected = rejected or []
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": status,
            "gate": "dump_structured_seed_import",
            "source_id": self.source.get("source_id"),
            "license_status": "cc0",
            "uses_sparql": False,
            "uses_live_query_endpoint": False,
            "blocked_reason": blocked_reason,
            "entities_scanned": entities_scanned,
            "records_validated": len(validated),
            "records_rejected": len(rejected),
            "rejected": rejected[:50],
            "sample_rows": validated[:50],
            "teams_covered": sorted({r["team"] for r in validated if r.get("team")}),
            "seasons_covered": sorted({r["season"] for r in validated if r.get("season")}),
            "role_groups_covered": sorted({r["role_group"] for r in validated if r.get("role_group")}),
            "instructions": instructions,
            "raw_dump_rows_persisted": False,
            "raw_payload_persisted": False,
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


class WikipediaCoachingTableSupplementAdapter(NflCoachingAdapter):
    """Wikipedia structured-table supplemental fallback (API only, attribution required, no prose)."""

    def run_table_import(
        self,
        *,
        allow_structured_seed: bool = False,
        table_fetch_fn: Callable[[str], list[dict[str, Any]]] | None = None,
        page_title: str = "List of NFL head coaches",
        persist_preview: bool = False,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        base = resolve_base_data_dir(base_data_dir)
        if not allow_structured_seed:
            return self._table_result(status="blocked", blocked_reason="structured_seed_disabled_by_default", page_title=page_title)
        if table_fetch_fn is None:
            # No prose parsing and no default HTML fetch: structured-table fetch must be supplied.
            return self._table_result(status="blocked", blocked_reason="wikipedia_table_fetch_not_configured", page_title=page_title)
        try:
            table_rows = table_fetch_fn(page_title)
        except Exception as exc:  # noqa: BLE001
            return self._table_result(status="blocked", blocked_reason="wikipedia_table_fetch_failed:" + type(exc).__name__, page_title=page_title)
        raw_rows: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for entry in table_rows or []:
            if not isinstance(entry, dict):
                continue
            team = _clean(entry.get("team"))
            name = _clean(entry.get("staff_name") or entry.get("coach"))
            if not team or not name:
                rejected.append({"reason": "ambiguous_table_row"})
                continue
            raw_rows.append(
                {
                    "team": team,
                    "season": _clean(entry.get("season")),
                    "staff_name": name,
                    "staff_role": _clean(entry.get("staff_role")) or "Head Coach",
                    "start_date": _clean(entry.get("start_date")),
                    "end_date": _clean(entry.get("end_date")),
                    "source_label": f"Wikipedia: {page_title}",
                    "source_license": "CC BY-SA",
                }
            )
        normalized: list[dict[str, Any]] = []
        for raw in raw_rows:
            for row in expand_coaching_dates_to_team_seasons(raw):
                rec = self.normalize_coaching_records([row])[0]
                rec["season_resolution_status"] = row.get("season_resolution_status")
                rec["attribution_required"] = True
                normalized.append(rec)
        validated, more_rejected = _validate_seed_rows(normalized)
        rejected.extend(more_rejected)
        paths = self.write_compact_validated_rows(validated, base_data_dir=base) if (persist_preview and validated) else {}
        result = self._table_result(status="ok" if validated else "no_records", blocked_reason=None, page_title=page_title, validated=validated, rejected=rejected)
        result.update(paths)
        return result

    def _table_result(self, *, status: str, blocked_reason: str | None, page_title: str, validated: list[dict[str, Any]] | None = None, rejected: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        validated = validated or []
        rejected = rejected or []
        return {
            **SAFETY_FIELDS,
            "ok": True,
            "status": status,
            "gate": "wikipedia_table_import",
            "source_id": self.source.get("source_id"),
            "license_status": "cc_by_sa",
            "attribution_required": True,
            "attribution_text": "Content derived from Wikipedia, licensed CC BY-SA.",
            "page_title": page_title,
            "parses_article_prose": False,
            "blocked_reason": blocked_reason,
            "records_validated": len(validated),
            "records_rejected": len(rejected),
            "rejected": rejected[:50],
            "sample_rows": validated[:50],
            "teams_covered": sorted({r["team"] for r in validated if r.get("team")}),
            "seasons_covered": sorted({r["season"] for r in validated if r.get("season")}),
            "role_groups_covered": sorted({r["role_group"] for r in validated if r.get("role_group")}),
            "raw_html_persisted": False,
            "raw_payload_persisted": False,
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


MANUAL_TEMPLATE_COLUMNS = [
    "team", "season", "staff_name", "staff_role", "canonical_role", "role_group",
    "start_date", "end_date", "source_label", "source_license", "source_url_label",
    "attribution_required", "notes",
]
MANUAL_TEMPLATES = ["head_coaches_template", "coordinators_template", "current_staff_template"]


def generate_manual_templates(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    template_dir = base / "manual_imports" / "nfl_coaching" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in MANUAL_TEMPLATES:
        path = template_dir / f"{name}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MANUAL_TEMPLATE_COLUMNS)
            writer.writeheader()
        written.append(_rel(path, base_data_dir))
    manifest = generate_team_qid_manifest_template(base_data_dir=base)
    return {
        "templates_written": written,
        "team_qid_manifest": manifest["manifest_path"],
        "import_command": ".\\scripts\\run_nfl_coaching_import.ps1 -Mode manual_import -AllowManualImport -InputCsv data/manual_imports/nfl_coaching/<file>.csv -PersistPreview",
    }


class OpenLicensedDatasetAdapter(NflCoachingAdapter):
    pass


class BlockedReferenceSourceAdapter(NflCoachingAdapter):
    pass


def _parse_iso_datetime(value: Any) -> datetime | None:
    text = _clean(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _retry_after_seconds(exc: urllib.error.HTTPError, *, default: int) -> int:
    headers = getattr(exc, "headers", None)
    raw = headers.get("Retry-After") if headers else None
    if raw is None:
        return default
    text = str(raw).strip()
    if text.isdigit():
        return max(1, int(text))
    return default


def _resume_ledger_path(source_id: str, base: Path) -> Path:
    return base / "data_sources" / "nfl_open_data" / "coaching" / "resume_ledgers" / f"{sanitize_filename(source_id)}.json"


def _read_resume_ledger(source_id: str, base: Path) -> dict[str, Any]:
    path = _resume_ledger_path(source_id, base)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_resume_ledger(source_id: str, base: Path, payload: dict[str, Any]) -> None:
    path = _resume_ledger_path(source_id, base)
    _atomic_write_json(path, {**SAFETY_FIELDS, "source_id": source_id, **payload, "raw_payload_included": False, "secrets_included": False})


def _validate_seed_rows(normalized: list[dict[str, Any]], *, season_start: int | None = None, season_end: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validated: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in normalized:
        ok, reason = validate_record_shape(row, require_license=True, require_season=False)
        if not ok:
            rejected.append({"reason": reason, "team": row.get("team")})
            continue
        if season_start is not None and row.get("season") and int(row["season"]) < int(season_start):
            continue
        if season_end is not None and row.get("season") and int(row["season"]) > int(season_end):
            continue
        validated.append(row)
    return validated, rejected


def _binding_value(binding: dict[str, Any], key: str) -> str:
    item = binding.get(key)
    return _clean(item.get("value")) if isinstance(item, dict) else ""


def _binding_qid(binding: dict[str, Any], key: str) -> str | None:
    value = _binding_value(binding, key)
    return value.rsplit("/", 1)[-1] if value.startswith("http") else None


def _coaching_validated_markdown(payload: dict[str, Any]) -> str:
    return (
        "# NFL Coaching Validated Rows\n\n"
        f"1. source_id: {payload.get('source_id')}\n"
        f"2. records_validated: {payload.get('records_validated')}\n"
        "3. raw_html_persisted=false; raw_payload_included=false; secrets_included=false\n"
    )


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
    "wikidata_entity_api": WikidataEntityApiCoachingAdapter,
    "wikidata_local_dump": WikidataDumpCoachingAdapter,
    "wikipedia_coaching_seed": WikipediaCoachingSeedAdapter,
    "wikipedia_coaching_tables": WikipediaCoachingTableSupplementAdapter,
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


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
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
    allow_structured_seed: bool = False,
    input_csv: str | Path | None = None,
    max_records: int | None = None,
    persist_preview: bool = False,
    fetch_fn: Callable[[str], dict[str, Any]] | None = None,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    sources = nfl_coaching_sources()
    runs: list[dict[str, Any]] = []
    validated_total = 0
    rejected_total = 0
    provider_calls_total = 0
    downloads_attempted_total = 0
    downloads_succeeded_total = 0
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
        elif isinstance(adapter, WikidataCoachingSeedAdapter) and allow_structured_seed:
            run = adapter.run_structured_seed_import(
                allow_structured_seed=True,
                max_records=max_records,
                persist_preview=persist_preview,
                fetch_fn=fetch_fn,
                base_data_dir=base,
            )
            validated_total += int(run.get("records_validated", 0) or 0)
            rejected_total += int(run.get("records_rejected", 0) or 0)
            provider_calls_total += int(run.get("provider_calls_attempted", 0) or 0)
            downloads_attempted_total += int(run.get("downloads_attempted", 0) or 0)
            downloads_succeeded_total += int(run.get("downloads_succeeded", 0) or 0)
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
        "nfl_coaching_structured_seed_available": validated_total > 0,
        "nfl_coaching_data_blocked_reason": None if validated_total > 0 else "no_coaching_rows_ingested_yet_sources_disabled_by_default",
        "coaching_runs": runs,
        "spoofing_used": False,
        "browser_impersonation_used": False,
        "raw_html_persisted": False,
        "raw_payload_persisted": False,
        "no_predictive_claim": True,
        "provider_calls_attempted": provider_calls_total,
        "downloads_attempted": downloads_attempted_total,
        "downloads_succeeded": downloads_succeeded_total,
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
