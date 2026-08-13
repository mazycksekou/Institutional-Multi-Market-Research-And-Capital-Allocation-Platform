from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

import src.data.oddswarehouse_nfl_basic_ingest as oddswarehouse_ingest
from scripts.run_oddswarehouse_nfl_basic_pilot import build_parser
from src.data.data_identity_lakehouse import DataIdentityLakehouseRuntime
from src.data.historical_canonical_compatibility import LINEAGE_METADATA, SEMANTIC_REUSE
from src.data.historical_dataset_acquisition_runtime import (
    HistoricalDatasetAcquisitionRuntime,
    _legacy_source_bundle_digest,
)
from src.data.oddswarehouse_nfl_basic_ingest import (
    EXPECTED_HEADERS,
    _apply_deterministic_row_limit,
    _build_acquisition_id,
    _build_source_bundle_id,
    _deterministic_replay_check,
    _profile_oddswarehouse_source,
    _selected_source_profile,
    _source_bundle_from_source_profile,
    normalize_oddswarehouse_workbook_rows,
    run_oddswarehouse_nfl_basic_pilot,
    validate_oddswarehouse_source_profile,
)
from src.data.research_asset_lifecycle_runtime import (
    ResearchAssetLifecycleRuntime,
    build_research_asset_identity_contract,
)
from src.storage.local_store import create_local_storage_engine


def _sample_workbook_rows() -> list[dict[str, object]]:
    return [
        {
            "Game ID": 95,
            "Date": "20090920",
            "Away Team": "St. Louis",
            "Away Score": 9,
            "Away Spread Open": 3.5,
            "Away Spread Open Odds": -110,
            "Away Spread Close": 4.0,
            "Away Spread Close Odds": -105,
            "Away MoneyLine Open": 160,
            "Away MoneyLine Close": 175,
            "Over Open": 42.5,
            "Over Open Odds": -110,
            "Over Close": 41.5,
            "Over Close Odds": -108,
            "Home Team": "Washington",
            "Home Score": 14,
            "Home Spread Open": -3.5,
            "Home Spread Open Odds": -110,
            "Home Spread Close": -4.0,
            "Home Spread Close Odds": -115,
            "Home MoneyLine Open": -190,
            "Home MoneyLine Close": -210,
            "Under Open": 42.5,
            "Under Open Odds": -110,
            "Under Close": 41.5,
            "Under Close Odds": -112,
        },
        {
            "Game ID": 96,
            "Date": "20090920",
            "Away Team": "Atlanta",
            "Away Score": 7,
            "Away Spread Open": 3.0,
            "Away Spread Open Odds": -110,
            "Away Spread Close": 2.5,
            "Away Spread Close Odds": -108,
            "Away MoneyLine Open": 145,
            "Away MoneyLine Close": 135,
            "Over Open": 38.5,
            "Over Open Odds": -110,
            "Over Close": 39.0,
            "Over Close Odds": -105,
            "Home Team": "Miami",
            "Home Score": 10,
            "Home Spread Open": -3.0,
            "Home Spread Open Odds": -110,
            "Home Spread Close": -2.5,
            "Home Spread Close Odds": -112,
            "Home MoneyLine Open": -165,
            "Home MoneyLine Close": -155,
            "Under Open": 38.5,
            "Under Open Odds": -110,
            "Under Close": 39.0,
            "Under Close Odds": -115,
        },
        {
            "Game ID": 97,
            "Date": "20090913",
            "Away Team": "Buffalo",
            "Away Score": 13,
            "Away Spread Open": 5.5,
            "Away Spread Open Odds": -110,
            "Away Spread Close": 6.0,
            "Away Spread Close Odds": -105,
            "Away MoneyLine Open": 210,
            "Away MoneyLine Close": 225,
            "Over Open": 44.5,
            "Over Open Odds": -110,
            "Over Close": 45.0,
            "Over Close Odds": -108,
            "Home Team": "New England",
            "Home Score": 24,
            "Home Spread Open": -5.5,
            "Home Spread Open Odds": -110,
            "Home Spread Close": -6.0,
            "Home Spread Close Odds": -115,
            "Home MoneyLine Open": -250,
            "Home MoneyLine Close": -270,
            "Under Open": 44.5,
            "Under Open Odds": -110,
            "Under Close": 45.0,
            "Under Close Odds": -112,
        },
    ]


def _row_with(base: dict[str, object], **overrides: object) -> dict[str, object]:
    row = dict(base)
    row.update(overrides)
    return row


def _repeated_team_workbook_rows() -> list[dict[str, object]]:
    base = _sample_workbook_rows()[0]
    return [
        base,
        _row_with(
            base,
            **{
                "Game ID": 195,
                "Date": "20090927",
                "Away Team": "Washington",
                "Away Score": 17,
                "Away Spread Open": 2.5,
                "Away Spread Open Odds": -110,
                "Away Spread Close": 2.0,
                "Away Spread Close Odds": -108,
                "Away MoneyLine Open": 130,
                "Away MoneyLine Close": 125,
                "Over Open": 39.5,
                "Over Open Odds": -110,
                "Over Close": 40.0,
                "Over Close Odds": -105,
                "Home Team": "Detroit",
                "Home Score": 10,
                "Home Spread Open": -2.5,
                "Home Spread Open Odds": -110,
                "Home Spread Close": -2.0,
                "Home Spread Close Odds": -112,
                "Home MoneyLine Open": -150,
                "Home MoneyLine Close": -145,
                "Under Open": 39.5,
                "Under Open Odds": -110,
                "Under Close": 40.0,
                "Under Close Odds": -115,
            },
        ),
        _sample_workbook_rows()[1],
    ]


def _xlsx_column_name(index: int) -> str:
    token = ""
    value = index + 1
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        token = chr(65 + remainder) + token
    return token


def _write_minimal_xlsx(path: Path, rows: list[dict[str, object]]) -> None:
    shared_strings: list[str] = []
    shared_indexes: dict[str, int] = {}

    def shared_index(value: object) -> int:
        text = str(value)
        if text not in shared_indexes:
            shared_indexes[text] = len(shared_strings)
            shared_strings.append(text)
        return shared_indexes[text]

    worksheet_rows: list[str] = []
    header_cells = []
    for index, header in enumerate(EXPECTED_HEADERS):
        header_cells.append(
            f'<c r="{_xlsx_column_name(index)}1" t="s"><v>{shared_index(header)}</v></c>'
        )
    worksheet_rows.append(f'<row r="1">{"".join(header_cells)}</row>')

    for row_number, row in enumerate(rows, start=2):
        cells: list[str] = []
        for column_index, header in enumerate(EXPECTED_HEADERS):
            cell_ref = f"{_xlsx_column_name(column_index)}{row_number}"
            value = row[header]
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{cell_ref}"><v>{value}</v></c>')
            else:
                cells.append(
                    f'<c r="{cell_ref}" t="s"><v>{shared_index(value)}</v></c>'
                )
        worksheet_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')

    shared_strings_xml = "".join(
        f"<si><t>{value}</t></si>"
        for value in shared_strings
    )
    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(worksheet_rows)}</sheetData>"
        "</worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets><sheet name=\"NFL_Basic\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "</workbook>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">'
        f"{shared_strings_xml}</sst>"
    )

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
        archive.writestr("xl/sharedStrings.xml", shared_xml)


