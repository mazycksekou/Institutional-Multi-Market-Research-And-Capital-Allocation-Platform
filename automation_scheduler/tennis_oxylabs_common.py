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
TENNIS_DATA_ROOT = Path("data") / "data_sources" / "tennis_open_data"

RUN_MODE = "tennis_final_mandatory_oxylabs_source_policy_free_open_exhaustion_backfill_finality"
TOURS_INCLUDED = ("ATP", "WTA", "Grand Slam men", "Grand Slam women")

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

OXYLABS_TENNIS_ALLOWED_DOMAINS = (
    "raw.githubusercontent.com",
    "*.raw.githubusercontent.com",
    "github.com",
    "*.github.com",
    "*.githubusercontent.com",
    "wikidata.org",
    "*.wikidata.org",
    "wikipedia.org",
    "*.wikipedia.org",
    "atptour.com",
    "*.atptour.com",
    "wtatennis.com",
    "*.wtatennis.com",
    "wimbledon.com",
    "*.wimbledon.com",
    "ausopen.com",
    "*.ausopen.com",
    "rolandgarros.com",
    "*.rolandgarros.com",
    "usopen.org",
    "*.usopen.org",
    "itftennis.com",
    "*.itftennis.com",
    "tennis-data.co.uk",
    "*.tennis-data.co.uk",
    "kaggle.com",
    "*.kaggle.com",
    "tennisabstract.com",
    "*.tennisabstract.com",
    "ultimatetennisstatistics.com",
    "*.ultimatetennisstatistics.com",
    "statsperform.com",
    "*.statsperform.com",
    "sportradar.com",
    "*.sportradar.com",
)

OXYLABS_TENNIS_ALLOWED_SOURCE_IDS = (
    "tennis_jeff_sackmann_atp_matches",
    "tennis_jeff_sackmann_wta_matches",
    "tennis_match_charting_project_repo",
    "tennis_wikidata_player_entities",
    "tennis_wikipedia_tennis_supplemental",
    "tennis_atp_official_rankings",
    "tennis_wta_official_rankings",
    "tennis_grand_slam_draw_pages",
    "tennis_itf_withdrawal_news",
    "tennis_tennis_data_uk_history",
    "tennis_kaggle_dataset_catalog",
    "tennis_tennis_abstract",
    "tennis_ultimate_tennis_statistics",
    "tennis_paid_tracking_vendor",
    "tennis_github_duplicate_mirror",
)

