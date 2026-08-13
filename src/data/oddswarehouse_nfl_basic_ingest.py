from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import monotonic
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET

from src.data.data_identity_lakehouse import DataIdentityLakehouseRuntime
from src.data.data_paths import get_runtime_data_path, get_storage_health
from src.data.historical_dataset_acquisition_runtime import HistoricalDatasetAcquisitionRuntime
from src.data.historical_canonical_compatibility import (
    DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY,
    GOVERNED_REVISION,
    SEMANTIC_REUSE,
    compare_historical_canonical_rows,
)
from src.data.historical_research_asset_certification_runtime import (
    HistoricalResearchAssetCertificationRuntime,
    ResearchAssetCertificationContract,
    build_historical_dataset_certification_row,
)
from src.data.local_platform import DatasetContract, LocalDataPlatform
from src.data.nfl_p0_foundation import get_nfl_p0_market_profile
from src.data.odds_math import american_to_implied_probability, remove_two_way_vig
from src.data.research_asset_lifecycle_runtime import (
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
)
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION = "src.data.oddswarehouse_nfl_basic_ingest.v1"
ODDSWAREHOUSE_NFL_BASIC_PARSER_VERSION = "src.data.oddswarehouse_nfl_basic_ingest.parser.v2"
ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID = "oddswarehouse"
ODDSWAREHOUSE_NFL_BASIC_PROVIDER_NAME = "OddsWarehouse"
ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID = "nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_DATASET_ID = "oddswarehouse.nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME = "OddsWarehouse NFL Basic"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE = "controlled_vendor_file"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY = "oddswarehouse_nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID = "connector.manual_import.oddswarehouse_nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_NAME = "OddsWarehouse NFL Basic Manual Import"
ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID = "sports:nfl"
ODDSWAREHOUSE_NFL_BASIC_DATASET_ID = "dataset.sports.nfl.oddswarehouse.nfl_basic.historical"
ODDSWAREHOUSE_NFL_BASIC_DATASET_ALIAS = "dataset.sports.nfl.oddswarehouse.nfl_basic.current"
ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION = "oddswarehouse.nfl_basic.historical.v1"
ODDSWAREHOUSE_NFL_BASIC_DATASET_REVISION = "r001"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID = f"{ODDSWAREHOUSE_NFL_BASIC_DATASET_ID}.source_events"
ODDSWAREHOUSE_NFL_BASIC_MARKET_OBSERVATIONS_ASSET_ID = f"{ODDSWAREHOUSE_NFL_BASIC_DATASET_ID}.market_observations"
ODDSWAREHOUSE_NFL_BASIC_GOLD_ASSET_ID = f"{ODDSWAREHOUSE_NFL_BASIC_DATASET_ID}.event_market_selection_gold"
ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET = "NFL_Basic"
ODDSWAREHOUSE_NFL_BASIC_LEGACY_BRONZE_SEASON = 2009
ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH = get_runtime_data_path(
    "historical",
    "oddswarehouse_nfl_basic_pilot",
    "canonical_data.sqlite",
)
ODDSWAREHOUSE_NFL_BASIC_LAKEHOUSE_ROOT = get_runtime_data_path(
    "lakehouse",
    "oddswarehouse_nfl_basic_pilot",
)
ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT = get_runtime_data_path(
    "historical",
    "ow_nfl_basic_pilot",
    "br",
)
ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT = get_runtime_data_path(
    "reports",
    "oddswarehouse_nfl_basic_pilot",
)
ODDSWAREHOUSE_PROGRESS_INTERVAL_SECONDS = 30.0
NFL_PRESEASON_LOOKBACK_DAYS = 35
NFL_POSTSEASON_LOOKAHEAD_DAYS = 35

EXPECTED_HEADERS: tuple[str, ...] = (
    "Game ID",
    "Date",
    "Away Team",
    "Away Score",
    "Away Spread Open",
    "Away Spread Open Odds",
    "Away Spread Close",
    "Away Spread Close Odds",
    "Away MoneyLine Open",
    "Away MoneyLine Close",
    "Over Open",
    "Over Open Odds",
    "Over Close",
    "Over Close Odds",
    "Home Team",
    "Home Score",
    "Home Spread Open",
    "Home Spread Open Odds",
    "Home Spread Close",
    "Home Spread Close Odds",
    "Home MoneyLine Open",
    "Home MoneyLine Close",
    "Under Open",
    "Under Open Odds",
    "Under Close",
    "Under Close Odds",
)

XML_NAMESPACES = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

SPREAD_LINE_FIELDS: frozenset[str] = frozenset(
    {
        "Away Spread Open",
        "Away Spread Close",
        "Home Spread Open",
        "Home Spread Close",
    }
)


@dataclass(frozen=True, slots=True)
class TeamMapping:
    source_name: str
    team_id: str
    franchise_id: str
    historical_display_name: str
    canonical_team_name: str
    effective_start: str
    effective_end: str


TEAM_MAPPINGS: dict[str, TeamMapping] = {
    mapping.source_name: mapping
    for mapping in (
        TeamMapping("Arizona", "ARI", "nfl.franchise.cardinals", "Arizona Cardinals", "Arizona Cardinals", "1988-01-01", ""),
        TeamMapping("Atlanta", "ATL", "nfl.franchise.falcons", "Atlanta Falcons", "Atlanta Falcons", "1966-01-01", ""),
        TeamMapping("Baltimore", "BAL", "nfl.franchise.ravens", "Baltimore Ravens", "Baltimore Ravens", "1996-01-01", ""),
        TeamMapping("Buffalo", "BUF", "nfl.franchise.bills", "Buffalo Bills", "Buffalo Bills", "1960-01-01", ""),
        TeamMapping("Carolina", "CAR", "nfl.franchise.panthers", "Carolina Panthers", "Carolina Panthers", "1995-01-01", ""),
        TeamMapping("Chicago", "CHI", "nfl.franchise.bears", "Chicago Bears", "Chicago Bears", "1920-01-01", ""),
        TeamMapping("Cincinnati", "CIN", "nfl.franchise.bengals", "Cincinnati Bengals", "Cincinnati Bengals", "1968-01-01", ""),
        TeamMapping("Cleveland", "CLE", "nfl.franchise.browns", "Cleveland Browns", "Cleveland Browns", "1999-01-01", ""),
        TeamMapping("Dallas", "DAL", "nfl.franchise.cowboys", "Dallas Cowboys", "Dallas Cowboys", "1960-01-01", ""),
        TeamMapping("Denver", "DEN", "nfl.franchise.broncos", "Denver Broncos", "Denver Broncos", "1960-01-01", ""),
        TeamMapping("Detroit", "DET", "nfl.franchise.lions", "Detroit Lions", "Detroit Lions", "1934-01-01", ""),
        TeamMapping("Green Bay", "GB", "nfl.franchise.packers", "Green Bay Packers", "Green Bay Packers", "1921-01-01", ""),
        TeamMapping("Houston", "HOU", "nfl.franchise.texans", "Houston Texans", "Houston Texans", "2002-01-01", ""),
        TeamMapping("Indianapolis", "IND", "nfl.franchise.colts", "Indianapolis Colts", "Indianapolis Colts", "1984-01-01", ""),
        TeamMapping("Jacksonville", "JAX", "nfl.franchise.jaguars", "Jacksonville Jaguars", "Jacksonville Jaguars", "1995-01-01", ""),
        TeamMapping("Kansas City", "KC", "nfl.franchise.chiefs", "Kansas City Chiefs", "Kansas City Chiefs", "1963-01-01", ""),
        TeamMapping("Miami", "MIA", "nfl.franchise.dolphins", "Miami Dolphins", "Miami Dolphins", "1966-01-01", ""),
        TeamMapping("Minnesota", "MIN", "nfl.franchise.vikings", "Minnesota Vikings", "Minnesota Vikings", "1961-01-01", ""),
        TeamMapping("N.Y. Giants", "NYG", "nfl.franchise.giants", "New York Giants", "New York Giants", "1925-01-01", ""),
        TeamMapping("N.Y. Jets", "NYJ", "nfl.franchise.jets", "New York Jets", "New York Jets", "1963-01-01", ""),
        TeamMapping("New England", "NE", "nfl.franchise.patriots", "New England Patriots", "New England Patriots", "1971-01-01", ""),
        TeamMapping("New Orleans", "NO", "nfl.franchise.saints", "New Orleans Saints", "New Orleans Saints", "1967-01-01", ""),
        TeamMapping("Oakland", "LV", "nfl.franchise.raiders", "Oakland Raiders", "Las Vegas Raiders", "1995-01-01", "2019-12-31"),
        TeamMapping("Philadelphia", "PHI", "nfl.franchise.eagles", "Philadelphia Eagles", "Philadelphia Eagles", "1933-01-01", ""),
        TeamMapping("Pittsburgh", "PIT", "nfl.franchise.steelers", "Pittsburgh Steelers", "Pittsburgh Steelers", "1933-01-01", ""),
        TeamMapping("San Diego", "LAC", "nfl.franchise.chargers", "San Diego Chargers", "Los Angeles Chargers", "1961-01-01", "2016-12-31"),
        TeamMapping("San Francisco", "SF", "nfl.franchise.49ers", "San Francisco 49ers", "San Francisco 49ers", "1946-01-01", ""),
        TeamMapping("Seattle", "SEA", "nfl.franchise.seahawks", "Seattle Seahawks", "Seattle Seahawks", "1976-01-01", ""),
        TeamMapping("St. Louis", "LAR", "nfl.franchise.rams", "St. Louis Rams", "Los Angeles Rams", "1995-01-01", "2015-12-31"),
        TeamMapping("Tampa Bay", "TB", "nfl.franchise.buccaneers", "Tampa Bay Buccaneers", "Tampa Bay Buccaneers", "1976-01-01", ""),
        TeamMapping("Tennessee", "TEN", "nfl.franchise.titans", "Tennessee Titans", "Tennessee Titans", "1999-01-01", ""),
        TeamMapping("Washington", "WAS", "nfl.franchise.washington", "Washington Redskins", "Washington Commanders", "1937-01-01", ""),
    )
}

TEAM_ALIAS_MAPPINGS: tuple[TeamMapping, ...] = (
    TeamMapping("L.A. Rams", "LAR", "nfl.franchise.rams", "Los Angeles Rams", "Los Angeles Rams", "2016-01-01", ""),
    TeamMapping("Los Angeles", "LAR", "nfl.franchise.rams", "Los Angeles Rams", "Los Angeles Rams", "2016-01-01", "2016-12-31"),
    TeamMapping("L.A. Chargers", "LAC", "nfl.franchise.chargers", "Los Angeles Chargers", "Los Angeles Chargers", "2017-01-01", ""),
    TeamMapping("Las Vegas", "LV", "nfl.franchise.raiders", "Las Vegas Raiders", "Las Vegas Raiders", "2020-01-01", ""),
    TeamMapping("AFC", "AFC", "nfl.conference.afc", "AFC Pro Bowl Team", "AFC Pro Bowl Team", "1960-01-01", ""),
    TeamMapping("NFC", "NFC", "nfl.conference.nfc", "NFC Pro Bowl Team", "NFC Pro Bowl Team", "1960-01-01", ""),
    TeamMapping("Team Rice", "TEAM_RICE", "nfl.special_team.team_rice", "Team Rice", "Team Rice", "2014-01-01", ""),
    TeamMapping("Team Sanders", "TEAM_SANDERS", "nfl.special_team.team_sanders", "Team Sanders", "Team Sanders", "2015-01-01", ""),
)

TEAM_MAPPING_VARIANTS: dict[str, tuple[TeamMapping, ...]] = {}
for _mapping in (*TEAM_MAPPINGS.values(), *TEAM_ALIAS_MAPPINGS):
    TEAM_MAPPING_VARIANTS.setdefault(_mapping.source_name, tuple())
    TEAM_MAPPING_VARIANTS[_mapping.source_name] = (*TEAM_MAPPING_VARIANTS[_mapping.source_name], _mapping)


class _StageProgressTracker:
    def __init__(
        self,
        *,
        run_id: str = "",
        emit_interval_seconds: float = ODDSWAREHOUSE_PROGRESS_INTERVAL_SECONDS,
        stream: Any = None,
    ) -> None:
        self.run_id = _normalize_text(run_id, "pending")
        self.emit_interval_seconds = max(0.0, float(emit_interval_seconds))
        self.stream = stream if stream is not None else sys.stderr
        self.stage_timings: dict[str, dict[str, Any]] = {}
        self.progress_events: list[dict[str, Any]] = []
        self._active_stage: str | None = None
        self._active_started_at = 0.0
        self._last_emitted_at = 0.0
        self._rows_processed = 0
        self._rows_total = 0
        self._partitions_processed = 0
        self._partitions_total = 0

    def set_run_id(self, run_id: str) -> None:
        normalized = _normalize_text(run_id)
        if normalized:
            self.run_id = normalized

    def start(
        self,
        stage: str,
        *,
        rows_total: int = 0,
        partitions_total: int = 0,
    ) -> None:
        self._active_stage = stage
        self._active_started_at = monotonic()
        self._last_emitted_at = self._active_started_at
        self._rows_processed = 0
        self._rows_total = max(0, int(rows_total))
        self._partitions_processed = 0
        self._partitions_total = max(0, int(partitions_total))

    def update(
        self,
        *,
        rows_processed: int | None = None,
        rows_total: int | None = None,
        partitions_processed: int | None = None,
        partitions_total: int | None = None,
        force: bool = False,
    ) -> None:
        if self._active_stage is None:
            return
        if rows_processed is not None:
            self._rows_processed = max(0, int(rows_processed))
        if rows_total is not None:
            self._rows_total = max(0, int(rows_total))
        if partitions_processed is not None:
            self._partitions_processed = max(0, int(partitions_processed))
        if partitions_total is not None:
            self._partitions_total = max(0, int(partitions_total))
        now = monotonic()
        if not force and self.emit_interval_seconds and (now - self._last_emitted_at) < self.emit_interval_seconds:
            return
        self._last_emitted_at = now
        self._emit("ACTIVE", elapsed_seconds=now - self._active_started_at)

    def complete(
        self,
        *,
        rows_processed: int | None = None,
        rows_total: int | None = None,
        partitions_processed: int | None = None,
        partitions_total: int | None = None,
    ) -> None:
        if self._active_stage is None:
            return
        self.update(
            rows_processed=rows_processed,
            rows_total=rows_total,
            partitions_processed=partitions_processed,
            partitions_total=partitions_total,
            force=True,
        )
        elapsed = monotonic() - self._active_started_at
        self.stage_timings[self._active_stage] = {
            "status": "COMPLETED",
            "elapsed_seconds": round(elapsed, 4),
            "rows_processed": self._rows_processed,
            "rows_total": self._rows_total,
            "partitions_processed": self._partitions_processed,
            "partitions_total": self._partitions_total,
        }
        self._emit("COMPLETED", elapsed_seconds=elapsed)
        self._active_stage = None

    def fail(
        self,
        *,
        interrupted: bool = False,
        error: str = "",
    ) -> None:
        if self._active_stage is None:
            return
        elapsed = monotonic() - self._active_started_at
        status = "INTERRUPTED" if interrupted else "FAILED"
        self.stage_timings[self._active_stage] = {
            "status": status,
            "elapsed_seconds": round(elapsed, 4),
            "rows_processed": self._rows_processed,
            "rows_total": self._rows_total,
            "partitions_processed": self._partitions_processed,
            "partitions_total": self._partitions_total,
            "error": error or None,
        }
        self._emit(status, elapsed_seconds=elapsed, error=error or None)
        self._active_stage = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "stage_timings": dict(self.stage_timings),
            "progress_events": list(self.progress_events),
        }

    def _emit(
        self,
        status: str,
        *,
        elapsed_seconds: float,
        error: str | None = None,
    ) -> None:
        if self._active_stage is None:
            return
        payload = {
            "run_id": self.run_id,
            "stage": self._active_stage,
            "status": status,
            "elapsed_seconds": round(float(elapsed_seconds), 4),
            "rows_processed": self._rows_processed,
            "rows_total": self._rows_total,
            "partitions_processed": self._partitions_processed,
            "partitions_total": self._partitions_total,
        }
        if error:
            payload["error"] = error
        self.progress_events.append(payload)
        print(_as_json(payload), file=self.stream, flush=True)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed or parsed in {float("inf"), float("-inf")}:
        return default
    return parsed


