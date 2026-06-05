from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import SPORTS, basketball_discovery_queries


def build_basketball_source_discovery_queries(sport: str | None = None) -> dict[str, Any]:
    queries = basketball_discovery_queries(sport=sport)
    return {
        "ok": True,
        "status": "ok",
        "sport": sport or "all_basketball",
        "sports_included": [sport] if sport else list(SPORTS),
        "query_count": len(queries),
        "queries": queries,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