def _write_canonical_csv(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [",".join(EXPECTED_HEADERS)]
    for row in rows:
        values = [str(row[header]) for header in EXPECTED_HEADERS]
        lines.append(",".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_malformed_companion_csv(path: Path, rows: list[dict[str, object]]) -> None:
    header_tokens = [token for header in EXPECTED_HEADERS for token in header.split(" ")]
    lines = [",".join(header_tokens)]
    for row in rows:
        values: list[str] = []
        for header in EXPECTED_HEADERS:
            value = str(row[header])
            if header in {"Away Team", "Home Team"}:
                values.extend(value.split(" "))
            else:
                values.append(value)
        lines.append(",".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _canonicalized_output(normalized: dict[str, object]) -> dict[str, object]:
    ignore_fields = {
        "dataset_id",
        "dataset_name",
        "market_profile",
        "profile_id",
        "profile_family",
        "stage_name",
        "batch_id",
        "source_file",
        "source_snapshot_time",
        "snapshot_time",
        "decision_time",
        "certified_at",
        "source_metadata_json",
        "context_json",
        "payload_json",
        "created_at",
        "updated_at",
        "snapshot_id",
        "lineage_id",
        "version_id",
        "completeness_score",
    }
    result: dict[str, object] = {}
    for key, value in normalized.items():
        if isinstance(value, list):
            cleaned_rows = []
            for row in value:
                cleaned_rows.append(
                    {
                        field: item
                        for field, item in dict(row).items()
                        if field not in ignore_fields
                    }
                )
            result[key] = cleaned_rows
        else:
            result[key] = value
    return result


def _lakehouse_parquet_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.parquet"))


def _legacy_stage_row(row: dict[str, object]) -> dict[str, object]:
    legacy: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, str) and value == "":
            legacy[key] = None
        elif isinstance(value, float) and value.is_integer():
            legacy[key] = int(value)
        else:
            legacy[key] = value
    return legacy


def test_normalize_oddswarehouse_workbook_rows_preserves_historical_identity_and_stage_only_timing() -> None:
    normalized = normalize_oddswarehouse_workbook_rows(
        [_sample_workbook_rows()[0]],
        batch_id="oddswarehouse.batch.test",
        created_at="2026-07-17T00:00:00Z",
        source_file="pilot.xlsx",
    )

    assert normalized["unresolved_mappings"] == []
    assert normalized["quarantined_rows"] == []
    assert len(normalized["event_rows"]) == 1
    assert len(normalized["participant_rows"]) == 2
    assert len(normalized["event_link_rows"]) == 1
    assert len(normalized["market_rows"]) == 6
    assert len(normalized["selection_rows"]) == 12
    assert len(normalized["gold_rows"]) == 6

    event_row = normalized["event_rows"][0]
    assert event_row["event_time_precision"] == "date_only"
    assert event_row["event_start_time"] == ""
    assert event_row["event_start_time_status"] == "unavailable_from_source"

    participants = {row["team_role"]: row for row in normalized["participant_rows"]}
    assert participants["away"]["team_id"] == "LAR"
    assert participants["away"]["historical_display_name"] == "St. Louis Rams"
    assert participants["away"]["source_team_name"] == "St. Louis"
    assert participants["home"]["team_id"] == "WAS"
    assert participants["home"]["historical_display_name"] == "Washington Redskins"

    assert all(row["observed_at"] == "" for row in normalized["market_rows"])
    assert all(row["observation_time_precision"] == "stage_only" for row in normalized["market_rows"])
    assert all(row["available_at"] == "" for row in normalized["selection_rows"])
    assert all(row["available_at_precision"] == "unknown" for row in normalized["selection_rows"])

    gold_rows = {
        (row["market_type"], row["selection_side"]): row
        for row in normalized["gold_rows"]
    }
    assert gold_rows[("moneyline", "home")]["selection_result_close"] == "win"
    assert gold_rows[("moneyline", "away")]["selection_result_close"] == "loss"
    assert gold_rows[("spread", "home")]["line_movement"] == -0.5
    assert gold_rows[("total", "over")]["line_movement"] == -1.0


def test_normalize_oddswarehouse_workbook_rows_maps_pk_spreads_to_zero() -> None:
    row = _row_with(
        _sample_workbook_rows()[0],
        **{
            "Away Spread Open": "PK",
            "Away Spread Close": "+0",
            "Home Spread Open": "PK",
            "Home Spread Close": "-0",
        },
    )
    profile = {"source": {"headers": EXPECTED_HEADERS, "logical_column_count": len(EXPECTED_HEADERS), "format": "csv", "rows": [row]}}
    validation = validate_oddswarehouse_source_profile(profile)
    normalized = normalize_oddswarehouse_workbook_rows(
        validation["accepted_rows"],
        batch_id="oddswarehouse.batch.pk",
        created_at="2026-08-08T00:00:00Z",
        source_file="NFL_Basic.csv",
    )

    assert validation["ok"] is True
    spread_markets = [item for item in normalized["market_rows"] if item["market_type"] == "spread"]
    spread_selections = [item for item in normalized["selection_rows"] if item["market_type"] == "spread"]
    assert {item["line_value"] for item in spread_markets} == {0.0}
    assert {item["line_value"] for item in spread_selections} == {0.0}


def test_oddswarehouse_replay_check_ignores_run_specific_lineage_tokens() -> None:
    replay = _deterministic_replay_check([_sample_workbook_rows()[0]])

    assert replay["ok"] is True
    assert replay["digest_a"] == replay["digest_b"]


def test_build_parser_accepts_mac_and_windows_source_paths() -> None:
    parser = build_parser()

    mac_args = parser.parse_args(["--source", "/Volumes/FantomHD/NFL_Basic.csv", "--limit", "100"])
    windows_args = parser.parse_args(["--source", r"D:\NFL_Basic.csv", "--limit", "100"])

    mac_source = str(mac_args.source).replace("\\", "/")
    windows_source = str(windows_args.source)

    assert PurePosixPath(mac_source).as_posix() == "/Volumes/FantomHD/NFL_Basic.csv"
    assert PurePosixPath(mac_source).name == "NFL_Basic.csv"
    assert str(PureWindowsPath(windows_source)) == r"D:\NFL_Basic.csv"
    assert PureWindowsPath(windows_source).name == "NFL_Basic.csv"
    assert mac_args.limit == 100
    assert windows_args.limit == 100


def test_module_cli_help_runs_without_pythonpath() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        [sys.executable, "-m", "scripts.run_oddswarehouse_nfl_basic_pilot", "--help"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--source" in result.stdout
    assert "--limit" in result.stdout


def test_deterministic_row_limit_selects_stable_first_rows() -> None:
    rows = _sample_workbook_rows()

    first, first_selection = _apply_deterministic_row_limit(rows, limit=2)
    second, second_selection = _apply_deterministic_row_limit(rows, limit=2)

    assert [row["Game ID"] for row in first] == [95, 96]
    assert [row["Game ID"] for row in second] == [95, 96]
    assert first_selection == second_selection


def test_deterministic_row_limit_skips_invalid_csv_rows_and_reports_scan_metadata(tmp_path: Path) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(EXPECTED_HEADERS),
                ",".join(str(rows[0][header]) for header in EXPECTED_HEADERS),
                "broken,row",
                ",".join(str(rows[1][header]) for header in EXPECTED_HEADERS),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)

    assert [row["Game ID"] for row in selected_rows] == ["95", "96"]
    assert selection["selected_row_count"] == 2
    assert selection["skipped_invalid_row_count"] == 1
    assert selection["inspected_physical_row_count"] == 3


def test_validate_oddswarehouse_source_profile_rejects_unknown_spread_token() -> None:
    row = _row_with(
        _sample_workbook_rows()[0],
        **{
            "Away Spread Open": "PICK",
            "Home Spread Open": "-0",
        },
    )
    profile = {"source": {"headers": EXPECTED_HEADERS, "logical_column_count": len(EXPECTED_HEADERS), "format": "csv", "rows": [row]}}

    validation = validate_oddswarehouse_source_profile(profile)

    assert validation["ok"] is False
    assert "non_numeric_Away Spread Open" in validation["rejected_rows"][0]["errors"]


def test_historical_week_resolution_supports_dates_beyond_week_two() -> None:
    rows = [
        _row_with(_sample_workbook_rows()[0], **{"Date": "20090910"}),
        _row_with(_sample_workbook_rows()[1], **{"Game ID": 196, "Date": "20090921"}),
        _row_with(_sample_workbook_rows()[2], **{"Game ID": 197, "Date": "20100103"}),
    ]

    normalized = normalize_oddswarehouse_workbook_rows(
        rows,
        batch_id="oddswarehouse.batch.historical",
        created_at="2026-08-06T00:00:00Z",
        source_file="NFL_Basic.csv",
    )

    weeks = {row["game_id"]: row["week"] for row in normalized["event_rows"]}
    seasons = {row["game_id"]: row["season"] for row in normalized["event_rows"]}

    assert weeks["95"] == 1
    assert weeks["196"] == 2
    assert weeks["197"] == 17
    assert seasons == {"95": 2009, "196": 2009, "197": 2009}


def test_xlsx_and_canonical_csv_sources_produce_equivalent_canonical_rows(tmp_path: Path) -> None:
    rows = _sample_workbook_rows()[:2]
    xlsx_path = tmp_path / "NFL_Basic.xlsx"
    csv_path = tmp_path / "NFL_Basic.csv"
    _write_minimal_xlsx(xlsx_path, rows)
    _write_canonical_csv(csv_path, rows)

    xlsx_profile = _profile_oddswarehouse_source(xlsx_path)
    csv_profile = _profile_oddswarehouse_source(csv_path)

    assert validate_oddswarehouse_source_profile(xlsx_profile)["ok"] is True
    assert validate_oddswarehouse_source_profile(csv_profile)["ok"] is True

    normalized_xlsx = normalize_oddswarehouse_workbook_rows(
        xlsx_profile["source"]["rows"],
        batch_id="oddswarehouse.batch.same",
        created_at="2026-07-17T00:00:00Z",
        source_file="shared-source",
    )
    normalized_csv = normalize_oddswarehouse_workbook_rows(
        csv_profile["source"]["rows"],
        batch_id="oddswarehouse.batch.same",
        created_at="2026-07-17T00:00:00Z",
        source_file="shared-source",
    )

    assert _canonicalized_output(normalized_xlsx) == _canonicalized_output(normalized_csv)


def test_xlsx_source_keeps_malformed_companion_csv_as_quarantined_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    xlsx_path = tmp_path / "NFL_Basic sample provider oddwarehouse 1.xlsx"
    malformed_csv_path = tmp_path / "NFL_Basic sample provider oddwarehouse.csv"
    storage_root = tmp_path / "external"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)

    _write_minimal_xlsx(xlsx_path, rows)
    _write_malformed_companion_csv(malformed_csv_path, rows)

    report = run_oddswarehouse_nfl_basic_pilot(
        xlsx_path,
        malformed_csv_path,
        storage_path=storage_root / "historical" / "oddswarehouse.sqlite",
        lakehouse_root=storage_root / "lakehouse" / "oddswarehouse",
        bronze_raw_root=storage_root / "bronze" / "oddswarehouse",
    )

    assert report["source_format"] == "xlsx"
    assert report["selected_row_count"] == 2
    assert report["quarantined_count"] == 1
    assert report["companion_evidence_profile"]["header_field_count"] > len(EXPECTED_HEADERS)
    assert len(report["bronze_file_copies"]) == 2
    assert report["storage_health"]["configured_via_env_var"] == "RESEARCH_DATA_ROOT"
    assert report["storage_health"]["repository_independent"] is True

    store = create_local_storage_engine(Path(report["storage_path"]))
    try:
        assert store.count("quarantine_records") == 1
        assert store.count("data_quality_events") == 1
    finally:
        store.close()


def test_validation_failure_returns_structured_report_without_publication(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    csv_path.write_text("Bad,Header\n1,2\n", encoding="utf-8")

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=storage_root / "lakehouse" / "oddswarehouse",
        bronze_raw_root=storage_root / "bronze" / "oddswarehouse",
        limit=1,
    )

    assert report["ok"] is False
    assert report["status"] == "failed"
    assert report["failure_stage"] == "validate_selection"
    assert report["replay_status"] == "failed_before_publication"
    assert report["publication_started"] is False
    assert report["publication_committed"] is False
    assert report["bronze_file_copies"] == []
    assert storage_path.exists() is False
    assert Path(report["report_path"]).exists()


def test_preflight_publication_is_read_only_and_avoids_lakehouse_copy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    _write_canonical_csv(csv_path, rows)
    storage_path = tmp_path / "historical.sqlite"
    lakehouse_root = tmp_path / "lakehouse"

    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)
    acquisition_id = _build_acquisition_id(
        profile,
        selected_rows=selected_rows,
        selection=selection,
    )
    selected_profile = _selected_source_profile(
        profile,
        selected_rows=selected_rows,
        selection=selection,
    )
    validation = validate_oddswarehouse_source_profile(selected_profile)
    normalized = normalize_oddswarehouse_workbook_rows(
        selected_rows,
        batch_id=acquisition_id,
        created_at="2026-08-10T00:00:00Z",
        source_file=csv_path.name,
    )

    def _unexpected_copytree(*args, **kwargs) -> None:
        raise AssertionError("preflight should not copy the lakehouse directory")

    monkeypatch.setattr(shutil, "copytree", _unexpected_copytree)

    result = oddswarehouse_ingest._preflight_governed_publication(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        batch_id=acquisition_id,
        created_at="2026-08-10T00:00:00Z",
        source_file=csv_path,
        selected_profile=selected_profile,
        validation=validation,
        normalized_payload=normalized,
        raw_acquisition_result={},
    )

    store = create_local_storage_engine(storage_path)
    try:
        assert store.count("historical_acquisition_batches") == 0
        assert store.count("historical_events") == 0
        assert store.count("historical_markets") == 0
        assert store.count("historical_selections") == 0
        assert store.count("lakehouse_partitions") == 0
    finally:
        store.close()

    assert result["source_row_counts"]["counts"]["NEW"] == 2
    assert result["classification_counts"]["NEW"] > 0
    assert result["identity_result"]["lakehouse_result"]["created_partition_count"] == 0
    assert result["publication_plan"]["affected_tables"]
    assert result["publication_plan"]["affected_partition_scope"]
    assert _lakehouse_parquet_files(lakehouse_root) == []


