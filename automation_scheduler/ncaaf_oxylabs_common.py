from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .oxylabs_residential_proxy_adapter import OxylabsResidentialProxyAdapter
from .oxylabs_web_scraper_api_adapter import OxylabsWebScraperApiAdapter
from .scheduler_config import sanitize_filename, utc_now_iso


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"
NCAAF_DATA_ROOT = Path("data") / "data_sources" / "ncaaf_open_data"

RUN_MODE = "ncaaf_final_mandatory_oxylabs_source_policy_free_open_exhaustion_backfill_finality"
SUBDIVISIONS_INCLUDED = ("FBS", "Bowl games", "Conference championship games", "College Football Playoff games")

FINAL_ACTIONABLE_STATES = (
    "free_open_backfilled",
    "free_open_postgame_training_only",
    "free_open_metadata_only",
    "free_open_loader_ready_hard_blocked_from_backfill",
    "manual_import_required",
    "paid_subscription_required",
    "policy_blocked",
    "robots_blocked",
    "terms_blocked",
    "login_paywall_captcha_blocked",
    "license_terms_unclear",
    "unavailable_after_exhaustive_free_search",
    "obsolete_or_duplicate",
)

CFBD_API_URL = "https://api.collegefootballdata.com/"
CFBD_DOCS_URL = "https://api.collegefootballdata.com/api/docs/"
CFBFASTR_URL = "https://github.com/sportsdataverse/cfbfastR"
NCAA_FOOTBALL_URL = "https://www.ncaa.com/sports/football/fbs"

OXYLABS_NCAAF_ALLOWED_DOMAINS = (
    "collegefootballdata.com",
    "*.collegefootballdata.com",
    "api.collegefootballdata.com",
    "github.com",
    "*.github.com",
    "raw.githubusercontent.com",
    "*.raw.githubusercontent.com",
    "sportsdataverse.org",
    "*.sportsdataverse.org",
    "ncaa.com",
    "*.ncaa.com",
    "cfbplayoff.com",
    "*.cfbplayoff.com",
    "wikipedia.org",
    "*.wikipedia.org",
    "wikidata.org",
    "*.wikidata.org",
    "kaggle.com",
    "*.kaggle.com",
    "sportsdata.io",
    "*.sportsdata.io",
    "sportradar.com",
    "*.sportradar.com",
    "espn.com",
    "*.espn.com",
)

OXYLABS_NCAAF_ALLOWED_SOURCE_IDS = (
    "ncaaf_cfbd_api_docs",
    "ncaaf_cfbfastr_repo",
    "ncaaf_sportsdataverse_data",
    "ncaaf_wikidata_team_entities",
    "ncaaf_wikipedia_bowl_tables",
    "ncaaf_ncaa_official_pages",
    "ncaaf_conference_official_pages",
    "ncaaf_school_official_pages",
    "ncaaf_bowl_cfp_official_pages",
    "ncaaf_espn_pages",
    "ncaaf_sports_reference_pages",
    "ncaaf_kaggle_catalog",
    "ncaaf_weather_archive",
    "ncaaf_paid_vendor",
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


def current_utc() -> str:
    return utc_now_iso()


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


def extract_web_scraper_content(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return text
    results = payload.get("results")
    if isinstance(results, list):
        parts = []
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
    timeout: int = 45,
) -> dict[str, Any]:
    allowed_domains = tuple(allowed_domains or OXYLABS_NCAAF_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_NCAAF_ALLOWED_SOURCE_IDS)
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
        response = {"ok": False, "status": "blocked", "blocked_reason": "unsupported_transport", "text": ""}
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
    headers: dict[str, str] | None = None,
    timeout: int = 45,
) -> dict[str, Any]:
    response = fetch_text_with_transport(
        transport=transport,
        source_id=source_id,
        domain=domain,
        url=url,
        headers=headers,
        timeout=timeout,
    )
    text = response.get("text") or ""
    if transport == "web_scraper_api":
        text = extract_web_scraper_content(text)
    return {**response, "text": text, "text_length": len(text), "source_url_hash": url_hash(url)}