ATP_MATCHES_2025_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2025.csv"
WTA_MATCHES_2025_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2025.csv"
ATP_README_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/README.md"
WTA_README_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/README.md"
MATCH_CHARTING_README_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/README.md"

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
    allowed_domains = tuple(allowed_domains or OXYLABS_TENNIS_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_TENNIS_ALLOWED_SOURCE_IDS)
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
        "tennis_jeff_sackmann_atp_matches": OxylabsSourceSpec(
            source_id="tennis_jeff_sackmann_atp_matches",
            source_name="Jeff Sackmann ATP Tennis Rankings, Results, and Stats",
            domain="raw.githubusercontent.com",
            url=ATP_MATCHES_2025_URL,
            transport="residential_proxy",
            source_type="open_csv_dataset",
            policy_status="license_terms_unclear",
            license_or_terms_note="Repo README advertises CC BY-NC-SA / non-commercial-only use; legal review required before automated backfill.",
        ),
        "tennis_jeff_sackmann_wta_matches": OxylabsSourceSpec(
            source_id="tennis_jeff_sackmann_wta_matches",
            source_name="Jeff Sackmann WTA Tennis Rankings, Results, and Stats",
            domain="raw.githubusercontent.com",
            url=WTA_MATCHES_2025_URL,
            transport="residential_proxy",
            source_type="open_csv_dataset",
            policy_status="license_terms_unclear",
            license_or_terms_note="Repo README advertises CC BY-NC-SA / non-commercial-only use; legal review required before automated backfill.",
        ),
        "tennis_match_charting_project_repo": OxylabsSourceSpec(
            source_id="tennis_match_charting_project_repo",
            source_name="Match Charting Project",
            domain="github.com",
            url="https://github.com/JeffSackmann/tennis_MatchChartingProject",
            transport="web_scraper_api",
            source_type="open_github_docs_page",
            policy_status="license_terms_unclear",
            license_or_terms_note="Detailed charting repo is useful, but project-license scope and downstream commercial use need review.",
        ),
        "tennis_wikidata_player_entities": OxylabsSourceSpec(
            source_id="tennis_wikidata_player_entities",
            source_name="Wikidata Tennis Entities",
            domain="wikidata.org",
            url="https://www.wikidata.org/wiki/Wikidata:Main_Page",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="accepted_for_metadata_only",
            license_or_terms_note="Use limited to metadata-level entity supplementation with attribution retained.",
        ),
        "tennis_wikipedia_tennis_supplemental": OxylabsSourceSpec(
            source_id="tennis_wikipedia_tennis_supplemental",
            source_name="Wikipedia Tennis Supplemental Tables",
            domain="wikipedia.org",
            url="https://en.wikipedia.org/wiki/ATP_Tour",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="accepted_for_metadata_only",
            license_or_terms_note="Use limited to metadata-level supplementation with attribution preserved.",
        ),
        "tennis_atp_official_rankings": OxylabsSourceSpec(
            source_id="tennis_atp_official_rankings",
            source_name="ATP Tour Official Rankings and Stats Pages",
            domain="atptour.com",
            url="https://www.atptour.com/en/rankings/singles",
            transport="web_scraper_api",
            source_type="official_rankings_page",
            policy_status="policy_blocked",
            license_or_terms_note="ATP terms reserve rankings, scores, and statistics content for ATP-controlled use and personal non-commercial copying only.",
        ),
        "tennis_wta_official_rankings": OxylabsSourceSpec(
            source_id="tennis_wta_official_rankings",
            source_name="WTA Official Rankings and Stats Pages",
            domain="wtatennis.com",
            url="https://www.wtatennis.com/rankings/singles",
            transport="web_scraper_api",
            source_type="official_rankings_page",
            policy_status="policy_blocked",
            license_or_terms_note="WTA terms cover WTA-controlled sites broadly; automated structured extraction is not approved here.",
        ),
        "tennis_grand_slam_draw_pages": OxylabsSourceSpec(
            source_id="tennis_grand_slam_draw_pages",
            source_name="Official Grand Slam Draw and Event Pages",
            domain="wimbledon.com",
            url="https://www.wimbledon.com/en_GB/scores/draws/index.html",
            transport="web_scraper_api",
            source_type="official_event_page",
            policy_status="accepted_for_manual_import_only",
            license_or_terms_note="Public event pages are suitable for timestamped manual capture only in this pass.",
        ),
        "tennis_itf_withdrawal_news": OxylabsSourceSpec(
            source_id="tennis_itf_withdrawal_news",
            source_name="ITF / Tournament Withdrawal and News Pages",
            domain="itftennis.com",
            url="https://www.itftennis.com/en/news-and-media/articles/",
            transport="web_scraper_api",
            source_type="official_news_page",
            policy_status="accepted_for_manual_import_only",
            license_or_terms_note="Availability and withdrawal news remains manual-only because timestamping and context review are required.",
        ),
        "tennis_tennis_data_uk_history": OxylabsSourceSpec(
            source_id="tennis_tennis_data_uk_history",
            source_name="tennis-data.co.uk Historical Files",
            domain="tennis-data.co.uk",
            url="https://www.tennis-data.co.uk/2025/2025.php",
            transport="web_scraper_api",
            source_type="open_csv_docs_page",
            policy_status="license_terms_unclear",
            license_or_terms_note="Historical betting-data package is visible, but reuse/license scope for this project needs review.",
        ),
        "tennis_kaggle_dataset_catalog": OxylabsSourceSpec(
            source_id="tennis_kaggle_dataset_catalog",
            source_name="Kaggle Tennis Dataset Catalog",
            domain="kaggle.com",
            url="https://www.kaggle.com/datasets?search=tennis",
            transport="web_scraper_api",
            source_type="dataset_catalog_page",
            policy_status="login_paywall_captcha_blocked",
            license_or_terms_note="Dataset catalog is account-gated and cannot be treated as a compliant free/open automated source.",
        ),
        "tennis_tennis_abstract": OxylabsSourceSpec(
            source_id="tennis_tennis_abstract",
            source_name="Tennis Abstract",
            domain="tennisabstract.com",
            url="https://www.tennisabstract.com/",
            transport="web_scraper_api",
            source_type="restricted_reference_site",
            policy_status="policy_blocked",
            license_or_terms_note="User instruction requires exact-path policy approval before any use; no compliant automated path was approved in this pass.",
        ),
        "tennis_ultimate_tennis_statistics": OxylabsSourceSpec(
            source_id="tennis_ultimate_tennis_statistics",
            source_name="Ultimate Tennis Statistics",
            domain="ultimatetennisstatistics.com",
            url="https://www.ultimatetennisstatistics.com/",
            transport="web_scraper_api",
            source_type="restricted_reference_site",
            policy_status="policy_blocked",
            license_or_terms_note="User instruction requires exact-path approval first; no compliant path was approved in this pass.",
        ),
        "tennis_paid_tracking_vendor": OxylabsSourceSpec(
            source_id="tennis_paid_tracking_vendor",
            source_name="Paid Tracking / Point-Level Vendor Page",
            domain="statsperform.com",
            url="https://www.statsperform.com/our-data/",
            transport="web_scraper_api",
            source_type="paid_vendor_page",
            policy_status="paid_subscription_required",
            license_or_terms_note="Broader point-tracking and shot-pattern context remains a paid vendor lane.",
        ),
        "tennis_github_duplicate_mirror": OxylabsSourceSpec(
            source_id="tennis_github_duplicate_mirror",
            source_name="GitHub Duplicate Mirror of Jeff Sackmann Tennis Data",
            domain="github.com",
            url="https://github.com/mare-imbrium/tennis-atp",
            transport="web_scraper_api",
            source_type="community_duplicate_source",
            policy_status="obsolete_or_duplicate",
            license_or_terms_note="Mirror duplicates Jeff Sackmann’s upstream data and adds no independent compliance advantage.",
        ),
    }


def source_spec_for(source_id: str) -> OxylabsSourceSpec | None:
    return source_spec_registry().get(source_id)


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    source_id = str(lane.get("source_id") or "")
    source_spec = source_spec_for(source_id)
    if source_spec is not None:
        return source_spec
    return source_spec_registry()["tennis_atp_official_rankings"]


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


def stable_match_key(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "tourney_id": row.get("tourney_id"),
            "tourney_date": row.get("tourney_date"),
            "match_num": row.get("match_num"),
            "winner_id": row.get("winner_id"),
            "loser_id": row.get("loser_id"),
        }
    )


def data_session_root(prefix: str) -> tuple[str, Path]:
    session_id = sanitize_filename(f"{prefix}_{current_utc().replace(':', '').replace('-', '')}_{stable_hash(prefix)[:8]}")
    session_root = TENNIS_DATA_ROOT / "backfill_sessions" / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    return session_id, session_root


def discover_tennis_sample_context() -> dict[str, Any]:
    global _SAMPLE_CONTEXT_CACHE
    if _SAMPLE_CONTEXT_CACHE is not None:
        return dict(_SAMPLE_CONTEXT_CACHE)
    atp_response = fetch_public_page_text(
        source_id="tennis_jeff_sackmann_atp_matches",
        domain="raw.githubusercontent.com",
        url=ATP_MATCHES_2025_URL,
        transport="residential_proxy",
        headers={"Accept": "text/csv,text/plain,*/*"},
        timeout=45,
    )
    wta_response = fetch_public_page_text(
        source_id="tennis_jeff_sackmann_wta_matches",
        domain="raw.githubusercontent.com",
        url=WTA_MATCHES_2025_URL,
        transport="residential_proxy",
        headers={"Accept": "text/csv,text/plain,*/*"},
        timeout=45,
    )
    atp_rows = parse_csv_rows(atp_response.get("text") or "", max_records=30)
    wta_rows = parse_csv_rows(wta_response.get("text") or "", max_records=30)
    context = {
        "ok": bool(atp_response.get("ok") and wta_response.get("ok") and atp_rows and wta_rows),
        "atp_response": atp_response,
        "wta_response": wta_response,
        "atp_rows": atp_rows,
        "wta_rows": wta_rows,
        "sample_atp_match": atp_rows[0] if atp_rows else {},
        "sample_wta_match": wta_rows[0] if wta_rows else {},
        "sample_atp_match_key": stable_match_key(atp_rows[0]) if atp_rows else "",
        "sample_wta_match_key": stable_match_key(wta_rows[0]) if wta_rows else "",
    }
    _SAMPLE_CONTEXT_CACHE = context
    return dict(context)
