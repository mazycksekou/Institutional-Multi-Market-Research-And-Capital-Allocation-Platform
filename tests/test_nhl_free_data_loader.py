import unittest
from unittest.mock import patch

from automation_scheduler.nhl_free_data_loader import load_nhl_lane_records


FAKE_BUNDLE = {
    "ok": True,
    "context": {"sample_game": {"id": 1, "season": 20252026, "homeTeam": {"id": 10, "abbrev": "CAR"}, "awayTeam": {"id": 20, "abbrev": "FLA"}}},
    "boxscore": {
        "json_payload": {
            "id": 1,
            "homeTeam": {"id": 10, "abbrev": "CAR", "score": 4, "sog": 30},
            "awayTeam": {"id": 20, "abbrev": "FLA", "score": 3, "sog": 28},
        }
    },
}


class TestNhlFreeDataLoader(unittest.TestCase):
    def test_team_box_loader_normalizes_two_rows(self):
        lane = {
            "lane_name": "team_box_scores",
            "candidate_source_name": "NHL public API",
            "source_url_hash": "hash",
        }
        with patch("automation_scheduler.nhl_free_data_loader.build_nhl_source_bundle", return_value=FAKE_BUNDLE):
            result = load_nhl_lane_records(lane, cache={})
        self.assertTrue(result["ok"])
        self.assertEqual(result["normalized_record_count"], 2)


if __name__ == "__main__":
    unittest.main()