def test_progress_events_report_stage_timings_and_scoped_partition_reuse(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    first = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )
    first_parquet_files = _lakehouse_parquet_files(lakehouse_root)
    store = create_local_storage_engine(storage_path)
    try:
        first_partition_count = store.count("lakehouse_partitions")
    finally:
        store.close()

    progress_stream = io.StringIO()
    replay = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
        progress_emit_interval_seconds=0.0,
        progress_stream=progress_stream,
    )

    events = [
        json.loads(line)
        for line in progress_stream.getvalue().splitlines()
        if line.strip()
    ]
    completed_stages = {
        event["stage"]
        for event in events
        if event["status"] == "COMPLETED"
    }
    required_stages = {
        "source_profiling",
        "row_selection",
        "validation",
        "normalization",
        "canonical_classification",
    }

    assert replay["ok"] is True
    assert replay["progress_events"] == events
    assert required_stages <= completed_stages
    assert set(replay["stage_timings"]) == required_stages
    assert replay["publication_started"] is False
    assert replay["publication_committed"] is False
    assert replay["created_partition_count"] == 0
    assert replay["updated_partition_count"] == 0
    assert replay["reused_partition_count"] == 0
    assert _lakehouse_parquet_files(lakehouse_root) == first_parquet_files
    assert first["created_partition_count"] == first_partition_count


