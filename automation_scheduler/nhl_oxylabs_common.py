from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .oxylabs_residential_proxy_adapter import OxylabsResidentialProxyAdapter
from .oxylabs_web_scraper_api_adapter import OxylabsWebScraperApiAdapter
from .scheduler_config import utc_now_iso


REPORT_ROOT = Path("reports")
NHL_DATA_ROOT = Path("data") / "data_sources" / "nhl_open_data"

FINAL_ACTIONABLE_STATES = (
    "free_open_backfilled",
    "free_open_loader_ready_hard_blocked_from_backfill",
    "paid_subscription_required",
    "manual_import_required",
    "policy_blocked",
    "license_terms_unclear",
    "unavailable_after_exhaustive_free_search",
    "obsolete_or_duplicate",
)

OXYLABS_NHL_ALLOWED_DOMAINS = (
    "api-web.nhle.com",
    "*.nhle.com",
    "nhl.com",
    "*.nhl.com",
    "records.nhl.com",
    "*.records.nhl.com",
    "github.com",
    "*.github.com",
    "*.githubusercontent.com",
    "wikidata.org",
    "*.wikidata.org",
    "wikipedia.org",
    "*.wikipedia.org",
    "naturalstattrick.com",
    "*.naturalstattrick.com",
    "evolving-hockey.com",
    "*.evolving-hockey.com",
    "statsperform.com",
    "*.statsperform.com",
)

OXYLABS_NHL_ALLOWED_SOURCE_IDS = (
    "nhl_official_api",
    "nhl_official_gamecenter_page",
    "nhl_official_reports_page",
    "nhl_team_roster_page",
    "nhl_github_open_docs",
    "nhl_natural_stat_trick_home",
    "nhl_paid_vendor_page",
    "nhl_wikidata_supplemental",
    "nhl_wikipedia_supplemental",
)


@dataclass(frozen=True)
class OxylabsSourceSpec:
    source_id: str
    source_name: str
    domain: str
    url: str
    transport: str
    source_type: str
    policy_status: str
    license_or_terms_note: str


def stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def url_hash(url: str) -> str:
    return hashlib.sha256(str(url).strip().encode("utf-8")).hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return str(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2, sort_keys=True), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def current_utc() -> str:
    return utc_now_iso()


