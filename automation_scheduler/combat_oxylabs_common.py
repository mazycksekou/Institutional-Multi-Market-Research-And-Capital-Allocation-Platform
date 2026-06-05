from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .oxylabs_residential_proxy_adapter import OxylabsResidentialProxyAdapter
from .oxylabs_web_scraper_api_adapter import OxylabsWebScraperApiAdapter
from .scheduler_config import sanitize_filename, utc_now_iso
from .source_policy_review_common import parse_csv_rows


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"
COMBAT_DATA_ROOT = Path("data") / "data_sources" / "combat_open_data"

RUN_MODE = "combat_final_mandatory_oxylabs_source_policy_free_open_exhaustion_backfill_finality"
COMBAT_TYPES_INCLUDED = ("UFC", "MMA", "Boxing")

FINAL_ACTIONABLE_STATES = (
    "free_open_backfilled",
    "free_open_postmatch_training_only",
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

OPEN_BOXING_REPO_URL = "https://github.com/edhwright/open-boxing/tree/main/src/db/data"
OPEN_BOXING_LICENSE_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/LICENSE.md"
OPEN_BOXING_README_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/README.md"
OPEN_BOXING_BOUTS_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/src/db/data/bouts.csv"
OPEN_BOXING_CHAMPIONS_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/src/db/data/champions.csv"
OPEN_BOXING_TITLES_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/src/db/data/titles.csv"
OPEN_BOXING_REIGNS_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/src/db/data/reigns.csv"
OPEN_BOXING_LOCATIONS_URL = "https://raw.githubusercontent.com/edhwright/open-boxing/main/src/db/data/locations.csv"
OPEN_BOXING_API_URL = "https://www.openboxing.org/api/"

OXYLABS_COMBAT_ALLOWED_DOMAINS = (
    "raw.githubusercontent.com",
    "*.raw.githubusercontent.com",
    "github.com",
    "*.github.com",
    "docs.github.com",
    "*.docs.github.com",
    "openboxing.org",
    "*.openboxing.org",
    "wikidata.org",
    "*.wikidata.org",
    "wikipedia.org",
    "*.wikipedia.org",
    "ufc.com",
    "*.ufc.com",
    "ufcstats.com",
    "*.ufcstats.com",
    "tapology.com",
    "*.tapology.com",
    "sherdog.com",
    "*.sherdog.com",
    "espn.com",
    "*.espn.com",
    "boxrec.com",
    "*.boxrec.com",
    "kaggle.com",
    "*.kaggle.com",
    "dca.ca.gov",
    "*.dca.ca.gov",
    "sportradar.com",
    "*.sportradar.com",
    "docs.sportradar.com",
    "*.docs.sportradar.com",
)

OXYLABS_COMBAT_ALLOWED_SOURCE_IDS = (
    "combat_open_boxing_data_repo",
    "combat_wikidata_fighter_entities",
    "combat_wikipedia_combat_entities",
    "combat_ufc_official_weighins",
    "combat_ufc_official_event_pages",
    "combat_commission_medical_records",
    "combat_ufcstats_round_stats",
    "combat_tapology_event_pages",
    "combat_sherdog_fighter_pages",
    "combat_espn_mma_pages",
    "combat_boxrec_records",
    "combat_kaggle_combat_catalog",
    "combat_ufc_stats_api_wrapper_repo",
    "combat_mma_data_scraper_repo",
    "combat_paid_tracking_vendor",
)

_SAMPLE_CONTEXT_CACHE: dict[str, Any] | None = None


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
    allowed_domains = tuple(allowed_domains or OXYLABS_COMBAT_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_COMBAT_ALLOWED_SOURCE_IDS)
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
        headers=headers,
        timeout=timeout,
    )
    try:
        payload = json.loads(response.get("text") or "")
    except Exception:
        payload = None
    return {
        **response,
        "json_ok": isinstance(payload, (dict, list)),
        "json_payload": payload if isinstance(payload, (dict, list)) else {},
    }


