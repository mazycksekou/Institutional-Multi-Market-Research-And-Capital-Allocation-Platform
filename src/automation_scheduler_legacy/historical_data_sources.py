"""
Phase 10H4: Historical Data Source Registry + Model Projection Source Ranking.

Registry-only module that ranks historical sports/betting data sources
for model testing, without any SQLite, downloads, scraping, or importers.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
KEEP = "keep"
KEEP_TOOL = "keep_tool"
DOWNGRADE = "downgrade"
EXPLORATION_ONLY = "exploration_only"
REMOVE = "remove"

# ---------------------------------------------------------------------------
# Historical sports/betting data source definitions
# ---------------------------------------------------------------------------
HISTORICAL_DATA_SOURCES: list[dict[str, Any]] = [
    # 1 – Football-Data.co.uk
    {
        "source_key": "football_data_uk",
        "name": "Football-Data.co.uk",
        "status": KEEP,
        "sport": "soccer",
        "description": (
            "Historical soccer CSV odds/results from multiple European leagues. "
            "The cleanest first source for historical odds/results backtesting."
        ),
        "format_type": "CSV",
        "priority_order": 1,
        "projection_ready": True,
    },
    # 2 – ArnavSaraogi MLB Odds Scraper
    {
        "source_key": "arnav_mlb_odds_scraper",
        "name": "ArnavSaraogi MLB Odds Scraper",
        "status": KEEP,
        "sport": "mlb",
        "description": (
            "MLB JSON odds data including moneyline, spread, and totals."
        ),
        "format_type": "JSON",
        "priority_order": 2,
        "projection_ready": True,
    },
    # 3 – SportsbookReview Scraper Dataset
    {
        "source_key": "sportsbookreview_scraper",
        "name": "SportsbookReview Scraper Dataset",
        "status": KEEP,
        "sport": "*",
        "description": (
            "NFL, NBA, MLB, NHL baseline community-collected data. "
            "Needs validation before production use."
        ),
        "format_type": "JSON/CSV",
        "priority_order": 3,
        "projection_ready": True,
    },
    # 4 – OddsHarvester (keep as tool, not first importer)
    {
        "source_key": "odds_harvester",
        "name": "OddsHarvester",
        "status": KEEP_TOOL,
        "sport": "*",
        "description": (
            "Scraper tool. Useful later for custom data gathering, "
            "but not a first source because scraping is fragile."
        ),
        "format_type": "JSON",
        "priority_order": 4,
        "projection_ready": False,
    },
    # 5 – DataHub Football Data (downgrade)
    {
        "source_key": "datahub_football",
        "name": "DataHub Football Data",
        "status": DOWNGRADE,
        "sport": "soccer",
        "description": (
            "Lower priority than Football-Data.co.uk; data quality unknown."
        ),
        "format_type": "CSV",
        "priority_order": None,
        "projection_ready": False,
    },
    # 6 – georgedouzas sports-betting (downgrade)
    {
        "source_key": "georgedouzas_sports_betting",
        "name": "georgedouzas sports-betting package",
        "status": DOWNGRADE,
        "sport": "*",
        "description": (
            "Library providing betting strategies, not historical odds data."
        ),
        "format_type": "N/A",
        "priority_order": None,
        "projection_ready": False,
    },
    # 7 – oddor (downgrade)
    {
        "source_key": "oddor",
        "name": "oddor",
        "status": DOWNGRADE,
        "sport": "*",
        "description": (
            "Limited scope dataset not suitable as a primary source."
        ),
        "format_type": "CSV",
        "priority_order": None,
        "projection_ready": False,
    },
    # 8 – Kaggle mixed datasets (downgrade)
    {
        "source_key": "kaggle_mixed",
        "name": "Kaggle mixed betting datasets",
        "status": DOWNGRADE,
        "sport": "*",
        "description": (
            "Kaggle datasets require case-by-case approval; "
            "not treated as a default source."
        ),
        "format_type": "CSV",
        "priority_order": None,
        "projection_ready": False,
    },
    # 9 – Medium articles (removed)
    {
        "source_key": "medium_articles",
        "name": "Medium articles",
        "status": REMOVE,
        "sport": "*",
        "description": "Not a data source.",
        "format_type": "N/A",
        "priority_order": None,
        "projection_ready": False,
    },
    # 10 – Reddit threads (removed)
    {
        "source_key": "reddit_threads",
        "name": "Reddit threads",
        "status": REMOVE,
        "sport": "*",
        "description": "Not a data source.",
        "format_type": "N/A",
        "priority_order": None,
        "projection_ready": False,
    },
    # 11 – Generic CSV-to-SQLite forum posts (removed)
    {
        "source_key": "generic_csv_to_sqlite_forum",
        "name": "Generic CSV-to-SQLite forum posts",
        "status": REMOVE,
        "sport": "*",
        "description": "Not an independent source.",
        "format_type": "N/A",
        "priority_order": None,
        "projection_ready": False,
    },
]

REJECTED_SOURCE_NOTES: dict[str, str] = {
    "datahub_football": (
        "Downgraded: Football-Data.co.uk is preferred. "
        "DataHub will be reconsidered after Phase 10H7."
    ),
    "georgedouzas_sports_betting": (
        "Downgraded: Library provides betting strategies not historical odds."
    ),
    "oddor": (
        "Downgraded: Limited scope, not a replacement for Football-Data.co.uk."
    ),
    "kaggle_mixed": (
        "Downgraded: Kaggle datasets require case-by-case approval."
    ),
    "medium_articles": "Removed: Not a data source.",
    "reddit_threads": "Removed: Not a data source.",
    "generic_csv_to_sqlite_forum": "Removed: Not an independent source.",
}


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------


def get_historical_data_sources(
    status: str | None = None,
    sport: str | None = None,
) -> list[dict[str, Any]]:
    """Return source definitions, optionally filtered by *status* and/or *sport*.

    A source whose ``sport`` equals ``"*"`` is considered a match for any sport
    unless a narrower sport filter is provided.
    """
    result = [dict(src) for src in HISTORICAL_DATA_SOURCES]
    if status is not None:
        result = [src for src in result if src["status"] == status]
    if sport is not None:
        result = [
            src for src in result
            if src["sport"] == sport or src["sport"] == "*"
        ]
    return result


def get_priority_import_sources(
    sport: str | None = None,
) -> list[dict[str, Any]]:
    """Return the sources that are immediate candidates for a historical
    odds importer (status ``KEEP``), sorted by their ``priority_order``."""
    keep = get_historical_data_sources(status=KEEP, sport=sport)
    keep.sort(key=lambda s: s.get("priority_order", 999))
    return keep


def get_historical_data_source_rows(
    include_rejected: bool = False,
) -> list[dict[str, Any]]:
    """Return flat rows suitable for display in Streamlit/data frames.

    When *include_rejected* is ``True``, sources with status ``REMOVE`` are
    also included.
    """
    rows: list[dict[str, Any]] = []
    for src in HISTORICAL_DATA_SOURCES:
        if not include_rejected and src["status"] == REMOVE:
            continue
        rows.append(
            {
                "source_key": src["source_key"],
                "name": src["name"],
                "status": src["status"],
                "sport": src["sport"],
                "description": src["description"],
                "format": src["format_type"],
                "priority_order": src.get("priority_order"),
                "projection_ready": src.get("projection_ready", False),
            }
        )
    return rows


def get_source_status_counts() -> dict[str, int]:
    """Return a dictionary counting how many sources have each status."""
    counts: dict[str, int] = {}
    for src in HISTORICAL_DATA_SOURCES:
        s = src["status"]
        counts[s] = counts.get(s, 0) + 1
    return counts


def get_model_testing_source_plan() -> str:
    """Return a human-readable markdown overview of the staged import plan."""
    lines = [
        "## Historical Data Source Import Plan",
        "",
        "**Phase 10H4** – Source registry complete.",
        "**Phase 10H5** – Importers complete.",
        "**Phase 10H6** – SQLite store complete.",
        "**Phase 10H7** – SQLite backtest bridge complete.",
        "**Phase 10H8** – Streamlit SQLite UI complete.",
        "**Phase 10H9** – Real sample import walkthrough in progress.",
        "",
        "Current priority order for first importer:",
    ]
    prio = get_priority_import_sources()
    for i, src in enumerate(prio, start=1):
        lines.append(f"  {i}. {src['name']} (`{src['source_key']}`)")
    lines.append("")
    lines.append("SQLite store is operational. See Phase 10H6 and later.")
    return "\n".join(lines)


def source_is_projection_ready(source_key: str) -> bool:
    """Return ``True`` if the source is trusted enough for model projection."""
    srcs = {s["source_key"]: s for s in HISTORICAL_DATA_SOURCES}
    src = srcs.get(source_key)
    if src is None:
        return False
    return src.get("projection_ready", False)


def summarize_source_registry() -> dict[str, Any]:
    """Return a dictionary summarising the whole registry."""
    keep = get_priority_import_sources()
    summary: dict[str, Any] = {}
    if keep:
        summary["first_importer"] = keep[0]["source_key"]
    else:
        summary["first_importer"] = None
    counts = get_source_status_counts()
    summary["total_sources"] = len(HISTORICAL_DATA_SOURCES)
    summary["keep_count"] = counts.get(KEEP, 0)
    summary["keep_tool_count"] = counts.get(KEEP_TOOL, 0)
    summary["downgrade_count"] = counts.get(DOWNGRADE, 0)
    summary["exploration_only_count"] = counts.get(EXPLORATION_ONLY, 0)
    summary["remove_count"] = counts.get(REMOVE, 0)
    summary["plan"] = get_model_testing_source_plan()
    return summary