def _normalize_oddswarehouse_spread_value(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    if isinstance(value, str):
        token = value.strip()
        if not token:
            return default
        if token.upper() == "PK":
            return 0.0
        value = token
    return _normalize_float(value, default)


def _normalize_numeric_source_value(field_name: str, value: Any, default: float | None = None) -> float | None:
    if field_name in SPREAD_LINE_FIELDS:
        return _normalize_oddswarehouse_spread_value(value, default)
    return _normalize_float(value, default)


def _normalize_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps([prefix, *parts], ensure_ascii=False, sort_keys=False, default=str)
    return f"{prefix}.{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def _stable_digest(*parts: Any) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _date_from_source(value: str) -> str:
    parsed = datetime.strptime(value, "%Y%m%d")
    return parsed.strftime("%Y-%m-%d")


_NFL_REGULAR_SEASON_WEEK_ONE_OVERRIDES = {
    2012: date(2012, 9, 5),
}


def _source_date_as_date(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def _season_for_source_date(event_date: date) -> int:
    return event_date.year - 1 if event_date.month <= 2 else event_date.year


def _nfl_regular_season_week_one_start(season: int) -> date:
    override = _NFL_REGULAR_SEASON_WEEK_ONE_OVERRIDES.get(int(season))
    if override is not None:
        return override
    september_first = date(int(season), 9, 1)
    labor_day_offset = (0 - september_first.weekday()) % 7
    labor_day = september_first + timedelta(days=labor_day_offset)
    return labor_day + timedelta(days=3)


def _nfl_regular_season_week_count(season: int) -> int:
    return 18 if int(season) >= 2021 else 17


def _mapping_effective_for_date(mapping: TeamMapping, event_date: date) -> bool:
    start = _source_date_as_date(mapping.effective_start.replace("-", "")) if _normalize_text(mapping.effective_start) else None
    end = _source_date_as_date(mapping.effective_end.replace("-", "")) if _normalize_text(mapping.effective_end) else None
    if start is not None and event_date < start:
        return False
    if end is not None and event_date > end:
        return False
    return True


def _resolve_team_mapping(source_name: str, date_value: str) -> TeamMapping | None:
    candidates = TEAM_MAPPING_VARIANTS.get(_normalize_text(source_name), ())
    if not candidates:
        return None
    if not re.fullmatch(r"\d{8}", _normalize_text(date_value)):
        return candidates[0]
    event_date = _source_date_as_date(date_value)
    for mapping in candidates:
        if _mapping_effective_for_date(mapping, event_date):
            return mapping
    return None


def _season_context_for_date(date_value: str) -> tuple[int | None, str | None, int | None, str | None]:
    if not re.fullmatch(r"\d{8}", date_value):
        return None, None, None, "invalid_date_format"
    event_date = _source_date_as_date(date_value)
    season = _season_for_source_date(event_date)
    week_one_start = _nfl_regular_season_week_one_start(season)
    preseason_start = week_one_start - timedelta(days=NFL_PRESEASON_LOOKBACK_DAYS)
    if event_date < preseason_start:
        return season, None, None, "before_supported_season_window"
    if event_date < week_one_start:
        preseason_week = max(1, ((event_date - preseason_start).days // 7) + 1)
        return season, "preseason", preseason_week, None
    regular_week_count = _nfl_regular_season_week_count(season)
    regular_season_end = week_one_start + timedelta(days=regular_week_count * 7)
    if event_date < regular_season_end:
        regular_week = ((event_date - week_one_start).days // 7) + 1
        return season, "regular", regular_week, None
    postseason_end = regular_season_end + timedelta(days=NFL_POSTSEASON_LOOKAHEAD_DAYS)
    if event_date < postseason_end:
        postseason_week = regular_week_count + 1 + ((event_date - regular_season_end).days // 7)
        return season, "postseason", postseason_week, None
    return season, None, None, "outside_supported_season_window"


def _regular_season_week_for_date(date_value: str) -> tuple[int | None, int | None, str | None]:
    season, season_type, week, error = _season_context_for_date(date_value)
    if season_type == "regular" and week is not None:
        return season, week, None
    if error:
        return season, None, error
    if season_type == "preseason":
        return season, None, "before_regular_season_window"
    if season_type == "postseason":
        return season, None, "outside_regular_season_window"
    return season, None, "outside_regular_season_window"


def _season_coverage_from_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    seasons: list[int] = []
    for row in rows:
        date_value = _normalize_text(row.get("Date"))
        season, _, _, error = _season_context_for_date(date_value)
        if season is None or error == "invalid_date_format":
            continue
        seasons.append(season)
    unique_seasons = sorted(set(seasons))
    return {
        "min": unique_seasons[0] if unique_seasons else None,
        "max": unique_seasons[-1] if unique_seasons else None,
        "values": unique_seasons,
    }


def _date_coverage_from_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dates = sorted(
        _normalize_text(row.get("Date"))
        for row in rows
        if _normalize_text(row.get("Date"))
    )
    return {
        "min": dates[0] if dates else None,
        "max": dates[-1] if dates else None,
    }


def _coverage_label(minimum: Any, maximum: Any) -> str:
    minimum_text = _normalize_text(minimum)
    maximum_text = _normalize_text(maximum)
    if minimum_text and maximum_text:
        return minimum_text if minimum_text == maximum_text else f"{minimum_text}-{maximum_text}"
    return minimum_text or maximum_text or "unknown"


def _dataset_metadata(
    *,
    source_profile: Mapping[str, Any],
    selected_profile: Mapping[str, Any],
) -> dict[str, Any]:
    full_source_rows = list(source_profile.get("rows") or [])
    selected_source_rows = list(selected_profile.get("rows") or [])
    full_date_coverage = dict(source_profile.get("date_coverage") or {}) or _date_coverage_from_rows(full_source_rows)
    full_season_coverage = dict(source_profile.get("season_coverage") or {}) or _season_coverage_from_rows(full_source_rows)
    selected_date_coverage = dict(selected_profile.get("date_coverage") or {}) or _date_coverage_from_rows(selected_source_rows)
    selected_season_coverage = dict(selected_profile.get("season_coverage") or {}) or _season_coverage_from_rows(selected_source_rows)
    return {
        "dataset_id": ODDSWAREHOUSE_NFL_BASIC_DATASET_ID,
        "dataset_alias": ODDSWAREHOUSE_NFL_BASIC_DATASET_ALIAS,
        "dataset_version": ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
        "dataset_revision": ODDSWAREHOUSE_NFL_BASIC_DATASET_REVISION,
        "report_catalog_name": "oddswarehouse_nfl_basic_historical",
        "full_source_date_coverage": full_date_coverage,
        "full_source_season_coverage": full_season_coverage,
        "selected_date_coverage": selected_date_coverage,
        "selected_season_coverage": selected_season_coverage,
        "full_source_date_label": _coverage_label(full_date_coverage.get("min"), full_date_coverage.get("max")),
        "full_source_season_label": _coverage_label(full_season_coverage.get("min"), full_season_coverage.get("max")),
        "selected_date_label": _coverage_label(selected_date_coverage.get("min"), selected_date_coverage.get("max")),
        "selected_season_label": _coverage_label(selected_season_coverage.get("min"), selected_season_coverage.get("max")),
    }


def _selected_source_profile(
    profile: Mapping[str, Any],
    *,
    selected_rows: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    source = dict(profile.get("source") or {})
    selected_dates = sorted(
        _normalize_text(row.get("Date"))
        for row in selected_rows
        if _normalize_text(row.get("Date"))
    )
    return {
        **dict(profile),
        "full_source": dict(source),
        "source": {
            **source,
            "rows": [dict(row) for row in selected_rows],
            "logical_data_row_count": int(selection.get("selected_row_count") or 0),
            "selected_row_count": int(selection.get("selected_row_count") or 0),
            "available_row_count": int(selection.get("available_row_count") or 0),
            "selection_rule": selection.get("selection_rule"),
            "original_logical_data_row_count": source.get("logical_data_row_count"),
            "date_coverage": {
                "min": min(selected_dates, default=""),
                "max": max(selected_dates, default=""),
            },
            "season_coverage": _season_coverage_from_rows(selected_rows),
            "invalid_rows": [dict(row) for row in selection.get("encountered_invalid_rows") or []],
            "duplicate_header_rows": [dict(row) for row in selection.get("encountered_duplicate_header_rows") or []],
        },
        "selection": dict(selection),
    }


def _existing_batch_state(storage_path: Path, batch_id: str) -> dict[str, Any]:
    if not storage_path.exists():
        return {
            "batch_exists": False,
            "batch_row": {},
        }
    store = create_local_storage_engine(storage_path, auto_initialize=False)
    try:
        batch_rows = store.fetch(
            "historical_acquisition_batches",
            where="batch_id = ?",
            params=[batch_id],
            limit=1,
        )
    except Exception:
        return {
            "batch_exists": False,
            "batch_row": {},
        }
    finally:
        store.close()
    return {
        "batch_exists": bool(batch_rows),
        "batch_row": dict(batch_rows[0]) if batch_rows else {},
    }


def _rejected_source_event_ids(
    validation: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
) -> list[str]:
    return [
        _normalize_text(item.get("source_event_id"))
        for item in validation.get("rejected_rows") or []
    ] + [
        _normalize_text(item.get("source_event_id"))
        for item in normalized_payload.get("quarantined_rows") or []
    ]


def _current_batch_summary(
    *,
    normalized_payload: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, int]:
    rejected_source_event_ids = _rejected_source_event_ids(validation, normalized_payload)
    return {
        "event_count": len(normalized_payload.get("event_rows") or []),
        "market_count": len(normalized_payload.get("market_rows") or []),
        "selection_count": len(normalized_payload.get("selection_rows") or []),
        "certified_row_count": len(normalized_payload.get("gold_rows") or []),
        "rejected_row_count": len([item for item in rejected_source_event_ids if item]),
    }


def _should_resume_incomplete_publication(
    *,
    prior_publication_state: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> bool:
    if not prior_publication_state.get("batch_exists"):
        return False
    batch_row = dict(prior_publication_state.get("batch_row") or {})
    if not batch_row:
        return False
    current_summary = _current_batch_summary(
        normalized_payload=normalized_payload,
        validation=validation,
    )
    return any(
        int(batch_row.get(field_name) or 0) != expected_value
        for field_name, expected_value in current_summary.items()
    )


def _resume_publication_tokens(
    *,
    batch_id: str,
    source_bundle_id: str,
) -> tuple[str, ...]:
    tokens = [
        _normalize_text(batch_id),
        _normalize_text(source_bundle_id),
    ]
    return tuple(token for token in dict.fromkeys(tokens) if token)


def _report_row_preview(
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    fields: Sequence[str] = ("Game ID", "Date", "Away Team", "Home Team"),
    limit: int = 5,
) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    for row in list(rows or [])[: max(0, int(limit))]:
        preview.append({field: row.get(field) for field in fields if field in row})
    return preview


def _report_safe_source_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(profile)
    payload["row_preview"] = _report_row_preview(profile.get("rows") or [])
    payload["invalid_row_preview"] = _report_row_preview(profile.get("invalid_rows") or [])
    payload["duplicate_header_row_preview"] = _report_row_preview(profile.get("duplicate_header_rows") or [])
    payload["row_preview_count"] = len(payload["row_preview"])
    payload["invalid_row_count"] = len(profile.get("invalid_rows") or [])
    payload["duplicate_header_row_count"] = len(profile.get("duplicate_header_rows") or [])
    payload.pop("rows", None)
    payload.pop("cells", None)
    payload.pop("invalid_rows", None)
    payload.pop("duplicate_header_rows", None)
    return payload


def _report_safe_validation(validation: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(validation)
    accepted_rows = list(validation.get("accepted_rows") or [])
    rejected_rows = list(validation.get("rejected_rows") or [])
    payload["accepted_row_preview"] = _report_row_preview(accepted_rows)
    payload["rejected_row_preview"] = [
        {
            "source_event_id": _normalize_text(row.get("source_event_id")),
            "game_id": _normalize_text(row.get("Game ID")),
            "errors": list(row.get("errors") or []),
        }
        for row in rejected_rows[:5]
    ]
    payload["accepted_row_count"] = len(accepted_rows)
    payload["rejected_row_count"] = len(rejected_rows)
    payload.pop("accepted_rows", None)
    payload.pop("rejected_rows", None)
    payload.pop("row_results", None)
    return payload


def _report_safe_source_bundle(source_bundle: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source_bundle)
    source_tables = dict(payload.get("source_tables") or {})
    payload["source_tables"] = {
        "file_artifacts": len(source_tables.get("file_artifacts") or []),
        "source_rows": len(source_tables.get("source_rows") or []),
        "source_cells": len(source_tables.get("source_cells") or []),
        "csv_evidence": len(source_tables.get("csv_evidence") or []),
    }
    return payload


def _report_safe_raw_acquisition_result(raw_acquisition_result: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(raw_acquisition_result)
    payload["source_bundle"] = _report_safe_source_bundle(raw_acquisition_result.get("source_bundle") or {})
    payload["raw_record_preview"] = [
        {
            "record_id": row.get("record_id"),
            "dataset_id": row.get("dataset_id"),
            "row_index": row.get("row_index"),
        }
        for row in list(raw_acquisition_result.get("raw_records") or [])[:5]
    ]
    payload["lineage_edge_count"] = len(raw_acquisition_result.get("lineage_edges") or [])
    payload.pop("raw_records", None)
    payload.pop("lineage_edges", None)
    validation = raw_acquisition_result.get("validation")
    if isinstance(validation, Mapping):
        payload["validation"] = _report_safe_validation(validation)
    return payload


def _report_safe_source_row_classifications(source_row_classifications: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source_row_classifications)
    rows = list(source_row_classifications.get("rows") or [])
    payload["row_count"] = len(rows)
    payload["row_preview"] = rows[:20]
    payload.pop("rows", None)
    return payload


def _report_safe_identity_runtime(identity_runtime: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(identity_runtime)
    seed_result = dict(identity_runtime.get("seed_result") or {})
    reconciliation_result = dict(identity_runtime.get("reconciliation_result") or {})
    lakehouse_result = dict(identity_runtime.get("lakehouse_result") or {})
    publication_scope = dict(identity_runtime.get("publication_scope") or {})
    payload["seed_summary"] = {
        "ok": bool(seed_result.get("ok", True)),
        "mapping_count": len(seed_result.get("mappings") or []),
        "mapping_request_count": int(seed_result.get("mapping_request_count") or 0),
        "identity_mapping_count": int(seed_result.get("identity_mapping_count") or 0),
    }
    payload["reconciliation_summary"] = {
        "ok": bool(reconciliation_result.get("ok", True)),
        "reconciliation_result_count": int(reconciliation_result.get("reconciliation_result_count") or 0),
        "selection_row_count": int(reconciliation_result.get("selection_row_count") or 0),
    }
    payload["lakehouse_result"] = {
        "ok": bool(lakehouse_result.get("ok", True)),
        "created_partition_count": int(lakehouse_result.get("created_partition_count") or 0),
        "updated_partition_count": int(lakehouse_result.get("updated_partition_count") or 0),
        "reused_partition_count": int(lakehouse_result.get("reused_partition_count") or 0),
        "created_partition_ids": list(lakehouse_result.get("created_partition_ids") or [])[:20],
        "updated_partition_ids": list(lakehouse_result.get("updated_partition_ids") or [])[:20],
        "reused_partition_ids": list(lakehouse_result.get("reused_partition_ids") or [])[:20],
    }
    payload["publication_scope"] = {}
    for table_name, table_scope in publication_scope.items():
        if isinstance(table_scope, Mapping):
            payload["publication_scope"][str(table_name)] = {
                "layer_name": table_scope.get("layer_name"),
                "row_count": int(table_scope.get("row_count") or 0),
                "affected_partition_count": len(table_scope.get("affected_partition_ids") or []),
                "affected_partition_ids": list(table_scope.get("affected_partition_ids") or [])[:20],
            }
            continue
        payload["publication_scope"][str(table_name)] = int(table_scope or 0)
    payload.pop("seed_result", None)
    payload.pop("reconciliation_result", None)
    return payload


def _report_safe_certification_results(certification_results: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(certification_results)
    asset_results = list(certification_results.get("asset_results") or [])
    payload["asset_result_count"] = len(asset_results)
    payload["asset_result_summaries"] = [
        {
            "ok": bool(result.get("ok", True)),
            "research_asset_id": dict(result.get("asset_contract") or {}).get("research_asset_id"),
            "research_asset_name": dict(result.get("asset_contract") or {}).get("research_asset_name"),
            "source_table_name": dict(result.get("asset_contract") or {}).get("source_table_name"),
            "certification_id": dict(result.get("research_asset_certification") or {}).get("certification_id"),
            "certification_status": dict(result.get("research_asset_certification") or {}).get("certification_status"),
            "valid_row_count": dict(result.get("research_asset_certification") or {}).get("valid_row_count"),
            "invalid_row_count": dict(result.get("research_asset_certification") or {}).get("invalid_row_count"),
            "coverage_score": dict(result.get("research_asset_certification") or {}).get("coverage_score"),
            "certification_score": dict(result.get("research_asset_certification") or {}).get("certification_score"),
        }
        for result in asset_results
    ]
    payload.pop("asset_results", None)
    return payload


def _report_safe_lifecycle_results(lifecycle_results: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(lifecycle_results)
    lifecycle_rows = list(lifecycle_results.get("lifecycle_rows") or [])
    payload["lifecycle_row_count"] = len(lifecycle_rows)
    payload["lifecycle_row_preview"] = [
        {
            "asset_id": row.get("asset_id"),
            "asset_type": row.get("asset_type"),
            "lifecycle_state": row.get("lifecycle_state"),
            "lifecycle_reason": row.get("lifecycle_reason"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        for row in lifecycle_rows[:20]
    ]
    payload.pop("lifecycle_rows", None)
    return payload


def _write_ingest_report(report: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    if isinstance(payload.get("source_profile"), Mapping):
        payload["source_profile"] = _report_safe_source_profile(payload["source_profile"])
    if isinstance(payload.get("companion_evidence_profile"), Mapping):
        payload["companion_evidence_profile"] = _report_safe_source_profile(payload["companion_evidence_profile"])
    if isinstance(payload.get("validation"), Mapping):
        payload["validation"] = _report_safe_validation(payload["validation"])
    if isinstance(payload.get("raw_acquisition_result"), Mapping):
        payload["raw_acquisition_result"] = _report_safe_raw_acquisition_result(payload["raw_acquisition_result"])
    if isinstance(payload.get("source_row_classifications"), Mapping):
        payload["source_row_classifications"] = _report_safe_source_row_classifications(payload["source_row_classifications"])
    if isinstance(payload.get("identity_runtime"), Mapping):
        payload["identity_runtime"] = _report_safe_identity_runtime(payload["identity_runtime"])
    if isinstance(payload.get("certification_results"), Mapping):
        payload["certification_results"] = _report_safe_certification_results(payload["certification_results"])
    if isinstance(payload.get("lifecycle_results"), Mapping):
        payload["lifecycle_results"] = _report_safe_lifecycle_results(payload["lifecycle_results"])
    ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    run_token = _normalize_text(payload.get("run_id"))
    acquisition_token = _normalize_text(payload.get("acquisition_id"))
    report_token = run_token or acquisition_token
    if not report_token:
        report_token = _stable_id(
            "oddswarehouse_report",
            payload.get("source_path"),
            payload.get("failure_stage"),
            payload.get("failure_type"),
        )
    report_path = ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT / f"{report_token}.json"
    payload["report_path"] = str(report_path)
    payload["run_report_path"] = str(report_path)
    if acquisition_token:
        acquisition_report_path = ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT / f"{acquisition_token}.json"
        payload["acquisition_report_path"] = str(acquisition_report_path)
        payload["latest_report_path"] = str(acquisition_report_path)
    else:
        payload["acquisition_report_path"] = None
        payload["latest_report_path"] = str(report_path)
    report_path.write_text(_as_json(payload), encoding="utf-8")
    if acquisition_token:
        acquisition_report_path.write_text(_as_json(payload), encoding="utf-8")
    return payload


def _report_replay_status(
    *,
    counts: Mapping[str, Any],
    publication_committed: bool,
    prior_publication_exists: bool,
    prior_incomplete_detected: bool,
    reuse_without_publication: bool = False,
) -> str:
    if reuse_without_publication:
        return "reused" if prior_publication_exists else "duplicate_rejected"
    if not publication_committed:
        return "failed_before_publication"
    if int(counts.get("CONFLICT") or 0) > 0:
        return "conflict"
    if prior_incomplete_detected:
        return "resumed"
    if int(counts.get("NEW") or 0) > 0:
        return "created"
    if prior_publication_exists:
        return "reused"
    return "duplicate_rejected"


def _derive_partial_state(
    *,
    prior_publication_exists: bool,
    raw_acquisition_result: Mapping[str, Any],
    bronze_actions: Sequence[Mapping[str, Any]],
    resume_publication: bool = False,
) -> tuple[bool, str]:
    if prior_publication_exists and not resume_publication:
        return (False, "")
    actions: list[str] = []
    if resume_publication:
        actions.append("resumed_incomplete_batch_publication")
    if raw_acquisition_result.get("status") != "raw_cache_reused":
        return (bool(actions), ",".join(actions))
    reuse_match_type = _normalize_text(raw_acquisition_result.get("reuse_match_type"))
    if reuse_match_type not in {"source_bundle_id", "legacy_source_bundle_id"}:
        return (bool(actions), ",".join(actions))
    if any(action.get("status") == "reused" for action in bronze_actions):
        actions.append("reused_bronze_artifacts")
    suffix = f":{reuse_match_type}" if reuse_match_type else ""
    actions.append(f"reused_raw_acquisition_cache{suffix}")
    return (True, ",".join(actions))


def _provider_capability(schema_headers: Sequence[str]) -> dict[str, Any]:
    return {
        "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        "provider_name": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_NAME,
        "provider_role": "controlled_vendor_historical",
        "connector_id": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
        "connector_name": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_NAME,
        "connector_family": "manual_import",
        "source_id": ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY,
        "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
        "source_family": "odds_data",
        "source_access_type": "manual_import",
        "supported_assets": [
            ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID,
            ODDSWAREHOUSE_NFL_BASIC_MARKET_OBSERVATIONS_ASSET_ID,
            ODDSWAREHOUSE_NFL_BASIC_GOLD_ASSET_ID,
        ],
        "supported_fields": list(schema_headers),
        "supported_markets": ["sports:nfl", "spread", "moneyline", "total"],
        "historical_depth": "historical",
        "update_frequency": "manual / governed historical file import",
        "point_in_time_safe": True,
        "licensing_notes": (
            "Controlled historical import from a manually supplied file bundle. "
            "Sportsbook identity and methodology remain unknown in the source evidence."
        ),
        "cost_class": "manual_import",
        "certification_readiness": "historical_ready",
        "quality_score": 0.9,
        "quality_tier": "approved_manual_import",
        "source_aliases": [ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID, "oddwarehouse"],
        "verification_provider_ids": ["authoritative_workbook"],
        "fallback_provider_ids": ["manual_review"],
        "contract_version": ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _xlsx_col_to_index(token: str) -> int:
    value = 0
    for character in token:
        value = value * 26 + (ord(character.upper()) - 64)
    return value - 1


def _safe_float(value: Any) -> float:
    parsed = _normalize_float(value, 0.0)
    return float(parsed if parsed is not None else 0.0)


def _parse_xlsx_workbook(path: Path) -> dict[str, Any]:
    workbook_report: dict[str, Any] = {
        "sheet_names": [],
        "sheets": {},
    }
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        workbook_rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in workbook_rels.findall("rel:Relationship", XML_NAMESPACES)
        }
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", XML_NAMESPACES):
                shared_strings.append(
                    "".join(text_node.text or "" for text_node in item.iterfind(".//a:t", XML_NAMESPACES))
                )

        sheet_nodes = workbook.find("a:sheets", XML_NAMESPACES)
        if sheet_nodes is None:
            return workbook_report
        for sheet_node in sheet_nodes.findall("a:sheet", XML_NAMESPACES):
            sheet_name = sheet_node.attrib["name"]
            workbook_report["sheet_names"].append(sheet_name)
            rel_id = sheet_node.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            sheet_target = rel_map[rel_id].replace("\\", "/")
            sheet_root = ET.fromstring(archive.read(f"xl/{sheet_target}"))
            rows: list[list[str]] = []
            cells: list[dict[str, Any]] = []
            max_cols = 0
            for row_node in sheet_root.findall(".//a:sheetData/a:row", XML_NAMESPACES):
                row_number = int(row_node.attrib.get("r", "0") or 0)
                row_map: dict[int, str] = {}
                for cell_node in row_node.findall("a:c", XML_NAMESPACES):
                    ref = cell_node.attrib.get("r", "")
                    match = re.match(r"([A-Z]+)(\d+)", ref)
                    if not match:
                        continue
                    col_index = _xlsx_col_to_index(match.group(1))
                    cell_type = cell_node.attrib.get("t", "")
                    value_node = cell_node.find("a:v", XML_NAMESPACES)
                    value = value_node.text if value_node is not None and value_node.text is not None else ""
                    if cell_type == "s" and value:
                        value = shared_strings[int(value)]
                    elif cell_type == "inlineStr":
                        value = "".join(
                            text_node.text or ""
                            for text_node in cell_node.iterfind(".//a:t", XML_NAMESPACES)
                        )
                    elif value:
                        try:
                            numeric = float(value)
                            value = str(int(numeric)) if numeric.is_integer() else str(numeric)
                        except (TypeError, ValueError):
                            value = _normalize_text(value)
                    row_map[col_index] = value
                    cells.append(
                        {
                            "sheet_name": sheet_name,
                            "row_number": row_number,
                            "column_number": col_index + 1,
                            "cell_reference": ref,
                            "cell_value": value,
                        }
                    )
                if row_map:
                    max_cols = max(max_cols, max(row_map) + 1)
                    rows.append([row_map.get(index, "") for index in range(max(row_map) + 1)])
            padded_rows = [row + [""] * (max_cols - len(row)) for row in rows]
            header = padded_rows[0] if padded_rows else []
            data_rows = [row for row in padded_rows[1:] if any(_normalize_text(cell) for cell in row)]
            workbook_report["sheets"][sheet_name] = {
                "physical_row_count_including_header": len(rows),
                "logical_data_row_count": len(data_rows),
                "physical_column_count": max_cols,
                "logical_column_count": len(header),
                "header": header,
                "rows": data_rows,
                "cells": cells,
            }
    return workbook_report


def _source_format_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return "xlsx"
    if suffix == ".csv":
        return "csv"
    raise ValueError(f"Unsupported OddsWarehouse source format: {path.suffix or '<none>'}")


def _row_dicts_from_matrix(
    rows: Sequence[Sequence[str]],
    header: Sequence[str],
    *,
    source_format: str,
) -> list[dict[str, Any]]:
    row_dicts: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=2):
        payload = {
            header[index]: row[index]
            for index in range(min(len(header), len(row)))
        }
        payload["_source_format"] = source_format
        payload["_physical_row_number"] = row_index
        row_dicts.append(payload)
    return row_dicts


def _profile_companion_csv_evidence(path: Path) -> dict[str, Any]:
    csv_text = path.read_text(encoding="utf-8", errors="replace")
    csv_lines = csv_text.splitlines()
    parsed_csv = list(csv.reader(csv_lines))
    csv_header = parsed_csv[0] if parsed_csv else []
    csv_drift_examples: list[dict[str, Any]] = []
    for index, row in enumerate(parsed_csv[1:6], start=2):
        if len(row) != len(EXPECTED_HEADERS):
            csv_drift_examples.append(
                {
                    "line_number": index,
                    "field_count": len(row),
                    "leading_fields": row[:15],
                }
            )
    return {
        "path": str(path),
        "line_count": len(csv_lines),
        "parsed_row_count_including_header": len(parsed_csv),
        "header_field_count": len(csv_header),
        "field_count_first_ten_rows": [len(row) for row in parsed_csv[:10]],
        "header_tokens": csv_header,
        "drift_examples": csv_drift_examples,
        "raw_preview": csv_lines[:3],
        "contains_split_multiword_headers": any(
            token in {"Game", "Away", "Spread", "Open", "MoneyLine", "Close", "Home", "Under"}
            for token in csv_header
        ),
        "schema_fingerprint": _stable_digest(csv_header, [len(row) for row in parsed_csv[:10]]),
    }


def _profile_canonical_csv_source(path: Path) -> dict[str, Any]:
    csv_text = path.read_text(encoding="utf-8", errors="replace")
    csv_lines = csv_text.splitlines()
    parsed_csv = list(csv.reader(csv_lines))
    header = parsed_csv[0] if parsed_csv else []
    data_rows: list[list[str]] = []
    row_dicts: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(parsed_csv[1:], start=2):
        if not any(_normalize_text(cell) for cell in row):
            continue
        if len(row) != len(EXPECTED_HEADERS):
            invalid_rows.append(
                {
                    "line_number": index,
                    "field_count": len(row),
                    "leading_fields": row[:15],
                }
            )
            continue
        data_rows.append(row)
        row_dicts.append(
            {
                header[column_index]: row[column_index]
                for column_index in range(min(len(header), len(row)))
            }
            | {
                "_source_format": "csv",
                "_physical_row_number": index,
            }
        )
    inferred_types = _infer_workbook_types(data_rows, header)
    team_names = sorted(
        {
            _normalize_text(row[2])
            for row in data_rows
            if len(row) >= 15
        }
        | {
            _normalize_text(row[14])
            for row in data_rows
            if len(row) >= 15
        }
    )
    duplicate_game_ids = sorted(
        game_id
        for game_id, count in Counter(_normalize_text(row[0]) for row in data_rows if row).items()
        if count > 1
    )
    duplicate_matchups = sorted(
        matchup
        for matchup, count in Counter(
            "|".join([_normalize_text(row[1]), _normalize_text(row[2]), _normalize_text(row[14])])
            for row in data_rows
            if len(row) >= 15
        ).items()
        if count > 1
    )
    return {
        "path": str(path),
        "format": "csv",
        "logical_data_row_count": len(data_rows),
        "physical_row_count_including_header": len(parsed_csv),
        "logical_column_count": len(header),
        "physical_column_count": max((len(row) for row in parsed_csv), default=0),
        "headers": header,
        "rows": row_dicts,
        "inferred_types": inferred_types,
        "date_coverage": {
            "min": min((_normalize_text(row.get("Date")) for row in row_dicts), default=""),
            "max": max((_normalize_text(row.get("Date")) for row in row_dicts), default=""),
        },
        "duplicate_game_ids": duplicate_game_ids,
        "duplicate_matchups": duplicate_matchups,
        "null_counts": _null_counts(data_rows, header),
        "team_names": team_names,
        "schema_fingerprint": _stable_digest(header, [row["inferred_type"] for row in inferred_types]),
        "invalid_rows": invalid_rows,
        "line_count": len(csv_lines),
    }


def _profile_oddswarehouse_source(
    source_path: str | Path,
    *,
    companion_evidence_path: str | Path | None = None,
) -> dict[str, Any]:
    source_file = Path(source_path).expanduser().resolve()
    source_format = _source_format_for_path(source_file)
    if source_format == "xlsx":
        workbook_profile = _parse_xlsx_workbook(source_file)
        sheet_payload = workbook_profile["sheets"].get(ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET, {})
        header = list(sheet_payload.get("header") or [])
        rows = list(sheet_payload.get("rows") or [])
        inferred_types = _infer_workbook_types(rows, header)
        row_dicts = _row_dicts_from_matrix(rows, header, source_format="xlsx")
        source_profile = {
            "path": str(source_file),
            "format": "xlsx",
            "sheet_names": workbook_profile["sheet_names"],
            "sheet_name": ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET,
            "physical_row_count_including_header": sheet_payload.get("physical_row_count_including_header", 0),
            "logical_data_row_count": sheet_payload.get("logical_data_row_count", 0),
            "physical_column_count": sheet_payload.get("physical_column_count", 0),
            "logical_column_count": sheet_payload.get("logical_column_count", 0),
            "headers": header,
            "rows": row_dicts,
            "cells": sheet_payload.get("cells", []),
            "inferred_types": inferred_types,
            "date_coverage": {
                "min": min((_normalize_text(row.get("Date")) for row in row_dicts), default=""),
                "max": max((_normalize_text(row.get("Date")) for row in row_dicts), default=""),
            },
            "duplicate_game_ids": sorted(
                game_id
                for game_id, count in Counter(_normalize_text(row[0]) for row in rows if row).items()
                if count > 1
            ),
            "duplicate_matchups": sorted(
                matchup
                for matchup, count in Counter(
                    "|".join([_normalize_text(row[1]), _normalize_text(row[2]), _normalize_text(row[14])])
                    for row in rows
                    if len(row) >= 15
                ).items()
                if count > 1
            ),
            "null_counts": _null_counts(rows, header),
            "team_names": sorted(
                {
                    _normalize_text(row[2])
                    for row in rows
                    if len(row) >= 15
                }
                | {
                    _normalize_text(row[14])
                    for row in rows
                    if len(row) >= 15
                }
            ),
            "schema_fingerprint": _stable_digest(header, [row["inferred_type"] for row in inferred_types]),
        }
    else:
        source_profile = _profile_canonical_csv_source(source_file)

    companion_profile = {}
    files = {
        source_file.name: {
            "filename": source_file.name,
            "size_bytes": source_file.stat().st_size,
            "sha256": _sha256(source_file),
            "format": source_format,
            "source_role": "primary_source",
        }
    }
    if companion_evidence_path is not None:
        companion_file = Path(companion_evidence_path).expanduser().resolve()
        companion_profile = _profile_companion_csv_evidence(companion_file)
        files[companion_file.name] = {
            "filename": companion_file.name,
            "size_bytes": companion_file.stat().st_size,
            "sha256": _sha256(companion_file),
            "format": "csv",
            "source_role": "companion_evidence",
        }
    return {
        "files": files,
        "source": source_profile,
        "companion_evidence": companion_profile,
    }


def _row_repeats_source_header(row: Mapping[str, Any], headers: Sequence[str]) -> bool:
    return bool(headers) and all(_normalize_text(row.get(header)) == header for header in headers)


def _apply_deterministic_row_limit(
    rows_or_source: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    limit: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    normalized_limit = int(limit) if limit is not None else None
    if normalized_limit is not None and normalized_limit < 1:
        raise ValueError("--limit must be a positive integer")

    if isinstance(rows_or_source, Mapping):
        source = dict(rows_or_source)
        rows = [dict(row) for row in source.get("rows") or []]
        headers = list(source.get("headers") or EXPECTED_HEADERS)
        invalid_rows = [dict(row) for row in source.get("invalid_rows") or []]
        physical_row_count = int(source.get("physical_row_count_including_header") or 0)
    else:
        source = {}
        rows = [dict(row) for row in rows_or_source]
        headers = list(EXPECTED_HEADERS)
        invalid_rows = []
        physical_row_count = 0

    selected_rows: list[dict[str, Any]] = []
    duplicate_header_rows: list[dict[str, Any]] = []
    for row in rows:
        if _row_repeats_source_header(row, headers):
            duplicate_header_rows.append(
                {
                    "line_number": int(row.get("_physical_row_number") or 0),
                    "field_count": len(headers),
                }
            )
            continue
        selected_rows.append(dict(row))
        if normalized_limit is not None and len(selected_rows) >= normalized_limit:
            break

    selected_physical_cutoff = max(
        (
            int(row.get("_physical_row_number") or 0)
            for row in selected_rows
        ),
        default=max((int(row.get("line_number") or 0) for row in duplicate_header_rows), default=1),
    )
    if normalized_limit is None and physical_row_count > 0:
        selected_physical_cutoff = max(selected_physical_cutoff, physical_row_count)
    encountered_invalid_rows = [
        dict(row)
        for row in invalid_rows
        if int(row.get("line_number") or 0) <= selected_physical_cutoff
    ]
    encountered_duplicate_header_rows = [
        dict(row)
        for row in duplicate_header_rows
        if int(row.get("line_number") or 0) <= selected_physical_cutoff
    ]
    inspected_physical_row_count = max(0, selected_physical_cutoff - 1) if selected_physical_cutoff else 0

    return selected_rows, {
        "selection_rule": f"first_valid_rows:{normalized_limit}" if normalized_limit is not None else "all_valid_rows",
        "available_row_count": len(rows),
        "selected_row_count": len(selected_rows),
        "limit": normalized_limit,
        "inspected_physical_row_count": inspected_physical_row_count,
        "selected_physical_cutoff": selected_physical_cutoff,
        "skipped_invalid_row_count": len(encountered_invalid_rows),
        "skipped_duplicate_header_row_count": len(encountered_duplicate_header_rows),
        "encountered_invalid_rows": encountered_invalid_rows,
        "encountered_duplicate_header_rows": encountered_duplicate_header_rows,
    }


def _infer_workbook_types(rows: Sequence[Sequence[str]], header: Sequence[str]) -> list[dict[str, Any]]:
    inferred: list[dict[str, Any]] = []
    for index, column_name in enumerate(header):
        values = [
            row[index]
            for row in rows
            if index < len(row) and _normalize_text(row[index])
        ]
        inferred_type = "empty"
        if values:
            is_int = True
            is_float = True
            for value in values:
                try:
                    numeric = float(value)
                    if not numeric.is_integer():
                        is_int = False
                except (TypeError, ValueError):
                    is_int = False
                    is_float = False
                    break
            if is_int:
                inferred_type = "int"
            elif is_float:
                inferred_type = "float"
            else:
                inferred_type = "string"
        inferred.append(
            {
                "index": index + 1,
                "header": column_name,
                "inferred_type": inferred_type,
            }
        )
    return inferred


def _null_counts(rows: Sequence[Sequence[str]], header: Sequence[str]) -> list[dict[str, Any]]:
    return [
        {
            "index": index + 1,
            "header": column_name,
            "null_count": sum(
                1
                for row in rows
                if index >= len(row) or not _normalize_text(row[index])
            ),
        }
        for index, column_name in enumerate(header)
    ]


def profile_oddswarehouse_nfl_basic_inputs(
    workbook_path: str | Path,
    csv_path: str | Path,
) -> dict[str, Any]:
    workbook_file = Path(workbook_path).expanduser().resolve()
    csv_file = Path(csv_path).expanduser().resolve()
    workbook_profile = _parse_xlsx_workbook(workbook_file)
    sheet_payload = workbook_profile["sheets"].get(ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET, {})
    header = list(sheet_payload.get("header") or [])
    rows = list(sheet_payload.get("rows") or [])
    workbook_types = _infer_workbook_types(rows, header)
    workbook_schema_fingerprint = _stable_digest(
        header,
        [row["inferred_type"] for row in workbook_types],
    )
    csv_text = csv_file.read_text(encoding="utf-8", errors="replace")
    csv_lines = csv_text.splitlines()
    parsed_csv = list(csv.reader(csv_lines))
    csv_header = parsed_csv[0] if parsed_csv else []
    csv_drift_examples: list[dict[str, Any]] = []
    for index, row in enumerate(parsed_csv[1:6], start=2):
        if len(row) != len(EXPECTED_HEADERS):
            csv_drift_examples.append(
                {
                    "line_number": index,
                    "field_count": len(row),
                    "leading_fields": row[:15],
                }
            )
    team_names = sorted(
        {
            _normalize_text(row[2])
            for row in rows
            if len(row) >= 15
        }
        | {
            _normalize_text(row[14])
            for row in rows
            if len(row) >= 15
        }
    )
    duplicate_game_ids = sorted(
        game_id
        for game_id, count in Counter(_normalize_text(row[0]) for row in rows if row).items()
        if count > 1
    )
    duplicate_matchups = sorted(
        matchup
        for matchup, count in Counter(
            "|".join([_normalize_text(row[1]), _normalize_text(row[2]), _normalize_text(row[14])])
            for row in rows
            if len(row) >= 15
        ).items()
        if count > 1
    )
    workbook_rows = [
        {
            header[index]: row[index]
            for index in range(min(len(header), len(row)))
        }
        | {
            "_sheet_name": ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET,
            "_physical_row_number": row_index + 2,
        }
        for row_index, row in enumerate(rows)
    ]
    return {
        "files": {
            workbook_file.name: {
                "filename": workbook_file.name,
                "size_bytes": workbook_file.stat().st_size,
                "sha256": _sha256(workbook_file),
            },
            csv_file.name: {
                "filename": csv_file.name,
                "size_bytes": csv_file.stat().st_size,
                "sha256": _sha256(csv_file),
            },
        },
        "workbook": {
            "path": str(workbook_file),
            "sheet_names": workbook_profile["sheet_names"],
            "sheet_name": ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET,
            "physical_row_count_including_header": sheet_payload.get("physical_row_count_including_header", 0),
            "logical_data_row_count": sheet_payload.get("logical_data_row_count", 0),
            "physical_column_count": sheet_payload.get("physical_column_count", 0),
            "logical_column_count": sheet_payload.get("logical_column_count", 0),
            "headers": header,
            "rows": workbook_rows,
            "cells": sheet_payload.get("cells", []),
            "inferred_types": workbook_types,
            "date_coverage": {
                "min": min((_normalize_text(row.get("Date")) for row in workbook_rows), default=""),
                "max": max((_normalize_text(row.get("Date")) for row in workbook_rows), default=""),
            },
            "duplicate_game_ids": duplicate_game_ids,
            "duplicate_matchups": duplicate_matchups,
            "null_counts": _null_counts(rows, header),
            "team_names": team_names,
            "schema_fingerprint": workbook_schema_fingerprint,
        },
        "csv": {
            "path": str(csv_file),
            "line_count": len(csv_lines),
            "parsed_row_count_including_header": len(parsed_csv),
            "header_field_count": len(csv_header),
            "field_count_first_ten_rows": [len(row) for row in parsed_csv[:10]],
            "header_tokens": csv_header,
            "drift_examples": csv_drift_examples,
            "raw_preview": csv_lines[:3],
            "contains_split_multiword_headers": any(
                token in {"Game", "Away", "Spread", "Open", "MoneyLine", "Close", "Home", "Under"}
                for token in csv_header
            ),
            "schema_fingerprint": _stable_digest(csv_header, [len(row) for row in parsed_csv[:10]]),
        },
    }


def validate_oddswarehouse_workbook_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    workbook = dict(profile.get("workbook") or {})
    rows = [dict(row) for row in workbook.get("rows") or []]
    errors: list[str] = []
    warnings: list[str] = []
    row_results: list[dict[str, Any]] = []

    if tuple(workbook.get("headers") or ()) != EXPECTED_HEADERS:
        errors.append("schema_headers_mismatch")
    if int(workbook.get("logical_data_row_count") or 0) != 30:
        warnings.append("pilot_row_count_differs_from_expected_30")
    if int(workbook.get("logical_column_count") or 0) != 26:
        errors.append("schema_column_count_mismatch")
    if workbook.get("sheet_name") != ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET:
        errors.append("unexpected_sheet_name")

    seen_event_keys: set[str] = set()
    duplicate_event_keys: set[str] = set()
    seen_market_selection_stage: set[str] = set()
    duplicate_market_selection_stage: set[str] = set()

    for row in rows:
        row_errors: list[str] = []
        game_id = _normalize_text(row.get("Game ID"))
        date_value = _normalize_text(row.get("Date"))
        away_team = _normalize_text(row.get("Away Team"))
        home_team = _normalize_text(row.get("Home Team"))
        if not game_id:
            row_errors.append("missing_game_id")
        if not re.fullmatch(r"\d{8}", date_value):
            row_errors.append("invalid_date_format")
        if not away_team or not home_team:
            row_errors.append("missing_team_name")
        if away_team == home_team and away_team:
            row_errors.append("same_team_both_sides")
        away_score = _normalize_int(row.get("Away Score"))
        home_score = _normalize_int(row.get("Home Score"))
        if away_score is None or away_score < 0:
            row_errors.append("invalid_away_score")
        if home_score is None or home_score < 0:
            row_errors.append("invalid_home_score")
        numeric_fields = (
            "Away Spread Open",
            "Away Spread Open Odds",
            "Away Spread Close",
            "Away Spread Close Odds",
            "Away MoneyLine Open",
            "Away MoneyLine Close",
            "Over Open",
            "Over Open Odds",
            "Over Close",
            "Over Close Odds",
            "Home Spread Open",
            "Home Spread Open Odds",
            "Home Spread Close",
            "Home Spread Close Odds",
            "Home MoneyLine Open",
            "Home MoneyLine Close",
            "Under Open",
            "Under Open Odds",
            "Under Close",
            "Under Close Odds",
        )
        for field_name in numeric_fields:
            if _normalize_numeric_source_value(field_name, row.get(field_name), None) is None:
                row_errors.append(f"non_numeric_{field_name}")
        american_fields = (
            "Away Spread Open Odds",
            "Away Spread Close Odds",
            "Away MoneyLine Open",
            "Away MoneyLine Close",
            "Over Open Odds",
            "Over Close Odds",
            "Home Spread Open Odds",
            "Home Spread Close Odds",
            "Home MoneyLine Open",
            "Home MoneyLine Close",
            "Under Open Odds",
            "Under Close Odds",
        )
        for field_name in american_fields:
            odds_value = _normalize_int(row.get(field_name))
            if odds_value == 0:
                row_errors.append(f"zero_american_odds_{field_name}")
        spread_open_sum = round(
            float(_normalize_oddswarehouse_spread_value(row.get("Away Spread Open"), 0.0) or 0.0)
            + float(_normalize_oddswarehouse_spread_value(row.get("Home Spread Open"), 0.0) or 0.0),
            6,
        )
        spread_close_sum = round(
            float(_normalize_oddswarehouse_spread_value(row.get("Away Spread Close"), 0.0) or 0.0)
            + float(_normalize_oddswarehouse_spread_value(row.get("Home Spread Close"), 0.0) or 0.0),
            6,
        )
        if spread_open_sum != 0:
            row_errors.append("spread_open_not_symmetric")
        if spread_close_sum != 0:
            row_errors.append("spread_close_not_symmetric")
        if round(_safe_float(row.get("Over Open")) - _safe_float(row.get("Under Open")), 6) != 0:
            row_errors.append("total_open_not_symmetric")
        if round(_safe_float(row.get("Over Close")) - _safe_float(row.get("Under Close")), 6) != 0:
            row_errors.append("total_close_not_symmetric")

        event_key = f"{date_value}|{away_team}|{home_team}"
        if event_key in seen_event_keys:
            duplicate_event_keys.add(event_key)
        seen_event_keys.add(event_key)
        for market_type, selection_labels in {
            "spread": ("away", "home"),
            "moneyline": ("away", "home"),
            "total": ("over", "under"),
        }.items():
            for source_stage in ("OPEN", "CLOSE"):
                for selection_label in selection_labels:
                    duplicate_key = f"{event_key}|{market_type}|{selection_label}|{source_stage}"
                    if duplicate_key in seen_market_selection_stage:
                        duplicate_market_selection_stage.add(duplicate_key)
                    seen_market_selection_stage.add(duplicate_key)

        row_results.append(
            {
                "game_id": game_id,
                "ok": not row_errors,
                "errors": row_errors,
            }
        )

    if duplicate_event_keys:
        errors.append("duplicate_canonical_event_mapping")
    if duplicate_market_selection_stage:
        errors.append("duplicate_market_selection_stage")

    csv_profile = dict(profile.get("csv") or {})
    if int(csv_profile.get("header_field_count") or 0) != 71:
        warnings.append("csv_header_field_count_differs_from_expected_71")

    return {
        "ok": not errors and all(row["ok"] for row in row_results),
        "status": "validated" if not errors and all(row["ok"] for row in row_results) else "blocked",
        "errors": errors,
        "warnings": warnings,
        "row_results": row_results,
        "duplicate_event_keys": sorted(duplicate_event_keys),
        "duplicate_market_selection_stage": sorted(duplicate_market_selection_stage),
        "validated_row_count": len(row_results),
    }


def validate_oddswarehouse_source_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    source = dict(profile.get("source") or {})
    rows = [dict(row) for row in source.get("rows") or []]
    errors: list[str] = []
    warnings: list[str] = []
    row_results: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    if tuple(source.get("headers") or ()) != EXPECTED_HEADERS:
        errors.append("schema_headers_mismatch")
    if int(source.get("logical_column_count") or 0) != len(EXPECTED_HEADERS):
        errors.append("schema_column_count_mismatch")
    if source.get("format") == "xlsx" and source.get("sheet_name") != ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET:
        errors.append("unexpected_sheet_name")
    original_row_count = int(source.get("original_logical_data_row_count") or source.get("logical_data_row_count") or 0)
    if source.get("format") == "xlsx" and original_row_count != 30:
        warnings.append("pilot_row_count_differs_from_expected_30")
    if source.get("format") == "csv" and list(source.get("invalid_rows") or []):
        warnings.append("csv_row_field_count_mismatch")

    seen_event_keys: set[str] = set()
    duplicate_event_keys: set[str] = set()
    seen_market_selection_stage: set[str] = set()
    duplicate_market_selection_stage: set[str] = set()

    for row in rows:
        row_errors: list[str] = []
        game_id = _normalize_text(row.get("Game ID"))
        date_value = _normalize_text(row.get("Date"))
        away_team = _normalize_text(row.get("Away Team"))
        home_team = _normalize_text(row.get("Home Team"))
        if not game_id:
            row_errors.append("missing_game_id")
        if not re.fullmatch(r"\d{8}", date_value):
            row_errors.append("invalid_date_format")
        if not away_team or not home_team:
            row_errors.append("missing_team_name")
        if away_team == home_team and away_team:
            row_errors.append("same_team_both_sides")
        away_score = _normalize_int(row.get("Away Score"))
        home_score = _normalize_int(row.get("Home Score"))
        if away_score is None or away_score < 0:
            row_errors.append("invalid_away_score")
        if home_score is None or home_score < 0:
            row_errors.append("invalid_home_score")
        numeric_fields = (
            "Away Spread Open",
            "Away Spread Open Odds",
            "Away Spread Close",
            "Away Spread Close Odds",
            "Away MoneyLine Open",
            "Away MoneyLine Close",
            "Over Open",
            "Over Open Odds",
            "Over Close",
            "Over Close Odds",
            "Home Spread Open",
            "Home Spread Open Odds",
            "Home Spread Close",
            "Home Spread Close Odds",
            "Home MoneyLine Open",
            "Home MoneyLine Close",
            "Under Open",
            "Under Open Odds",
            "Under Close",
            "Under Close Odds",
        )
        for field_name in numeric_fields:
            if _normalize_numeric_source_value(field_name, row.get(field_name), None) is None:
                row_errors.append(f"non_numeric_{field_name}")
        american_fields = (
            "Away Spread Open Odds",
            "Away Spread Close Odds",
            "Away MoneyLine Open",
            "Away MoneyLine Close",
            "Over Open Odds",
            "Over Close Odds",
            "Home Spread Open Odds",
            "Home Spread Close Odds",
            "Home MoneyLine Open",
            "Home MoneyLine Close",
            "Under Open Odds",
            "Under Close Odds",
        )
        for field_name in american_fields:
            odds_value = _normalize_int(row.get(field_name))
            if odds_value == 0:
                row_errors.append(f"zero_american_odds_{field_name}")
        spread_open_sum = round(
            float(_normalize_oddswarehouse_spread_value(row.get("Away Spread Open"), 0.0) or 0.0)
            + float(_normalize_oddswarehouse_spread_value(row.get("Home Spread Open"), 0.0) or 0.0),
            6,
        )
        spread_close_sum = round(
            float(_normalize_oddswarehouse_spread_value(row.get("Away Spread Close"), 0.0) or 0.0)
            + float(_normalize_oddswarehouse_spread_value(row.get("Home Spread Close"), 0.0) or 0.0),
            6,
        )
        if spread_open_sum != 0:
            row_errors.append("spread_open_not_symmetric")
        if spread_close_sum != 0:
            row_errors.append("spread_close_not_symmetric")
        if round(_safe_float(row.get("Over Open")) - _safe_float(row.get("Under Open")), 6) != 0:
            row_errors.append("total_open_not_symmetric")
        if round(_safe_float(row.get("Over Close")) - _safe_float(row.get("Under Close")), 6) != 0:
            row_errors.append("total_close_not_symmetric")

        if not row_errors:
            away_team_resolved = _resolve_team_mapping(away_team, date_value)
            home_team_resolved = _resolve_team_mapping(home_team, date_value)
            if away_team and away_team_resolved is None:
                row_errors.append("unresolved_away_team_mapping")
            if home_team and home_team_resolved is None:
                row_errors.append("unresolved_home_team_mapping")
            _, _, _, week_error = _season_context_for_date(date_value)
            if week_error is not None:
                row_errors.append(f"week_resolution:{week_error}")

        event_key = f"{date_value}|{away_team}|{home_team}"
        if event_key in seen_event_keys:
            duplicate_event_keys.add(event_key)
        seen_event_keys.add(event_key)
        for market_type, selection_labels in {
            "spread": ("away", "home"),
            "moneyline": ("away", "home"),
            "total": ("over", "under"),
        }.items():
            for source_stage in ("OPEN", "CLOSE"):
                for selection_label in selection_labels:
                    duplicate_key = f"{event_key}|{market_type}|{selection_label}|{source_stage}"
                    if duplicate_key in seen_market_selection_stage:
                        duplicate_market_selection_stage.add(duplicate_key)
                    seen_market_selection_stage.add(duplicate_key)

        row_results.append(
            {
                "game_id": game_id,
                "source_event_id": _source_event_scope_from_row(row),
                "physical_row_number": int(row.get("_physical_row_number") or 0),
                "ok": not row_errors,
                "errors": row_errors,
            }
        )
        if row_errors:
            rejected_rows.append(
                {
                    "source_event_id": _source_event_scope_from_row(row),
                    "physical_row_number": int(row.get("_physical_row_number") or 0),
                    "errors": list(row_errors),
                    "row": dict(row),
                }
            )
            continue
        accepted_rows.append(dict(row))

    if duplicate_event_keys:
        errors.append("duplicate_canonical_event_mapping")
    if duplicate_market_selection_stage:
        errors.append("duplicate_market_selection_stage")
    if not rows:
        errors.append("no_rows_selected")
    if not accepted_rows:
        errors.append("no_valid_rows_selected")

    companion_profile = dict(profile.get("companion_evidence") or {})
    if companion_profile and int(companion_profile.get("header_field_count") or 0) != 71:
        warnings.append("companion_csv_header_field_count_differs_from_expected_71")

    return {
        "ok": not errors,
        "status": "validated" if not errors else "blocked",
        "errors": errors,
        "warnings": warnings,
        "row_results": row_results,
        "accepted_rows": accepted_rows,
        "rejected_rows": rejected_rows,
        "duplicate_event_keys": sorted(duplicate_event_keys),
        "duplicate_market_selection_stage": sorted(duplicate_market_selection_stage),
        "selected_row_count": len(rows),
        "validated_row_count": len(accepted_rows),
        "rejected_row_count": len(rejected_rows),
    }


def _bronze_raw_dir(artifact_id: str) -> Path:
    return _bronze_raw_dir_for_root(artifact_id, ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT)


def _bounded_artifact_token(artifact_id: str) -> str:
    token = _normalize_text(artifact_id).rsplit(".", 1)[-1]
    if not token:
        token = _stable_digest("bronze.raw.artifact", artifact_id)[:16]
    return token[:16]


def _bronze_raw_dir_for_root(artifact_id: str, bronze_raw_root: str | Path) -> Path:
    return (
        Path(bronze_raw_root)
        / f"provider={ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID}"
        / "league=nfl"
        / f"season={ODDSWAREHOUSE_NFL_BASIC_LEGACY_BRONZE_SEASON}"
        / f"product={ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID}"
        / f"a={_bounded_artifact_token(artifact_id)}"
    )


def _bronze_target_name(
    *,
    source_role: str,
    source_format: str,
    source_path: Path,
) -> str:
    extension = source_path.suffix.lstrip(".").lower() or _normalize_text(source_format, "bin").lower()
    return f"{_normalize_text(source_role, 'source').lower()}.{extension}"


def _copy_bronze_artifacts(
    artifact_id: str,
    source_artifacts: Sequence[Mapping[str, Any]],
    *,
    bronze_raw_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    output_dir = _bronze_raw_dir_for_root(artifact_id, bronze_raw_root or ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT)
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_paths: list[dict[str, Any]] = []
    for artifact in source_artifacts:
        source_path = Path(str(artifact.get("source_path") or "")).expanduser().resolve()
        source_role = _normalize_text(artifact.get("source_role"), "source")
        source_format = _normalize_text(artifact.get("source_format"), source_path.suffix.lstrip("."))
        target_path = output_dir / _bronze_target_name(
            source_role=source_role,
            source_format=source_format,
            source_path=source_path,
        )
        source_sha256 = _sha256(source_path)
        target_exists = target_path.exists()
        target_sha256 = _sha256(target_path) if target_exists else None
        if not target_exists or target_sha256 != source_sha256:
            shutil.copy2(source_path, target_path)
        copied_paths.append(
            {
                "source_path": str(source_path),
                "target_path": str(target_path),
                "sha256": source_sha256,
                "source_role": source_role,
                "source_format": source_format,
                "source_file_name": source_path.name,
                "status": "reused" if target_exists and target_sha256 == source_sha256 else "created",
            }
        )
    return copied_paths


def _copy_bronze_files(
    artifact_id: str,
    workbook_path: Path,
    csv_path: Path,
    *,
    bronze_raw_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    return _copy_bronze_artifacts(
        artifact_id,
        [
            {"source_path": workbook_path, "source_role": "primary_source", "source_format": workbook_path.suffix.lstrip(".")},
            {"source_path": csv_path, "source_role": "companion_evidence", "source_format": csv_path.suffix.lstrip(".")},
        ],
        bronze_raw_root=bronze_raw_root,
    )


def _source_bundle_from_source_profile(
    profile: Mapping[str, Any],
    source_bundle_id: str,
    acquired_at: str,
    *,
    acquisition_id: str = "",
    batch_id: str = "",
) -> dict[str, Any]:
    source = dict(profile.get("source") or {})
    companion_profile = dict(profile.get("companion_evidence") or {})
    source_rows = [dict(row) for row in source.get("rows") or []]
    source_cells = [
        {
            "sheet_name": cell.get("sheet_name"),
            "row_number": cell.get("row_number"),
            "column_number": cell.get("column_number"),
            "cell_reference": cell.get("cell_reference"),
            "cell_value": cell.get("cell_value"),
        }
        for cell in source.get("cells") or []
        if _normalize_text(cell.get("cell_value")) or cell.get("row_number") == 1
    ]
    file_artifacts = [
        {
            "file_name": file_name,
            "file_sha256": file_info["sha256"],
            "size_bytes": file_info["size_bytes"],
            "source_role": file_info.get("source_role"),
            "validation_status": "eligible_for_normalization" if file_info.get("source_role") == "primary_source" else "malformed_schema",
            "normalization_status": "allowed" if file_info.get("source_role") == "primary_source" else "blocked",
            "quarantine_reason": (
                ""
                if file_info.get("source_role") == "primary_source"
                else "unquoted multiword headers and team names produce positional column drift"
            ),
            "schema_fingerprint": (
                source.get("schema_fingerprint")
                if file_info.get("source_role") == "primary_source"
                else companion_profile.get("schema_fingerprint")
            ),
            "source_format": file_info.get("format"),
        }
        for file_name, file_info in (profile.get("files") or {}).items()
    ]
    csv_evidence = [
        {
            "evidence_id": f"csv_evidence_{index:02d}",
            "evidence_type": "malformed_csv_preview",
            "field_count": example.get("field_count"),
            "line_number": example.get("line_number"),
            "leading_fields_json": _as_json(example.get("leading_fields") or []),
        }
        for index, example in enumerate(companion_profile.get("drift_examples") or [], start=1)
    ]
    return {
        "dataset_id": "dataset.sports.nfl.oddswarehouse.raw_acquisition_cache",
        "dataset_version": ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
        "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
        "source_type": ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE,
        "source_key": ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY,
        "provider": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        "provider_sources": [ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME],
        "provider_versions": [ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION],
        "source_bundle_id": source_bundle_id,
        "acquisition_id": _normalize_text(acquisition_id),
        "batch_id": _normalize_text(batch_id or acquisition_id),
        "acquisition_timestamp": acquired_at,
        "connector_id": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
        "connector_name": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_NAME,
        "connector_role": "controlled_manual_import",
        "execution_mode": "manual_bounded_ingest",
        "provider_role": "controlled_vendor_historical",
        "source_family": "odds_data",
        "source_access_type": "manual_import",
        "provider_capability": _provider_capability(source.get("headers") or EXPECTED_HEADERS),
        "source_tables": {
            "file_artifacts": file_artifacts,
            "source_rows": source_rows,
            "source_cells": source_cells,
            "csv_evidence": csv_evidence,
        },
    }


def _paired_no_vig_probability(first_odds: int, second_odds: int, first_side: str) -> float | None:
    try:
        fair = remove_two_way_vig(
            american_to_implied_probability(first_odds),
            american_to_implied_probability(second_odds),
        )
    except Exception:
        return None
    if first_side == "a":
        return fair["fair_probability_a"]
    return fair["fair_probability_b"]


def _selection_result(
    *,
    market_type: str,
    selection_side: str,
    team_score: int | None,
    opponent_score: int | None,
    line_value: float | None,
    total_points: int | None,
) -> tuple[str, float | None]:
    if team_score is None or opponent_score is None or total_points is None:
        return ("unknown", None)
    if market_type == "moneyline":
        margin = float(team_score - opponent_score)
        if margin > 0:
            return ("win", margin)
        return ("loss", margin)
    if market_type == "spread":
        adjusted_margin = float(team_score - opponent_score) + float(line_value or 0.0)
        if adjusted_margin > 0:
            return ("win", adjusted_margin)
        if adjusted_margin < 0:
            return ("loss", adjusted_margin)
        return ("push", adjusted_margin)
    if market_type == "total":
        target = float(line_value or 0.0)
        margin = float(total_points) - target
        if selection_side == "under":
            margin = -margin
        if margin > 0:
            return ("win", margin)
        if margin < 0:
            return ("loss", margin)
        return ("push", margin)
    return ("unknown", None)


def _source_event_scope_from_row(row: Mapping[str, Any]) -> str:
    return f"{ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID}|{ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID}|{_normalize_text(row.get('Game ID'))}"

def _classification_count_template() -> dict[str, int]:
    return {
        "NEW": 0,
        "EXACT_DUPLICATE": 0,
        "SEMANTIC_REUSE": 0,
        "REVISION": 0,
        "CONFLICT": 0,
        "REJECTED": 0,
    }


def _row_key(row: Mapping[str, Any], key_columns: Sequence[str]) -> tuple[Any, ...]:
    return tuple(row.get(column) for column in key_columns)


def _filtered_table_rows(
    store: LocalStorageEngine,
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    columns = set(store.table_columns(table_name))
    return [
        {
            str(key): value
            for key, value in dict(row).items()
            if str(key) in columns
        }
        for row in rows
    ]


def _fetch_existing_rows_by_key(
    store: LocalStorageEngine,
    table_name: str,
    filtered_rows: Sequence[Mapping[str, Any]],
    *,
    key_columns: Sequence[str],
    chunk_size: int = 200,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    keys = []
    seen_keys: set[tuple[Any, ...]] = set()
    for row in filtered_rows:
        key = _row_key(row, key_columns)
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        keys.append(key)
    if not keys:
        return {}
    existing_lookup: dict[tuple[Any, ...], dict[str, Any]] = {}
    for start in range(0, len(keys), chunk_size):
        chunk = keys[start : start + chunk_size]
        if len(key_columns) == 1:
            where = f"{key_columns[0]} IN ({', '.join('?' for _ in chunk)})"
            params = [key[0] for key in chunk]
        else:
            clauses: list[str] = []
            params = []
            for key in chunk:
                clauses.append("(" + " AND ".join(f"{column} = ?" for column in key_columns) + ")")
                params.extend(key)
            where = " OR ".join(clauses)
        for existing_row in store.fetch(table_name, where=where, params=params):
            existing_lookup[_row_key(existing_row, key_columns)] = dict(existing_row)
    return existing_lookup


def _classify_rows_against_store(
    store: LocalStorageEngine,
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    key_columns: Sequence[str],
    progress: _StageProgressTracker | None = None,
    progress_offset: int = 0,
    progress_total: int | None = None,
) -> dict[str, Any]:
    filtered_rows = _filtered_table_rows(store, table_name, rows)
    existing_lookup = _fetch_existing_rows_by_key(
        store,
        table_name,
        filtered_rows,
        key_columns=key_columns,
    )
    counts = _classification_count_template()
    source_event_statuses: dict[str, list[str]] = defaultdict(list)
    compatibility_diagnostics: list[dict[str, Any]] = []
    rows_to_write: list[dict[str, Any]] = []
    expected_canonical_delta = {
        "new": 0,
        "reused": 0,
        "revised": 0,
        "conflicted": 0,
    }
    total_rows = len(filtered_rows)
    for index, filtered in enumerate(filtered_rows, start=1):
        existing_row = existing_lookup.get(_row_key(filtered, key_columns))
        diagnostic_classification = ""
        if existing_row is None:
            classification = "NEW"
            compatibility = {
                "decision": "NEW_PUBLICATION",
                "differences": [],
                "semantic_difference_fields": [],
                "metadata_difference_fields": [],
            }
            rows_to_write.append(filtered)
            expected_canonical_delta["new"] += 1
        elif table_name == "historical_acquisition_batches":
            if dict(existing_row) == dict(filtered):
                classification = "EXACT_DUPLICATE"
                compatibility = {
                    "decision": SEMANTIC_REUSE,
                    "differences": [],
                    "semantic_difference_fields": [],
                    "metadata_difference_fields": [],
                }
                expected_canonical_delta["reused"] += 1
            else:
                classification = "REVISION"
                compatibility = {
                    "decision": GOVERNED_REVISION,
                    "differences": [],
                    "semantic_difference_fields": [],
                    "metadata_difference_fields": [],
                }
                rows_to_write.append(filtered)
                expected_canonical_delta["revised"] += 1
        else:
            compatibility = compare_historical_canonical_rows(
                existing_row,
                filtered,
                policy=DEFAULT_HISTORICAL_STAGE_COMPATIBILITY_POLICY,
            )
            if compatibility["decision"] == SEMANTIC_REUSE:
                classification = "EXACT_DUPLICATE"
                if compatibility.get("differences"):
                    counts["SEMANTIC_REUSE"] += 1
                    diagnostic_classification = "SEMANTIC_REUSE"
                expected_canonical_delta["reused"] += 1
            elif compatibility["decision"] == GOVERNED_REVISION:
                classification = "REVISION"
                rows_to_write.append(filtered)
                expected_canonical_delta["revised"] += 1
            else:
                classification = "CONFLICT"
                expected_canonical_delta["conflicted"] += 1
        counts[classification] += 1
        source_event_statuses[_normalize_text(filtered.get("source_event_id"))].append(classification)
        if classification in {"EXACT_DUPLICATE", "REVISION", "CONFLICT"} or diagnostic_classification:
            compatibility_diagnostics.append(
                {
                    "table_name": table_name,
                    "key": {column: filtered.get(column) for column in key_columns},
                    "classification": diagnostic_classification or classification,
                    "decision": compatibility.get("decision"),
                    "differences": list(compatibility.get("differences") or []),
                }
            )
        if progress is not None:
            progress.update(
                rows_processed=progress_offset + index,
                rows_total=progress_total if progress_total is not None else total_rows,
            )
    return {
        "table_name": table_name,
        "counts": counts,
        "source_event_statuses": source_event_statuses,
        "compatibility_diagnostics": compatibility_diagnostics,
        "rows_to_write": rows_to_write,
        "expected_canonical_delta": expected_canonical_delta,
    }


def _persist_classification_plan(
    store: LocalStorageEngine,
    plan: Mapping[str, Any],
    *,
    key_columns: Sequence[str],
) -> None:
    rows_to_write = [dict(row) for row in plan.get("rows_to_write") or []]
    if not rows_to_write:
        return
    with store.transaction():
        for row in rows_to_write:
            store.upsert(plan["table_name"], row, key_columns=key_columns)


def _persist_classified_rows(
    store: LocalStorageEngine,
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    key_columns: Sequence[str],
) -> dict[str, Any]:
    plan = _classify_rows_against_store(
        store,
        table_name,
        rows,
        key_columns=key_columns,
    )
    _persist_classification_plan(store, plan, key_columns=key_columns)
    return plan


def _stage_base(
    *,
    stage_name: str,
    batch_id: str,
    source_file: str,
    source_event_id: str = "",
    source_market_id: str = "",
    source_selection_id: str = "",
    source_snapshot_time: str = "",
    snapshot_time: str = "",
    decision_time: str = "",
    created_at: str,
    point_in_time_status: str,
    leakage_status: str = "none",
    certification_status: str = "certified",
    status: str = "certified",
    completeness_score: float = 1.0,
    quality_score: float = 1.0,
    context: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
    market_type: str = "",
) -> dict[str, Any]:
    effective_market_type = market_type or stage_name
    snapshot_id = _stable_id(
        "snapshot",
        stage_name,
        batch_id,
        source_event_id,
        source_market_id,
        source_selection_id,
        effective_market_type,
    )
    lineage_id = _stable_id(
        "lineage",
        stage_name,
        batch_id,
        source_event_id,
        source_market_id,
        source_selection_id,
        effective_market_type,
    )
    return {
        "dataset_id": f"dataset.sports.nfl.oddswarehouse.{stage_name}",
        "dataset_name": stage_name,
        "market_profile": ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
        "profile_id": ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
        "profile_family": "sports",
        "stage_name": stage_name,
        "batch_id": batch_id,
        "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
        "source_type": ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE,
        "source_key": ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY,
        "source_file": source_file,
        "source_event_id": source_event_id,
        "source_market_id": source_market_id,
        "source_selection_id": source_selection_id,
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "certified_at": created_at,
        "certification_status": certification_status,
        "point_in_time_status": point_in_time_status,
        "leakage_status": leakage_status,
        "status": status,
        "completeness_score": completeness_score,
        "source_metadata_json": _as_json(
            {
                "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                "provider_name": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_NAME,
                "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
                "source_stage_precision": "stage_only",
                "sportsbook_status": "unknown",
                "market_source_methodology_status": "unknown",
            }
        ),
        "context_json": _as_json(dict(context or {})),
        "payload_json": _as_json(dict(payload or {})),
        "schema_version": ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
        "created_at": created_at,
        "updated_at": created_at,
        "source": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
        "provider": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        "market": ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
        "market_type": effective_market_type,
        "asset_class": "historical",
        "snapshot_id": snapshot_id,
        "lineage_id": lineage_id,
        "version_id": ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
        "quality_score": quality_score,
    }


def normalize_oddswarehouse_workbook_rows(
    workbook_rows: Sequence[Mapping[str, Any]],
    *,
    batch_id: str,
    created_at: str,
    source_file: str,
) -> dict[str, Any]:
    event_rows: list[dict[str, Any]] = []
    participant_rows: list[dict[str, Any]] = []
    event_link_rows: list[dict[str, Any]] = []
    market_rows: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    gold_rows: list[dict[str, Any]] = []
    team_mappings: list[dict[str, Any]] = []
    unresolved_mappings: list[str] = []
    quarantined_rows: list[dict[str, Any]] = []

    for workbook_row in workbook_rows:
        source_game_id = _normalize_text(workbook_row.get("Game ID"))
        source_date = _normalize_text(workbook_row.get("Date"))
        away_source_name = _normalize_text(workbook_row.get("Away Team"))
        home_source_name = _normalize_text(workbook_row.get("Home Team"))
        source_event_scope = f"{ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID}|{ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID}|{source_game_id}"
        away_mapping = _resolve_team_mapping(away_source_name, source_date)
        home_mapping = _resolve_team_mapping(home_source_name, source_date)
        if away_mapping is None:
            unresolved_mappings.append(away_source_name)
            quarantined_rows.append(
                {
                    "source_event_id": source_event_scope,
                    "game_id": source_game_id,
                    "physical_row_number": int(workbook_row.get("_physical_row_number") or 0),
                    "reason": "unresolved_away_team_mapping",
                    "external_identifier": away_source_name,
                }
            )
            continue
        if home_mapping is None:
            unresolved_mappings.append(home_source_name)
            quarantined_rows.append(
                {
                    "source_event_id": source_event_scope,
                    "game_id": source_game_id,
                    "physical_row_number": int(workbook_row.get("_physical_row_number") or 0),
                    "reason": "unresolved_home_team_mapping",
                    "external_identifier": home_source_name,
                }
            )
            continue
        resolved_season, season_type, week, week_error = _season_context_for_date(source_date)
        if resolved_season is None or season_type is None or week is None:
            quarantined_rows.append(
                {
                    "source_event_id": source_event_scope,
                    "game_id": source_game_id,
                    "physical_row_number": int(workbook_row.get("_physical_row_number") or 0),
                    "reason": f"week_resolution:{week_error or 'unresolved'}",
                    "external_identifier": source_date,
                }
            )
            continue
        event_date = _date_from_source(source_date)
        event_id = _stable_id(
            "historical_event",
            "NFL",
            resolved_season,
            event_date,
            away_mapping.team_id,
            home_mapping.team_id,
        )
        home_score = _normalize_int(workbook_row.get("Home Score"))
        away_score = _normalize_int(workbook_row.get("Away Score"))
        total_points = None if home_score is None or away_score is None else home_score + away_score
        margin = None if home_score is None or away_score is None else home_score - away_score
        winner_mapping = home_mapping if (margin or 0) > 0 else away_mapping
        loser_mapping = away_mapping if winner_mapping is home_mapping else home_mapping
        event_context = {
            "source_event_scope": source_event_scope,
            "event_date_precision": "date_only",
            "kickoff_time_available": False,
            "home_team_source_name": home_source_name,
            "away_team_source_name": away_source_name,
        }
        event_rows.append(
            {
                **_stage_base(
                    stage_name="historical_events",
                    batch_id=batch_id,
                    source_file=source_file,
                    source_event_id=source_event_scope,
                    created_at=created_at,
                    point_in_time_status="date_only_source_event",
                    context=event_context,
                    payload=workbook_row,
                    market_type="event",
                ),
                "event_id": event_id,
                "event_key": f"NFL|{event_date}|{away_mapping.team_id}|{home_mapping.team_id}",
                "sport": "football",
                "league": "NFL",
                "season": resolved_season,
                "season_type": season_type,
                "week": week,
                "game_id": source_game_id,
                "event_date": event_date,
                "event_start_time": "",
                "event_time_precision": "date_only",
                "event_start_time_status": "unavailable_from_source",
                "home_team_id": home_mapping.team_id,
                "home_team": home_mapping.historical_display_name,
                "home_team_source_name": home_source_name,
                "away_team_id": away_mapping.team_id,
                "away_team": away_mapping.historical_display_name,
                "away_team_source_name": away_source_name,
                "venue_id": "",
                "venue_name": "",
                "venue_city": "",
                "venue_state": "",
                "neutral_site": 0,
                "final_result": "home_win" if winner_mapping is home_mapping else "away_win",
                "final_score_home": home_score,
                "final_score_away": away_score,
                "winner_team": winner_mapping.historical_display_name,
                "margin": margin,
                "total_points": total_points,
                "result_recorded_time": "",
                "result_status": "final_score_present",
                "settlement_status": "settled",
            }
        )
        for mapping, role, source_name in (
            (home_mapping, "home", home_source_name),
            (away_mapping, "away", away_source_name),
        ):
            participant_rows.append(
                {
                    **_stage_base(
                        stage_name="historical_event_participants",
                        batch_id=batch_id,
                        source_file=source_file,
                        source_event_id=source_event_scope,
                        created_at=created_at,
                        point_in_time_status="date_only_source_event",
                        context={"event_id": event_id, "team_role": role},
                        payload=workbook_row,
                        market_type="event_participant",
                    ),
                    "participant_id": _stable_id("event_participant", event_id, mapping.team_id, role),
                    "event_id": event_id,
                    "season": resolved_season,
                    "league": "NFL",
                    "event_date": event_date,
                    "team_id": mapping.team_id,
                    "franchise_id": mapping.franchise_id,
                    "team_role": role,
                    "source_team_name": source_name,
                    "historical_display_name": mapping.historical_display_name,
                    "effective_date": event_date,
                    "mapping_confidence": 1.0,
                    "approval_status": "approved",
                    "mapping_version": ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
                }
            )
            team_mappings.append(
                {
                    "source_name": source_name,
                    "team_id": mapping.team_id,
                    "franchise_id": mapping.franchise_id,
                    "historical_display_name": mapping.historical_display_name,
                    "valid_from": mapping.effective_start,
                    "valid_to": mapping.effective_end,
                    "effective_date": event_date,
                    "mapping_confidence": 100.0,
                    "approval_status": "approved",
                    "mapping_version": ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
                }
            )
        event_link_rows.append(
            {
                **_stage_base(
                    stage_name="historical_source_event_links",
                    batch_id=batch_id,
                    source_file=source_file,
                    source_event_id=source_event_scope,
                    created_at=created_at,
                    point_in_time_status="date_only_source_event",
                    context={"event_id": event_id},
                    payload=workbook_row,
                    market_type="source_event_link",
                ),
                "link_id": _stable_id("source_event_link", source_event_scope, event_id),
                "event_id": event_id,
                "season": resolved_season,
                "league": "NFL",
                "event_date": event_date,
                "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
                "link_scope": "provider_id+product_id+source_game_id",
                "match_method": "exact_composite_identity",
                "mapping_confidence": 1.0,
                "approval_status": "approved",
            }
        )

        paired_probabilities: dict[tuple[str, str], tuple[float | None, float | None]] = {}
        paired_probabilities[("spread", "OPEN")] = (
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away Spread Open Odds"))),
                int(_safe_float(workbook_row.get("Home Spread Open Odds"))),
                "a",
            ),
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away Spread Open Odds"))),
                int(_safe_float(workbook_row.get("Home Spread Open Odds"))),
                "b",
            ),
        )
        paired_probabilities[("spread", "CLOSE")] = (
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away Spread Close Odds"))),
                int(_safe_float(workbook_row.get("Home Spread Close Odds"))),
                "a",
            ),
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away Spread Close Odds"))),
                int(_safe_float(workbook_row.get("Home Spread Close Odds"))),
                "b",
            ),
        )
        paired_probabilities[("moneyline", "OPEN")] = (
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away MoneyLine Open"))),
                int(_safe_float(workbook_row.get("Home MoneyLine Open"))),
                "a",
            ),
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away MoneyLine Open"))),
                int(_safe_float(workbook_row.get("Home MoneyLine Open"))),
                "b",
            ),
        )
        paired_probabilities[("moneyline", "CLOSE")] = (
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away MoneyLine Close"))),
                int(_safe_float(workbook_row.get("Home MoneyLine Close"))),
                "a",
            ),
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Away MoneyLine Close"))),
                int(_safe_float(workbook_row.get("Home MoneyLine Close"))),
                "b",
            ),
        )
        paired_probabilities[("total", "OPEN")] = (
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Over Open Odds"))),
                int(_safe_float(workbook_row.get("Under Open Odds"))),
                "a",
            ),
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Over Open Odds"))),
                int(_safe_float(workbook_row.get("Under Open Odds"))),
                "b",
            ),
        )
        paired_probabilities[("total", "CLOSE")] = (
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Over Close Odds"))),
                int(_safe_float(workbook_row.get("Under Close Odds"))),
                "a",
            ),
            _paired_no_vig_probability(
                int(_safe_float(workbook_row.get("Over Close Odds"))),
                int(_safe_float(workbook_row.get("Under Close Odds"))),
                "b",
            ),
        )

        market_stage_rows: dict[tuple[str, str], dict[str, Any]] = {}
        gold_candidates: dict[tuple[str, str], dict[str, Any]] = {}
        for market_type, stage_fields in {
            "spread": {
                "OPEN": (
                    ("away", away_mapping, "Away Spread Open", "Away Spread Open Odds"),
                    ("home", home_mapping, "Home Spread Open", "Home Spread Open Odds"),
                ),
                "CLOSE": (
                    ("away", away_mapping, "Away Spread Close", "Away Spread Close Odds"),
                    ("home", home_mapping, "Home Spread Close", "Home Spread Close Odds"),
                ),
            },
            "moneyline": {
                "OPEN": (
                    ("away", away_mapping, None, "Away MoneyLine Open"),
                    ("home", home_mapping, None, "Home MoneyLine Open"),
                ),
                "CLOSE": (
                    ("away", away_mapping, None, "Away MoneyLine Close"),
                    ("home", home_mapping, None, "Home MoneyLine Close"),
                ),
            },
            "total": {
                "OPEN": (
                    ("over", None, "Over Open", "Over Open Odds"),
                    ("under", None, "Under Open", "Under Open Odds"),
                ),
                "CLOSE": (
                    ("over", None, "Over Close", "Over Close Odds"),
                    ("under", None, "Under Close", "Under Close Odds"),
                ),
            },
        }.items():
            for source_stage, selection_specs in stage_fields.items():
                if market_type == "spread":
                    market_line_value = abs(
                        float(_normalize_oddswarehouse_spread_value(workbook_row.get(selection_specs[0][2]), 0.0) or 0.0)
                    )
                elif market_type == "total":
                    market_line_value = _safe_float(workbook_row.get(selection_specs[0][2]))
                else:
                    market_line_value = None
                market_id = _stable_id("historical_market", event_id, market_type, source_stage)
                market_row = {
                    **_stage_base(
                        stage_name="historical_markets",
                        batch_id=batch_id,
                        source_file=source_file,
                        source_event_id=source_event_scope,
                        source_market_id=f"{source_event_scope}|{market_type}|{source_stage}",
                        created_at=created_at,
                        point_in_time_status="stage_only_vendor_observation",
                        context={"event_id": event_id, "market_type": market_type, "source_stage": source_stage},
                        payload=workbook_row,
                        market_type=market_type,
                    ),
                    "market_id": market_id,
                    "event_id": event_id,
                    "event_start_time": "",
                    "event_time_precision": "date_only",
                    "market_family": market_type,
                    "market_type": market_type,
                    "market_name": market_type,
                    "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
                    "book": "unknown",
                    "sportsbook_id": "",
                    "sportsbook_status": "unknown",
                    "line_value": market_line_value,
                    "odds": None,
                    "american_odds": None,
                    "implied_probability": None,
                    "opening_odds": None,
                    "closing_odds": None,
                    "price_type": "american",
                    "market_label": f"{market_type}_{source_stage.lower()}",
                    "selection_count": 2,
                    "source_stage": source_stage,
                    "observed_at": "",
                    "observation_time_precision": "stage_only",
                    "available_at": "",
                    "available_at_precision": "unknown",
                    "market_source_methodology": "",
                    "market_source_status": "unknown",
                }
                market_rows.append(market_row)
                market_stage_rows[(market_type, source_stage)] = market_row
                for selection_index, (selection_side, mapping, line_field, odds_field) in enumerate(selection_specs):
                    line_value = _normalize_numeric_source_value(line_field, workbook_row.get(line_field), None) if line_field else None
                    american_odds = int(_safe_float(workbook_row.get(odds_field)))
                    implied_probability = american_to_implied_probability(american_odds)
                    paired_index = 0 if selection_index == 0 else 1
                    no_vig_probability = paired_probabilities[(market_type, source_stage)][paired_index]
                    selection_name = (
                        "Over"
                        if selection_side == "over"
                        else "Under"
                        if selection_side == "under"
                        else mapping.historical_display_name
                    )
                    team_score = (
                        away_score if selection_side == "away" else home_score if selection_side == "home" else None
                    )
                    opponent_score = (
                        home_score if selection_side == "away" else away_score if selection_side == "home" else None
                    )
                    selection_result, result_margin = _selection_result(
                        market_type=market_type,
                        selection_side=selection_side,
                        team_score=team_score,
                        opponent_score=opponent_score,
                        line_value=line_value,
                        total_points=total_points,
                    )
                    selection_id = _stable_id(
                        "historical_selection",
                        event_id,
                        market_type,
                        selection_side,
                        source_stage,
                    )
                    selection_row = {
                        **_stage_base(
                            stage_name="historical_selections",
                            batch_id=batch_id,
                            source_file=source_file,
                            source_event_id=source_event_scope,
                            source_market_id=f"{source_event_scope}|{market_type}|{source_stage}",
                            source_selection_id=f"{source_event_scope}|{market_type}|{selection_side}|{source_stage}",
                            created_at=created_at,
                            point_in_time_status="stage_only_vendor_observation",
                            context={
                                "event_id": event_id,
                                "market_type": market_type,
                                "selection_side": selection_side,
                                "source_stage": source_stage,
                            },
                            payload=workbook_row,
                            market_type=market_type,
                        ),
                        "selection_id": selection_id,
                        "event_id": event_id,
                        "event_start_time": "",
                        "event_time_precision": "date_only",
                        "market_id": market_id,
                        "market_family": market_type,
                        "market_type": market_type,
                        "market_name": market_type,
                        "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
                        "book": "unknown",
                        "sportsbook_id": "",
                        "sportsbook_status": "unknown",
                        "selection": selection_name,
                        "selection_side": selection_side,
                        "team_id": mapping.team_id if mapping else "",
                        "line_value": line_value,
                        "odds": american_odds,
                        "american_odds": american_odds,
                        "implied_probability": implied_probability,
                        "opening_odds": american_odds if source_stage == "OPEN" else None,
                        "closing_odds": american_odds if source_stage == "CLOSE" else None,
                        "price_type": "american",
                        "market_label": f"{market_type}_{source_stage.lower()}",
                        "selection_count": 2,
                        "source_stage": source_stage,
                        "observed_at": "",
                        "observation_time_precision": "stage_only",
                        "available_at": "",
                        "available_at_precision": "unknown",
                        "market_source_methodology": "",
                        "market_source_status": "unknown",
                    }
                    selection_rows.append(selection_row)
                    gold_key = (market_type, selection_side)
                    candidate = gold_candidates.setdefault(
                        gold_key,
                        {
                            **_stage_base(
                                stage_name="historical_event_market_selections",
                                batch_id=batch_id,
                                source_file=source_file,
                                source_event_id=source_event_scope,
                                created_at=created_at,
                                point_in_time_status="stage_only_vendor_observation",
                                context={"event_id": event_id, "market_type": market_type, "selection_side": selection_side},
                                payload=workbook_row,
                                market_type=market_type,
                            ),
                            "dataset_row_id": _stable_id("gold_selection_row", event_id, market_type, selection_side),
                            "event_id": event_id,
                            "game_id": source_game_id,
                            "season": resolved_season,
                            "week": week,
                            "league": "NFL",
                            "event_date": event_date,
                            "home_team_id": home_mapping.team_id,
                            "home_team": home_mapping.historical_display_name,
                            "away_team_id": away_mapping.team_id,
                            "away_team": away_mapping.historical_display_name,
                            "winner_team_id": winner_mapping.team_id,
                            "loser_team_id": loser_mapping.team_id,
                            "home_score": home_score,
                            "away_score": away_score,
                            "score_differential": margin,
                            "total_points": total_points,
                            "market_id": _stable_id("gold_market", event_id, market_type, selection_side),
                            "market_family": market_type,
                            "market_type": market_type,
                            "selection": selection_name,
                            "selection_side": selection_side,
                            "team_id": mapping.team_id if mapping else "",
                            "source_stage_open": "OPEN",
                            "source_stage_close": "CLOSE",
                            "open_line_value": None,
                            "close_line_value": None,
                            "open_american_odds": None,
                            "close_american_odds": None,
                            "open_implied_probability": None,
                            "close_implied_probability": None,
                            "open_no_vig_probability": None,
                            "close_no_vig_probability": None,
                            "line_movement": None,
                            "odds_movement": None,
                            "selection_result_open": "",
                            "selection_result_close": "",
                            "result_margin_open": None,
                            "result_margin_close": None,
                        },
                    )
                    if source_stage == "OPEN":
                        candidate["open_line_value"] = line_value
                        candidate["open_american_odds"] = american_odds
                        candidate["open_implied_probability"] = implied_probability
                        candidate["open_no_vig_probability"] = no_vig_probability
                        candidate["selection_result_open"] = selection_result
                        candidate["result_margin_open"] = result_margin
                    else:
                        candidate["close_line_value"] = line_value
                        candidate["close_american_odds"] = american_odds
                        candidate["close_implied_probability"] = implied_probability
                        candidate["close_no_vig_probability"] = no_vig_probability
                        candidate["selection_result_close"] = selection_result
                        candidate["result_margin_close"] = result_margin

        for gold_row in gold_candidates.values():
            open_line = _normalize_float(gold_row.get("open_line_value"), None)
            close_line = _normalize_float(gold_row.get("close_line_value"), None)
            if open_line is not None and close_line is not None:
                gold_row["line_movement"] = round(close_line - open_line, 6)
            open_odds = _normalize_float(gold_row.get("open_american_odds"), None)
            close_odds = _normalize_float(gold_row.get("close_american_odds"), None)
            if open_odds is not None and close_odds is not None:
                gold_row["odds_movement"] = round(close_odds - open_odds, 6)
            gold_rows.append(gold_row)

    return {
        "event_rows": event_rows,
        "participant_rows": participant_rows,
        "event_link_rows": event_link_rows,
        "market_rows": market_rows,
        "selection_rows": selection_rows,
        "gold_rows": gold_rows,
        "team_mappings": team_mappings,
        "quarantined_rows": quarantined_rows,
        "unresolved_mappings": sorted(set(unresolved_mappings)),
    }


def _acquisition_batch_row(
    *,
    batch_id: str,
    created_at: str,
    source_file: str,
    source_count: int,
    event_count: int,
    market_count: int,
    selection_count: int,
    gold_count: int,
    workbook_profile: Mapping[str, Any],
    csv_profile: Mapping[str, Any],
    rejected_row_count: int = 0,
) -> dict[str, Any]:
    return {
        **_stage_base(
            stage_name="historical_acquisition_batches",
            batch_id=batch_id,
            source_file=source_file,
            created_at=created_at,
            point_in_time_status="raw_acquisition_preserved",
            context={"sheet_name": workbook_profile.get("sheet_name")},
            payload={
                "workbook_schema_fingerprint": workbook_profile.get("schema_fingerprint"),
                "csv_schema_fingerprint": csv_profile.get("schema_fingerprint"),
            },
            market_type="acquisition_batch",
        ),
        "batch_id": batch_id,
        "acquisition_started_at": created_at,
        "acquisition_completed_at": created_at,
        "source_count": source_count,
        "event_count": event_count,
        "market_count": market_count,
        "selection_count": selection_count,
        "certified_row_count": gold_count,
        "rejected_row_count": int(rejected_row_count),
        "coverage_json": _as_json(
            {
                "season_coverage": workbook_profile.get("season_coverage") or {},
                "date_min": workbook_profile.get("date_coverage", {}).get("min"),
                "date_max": workbook_profile.get("date_coverage", {}).get("max"),
                "row_count": workbook_profile.get("logical_data_row_count"),
            }
        ),
        "licensing_json": _as_json(
            {
                "sportsbook_identity": "unknown",
                "methodology": "unknown",
                "source_role": "authoritative_historical_source",
            }
        ),
        "provenance_json": _as_json(
            {
                "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
                "workbook_schema_fingerprint": workbook_profile.get("schema_fingerprint"),
                "csv_schema_fingerprint": csv_profile.get("schema_fingerprint"),
            }
        ),
        "notes_json": _as_json(
            {
                "csv_status": "malformed_schema",
                "workbook_status": "eligible_for_normalization",
            }
        ),
    }


def _register_identity_and_quality(
    *,
    runtime: DataIdentityLakehouseRuntime,
    batch_id: str,
    created_at: str,
    normalized_payload: Mapping[str, Any],
    workbook_profile: Mapping[str, Any],
    csv_profile: Mapping[str, Any],
    canonical_publication_scope: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    raw_rows: Sequence[Mapping[str, Any]] = (),
    progress: _StageProgressTracker | None = None,
) -> dict[str, Any]:
    team_mapping_rows = list(normalized_payload.get("team_mappings") or [])
    event_rows = list(normalized_payload.get("event_rows") or [])
    market_rows = list(normalized_payload.get("market_rows") or [])
    selection_rows = list(normalized_payload.get("selection_rows") or [])
    identity_mapping_rows: list[dict[str, Any]] = []
    canonical_scope_rows = canonical_publication_scope or {}
    scope_event_rows = [
        dict(row)
        for row in (canonical_scope_rows.get("historical_events") or event_rows)
    ]
    scope_market_rows = [
        dict(row)
        for row in (canonical_scope_rows.get("historical_markets") or market_rows)
    ]
    scope_selection_rows = [
        dict(row)
        for row in (canonical_scope_rows.get("historical_selections") or selection_rows)
    ]

    if progress is not None:
        progress.start(
            "identity_mapping",
            rows_total=len(team_mapping_rows) + len(event_rows),
        )
    direct_mapping_requests: list[dict[str, Any]] = []
    for team_row in team_mapping_rows:
        direct_mapping_requests.append(
            {
                "provider": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                "external_identifier": _normalize_text(team_row.get("source_name")),
                "internal_identifier": _normalize_text(team_row.get("team_id")),
                "entity_type": "team",
                "entity_name": _normalize_text(team_row.get("historical_display_name")),
                "canonical_key": _normalize_text(team_row.get("franchise_id")),
                "approval_reference": batch_id,
                "approval_evidence": team_row,
                "source_payload": team_row,
                "valid_from": team_row.get("valid_from"),
                "valid_to": team_row.get("valid_to"),
                "notes": {
                    "historical_display_name": team_row.get("historical_display_name"),
                    "observation_date": team_row.get("effective_date"),
                    "valid_from": team_row.get("valid_from"),
                    "valid_to": team_row.get("valid_to"),
                },
                "processed_at": created_at,
            }
        )

    for event_row in event_rows:
        direct_mapping_requests.append(
            {
                "provider": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                "external_identifier": _normalize_text(event_row.get("source_event_id")),
                "internal_identifier": _normalize_text(event_row.get("event_id")),
                "entity_type": "event",
                "entity_name": _normalize_text(event_row.get("event_key")),
                "canonical_key": _normalize_text(event_row.get("event_key")),
                "approval_reference": batch_id,
                "approval_evidence": {
                    "event_date": event_row.get("event_date"),
                    "home_team_id": event_row.get("home_team_id"),
                    "away_team_id": event_row.get("away_team_id"),
                },
                "source_payload": event_row,
                "valid_from": event_row.get("event_date"),
                "processed_at": created_at,
            }
        )
    with runtime.store.transaction():
        identity_mapping_rows.extend(
            runtime.register_identity_mappings_batch(
                direct_mapping_requests,
                progress_callback=(
                    (lambda processed, total: progress.update(rows_processed=processed, rows_total=total))
                    if progress is not None
                    else None
                ),
            )
        )
    if progress is not None:
        progress.complete(rows_processed=len(identity_mapping_rows))
        progress.start("identity_seed")

    with runtime.store.transaction():
        seed_result = runtime.seed_from_certified_outputs(
            events=scope_event_rows,
            markets=scope_market_rows,
            selections=scope_selection_rows,
            progress_callback=(
                (lambda processed, total: progress.update(rows_processed=processed, rows_total=total))
                if progress is not None
                else None
            ),
        )
        identity_mapping_rows.extend(seed_result.get("mappings") or [])
    if progress is not None:
        seed_total = int(seed_result.get("mapping_request_count") or len(seed_result.get("mappings") or []))
        progress.complete(rows_processed=seed_total, rows_total=seed_total)

    if progress is not None:
        progress.start("reconciliation")
    with runtime.store.transaction():
        reconciliation_result = runtime.reconcile_certified_outputs(
            selection_rows=scope_selection_rows,
            progress_callback=(
                (lambda processed, total: progress.update(rows_processed=processed, rows_total=total))
                if progress is not None
                else None
            ),
        )
    if progress is not None:
        reconciliation_total = int(
            reconciliation_result.get("selection_row_count")
            or len(reconciliation_result.get("reconciliation_rows") or [])
        )
        progress.complete(
            rows_processed=reconciliation_total,
            rows_total=reconciliation_total,
        )

    publication_scope_rows: dict[str, list[dict[str, Any]]]
    if canonical_scope_rows:
        publication_scope_rows = {
            table_name: [dict(row) for row in rows]
            for table_name, rows in canonical_scope_rows.items()
            if rows
        }
    else:
        publication_scope_rows = {
            table_name: [dict(row) for row in rows]
            for table_name, rows in _canonical_publication_rows(normalized_payload).items()
            if rows
        }
    if raw_rows:
        publication_scope_rows["raw_records"] = [dict(row) for row in raw_rows]
    if identity_mapping_rows:
        publication_scope_rows["identity_mappings"] = [dict(row) for row in identity_mapping_rows]
    reconciliation_rows = [dict(row) for row in reconciliation_result.get("reconciliation_rows") or []]
    if reconciliation_rows:
        publication_scope_rows["identity_reconciliation_results"] = reconciliation_rows

    if csv_profile:
        evidence_name = Path(str(csv_profile.get("path") or "NFL_Basic sample provider oddwarehouse.csv")).name
        runtime.record_quality_event(
            dataset_table="raw_records",
            record_identifier=f"{batch_id}:csv",
            entity_type="vendor_entity",
            provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
            internal_identifier=f"{batch_id}:csv",
            external_identifier=evidence_name,
            quality_event_type="malformed_schema",
            severity="warning",
            decision_status="quarantined",
            decision_explanation="CSV kept as source evidence only because unquoted multiword tokens cause positional drift.",
            review_state="approved_no_normalization",
            details={
                "header_field_count": csv_profile.get("header_field_count"),
                "schema_fingerprint": csv_profile.get("schema_fingerprint"),
            },
            processed_at=created_at,
        )
        runtime.record_quarantine_record(
            dataset_table="raw_records",
            record_identifier=f"{batch_id}:csv",
            entity_type="vendor_entity",
            provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
            internal_identifier=f"{batch_id}:csv",
            external_identifier=evidence_name,
            quarantine_reason="malformed_schema",
            decision_status="quarantined",
            review_state="approved_no_normalization",
            release_state="blocked_original_source_retained",
            details={
                "reason": "unquoted multiword headers and team names produce positional column drift",
            },
            processed_at=created_at,
        )
    if normalized_payload.get("quarantined_rows"):
        for row in normalized_payload["quarantined_rows"]:
            reason = _normalize_text(row.get("reason"))
            external_identifier = _normalize_text(row.get("external_identifier")) or _normalize_text(row.get("source_event_id"))
            decision_explanation = (
                "Team name could not be deterministically resolved from the approved historical mapping catalog."
                if reason.startswith("unresolved_")
                else "Historical event could not be assigned a deterministic regular-season week."
            )
            runtime.record_quality_event(
                dataset_table="historical_events",
                record_identifier=_normalize_text(row.get("source_event_id")) or _normalize_text(row.get("game_id")),
                entity_type="team" if reason.startswith("unresolved_") else "event",
                provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                internal_identifier="",
                external_identifier=external_identifier,
                quality_event_type=reason or "quarantined_source_row",
                severity="error",
                decision_status="quarantined",
                decision_explanation=decision_explanation,
                review_state="manual_review",
                details=dict(row),
                processed_at=created_at,
            )
            runtime.record_quarantine_record(
                dataset_table="historical_events",
                record_identifier=_normalize_text(row.get("source_event_id")) or _normalize_text(row.get("game_id")),
                entity_type="team" if reason.startswith("unresolved_") else "event",
                provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                internal_identifier="",
                external_identifier=external_identifier,
                quarantine_reason=reason or "quarantined_source_row",
                decision_status="quarantined",
                review_state="manual_review",
                release_state="blocked_until_manual_resolution",
                details=dict(row),
                processed_at=created_at,
            )
    lakehouse_result = runtime.publish_lakehouse_views(
        publication_scope=runtime.summarize_publication_scope(publication_scope_rows),
        progress_reporter=progress,
    )
    readiness_snapshot = runtime.build_readiness_snapshot()
    return {
        "reconciliation_result": reconciliation_result,
        "seed_result": seed_result,
        "lakehouse_result": lakehouse_result,
        "readiness_snapshot": readiness_snapshot,
        "selection_row_count": len(selection_rows),
        "publication_scope": runtime.summarize_publication_scope(publication_scope_rows),
    }


def _certify_assets(
    *,
    storage_path: Path,
    batch_id: str,
    created_at: str,
    raw_acquisition_result: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
) -> dict[str, Any]:
    source_bundle = dict(raw_acquisition_result.get("source_bundle") or {})
    runtime = HistoricalResearchAssetCertificationRuntime(storage_path=storage_path)
    try:
        asset_contracts = [
            ResearchAssetCertificationContract(
                research_asset_id=ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID,
                research_asset_name="OddsWarehouse NFL Source Events",
                asset_category="dataset",
                asset_type="source_event_snapshot",
                source_table_name="historical_events",
                required_fields=("event_id", "event_date", "home_team_id", "away_team_id", "source_event_id"),
                description="Canonical event rows created from the authoritative OddsWarehouse workbook.",
            ),
            ResearchAssetCertificationContract(
                research_asset_id=ODDSWAREHOUSE_NFL_BASIC_MARKET_OBSERVATIONS_ASSET_ID,
                research_asset_name="OddsWarehouse NFL Market Observations",
                asset_category="dataset",
                asset_type="market_observation_snapshot",
                source_table_name="historical_selections",
                required_fields=("selection_id", "event_id", "market_id", "market_type", "selection", "source_stage"),
                description="OPEN and CLOSE selection observations preserved without inventing timestamps.",
            ),
            ResearchAssetCertificationContract(
                research_asset_id=ODDSWAREHOUSE_NFL_BASIC_GOLD_ASSET_ID,
                research_asset_name="OddsWarehouse NFL Event Market Selection Gold",
                asset_category="dataset",
                asset_type="event_market_selection_gold",
                source_table_name="historical_event_market_selections",
                required_fields=("dataset_row_id", "event_id", "market_type", "selection", "open_american_odds", "close_american_odds"),
                description="Backtest-ready gold rows with open and close values aligned to settled outcomes.",
            ),
        ]
        results = []
        for contract in asset_contracts:
            table_key = {
                "historical_events": "event_rows",
                "historical_selections": "selection_rows",
                "historical_event_market_selections": "gold_rows",
            }[contract.source_table_name]
            results.append(
                runtime.certify_research_asset(
                    asset_contract=contract,
                    rows=normalized_payload.get(table_key) or [],
                    source_bundle=source_bundle,
                    raw_acquisition_result=raw_acquisition_result,
                    dataset_version=ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
                    created_at=created_at,
                    batch_id=batch_id,
                )
            )
        return {
            "ok": all(result["ok"] for result in results),
            "asset_results": results,
        }
    finally:
        runtime.close()


def _record_lifecycle(
    *,
    storage_path: Path,
    batch_id: str,
    created_at: str,
    raw_acquisition_result: Mapping[str, Any],
    certification_results: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    selected_profile: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path)
    try:
        lifecycle_rows = []
        full_source_profile = selected_profile.get("full_source") or selected_profile.get("source") or {}
        dataset_identity = _dataset_metadata(
            source_profile=full_source_profile,
            selected_profile=selected_profile.get("source") or {},
        )
        asset_id_to_rows = {
            ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID: normalized_payload.get("event_rows") or [],
            ODDSWAREHOUSE_NFL_BASIC_MARKET_OBSERVATIONS_ASSET_ID: normalized_payload.get("selection_rows") or [],
            ODDSWAREHOUSE_NFL_BASIC_GOLD_ASSET_ID: normalized_payload.get("gold_rows") or [],
        }
        for asset_result in certification_results.get("asset_results") or []:
            contract = asset_result["asset_contract"]
            identity = build_research_asset_identity_contract(
                asset_id=contract["research_asset_id"],
                asset_family="dataset",
                market_profile=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                market=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                league="NFL",
                sport="football",
                season=dataset_identity["full_source_season_label"],
                week_or_date=dataset_identity["full_source_date_label"],
                event_id="",
                market_id=contract["source_table_name"],
                selection="",
                provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                connector=ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
                schema_version=ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
                lineage_version=ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
                asset_name=contract["research_asset_name"],
                asset_type=contract["asset_type"],
                participant_id="",
                team_id="",
                game_id="",
                market_type=contract["source_table_name"],
            ).as_dict()
            for state, reason in (
                ("discovered", "OddsWarehouse historical asset discovered from the governed source import request."),
                ("source_identified", "Authoritative historical source identified for controlled vendor onboarding."),
                ("raw_acquired", "Raw historical source evidence staged through the canonical acquisition runtime."),
                ("normalized", "Canonical event, market, selection, and gold rows normalized through repository storage owners."),
            ):
                lifecycle_rows.append(
                    runtime.record_lifecycle_state(
                        identity=identity,
                        lifecycle_state=state,
                        lifecycle_reason=reason,
                        source_bundle=raw_acquisition_result.get("source_bundle") or {},
                        raw_acquisition_result=raw_acquisition_result,
                        created_at=created_at,
                        notes={"row_count": len(asset_id_to_rows.get(contract["research_asset_id"], []))},
                    )
                )
            lifecycle_rows.append(
                runtime.record_research_asset_certified(
                    identity=identity,
                    certification_result=asset_result["research_asset_certification"],
                    source_bundle=raw_acquisition_result.get("source_bundle") or {},
                    raw_acquisition_result=raw_acquisition_result,
                    created_at=created_at,
                )
            )
        return {
            "ok": True,
            "lifecycle_rows": lifecycle_rows,
        }
    finally:
        runtime.close()


def _safe_json_loads(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _iter_file_artifacts(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        payload.get("file_artifacts"),
        dict(payload.get("metadata") or {}).get("file_artifacts"),
    ]
    source_tables = payload.get("source_tables")
    if isinstance(source_tables, Mapping):
        candidates.append(dict(source_tables).get("file_artifacts"))
    artifacts: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, Sequence) or isinstance(candidate, (str, bytes)):
            continue
        for artifact in candidate:
            if isinstance(artifact, Mapping):
                artifacts.append(dict(artifact))
    return artifacts


def _extract_source_sha256(value: Any) -> str:
    if isinstance(value, Mapping):
        direct = _normalize_text(value.get("source_sha256") or value.get("file_sha256"))
        if direct:
            return direct
        for artifact_payload in _iter_file_artifacts(value):
            checksum = _normalize_text(artifact_payload.get("file_sha256"))
            if checksum:
                return checksum
        for nested in value.values():
            checksum = _extract_source_sha256(nested)
            if checksum:
                return checksum
        return ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            checksum = _extract_source_sha256(item)
            if checksum:
                return checksum
        return ""
    if isinstance(value, str):
        text = value.strip()
        for pattern in (
            r'"source_sha256"\s*:\s*"([^"]+)"',
            r'"file_sha256"\s*:\s*"([^"]+)"',
            r'\\"source_sha256\\"\s*:\s*\\"([^\\"]+)\\"',
            r'\\"file_sha256\\"\s*:\s*\\"([^\\"]+)\\"',
        ):
            match = re.search(pattern, text)
            if match:
                return _normalize_text(match.group(1))
        if text.startswith("{") or text.startswith("["):
            try:
                return _extract_source_sha256(json.loads(text))
            except json.JSONDecodeError:
                return ""
    return ""


def _extract_source_row_identifier(value: Any) -> str:
    if isinstance(value, Mapping):
        direct = _normalize_text(value.get("source_event_id") or value.get("source_row_id") or value.get("Game ID") or value.get("game_id"))
        if direct:
            return direct
        for nested in value.values():
            identifier = _extract_source_row_identifier(nested)
            if identifier:
                return identifier
        return ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            identifier = _extract_source_row_identifier(item)
            if identifier:
                return identifier
        return ""
    if isinstance(value, str):
        text = value.strip()
        for pattern in (
            r'"source_event_id"\s*:\s*"([^"]+)"',
            r'"source_row_id"\s*:\s*"([^"]+)"',
            r'"Game ID"\s*:\s*"([^"]+)"',
            r'"game_id"\s*:\s*"([^"]+)"',
            r'\\"source_event_id\\"\s*:\s*\\"([^\\"]+)\\"',
            r'\\"source_row_id\\"\s*:\s*\\"([^\\"]+)\\"',
            r'\\"Game ID\\"\s*:\s*\\"([^\\"]+)\\"',
            r'\\"game_id\\"\s*:\s*\\"([^\\"]+)\\"',
        ):
            match = re.search(pattern, text)
            if match:
                return _normalize_text(match.group(1))
        if text.startswith("{") or text.startswith("["):
            try:
                return _extract_source_row_identifier(json.loads(text))
            except json.JSONDecodeError:
                return ""
    return ""


def _oddswarehouse_historical_dataset_contract(storage_path: Path) -> DatasetContract:
    return DatasetContract(
        dataset_id=ODDSWAREHOUSE_NFL_BASIC_DATASET_ID,
        dataset_name="oddswarehouse_nfl_basic_historical",
        source_name=ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
        source_type=ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE,
        market=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
        sport="americanfootball_nfl",
        asset_class="historical",
        provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        schema_version=ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
        feature_pack=ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
        storage_location=str(storage_path),
        readiness="dataset_certified",
        update_frequency="manual",
        validation_state="validated",
        owner="src.data",
        status="active",
        market_type="historical_event_market_selection_gold",
        quality_score=1.0,
        metadata={
            "dataset_alias": ODDSWAREHOUSE_NFL_BASIC_DATASET_ALIAS,
            "dataset_revision": ODDSWAREHOUSE_NFL_BASIC_DATASET_REVISION,
            "report_catalog_name": "oddswarehouse_nfl_basic_historical",
            "gold_table": "historical_event_market_selections",
        },
    )


def _latest_oddswarehouse_batch_row(store: LocalStorageEngine, batch_id: str = "") -> dict[str, Any]:
    if batch_id:
        rows = store.fetch(
            "historical_acquisition_batches",
            where="batch_id = ?",
            params=[batch_id],
            order_by="created_at DESC",
            limit=1,
        )
        return dict(rows[0]) if rows else {}
    rows = store.fetch(
        "historical_acquisition_batches",
        where="version_id = ?",
        params=[ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION],
        order_by="created_at DESC",
        limit=1,
    )
    return dict(rows[0]) if rows else {}


def _latest_oddswarehouse_raw_version_row(store: LocalStorageEngine) -> dict[str, Any]:
    rows = store.fetch(
        "dataset_versions",
        where="dataset_id = ?",
        params=["dataset.sports.nfl.oddswarehouse.raw_acquisition_cache"],
        order_by="version_number DESC",
    )
    for row in rows:
        payload = dict(row)
        if int(payload.get("raw_record_count") or 0) >= 5076:
            return payload
    return dict(rows[0]) if rows else {}


def _oddswarehouse_source_sha_from_raw_version(
    version_row: Mapping[str, Any],
    *,
    store: LocalStorageEngine | None = None,
) -> str:
    for payload in (
        version_row.get("metadata_json"),
        version_row.get("payload_json"),
        _safe_json_loads(version_row.get("payload_json")).get("metadata_json"),
    ):
        checksum = _extract_source_sha256(payload)
        if checksum:
            return checksum
    if store is not None:
        version_id = _normalize_text(version_row.get("version_id"))
        if version_id:
            raw_rows = store.fetch(
                "raw_records",
                where="dataset_id = ? AND version_id = ?",
                params=["dataset.sports.nfl.oddswarehouse.raw_acquisition_cache", version_id],
                order_by="row_index ASC",
                limit=10,
            )
            for raw_row in raw_rows:
                checksum = _extract_source_sha256(raw_row.get("payload_json"))
                if checksum:
                    return checksum
    return ""


def _oddswarehouse_dataset_validation(
    *,
    batch_row: Mapping[str, Any],
    asset_rows: Sequence[Mapping[str, Any]],
    dataset_certification_row: Mapping[str, Any],
    gold_row_count: int,
    source_sha256: str,
) -> dict[str, Any]:
    validation_payload = _safe_json_loads(dataset_certification_row.get("validation_json"))
    errors = list(validation_payload.get("invalid_assets") or [])
    return {
        "ok": _normalize_text(dataset_certification_row.get("certification_status")) == "certified",
        "status": _normalize_text(dataset_certification_row.get("certification_status"), "missing"),
        "errors": errors,
        "warnings": [],
        "row_count": gold_row_count,
        "batch_id": _normalize_text(batch_row.get("batch_id")),
        "dataset_version": ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
        "source_sha256": source_sha256,
        "research_asset_certification_count": len(asset_rows),
        "date_coverage": _safe_json_loads(batch_row.get("coverage_json")).get("date_min"),
        "validation": validation_payload,
    }


def certify_oddswarehouse_nfl_basic_historical_dataset(
    *,
    storage_path: str | Path | None = None,
    batch_id: str = "",
    created_at: str | None = None,
) -> dict[str, Any]:
    effective_storage_path = Path(storage_path or ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH).expanduser().resolve()
    created_at = _normalize_text(created_at, _utc_now_iso())
    store = create_local_storage_engine(effective_storage_path)
    try:
        batch_row = _latest_oddswarehouse_batch_row(store, batch_id=batch_id)
        if not batch_row:
            raise ValueError("oddswarehouse_full_batch_missing")
        effective_batch_id = _normalize_text(batch_row.get("batch_id"))
        asset_rows = [
            dict(row)
            for row in store.fetch(
                "historical_research_asset_certifications",
                where="batch_id = ?",
                params=[effective_batch_id],
                order_by="research_asset_id ASC",
            )
        ]
        if not asset_rows:
            raise ValueError("oddswarehouse_asset_certifications_missing")
        raw_version_row = _latest_oddswarehouse_raw_version_row(store)
        source_sha256 = _oddswarehouse_source_sha_from_raw_version(raw_version_row, store=store)
        source_bundle = {
            "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
            "source_type": ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE,
            "source_key": ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY,
            "provider": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
            "source_file": _normalize_text(batch_row.get("source_file")),
        }
        raw_acquisition_result = {
            "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
            "source_type": ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE,
            "source_key": ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY,
            "provider": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
            "source_file": _normalize_text(batch_row.get("source_file")),
            "source_sha256": source_sha256,
            "dataset_version": _normalize_text(raw_version_row.get("version_id")),
            "source_bundle_id": _normalize_text(_safe_json_loads(raw_version_row.get("metadata_json")).get("source_bundle_id")),
        }
        certification_row = build_historical_dataset_certification_row(
            profile=get_nfl_p0_market_profile(),
            dataset_version=ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
            batch_id=effective_batch_id,
            created_at=created_at,
            source_bundle=source_bundle,
            raw_acquisition_result=raw_acquisition_result,
            asset_rows=asset_rows,
        )
        store.upsert("historical_certifications", certification_row, key_columns=("certification_id",))
        gold_row_count = int(
            store.connection.execute(
                "SELECT COUNT(*) FROM historical_event_market_selections WHERE batch_id = ?",
                [effective_batch_id],
            ).fetchone()[0]
        )
        contract = _oddswarehouse_historical_dataset_contract(effective_storage_path)
        platform = LocalDataPlatform(storage_path=effective_storage_path, dataset_owner="src.data")
        try:
            platform.register_dataset(contract)
            validation = _oddswarehouse_dataset_validation(
                batch_row=batch_row,
                asset_rows=asset_rows,
                dataset_certification_row=certification_row,
                gold_row_count=gold_row_count,
                source_sha256=source_sha256,
            )
            validation_row = platform.store_validation_result(
                contract,
                version_id=ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
                snapshot_id=_normalize_text(certification_row.get("snapshot_id")),
                lineage_id=_normalize_text(certification_row.get("lineage_id")),
                validation=validation,
                created_at=created_at,
                updated_at=created_at,
            )
            existing_versions = platform.store.fetch(
                "dataset_versions",
                where="dataset_id = ?",
                params=[contract.dataset_id],
                order_by="version_number ASC",
            )
            existing_version_row = next(
                (
                    dict(row)
                    for row in existing_versions
                    if _normalize_text(row.get("version_id")) == ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION
                ),
                {},
            )
            version_number = int(existing_version_row.get("version_number") or max(len(existing_versions), 1))
            checksum = hashlib.sha256(
                _as_json(
                    {
                        "batch_id": effective_batch_id,
                        "gold_row_count": gold_row_count,
                        "dataset_certification_id": certification_row.get("certification_id"),
                        "source_sha256": source_sha256,
                        "asset_certification_ids": [
                            _normalize_text(row.get("certification_id"))
                            for row in asset_rows
                        ],
                    }
                ).encode("utf-8")
            ).hexdigest()
            version_row = {
                "version_id": ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
                "owner": contract.owner,
                "sport": contract.sport,
                "feature_pack": contract.feature_pack,
                "storage_location": contract.storage_location,
                "readiness": "dataset_certified",
                "update_frequency": contract.update_frequency,
                "validation_state": "validated",
                "status": "active",
                "version_number": version_number,
                "raw_record_count": int(batch_row.get("source_count") or 0),
                "normalized_record_count": int(gold_row_count),
                "feature_snapshot_count": 0,
                "validation_id": validation_row["validation_id"],
                "checksum": checksum,
                "schema_version": contract.schema_version,
                "created_at": created_at,
                "updated_at": created_at,
                "source": contract.source_name,
                "provider": contract.provider,
                "market": contract.market,
                "market_type": contract.market_type,
                "asset_class": contract.asset_class,
                "snapshot_id": _normalize_text(certification_row.get("snapshot_id")),
                "lineage_id": _normalize_text(certification_row.get("lineage_id")),
                "quality_score": float(certification_row.get("quality_score") or 0.0),
                "metadata_json": _as_json(
                    {
                        **dict(contract.metadata),
                        "batch_id": effective_batch_id,
                        "source_sha256": source_sha256,
                        "certification_id": certification_row.get("certification_id"),
                    }
                ),
                "payload_json": _as_json(
                    {
                        **contract.as_dict(),
                        "batch_id": effective_batch_id,
                        "source_sha256": source_sha256,
                        "gold_row_count": gold_row_count,
                        "certification_id": certification_row.get("certification_id"),
                    }
                ),
            }
            platform.store.upsert("dataset_versions", version_row, key_columns=("version_id",))
            registry_contract = DatasetContract.from_mapping(
                {
                    **contract.as_dict(),
                    "readiness": "dataset_certified",
                    "validation_state": "validated",
                    "status": "active",
                    "quality_score": float(certification_row.get("quality_score") or 0.0),
                }
            )
            registry_row = platform._registry_row(
                registry_contract,
                latest_version_number=version_number,
                latest_snapshot_id=_normalize_text(certification_row.get("snapshot_id")),
                latest_feature_snapshot_id=_normalize_text(
                    (platform.read_dataset(contract.dataset_id).get("latest_feature_snapshot_id") or f"{contract.dataset_id}.feature.000")
                ),
                latest_validation_id=validation_row["validation_id"],
                version_count=max(len(existing_versions), version_number),
                validation_state="validated",
            )
            platform.store.upsert("dataset_registry", registry_row, key_columns=("dataset_id",))
        finally:
            platform.close()
        lifecycle_runtime = ResearchAssetLifecycleRuntime(storage_path=effective_storage_path)
        try:
            coverage = _safe_json_loads(batch_row.get("coverage_json"))
            identity = build_research_asset_identity_contract(
                asset_id=ODDSWAREHOUSE_NFL_BASIC_DATASET_ID,
                asset_family="dataset",
                market_profile=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                market=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                league="NFL",
                sport="football",
                season=_coverage_label(
                    (coverage.get("season_coverage") or {}).get("min"),
                    (coverage.get("season_coverage") or {}).get("max"),
                ),
                week_or_date=_coverage_label(coverage.get("date_min"), coverage.get("date_max")),
                provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                connector=ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
                schema_version=ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
                lineage_version=ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
                asset_name="OddsWarehouse NFL Basic Historical Dataset",
                asset_type="historical_dataset",
                metadata={
                    "batch_id": effective_batch_id,
                    "source_sha256": source_sha256,
                    "dataset_alias": ODDSWAREHOUSE_NFL_BASIC_DATASET_ALIAS,
                },
            )
            lifecycle_result = lifecycle_runtime.record_dataset_certified(
                identity=identity,
                certification_result={
                    "certification_id": certification_row["certification_id"],
                    "certification_status": certification_row["certification_status"],
                    "certification_state": certification_row["certification_status"],
                    "batch_id": effective_batch_id,
                    "version_id": ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION,
                    "quality_score": certification_row.get("quality_score"),
                    "coverage_score": certification_row.get("completeness_score"),
                    "point_in_time_status": certification_row.get("point_in_time_status"),
                    "summary": {
                        "gold_row_count": gold_row_count,
                        "source_sha256": source_sha256,
                    },
                },
                source_bundle=source_bundle,
                raw_acquisition_result=raw_acquisition_result,
                created_at=created_at,
            )
        finally:
            lifecycle_runtime.close()
        return {
            "ok": _normalize_text(certification_row.get("certification_status")) == "certified",
            "status": _normalize_text(certification_row.get("certification_status"), "missing"),
            "batch_id": effective_batch_id,
            "source_sha256": source_sha256,
            "dataset_contract": contract.as_dict(),
            "dataset_certification": certification_row,
            "dataset_registry": registry_row,
            "dataset_version": version_row,
            "dataset_validation": validation_row,
            "research_asset_certifications": asset_rows,
            "lifecycle_result": lifecycle_result,
        }
    finally:
        store.close()


def query_oddswarehouse_nfl_basic_dataset(
    *,
    storage_path: str | Path | None = None,
    season: int | None = None,
    date_from: str = "",
    date_to: str = "",
    event_id: str = "",
    team: str = "",
    sportsbook: str = "",
    market_type: str = "",
    selection: str = "",
    dataset_version: str = "",
    acquisition_id: str = "",
    limit: int = 100,
) -> dict[str, Any]:
    effective_storage_path = Path(storage_path or ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH).expanduser().resolve()
    store = create_local_storage_engine(effective_storage_path, auto_initialize=False)
    try:
        params: list[Any] = []
        clauses = ["g.version_id = ?"]
        params.append(_normalize_text(dataset_version, ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION))
        if season is not None:
            clauses.append("g.season = ?")
            params.append(int(season))
        if date_from:
            clauses.append("g.event_date >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("g.event_date <= ?")
            params.append(date_to)
        if event_id:
            clauses.append("g.event_id = ?")
            params.append(event_id)
        if team:
            clauses.append(
                "(g.home_team = ? OR g.away_team = ? OR g.selection = ? OR g.team_id = ? OR g.home_team_id = ? OR g.away_team_id = ?)"
            )
            params.extend([team, team, team, team, team, team])
        if sportsbook:
            clauses.append("'unknown' = ?")
            params.append(sportsbook)
        if market_type:
            clauses.append("g.market_type = ?")
            params.append(market_type)
        if selection:
            clauses.append("g.selection = ?")
            params.append(selection)
        if acquisition_id:
            clauses.append("g.batch_id = ?")
            params.append(acquisition_id)
        query = f"""
            SELECT
                g.dataset_row_id,
                g.event_id,
                g.market_id,
                g.selection,
                g.market_type,
                g.season,
                g.event_date,
                g.home_team,
                g.away_team,
                g.batch_id,
                g.version_id,
                g.certification_status,
                g.point_in_time_status,
                e.season_type,
                e.week,
                'unknown' AS sportsbook,
                'unknown' AS sportsbook_id
            FROM historical_event_market_selections AS g
            JOIN historical_events AS e ON e.event_id = g.event_id
            WHERE {' AND '.join(clauses)}
            ORDER BY g.event_date ASC, g.event_id ASC, g.market_type ASC, g.selection ASC
            LIMIT ?
        """
        params.append(max(1, int(limit)))
        rows = [dict(row) for row in store.connection.execute(query, params).fetchall()]
        return {
            "ok": True,
            "status": "ready",
            "filters": {
                "season": season,
                "date_from": date_from or None,
                "date_to": date_to or None,
                "event_id": event_id or None,
                "team": team or None,
                "sportsbook": sportsbook or None,
                "market_type": market_type or None,
                "selection": selection or None,
                "dataset_version": _normalize_text(dataset_version, ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION),
                "acquisition_id": acquisition_id or None,
            },
            "row_count": len(rows),
            "rows": rows,
        }
    finally:
        store.close()


def trace_oddswarehouse_nfl_basic_dataset_row(
    dataset_row_id: str,
    *,
    storage_path: str | Path | None = None,
) -> dict[str, Any]:
    effective_storage_path = Path(storage_path or ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH).expanduser().resolve()
    store = create_local_storage_engine(effective_storage_path, auto_initialize=False)
    try:
        gold_rows = store.fetch(
            "historical_event_market_selections",
            where="dataset_row_id = ?",
            params=[dataset_row_id],
            limit=1,
        )
        if not gold_rows:
            return {"ok": False, "status": "missing", "dataset_row_id": dataset_row_id}
        gold_row = dict(gold_rows[0])
        event_rows = store.fetch("historical_events", where="event_id = ?", params=[gold_row["event_id"]], limit=1)
        market_rows = store.fetch(
            "historical_markets",
            where="event_id = ? AND market_family = ?",
            params=[gold_row["event_id"], gold_row["market_family"]],
            order_by="source_stage ASC",
        )
        batch_rows = store.fetch(
            "historical_acquisition_batches",
            where="batch_id = ?",
            params=[gold_row["batch_id"]],
            limit=1,
        )
        if not event_rows or not market_rows or not batch_rows:
            return {
                "ok": False,
                "status": "incomplete_lineage",
                "dataset_row_id": dataset_row_id,
                "gold_row": gold_row,
            }
        event_row = dict(event_rows[0])
        market_row = dict(market_rows[0])
        batch_row = dict(batch_rows[0])
        selection_rows = [
            dict(row)
            for row in store.fetch(
                "historical_selections",
                where="event_id = ? AND market_family = ? AND selection = ?",
                params=[gold_row["event_id"], gold_row["market_family"], gold_row["selection"]],
                order_by="source_stage ASC",
            )
        ]
        source_game_id = _normalize_text(event_row.get("game_id"))
        source_event_id = _normalize_text(gold_row.get("source_event_id"))
        raw_version_row = _latest_oddswarehouse_raw_version_row(store)
        source_sha256 = _oddswarehouse_source_sha_from_raw_version(raw_version_row, store=store)
        raw_rows = [
            dict(row)
            for row in store.fetch(
                "raw_records",
                where="dataset_id = ?",
                params=["dataset.sports.nfl.oddswarehouse.raw_acquisition_cache"],
                order_by="created_at DESC, row_index ASC",
            )
        ]
        matched_raw_row: dict[str, Any] = {}
        for raw_row in raw_rows:
            raw_payload_text = str(raw_row.get("payload_json") or "")
            candidate_identifier = _extract_source_row_identifier(raw_payload_text)
            if (
                candidate_identifier in {source_event_id, source_game_id}
                or (source_event_id and source_event_id in raw_payload_text)
                or (source_game_id and f'"Game ID": "{source_game_id}"' in raw_payload_text)
                or (source_game_id and f'\\"Game ID\\": \\"{source_game_id}\\"' in raw_payload_text)
            ):
                matched_raw_row = {
                    "record_id": raw_row.get("record_id"),
                    "version_id": raw_row.get("version_id"),
                    "row_index": raw_row.get("row_index"),
                    "source_identifier": candidate_identifier,
                }
                break
        dataset_certifications = [
            dict(row)
            for row in store.fetch(
                "historical_certifications",
                where="version_id = ? AND batch_id = ?",
                params=[ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION, gold_row["batch_id"]],
                order_by="created_at DESC",
                limit=1,
            )
        ]
        return {
            "ok": True,
            "status": "ready",
            "dataset_row_id": dataset_row_id,
            "gold_row": gold_row,
            "silver_event": event_row,
            "silver_market": market_row,
            "silver_markets": [dict(row) for row in market_rows],
            "silver_selections": selection_rows,
            "bronze_raw_record": matched_raw_row,
            "source_artifact": {
                "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
                "source_file": batch_row.get("source_file"),
                "source_sha256": source_sha256,
                "raw_version_id": raw_version_row.get("version_id"),
            },
            "acquisition": {
                "batch_id": batch_row.get("batch_id"),
                "version_id": batch_row.get("version_id"),
                "provider": batch_row.get("provider"),
                "source_type": batch_row.get("source_type"),
            },
            "runtime": {
                "parser_version": ODDSWAREHOUSE_NFL_BASIC_PARSER_VERSION,
                "schema_version": ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
            },
            "dataset_certification": dataset_certifications[0] if dataset_certifications else {},
        }
    finally:
        store.close()


def _publication_table_specs(
    *,
    batch_id: str,
    created_at: str,
    source_file: Path,
    selected_profile: Mapping[str, Any],
    validation: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
) -> tuple[list[tuple[str, Sequence[Mapping[str, Any]], tuple[str, ...]]], list[str]]:
    rejected_source_event_ids = _rejected_source_event_ids(validation, normalized_payload)
    acquisition_batch_row = _acquisition_batch_row(
        batch_id=batch_id,
        created_at=created_at,
        source_file=source_file.name,
        source_count=len(selected_profile.get("files") or {}),
        event_count=len(normalized_payload.get("event_rows") or []),
        market_count=len(normalized_payload.get("market_rows") or []),
        selection_count=len(normalized_payload.get("selection_rows") or []),
        gold_count=len(normalized_payload.get("gold_rows") or []),
        rejected_row_count=len([item for item in rejected_source_event_ids if item]),
        workbook_profile=selected_profile["source"],
        csv_profile=selected_profile.get("companion_evidence") or {},
    )
    table_specs = [
        ("historical_acquisition_batches", [acquisition_batch_row], ("batch_id",)),
        ("historical_events", normalized_payload.get("event_rows") or [], ("event_id",)),
        ("historical_event_participants", normalized_payload.get("participant_rows") or [], ("participant_id",)),
        ("historical_source_event_links", normalized_payload.get("event_link_rows") or [], ("link_id",)),
        ("historical_markets", normalized_payload.get("market_rows") or [], ("market_id",)),
        ("historical_selections", normalized_payload.get("selection_rows") or [], ("selection_id",)),
        ("historical_event_market_selections", normalized_payload.get("gold_rows") or [], ("dataset_row_id",)),
    ]
    return table_specs, rejected_source_event_ids


def _canonical_publication_rows(normalized_payload: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        "historical_events": [dict(row) for row in normalized_payload.get("event_rows") or []],
        "historical_event_participants": [dict(row) for row in normalized_payload.get("participant_rows") or []],
        "historical_source_event_links": [dict(row) for row in normalized_payload.get("event_link_rows") or []],
        "historical_markets": [dict(row) for row in normalized_payload.get("market_rows") or []],
        "historical_selections": [dict(row) for row in normalized_payload.get("selection_rows") or []],
        "historical_event_market_selections": [dict(row) for row in normalized_payload.get("gold_rows") or []],
    }


def _build_publication_plan(
    *,
    storage_path: Path,
    lakehouse_root: Path,
    batch_id: str,
    created_at: str,
    source_file: Path,
    selected_profile: Mapping[str, Any],
    validation: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    progress: _StageProgressTracker | None = None,
) -> dict[str, Any]:
    table_specs, rejected_source_event_ids = _publication_table_specs(
        batch_id=batch_id,
        created_at=created_at,
        source_file=source_file,
        selected_profile=selected_profile,
        validation=validation,
        normalized_payload=normalized_payload,
    )
    total_rows = sum(len(rows) for _, rows, _ in table_specs)
    publication_plans: list[dict[str, Any]] = []
    store = create_local_storage_engine(storage_path)
    try:
        store.ensure_schema()
        if progress is not None:
            progress.start("canonical_classification", rows_total=total_rows)
        processed = 0
        for table_name, rows, key_columns in table_specs:
            plan = _classify_rows_against_store(
                store,
                table_name,
                rows,
                key_columns=key_columns,
                progress=progress,
                progress_offset=processed,
                progress_total=total_rows,
            )
            plan["key_columns"] = tuple(key_columns)
            publication_plans.append(plan)
            processed += len(rows)
        if progress is not None:
            progress.complete(rows_processed=total_rows, rows_total=total_rows)
    finally:
        store.close()

    source_row_counts = _source_row_classification_counts(
        list(selected_profile.get("source", {}).get("rows") or []),
        publication_plans[1:],
        rejected_source_event_ids=rejected_source_event_ids,
    )
    classification_counts = _classification_count_template()
    for plan in publication_plans:
        for classification, count in (plan.get("counts") or {}).items():
            classification_counts[classification] = classification_counts.get(classification, 0) + int(count or 0)
    affected_rows_by_table = {
        plan["table_name"]: [dict(row) for row in plan.get("rows_to_write") or []]
        for plan in publication_plans
        if plan.get("rows_to_write") and plan.get("table_name") != "historical_acquisition_batches"
    }
    identity_runtime = DataIdentityLakehouseRuntime(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
    )
    try:
        publication_scope = identity_runtime.summarize_publication_scope(affected_rows_by_table)
    finally:
        identity_runtime.close()
    return {
        "publication_plans": publication_plans,
        "classification_counts": classification_counts,
        "source_row_counts": source_row_counts,
        "affected_rows_by_table": affected_rows_by_table,
        "canonical_rows_by_table": _canonical_publication_rows(normalized_payload),
        "affected_tables": sorted(affected_rows_by_table),
        "affected_partition_scope": publication_scope,
        "expected_canonical_deltas": {
            plan["table_name"]: dict(plan.get("expected_canonical_delta") or {})
            for plan in publication_plans
        },
    }


def _persist_publication_plans(
    store: LocalStorageEngine,
    publication_plans: Sequence[Mapping[str, Any]],
    *,
    progress: _StageProgressTracker | None = None,
) -> None:
    total_rows = sum(len(plan.get("rows_to_write") or []) for plan in publication_plans)
    if progress is not None:
        progress.start("sqlite_persistence", rows_total=total_rows)
    processed = 0
    with store.transaction():
        for plan in publication_plans:
            key_columns = tuple(plan.get("key_columns") or ())
            for row in plan.get("rows_to_write") or []:
                store.upsert(plan["table_name"], row, key_columns=key_columns)
                processed += 1
                if progress is not None:
                    progress.update(rows_processed=processed, rows_total=total_rows)
    if progress is not None:
        progress.complete(rows_processed=processed, rows_total=total_rows)


def _execute_governed_publication(
    *,
    storage_path: Path,
    lakehouse_root: Path,
    batch_id: str,
    created_at: str,
    source_file: Path,
    selected_profile: Mapping[str, Any],
    validation: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    raw_acquisition_result: Mapping[str, Any],
    publication_plan: Mapping[str, Any],
    resume_publication: bool = False,
    preflight_only: bool = False,
    progress: _StageProgressTracker | None = None,
) -> dict[str, Any]:
    source_row_counts = dict(publication_plan.get("source_row_counts") or {})
    classification_counts = dict(publication_plan.get("classification_counts") or {})
    if source_row_counts["counts"]["CONFLICT"] > 0:
        return {
            "source_row_counts": source_row_counts,
            "classification_counts": classification_counts,
            "affected_tables": list(publication_plan.get("affected_tables") or []),
            "affected_partition_scope": dict(publication_plan.get("affected_partition_scope") or {}),
            "expected_canonical_deltas": dict(publication_plan.get("expected_canonical_deltas") or {}),
            "identity_result": {
                "lakehouse_result": {"ok": False, "created_partition_count": 0, "reused_partition_count": 0},
                "readiness_snapshot": {"parquet_readiness": {"roundtrip_ok": False}},
            },
            "certification_results": {"ok": False, "asset_results": []},
            "lifecycle_results": {"ok": False, "lifecycle_rows": []},
        }

    if preflight_only:
        return {
            "source_row_counts": source_row_counts,
            "classification_counts": classification_counts,
            "affected_tables": list(publication_plan.get("affected_tables") or []),
            "affected_partition_scope": dict(publication_plan.get("affected_partition_scope") or {}),
            "expected_canonical_deltas": dict(publication_plan.get("expected_canonical_deltas") or {}),
            "identity_result": {
                "lakehouse_result": {"ok": True, "created_partition_count": 0, "reused_partition_count": 0},
                "readiness_snapshot": {"parquet_readiness": {"roundtrip_ok": False}},
            },
            "certification_results": {"ok": True, "asset_results": []},
            "lifecycle_results": {"ok": True, "lifecycle_rows": []},
        }

    store = create_local_storage_engine(storage_path)
    try:
        store.ensure_schema()
        _persist_publication_plans(
            store,
            publication_plan.get("publication_plans") or [],
            progress=progress,
        )
    finally:
        store.close()

    identity_runtime = DataIdentityLakehouseRuntime(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
    )
    try:
        identity_result = _register_identity_and_quality(
            runtime=identity_runtime,
            batch_id=batch_id,
            created_at=created_at,
            normalized_payload=normalized_payload,
            workbook_profile=selected_profile["source"],
            csv_profile=selected_profile.get("companion_evidence") or {},
            canonical_publication_scope=(
                publication_plan.get("canonical_rows_by_table") or {}
                if resume_publication
                else publication_plan.get("affected_rows_by_table") or {}
            ),
            raw_rows=raw_acquisition_result.get("raw_records") or [],
            progress=progress,
        )
    finally:
        identity_runtime.close()

    if progress is not None:
        progress.start("certification")
    certification_results = _certify_assets(
        storage_path=storage_path,
        batch_id=batch_id,
        created_at=created_at,
        raw_acquisition_result=raw_acquisition_result,
        normalized_payload=normalized_payload,
    )
    if progress is not None:
        progress.complete()
        progress.start("lifecycle_recording")
    lifecycle_results = _record_lifecycle(
        storage_path=storage_path,
        batch_id=batch_id,
        created_at=created_at,
        raw_acquisition_result=raw_acquisition_result,
        certification_results=certification_results,
        normalized_payload=normalized_payload,
        selected_profile=selected_profile,
    )
    if progress is not None:
        progress.complete()
    return {
        "source_row_counts": source_row_counts,
        "classification_counts": classification_counts,
        "affected_tables": list(publication_plan.get("affected_tables") or []),
        "affected_partition_scope": dict(publication_plan.get("affected_partition_scope") or {}),
        "expected_canonical_deltas": dict(publication_plan.get("expected_canonical_deltas") or {}),
        "identity_result": identity_result,
        "certification_results": certification_results,
        "lifecycle_results": lifecycle_results,
    }


def _copy_directory_if_exists(source_dir: Path, target_dir: Path) -> None:
    if source_dir.exists():
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)


def _remove_path_if_exists(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return
    path.unlink(missing_ok=True)


def _publication_workspace_root(storage_path: Path, lakehouse_root: Path) -> Path:
    return Path(
        os.path.commonpath(
            [
                str(storage_path.expanduser().resolve().parent),
                str(lakehouse_root.expanduser().resolve().parent),
            ]
        )
    )


def _reset_resume_publication_workspace(
    *,
    storage_path: Path,
    lakehouse_root: Path,
    batch_id: str,
    publication_tokens: Sequence[str],
) -> None:
    normalized_batch_id = _normalize_text(batch_id)
    normalized_tokens = {
        _normalize_text(token)
        for token in publication_tokens
        if _normalize_text(token)
    }
    resolved_lakehouse_root = lakehouse_root.expanduser().resolve()
    if not normalized_batch_id and not normalized_tokens:
        return
    store = create_local_storage_engine(storage_path, auto_initialize=False)
    try:
        if not store.table_exists("lakehouse_partitions"):
            return
        partition_rows = store.fetch("lakehouse_partitions", order_by="partition_id ASC")
        for partition_row in partition_rows:
            partition_values: dict[str, Any] = {}
            payload = partition_row.get("partition_values_json")
            if isinstance(payload, str):
                try:
                    parsed = json.loads(payload)
                except json.JSONDecodeError:
                    parsed = {}
                if isinstance(parsed, Mapping):
                    partition_values = {str(key): value for key, value in parsed.items()}
            publication_batch = _normalize_text(partition_values.get("publication_batch"))
            if publication_batch not in normalized_tokens:
                continue
            file_path_text = _normalize_text(partition_row.get("file_path"))
            if file_path_text:
                file_path = Path(file_path_text).expanduser().resolve()
                try:
                    inside_workspace = os.path.commonpath([str(file_path), str(resolved_lakehouse_root)]) == str(resolved_lakehouse_root)
                except ValueError:
                    inside_workspace = False
                if inside_workspace:
                    _remove_path_if_exists(file_path)
            store.execute(
                "DELETE FROM lakehouse_partitions WHERE partition_id = ?",
                [_normalize_text(partition_row.get("partition_id"))],
            )
    finally:
        store.close()


def _promote_publication_state(
    *,
    staged_storage_path: Path,
    staged_lakehouse_root: Path,
    storage_path: Path,
    lakehouse_root: Path,
) -> None:
    token = _stable_digest(
        "oddswarehouse.publication.promote",
        str(storage_path),
        str(lakehouse_root),
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )[:12]
    storage_backup = storage_path.with_name(f".{storage_path.name}.backup.{token}")
    lakehouse_backup = lakehouse_root.parent / f".{lakehouse_root.name}.backup.{token}"
    _remove_path_if_exists(storage_backup)
    _remove_path_if_exists(lakehouse_backup)

    storage_backed_up = False
    promoted_storage = False
    promoted_files: list[Path] = []
    backed_up_files: list[tuple[Path, Path]] = []
    staged_files = sorted(path for path in staged_lakehouse_root.rglob("*.parquet")) if staged_lakehouse_root.exists() else []
    try:
        if storage_path.exists():
            storage_backup.parent.mkdir(parents=True, exist_ok=True)
            storage_path.rename(storage_backup)
            storage_backed_up = True

        storage_path.parent.mkdir(parents=True, exist_ok=True)
        staged_storage_path.rename(storage_path)
        promoted_storage = True

        lakehouse_root.parent.mkdir(parents=True, exist_ok=True)
        for staged_file in staged_files:
            relative_path = staged_file.relative_to(staged_lakehouse_root)
            target_path = lakehouse_root / relative_path
            backup_path = lakehouse_backup / relative_path
            if target_path.exists():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.rename(backup_path)
                backed_up_files.append((target_path, backup_path))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            staged_file.rename(target_path)
            promoted_files.append(target_path)
    except Exception:
        if promoted_storage and storage_path.exists():
            _remove_path_if_exists(storage_path)
        if storage_backed_up and storage_backup.exists():
            storage_backup.rename(storage_path)
        for target_path in reversed(promoted_files):
            _remove_path_if_exists(target_path)
        for target_path, backup_path in reversed(backed_up_files):
            if backup_path.exists():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.rename(target_path)
        raise
    finally:
        if promoted_storage and storage_backed_up and storage_backup.exists():
            _remove_path_if_exists(storage_backup)
        if lakehouse_backup.exists():
            _remove_path_if_exists(lakehouse_backup)
        if staged_lakehouse_root.exists():
            _remove_path_if_exists(staged_lakehouse_root)


def _rebase_staged_lakehouse_manifests(
    *,
    staged_storage_path: Path,
    staged_lakehouse_root: Path,
    actual_lakehouse_root: Path,
) -> None:
    staged_root_text = str(staged_lakehouse_root.expanduser().resolve())
    actual_root_text = str(actual_lakehouse_root.expanduser().resolve())
    if staged_root_text == actual_root_text:
        return
    store = create_local_storage_engine(staged_storage_path, auto_initialize=False)
    try:
        if not store.table_exists("lakehouse_partitions"):
            return
        for row in store.fetch("lakehouse_partitions", order_by="partition_id ASC"):
            updated = dict(row)
            for field_name in ("storage_location", "file_path", "metadata_json", "payload_json"):
                value = updated.get(field_name)
                if not isinstance(value, str) or staged_root_text not in value:
                    continue
                updated[field_name] = value.replace(staged_root_text, actual_root_text)
            store.upsert("lakehouse_partitions", updated, key_columns=("partition_id",))
    finally:
        store.close()


def _execute_atomic_governed_publication(
    *,
    storage_path: Path,
    lakehouse_root: Path,
    batch_id: str,
    created_at: str,
    source_file: Path,
    selected_profile: Mapping[str, Any],
    validation: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    raw_acquisition_result: Mapping[str, Any],
    publication_plan: Mapping[str, Any],
    resume_publication_tokens: Sequence[str] = (),
    progress: _StageProgressTracker | None = None,
) -> dict[str, Any]:
    workspace_root = _publication_workspace_root(storage_path, lakehouse_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="oddswarehouse-publication-",
        dir=workspace_root,
    ) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        temp_storage_path = temp_dir / storage_path.name
        if storage_path.exists():
            shutil.copy2(storage_path, temp_storage_path)
        temp_lakehouse_root = temp_dir / "lakehouse"
        if resume_publication_tokens:
            _reset_resume_publication_workspace(
                storage_path=temp_storage_path,
                lakehouse_root=temp_lakehouse_root,
                batch_id=batch_id,
                publication_tokens=resume_publication_tokens,
            )
        publication_result = _execute_governed_publication(
            storage_path=temp_storage_path,
            lakehouse_root=temp_lakehouse_root,
            batch_id=batch_id,
            created_at=created_at,
            source_file=source_file,
            selected_profile=selected_profile,
            validation=validation,
            normalized_payload=normalized_payload,
            raw_acquisition_result=raw_acquisition_result,
            publication_plan=publication_plan,
            resume_publication=bool(resume_publication_tokens),
            preflight_only=False,
            progress=progress,
        )
        if int(publication_result.get("source_row_counts", {}).get("counts", {}).get("CONFLICT") or 0) > 0:
            return publication_result
        _rebase_staged_lakehouse_manifests(
            staged_storage_path=temp_storage_path,
            staged_lakehouse_root=temp_lakehouse_root,
            actual_lakehouse_root=lakehouse_root,
        )
        _promote_publication_state(
            staged_storage_path=temp_storage_path,
            staged_lakehouse_root=temp_lakehouse_root,
            storage_path=storage_path,
            lakehouse_root=lakehouse_root,
        )
        return publication_result


def _preflight_governed_publication(
    *,
    storage_path: Path,
    lakehouse_root: Path,
    batch_id: str,
    created_at: str,
    source_file: Path,
    selected_profile: Mapping[str, Any],
    validation: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    raw_acquisition_result: Mapping[str, Any],
    progress: _StageProgressTracker | None = None,
) -> dict[str, Any]:
    publication_plan = _build_publication_plan(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        batch_id=batch_id,
        created_at=created_at,
        source_file=source_file,
        selected_profile=selected_profile,
        validation=validation,
        normalized_payload=normalized_payload,
        progress=progress,
    )
    result = _execute_governed_publication(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        batch_id=batch_id,
        created_at=created_at,
        source_file=source_file,
        selected_profile=selected_profile,
        validation=validation,
        normalized_payload=normalized_payload,
        raw_acquisition_result=raw_acquisition_result,
        publication_plan=publication_plan,
        preflight_only=True,
        progress=progress,
    )
    return {
        **result,
        "publication_plan": publication_plan,
    }


def _semantic_replay_payload(normalized_payload: Mapping[str, Any]) -> dict[str, Any]:
    volatile_fields = {"batch_id", "snapshot_id", "lineage_id"}
    canonical: dict[str, Any] = {}
    for key in (
        "event_rows",
        "participant_rows",
        "event_link_rows",
        "market_rows",
        "selection_rows",
        "gold_rows",
        "team_mappings",
        "quarantined_rows",
    ):
        rows = normalized_payload.get(key) or []
        canonical[key] = [
            {field: value for field, value in dict(row).items() if field not in volatile_fields}
            for row in rows
        ]
    canonical["unresolved_mappings"] = sorted(normalized_payload.get("unresolved_mappings") or [])
    return canonical


def _deterministic_replay_check(workbook_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    payload_a = _semantic_replay_payload(
        normalize_oddswarehouse_workbook_rows(
            workbook_rows,
            batch_id="replay.a",
            created_at="2026-07-17T00:00:00Z",
            source_file="pilot.xlsx",
        )
    )
    payload_b = _semantic_replay_payload(
        normalize_oddswarehouse_workbook_rows(
            workbook_rows,
            batch_id="replay.b",
            created_at="2026-07-17T00:00:00Z",
            source_file="pilot.xlsx",
        )
    )
    digest_a = _stable_digest(payload_a)
    digest_b = _stable_digest(payload_b)
    return {
        "ok": digest_a == digest_b,
        "digest_a": digest_a,
        "digest_b": digest_b,
    }


def _primary_source_file_info(profile: Mapping[str, Any]) -> dict[str, Any]:
    files = dict(profile.get("files") or {})
    for file_info in files.values():
        if file_info.get("source_role") == "primary_source":
            return dict(file_info)
    return {}


def _selected_rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {header: row.get(header) for header in EXPECTED_HEADERS}
        for row in rows
    ]
    return hashlib.sha256(_as_json(payload).encode("utf-8")).hexdigest()


def _build_source_artifact_id(profile: Mapping[str, Any]) -> str:
    source = dict(profile.get("source") or {})
    primary_file = _primary_source_file_info(profile)
    companion_files = [
        dict(file_info)
        for file_info in (profile.get("files") or {}).values()
        if file_info.get("source_role") == "companion_evidence"
    ]
    return _stable_id(
        "oddswarehouse_source_artifact",
        ODDSWAREHOUSE_NFL_BASIC_SOURCE_DATASET_ID,
        source.get("format"),
        primary_file.get("sha256"),
        [file_info.get("sha256") for file_info in companion_files],
    )


def _build_source_bundle_id(
    profile: Mapping[str, Any],
    *,
    selected_rows: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
) -> str:
    source = dict(profile.get("source") or {})
    primary_file = _primary_source_file_info(profile)
    companion_files = [
        dict(file_info)
        for file_info in (profile.get("files") or {}).values()
        if file_info.get("source_role") == "companion_evidence"
    ]
    return _stable_id(
        "oddswarehouse_source_bundle",
        ODDSWAREHOUSE_NFL_BASIC_SOURCE_DATASET_ID,
        source.get("format"),
        primary_file.get("sha256"),
        [file_info.get("sha256") for file_info in companion_files],
        selection.get("selection_rule"),
        selection.get("selected_row_count"),
        _selected_rows_digest(selected_rows),
    )


def _build_acquisition_id(
    profile: Mapping[str, Any],
    *,
    selected_rows: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
) -> str:
    source = dict(profile.get("source") or {})
    primary_file = _primary_source_file_info(profile)
    companion_files = [
        dict(file_info)
        for file_info in (profile.get("files") or {}).values()
        if file_info.get("source_role") == "companion_evidence"
    ]
    return _stable_id(
        "oddswarehouse_acquisition",
        ODDSWAREHOUSE_NFL_BASIC_SOURCE_DATASET_ID,
        source.get("format"),
        primary_file.get("sha256"),
        [file_info.get("sha256") for file_info in companion_files],
        ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
        ODDSWAREHOUSE_NFL_BASIC_PARSER_VERSION,
        selection.get("selection_rule"),
        selection.get("selected_row_count"),
        _selected_rows_digest(selected_rows),
    )


def _build_run_id(acquisition_id: str, started_at: str) -> str:
    return _stable_id("oddswarehouse_run", acquisition_id, started_at)


def _source_row_classification_counts(
    selected_rows: Sequence[Mapping[str, Any]],
    persistence_results: Sequence[Mapping[str, Any]],
    *,
    rejected_source_event_ids: Sequence[str] = (),
) -> dict[str, Any]:
    combined_statuses: dict[str, list[str]] = defaultdict(list)
    for result in persistence_results:
        for source_event_id, statuses in (result.get("source_event_statuses") or {}).items():
            combined_statuses[_normalize_text(source_event_id)].extend(str(status) for status in statuses)
    rejected_ids = {_normalize_text(source_event_id) for source_event_id in rejected_source_event_ids if _normalize_text(source_event_id)}

    counts = {
        "NEW": 0,
        "EXACT_DUPLICATE": 0,
        "REVISION": 0,
        "CONFLICT": 0,
        "REJECTED": 0,
    }
    row_classifications: list[dict[str, Any]] = []
    for row in selected_rows:
        source_event_id = _source_event_scope_from_row(row)
        statuses = combined_statuses.get(source_event_id, [])
        if source_event_id in rejected_ids:
            classification = "REJECTED"
        elif any(status == "CONFLICT" for status in statuses):
            classification = "CONFLICT"
        elif any(status == "REVISION" for status in statuses):
            classification = "REVISION"
        elif any(status == "REJECTED" for status in statuses):
            classification = "REJECTED"
        elif any(status == "NEW" for status in statuses):
            classification = "NEW"
        else:
            classification = "EXACT_DUPLICATE"
        counts[classification] += 1
        row_classifications.append(
            {
                "source_event_id": source_event_id,
                "game_id": _normalize_text(row.get("Game ID")),
                "classification": classification,
            }
        )
    return {
        "counts": counts,
        "rows": row_classifications,
    }


def _replay_status_from_counts(counts: Mapping[str, Any]) -> str:
    if int(counts.get("CONFLICT") or 0) > 0:
        return "CONFLICT"
    if int(counts.get("REVISION") or 0) > 0:
        return "REVISION"
    if int(counts.get("REJECTED") or 0) > 0:
        return "REJECTED"
    if int(counts.get("NEW") or 0) == 0:
        return "IDEMPOTENT_REUSE"
    if int(counts.get("EXACT_DUPLICATE") or 0) > 0:
        return "INCREMENTAL_APPEND"
    return "NEW_PUBLICATION"


def _should_skip_publication_for_reuse(
    *,
    publication_plan: Mapping[str, Any],
    prior_publication_exists: bool,
    partial_state_detected: bool,
    raw_acquisition_result: Mapping[str, Any],
) -> bool:
    if not prior_publication_exists or partial_state_detected:
        return False
    if _normalize_text(raw_acquisition_result.get("status")) != "raw_cache_reused":
        return False
    if publication_plan.get("affected_tables") or publication_plan.get("affected_partition_scope"):
        return False
    counts = dict((publication_plan.get("source_row_counts") or {}).get("counts") or {})
    return int(counts.get("NEW") or 0) == 0 and int(counts.get("CONFLICT") or 0) == 0


def run_oddswarehouse_nfl_basic_pilot(
    source_path: str | Path,
    companion_evidence_path: str | Path | None = None,
    *,
    storage_path: str | Path | None = None,
    lakehouse_root: str | Path | None = None,
    bronze_raw_root: str | Path | None = None,
    limit: int | None = None,
    progress_emit_interval_seconds: float = ODDSWAREHOUSE_PROGRESS_INTERVAL_SECONDS,
    progress_stream: Any | None = None,
) -> dict[str, Any]:
    get_nfl_p0_market_profile()
    effective_storage_path = Path(storage_path or ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH).expanduser().resolve()
    effective_lakehouse_root = Path(lakehouse_root or ODDSWAREHOUSE_NFL_BASIC_LAKEHOUSE_ROOT).expanduser().resolve()
    effective_bronze_root = Path(bronze_raw_root or ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT).expanduser().resolve()
    effective_storage_path.parent.mkdir(parents=True, exist_ok=True)
    effective_lakehouse_root.mkdir(parents=True, exist_ok=True)
    effective_bronze_root.mkdir(parents=True, exist_ok=True)

    started_at = _utc_now_iso()
    storage_health = get_storage_health()
    source_file = Path(source_path).expanduser().resolve()
    companion_file = Path(companion_evidence_path).expanduser().resolve() if companion_evidence_path is not None else None
    profile: dict[str, Any] = {}
    selected_profile: dict[str, Any] = {}
    selected_rows: list[dict[str, Any]] = []
    selection: dict[str, Any] = {
        "selection_rule": f"first_valid_rows:{int(limit)}" if limit is not None else "all_valid_rows",
        "available_row_count": 0,
        "selected_row_count": 0,
        "limit": limit,
        "inspected_physical_row_count": 0,
        "skipped_invalid_row_count": 0,
        "skipped_duplicate_header_row_count": 0,
        "encountered_invalid_rows": [],
        "encountered_duplicate_header_rows": [],
    }
    validation: dict[str, Any] = {
        "ok": False,
        "status": "unvalidated",
        "errors": [],
        "warnings": [],
        "row_results": [],
        "accepted_rows": [],
        "rejected_rows": [],
        "selected_row_count": 0,
        "validated_row_count": 0,
        "rejected_row_count": 0,
    }
    normalized: dict[str, Any] = {
        "event_rows": [],
        "participant_rows": [],
        "event_link_rows": [],
        "market_rows": [],
        "selection_rows": [],
        "gold_rows": [],
        "team_mappings": [],
        "quarantined_rows": [],
        "unresolved_mappings": [],
    }
    source_row_counts: dict[str, Any] = {
        "counts": {
            "NEW": 0,
            "EXACT_DUPLICATE": 0,
            "REVISION": 0,
            "CONFLICT": 0,
            "REJECTED": 0,
        },
        "rows": [],
    }
    classification_counts = _classification_count_template()
    publication_plan: dict[str, Any] = {}
    raw_acquisition_result: dict[str, Any] = {}
    identity_result: dict[str, Any] = {
        "lakehouse_result": {"ok": False, "created_partition_count": 0, "reused_partition_count": 0},
        "readiness_snapshot": {"parquet_readiness": {"roundtrip_ok": False}},
    }
    certification_results: dict[str, Any] = {"ok": False, "asset_results": []}
    lifecycle_results: dict[str, Any] = {"ok": False, "lifecycle_rows": []}
    bronze_actions: list[dict[str, Any]] = []
    primary_source_file: dict[str, Any] = {}
    acquisition_id = ""
    batch_id = ""
    run_id = ""
    source_bundle_id = ""
    source_artifact_id = ""
    failure_stage = ""
    failure_type = ""
    failure_message = ""
    publication_started = False
    publication_committed = False
    reuse_without_publication = False
    prior_publication_state = {"batch_exists": False, "batch_row": {}}
    partial_state_detected = False
    partial_state_action = ""
    resume_publication = False
    progress_tracker = _StageProgressTracker(
        emit_interval_seconds=progress_emit_interval_seconds,
        stream=progress_stream,
    )
    dataset_metadata: dict[str, Any] = {}

    try:
        failure_stage = "profile_source"
        progress_tracker.start("source_profiling")
        profile = _profile_oddswarehouse_source(
            source_file,
            companion_evidence_path=companion_file,
        )
        primary_source_file = _primary_source_file_info(profile)
        progress_tracker.complete()

        failure_stage = "select_rows"
        progress_tracker.start("row_selection")
        selected_rows, selection = _apply_deterministic_row_limit(
            profile["source"],
            limit=limit,
        )
        acquisition_id = _build_acquisition_id(
            profile,
            selected_rows=selected_rows,
            selection=selection,
        )
        source_bundle_id = _build_source_bundle_id(
            profile,
            selected_rows=selected_rows,
            selection=selection,
        )
        source_artifact_id = _build_source_artifact_id(profile)
        batch_id = acquisition_id
        run_id = _build_run_id(acquisition_id, started_at)
        selected_profile = _selected_source_profile(
            profile,
            selected_rows=selected_rows,
            selection=selection,
        )
        dataset_metadata = _dataset_metadata(
            source_profile=profile.get("source") or {},
            selected_profile=selected_profile.get("source") or {},
        )
        source_bundle = _source_bundle_from_source_profile(
            selected_profile,
            source_bundle_id,
            started_at,
            acquisition_id=acquisition_id,
            batch_id=batch_id,
        )
        progress_tracker.set_run_id(run_id)
        progress_tracker.complete(
            rows_processed=int(selection.get("selected_row_count") or 0),
            rows_total=int(selection.get("selected_row_count") or 0),
        )

        failure_stage = "validate_selection"
        progress_tracker.start("validation", rows_total=int(selection.get("selected_row_count") or 0))
        validation = validate_oddswarehouse_source_profile(selected_profile)
        if not validation["ok"]:
            raise ValueError("; ".join(str(error) for error in validation.get("errors") or []) or "selected_rows_validation_blocked")
        progress_tracker.complete(
            rows_processed=int(validation.get("validated_row_count") or 0),
            rows_total=int(selection.get("selected_row_count") or 0),
        )

        failure_stage = "normalize_selection"
        progress_tracker.start("normalization", rows_total=int(validation.get("validated_row_count") or 0))
        normalized = normalize_oddswarehouse_workbook_rows(
            validation["accepted_rows"],
            batch_id=batch_id,
            created_at=started_at,
            source_file=source_file.name,
        )
        progress_tracker.complete(
            rows_processed=int(validation.get("validated_row_count") or 0),
            rows_total=int(validation.get("validated_row_count") or 0),
        )

        prior_publication_state = _existing_batch_state(effective_storage_path, batch_id)
        resume_publication = _should_resume_incomplete_publication(
            prior_publication_state=prior_publication_state,
            normalized_payload=normalized,
            validation=validation,
        )

        raw_acquisition_result = {
            "ok": True,
            "status": "raw_cache_pending",
            "source_bundle": dict(source_bundle),
            "replay_status": "PENDING_PUBLICATION",
            "reuse_match_type": "",
        }
        if effective_storage_path.exists():
            with HistoricalDatasetAcquisitionRuntime(effective_storage_path) as acquisition_runtime:
                reusable_raw_acquisition = acquisition_runtime.find_reusable_raw_acquisition_cache(
                    source_bundle,
                    profile_id=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                    dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
                )
            if reusable_raw_acquisition is not None:
                raw_acquisition_result = dict(reusable_raw_acquisition)
                partial_state_detected, partial_state_action = _derive_partial_state(
                    prior_publication_exists=bool(prior_publication_state.get("batch_exists")),
                    raw_acquisition_result=raw_acquisition_result,
                    bronze_actions=bronze_actions,
                    resume_publication=resume_publication,
                )

        failure_stage = "preflight_publication"
        preflight_result = _preflight_governed_publication(
            storage_path=effective_storage_path,
            lakehouse_root=effective_lakehouse_root,
            batch_id=batch_id,
            created_at=started_at,
            source_file=source_file,
            selected_profile=selected_profile,
            validation=validation,
            normalized_payload=normalized,
            raw_acquisition_result=raw_acquisition_result,
            progress=progress_tracker,
        )
        source_row_counts = dict(preflight_result.get("source_row_counts") or source_row_counts)
        classification_counts = dict(preflight_result.get("classification_counts") or classification_counts)
        publication_plan = dict(preflight_result.get("publication_plan") or {})
        if source_row_counts["counts"]["CONFLICT"] > 0:
            validation = {
                **validation,
                "ok": False,
                "status": "blocked",
                "errors": list(validation.get("errors") or []) + ["canonical_row_conflict"],
            }
            raise ValueError("canonical_row_conflict")

        failure_stage = "stage_raw_acquisition"
        with HistoricalDatasetAcquisitionRuntime(effective_storage_path) as acquisition_runtime:
            raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
                source_bundle,
                profile_id=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
            )

        failure_stage = "stage_bronze"
        bronze_actions = _copy_bronze_artifacts(
            source_artifact_id,
            [
                {
                    "source_path": path,
                    "source_role": "primary_source" if path == source_file else "companion_evidence",
                    "source_format": path.suffix.lstrip("."),
                }
                for path in (source_file, companion_file)
                if path is not None
            ],
            bronze_raw_root=effective_bronze_root,
        )
        partial_state_detected, partial_state_action = _derive_partial_state(
            prior_publication_exists=bool(prior_publication_state.get("batch_exists")),
            raw_acquisition_result=raw_acquisition_result,
            bronze_actions=bronze_actions,
            resume_publication=resume_publication,
        )

        if _should_skip_publication_for_reuse(
            publication_plan=publication_plan,
            prior_publication_exists=bool(prior_publication_state.get("batch_exists")),
            partial_state_detected=partial_state_detected,
            raw_acquisition_result=raw_acquisition_result,
        ):
            reuse_without_publication = True
            identity_result = dict(preflight_result.get("identity_result") or identity_result)
            certification_results = dict(preflight_result.get("certification_results") or certification_results)
            lifecycle_results = dict(preflight_result.get("lifecycle_results") or lifecycle_results)
            failure_stage = ""
        else:
            publication_started = True
            failure_stage = "persist_canonical_rows"
            publication_result = _execute_atomic_governed_publication(
                storage_path=effective_storage_path,
                lakehouse_root=effective_lakehouse_root,
                batch_id=batch_id,
                created_at=started_at,
                source_file=source_file,
                selected_profile=selected_profile,
                validation=validation,
                normalized_payload=normalized,
                raw_acquisition_result=raw_acquisition_result,
                publication_plan=publication_plan,
                resume_publication_tokens=(
                    _resume_publication_tokens(
                        batch_id=batch_id,
                        source_bundle_id=source_bundle_id,
                    )
                    if resume_publication
                    else ()
                ),
                progress=progress_tracker,
            )
            source_row_counts = dict(publication_result.get("source_row_counts") or source_row_counts)
            classification_counts = dict(publication_result.get("classification_counts") or classification_counts)
            if source_row_counts["counts"]["CONFLICT"] > 0:
                validation = {
                    **validation,
                    "ok": False,
                    "status": "blocked",
                    "errors": list(validation.get("errors") or []) + ["canonical_row_conflict"],
                }
                raise ValueError("canonical_row_conflict")
            identity_result = dict(publication_result.get("identity_result") or identity_result)
            certification_results = dict(publication_result.get("certification_results") or certification_results)
            lifecycle_results = dict(publication_result.get("lifecycle_results") or lifecycle_results)
            publication_committed = True
            failure_stage = ""
    except KeyboardInterrupt as exc:
        failure_type = exc.__class__.__name__
        failure_message = "ingest_interrupted"
        progress_tracker.fail(interrupted=True, error=failure_message)
        rejected_source_event_ids = _rejected_source_event_ids(validation, normalized)
        source_row_counts = {
            "counts": {
                "NEW": 0,
                "EXACT_DUPLICATE": 0,
                "REVISION": 0,
                "CONFLICT": 0,
                "REJECTED": len([item for item in rejected_source_event_ids if item]),
            },
            "rows": [],
        }
    except Exception as exc:
        failure_type = exc.__class__.__name__
        failure_message = str(exc)
        progress_tracker.fail(error=failure_message)
        rejected_source_event_ids = _rejected_source_event_ids(validation, normalized)
        source_row_counts = {
            "counts": {
                "NEW": 0,
                "EXACT_DUPLICATE": 0,
                "REVISION": 0,
                "CONFLICT": 0,
                "REJECTED": len([item for item in rejected_source_event_ids if item]),
            },
            "rows": [],
        }

    replay_rows = validation.get("accepted_rows") or selected_rows
    replay_result = _deterministic_replay_check(replay_rows) if replay_rows else {"ok": True, "digest_a": "", "digest_b": ""}
    replay_status = _report_replay_status(
        counts=source_row_counts["counts"],
        publication_committed=publication_committed,
        prior_publication_exists=bool(prior_publication_state.get("batch_exists")),
        prior_incomplete_detected=partial_state_detected,
        reuse_without_publication=reuse_without_publication,
    )
    progress_snapshot = progress_tracker.snapshot()
    market_counts = {
        "historical_markets": len(normalized["market_rows"]),
        "historical_selections": len(normalized["selection_rows"]),
        "gold_event_market_selection_rows": len(normalized["gold_rows"]),
    }
    report = {
        "ok": bool(
            (publication_committed or reuse_without_publication)
            and validation.get("ok")
            and certification_results.get("ok")
            and replay_result.get("ok")
            and not normalized.get("quarantined_rows")
            and int(source_row_counts["counts"].get("CONFLICT") or 0) == 0
        ),
        "status": (
            "interrupted"
            if failure_type == "KeyboardInterrupt"
            else
            "failed"
            if not (publication_committed or reuse_without_publication) and failure_message
            else "ready"
            if (publication_committed or reuse_without_publication) and not normalized.get("quarantined_rows") and int(source_row_counts["counts"].get("CONFLICT") or 0) == 0
            else "partially_ready"
        ),
        "failure_stage": failure_stage or None,
        "failure_type": failure_type or None,
        "failure_message": failure_message or None,
        "source_dataset_id": ODDSWAREHOUSE_NFL_BASIC_SOURCE_DATASET_ID,
        "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
        "acquisition_id": acquisition_id or None,
        "run_id": run_id or None,
        "batch_id": batch_id or None,
        "source_bundle_id": source_bundle_id or None,
        "source_artifact_id": source_artifact_id or None,
        "source_format": (selected_profile.get("source") or profile.get("source") or {}).get("format"),
        "source_path": str(source_file),
        "source_sha256": primary_source_file.get("sha256"),
        "schema_version": ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
        "parser_version": ODDSWAREHOUSE_NFL_BASIC_PARSER_VERSION,
        "dataset_identity": dataset_metadata,
        "storage_path": str(effective_storage_path),
        "lakehouse_root": str(effective_lakehouse_root),
        "bronze_raw_root": str(_bronze_raw_dir_for_root(source_artifact_id or "pending", effective_bronze_root)),
        "storage_health": storage_health,
        "selection": selection,
        "selected_rows_digest": _selected_rows_digest(selected_rows) if selected_rows else "",
        "selected_row_count": int(selection.get("selected_row_count") or 0),
        "validated_row_count": int(validation.get("validated_row_count") or 0),
        "new_row_count": int(source_row_counts["counts"].get("NEW") or 0),
        "exact_duplicate_count": int(source_row_counts["counts"].get("EXACT_DUPLICATE") or 0),
        "semantic_reuse_count": int(classification_counts.get("SEMANTIC_REUSE") or 0),
        "revision_count": int(source_row_counts["counts"].get("REVISION") or 0),
        "conflict_count": int(source_row_counts["counts"].get("CONFLICT") or 0),
        "rejected_count": int(source_row_counts["counts"].get("REJECTED") or 0),
        "quarantined_count": (1 if (selected_profile.get("companion_evidence") or {}) else 0) + len(normalized.get("quarantined_rows") or []),
        "replay_status": replay_status,
        "publication_outcome": replay_status,
        "publication_started": publication_started,
        "publication_committed": publication_committed,
        "partial_state_detected": partial_state_detected,
        "partial_state_action": partial_state_action or None,
        "prior_incomplete_acquisition_detected": partial_state_detected,
        "files": profile.get("files") or {},
        "source_profile": (selected_profile.get("source") or profile.get("source") or {}),
        "companion_evidence_profile": selected_profile.get("companion_evidence") or profile.get("companion_evidence") or {},
        "validation": validation,
        "raw_acquisition_result": raw_acquisition_result,
        "bronze_file_copies": [action["target_path"] for action in bronze_actions],
        "bronze_file_actions": bronze_actions,
        "affected_tables": publication_plan.get("affected_tables") or [],
        "affected_partition_scope": publication_plan.get("affected_partition_scope") or {},
        "expected_canonical_deltas": publication_plan.get("expected_canonical_deltas") or {},
        "silver_counts": {
            "historical_events": len(normalized["event_rows"]),
            "historical_event_participants": len(normalized["participant_rows"]),
            "historical_source_event_links": len(normalized["event_link_rows"]),
            "historical_markets": len(normalized["market_rows"]),
            "historical_selections": len(normalized["selection_rows"]),
        },
        "gold_counts": {
            "historical_event_market_selections": len(normalized["gold_rows"]),
        },
        "market_transformation_counts": market_counts,
        "source_row_classifications": source_row_counts,
        "identity_mapping_results": {
            "resolved_team_mappings": len(normalized["team_mappings"]),
            "unresolved_team_mappings": normalized["unresolved_mappings"],
            "quarantined_rows": normalized.get("quarantined_rows") or [],
        },
        "identity_runtime": identity_result,
        "certification_results": certification_results,
        "lifecycle_results": lifecycle_results,
        "created_partition_count": int(identity_result.get("lakehouse_result", {}).get("created_partition_count") or 0),
        "updated_partition_count": int(identity_result.get("lakehouse_result", {}).get("updated_partition_count") or 0),
        "reused_partition_count": int(identity_result.get("lakehouse_result", {}).get("reused_partition_count") or 0),
        "parquet_roundtrip_result": bool(
            identity_result.get("lakehouse_result", {}).get("ok")
            and identity_result.get("readiness_snapshot", {}).get("parquet_readiness", {}).get("roundtrip_ok")
        ),
        "deterministic_replay_result": replay_result,
        "stage_timings": progress_snapshot["stage_timings"],
        "progress_events": progress_snapshot["progress_events"],
        "metadata_gaps": [
            "Exact kickoff time is unavailable from the source file and remains unset.",
            "Sportsbook identity is unknown in the supplied source evidence.",
            "Market-source methodology is unknown in the supplied source evidence.",
        ],
        "historical_readiness": "ready" if (publication_committed or reuse_without_publication) and not normalized.get("quarantined_rows") else "partially_ready",
        "pilot_readiness": "ready" if (publication_committed or reuse_without_publication) and not normalized.get("quarantined_rows") else "partially_ready",
        "additional_file_readiness": "ready_with_schema_validation" if validation.get("ok") else "manual_review_required",
    }
    return _write_ingest_report(report)


__all__ = [
    "EXPECTED_HEADERS",
    "ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT",
    "ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID",
    "ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION",
    "ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET",
    "ODDSWAREHOUSE_NFL_BASIC_LAKEHOUSE_ROOT",
    "ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID",
    "ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID",
    "ODDSWAREHOUSE_NFL_BASIC_PROVIDER_NAME",
    "ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT",
    "ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION",
    "ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY",
    "ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME",
    "ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE",
    "ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH",
    "TEAM_MAPPINGS",
    "TeamMapping",
    "certify_oddswarehouse_nfl_basic_historical_dataset",
    "normalize_oddswarehouse_workbook_rows",
    "profile_oddswarehouse_nfl_basic_inputs",
    "query_oddswarehouse_nfl_basic_dataset",
    "run_oddswarehouse_nfl_basic_pilot",
    "trace_oddswarehouse_nfl_basic_dataset_row",
    "validate_oddswarehouse_workbook_profile",
]
