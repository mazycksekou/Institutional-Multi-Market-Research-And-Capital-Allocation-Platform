from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .paid_retrieval_sources import (
    OXYLABS_ALLOWED_SOURCE_IDS,
    OXYLABS_INITIAL_ALLOWLIST_DOMAINS,
    OXYLABS_REQUIRED_BLOCKLIST_DOMAINS,
    OXYLABS_WEB_SCRAPER_API_ENV_VARS,
    PaidRetrievalSourcePolicy,
)
from .retrieval_policy import normalize_domain


DEFAULT_WEB_SCRAPER_TIMEOUT_SECONDS = 45
DEFAULT_USER_AGENT = "betting-stock-api-research-bot/0.1"


@dataclass
class OxylabsWebScraperApiAdapter:
    source_id: str = ""
    domain: str = ""
    allow_oxylabs: bool = False
    allow_paid_retrieval: bool = False
    allowed_source_ids: tuple[str, ...] = OXYLABS_ALLOWED_SOURCE_IDS
    allowed_domains: tuple[str, ...] = OXYLABS_INITIAL_ALLOWLIST_DOMAINS
    blocked_domains: tuple[str, ...] = OXYLABS_REQUIRED_BLOCKLIST_DOMAINS

    @property
    def username(self) -> str:
        return str(os.getenv(OXYLABS_WEB_SCRAPER_API_ENV_VARS[0], "")).strip()

    @property
    def password(self) -> str:
        return str(os.getenv(OXYLABS_WEB_SCRAPER_API_ENV_VARS[1], "")).strip()

    @property
    def endpoint(self) -> str:
        return str(os.getenv(OXYLABS_WEB_SCRAPER_API_ENV_VARS[2], "")).strip()

    def is_configured(self) -> bool:
        return all(str(os.getenv(name, "")).strip() for name in OXYLABS_WEB_SCRAPER_API_ENV_VARS)

    def __repr__(self) -> str:
        return (
            f"OxylabsWebScraperApiAdapter(source_id={self.source_id!r}, domain={normalize_domain(self.domain)!r}, "
            f"configured={self.is_configured()}, allow_oxylabs={self.allow_oxylabs}, allow_paid_retrieval={self.allow_paid_retrieval})"
        )

    def evaluate(self) -> dict[str, object]:
        return PaidRetrievalSourcePolicy(
            source_id=self.source_id,
            domain=self.domain,
            allow_oxylabs=self.allow_oxylabs,
            allow_paid_retrieval=self.allow_paid_retrieval,
            source_allowlist=self.allowed_source_ids,
            domain_allowlist=self.allowed_domains,
            domain_blocklist=self.blocked_domains,
        ).evaluate()

    def fetch_text(self, url: str, *, timeout: int = DEFAULT_WEB_SCRAPER_TIMEOUT_SECONDS) -> dict[str, Any]:
        decision = self.evaluate()
        if not decision["allowed"]:
            return {"ok": False, "status": "blocked", "blocked_reason": decision["blocked_reason"], "text": "", "raw_html_persisted": False, "raw_payload_included": False, "secrets_included": False}
        if not self.is_configured():
            return {"ok": False, "status": "blocked", "blocked_reason": "oxylabs_web_scraper_not_configured", "text": "", "raw_html_persisted": False, "raw_payload_included": False, "secrets_included": False}
        token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps({"url": url}).encode("utf-8"),
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/json,text/plain,*/*",
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return {"ok": False, "status": "blocked", "blocked_reason": f"oxylabs_http_error_{exc.code}", "text": "", "raw_html_persisted": False, "raw_payload_included": False, "secrets_included": False}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "status": "blocked", "blocked_reason": f"oxylabs_fetch_failed_{type(exc).__name__}", "text": "", "raw_html_persisted": False, "raw_payload_included": False, "secrets_included": False}
        return {
            "ok": True,
            "status": "ok",
            "blocked_reason": None,
            "text": text,
            "raw_html_persisted": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }
