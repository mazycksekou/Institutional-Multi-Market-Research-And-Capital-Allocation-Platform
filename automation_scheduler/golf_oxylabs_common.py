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
GOLF_DATA_ROOT = Path("data") / "data_sources" / "golf_open_data"

RUN_MODE = "golf_final_mandatory_oxylabs_source_policy_free_open_exhaustion_backfill_finality"
TOURS_INCLUDED = ("PGA Tour", "DP World Tour", "LPGA", "Majors")

FINAL_ACTIONABLE_STATES = (
    "free_open_backfilled",
    "free_open_postevent_training_only",
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

OPEN_GOLF_API_URL = "https://courses.opengolfapi.org/"
OPEN_GOLF_TERMS_URL = "https://courses.opengolfapi.org/legal/terms"
OPEN_GOLF_GITHUB_URL = "https://github.com/OpenGolfAPI"
OPEN_GOLF_SCHEMA_URL = "https://opensourcegolf.com/open-course.html"

OXYLABS_GOLF_ALLOWED_DOMAINS = (
    "courses.opengolfapi.org",
    "*.opengolfapi.org",
    "opensourcegolf.com",
    "*.opensourcegolf.com",
    "github.com",
    "*.github.com",
    "raw.githubusercontent.com",
    "*.raw.githubusercontent.com",
    "wikidata.org",
    "*.wikidata.org",
    "wikipedia.org",
    "*.wikipedia.org",
    "pgatour.com",
    "*.pgatour.com",
    "europeantour.com",
    "*.europeantour.com",
    "lpga.com",
    "*.lpga.com",
    "masters.com",
    "*.masters.com",
    "usopen.com",
    "*.usopen.com",
    "theopen.com",
    "*.theopen.com",
    "owgr.com",
    "*.owgr.com",
    "datagolf.com",
    "*.datagolf.com",
    "espn.com",
    "*.espn.com",
    "kaggle.com",
    "*.kaggle.com",
    "sportsdata.io",
    "*.sportsdata.io",
    "datasportsgroup.com",
    "*.datasportsgroup.com",
)

OXYLABS_GOLF_ALLOWED_SOURCE_IDS = (
    "golf_open_course_data",
    "golf_wikidata_player_entities",
    "golf_wikipedia_tournament_tables",
    "golf_pga_tour_official_pages",
    "golf_dp_world_tour_official_pages",
    "golf_lpga_official_pages",
    "golf_major_championship_pages",
    "golf_owgr_rankings",
    "golf_datagolf_public_pages",
    "golf_pgatour_shotlink",
    "golf_espn_golf_pages",
    "golf_kaggle_catalog",
    "golf_golfastr_repo",
    "golf_pgatour_api_wrapper_repo",
    "golf_paid_tracking_vendor",
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
    allowed_domains = tuple(allowed_domains or OXYLABS_GOLF_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_GOLF_ALLOWED_SOURCE_IDS)
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
        "golf_open_course_data": OxylabsSourceSpec("golf_open_course_data", "OpenGolfAPI course dataset", "courses.opengolfapi.org", OPEN_GOLF_API_URL, "web_scraper_api", "open_course_dataset", "accepted_for_automated_normalized_backfill", "OpenGolfAPI publishes course data under ODbL with attribution/share-alike obligations."),
        "golf_wikidata_player_entities": OxylabsSourceSpec("golf_wikidata_player_entities", "Wikidata golfer entities", "wikidata.org", "https://www.wikidata.org/wiki/Wikidata:Main_Page", "web_scraper_api", "structured_open_metadata", "accepted_for_metadata_only", "Wikidata is metadata-only enrichment with attribution retained."),
        "golf_wikipedia_tournament_tables": OxylabsSourceSpec("golf_wikipedia_tournament_tables", "Wikipedia golf tournament tables", "wikipedia.org", "https://en.wikipedia.org/wiki/Men%27s_major_golf_championships", "web_scraper_api", "structured_open_metadata", "accepted_for_metadata_only", "Wikipedia tables remain supplemental metadata only with attribution retained."),
        "golf_pga_tour_official_pages": OxylabsSourceSpec("golf_pga_tour_official_pages", "PGA Tour official pages", "pgatour.com", "https://www.pgatour.com/", "web_scraper_api", "official_tour_page", "accepted_for_manual_import_only", "PGA Tour public pages remain manual-only unless exact automated access is approved."),
        "golf_dp_world_tour_official_pages": OxylabsSourceSpec("golf_dp_world_tour_official_pages", "DP World Tour official pages", "europeantour.com", "https://www.europeantour.com/dpworld-tour/", "web_scraper_api", "official_tour_page", "accepted_for_manual_import_only", "DP World Tour public pages remain manual-only under the policy floor."),
        "golf_lpga_official_pages": OxylabsSourceSpec("golf_lpga_official_pages", "LPGA official pages", "lpga.com", "https://www.lpga.com/", "web_scraper_api", "official_tour_page", "accepted_for_manual_import_only", "LPGA public pages remain manual-only under the policy floor."),
        "golf_major_championship_pages": OxylabsSourceSpec("golf_major_championship_pages", "Major championship official pages", "masters.com", "https://www.masters.com/", "web_scraper_api", "official_major_page", "accepted_for_manual_import_only", "Major championship pages and media guides remain manual-only unless exact terms approve automation."),
        "golf_owgr_rankings": OxylabsSourceSpec("golf_owgr_rankings", "Official World Golf Ranking pages", "owgr.com", "https://www.owgr.com/", "web_scraper_api", "ranking_page", "policy_blocked", "OWGR automated extraction is not approved in this pass."),
        "golf_datagolf_public_pages": OxylabsSourceSpec("golf_datagolf_public_pages", "Data Golf public pages", "datagolf.com", "https://datagolf.com/", "web_scraper_api", "analytics_page", "license_terms_unclear", "Data Golf requires exact licensed/API terms before automated use."),
        "golf_pgatour_shotlink": OxylabsSourceSpec("golf_pgatour_shotlink", "PGA Tour ShotLink", "pgatour.com", "https://www.pgatour.com/stats", "web_scraper_api", "shotlink_stats", "paid_subscription_required", "ShotLink-style shot-level data remains licensed/paid."),
        "golf_espn_golf_pages": OxylabsSourceSpec("golf_espn_golf_pages", "ESPN Golf pages", "espn.com", "https://www.espn.com/golf/", "web_scraper_api", "reference_site", "policy_blocked", "ESPN Golf pages were reviewed but not approved for automated extraction."),
        "golf_kaggle_catalog": OxylabsSourceSpec("golf_kaggle_catalog", "Kaggle golf dataset catalog", "kaggle.com", "https://www.kaggle.com/datasets?search=golf", "web_scraper_api", "dataset_catalog", "login_paywall_captcha_blocked", "Kaggle remains account-gated and not used for automated free/open backfill."),
        "golf_golfastr_repo": OxylabsSourceSpec("golf_golfastr_repo", "golfastr GitHub repository", "github.com", "https://github.com/cran/golfastr", "web_scraper_api", "community_wrapper_repo", "license_terms_unclear", "Wrapper package is public, but upstream ESPN/PGA rights remain unclear for normalized automated reuse."),
        "golf_pgatour_api_wrapper_repo": OxylabsSourceSpec("golf_pgatour_api_wrapper_repo", "pgatouR GitHub/docs", "github.com", "https://walrusquant.github.io/pgatouR/", "web_scraper_api", "community_api_wrapper_repo", "license_terms_unclear", "Wrapper documentation is public, but upstream PGA API rights remain unclear."),
        "golf_paid_tracking_vendor": OxylabsSourceSpec("golf_paid_tracking_vendor", "Licensed golf data vendor", "sportsdata.io", "https://sportsdata.io/developers/data-dictionary/golf", "web_scraper_api", "paid_vendor_page", "paid_subscription_required", "Tournament, player, ranking, and stat feeds remain paid/licensed for broad production use."),
    }


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    return source_spec_registry().get(str(lane.get("source_id") or "")) or source_spec_registry()["golf_open_course_data"]


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
    session_root = GOLF_DATA_ROOT / "backfill_sessions" / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    return session_id, session_root


def open_course_sample_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "courses": [
            {"course_id": "augusta-national", "course_name": "Augusta National Golf Club", "city": "Augusta", "region": "Georgia", "country": "USA", "par": 72, "yardage": 7555, "source_record_hash": stable_hash("augusta")},
            {"course_id": "st-andrews-old", "course_name": "The Old Course at St Andrews", "city": "St Andrews", "region": "Fife", "country": "Scotland", "par": 72, "yardage": 7313, "source_record_hash": stable_hash("standrews")},
            {"course_id": "pebble-beach", "course_name": "Pebble Beach Golf Links", "city": "Pebble Beach", "region": "California", "country": "USA", "par": 72, "yardage": 7075, "source_record_hash": stable_hash("pebble")},
        ],
        "scorecard": [
            {"course_id": "augusta-national", "hole": 1, "hole_par": 4, "hole_yardage": 445, "nine": "front"},
            {"course_id": "augusta-national", "hole": 2, "hole_par": 5, "hole_yardage": 575, "nine": "front"},
            {"course_id": "augusta-national", "hole": 12, "hole_par": 3, "hole_yardage": 155, "nine": "back"},
        ],
    }
