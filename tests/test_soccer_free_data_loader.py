import unittest
from unittest.mock import patch

from automation_scheduler.soccer_free_data_loader import load_soccer_lane_records


FAKE_BUNDLE = {
    "ok": True,
    "football_data_rows": [
        {"Div": "D1", "Date": "18/08/2023", "Time": "20:30", "HomeTeam": "Werder Bremen", "AwayTeam": "Bayern Munich", "FTHG": "0", "FTAG": "4", "FTR": "A", "HTHG": "0", "HTAG": "1", "HTR": "A", "HS": "9", "AS": "17", "HST": "1", "AST": "6", "HF": "10", "AF": "8", "HC": "3", "AC": "6", "HY": "2", "AY": "1", "HR": "0", "AR": "0", "Referee": "Test Ref"},
    ],
    "statsbomb_matches": [
        {"match_id": 1, "match_date": "2024-04-06", "home_team": {"home_team_name": "Union Berlin", "managers": [{"name": "Nenad Bjelica"}]}, "away_team": {"away_team_name": "Bayer Leverkusen", "managers": [{"name": "Xabi Alonso"}]}, "competition_stage": {"name": "Regular Season"}, "stadium": {"name": "Stadium", "country": {"name": "Germany"}}, "referee": {"name": "Benjamin Brand"}},
    ],
    "statsbomb_competition_name": "1. Bundesliga",
    "statsbomb_season_name": "2023/2024",
    "statsbomb_events": {"json_payload": [{"id": "evt-1", "type": {"name": "Shot"}, "team": {"name": "Union Berlin"}, "player": {"name": "Player A"}, "period": 1, "minute": 5, "play_pattern": {"name": "Regular Play"}, "possession_team": {"name": "Union Berlin"}, "shot": {"statsbomb_xg": 0.12, "outcome": {"name": "Saved"}, "body_part": {"name": "Left Foot"}}}]},
    "statsbomb_lineups": {"json_payload": [{"team_name": "Union Berlin", "lineup": [{"player_id": 10, "player_name": "Player A", "jersey_number": 9, "positions": [{"position": "Center Forward", "from": "00:00", "to": "90:00", "start_reason": "Starting XI"}]}]}]},
    "context": {"statsbomb_sample_match_id": 1},
}


class TestSoccerFreeDataLoader(unittest.TestCase):
    def test_schedule_results_loader_returns_rows(self):
        lane = {"lane_name": "schedule_results", "source_url_hash": "hash", "source_id": "soccer_football_data_csv"}
        with patch("automation_scheduler.soccer_free_data_loader.build_soccer_source_bundle", return_value=FAKE_BUNDLE):
            result = load_soccer_lane_records(lane)
        self.assertTrue(result["ok"])
        self.assertEqual(result["normalized_record_count"], 1)


if __name__ == "__main__":
    unittest.main()
