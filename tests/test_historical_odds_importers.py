"""
Tests for automation_scheduler/historical_odds_importers.py.

Uses temporary files (CSV/JSON) with tiny samples.
No external network, no database writes.
"""

from __future__ import annotations

import csv
import json
import math
import tempfile
from pathlib import Path

import pytest

# module under test
import sys
import os

# ensure the parent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.streamlit_dashboard_facade import american_to_implied_probability, decimal_to_implied_probability, odds_to_implied_probability, normalize_team_name, normalize_market_name, normalize_selection_name, build_canonical_historical_odds_row, validate_canonical_historical_odds_row, import_football_data_csv, import_mlb_odds_json, import_sbr_odds_file, import_historical_odds_file, summarize_imported_historical_rows, get_supported_importer_keys, SUPPORTED_IMPORTER_KEYS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, data: object) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------
# 1. Football‑Data CSV → 3 canonical rows  (B365 odds)
# ---------------------------------------------------------------------------


def test_football_data_csv_creates_three_rows() -> None:
    header = [
        "Div",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        "B365H",
        "B365D",
        "B365A",
    ]
    data = [
        ["E0", "2023-08-12", "Arsenal", "Chelsea", "3", "1", "H", "1.50", "4.00", "6.50"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.csv"
        _write_csv(path, header, data)
        rows = import_football_data_csv(path)
    assert len(rows) == 3
    selections = {r["selection"] for r in rows}
    assert selections == {"home", "draw", "away"}


def test_football_data_sport_market() -> None:
    header = [
        "Div",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        "B365H",
        "B365D",
        "B365A",
    ]
    data = [
        ["E0", "2023-08-12", "Arsenal", "Chelsea", "3", "1", "H", "1.50", "4.00", "6.50"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.csv"
        _write_csv(path, header, data)
        rows = import_football_data_csv(path)
    for r in rows:
        assert r["sport"] == "soccer"
        assert r["market"] == "1x2"
        assert r["source_key"] == "football_data_uk"


def test_football_data_implied_prob() -> None:
    header = [
        "Div",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        "B365H",
        "B365D",
        "B365A",
    ]
    data = [
        ["E0", "2023-08-12", "Arsenal", "Chelsea", "0", "0", "D", "2.0", "3.0", "4.0"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.csv"
        _write_csv(path, header, data)
        rows = import_football_data_csv(path)
    home_prob = [r for r in rows if r["selection"] == "home"][0]["market_implied_probability"]
    assert abs(home_prob - 0.5) < 0.01  # 2.0 → 0.5


# ---------------------------------------------------------------------------
# 2. MLB JSON sample
# ---------------------------------------------------------------------------


def test_mlb_json_creates_rows() -> None:
    payload = {
        "events": [
            {
                "home_team": "NY Yankees",
                "away_team": "Boston Red Sox",
                "commence_time": "2024-04-01",
                "league": "MLB",
                "bookmakers": [
                    {
                        "name": "BookA",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "NY Yankees", "price": -110},
                                    {"name": "Boston Red Sox", "price": -105},
                                ],
                            }
                        ],
                    }
                ],
                "raw_event_id": "evt123",
            }
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mlb.json"
        _write_json(path, payload)
        rows = import_mlb_odds_json(path)
    assert len(rows) == 2
    selections = {r["selection"] for r in rows}
    assert selections == {"ny yankees", "boston red sox"}
    assert rows[0]["sport"] == "baseball"
    assert rows[1]["source_key"] == "arnav_mlb_odds_scraper"


# ---------------------------------------------------------------------------
# 3. SBR CSV sample
# ---------------------------------------------------------------------------


def test_sbr_csv_creates_rows() -> None:
    header = ["date", "sport", "league", "home_team", "away_team", "market", "selection", "odds"]
    data = [
        ["2024-06-01", "football", "NFL", "Team X", "Team Y", "moneyline", "Team X", "150"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sbr.csv"
        _write_csv(path, header, data)
        rows = import_sbr_odds_file(path)
    assert len(rows) == 1
    r = rows[0]
    assert r["source_key"] == "sportsbookreview_scraper"
    assert r["sport"] == "football"
    assert r["selection"] == "team x"


# ---------------------------------------------------------------------------
# 4. Odds conversion
# ---------------------------------------------------------------------------


def test_american_positive_odds() -> None:
    # +150 → 100 / (150 + 100) = 0.4
    assert abs(american_to_implied_probability(150) - 0.4) < 1e-9


def test_american_negative_odds() -> None:
    # -150 → 150 / (150 + 100) = 0.6
    assert abs(american_to_implied_probability(-150) - 0.6) < 1e-9


def test_decimal_odds() -> None:
    assert abs(decimal_to_implied_probability(2.0) - 0.5) < 1e-9


# ---------------------------------------------------------------------------
# 5. Validation fails on missing required fields
# ---------------------------------------------------------------------------


def test_validation_missing_required() -> None:
    row = build_canonical_historical_odds_row(
        source_name="test", source_key="x", source_file="f.csv"
    )
    # most fields are None
    val = validate_canonical_historical_odds_row(row)
    assert val["ok"] is False
    assert "event_date" in val["missing_required_fields"]


# ---------------------------------------------------------------------------
# 6. Validation warns on leakage fields
# ---------------------------------------------------------------------------


def test_validation_leakage() -> None:
    row = build_canonical_historical_odds_row(
        source_name="a",
        source_key="b",
        source_file="c.csv",
        sport="soccer",
        league="E0",
        event_date="2023-01-01",
        home_team="A",
        away_team="B",
        market="1x2",
        selection="home",
        odds_at_decision_time=2.0,
        final_result="H",
        features_known_at_decision_time=["final_result", "profit_loss"],
    )
    val = validate_canonical_historical_odds_row(row)
    assert len(val["warnings"]) >= 2


# ---------------------------------------------------------------------------
# 7. Router routes correctly
# ---------------------------------------------------------------------------


def test_router_football() -> None:
    header = [
        "Div",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        "B365H",
        "B365D",
        "B365A",
    ]
    data = [
        ["SC", "2023-01-01", "T1", "T2", "1", "2", "A", "3.0", "4.0", "5.0"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "foot.csv"
        _write_csv(path, header, data)
        rows = import_historical_odds_file("football_data_uk", path)
    assert len(rows) == 3


def test_router_mlb() -> None:
    payload = {"events": []}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mlb.json"
        _write_json(path, payload)
        rows = import_historical_odds_file("arnav_mlb_odds_scraper", path)
    assert rows == []


def test_router_sbr() -> None:
    header = ["date", "sport", "league", "home_team", "away_team", "market", "selection", "odds"]
    data = [["2024-01-01", "baseball", "MLB", "A", "B", "moneyline", "A", "-110"]]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sbr.csv"
        _write_csv(path, header, data)
        rows = import_historical_odds_file("sportsbookreview_scraper", path)
    assert len(rows) == 1


def test_router_unknown_key() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "dummy.csv"
        path.write_text("a,b\n1,2")
        with pytest.raises(ValueError):
            import_historical_odds_file("unknown_key", path)


# ---------------------------------------------------------------------------
# 8. Summary
# ---------------------------------------------------------------------------


def test_summary_projection_ready() -> None:
    header = [
        "Div",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        "B365H",
        "B365D",
        "B365A",
    ]
    data = [
        ["E0", "2023-08-12", "Arsenal", "Chelsea", "3", "1", "H", "1.50", "4.00", "6.50"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.csv"
        _write_csv(path, header, data)
        rows = import_football_data_csv(path)
    summary = summarize_imported_historical_rows(rows)
    assert summary["ok"] is True
    assert summary["projection_ready"] is True
    assert summary["rows"] == 3


def test_summary_no_rows() -> None:
    summary = summarize_imported_historical_rows([])
    assert summary["projection_ready"] is False


# ---------------------------------------------------------------------------
# 9. Supported keys
# ---------------------------------------------------------------------------


def test_supported_keys_match() -> None:
    keys = get_supported_importer_keys()
    assert keys == SUPPORTED_IMPORTER_KEYS
    assert "football_data_uk" in keys
    assert "arnav_mlb_odds_scraper" in keys
    assert "sportsbookreview_scraper" in keys


# -- Phase 10H9A hardening tests -------------------------------------------------


def test_football_data_date_normalization() -> None:
    header = [
        "Div","Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR","B365H","B365D","B365A",
    ]
    data = [
        ["E0","31/08/2024","Arsenal","Chelsea","3","1","H","1.5","4.0","6.5"],
        ["E0","01/01/2025","ManU","Liverpool","0","0","D","2.0","3.0","4.0"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "date_test.csv"
        _write_csv(path, header, data)
        rows = import_football_data_csv(path)
    assert len(rows) == 6
    dates = {r["event_date"] for r in rows}
    assert "2024-08-31" in dates
    assert "2025-01-01" in dates


def test_football_data_settlement_fields() -> None:
    header = [
        "Div","Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR","B365H","B365D","B365A",
    ]
    data = [
        ["E0","2023-08-12","Arsenal","Chelsea","3","1","H","1.5","4.0","6.5"],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settle.csv"
        _write_csv(path, header, data)
        rows = import_football_data_csv(path)
    assert len(rows) == 3
    home_row = [r for r in rows if r["selection"]=="home"][0]
    assert home_row["home_score"] == 3
    assert home_row["away_score"] == 1
    assert home_row["final_result"] == "H"
    assert home_row["winner"] == "arsenal"
    draw_row = [r for r in rows if r["selection"]=="draw"][0]
    assert draw_row["home_score"] == 3
    assert draw_row["away_score"] == 1
    assert draw_row["final_result"] == "H"
    away_row = [r for r in rows if r["selection"]=="away"][0]
    assert away_row["final_result"] == "H"
