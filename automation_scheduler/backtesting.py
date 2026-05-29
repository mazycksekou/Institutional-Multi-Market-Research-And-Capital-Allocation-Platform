from __future__ import annotations

from typing import Any


def run_backtesting_scaffold(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (rows or []) if isinstance(row, dict)]
    settled = [row for row in rows if row.get("final_outcome") is not None]
    if not settled:
        return {
            "ok": True,
            "status": "insufficient_data",
            "sample_size": len(rows),
            "settled_count": 0,
            "insufficient_data": True,
            "metrics": {},
        }
    by_provider: dict[str, int] = {}
    for row in settled:
        provider = str(row.get("provider") or "unknown")
        by_provider[provider] = by_provider.get(provider, 0) + 1
    return {
        "ok": True,
        "status": "computed",
        "sample_size": len(rows),
        "settled_count": len(settled),
        "insufficient_data": False,
        "metrics": {
            "provider_counts": by_provider,
        },
    }