def test_oddswarehouse_ingest_batches_direct_identity_mapping_registration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    register_calls = 0
    original_register = DataIdentityLakehouseRuntime.register_identity_mapping

    def _recording_register(self, *args, **kwargs):
        nonlocal register_calls
        register_calls += 1
        return original_register(self, *args, **kwargs)

    monkeypatch.setattr(
        DataIdentityLakehouseRuntime,
        "register_identity_mapping",
        _recording_register,
    )

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_root / "historical" / "oddswarehouse.sqlite",
        lakehouse_root=storage_root / "lakehouse" / "oddswarehouse",
        bronze_raw_root=storage_root / "bronze" / "oddswarehouse",
        limit=2,
    )

    assert report["ok"] is True
    assert register_calls == 0


def test_ingest_report_compacts_large_runtime_payloads(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_root / "historical" / "oddswarehouse.sqlite",
        lakehouse_root=storage_root / "lakehouse" / "oddswarehouse",
        bronze_raw_root=storage_root / "bronze" / "oddswarehouse",
        limit=2,
    )

    persisted = json.loads(Path(report["report_path"]).read_text(encoding="utf-8"))

    assert persisted["ok"] is True
    assert "seed_result" not in persisted["identity_runtime"]
    assert "reconciliation_result" not in persisted["identity_runtime"]
    assert "lifecycle_rows" not in persisted["lifecycle_results"]
    assert "asset_results" not in persisted["certification_results"]
    assert "rows" not in persisted["source_row_classifications"]
    assert persisted["identity_runtime"]["seed_summary"]["mapping_request_count"] >= 1
    assert persisted["lifecycle_results"]["lifecycle_row_count"] >= 1
    assert persisted["source_row_classifications"]["row_count"] == 2


def test_cli_prints_bounded_summary_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["RESEARCH_DATA_ROOT"] = str(storage_root)
    env.pop("AUTOMATION_DATA_DIR", None)

    completed = subprocess.run(
        [
            str(repo_root / ".venv" / "bin" / "python"),
            "-m",
            "scripts.run_oddswarehouse_nfl_basic_pilot",
            "--source",
            str(csv_path),
            "--limit",
            "2",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert "report_path" in payload
    assert "identity_runtime" not in payload
    assert "validation" not in payload
    assert "raw_acquisition_result" not in payload


def test_dataset_identity_uses_full_source_coverage_for_production_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = [
        _sample_workbook_rows()[0],
        _sample_workbook_rows()[1],
        _row_with(_sample_workbook_rows()[2], **{"Game ID": 2097, "Date": "20250907"}),
    ]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_root / "historical" / "oddswarehouse.sqlite",
        lakehouse_root=storage_root / "lakehouse" / "oddswarehouse",
        bronze_raw_root=storage_root / "bronze" / "oddswarehouse",
        limit=2,
    )

    assert report["ok"] is True
    assert report["dataset_identity"]["dataset_id"] == "dataset.sports.nfl.oddswarehouse.nfl_basic.historical"
    assert report["dataset_identity"]["dataset_alias"] == "dataset.sports.nfl.oddswarehouse.nfl_basic.current"
    assert report["dataset_identity"]["report_catalog_name"] == "oddswarehouse_nfl_basic_historical"
    assert report["dataset_identity"]["full_source_season_label"] == "2009-2025"
    assert report["dataset_identity"]["selected_season_label"] == "2009"
    assert report["dataset_identity"]["full_source_date_label"] == "20090920-20250907"
    assert report["dataset_identity"]["selected_date_label"] == "20090920"


def test_raw_acquisition_reuses_semantic_bundle_with_digest_drift_and_prefers_oldest_duplicate_version(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)
    source_bundle_id = _build_source_bundle_id(profile, selected_rows=selected_rows, selection=selection)
    selected_profile = _selected_source_profile(profile, selected_rows=selected_rows, selection=selection)
    source_bundle = _source_bundle_from_source_profile(
        selected_profile,
        source_bundle_id,
        "2026-08-10T15:41:56Z",
    )
    oddswarehouse_ingest.get_nfl_p0_market_profile()

    with HistoricalDatasetAcquisitionRuntime(storage_path=storage_path) as runtime:
        first = runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id="sports:nfl",
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )
        assert first["status"] == "raw_cache_ready"

        version_row = dict(
            runtime.platform.store.fetch(
                "dataset_versions",
                where="version_id = ?",
                params=[first["dataset_version"]["version_id"]],
                limit=1,
            )[0]
        )
        validation_row = dict(
            runtime.platform.store.fetch(
                "validation_results",
                where="validation_id = ?",
                params=[first["validation_result"]["validation_id"]],
                limit=1,
            )[0]
        )
        raw_rows = runtime.platform.store.fetch(
            "raw_records",
            where="dataset_id = ? AND version_id = ?",
            params=[first["contract"]["dataset_id"], first["dataset_version"]["version_id"]],
            order_by="row_index ASC",
        )

        original_metadata = HistoricalDatasetAcquisitionRuntime._version_metadata_payload(version_row)
        drifted_metadata = dict(original_metadata)
        drifted_metadata["source_bundle_digest"] = "legacy-digest-drift"
        version_row["metadata_json"] = json.dumps(drifted_metadata, sort_keys=True)
        runtime.platform.store.upsert("dataset_versions", version_row, key_columns=("version_id",))

        duplicate_version_id = f"{first['contract']['dataset_id']}.v002"
        duplicate_snapshot_id = f"{first['contract']['dataset_id']}.snapshot.v002"
        duplicate_lineage_id = f"{first['contract']['dataset_id']}.lineage.v002"
        duplicate_validation_id = f"{duplicate_version_id}.validation"
        duplicate_created_at = "2026-08-10T15:42:56Z"

        duplicate_validation_row = dict(validation_row)
        duplicate_validation_row["validation_id"] = duplicate_validation_id
        duplicate_validation_row["version_id"] = duplicate_version_id
        duplicate_validation_row["snapshot_id"] = duplicate_snapshot_id
        duplicate_validation_row["lineage_id"] = duplicate_lineage_id
        duplicate_validation_row["created_at"] = duplicate_created_at
        duplicate_validation_row["updated_at"] = duplicate_created_at
        runtime.platform.store.upsert("validation_results", duplicate_validation_row, key_columns=("validation_id",))

        duplicate_version_row = dict(version_row)
        duplicate_version_row["version_id"] = duplicate_version_id
        duplicate_version_row["version_number"] = 2
        duplicate_version_row["validation_id"] = duplicate_validation_id
        duplicate_version_row["snapshot_id"] = duplicate_snapshot_id
        duplicate_version_row["lineage_id"] = duplicate_lineage_id
        duplicate_version_row["created_at"] = duplicate_created_at
        duplicate_version_row["updated_at"] = duplicate_created_at
        duplicate_version_metadata = dict(original_metadata)
        duplicate_version_row["metadata_json"] = json.dumps(duplicate_version_metadata, sort_keys=True)
        runtime.platform.store.upsert("dataset_versions", duplicate_version_row, key_columns=("version_id",))

        for raw_row in raw_rows:
            duplicate_raw_row = dict(raw_row)
            duplicate_raw_row["record_id"] = f"{raw_row['record_id']}.dup"
            duplicate_raw_row["version_id"] = duplicate_version_id
            duplicate_raw_row["snapshot_id"] = duplicate_snapshot_id
            duplicate_raw_row["lineage_id"] = duplicate_lineage_id
            duplicate_raw_row["created_at"] = duplicate_created_at
            duplicate_raw_row["updated_at"] = duplicate_created_at
            runtime.platform.store.upsert("raw_records", duplicate_raw_row, key_columns=("record_id",))

        replay = runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id="sports:nfl",
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )

    assert replay["status"] == "raw_cache_reused"
    assert replay["dataset_version"]["version_id"] == first["dataset_version"]["version_id"]
    assert replay["reuse_match_type"] == "legacy_source_bundle_id"


