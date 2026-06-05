from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .oxylabs_residential_proxy_adapter import OxylabsResidentialProxyAdapter
from .oxylabs_web_scraper_api_adapter import OxylabsWebScraperApiAdapter
from .scheduler_config import utc_now_iso


REPORT_ROOT = Path("reports")
SOCCER_DATA_ROOT = Path("data") / "data_sources" / "soccer_open_data"
SOCCER_FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/2324/D1.csv"
SOCCER_STATSBOMB_COMPETITIONS_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json"
SOCCER_STATSBOMB_MATCHES_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/9/281.json"
SOCCER_OPENFOOTBALL_BUNDESLIGA_URL = "https://raw.githubusercontent.com/openfootball/deutschland/master/2023-24/1-bundesliga.txt"

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

OXYLABS_SOCCER_ALLOWED_DOMAINS = (
    "football-data.co.uk",
    "*.football-data.co.uk",
    "github.com",
    "*.github.com",
    "raw.githubusercontent.com",
    "*.githubusercontent.com",
    "bundesliga.com",
    "*.bundesliga.com",
    "statsbomb.com",
    "*.statsbomb.com",
    "understat.com",
    "*.understat.com",
    "wikidata.org",
    "*.wikidata.org",
    "wikipedia.org",
    "*.wikipedia.org",
)

OXYLABS_SOCCER_ALLOWED_SOURCE_IDS = (
    "soccer_football_data_csv",
    "soccer_football_data_docs",
    "soccer_statsbomb_open_data",
    "soccer_statsbomb_open_repo",
    "soccer_openfootball_repo",
    "soccer_official_league_page",
    "soccer_understat_public_page",
    "soccer_statsbomb_paid_vendor_page",
    "soccer_wikidata_supplemental",
    "soccer_wikipedia_supplemental",
)

_FETCH_CACHE: dict[str, dict[str, Any]] = {}
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
    allowed_domains = tuple(allowed_domains or OXYLABS_SOCCER_ALLOWED_DOMAINS)
    allowed_source_ids = tuple(allowed_source_ids or OXYLABS_SOCCER_ALLOWED_SOURCE_IDS)
    cache_key = stable_hash(
        {
            "transport": transport,
            "source_id": source_id,
            "domain": domain,
            "url": url,
            "allowed_domains": allowed_domains,
            "allowed_source_ids": allowed_source_ids,
            "headers": headers or {},
            "timeout": timeout,
        }
    )
    cached = _FETCH_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)
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
    payload = {
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
    _FETCH_CACHE[cache_key] = payload
    return dict(payload)


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
        headers=headers or {"Accept": "application/json,text/plain,*/*"},
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


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def source_spec_registry() -> dict[str, OxylabsSourceSpec]:
    return {
        "soccer_football_data_csv": OxylabsSourceSpec(
            source_id="soccer_football_data_csv",
            source_name="football-data.co.uk Bundesliga CSV",
            domain="football-data.co.uk",
            url=SOCCER_FOOTBALL_DATA_URL,
            transport="residential_proxy",
            source_type="open_csv_dataset",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public CSV used for transient in-memory normalized extraction and summary-only reporting.",
        ),
        "soccer_football_data_docs": OxylabsSourceSpec(
            source_id="soccer_football_data_docs",
            source_name="football-data.co.uk data page",
            domain="football-data.co.uk",
            url="https://www.football-data.co.uk/data.php",
            transport="web_scraper_api",
            source_type="public_docs_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public source page used for source confirmation and terms review context.",
        ),
        "soccer_statsbomb_open_data": OxylabsSourceSpec(
            source_id="soccer_statsbomb_open_data",
            source_name="StatsBomb open-data raw GitHub files",
            domain="raw.githubusercontent.com",
            url=SOCCER_STATSBOMB_COMPETITIONS_URL,
            transport="residential_proxy",
            source_type="open_github_json_dataset",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public open-data repository used only for normalized facts and validated derived features.",
        ),
        "soccer_statsbomb_open_repo": OxylabsSourceSpec(
            source_id="soccer_statsbomb_open_repo",
            source_name="StatsBomb open-data GitHub repository",
            domain="github.com",
            url="https://github.com/statsbomb/open-data",
            transport="web_scraper_api",
            source_type="github_open_source_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public repository page used for discovery and public documentation confirmation.",
        ),
        "soccer_openfootball_repo": OxylabsSourceSpec(
            source_id="soccer_openfootball_repo",
            source_name="openfootball Germany repository",
            domain="github.com",
            url="https://github.com/openfootball/deutschland",
            transport="web_scraper_api",
            source_type="github_open_source_page",
            policy_status="approved_free_open_transport",
            license_or_terms_note="Public openfootball repository used for duplicate checking and source-family confirmation.",
        ),
        "soccer_official_league_page": OxylabsSourceSpec(
            source_id="soccer_official_league_page",
            source_name="Bundesliga official public pages",
            domain="bundesliga.com",
            url="https://www.bundesliga.com/en/bundesliga",
            transport="web_scraper_api",
            source_type="official_league_public_page",
            policy_status="manual_import_only",
            license_or_terms_note="Official public league pages can support manual review or manual imports, but not broad automated structured extraction in this pass.",
        ),
        "soccer_understat_public_page": OxylabsSourceSpec(
            source_id="soccer_understat_public_page",
            source_name="Understat public pages",
            domain="understat.com",
            url="https://understat.com/",
            transport="web_scraper_api",
            source_type="public_xg_stat_page",
            policy_status="license_terms_unclear",
            license_or_terms_note="Public pages exist, but the exact automated data path was not conservatively approved in this pass.",
        ),
        "soccer_statsbomb_paid_vendor_page": OxylabsSourceSpec(
            source_id="soccer_statsbomb_paid_vendor_page",
            source_name="StatsBomb 360 or broader paid product pages",
            domain="statsbomb.com",
            url="https://statsbomb.com/360/",
            transport="web_scraper_api",
            source_type="paid_vendor_page",
            policy_status="paid_subscription_required",
            license_or_terms_note="Public product pages can confirm scope, but broad tracking and enriched 360 coverage remain paid/licensed.",
        ),
        "soccer_wikidata_supplemental": OxylabsSourceSpec(
            source_id="soccer_wikidata_supplemental",
            source_name="Wikidata",
            domain="wikidata.org",
            url="https://www.wikidata.org/",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="supplemental_only",
            license_or_terms_note="Supplemental structured entity metadata only, not a primary performance-stat source.",
        ),
        "soccer_wikipedia_supplemental": OxylabsSourceSpec(
            source_id="soccer_wikipedia_supplemental",
            source_name="Wikipedia",
            domain="wikipedia.org",
            url="https://www.wikipedia.org/",
            transport="web_scraper_api",
            source_type="structured_open_supplemental",
            policy_status="supplemental_only",
            license_or_terms_note="Supplemental table and entity lookup only, not a primary performance-stat source.",
        ),
    }


def source_spec_for(source_id: str) -> OxylabsSourceSpec | None:
    return source_spec_registry().get(source_id)


def lane_source_spec(lane: dict[str, Any]) -> OxylabsSourceSpec:
    source_id = str(lane.get("source_id") or "")
    source_spec = source_spec_for(source_id)
    if source_spec is not None:
        return source_spec
    category = str(lane.get("free_or_paid_category") or "")
    if category in {"policy_blocked", "blocked_reference_or_restricted_source"}:
        return OxylabsSourceSpec(
            source_id="soccer_fbref_blocked",
            source_name="FBref / Sports Reference blocked source",
            domain="fbref.com",
            url="https://fbref.com/",
            transport="web_scraper_api",
            source_type="restricted_reference_site",
            policy_status="blocked_reference_or_restricted_source",
            license_or_terms_note="Blocked by repo policy and explicit user instruction.",
        )
    return source_spec_registry()["soccer_official_league_page"]


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


def discover_soccer_sample_context() -> dict[str, Any]:
    global _SAMPLE_CONTEXT_CACHE
    if _SAMPLE_CONTEXT_CACHE is not None:
        return dict(_SAMPLE_CONTEXT_CACHE)
    football_data_response = fetch_public_page_text(
        source_id="soccer_football_data_csv",
        domain="football-data.co.uk",
        url=SOCCER_FOOTBALL_DATA_URL,
        transport="residential_proxy",
        headers={"Accept": "text/csv,text/plain,*/*"},
    )
    football_data_rows = parse_csv_rows(football_data_response.get("text") or "")
    competitions_response = fetch_public_json(
        source_id="soccer_statsbomb_open_data",
        domain="raw.githubusercontent.com",
        url=SOCCER_STATSBOMB_COMPETITIONS_URL,
        transport="residential_proxy",
    )
    matches_response = fetch_public_json(
        source_id="soccer_statsbomb_open_data",
        domain="raw.githubusercontent.com",
        url=SOCCER_STATSBOMB_MATCHES_URL,
        transport="residential_proxy",
    )
    openfootball_response = fetch_public_page_text(
        source_id="soccer_statsbomb_open_data",
        domain="raw.githubusercontent.com",
        url=SOCCER_OPENFOOTBALL_BUNDESLIGA_URL,
        transport="residential_proxy",
        headers={"Accept": "text/plain,*/*"},
    )
    matches_payload = matches_response.get("json_payload") or []
    sample_match = matches_payload[0] if isinstance(matches_payload, list) and matches_payload else {}
    context = {
        "ok": bool(football_data_response.get("ok") and football_data_rows and matches_response.get("ok") and sample_match),
        "football_data_response": football_data_response,
        "football_data_rows": football_data_rows,
        "statsbomb_competitions_response": competitions_response,
        "statsbomb_matches_response": matches_response,
        "statsbomb_matches": matches_payload if isinstance(matches_payload, list) else [],
        "statsbomb_sample_match": sample_match,
        "statsbomb_sample_match_id": int(sample_match.get("match_id") or 0),
        "statsbomb_competition_name": str(sample_match.get("competition", {}).get("competition_name") or "1. Bundesliga"),
        "statsbomb_season_name": str(sample_match.get("season", {}).get("season_name") or "2023/2024"),
        "openfootball_response": openfootball_response,
        "openfootball_text": openfootball_response.get("text") or "",
    }
    _SAMPLE_CONTEXT_CACHE = context
    return dict(context)
