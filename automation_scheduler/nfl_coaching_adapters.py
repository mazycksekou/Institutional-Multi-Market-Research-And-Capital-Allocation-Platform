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
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
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

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_DEFAULT_TIMEOUT_SECONDS = 15
WIKIDATA_MAX_RETRIES = 1


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
            "User-Agent": RESEARCH_USER_AGENT,
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


class OpenLicensedDatasetAdapter(NflCoachingAdapter):
    pass


class BlockedReferenceSourceAdapter(NflCoachingAdapter):
    pass


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