def test_production_historical_lifecycle_identity_preserves_legacy_pilot_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = [
        _sample_workbook_rows()[0],
        _sample_workbook_rows()[1],
        _row_with(_sample_workbook_rows()[2], **{"Game ID": 2097, "Date": "20250907"}),
    ]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    legacy_assets = (
        (
            "dataset.sports.nfl.oddswarehouse.source_events",
            "OddsWarehouse NFL Source Events",
            "source_event_snapshot",
            "historical_events",
        ),
        (
            "dataset.sports.nfl.oddswarehouse.market_observations",
            "OddsWarehouse NFL Market Observations",
            "market_observation_snapshot",
            "historical_selections",
        ),
        (
            "dataset.sports.nfl.oddswarehouse.event_market_selection_gold",
            "OddsWarehouse NFL Event Market Selection Gold",
            "event_market_selection_gold",
            "historical_event_market_selections",
        ),
    )

    runtime = ResearchAssetLifecycleRuntime(storage_path=storage_path)
    try:
        for asset_id, asset_name, asset_type, market_id in legacy_assets:
            identity = build_research_asset_identity_contract(
                asset_id=asset_id,
                asset_family="dataset",
                market_profile=oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                market=oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_PROFILE_ID,
                league="NFL",
                sport="football",
                season="2009",
                week_or_date="2009-09-10..2009-09-20",
                event_id="oddswarehouse_pilot",
                game_id="",
                market_id=market_id,
                selection="",
                provider=oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_PROVIDER_ID,
                connector=oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_CONNECTOR_ID,
                schema_version=oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_SCHEMA_VERSION,
                lineage_version="oddswarehouse.nfl_basic.2009.pilot.v1",
                asset_name=asset_name,
                asset_type=asset_type,
                participant_id="",
                team_id="",
                market_type=market_id,
            )
            runtime.record_lifecycle_state(
                identity=identity.as_dict(),
                lifecycle_state="research_asset_certified",
                lifecycle_reason="legacy pilot evidence",
                source_bundle={"source_name": "OddsWarehouse NFL Basic", "source_type": "controlled_vendor_workbook", "source_key": "oddswarehouse_nfl_basic", "provider": "oddswarehouse"},
                raw_acquisition_result={"batch_id": "oddswarehouse.batch.legacy"},
                created_at="2026-08-09T21:36:40Z",
            )
    finally:
        runtime.close()

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )

    store = create_local_storage_engine(storage_path)
    try:
        lifecycle_rows = store.fetch(
            "research_asset_lifecycles",
            order_by="asset_id ASC",
        )
    finally:
        store.close()

    lifecycle_by_asset_id = {row["asset_id"]: dict(row) for row in lifecycle_rows}

    assert report["ok"] is True
    assert {asset_id for asset_id, *_ in legacy_assets} <= set(lifecycle_by_asset_id)
    assert oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID in lifecycle_by_asset_id
    assert oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_MARKET_OBSERVATIONS_ASSET_ID in lifecycle_by_asset_id
    assert oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_GOLD_ASSET_ID in lifecycle_by_asset_id
    assert lifecycle_by_asset_id[oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID]["season"] == "2009-2025"
    assert lifecycle_by_asset_id[oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_SOURCE_EVENTS_ASSET_ID]["week_or_date"] == "20090920-20250907"


def test_retry_after_incomplete_acquisition_reuses_raw_artifact(tmp_path: Path, monkeypatch) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)
    acquisition_id = _build_acquisition_id(profile, selected_rows=selected_rows, selection=selection)
    source_bundle_id = _build_source_bundle_id(profile, selected_rows=selected_rows, selection=selection)
    selected_profile = _selected_source_profile(profile, selected_rows=selected_rows, selection=selection)
    source_bundle = _source_bundle_from_source_profile(selected_profile, source_bundle_id, "2026-08-06T00:00:00Z")

    with HistoricalDatasetAcquisitionRuntime(storage_path=storage_path) as runtime:
        staged = runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id="sports:nfl",
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )

    assert staged["status"] == "raw_cache_ready"

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )

    assert report["acquisition_id"] == acquisition_id
    assert report["prior_incomplete_acquisition_detected"] is True
    assert report["raw_acquisition_result"]["status"] == "raw_cache_reused"
    assert report["raw_acquisition_result"]["reuse_match_type"] == "source_bundle_id"
    assert report["replay_status"] == "resumed"
    assert "reused_raw_acquisition_cache" in (report["partial_state_action"] or "")


def test_retry_after_incomplete_acquisition_reuses_legacy_raw_cache_fingerprint(tmp_path: Path, monkeypatch) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)
    acquisition_id = _build_acquisition_id(profile, selected_rows=selected_rows, selection=selection)
    source_bundle_id = _build_source_bundle_id(profile, selected_rows=selected_rows, selection=selection)
    selected_profile = _selected_source_profile(profile, selected_rows=selected_rows, selection=selection)
    source_bundle = _source_bundle_from_source_profile(
        selected_profile,
        source_bundle_id,
        "2026-08-06T00:00:00Z",
        acquisition_id=acquisition_id,
        batch_id=acquisition_id,
    )

    with HistoricalDatasetAcquisitionRuntime(storage_path=storage_path) as runtime:
        staged = runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id="sports:nfl",
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )
        version_rows = runtime.platform.store.fetch(
            "dataset_versions",
            where="dataset_id = ?",
            params=[staged["contract"]["dataset_id"]],
            order_by="version_number ASC",
        )
        assert len(version_rows) == 1
        version_row = dict(version_rows[0])
        legacy_metadata = HistoricalDatasetAcquisitionRuntime._version_metadata_payload(version_row)
        legacy_metadata["source_bundle_id"] = acquisition_id
        legacy_metadata["source_bundle_digest"] = _legacy_source_bundle_digest(
            source_bundle,
            source_bundle_id=acquisition_id,
        )
        version_row["metadata_json"] = json.dumps(legacy_metadata, sort_keys=True)
        runtime.platform.store.upsert("dataset_versions", version_row, key_columns=("version_id",))

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )

    store = create_local_storage_engine(storage_path)
    try:
        version_rows = store.fetch(
            "dataset_versions",
            where="dataset_id = ?",
            params=["dataset.sports.nfl.oddswarehouse.raw_acquisition_cache"],
            order_by="version_number ASC",
        )
        assert len(version_rows) == 1
    finally:
        store.close()

    assert report["prior_incomplete_acquisition_detected"] is True
    assert report["raw_acquisition_result"]["status"] == "raw_cache_reused"
    assert report["raw_acquisition_result"]["reuse_match_type"] == "legacy_source_bundle_id"
    assert report["replay_status"] == "resumed"


