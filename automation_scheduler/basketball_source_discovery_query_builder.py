from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import SPORTS
from .basketball_source_exhaustion_query_builder import build_basketball_source_exhaustion_queries


def build_basketball_source_discovery_queries(sport: str | None = None) -> dict[str, Any]:
    plan = build_basketball_source_exhaustion_queries(sport=sport)
    return {
        "ok": True,
        "status": "ok",
        "sport": sport or "all_basketball",
        "sports_included": [sport] if sport else list(SPORTS),
        "query_count": int(plan.get("query_count", 0) or 0),
        "queries": list(plan.get("query_rows") or []),
        "query_texts": list(plan.get("queries") or []),
        "query_rows": list(plan.get("query_rows") or []),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
