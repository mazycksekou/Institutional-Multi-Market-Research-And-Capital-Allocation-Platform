from __future__ import annotations

import csv
import hashlib
import io
import json
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .basketball_free_vs_paid_readiness import SPORTS, basketball_lane_catalog
from .oxylabs_residential_proxy_adapter import OxylabsResidentialProxyAdapter
from .oxylabs_web_scraper_api_adapter import OxylabsWebScraperApiAdapter
from .scheduler_config import utc_now_iso


REPORT_ROOT = Path("reports")
BASKETBALL_DATA_ROOT = Path("data") / "data_sources" / "basketball_open_data"

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

OXYLABS_BASKETBALL_ALLOWED_DOMAINS = (
    "github.com",
    "*.github.com",
    "*.githubusercontent.com",
    "nba.com",
    "*.nba.com",
    "wnba.com",
    "*.wnba.com",
    "stats.wnba.com",
    "ncaa.com",
    "*.ncaa.com",
    "wikidata.org",
    "*.wikidata.org",
    "wikipedia.org",
    "*.wikipedia.org",
    "sportsdataverse.org",
    "*.sportsdataverse.org",
    "developer.sportradar.com",
    "developer.geniussports.com",
    "statsperform.com",
    "*.statsperform.com",
    "second-spectrum.com",
    "*.second-spectrum.com",
)

OXYLABS_BASKETBALL_ALLOWED_SOURCE_IDS = (
    "basketball_release_assets",
    "basketball_release_page",
    "basketball_docs_page",
    "basketball_wnba_stats_page",
    "basketball_ncaa_net_page",
    "basketball_nba_api_docs",
    "basketball_sportradar_docs",
    "basketball_genius_sports_docs",
    "basketball_statsperform_docs",
    "basketball_second_spectrum_docs",
    "basketball_wikidata_supplemental",
    "basketball_wikipedia_supplemental",
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
    accepted: bool = True


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
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
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


def release_asset_url(tag: str, asset_name: str) -> str:
    return f"https://github.com/sportsdataverse/sportsdataverse-data/releases/download/{tag}/{asset_name}"


def release_page_url(tag: str | None = None) -> str:
    if tag:
        return f"https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/{tag}"
    return "https://github.com/sportsdataverse/sportsdataverse-data/releases"


def lane_lookup() -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["sport"], row["lane_name"]): row for row in basketball_lane_catalog()}


def sport_lanes(sport: str) -> list[dict[str, Any]]:
    return [row for row in basketball_lane_catalog() if row["sport"] == sport]


def unresolved_lanes() -> list[dict[str, Any]]:
    return [
        row
        for row in basketball_lane_catalog()
        if row["free_or_paid_category"] not in {"free_open_populated", "free_open_partial", "obsolete_or_duplicate"}
    ]


def loader_ready_lanes() -> list[dict[str, Any]]:
    return [
        row
        for row in basketball_lane_catalog()
        if row["loader_exists"] and row["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}
    ]


def partial_lanes() -> list[dict[str, Any]]:
    return [row for row in basketball_lane_catalog() if row["free_or_paid_category"] == "free_open_partial"]


def parse_csv_text(text: str, *, max_records: int | None = None) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(text))
    records: list[dict[str, Any]] = []
    for row in reader:
        if not row:
            continue
        records.append({str(key): value for key, value in row.items()})
        if max_records is not None and len(records) >= max_records:
            break
    return {
        "fieldnames": list(reader.fieldnames or []),
        "records": records,
        "record_count": len(records),
    }


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
            content = result.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content)
                continue
            html = result.get("html")
            if isinstance(html, str) and html.strip():
                parts.append(html)
                continue
            body = result.get("body")
            if isinstance(body, str) and body.strip():
                parts.append(body)
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
    allowed_domains = tuple(allowed_domains or OXYLABS_BASKETBALL_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_BASKETBALL_ALLOWED_SOURCE_IDS)
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
        return {
            "ok": bool(response.get("ok")),
            "status": response.get("status"),
            "blocked_reason": response.get("blocked_reason"),
            "text": response.get("text") or "",
            "transport": transport,
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "source_id": source_id,
            "domain": domain,
            "url": url,
        }
    if transport == "web_scraper_api":
        adapter = OxylabsWebScraperApiAdapter(
            source_id=source_id,
            domain=domain,
            allow_oxylabs=True,
            allow_paid_retrieval=True,
            allowed_source_ids=allowed_source_ids,
            allowed_domains=allowed_domains,
        )
        response = adapter.fetch_text(url, timeout=timeout)
        text = response.get("text") or ""
        return {
            "ok": bool(response.get("ok")),
            "status": response.get("status"),
            "blocked_reason": response.get("blocked_reason"),
            "text": text,
            "transport": transport,
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "source_id": source_id,
            "domain": domain,
            "url": url,
        }
    return {
        "ok": False,
        "status": "blocked",
        "blocked_reason": "unsupported_transport",
        "text": "",
        "transport": transport,
        "raw_html_persisted": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "source_id": source_id,
        "domain": domain,
        "url": url,
    }