def test_resume_partial_publication_reuses_raw_bundle_and_replaces_legacy_partitions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)
    acquisition_id = _build_acquisition_id(profile, selected_rows=selected_rows, selection=selection)
    source_bundle_id = _build_source_bundle_id(profile, selected_rows=selected_rows, selection=selection)
    selected_profile = _selected_source_profile(profile, selected_rows=selected_rows, selection=selection)
    source_bundle = _source_bundle_from_source_profile(
        selected_profile,
        source_bundle_id,
        "2026-08-06T00:00:00Z",
        acquisition_id=acquisition_id,
        batch_id=acquisition_id,
    )
    oddswarehouse_ingest.get_nfl_p0_market_profile()
    partial_normalized = normalize_oddswarehouse_workbook_rows(
        [selected_rows[0]],
        batch_id=acquisition_id,
        created_at="2026-08-06T00:00:00Z",
        source_file=csv_path.name,
    )

    with HistoricalDatasetAcquisitionRuntime(storage_path=storage_path) as runtime:
        staged = runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id="sports:nfl",
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )

    assert staged["status"] == "raw_cache_ready"
    staged_version_id = staged["dataset_version"]["version_id"]

    store = create_local_storage_engine(storage_path)
    try:
        store.ensure_schema()
        batch_row = oddswarehouse_ingest._acquisition_batch_row(
            batch_id=acquisition_id,
            created_at="2026-08-06T00:00:00Z",
            source_file=csv_path.name,
            source_count=len(selected_profile.get("files") or {}),
            event_count=len(partial_normalized["event_rows"]),
            market_count=len(partial_normalized["market_rows"]),
            selection_count=len(partial_normalized["selection_rows"]),
            gold_count=len(partial_normalized["gold_rows"]),
            rejected_row_count=1,
            workbook_profile=selected_profile["source"],
            csv_profile=selected_profile.get("companion_evidence") or {},
        )
        store.upsert("historical_acquisition_batches", batch_row, key_columns=("batch_id",))
        table_rows = {
            "historical_events": (partial_normalized["event_rows"], ("event_id",)),
            "historical_event_participants": (partial_normalized["participant_rows"], ("participant_id",)),
            "historical_source_event_links": (partial_normalized["event_link_rows"], ("link_id",)),
            "historical_markets": (partial_normalized["market_rows"], ("market_id",)),
            "historical_selections": (partial_normalized["selection_rows"], ("selection_id",)),
            "historical_event_market_selections": (partial_normalized["gold_rows"], ("dataset_row_id",)),
        }
        for table_name, (table_rows_payload, key_columns) in table_rows.items():
            columns = set(store.table_columns(table_name))
            for row in table_rows_payload:
                filtered = {
                    field: value
                    for field, value in _legacy_stage_row(dict(row)).items()
                    if field in columns
                }
                filtered["source_type"] = "controlled_vendor_workbook"
                store.upsert(table_name, filtered, key_columns=key_columns)
    finally:
        store.close()

    identity_runtime = DataIdentityLakehouseRuntime(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
    )
    try:
        legacy_publish = oddswarehouse_ingest._register_identity_and_quality(
            runtime=identity_runtime,
            batch_id=acquisition_id,
            created_at="2026-08-06T00:00:00Z",
            normalized_payload=partial_normalized,
            workbook_profile=selected_profile["source"],
            csv_profile=selected_profile.get("companion_evidence") or {},
        )
        assert legacy_publish["lakehouse_result"]["ok"] is True
    finally:
        identity_runtime.close()

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )

    store = create_local_storage_engine(storage_path)
    try:
        batch_rows = store.fetch(
            "historical_acquisition_batches",
            where="batch_id = ?",
            params=[acquisition_id],
            limit=1,
        )
        raw_partitions = [
            row
            for row in store.fetch(
                "lakehouse_partitions",
                where="dataset_table = ?",
                params=["raw_records"],
                order_by="partition_id ASC",
            )
            if json.loads(row["partition_values_json"]).get("publication_batch") in {acquisition_id, source_bundle_id}
        ]
        assert len(batch_rows) == 1
        assert len(raw_partitions) == 1
        version_rows = store.fetch(
            "dataset_versions",
            where="dataset_id = ?",
            params=["dataset.sports.nfl.oddswarehouse.raw_acquisition_cache"],
            order_by="version_number ASC",
        )
        batch_row = dict(batch_rows[0])
        raw_partition_values = json.loads(raw_partitions[0]["partition_values_json"])
        assert [row["version_id"] for row in version_rows] == [staged_version_id]
        assert batch_row["event_count"] == 2
        assert batch_row["market_count"] == 12
        assert batch_row["selection_count"] == 24
        assert batch_row["certified_row_count"] == 12
        assert batch_row["rejected_row_count"] == 0
        assert raw_partition_values["publication_batch"] == source_bundle_id
        assert store.count("historical_events") == 2
        assert store.count("historical_markets") == 12
        assert store.count("historical_selections") == 24
    finally:
        store.close()

    assert report["ok"] is True
    assert report["acquisition_id"] == acquisition_id
    assert report["prior_incomplete_acquisition_detected"] is True
    assert report["raw_acquisition_result"]["status"] == "raw_cache_reused"
    assert report["replay_status"] == "resumed"
    assert report["new_row_count"] == 1
    assert report["exact_duplicate_count"] == 1
    assert report["conflict_count"] == 0


def test_canonical_csv_exact_replay_and_overlapping_sample_are_idempotent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    first = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )
    store = create_local_storage_engine(storage_path)
    try:
        first_identity_count = store.count("identity_mappings")
        first_partition_count = store.count("lakehouse_partitions")
        first_event_count = store.count("historical_events")
    finally:
        store.close()
    first_parquet_files = _lakehouse_parquet_files(lakehouse_root)

    second = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )
    store = create_local_storage_engine(storage_path)
    try:
        assert store.count("identity_mappings") == first_identity_count
        assert store.count("lakehouse_partitions") == first_partition_count
        assert store.count("historical_events") == first_event_count
    finally:
        store.close()
    second_parquet_files = _lakehouse_parquet_files(lakehouse_root)

    assert first["source_format"] == "csv"
    assert first["selected_row_count"] == 2
    assert first["new_row_count"] == 2
    assert first["exact_duplicate_count"] == 0
    assert first["storage_health"]["configured_via_env_var"] == "RESEARCH_DATA_ROOT"
    assert first["storage_health"]["repository_independent"] is True
    assert first["replay_status"] == "created"
    assert second["acquisition_id"] == first["acquisition_id"]
    assert second["raw_acquisition_result"]["replay_status"] == "IDEMPOTENT_REUSE"
    assert second["replay_status"] == "reused"
    assert second["selected_row_count"] == 2
    assert second["new_row_count"] == 0
    assert second["exact_duplicate_count"] == 2
    assert second["publication_started"] is False
    assert second["publication_committed"] is False
    assert second["created_partition_count"] == 0
    assert second["updated_partition_count"] == 0
    assert second["reused_partition_count"] == 0
    assert second_parquet_files == first_parquet_files

    overlap = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=3,
    )
    store = create_local_storage_engine(storage_path)
    try:
        assert store.count("historical_events") == 3
    finally:
        store.close()

    assert overlap["acquisition_id"] != first["acquisition_id"]
    assert overlap["replay_status"] == "created"
    assert overlap["selected_row_count"] == 3
    assert overlap["new_row_count"] == 1
    assert overlap["exact_duplicate_count"] == 2
    assert overlap["created_partition_count"] > 0


