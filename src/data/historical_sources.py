from __future__ import annotations

from typing import Any

from .contracts import DataSourceDescriptor
from .source_registry import DEFAULT_LOCAL_SOURCE_REGISTRY, register_local_source


_SOURCE_ROWS: tuple[dict[str, Any], ...] = (
    {
        "source_key": "football_data_uk",
        "name": "Football-Data.co.uk",
        "status": "keep",
        "sport": "soccer",
        "description": "Premier League and other football datasets.",
        "format": "csv",
        "priority_order": 1,
        "projection_ready": True,
        "source_type": "local",
    },
    {
        "source_key": "arnav_mlb_odds_scraper",
        "name": "Arnav MLB Odds Scraper",
        "status": "keep",
        "sport": "mlb",
        "description": "MLB odds scrape archive used by tests.",
        "format": "csv",
        "priority_order": 2,
        "projection_ready": True,
        "source_type": "local",
    },
    {
        "source_key": "sportsbookreview_scraper",
        "name": "Sportsbook Review Scraper",
        "status": "keep",
        "sport": "any",
        "description": "Legacy sportsbook review odds archive.",
        "format": "csv",
        "priority_order": 3,
        "projection_ready": True,
        "source_type": "local",
    },
    {
        "source_key": "odds_harvester",
        "name": "Odds Harvester",
        "status": "keep_tool",
        "sport": "any",
        "description": "Tool-only odds source kept out of import queues.",
        "format": "csv",
        "priority_order": 99,
        "projection_ready": False,
        "source_type": "local",
    },
)


def _seed_sources() -> tuple[DataSourceDescriptor, ...]:
    sources = tuple(
        DataSourceDescriptor(
            name=row["source_key"],
            source_type=row["source_type"],
            description=row["description"],
            tags=(row["sport"], "local", "historical"),
            metadata={
                "priority": row["priority_order"],
                "status": row["status"],
                "source_key": row["source_key"],
                "format": row["format"],
                "sport": row["sport"],
                "projection_ready": row["projection_ready"],
            },
        )
        for row in _SOURCE_ROWS
    )
    for source in sources:
        try:
            register_local_source(source)
        except ValueError:
            continue
    return sources


def _source_rows() -> list[dict[str, Any]]:
    _seed_sources()
    rows: list[dict[str, Any]] = []
    for source in _SOURCE_ROWS:
        row = dict(source)
        row["local_only"] = True
        rows.append(row)
    return rows


def get_historical_data_sources(*args: Any, status: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
    rows = _source_rows()
    if status is not None:
        rows = [row for row in rows if str(row.get("status") or "").lower() == str(status).lower()]
    return rows


def get_priority_import_sources(*args: Any, sport: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
    from src.data.historical_data_sources import (
        get_priority_import_sources as legacy_get_priority_import_sources,
    )

    return legacy_get_priority_import_sources(*args, sport=sport, **kwargs)


def get_historical_data_source_rows(*args: Any, include_rejected: bool = True, **kwargs: Any) -> list[dict[str, Any]]:
    rows = _source_rows()
    if not include_rejected:
        rows = [row for row in rows if row.get("status") != "remove"]
    return [
        {
            "source_key": row["source_key"],
            "name": row["name"],
            "status": row["status"],
            "sport": row["sport"],
            "description": row["description"],
            "format": row["format"],
            "priority_order": row["priority_order"],
            "priority": row["priority_order"],
            "projection_ready": bool(row["projection_ready"]),
            "source_type": row["source_type"],
            "local_only": True,
        }
        for row in rows
    ]


def get_source_status_counts(*args: Any, **kwargs: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in get_historical_data_source_rows():
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def get_model_testing_source_plan(*args: Any, **kwargs: Any) -> str:
    rows = get_historical_data_source_rows()
    return "\n".join(
        [
            "Phase 10H6 local-only data source testing plan",
            f"source_count={len(rows)}",
            "automation_scheduler removed from runtime boundary",
        ]
    )


__all__ = [
    "get_historical_data_source_rows",
    "get_historical_data_sources",
    "get_model_testing_source_plan",
    "get_priority_import_sources",
    "get_source_status_counts",
]