def extract_web_scraper_content(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return text
    results = payload.get("results")
    if isinstance(results, list):
        parts: list[str] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            for key in ("content", "html", "body"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value)
                    break
        if parts:
            return "\n".join(parts)
    job = payload.get("job")
    if isinstance(job, dict):
        content = job.get("content")
        if isinstance(content, str) and content.strip():
            return content
    return text


def fetch_text_with_transport(
    *,
    transport: str,
    source_id: str,
    domain: str,
    url: str,
    allowed_domains: Iterable[str] | None = None,
    allowed_source_ids: Iterable[str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    allowed_domains = tuple(allowed_domains or OXYLABS_NHL_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_NHL_ALLOWED_SOURCE_IDS)
    if transport == "residential_proxy":
        adapter = OxylabsResidentialProxyAdapter(
            source_id=source_id,
            domain=domain,
            allow_oxylabs=True,
            allow_paid_retrieval=True,
            allowed_source_ids=allowed_source_ids,
            allowed_domains=allowed_domains,
        )
        response = adapter.fetch_text(url, timeout=timeout, headers=headers)
    elif transport == "web_scraper_api":
        adapter = OxylabsWebScraperApiAdapter(
            source_id=source_id,
            domain=domain,
            allow_oxylabs=True,
            allow_paid_retrieval=True,
            allowed_source_ids=allowed_source_ids,
            allowed_domains=allowed_domains,
        )
        response = adapter.fetch_text(url, timeout=timeout)
    else:
        response = {
            "ok": False,
            "status": "blocked",
            "blocked_reason": "unsupported_transport",
            "text": "",
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    return {
        "ok": bool(response.get("ok")),
        "status": response.get("status"),
        "blocked_reason": response.get("blocked_reason"),
        "text": response.get("text") or "",
        "transport": transport,
        "source_id": source_id,
        "domain": domain,
        "url": url,
        "raw_html_persisted": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def fetch_public_page_text(
    *,
    source_id: str,
    domain: str,
    url: str,
    transport: str = "web_scraper_api",
    allowed_domains: Iterable[str] | None = None,
    allowed_source_ids: Iterable[str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    response = fetch_text_with_transport(
        transport=transport,
        source_id=source_id,
        domain=domain,
        url=url,
        allowed_domains=allowed_domains,
        allowed_source_ids=allowed_source_ids,
        headers=headers,
        timeout=timeout,
    )
    text = response.get("text") or ""
    if transport == "web_scraper_api":
        text = extract_web_scraper_content(text)
    return {
        **response,
        "text": text,
        "text_length": len(text),
        "source_url_hash": url_hash(url),
    }


def fetch_public_json(
    *,
    source_id: str,
    domain: str,
    url: str,
    transport: str = "residential_proxy",
    allowed_domains: Iterable[str] | None = None,
    allowed_source_ids: Iterable[str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    response = fetch_public_page_text(
        source_id=source_id,
        domain=domain,
        url=url,
        transport=transport,
        allowed_domains=allowed_domains,
        allowed_source_ids=allowed_source_ids,
        headers=headers or {"Accept": "application/json,*/*"},
        timeout=timeout,
    )
    payload: Any = None
    if response.get("ok"):
        try:
            payload = json.loads(response.get("text") or "")
        except Exception:
            payload = None
    return {
        **response,
        "json_payload": payload,
        "json_ok": isinstance(payload, (dict, list)),
    }


def source_spec_registry() -> dict[str, OxylabsSourceSpec]:
    return {
        "nhl_official_api": OxylabsSourceSpec(
            source_id="nhl_official_api",
            source_name="NHL public API",
            domain="api-web.nhle.com",
            url="https://api-web.nhle.com/v1/schedule/now",
            transport="residential_proxy",
            source_type="official_public_api",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Official public NHL API endpoints used only for transient in-memory normalized extraction.",
        ),
        "nhl_official_gamecenter_page": OxylabsSourceSpec(
            source_id="nhl_official_gamecenter_page",
            source_name="NHL Gamecenter landing page",
            domain="api-web.nhle.com",
            url="https://api-web.nhle.com/v1/gamecenter",
            transport="web_scraper_api",
            source_type="official_public_gamecenter_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Official public Gamecenter landing payload used for source confirmation and summary-only discovery.",
        ),
        "nhl_official_reports_page": OxylabsSourceSpec(
            source_id="nhl_official_reports_page",
            source_name="NHL official reports or team public pages",
            domain="nhl.com",
            url="https://www.nhl.com/info",
            transport="web_scraper_api",
            source_type="official_public_report_page",
            policy_status="manual_import_only",
            license_or_terms_note="Public NHL pages may support manual review/import, but automated structured extraction remains conservative in this pass.",
        ),
        "nhl_team_roster_page": OxylabsSourceSpec(
            source_id="nhl_team_roster_page",
            source_name="NHL team roster page",
            domain="nhl.com",
            url="https://www.nhl.com/hurricanes/roster",
            transport="web_scraper_api",
            source_type="official_team_public_page",
            policy_status="manual_import_only",
            license_or_terms_note="Public team pages can support manual imports for unresolved availability lanes.",
        ),
        "nhl_github_open_docs": OxylabsSourceSpec(
            source_id="nhl_github_open_docs",
            source_name="SportsDataverse NHL or GitHub open community docs",
            domain="github.com",
            url="https://github.com/sportsdataverse",
            transport="web_scraper_api",
            source_type="github_open_source_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public GitHub pages are used only for source-family discovery and duplicate checking.",
        ),
        "nhl_natural_stat_trick_home": OxylabsSourceSpec(
            source_id="nhl_natural_stat_trick_home",
            source_name="Natural Stat Trick public pages",
            domain="naturalstattrick.com",
            url="https://www.naturalstattrick.com/",
            transport="web_scraper_api",
            source_type="public_xg_or_line_combo_page",
            policy_status="license_terms_unclear",
            license_or_terms_note="Public pages exist, but the exact automated retrieval path for line-combination or xG data was not safely confirmed in this pass.",
        ),
        "nhl_paid_vendor_page": OxylabsSourceSpec(
            source_id="nhl_paid_vendor_page",
            source_name="Stats Perform / licensed NHL data vendors",
            domain="statsperform.com",
            url="https://www.statsperform.com/",
            transport="web_scraper_api",
            source_type="paid_vendor_page",
            policy_status="paid_subscription_required",
            license_or_terms_note="Public marketing pages can confirm product scope, but the structured data itself requires a paid subscription or license.",
        ),
        "nhl_wikidata_supplemental": OxylabsSourceSpec(
            source_id="nhl_wikidata_supplemental",
            source_name="Wikidata",
            domain="wikidata.org",
            url="https://www.wikidata.org/",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="supplemental_only",
            license_or_terms_note="Supplemental public structured entity metadata only, not a primary performance-stat source.",
        ),
        "nhl_wikipedia_supplemental": OxylabsSourceSpec(
            source_id="nhl_wikipedia_supplemental",
            source_name="Wikipedia",
            domain="wikipedia.org",
            url="https://www.wikipedia.org/",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="supplemental_only",
            license_or_terms_note="Supplemental public table/entity lookup only, not a primary performance-stat source.",
        ),
    }


def source_spec_for(source_id: str) -> OxylabsSourceSpec | None:
    return source_spec_registry().get(source_id)


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    category = str(lane.get("free_or_paid_category") or "")
    lane_name = str(lane.get("lane_name") or "")
    if category in {"free_open_populated", "free_open_partial"}:
        return source_spec_registry()["nhl_official_api"]
    if category == "free_open_manual_import_needed":
        if lane_name == "injuries_availability":
            return source_spec_registry()["nhl_team_roster_page"]
        return source_spec_registry()["nhl_official_reports_page"]
    if category == "paid_data_subscription_required":
        return source_spec_registry()["nhl_paid_vendor_page"]
    if category == "license_terms_unclear":
        return source_spec_registry()["nhl_natural_stat_trick_home"]
    if category in {"policy_blocked", "blocked_reference_or_restricted_source"}:
        return OxylabsSourceSpec(
            source_id="nhl_hockey_reference_blocked",
            source_name="Hockey Reference / blocked restricted source",
            domain="hockey-reference.com",
            url="https://www.hockey-reference.com/",
            transport="web_scraper_api",
            source_type="restricted_reference_site",
            policy_status="blocked_reference_or_restricted_source",
            license_or_terms_note="Blocked by repo policy and explicit user instruction.",
        )
    if category == "obsolete_or_duplicate":
        return source_spec_registry()["nhl_github_open_docs"]
    return source_spec_registry()["nhl_official_gamecenter_page"]


def lane_final_state(lane: dict[str, Any], *, backfill_written: bool, hard_blocked: bool = False) -> str:
    category = str(lane.get("free_or_paid_category") or "")
    if hard_blocked:
        if category in {"policy_blocked", "blocked_reference_or_restricted_source"}:
            return "policy_blocked"
        return "free_open_loader_ready_hard_blocked_from_backfill"
    if category in {"free_open_populated", "free_open_partial"} and backfill_written:
        return "free_open_backfilled"
    if category == "paid_data_subscription_required":
        return "paid_subscription_required"
    if category == "free_open_manual_import_needed":
        return "manual_import_required"
    if category in {"policy_blocked", "blocked_reference_or_restricted_source"}:
        return "policy_blocked"
    if category == "license_terms_unclear":
        return "license_terms_unclear"
    if category == "obsolete_or_duplicate":
        return "obsolete_or_duplicate"
    return "unavailable_after_exhaustive_free_search"


def discover_nhl_sample_context() -> dict[str, Any]:
    schedule_response = fetch_public_json(
        source_id="nhl_official_api",
        domain="api-web.nhle.com",
        url="https://api-web.nhle.com/v1/schedule/now",
        transport="residential_proxy",
    )
    schedule_payload = schedule_response.get("json_payload") or {}
    game_weeks = list(schedule_payload.get("gameWeek") or [])
    sample_game: dict[str, Any] = {}
    for week in game_weeks:
        games = list(week.get("games") or [])
        if games:
            sample_game = games[0]
            break
    previous_start = str(schedule_payload.get("previousStartDate") or "").strip()
    previous_response = (
        fetch_public_json(
            source_id="nhl_official_api",
            domain="api-web.nhle.com",
            url=f"https://api-web.nhle.com/v1/schedule/{previous_start}",
            transport="residential_proxy",
        )
        if previous_start
        else {"ok": False, "json_ok": False, "json_payload": {}}
    )
    sample_game_id = int(sample_game.get("id") or 0)
    home_team = sample_game.get("homeTeam") or {}
    away_team = sample_game.get("awayTeam") or {}
    return {
        "ok": bool(schedule_response.get("ok") and sample_game_id),
        "schedule_response": schedule_response,
        "previous_schedule_response": previous_response,
        "schedule_now": schedule_payload if isinstance(schedule_payload, dict) else {},
        "schedule_previous": previous_response.get("json_payload") if isinstance(previous_response.get("json_payload"), dict) else {},
        "sample_game": sample_game,
        "sample_game_id": sample_game_id,
        "sample_season": int(sample_game.get("season") or 0),
        "sample_game_type": int(sample_game.get("gameType") or 0),
        "home_team_abbrev": str(home_team.get("abbrev") or ""),
        "away_team_abbrev": str(away_team.get("abbrev") or ""),
        "home_team_id": int(home_team.get("id") or 0),
        "away_team_id": int(away_team.get("id") or 0),
        "sample_date": str(sample_game.get("gameDate") or ""),
        "previous_start_date": previous_start,
    }