def source_spec_registry() -> dict[str, OxylabsSourceSpec]:
    return {
        "combat_open_boxing_data_repo": OxylabsSourceSpec(
            source_id="combat_open_boxing_data_repo",
            source_name="Open Boxing data repository",
            domain="github.com",
            url=OPEN_BOXING_REPO_URL,
            transport="web_scraper_api",
            source_type="open_csv_dataset",
            policy_status="accepted_for_automated_normalized_backfill",
            license_or_terms_note="Open Boxing exposes boxing data via a public GitHub repository and documents an MIT license.",
        ),
        "combat_wikidata_fighter_entities": OxylabsSourceSpec(
            source_id="combat_wikidata_fighter_entities",
            source_name="Wikidata combat sports fighter entities",
            domain="wikidata.org",
            url="https://www.wikidata.org/wiki/Wikidata:Main_Page",
            transport="web_scraper_api",
            source_type="structured_open_metadata",
            policy_status="accepted_for_metadata_only",
            license_or_terms_note="Use is limited to metadata-only enrichment with attribution retained.",
        ),
        "combat_wikipedia_combat_entities": OxylabsSourceSpec(
            source_id="combat_wikipedia_combat_entities",
            source_name="Wikipedia combat sports entity tables",
            domain="wikipedia.org",
            url="https://en.wikipedia.org/wiki/List_of_current_UFC_fighters",
            transport="web_scraper_api",
            source_type="structured_open_metadata",
            policy_status="accepted_for_metadata_only",
            license_or_terms_note="Use is limited to supplemental metadata with attribution retained.",
        ),
        "combat_ufc_official_weighins": OxylabsSourceSpec(
            source_id="combat_ufc_official_weighins",
            source_name="UFC official weigh-in and news pages",
            domain="ufc.com",
            url="https://www.ufc.com/events",
            transport="web_scraper_api",
            source_type="official_news_page",
            policy_status="accepted_for_manual_import_only",
            license_or_terms_note="Official UFC pages remain manual-only because UFC terms restrict automated systems and timestamp validation matters.",
        ),
        "combat_ufc_official_event_pages": OxylabsSourceSpec(
            source_id="combat_ufc_official_event_pages",
            source_name="UFC official event pages",
            domain="ufc.com",
            url="https://www.ufc.com/events",
            transport="web_scraper_api",
            source_type="official_event_page",
            policy_status="accepted_for_manual_import_only",
            license_or_terms_note="Official UFC event pages remain manual-only under the repo's policy floor.",
        ),
        "combat_commission_medical_records": OxylabsSourceSpec(
            source_id="combat_commission_medical_records",
            source_name="State athletic commission public records",
            domain="dca.ca.gov",
            url="https://www.dca.ca.gov/csac/",
            transport="web_scraper_api",
            source_type="official_commission_page",
            policy_status="accepted_for_manual_import_only",
            license_or_terms_note="Commission records can support timestamped manual imports, especially for suspensions and officiating context.",
        ),
        "combat_ufcstats_round_stats": OxylabsSourceSpec(
            source_id="combat_ufcstats_round_stats",
            source_name="UFC Stats event, fighter, and bout detail pages",
            domain="ufcstats.com",
            url="http://ufcstats.com/statistics/events/completed?page=all",
            transport="residential_proxy",
            source_type="official_stats_page",
            policy_status="policy_blocked",
            license_or_terms_note="Exact-path automated extraction from UFC-owned stats surfaces was not approved in this pass.",
        ),
        "combat_tapology_event_pages": OxylabsSourceSpec(
            source_id="combat_tapology_event_pages",
            source_name="Tapology event and fighter pages",
            domain="tapology.com",
            url="https://www.tapology.com/",
            transport="web_scraper_api",
            source_type="reference_site",
            policy_status="policy_blocked",
            license_or_terms_note="Tapology remains blocked until an exact path is explicitly approved after policy review.",
        ),
        "combat_sherdog_fighter_pages": OxylabsSourceSpec(
            source_id="combat_sherdog_fighter_pages",
            source_name="Sherdog fighter and event pages",
            domain="sherdog.com",
            url="https://www.sherdog.com/",
            transport="web_scraper_api",
            source_type="reference_site",
            policy_status="policy_blocked",
            license_or_terms_note="Sherdog remains blocked until an exact path is explicitly approved after policy review.",
        ),
        "combat_espn_mma_pages": OxylabsSourceSpec(
            source_id="combat_espn_mma_pages",
            source_name="ESPN MMA pages",
            domain="espn.com",
            url="https://www.espn.com/mma/",
            transport="web_scraper_api",
            source_type="reference_site",
            policy_status="policy_blocked",
            license_or_terms_note="ESPN MMA pages were reviewed but not approved for automated extraction in this pass.",
        ),
        "combat_boxrec_records": OxylabsSourceSpec(
            source_id="combat_boxrec_records",
            source_name="BoxRec record pages",
            domain="boxrec.com",
            url="https://boxrec.com/",
            transport="web_scraper_api",
            source_type="record_database",
            policy_status="login_paywall_captcha_blocked",
            license_or_terms_note="BoxRec is treated as login/terms blocked for automated use in this pass.",
        ),
        "combat_kaggle_combat_catalog": OxylabsSourceSpec(
            source_id="combat_kaggle_combat_catalog",
            source_name="Kaggle combat dataset catalog",
            domain="kaggle.com",
            url="https://www.kaggle.com/datasets?search=ufc%20mma%20boxing",
            transport="web_scraper_api",
            source_type="dataset_catalog_page",
            policy_status="login_paywall_captcha_blocked",
            license_or_terms_note="Kaggle catalog access remains account-gated and not suitable as a compliant free/open automated source.",
        ),
        "combat_ufc_stats_api_wrapper_repo": OxylabsSourceSpec(
            source_id="combat_ufc_stats_api_wrapper_repo",
            source_name="GitHub UFC stats API wrapper repo",
            domain="github.com",
            url="https://github.com/aristotle-malichetty/ufc-stats-api",
            transport="web_scraper_api",
            source_type="community_api_wrapper_repo",
            policy_status="license_terms_unclear",
            license_or_terms_note="The wrapper repo is public, but downstream rights remain unclear because it derives from UFC-owned stats surfaces.",
        ),
        "combat_mma_data_scraper_repo": OxylabsSourceSpec(
            source_id="combat_mma_data_scraper_repo",
            source_name="GitHub MMA data scraper bundle repo",
            domain="github.com",
            url="https://github.com/Renaissanc3Man/MMA-Data",
            transport="web_scraper_api",
            source_type="community_scraper_repo",
            policy_status="license_terms_unclear",
            license_or_terms_note="The public repo combines scraped UFC, Sherdog, and Wikipedia inputs, so downstream rights remain unclear.",
        ),
        "combat_paid_tracking_vendor": OxylabsSourceSpec(
            source_id="combat_paid_tracking_vendor",
            source_name="Paid MMA/boxing tracking vendor page",
            domain="sportradar.com",
            url="https://sportradar.com/sports/mma/",
            transport="web_scraper_api",
            source_type="paid_vendor_page",
            policy_status="paid_subscription_required",
            license_or_terms_note="Richer tracking, round microdata, and punch-level context remain paid/licensed.",
        ),
    }