def source_spec_registry() -> dict[str, OxylabsSourceSpec]:
    return {
        "ncaaf_cfbd_api_docs": OxylabsSourceSpec("ncaaf_cfbd_api_docs", "CollegeFootballData API/docs", "api.collegefootballdata.com", CFBD_DOCS_URL, "residential_proxy", "public_api_docs", "accepted_for_automated_normalized_backfill", "CFBD remains free-key/API-doc governed; this pass uses deterministic normalized sample facts only and records paid/API-key constraints."),
        "ncaaf_cfbfastr_repo": OxylabsSourceSpec("ncaaf_cfbfastr_repo", "cfbfastR GitHub repository", "github.com", CFBFASTR_URL, "web_scraper_api", "community_repo", "license_terms_unclear", "cfbfastR is public, but exact upstream/API/license storage rules require legal review before automated broad reuse."),
        "ncaaf_sportsdataverse_data": OxylabsSourceSpec("ncaaf_sportsdataverse_data", "SportsDataverse CFB data", "sportsdataverse.org", "https://sportsdataverse.org/", "web_scraper_api", "open_data_project", "license_terms_unclear", "SportsDataverse CFB requires exact package/data license and upstream clarity before automated broad reuse."),
        "ncaaf_wikidata_team_entities": OxylabsSourceSpec("ncaaf_wikidata_team_entities", "Wikidata college football entities", "wikidata.org", "https://www.wikidata.org/wiki/Wikidata:Main_Page", "web_scraper_api", "structured_open_metadata", "accepted_for_metadata_only", "Wikidata is metadata-only enrichment with attribution retained."),
        "ncaaf_wikipedia_bowl_tables": OxylabsSourceSpec("ncaaf_wikipedia_bowl_tables", "Wikipedia bowl and CFP tables", "wikipedia.org", "https://en.wikipedia.org/wiki/College_Football_Playoff", "web_scraper_api", "structured_open_metadata", "accepted_for_metadata_only", "Wikipedia tables remain supplemental metadata only with attribution retained."),
        "ncaaf_ncaa_official_pages": OxylabsSourceSpec("ncaaf_ncaa_official_pages", "NCAA football official pages", "ncaa.com", NCAA_FOOTBALL_URL, "web_scraper_api", "official_page", "accepted_for_manual_import_only", "NCAA public pages remain manual-only unless exact automated rights approve extraction."),
        "ncaaf_conference_official_pages": OxylabsSourceSpec("ncaaf_conference_official_pages", "Conference official football pages", "ncaa.com", "https://www.ncaa.com/standings/football/fbs", "web_scraper_api", "official_conference_page", "accepted_for_manual_import_only", "Conference/team data from official pages remains manual-only under the policy floor."),
        "ncaaf_school_official_pages": OxylabsSourceSpec("ncaaf_school_official_pages", "School athletic football pages", "ncaa.com", NCAA_FOOTBALL_URL, "web_scraper_api", "official_school_page", "accepted_for_manual_import_only", "School roster/depth-chart pages remain manual-only unless exact site terms approve automation."),
        "ncaaf_bowl_cfp_official_pages": OxylabsSourceSpec("ncaaf_bowl_cfp_official_pages", "Bowl and CFP official pages", "cfbplayoff.com", "https://collegefootballplayoff.com/", "web_scraper_api", "official_postseason_page", "accepted_for_manual_import_only", "Bowl and CFP pages remain manual-only for timestamped review."),
        "ncaaf_espn_pages": OxylabsSourceSpec("ncaaf_espn_pages", "ESPN college football pages", "espn.com", "https://www.espn.com/college-football/", "web_scraper_api", "reference_site", "policy_blocked", "ESPN scraping is prohibited unless an exact source path passes policy review; this pass blocks automation."),
        "ncaaf_sports_reference_pages": OxylabsSourceSpec("ncaaf_sports_reference_pages", "Sports Reference college football pages", "sports-reference.com", "https://www.sports-reference.com/cfb/", "web_scraper_api", "reference_site", "policy_blocked", "Sports Reference / College Football Reference scraping is explicitly prohibited."),
        "ncaaf_kaggle_catalog": OxylabsSourceSpec("ncaaf_kaggle_catalog", "Kaggle college football dataset catalog", "kaggle.com", "https://www.kaggle.com/datasets?search=college%20football", "web_scraper_api", "dataset_catalog", "login_paywall_captcha_blocked", "Kaggle catalog remains account-gated and not used for automated backfill."),
        "ncaaf_weather_archive": OxylabsSourceSpec("ncaaf_weather_archive", "Public weather archive", "github.com", "https://github.com/search?q=college+football+weather+dataset", "web_scraper_api", "dataset_search", "unavailable_after_exhaustive_search", "No policy-approved normalized NCAAF weather archive was accepted in this pass."),
        "ncaaf_paid_vendor": OxylabsSourceSpec("ncaaf_paid_vendor", "Licensed NCAAF data vendor", "sportsdata.io", "https://sportsdata.io/developers/data-dictionary/ncaa-football", "web_scraper_api", "paid_vendor_page", "paid_subscription_required", "Production NCAAF play-by-play, depth chart, injury, odds, and advanced feeds remain paid/licensed."),
    }


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    return source_spec_registry().get(str(lane.get("source_id") or "")) or source_spec_registry()["ncaaf_cfbd_api_docs"]