def test_exact_replay_with_repeated_team_aliases_reuses_identity_mappings_and_preserves_run_reports(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _repeated_team_workbook_rows()
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    first = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=3,
    )
    second = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=3,
    )

    store = create_local_storage_engine(storage_path)
    try:
        washington_rows = store.fetch(
            "identity_mappings",
            where="provider = ? AND entity_type = ? AND external_identifier = ?",
            params=["oddswarehouse", "team", "Washington"],
            order_by="revision_number ASC",
        )
        assert len(washington_rows) == 1
    finally:
        store.close()

    assert first["replay_status"] == "created"
    assert second["replay_status"] == "reused"
    assert second["exact_duplicate_count"] == 3
    assert second["publication_started"] is False
    assert second["publication_committed"] is False
    assert second["created_partition_count"] == 0
    assert second["updated_partition_count"] == 0
    assert second["reused_partition_count"] == 0
    assert first["report_path"] != second["report_path"]
    assert first["acquisition_report_path"] == second["acquisition_report_path"]
    assert Path(first["report_path"]).exists()
    assert Path(second["report_path"]).exists()
    assert Path(first["acquisition_report_path"]).exists()
    with Path(first["report_path"]).open("r", encoding="utf-8") as handle:
        first_report = json.load(handle)
    with Path(second["report_path"]).open("r", encoding="utf-8") as handle:
        second_report = json.load(handle)
    assert first_report["run_id"] == first["run_id"]
    assert second_report["run_id"] == second["run_id"]


def test_same_content_different_filename_reuses_bronze_and_raw_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    renamed_csv_path = tmp_path / "NFL_Basic_copy.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)
    _write_canonical_csv(renamed_csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    first = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )
    second = run_oddswarehouse_nfl_basic_pilot(
        renamed_csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )

    assert second["acquisition_id"] == first["acquisition_id"]
    assert second["raw_acquisition_result"]["status"] == "raw_cache_reused"
    assert second["raw_acquisition_result"]["reuse_match_type"] == "source_bundle_id"
    assert second["bronze_file_actions"][0]["status"] == "reused"
    assert second["publication_started"] is False
    assert second["publication_committed"] is False
    assert second["created_partition_count"] == 0
    assert second["updated_partition_count"] == 0
    assert second["reused_partition_count"] == 0
    bronze_files = sorted(path.name for path in bronze_root.rglob("*") if path.is_file())
    assert bronze_files == ["primary_source.csv"]


def test_preflight_publication_failure_leaves_canonical_state_unpublished(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    def _boom(**_: object) -> dict[str, object]:
        raise RuntimeError("simulated_preflight_failure")

    monkeypatch.setattr(oddswarehouse_ingest, "_preflight_governed_publication", _boom)

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_root / "historical" / "oddswarehouse.sqlite",
        lakehouse_root=storage_root / "lakehouse" / "oddswarehouse",
        bronze_raw_root=storage_root / "bronze" / "oddswarehouse",
        limit=2,
    )

    store = create_local_storage_engine(Path(report["storage_path"]))
    try:
        assert store.count("historical_events") == 0
        assert store.count("historical_markets") == 0
        assert store.count("historical_selections") == 0
        assert store.count("historical_certifications") == 0
        assert store.count("research_asset_lifecycles") == 0
        assert store.count("lakehouse_partitions") == 0
    finally:
        store.close()

    assert report["ok"] is False
    assert report["failure_stage"] == "preflight_publication"
    assert report["publication_started"] is False
    assert report["publication_committed"] is False
    assert report["bronze_file_copies"] == []
    assert Path(report["bronze_raw_root"]).exists() is False


def test_publish_failure_after_raw_reuse_leaves_canonical_and_lakehouse_state_unchanged(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    profile = _profile_oddswarehouse_source(csv_path)
    selected_rows, selection = _apply_deterministic_row_limit(profile["source"], limit=2)
    source_bundle_id = _build_source_bundle_id(profile, selected_rows=selected_rows, selection=selection)
    selected_profile = _selected_source_profile(profile, selected_rows=selected_rows, selection=selection)
    source_bundle = _source_bundle_from_source_profile(
        selected_profile,
        source_bundle_id,
        "2026-08-06T00:00:00Z",
    )
    oddswarehouse_ingest.get_nfl_p0_market_profile()

    with HistoricalDatasetAcquisitionRuntime(storage_path=storage_path) as runtime:
        staged = runtime.stage_raw_acquisition_cache(
            source_bundle,
            profile_id="sports:nfl",
            dataset_name="oddswarehouse_nfl_basic_raw_acquisition_cache",
        )
    assert staged["status"] == "raw_cache_ready"

    bronze_actions = oddswarehouse_ingest._copy_bronze_artifacts(
        oddswarehouse_ingest._build_source_artifact_id(profile),
        [
            {
                "source_path": csv_path,
                "source_role": "primary_source",
                "source_format": "csv",
            }
        ],
        bronze_raw_root=bronze_root,
    )
    assert any(action["status"] == "created" for action in bronze_actions)
    bronze_files_before = sorted(path for path in bronze_root.rglob("*") if path.is_file())

    def _boom(self, *args, **kwargs) -> dict[str, object]:
        raise RuntimeError("simulated_publish_failure")

    monkeypatch.setattr(DataIdentityLakehouseRuntime, "publish_lakehouse_views", _boom)

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )

    store = create_local_storage_engine(storage_path)
    try:
        assert store.count("historical_events") == 0
        assert store.count("historical_markets") == 0
        assert store.count("historical_selections") == 0
        assert store.count("historical_event_market_selections") == 0
        assert store.count("lakehouse_partitions") == 0
    finally:
        store.close()

    bronze_files_after = sorted(path for path in bronze_root.rglob("*") if path.is_file())
    assert bronze_files_after == bronze_files_before
    assert _lakehouse_parquet_files(lakehouse_root) == []
    assert report["ok"] is False
    assert report["failure_stage"] == "persist_canonical_rows"
    assert report["failure_type"] == "RuntimeError"
    assert report["failure_message"] == "simulated_publish_failure"
    assert report["publication_started"] is True
    assert report["publication_committed"] is False
    assert report["raw_acquisition_result"]["status"] == "raw_cache_reused"
    assert report["bronze_file_actions"][0]["status"] == "reused"


def test_legacy_semantic_stage_rows_replay_without_conflict(tmp_path: Path) -> None:
    normalized = normalize_oddswarehouse_workbook_rows(
        [_sample_workbook_rows()[0]],
        batch_id="oddswarehouse.batch.legacy",
        created_at="2026-08-08T00:00:00Z",
        source_file="NFL_Basic.csv",
    )
    storage_path = tmp_path / "legacy_stage.sqlite"
    store = create_local_storage_engine(storage_path)
    try:
        store.ensure_schema()
        table_rows = {
            "historical_events": (normalized["event_rows"], ("event_id",)),
            "historical_event_participants": (normalized["participant_rows"], ("participant_id",)),
            "historical_source_event_links": (normalized["event_link_rows"], ("link_id",)),
            "historical_markets": (normalized["market_rows"], ("market_id",)),
            "historical_selections": (normalized["selection_rows"], ("selection_id",)),
            "historical_event_market_selections": (normalized["gold_rows"], ("dataset_row_id",)),
        }
        for table_name, (rows, key_columns) in table_rows.items():
            columns = set(store.table_columns(table_name))
            for row in rows:
                filtered = {
                    field: value
                    for field, value in _legacy_stage_row(dict(row)).items()
                    if field in columns
                }
                filtered["source_type"] = "controlled_vendor_workbook"
                store.upsert(table_name, filtered, key_columns=key_columns)
            result = oddswarehouse_ingest._persist_classified_rows(
                store,
                table_name,
                rows,
                key_columns=key_columns,
            )
            assert result["counts"]["CONFLICT"] == 0
            assert result["counts"]["EXACT_DUPLICATE"] == len(rows)
            assert all(item["decision"] == SEMANTIC_REUSE for item in result["compatibility_diagnostics"])
            assert all(
                any(
                    diff["field_name"] == "source_type"
                    and diff["classification"] == LINEAGE_METADATA
                    for diff in item["differences"]
                )
                for item in result["compatibility_diagnostics"]
            )
    finally:
        store.close()


