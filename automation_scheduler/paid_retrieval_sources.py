from __future__ import annotations

from dataclasses import dataclass

from .retrieval_policy import RetrievalPolicy


OXYLABS_RESIDENTIAL_PROXY_ENV_VARS = (
    "OXYLABS_PROXY_HOST",
    "OXYLABS_PROXY_PORT",
    "OXYLABS_PROXY_USERNAME",
    "OXYLABS_PROXY_PASSWORD",
)

OXYLABS_WEB_SCRAPER_API_ENV_VARS = (
    "OXYLABS_API_USERNAME",
    "OXYLABS_API_PASSWORD",
    "OXYLABS_API_ENDPOINT",
)

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

OXYLABS_INITIAL_ALLOWLIST_DOMAINS = (
    "nfl.com",
    "*.nfl.com",
)

OXYLABS_ALLOWED_SOURCE_IDS = (
    "official_team_staff_pages",
    "official_team_press_releases",
    "official_nfl_staff_or_news_pages",
)


@dataclass(frozen=True)
class PaidRetrievalSourcePolicy:
    source_id: str
    domain: str
    allow_oxylabs: bool = False
    allow_paid_retrieval: bool = False
    source_allowlist: tuple[str, ...] = OXYLABS_ALLOWED_SOURCE_IDS
    domain_allowlist: tuple[str, ...] = OXYLABS_INITIAL_ALLOWLIST_DOMAINS
    domain_blocklist: tuple[str, ...] = OXYLABS_REQUIRED_BLOCKLIST_DOMAINS

    def evaluate(self) -> dict[str, object]:
        return RetrievalPolicy(
            allow_oxylabs=self.allow_oxylabs,
            allow_paid_retrieval=self.allow_paid_retrieval,
            source_id=self.source_id,
            domain=self.domain,
            source_allowlist=self.source_allowlist,
            domain_allowlist=self.domain_allowlist,
            domain_blocklist=self.domain_blocklist,
        ).evaluate()