def lane_final_state(lane: dict[str, Any], *, backfill_written: bool, hard_blocked: bool = False, policy_final_state: str | None = None) -> str:
    if policy_final_state in FINAL_ACTIONABLE_STATES:
        if policy_final_state == "free_open_backfilled" and not backfill_written:
            return "free_open_loader_ready_hard_blocked_from_backfill"
        return policy_final_state
    category = str(lane.get("free_or_paid_category") or "")
    if hard_blocked:
        return "free_open_loader_ready_hard_blocked_from_backfill"
    if category in {"free_open_populated", "free_open_partial", "free_open_loader_needed", "free_open_sample_required"} and backfill_written:
        return "free_open_backfilled"
    return {
        "paid_data_subscription_required": "paid_subscription_required",
        "free_open_manual_import_needed": "manual_import_required",
        "policy_blocked": "policy_blocked",
        "robots_blocked": "robots_blocked",
        "terms_blocked": "terms_blocked",
        "login_paywall_captcha_blocked": "login_paywall_captcha_blocked",
        "license_terms_unclear": "license_terms_unclear",
        "obsolete_or_duplicate": "obsolete_or_duplicate",
    }.get(category, "unavailable_after_exhaustive_free_search")


def data_session_root(prefix: str) -> tuple[str, Path]:
    session_id = sanitize_filename(f"{prefix}_{current_utc().replace(':', '').replace('-', '')}_{stable_hash(prefix)[:8]}")
    session_root = NCAAF_DATA_ROOT / "backfill_sessions" / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    return session_id, session_root


def ncaaf_sample_rows() -> dict[str, list[dict[str, Any]]]:
    game = {
        "game_id": "2023-401520384",
        "season": 2023,
        "week": 1,
        "season_type": "regular",
        "home_team": "Michigan",
        "away_team": "East Carolina",
        "neutral_site": False,
        "conference_game": False,
        "home_points": 30,
        "away_points": 3,
        "final_margin": 27,
        "total_points": 33,
        "start_date": "2023-09-02T16:00:00Z",
        "venue_id": "michigan-stadium",
        "venue_name": "Michigan Stadium",
        "source_record_hash": stable_hash("2023-michigan-ecu"),
    }
    return {
        "teams": [
            {"team_id": "michigan", "team_name": "Michigan", "subdivision": "FBS", "conference": "Big Ten", "mascot": "Wolverines"},
            {"team_id": "georgia", "team_name": "Georgia", "subdivision": "FBS", "conference": "SEC", "mascot": "Bulldogs"},
            {"team_id": "north-dakota-state", "team_name": "North Dakota State", "subdivision": "FCS", "conference": "MVFC", "mascot": "Bison", "scope_note": "metadata_only_if_existing_scope_accepts_fcs"},
        ],
        "games": [game],
        "drives": [
            {**game, "drive_id": "2023-401520384-1", "offense": "Michigan", "defense": "East Carolina", "drive_number": 1, "plays": 8, "yards": 75, "drive_result": "TD", "drive_points": 7, "drive_epa": 3.42},
            {**game, "drive_id": "2023-401520384-2", "offense": "East Carolina", "defense": "Michigan", "drive_number": 2, "plays": 5, "yards": 18, "drive_result": "PUNT", "drive_points": 0, "drive_epa": -0.88},
        ],
        "plays": [
            {**game, "drive_id": "2023-401520384-1", "play_id": "2023-401520384-1-1", "offense": "Michigan", "defense": "East Carolina", "down": 1, "distance": 10, "yard_line": 25, "play_type": "rush", "yards_gained": 6, "epa": 0.32, "success": True, "explosive": False},
            {**game, "drive_id": "2023-401520384-1", "play_id": "2023-401520384-1-2", "offense": "Michigan", "defense": "East Carolina", "down": 2, "distance": 4, "yard_line": 31, "play_type": "pass", "yards_gained": 24, "epa": 1.14, "success": True, "explosive": True},
        ],
        "venues": [
            {"venue_id": "michigan-stadium", "venue_name": "Michigan Stadium", "city": "Ann Arbor", "state": "MI", "capacity": 107601, "surface": "fieldturf", "indoor": False},
            {"venue_id": "rose-bowl", "venue_name": "Rose Bowl", "city": "Pasadena", "state": "CA", "capacity": 88565, "surface": "grass", "indoor": False},
        ],
    }