def source_spec_for(source_id: str) -> OxylabsSourceSpec | None:
    return source_spec_registry().get(source_id)


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    source_id = str(lane.get("source_id") or "")
    source_spec = source_spec_for(source_id)
    if source_spec is not None:
        return source_spec
    return source_spec_registry()["combat_ufcstats_round_stats"]


def lane_final_state(lane: dict[str, Any], *, backfill_written: bool, hard_blocked: bool = False, policy_final_state: str | None = None) -> str:
    if policy_final_state in FINAL_ACTIONABLE_STATES:
        if policy_final_state == "free_open_backfilled" and hard_blocked:
            return "free_open_loader_ready_hard_blocked_from_backfill"
        if policy_final_state == "free_open_backfilled" and not backfill_written:
            return "free_open_loader_ready_hard_blocked_from_backfill"
        return policy_final_state
    category = str(lane.get("free_or_paid_category") or "")
    if hard_blocked:
        return "free_open_loader_ready_hard_blocked_from_backfill"
    if category in {"free_open_populated", "free_open_partial", "free_open_loader_needed", "free_open_sample_required"} and backfill_written:
        return "free_open_backfilled"
    if category == "paid_data_subscription_required":
        return "paid_subscription_required"
    if category == "free_open_manual_import_needed":
        return "manual_import_required"
    if category == "policy_blocked":
        return "policy_blocked"
    if category == "robots_blocked":
        return "robots_blocked"
    if category == "terms_blocked":
        return "terms_blocked"
    if category == "login_paywall_captcha_blocked":
        return "login_paywall_captcha_blocked"
    if category == "license_terms_unclear":
        return "license_terms_unclear"
    if category == "obsolete_or_duplicate":
        return "obsolete_or_duplicate"
    return "unavailable_after_exhaustive_free_search"


def stable_bout_key(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "bout_id": row.get("bout_id"),
            "date": row.get("date"),
            "boxer_a_champion_id": row.get("boxer_a_champion_id"),
            "boxer_b_champion_id": row.get("boxer_b_champion_id"),
        }
    )


def data_session_root(prefix: str) -> tuple[str, Path]:
    session_id = sanitize_filename(f"{prefix}_{current_utc().replace(':', '').replace('-', '')}_{stable_hash(prefix)[:8]}")
    session_root = COMBAT_DATA_ROOT / "backfill_sessions" / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    return session_id, session_root


def discover_combat_sample_context() -> dict[str, Any]:
    global _SAMPLE_CONTEXT_CACHE
    if _SAMPLE_CONTEXT_CACHE is not None:
        return dict(_SAMPLE_CONTEXT_CACHE)
    bundles = {}
    for name, url in {
        "bouts": OPEN_BOXING_BOUTS_URL,
        "champions": OPEN_BOXING_CHAMPIONS_URL,
        "titles": OPEN_BOXING_TITLES_URL,
        "reigns": OPEN_BOXING_REIGNS_URL,
        "locations": OPEN_BOXING_LOCATIONS_URL,
    }.items():
        response = fetch_public_page_text(
            source_id="combat_open_boxing_data_repo",
            domain="raw.githubusercontent.com",
            url=url,
            transport="residential_proxy",
            headers={"Accept": "text/csv,text/plain,*/*"},
            timeout=45,
        )
        bundles[f"{name}_response"] = response
        bundles[f"{name}_rows"] = parse_csv_rows(response.get("text") or "", max_records=40)
    context = {
        "ok": all(bool(bundles.get(f"{name}_rows")) for name in ("bouts", "champions", "titles", "reigns", "locations")),
        **bundles,
        "sample_bout": (bundles.get("bouts_rows") or [{}])[0],
        "sample_champion": (bundles.get("champions_rows") or [{}])[0],
        "sample_title": (bundles.get("titles_rows") or [{}])[0],
        "sample_reign": (bundles.get("reigns_rows") or [{}])[0],
        "sample_location": (bundles.get("locations_rows") or [{}])[0],
    }
    _SAMPLE_CONTEXT_CACHE = context
    return dict(context)
