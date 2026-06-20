"""Scaffold-only web scraping connector boundary."""

from .contracts import WEB_SCRAPING_CONNECTOR_CATEGORY, WebScrapingConnectorContract, build_web_intake_connector_contract

__all__ = [
    "WEB_SCRAPING_CONNECTOR_CATEGORY",
    "WebScrapingConnectorContract",
    "build_web_intake_connector_contract",
]