def fetch_release_asset_rows(
    *,
    tag: str,
    asset_name: str,
    max_bytes: int = 250_000,
    max_records: int = 10,
    source_id: str = "basketball_release_assets",
    transport: str = "residential_proxy",
) -> dict[str, Any]:
    url = release_asset_url(tag, asset_name)
    response = fetch_text_with_transport(
        transport=transport,
        source_id=source_id,
        domain="github.com",
        url=url,
        allowed_domains=("github.com", "*.github.com", "*.githubusercontent.com"),
        headers={
            "Accept": "text/csv,*/*",
            "Range": f"bytes=0-{max_bytes - 1}",
        },
        timeout=60,
    )
    text = response.get("text") or ""
    parsed = parse_csv_text(text, max_records=max_records) if response.get("ok") else {"fieldnames": [], "records": [], "record_count": 0}
    return {
        **response,
        "url": url,
        "source_url_hash": url_hash(url),
        "fieldnames": parsed.get("fieldnames", []),
        "records": parsed.get("records", []),
        "record_count": parsed.get("record_count", 0),
        "bytes_read": len(text.encode("utf-8", errors="ignore")),
    }


def fetch_public_page_text(
    *,
    source_id: str,
    domain: str,
    url: str,
    transport: str = "web_scraper_api",
    allowed_domains: Iterable[str] | None = None,
    allowed_source_ids: Iterable[str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    response = fetch_text_with_transport(
        transport=transport,
        source_id=source_id,
        domain=domain,
        url=url,
        allowed_domains=allowed_domains,
        allowed_source_ids=allowed_source_ids,
        timeout=timeout,
    )
    text = extract_web_scraper_content(response.get("text") or "") if response.get("ok") else ""
    return {
        **response,
        "url": url,
        "source_url_hash": url_hash(url),
        "text": text,
        "text_length": len(text),
    }


def source_spec_registry() -> dict[str, OxylabsSourceSpec]:
    return {
        "basketball_release_assets": OxylabsSourceSpec(
            source_id="basketball_release_assets",
            source_name="SportsDataverse release assets",
            domain="github.com",
            url=release_page_url(),
            transport="residential_proxy",
            source_type="open_release_asset",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public GitHub release assets; transient in-memory extraction only.",
        ),
        "basketball_release_page": OxylabsSourceSpec(
            source_id="basketball_release_page",
            source_name="SportsDataverse release page",
            domain="github.com",
            url=release_page_url(),
            transport="web_scraper_api",
            source_type="public_release_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public release page used for duplicate discovery and asset confirmation.",
        ),
        "basketball_docs_page": OxylabsSourceSpec(
            source_id="basketball_docs_page",
            source_name="hoopR or wehoop docs",
            domain="github.com",
            url="https://github.com/sportsdataverse/hoopR",
            transport="web_scraper_api",
            source_type="public_docs_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public docs used for path confirmation and endpoint terminology only.",
        ),
        "basketball_nba_api_docs": OxylabsSourceSpec(
            source_id="basketball_nba_api_docs",
            source_name="nba_api docs",
            domain="github.com",
            url="https://github.com/swar/nba_api",
            transport="web_scraper_api",
            source_type="public_docs_page",
            policy_status="license_terms_unclear",
            license_or_terms_note="Public docs page only; direct endpoint access remains path/terms review gated.",
        ),
        "basketball_wnba_stats_page": OxylabsSourceSpec(
            source_id="basketball_wnba_stats_page",
            source_name="WNBA Stats",
            domain="stats.wnba.com",
            url="https://stats.wnba.com/",
            transport="web_scraper_api",
            source_type="public_stats_page",
            policy_status="license_terms_unclear",
            license_or_terms_note="Public landing page only; direct endpoint use remains path review gated.",
        ),
        "basketball_ncaa_net_page": OxylabsSourceSpec(
            source_id="basketball_ncaa_net_page",
            source_name="NCAA NET rankings page",
            domain="ncaa.com",
            url="https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings",
            transport="web_scraper_api",
            source_type="public_table_page",
            policy_status="manual_import_only",
            license_or_terms_note="Public table is suitable for manual review/import; automation remains conservative.",
        ),
        "basketball_sportradar_docs": OxylabsSourceSpec(
            source_id="basketball_sportradar_docs",
            source_name="Sportradar basketball docs",
            domain="developer.sportradar.com",
            url="https://developer.sportradar.com/basketball",
            transport="web_scraper_api",
            source_type="paid_official_data_api",
            policy_status="paid_subscription_required",
            license_or_terms_note="Paid/official feed candidate; used only to confirm availability and scope.",
        ),
        "basketball_genius_sports_docs": OxylabsSourceSpec(
            source_id="basketball_genius_sports_docs",
            source_name="Genius Sports docs",
            domain="developer.geniussports.com",
            url="https://developer.geniussports.com/",
            transport="web_scraper_api",
            source_type="paid_official_data_api",
            policy_status="paid_subscription_required",
            license_or_terms_note="Paid/official feed candidate; used only to confirm availability and scope.",
        ),
        "basketball_statsperform_docs": OxylabsSourceSpec(
            source_id="basketball_statsperform_docs",
            source_name="Stats Perform public site",
            domain="statsperform.com",
            url="https://www.statsperform.com/",
            transport="web_scraper_api",
            source_type="paid_or_marketing_page",
            policy_status="paid_subscription_required",
            license_or_terms_note="Public marketing page only; the actual feed requires a paid subscription.",
        ),
        "basketball_second_spectrum_docs": OxylabsSourceSpec(
            source_id="basketball_second_spectrum_docs",
            source_name="Second Spectrum public site",
            domain="second-spectrum.com",
            url="https://www.second-spectrum.com/",
            transport="web_scraper_api",
            source_type="paid_tracking_vendor",
            policy_status="paid_subscription_required",
            license_or_terms_note="Public marketing page only; tracking feed remains licensed/paid.",
        ),
        "basketball_wikidata_supplemental": OxylabsSourceSpec(
            source_id="basketball_wikidata_supplemental",
            source_name="Wikidata",
            domain="wikidata.org",
            url="https://www.wikidata.org/",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="supplemental_only",
            license_or_terms_note="Supplemental entity metadata only; not a primary performance-stat source.",
        ),
        "basketball_wikipedia_supplemental": OxylabsSourceSpec(
            source_id="basketball_wikipedia_supplemental",
            source_name="Wikipedia",
            domain="wikipedia.org",
            url="https://www.wikipedia.org/",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="supplemental_only",
            license_or_terms_note="Supplemental only; not used as a primary statistics source.",
        ),
    }


def source_spec_for(source_id: str) -> OxylabsSourceSpec | None:
    return source_spec_registry().get(source_id)


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    category = str(lane.get("free_or_paid_category") or "")
    lane_name = str(lane.get("lane_name") or "")
    sport = str(lane.get("sport") or "")
    if category in {"free_open_populated", "free_open_partial"}:
        return source_spec_registry()["basketball_release_assets"]
    if category == "license_terms_unclear" and lane_name == "lineup_on_off" and sport == "basketball_nba":
        return source_spec_registry()["basketball_nba_api_docs"]
    if category == "free_open_manual_import_needed":
        if lane_name == "strength_of_schedule_context":
            return source_spec_registry()["basketball_ncaa_net_page"]
        return source_spec_registry()["basketball_wnba_stats_page"]
    if category == "paid_data_subscription_required":
        if lane_name == "injuries_availability":
            return source_spec_registry()["basketball_sportradar_docs"]
        if lane_name == "transaction_availability_volatility":
            return source_spec_registry()["basketball_statsperform_docs"]
        if lane_name == "optical_tracking_player_location":
            return source_spec_registry()["basketball_second_spectrum_docs"]
        return source_spec_registry()["basketball_genius_sports_docs"]
    if category in {"blocked_reference_or_restricted_source", "policy_blocked"}:
        return source_spec_registry()["basketball_docs_page"]
    if category == "obsolete_or_duplicate":
        return source_spec_registry()["basketball_release_page"]
    return source_spec_registry()["basketball_release_page"]


def lane_final_state(lane: dict[str, Any], *, backfill_written: bool, hard_blocked: bool = False) -> str:
    category = str(lane.get("free_or_paid_category") or "")
    if hard_blocked:
        if category in {"blocked_reference_or_restricted_source", "policy_blocked"}:
            return "policy_blocked"
        return "free_open_loader_ready_hard_blocked_from_backfill"
    if category in {"free_open_populated", "free_open_partial"} and backfill_written:
        return "free_open_backfilled"
    if category == "paid_data_subscription_required":
        return "paid_subscription_required"
    if category == "free_open_manual_import_needed":
        return "manual_import_required"
    if category in {"blocked_reference_or_restricted_source", "policy_blocked"}:
        return "policy_blocked"
    if category == "license_terms_unclear":
        return "license_terms_unclear"
    if category == "obsolete_or_duplicate":
        return "obsolete_or_duplicate"
    return "unavailable_after_exhaustive_free_search"


def current_utc() -> str:
    return utc_now_iso()
