from __future__ import annotations

from typing import Any


SOURCE_FAMILIES = (
    "odds_feed_providers",
    "live_state_feed_providers",
    "sportsbook_odds_pages",
    "public_odds_apis",
    "historical_odds_apis",
    "exchange_price_feeds",
    "score_state_providers",
    "official_league_state_feeds",
    "replay_odds_snapshot_providers",
    "public_odds_archives",
    "paid_market_data_providers",
)


def build_queries() -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    for family in SOURCE_FAMILIES:
        queries.append(
            {
                "source_family": family,
                "queries": [
                    f"{family} API documentation terms normalized odds read only",
                    f"{family} commercial use license automated access data dictionary",
                    f"{family} robots terms replay archive odds snapshots",
                ],
                "required_reviews": ["terms", "license", "robots_if_public_web", "api_docs", "data_dictionary"],
                "forbidden_actions": ["provider_write", "raw_payload_persistence", "account_session_access"],
            }
        )
    return queries


def main() -> int:
    for row in build_queries():
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
