from __future__ import annotations

from dataclasses import dataclass


OXYLABS_REQUIRED_BLOCKLIST_DOMAINS = (
    "pro-football-reference.com",
    "sports-reference.com",
    "football-reference.com",
    "baseball-reference.com",
    "basketball-reference.com",
    "hockey-reference.com",
    "fbref.com",
    "fangraphs.com",
    "ftnfantasy.com",
)


@dataclass(frozen=True)
class PaidRetrievalSourceRecord:
    sport: str
    source_id: str
    domain: str
    retrieval_method: str
    terms_or_license_status: str
    source_type: str


PAID_RETRIEVAL_SOURCE_REGISTRY: dict[str, list[PaidRetrievalSourceRecord]] = {
    "nfl": [
        PaidRetrievalSourceRecord("nfl", "official_team_staff_pages", "nfl.com", "oxylabs_web_scraper_api", "public_team_media_guides", "official"),
        PaidRetrievalSourceRecord("nfl", "official_team_press_releases", "nfl.com", "oxylabs_web_scraper_api", "public_press_pages", "official"),
        PaidRetrievalSourceRecord("nfl", "official_nfl_staff_or_news_pages", "operations.nfl.com", "oxylabs_web_scraper_api", "public_football_operations_pages", "official"),
    ],
    "mlb": [
        PaidRetrievalSourceRecord("mlb", "official_team_staff_pages", "mlb.com", "oxylabs_web_scraper_api", "public_team_media_guides", "official"),
        PaidRetrievalSourceRecord("mlb", "official_team_press_releases", "mlb.com", "oxylabs_web_scraper_api", "public_press_pages", "official"),
        PaidRetrievalSourceRecord("mlb", "official_public_web", "content.mlb.com", "oxylabs_residential_proxy", "public_pdf_media_guides", "official"),
    ],
}


def paid_retrieval_sources_for(sport: str) -> list[PaidRetrievalSourceRecord]:
    return list(PAID_RETRIEVAL_SOURCE_REGISTRY.get(str(sport).lower(), []))

