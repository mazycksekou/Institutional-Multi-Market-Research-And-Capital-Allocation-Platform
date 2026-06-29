from src.services.streamlit_dashboard_facade import BACKTEST_FIELD_ALIASES, LEAKAGE_FIELD_ALIASES, REQUIRED_BACKTEST_FIELDS, describe_backtest_schema, missing_required_backtest_fields, normalize_backtest_row, validate_no_leakage_features
from src.services.streamlit_dashboard_facade import replay_rows, run_backtest


def test_backtest_schema_has_required_fields_and_aliases():
    schema = describe_backtest_schema()

    for field in REQUIRED_BACKTEST_FIELDS:
        assert field in schema["required_fields"]
        assert field in BACKTEST_FIELD_ALIASES
        assert BACKTEST_FIELD_ALIASES[field]


def test_backtest_schema_normalizes_aliases():
    row = normalize_backtest_row(
        {
            "event": "event-1",
            "ticker": "KXTEST-1",
            "sport_key": "basketball_nba",
            "competition": "NBA",
            "market_type": "moneyline",
            "timestamp": "2026-01-01T00:00:00Z",
            "american_odds": -110,
            "features": {"pace": 99.1},
            "predicted_probability": 0.56,
            "implied_probability": 0.524,
            "ev_percent": 3.6,
            "paper_stake": 10,
            "result_status": "win",
            "closing_odds": -125,
            "clv_percent": 2.2,
        }
    )

    assert row["event_id"] == "event-1"
    assert row["contract_id"] == "KXTEST-1"
    assert row["sport"] == "basketball_nba"
    assert row["league"] == "NBA"
    assert row["market"] == "moneyline"
    assert row["decision_time"] == "2026-01-01T00:00:00Z"
    assert row["odds_at_decision_time"] == -110
    assert row["recommended_odds"] == -110
    assert row["features_known_at_decision_time"] == {"pace": 99.1}
    assert row["model_probability"] == 0.56
    assert row["market_implied_probability"] == 0.524
    assert row["edge"] == 3.6
    assert row["stake"] == 10
    assert row["final_result"] == "win"
    assert row["closing_line"] == -125
    assert row["clv"] == 2.2


def test_backtest_schema_blocks_leakage_inside_features():
    result = validate_no_leakage_features(
        {
            "event_id": "event-1",
            "features": {
                "pace": 99.1,
                "nested": {
                    "final_result": "win",
                    "closing_odds": -125,
                },
            },
        }
    )

    assert result["ok"] is False
    assert "nested.final_result" in result["leakage_fields"]
    assert "nested.closing_odds" in result["leakage_fields"]


def test_backtest_schema_allows_settlement_fields_outside_features():
    result = validate_no_leakage_features(
        {
            "event_id": "event-1",
            "result_status": "win",
            "closing_odds": -125,
            "clv_percent": 2.2,
            "features": {"pace": 99.1},
        }
    )

    assert result["ok"] is True


def test_backtesting_engine_accepts_alias_rows():
    result = replay_rows(
        [
            {
                "event": "event-1",
                "market_type": "moneyline",
                "odds": -110,
                "closing_odds": -120,
                "predicted_probability": 0.56,
                "result_status": "win",
                "features": {"pace": 99.1},
            }
        ]
    )

    row = result["rows"][0]
    assert row["event_id"] == "event-1"
    assert row["recommended_odds"] == -110
    assert row["model_probability"] == 0.56


def test_backtest_schema_missing_required_fields_reports_canonical_names():
    missing = missing_required_backtest_fields({"event": "event-1", "features": {"pace": 99.1}})

    assert "event_id" not in missing
    assert "contract_id" in missing
    assert "model_probability" in missing
