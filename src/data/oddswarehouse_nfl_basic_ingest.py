from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET

from src.data.data_identity_lakehouse import DataIdentityLakehouseRuntime
from src.data.data_paths import get_runtime_data_path
from src.data.historical_dataset_acquisition_runtime import HistoricalDatasetAcquisitionRuntime
from src.data.historical_research_asset_certification_runtime import (
    HistoricalResearchAssetCertificationRuntime,
    ResearchAssetCertificationContract,
)
from src.data.nfl_p0_foundation import get_nfl_p0_market_profile
from src.data.odds_math import american_to_implied_probability, remove_two_way_vig
from src.data.research_asset_lifecycle_runtime import (
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
)
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION = "src.data.oddswarehouse_nfl_basic_ingest.v1"
ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID = "oddswarehouse"
ODDSWAREHOUSE_NFL_BASIC_PROVIDER_NAME = "OddsWarehouse"
ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID = "nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME = "OddsWarehouse NFL Basic"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_TYPE = "controlled_vendor_workbook"
ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY = "oddswarehouse_nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID = "connector.manual_import.oddswarehouse_nfl_basic"
ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_NAME = "OddsWarehouse NFL Basic Manual Import"
ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID = "sports:nfl"
ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION = "oddswarehouse.nfl_basic.2009.pilot.v1"
ODDSWAREHOUSE_NFL_BASIC_EXPECTED_SHEET = "NFL_Basic"
ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON = 2009
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


def _normalize_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _pilot_week_for_date(date_value: str) -> int:
    if date_value in {"20090910", "20090913", "20090914"}:
        return 1
    if date_value == "20090920":
        return 2
    raise ValueError(f"Unsupported pilot date outside Week 1/2 window: {date_value}")


