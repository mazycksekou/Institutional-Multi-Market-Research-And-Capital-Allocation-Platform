import unittest

from automation_scheduler.derived_feature_planner import plan_derived_features


class TestDerivedFeaturePlanner(unittest.TestCase):
    def _feature(self, payload, name):
        return {row["feature"]: row for row in payload["features"]}[name]

    def test_final_score_features_are_derivable_without_fabrication(self):
        payload = plan_derived_features(
            available_fields=["home_points", "away_points"],
            requested_features=["final_margin", "total_points", "winner"],
        )
        self.assertEqual(payload["derived_features_available"], ["final_margin", "total_points", "winner"])
        self.assertFalse(payload["raw_payload_included"])
        self.assertFalse(payload["secrets_included"])

    def test_rolling_feature_requires_enough_history(self):
        payload = plan_derived_features(
            available_fields=["points_for"],
            history_rows=[{"points_for": 21}, {"points_for": 28}],
            requested_features=["rolling_points_for"],
        )
        row = self._feature(payload, "rolling_points_for")
        self.assertEqual(row["derivation_status"], "insufficient_history_for_derived_feature")
        self.assertEqual(row["required_history_length"], 3)

    def test_missing_fields_are_explicit(self):
        payload = plan_derived_features(
            available_fields=["points_for"],
            requested_features=["rolling_points_against"],
        )
        row = self._feature(payload, "rolling_points_against")
        self.assertEqual(row["derivation_status"], "missing_required_fields")
        self.assertIn("points_against", row["missing_fields"])

    def test_placeholders_do_not_count_as_real_history(self):
        payload = plan_derived_features(
            available_fields=[],
            history_rows=[{"points_for": "TBD"}, {"points_for": None}, {"points_for": ""}],
            requested_features=["rolling_points_for"],
        )
        row = self._feature(payload, "rolling_points_for")
        self.assertEqual(row["derivation_status"], "missing_required_fields")

    def test_market_implied_probability_when_odds_exist(self):
        payload = plan_derived_features(
            available_fields=["moneyline"],
            requested_features=["market_implied_probability"],
        )
        row = self._feature(payload, "market_implied_probability")
        self.assertEqual(row["derivation_status"], "derivable")


if __name__ == "__main__":
    unittest.main()

