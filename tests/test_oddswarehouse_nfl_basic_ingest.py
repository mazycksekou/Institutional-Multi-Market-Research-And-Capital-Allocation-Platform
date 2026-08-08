from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

import src.data.oddswarehouse_nfl_basic_ingest as oddswarehouse_ingest
from scripts.run_oddswarehouse_nfl_basic_pilot import build_parser
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
    assert second["created_partition_count"] == 0
    assert second["reused_partition_count"] >= first_partition_count
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
    assert second["created_partition_count"] == 0
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
                store.upsert(table_name, filtered, key_columns=key_columns)
            result = oddswarehouse_ingest._persist_classified_rows(
                store,
                table_name,
                rows,
                key_columns=key_columns,
            )
            assert result["counts"]["CONFLICT"] == 0
            assert result["counts"]["EXACT_DUPLICATE"] == len(rows)
    finally:
        store.close()