def test_exact_replay_reuses_legacy_workbook_source_type_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()[:2]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    first = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )
    parquet_before = _lakehouse_parquet_files(lakehouse_root)

    store = create_local_storage_engine(storage_path)
    try:
        legacy_tables = (
            "historical_events",
            "historical_event_participants",
            "historical_source_event_links",
            "historical_markets",
            "historical_selections",
            "historical_event_market_selections",
            "identity_mappings",
            "identity_reconciliation_results",
            "historical_dataset_rows",
            "feature_snapshots",
        )
        for table_name in legacy_tables:
            if not store.table_exists(table_name):
                continue
            text_columns = [
                row[1]
                for row in store.connection.execute(f"PRAGMA table_info({table_name})").fetchall()
                if str(row[2]).upper() == "TEXT"
            ]
            for column_name in text_columns:
                store.connection.execute(
                    f"UPDATE {table_name} SET {column_name} = REPLACE({column_name}, 'controlled_vendor_file', 'controlled_vendor_workbook')"
                )
        store.connection.commit()
        shutil.rmtree(lakehouse_root, ignore_errors=True)
        if store.table_exists("lakehouse_partitions"):
            store.connection.execute("DELETE FROM lakehouse_partitions")
            store.connection.commit()
    finally:
        store.close()
    identity_runtime = DataIdentityLakehouseRuntime(
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
    )
    try:
        legacy_publish = identity_runtime.publish_lakehouse_views()
        assert legacy_publish["ok"] is True
    finally:
        identity_runtime.close()

    replay = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=2,
    )
    parquet_after = _lakehouse_parquet_files(lakehouse_root)

    assert first["ok"] is True
    assert replay["ok"] is True
    assert replay["replay_status"] == "reused"
    assert replay["raw_acquisition_result"]["status"] == "raw_cache_reused"
    assert replay["new_row_count"] == 0
    assert replay["exact_duplicate_count"] == 2
    assert replay["conflict_count"] == 0
    assert replay["publication_started"] is False
    assert replay["publication_committed"] is False
    assert replay["created_partition_count"] == 0
    assert replay["updated_partition_count"] == 0
    assert replay["reused_partition_count"] == 0
    assert parquet_after == parquet_before


def test_historical_aliases_and_extended_season_windows_validate_and_normalize(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = [
        _row_with(
            _sample_workbook_rows()[0],
            **{
                "Game ID": 3001,
                "Date": "20200829",
                "Away Team": "L.A. Rams",
                "Home Team": "Las Vegas",
            },
        ),
        _row_with(
            _sample_workbook_rows()[1],
            **{
                "Game ID": 3002,
                "Date": "20150125",
                "Away Team": "Team Rice",
                "Home Team": "Team Sanders",
            },
        ),
        _row_with(
            _sample_workbook_rows()[2],
            **{
                "Game ID": 3003,
                "Date": "20100131",
                "Away Team": "AFC",
                "Home Team": "NFC",
            },
        ),
    ]
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    profile = _profile_oddswarehouse_source(csv_path)
    validation = validate_oddswarehouse_source_profile(profile)

    assert validation["ok"] is True
    assert validation["rejected_rows"] == []
    normalized = normalize_oddswarehouse_workbook_rows(
        validation["accepted_rows"],
        batch_id="oddswarehouse.batch.aliases",
        created_at="2026-08-13T00:00:00Z",
        source_file=csv_path.name,
    )
    event_rows = normalized["event_rows"]
    participant_rows = normalized["participant_rows"]

    assert {row["season_type"] for row in event_rows} == {"preseason", "postseason"}
    assert {row["season"] for row in event_rows} == {2009, 2014, 2020}
    assert {
        row["team_id"]
        for row in participant_rows
    } >= {"LAR", "LV", "TEAM_RICE", "TEAM_SANDERS", "AFC", "NFC"}


def test_dataset_certification_and_repository_owned_retrieval_use_canonical_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rows = _sample_workbook_rows()
    csv_path = tmp_path / "NFL_Basic.csv"
    storage_root = tmp_path / "research-data"
    storage_root.mkdir()
    monkeypatch.setenv("RESEARCH_DATA_ROOT", str(storage_root))
    monkeypatch.delenv("AUTOMATION_DATA_DIR", raising=False)
    _write_canonical_csv(csv_path, rows)

    storage_path = storage_root / "historical" / "oddswarehouse.sqlite"
    lakehouse_root = storage_root / "lakehouse" / "oddswarehouse"
    bronze_root = storage_root / "bronze" / "oddswarehouse"

    report = run_oddswarehouse_nfl_basic_pilot(
        csv_path,
        storage_path=storage_path,
        lakehouse_root=lakehouse_root,
        bronze_raw_root=bronze_root,
        limit=3,
    )
    certification = oddswarehouse_ingest.certify_oddswarehouse_nfl_basic_historical_dataset(
        storage_path=storage_path,
        batch_id=report["acquisition_id"],
        created_at="2026-08-13T00:00:00Z",
    )
    query = oddswarehouse_ingest.query_oddswarehouse_nfl_basic_dataset(
        storage_path=storage_path,
        season=2009,
        limit=10,
    )
    team_query = oddswarehouse_ingest.query_oddswarehouse_nfl_basic_dataset(
        storage_path=storage_path,
        team=query["rows"][0]["home_team"],
        limit=10,
    )
    traced = oddswarehouse_ingest.trace_oddswarehouse_nfl_basic_dataset_row(
        query["rows"][0]["dataset_row_id"],
        storage_path=storage_path,
    )

    store = create_local_storage_engine(storage_path)
    try:
        certification_rows = store.fetch(
            "historical_certifications",
            where="version_id = ?",
            params=[oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION],
            order_by="created_at DESC",
        )
        dataset_rows = store.fetch(
            "dataset_registry",
            where="dataset_id = ?",
            params=[oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_DATASET_ID],
            limit=1,
        )
        lifecycle_rows = store.fetch(
            "research_asset_lifecycles",
            where="asset_id = ?",
            params=[oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_DATASET_ID],
            limit=1,
        )
        version_rows = store.fetch(
            "dataset_versions",
            where="version_id = ?",
            params=[oddswarehouse_ingest.ODDSWAREHOUSE_NFL_BASIC_DATASET_VERSION],
            limit=1,
        )
    finally:
        store.close()

    assert report["ok"] is True
    assert certification["ok"] is True
    assert certification["status"] == "certified"
    assert certification_rows
    assert dataset_rows
    assert lifecycle_rows
    assert version_rows
    assert query["ok"] is True
    assert query["row_count"] > 0
    assert all(row["season"] == 2009 for row in query["rows"])
    assert team_query["ok"] is True
    assert team_query["row_count"] > 0
    assert traced["ok"] is True
    assert traced["dataset_certification"]["certification_status"] == "certified"
    assert traced["source_artifact"]["source_sha256"]
    assert traced["bronze_raw_record"]
    assert lifecycle_rows[0]["lifecycle_state"] == "dataset_certified"