def _provider_capability(schema_headers: Sequence[str]) -> dict[str, Any]:
    return {
        "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        "provider_name": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_NAME,
        "provider_role": "controlled_vendor_pilot",
        "connector_id": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
        "connector_name": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_NAME,
        "connector_family": "manual_import",
        "source_id": ODDSWAREHOUSE_NFL_BASIC_SOURCE_KEY,
        "source_name": ODDSWAREHOUSE_NFL_BASIC_SOURCE_NAME,
        "source_family": "odds_data",
        "source_access_type": "manual_import",
        "supported_assets": [
            "dataset.sports.nfl.oddswarehouse.source_events",
            "dataset.sports.nfl.oddswarehouse.market_observations",
            "dataset.sports.nfl.oddswarehouse.event_market_selection_gold",
        ],
        "supported_fields": list(schema_headers),
        "supported_markets": ["sports:nfl", "spread", "moneyline", "total"],
        "historical_depth": "historical",
        "update_frequency": "manual / workbook pilot",
        "point_in_time_safe": True,
        "licensing_notes": (
            "Controlled pilot import from a manually supplied workbook. "
            "Sportsbook identity and methodology remain unknown in the source evidence."
        ),
        "cost_class": "manual_import",
        "certification_readiness": "pilot_ready",
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
            if _normalize_float(row.get(field_name), None) is None:
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
            _safe_float(row.get("Away Spread Open")) + _safe_float(row.get("Home Spread Open")),
            6,
        )
        spread_close_sum = round(
            _safe_float(row.get("Away Spread Close")) + _safe_float(row.get("Home Spread Close")),
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


def _bronze_raw_dir(batch_id: str) -> Path:
    return _bronze_raw_dir_for_root(batch_id, ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT)


def _bounded_batch_token(batch_id: str) -> str:
    token = _normalize_text(batch_id).rsplit(".", 1)[-1]
    if not token:
        token = _stable_digest("bronze.raw.batch", batch_id)[:16]
    return token[:16]


def _bronze_raw_dir_for_root(batch_id: str, bronze_raw_root: str | Path) -> Path:
    return (
        Path(bronze_raw_root)
        / f"provider={ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID}"
        / "league=nfl"
        / f"season={ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON}"
        / f"product={ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID}"
        / f"b={_bounded_batch_token(batch_id)}"
    )


def _copy_bronze_files(
    batch_id: str,
    workbook_path: Path,
    csv_path: Path,
    *,
    bronze_raw_root: str | Path | None = None,
) -> list[str]:
    output_dir = _bronze_raw_dir_for_root(batch_id, bronze_raw_root or ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT)
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_paths: list[str] = []
    for source_path in (workbook_path, csv_path):
        target_path = output_dir / source_path.name
        shutil.copy2(source_path, target_path)
        copied_paths.append(str(target_path))
    return copied_paths


def _source_bundle_from_profile(profile: Mapping[str, Any], batch_id: str, acquired_at: str) -> dict[str, Any]:
    workbook = dict(profile.get("workbook") or {})
    csv_profile = dict(profile.get("csv") or {})
    workbook_rows = [dict(row) for row in workbook.get("rows") or []]
    workbook_cells = [
        {
            "sheet_name": cell.get("sheet_name"),
            "row_number": cell.get("row_number"),
            "column_number": cell.get("column_number"),
            "cell_reference": cell.get("cell_reference"),
            "cell_value": cell.get("cell_value"),
        }
        for cell in workbook.get("cells") or []
        if _normalize_text(cell.get("cell_value")) or cell.get("row_number") == 1
    ]
    file_artifacts = [
        {
            "file_name": file_name,
            "file_sha256": file_info["sha256"],
            "size_bytes": file_info["size_bytes"],
            "source_role": (
                "authoritative_pilot_structured_input"
                if file_name.endswith(".xlsx")
                else "accompanying_source_artifact"
            ),
            "validation_status": (
                "eligible_for_normalization"
                if file_name.endswith(".xlsx")
                else "malformed_schema"
            ),
            "normalization_status": (
                "allowed"
                if file_name.endswith(".xlsx")
                else "blocked"
            ),
            "quarantine_reason": (
                ""
                if file_name.endswith(".xlsx")
                else "unquoted multiword headers and team names produce positional column drift"
            ),
            "schema_fingerprint": (
                workbook.get("schema_fingerprint")
                if file_name.endswith(".xlsx")
                else csv_profile.get("schema_fingerprint")
            ),
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
        for index, example in enumerate(csv_profile.get("drift_examples") or [], start=1)
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
        "source_bundle_id": batch_id,
        "acquisition_timestamp": acquired_at,
        "connector_id": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
        "connector_name": ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_NAME,
        "connector_role": "controlled_manual_import",
        "execution_mode": "manual_workbook_pilot",
        "provider_role": "controlled_vendor_pilot",
        "source_family": "odds_data",
        "source_access_type": "manual_import",
        "provider_capability": _provider_capability(workbook.get("headers") or EXPECTED_HEADERS),
        "source_tables": {
            "file_artifacts": file_artifacts,
            "workbook_rows": workbook_rows,
            "workbook_cells": workbook_cells,
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


def _persist_rows(
    store: LocalStorageEngine,
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    key_columns: Sequence[str],
) -> None:
    columns = set(store.table_columns(table_name))
    for row in rows:
        filtered = {
            str(key): value
            for key, value in dict(row).items()
            if str(key) in columns
        }
        store.upsert(table_name, filtered, key_columns=key_columns)


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

    for workbook_row in workbook_rows:
        source_game_id = _normalize_text(workbook_row.get("Game ID"))
        source_date = _normalize_text(workbook_row.get("Date"))
        away_source_name = _normalize_text(workbook_row.get("Away Team"))
        home_source_name = _normalize_text(workbook_row.get("Home Team"))
        away_mapping = TEAM_MAPPINGS.get(away_source_name)
        home_mapping = TEAM_MAPPINGS.get(home_source_name)
        if away_mapping is None:
            unresolved_mappings.append(away_source_name)
            continue
        if home_mapping is None:
            unresolved_mappings.append(home_source_name)
            continue
        event_date = _date_from_source(source_date)
        week = _pilot_week_for_date(source_date)
        source_event_scope = f"{ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID}|{ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID}|{source_game_id}"
        event_id = _stable_id(
            "historical_event",
            "NFL",
            ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON,
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
                "season": ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON,
                "season_type": "regular",
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
                    "season": ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON,
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
                "season": ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON,
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
                    market_line_value = abs(_safe_float(workbook_row.get(selection_specs[0][2])))
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
                    line_value = _normalize_float(workbook_row.get(line_field), None) if line_field else None
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
                            "season": ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON,
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
        "rejected_row_count": 0,
        "coverage_json": _as_json(
            {
                "season": ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON,
                "date_min": workbook_profile.get("date_coverage", {}).get("min"),
                "date_max": workbook_profile.get("date_coverage", {}).get("max"),
                "row_count": workbook_profile.get("logical_data_row_count"),
            }
        ),
        "licensing_json": _as_json(
            {
                "sportsbook_identity": "unknown",
                "methodology": "unknown",
                "source_role": "authoritative_workbook_pilot",
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
) -> dict[str, Any]:
    team_mapping_rows = list(normalized_payload.get("team_mappings") or [])
    event_rows = list(normalized_payload.get("event_rows") or [])
    selection_rows = list(normalized_payload.get("selection_rows") or [])

    for team_row in team_mapping_rows:
        runtime.register_identity_mapping(
            provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
            external_identifier=_normalize_text(team_row.get("source_name")),
            internal_identifier=_normalize_text(team_row.get("team_id")),
            entity_type="team",
            entity_name=_normalize_text(team_row.get("historical_display_name")),
            canonical_key=_normalize_text(team_row.get("franchise_id")),
            approval_reference=batch_id,
            approval_evidence=team_row,
            source_payload=team_row,
            valid_from=team_row.get("effective_date"),
            notes={
                "historical_display_name": team_row.get("historical_display_name"),
                "effective_date": team_row.get("effective_date"),
            },
            processed_at=created_at,
        )

    for event_row in event_rows:
        runtime.register_identity_mapping(
            provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
            external_identifier=_normalize_text(event_row.get("source_event_id")),
            internal_identifier=_normalize_text(event_row.get("event_id")),
            entity_type="event",
            entity_name=_normalize_text(event_row.get("event_key")),
            canonical_key=_normalize_text(event_row.get("event_key")),
            approval_reference=batch_id,
            approval_evidence={
                "event_date": event_row.get("event_date"),
                "home_team_id": event_row.get("home_team_id"),
                "away_team_id": event_row.get("away_team_id"),
            },
            source_payload=event_row,
            valid_from=event_row.get("event_date"),
            processed_at=created_at,
        )

    runtime.seed_from_certified_outputs()
    reconciliation_result = runtime.reconcile_certified_outputs()

    runtime.record_quality_event(
        dataset_table="raw_records",
        record_identifier=f"{batch_id}:csv",
        entity_type="vendor_entity",
        provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        internal_identifier=f"{batch_id}:csv",
        external_identifier="NFL_Basic sample provider oddwarehouse.csv",
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
        external_identifier="NFL_Basic sample provider oddwarehouse.csv",
        quarantine_reason="malformed_schema",
        decision_status="quarantined",
        review_state="approved_no_normalization",
        release_state="blocked_original_source_retained",
        details={
            "reason": "unquoted multiword headers and team names produce positional column drift",
        },
        processed_at=created_at,
    )
    if normalized_payload.get("unresolved_mappings"):
        for team_name in normalized_payload["unresolved_mappings"]:
            runtime.record_quality_event(
                dataset_table="historical_events",
                record_identifier=team_name,
                entity_type="team",
                provider=ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                internal_identifier="",
                external_identifier=team_name,
                quality_event_type="unresolved_team_identity",
                severity="error",
                decision_status="quarantined",
                decision_explanation="Team name could not be deterministically resolved from the approved historical mapping catalog.",
                review_state="manual_review",
                details={"team_name": team_name},
                processed_at=created_at,
            )
    lakehouse_result = runtime.publish_lakehouse_views()
    readiness_snapshot = runtime.build_readiness_snapshot()
    return {
        "reconciliation_result": reconciliation_result,
        "lakehouse_result": lakehouse_result,
        "readiness_snapshot": readiness_snapshot,
        "selection_row_count": len(selection_rows),
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
                research_asset_id="dataset.sports.nfl.oddswarehouse.source_events",
                research_asset_name="OddsWarehouse NFL Source Events",
                asset_category="dataset",
                asset_type="source_event_snapshot",
                source_table_name="historical_events",
                required_fields=("event_id", "event_date", "home_team_id", "away_team_id", "source_event_id"),
                description="Canonical event rows created from the authoritative OddsWarehouse workbook.",
            ),
            ResearchAssetCertificationContract(
                research_asset_id="dataset.sports.nfl.oddswarehouse.market_observations",
                research_asset_name="OddsWarehouse NFL Market Observations",
                asset_category="dataset",
                asset_type="market_observation_snapshot",
                source_table_name="historical_selections",
                required_fields=("selection_id", "event_id", "market_id", "market_type", "selection", "source_stage"),
                description="OPEN and CLOSE selection observations preserved without inventing timestamps.",
            ),
            ResearchAssetCertificationContract(
                research_asset_id="dataset.sports.nfl.oddswarehouse.event_market_selection_gold",
                research_asset_name="OddsWarehouse NFL Event Market Selection Gold",
                asset_category="dataset",
                asset_type="event_market_selection_gold",
                source_table_name="historical_event_market_selections",
                required_fields=("dataset_row_id", "event_id", "market_type", "selection", "open_american_odds", "close_american_odds"),
                description="Backtest-ready pilot gold rows with open and close values aligned to settled outcomes.",
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
) -> dict[str, Any]:
    runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path)
    try:
        lifecycle_rows = []
        asset_id_to_rows = {
            "dataset.sports.nfl.oddswarehouse.source_events": normalized_payload.get("event_rows") or [],
            "dataset.sports.nfl.oddswarehouse.market_observations": normalized_payload.get("selection_rows") or [],
            "dataset.sports.nfl.oddswarehouse.event_market_selection_gold": normalized_payload.get("gold_rows") or [],
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
                season=str(ODDSWAREHOUSE_NFL_BASIC_PILOT_SEASON),
                week_or_date="2009-09-10..2009-09-20",
                event_id="oddswarehouse_pilot",
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
                ("discovered", "OddsWarehouse pilot asset discovered from the controlled workbook import request."),
                ("source_identified", "Authoritative workbook source identified for controlled vendor onboarding."),
                ("raw_acquired", "Raw workbook and CSV evidence staged through the canonical acquisition runtime."),
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


def run_oddswarehouse_nfl_basic_pilot(
    workbook_path: str | Path,
    csv_path: str | Path,
    *,
    storage_path: str | Path | None = None,
    lakehouse_root: str | Path | None = None,
    bronze_raw_root: str | Path | None = None,
) -> dict[str, Any]:
    get_nfl_p0_market_profile()
    effective_storage_path = Path(storage_path or ODDSWAREHOUSE_NFL_BASIC_STORAGE_PATH).expanduser().resolve()
    effective_lakehouse_root = Path(lakehouse_root or ODDSWAREHOUSE_NFL_BASIC_LAKEHOUSE_ROOT).expanduser().resolve()
    effective_bronze_root = Path(bronze_raw_root or ODDSWAREHOUSE_NFL_BASIC_BRONZE_RAW_ROOT).expanduser().resolve()
    effective_storage_path.parent.mkdir(parents=True, exist_ok=True)
    effective_lakehouse_root.mkdir(parents=True, exist_ok=True)
    effective_bronze_root.mkdir(parents=True, exist_ok=True)

    workbook_file = Path(workbook_path).expanduser().resolve()
    csv_file = Path(csv_path).expanduser().resolve()
    profile = profile_oddswarehouse_nfl_basic_inputs(workbook_file, csv_file)
    validation = validate_oddswarehouse_workbook_profile(profile)
    created_at = _utc_now_iso()
    batch_id = _stable_id(
        "oddswarehouse_batch",
        ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
        profile["files"][workbook_file.name]["sha256"],
        profile["files"][csv_file.name]["sha256"],
    )
    bronze_files = _copy_bronze_files(
        batch_id,
        workbook_file,
        csv_file,
        bronze_raw_root=effective_bronze_root,
    )
    source_bundle = _source_bundle_from_profile(profile, batch_id, created_at)
    with HistoricalDatasetAcquisitionRuntime(effective_storage_path) as acquisition_runtime:
        raw_acquisition_result = acquisition_runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id=ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )
    normalized = normalize_oddswarehouse_workbook_rows(
        profile["workbook"]["rows"],
        batch_id=batch_id,
        created_at=created_at,
        source_file=workbook_file.name,
    )
    store = create_local_storage_engine(effective_storage_path)
    try:
        store.ensure_schema()
        acquisition_batch_row = _acquisition_batch_row(
            batch_id=batch_id,
            created_at=created_at,
            source_file=workbook_file.name,
            source_count=2,
            event_count=len(normalized["event_rows"]),
            market_count=len(normalized["market_rows"]),
            selection_count=len(normalized["selection_rows"]),
            gold_count=len(normalized["gold_rows"]),
            workbook_profile=profile["workbook"],
            csv_profile=profile["csv"],
        )
        _persist_rows(store, "historical_acquisition_batches", [acquisition_batch_row], key_columns=("batch_id",))
        _persist_rows(store, "historical_events", normalized["event_rows"], key_columns=("event_id",))
        _persist_rows(store, "historical_event_participants", normalized["participant_rows"], key_columns=("participant_id",))
        _persist_rows(store, "historical_source_event_links", normalized["event_link_rows"], key_columns=("link_id",))
        _persist_rows(store, "historical_markets", normalized["market_rows"], key_columns=("market_id",))
        _persist_rows(store, "historical_selections", normalized["selection_rows"], key_columns=("selection_id",))
        _persist_rows(
            store,
            "historical_event_market_selections",
            normalized["gold_rows"],
            key_columns=("dataset_row_id",),
        )
    finally:
        store.close()

    identity_runtime = DataIdentityLakehouseRuntime(
        storage_path=effective_storage_path,
        lakehouse_root=effective_lakehouse_root,
    )
    try:
        identity_result = _register_identity_and_quality(
            runtime=identity_runtime,
            batch_id=batch_id,
            created_at=created_at,
            normalized_payload=normalized,
            workbook_profile=profile["workbook"],
            csv_profile=profile["csv"],
        )
    finally:
        identity_runtime.close()

    certification_results = _certify_assets(
        storage_path=effective_storage_path,
        batch_id=batch_id,
        created_at=created_at,
        raw_acquisition_result=raw_acquisition_result,
        normalized_payload=normalized,
    )
    lifecycle_results = _record_lifecycle(
        storage_path=effective_storage_path,
        batch_id=batch_id,
        created_at=created_at,
        raw_acquisition_result=raw_acquisition_result,
        certification_results=certification_results,
        normalized_payload=normalized,
    )
    replay_result = _deterministic_replay_check(profile["workbook"]["rows"])

    market_counts = {
        "historical_markets": len(normalized["market_rows"]),
        "historical_selections": len(normalized["selection_rows"]),
        "gold_event_market_selection_rows": len(normalized["gold_rows"]),
    }
    report = {
        "ok": validation["ok"] and not normalized["unresolved_mappings"] and certification_results["ok"] and replay_result["ok"],
        "status": "ready" if validation["ok"] and not normalized["unresolved_mappings"] and certification_results["ok"] and replay_result["ok"] else "partially_ready",
        "provider_id": ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
        "product_id": ODDSWAREHOUSE_NFL_BASIC_PRODUCT_ID,
        "batch_id": batch_id,
        "storage_path": str(effective_storage_path),
        "lakehouse_root": str(effective_lakehouse_root),
        "bronze_raw_root": str(_bronze_raw_dir_for_root(batch_id, effective_bronze_root)),
        "files": profile["files"],
        "workbook_profile": profile["workbook"],
        "csv_profile": profile["csv"],
        "validation": validation,
        "raw_acquisition_result": raw_acquisition_result,
        "bronze_file_copies": bronze_files,
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
        "identity_mapping_results": {
            "resolved_team_mappings": len(normalized["team_mappings"]),
            "unresolved_team_mappings": normalized["unresolved_mappings"],
        },
        "identity_runtime": identity_result,
        "certification_results": certification_results,
        "lifecycle_results": lifecycle_results,
        "parquet_roundtrip_result": identity_result["lakehouse_result"]["ok"]
        and bool(identity_result["readiness_snapshot"]["parquet_readiness"]["roundtrip_ok"]),
        "deterministic_replay_result": replay_result,
        "metadata_gaps": [
            "Exact kickoff time is unavailable from the source workbook and remains unset.",
            "Sportsbook identity is unknown in the supplied pilot files.",
            "Market-source methodology is unknown in the supplied pilot files.",
        ],
        "pilot_readiness": "ready" if validation["ok"] and not normalized["unresolved_mappings"] else "partially_ready",
        "additional_file_readiness": "ready_with_schema_validation" if validation["ok"] else "manual_review_required",
    }
    ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = ODDSWAREHOUSE_NFL_BASIC_REPORT_ROOT / f"{batch_id}.json"
    report_path.write_text(_as_json(report), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


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
    "normalize_oddswarehouse_workbook_rows",
    "profile_oddswarehouse_nfl_basic_inputs",
    "run_oddswarehouse_nfl_basic_pilot",
    "validate_oddswarehouse_workbook_profile",
]
