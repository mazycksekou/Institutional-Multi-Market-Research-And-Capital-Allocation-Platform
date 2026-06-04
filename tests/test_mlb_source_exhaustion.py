import tempfile
import unittest

from automation_scheduler.mlb_open_data_source_exhaustion import (
    audit_candidate_source_families,
    build_source_exhaustion_report,
    build_source_field_diff_report,
    classify_candidate_field_novelty,
)
from automation_scheduler.mlb_open_data_sources import mlb_open_data_sources
from automation_scheduler.mlb_open_data_field_catalog import build_existing_mlb_field_index


class TestMlbSourceExhaustion(unittest.TestCase):
    def test_source_exhaustion_reports_new_safe_redundant_and_blocked_sources(self):
        report = build_source_exhaustion_report()
        self.assertTrue(report["mlb_source_exhaustion_checked"])
        self.assertEqual(report["candidate_sources_found"], len(mlb_open_data_sources()))
        self.assertGreater(report["mlb_new_safe_source_count"], 0)
        self.assertGreaterEqual(report["mlb_blocked_source_count"], 3)
        self.assertIn("market_odds_blocked", {row["source_id"] for row in report["mlb_blocked_sources"]})
        self.assertTrue(report["source_field_diffs"])
        self.assertTrue(report["families"])

    def test_family_audit_groups_source_ids(self):
        families = audit_candidate_source_families()
        family_names = {row["source_family"] for row in families}
        self.assertIn("lahman_database", family_names)
        self.assertIn("mlb_stats_api", family_names)
        self.assertTrue(all(row["source_ids"] for row in families))

    def test_field_diff_and_novelty_helpers_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = build_existing_mlb_field_index(base_data_dir=tmp)
            novelty = classify_candidate_field_novelty(
                {"field_name": "game_id", "join_key": True, "new_entity_coverage": False},
                index,
            )
            diff = build_source_field_diff_report(
                source_id="team_stats_lahman",
                candidate_fields=[{"field_name": "game_id", "join_key": True}],
                base_data_dir=tmp,
                existing_index=index,
            )
        self.assertEqual(novelty["novelty"], "exact_duplicate")
        self.assertFalse(novelty["ingestible"])
        self.assertEqual(diff["duplicate_field_count"], 1)
        self.assertEqual(diff["ingestible_field_count"], 0)


if __name__ == "__main__":
    unittest.main()
