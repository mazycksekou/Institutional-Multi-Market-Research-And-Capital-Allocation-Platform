from __future__ import annotations

from src.data.oddswarehouse_nfl_basic_ingest import (
    _deterministic_replay_check,
    normalize_oddswarehouse_workbook_rows,
)


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
        }
    ]


def test_normalize_oddswarehouse_workbook_rows_preserves_historical_identity_and_stage_only_timing() -> None:
    normalized = normalize_oddswarehouse_workbook_rows(
        _sample_workbook_rows(),
        batch_id="oddswarehouse.batch.test",
        created_at="2026-07-17T00:00:00Z",
        source_file="pilot.xlsx",
    )

    assert normalized["unresolved_mappings"] == []
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


def test_oddswarehouse_replay_check_ignores_run_specific_lineage_tokens() -> None:
    replay = _deterministic_replay_check(_sample_workbook_rows())

    assert replay["ok"] is True
    assert replay["digest_a"] == replay["digest_b"]
