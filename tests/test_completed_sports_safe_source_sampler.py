import unittest

from automation_scheduler.completed_sports_safe_source_sampler import sample_completed_sports_source


class TestCompletedSportsSafeSourceSampler(unittest.TestCase):
    def test_metadata_only_candidate_emits_metadata_row(self):
        candidate = {
            "sport": "nfl",
            "source_id": "nflverse_release_data",
            "source_name": "nflverse releases",
            "source_url": "https://github.com/nflverse/nflverse-data/releases",
            "source_path_or_path_pattern": "/nflverse/nflverse-data/releases",
            "field_group": "injuries",
            "repo_field_mapping": ["injuries"],
            "cutoff_safe": True,
            "usable_for_prematch_model": True,
            "usable_for_postmatch_training_only": False,
            "expected_calibration_value": "high",
            "required_attribution_text_or_url_hash": "hash",
            "sample_strategy": "metadata_only",
            "primary_transport": "web_scraper_api",
            "source_domain": "github.com",
        }
        row = sample_completed_sports_source(candidate, {"path_level_decision": "accepted_for_metadata_only"})
        self.assertEqual(row["normalized_records_added"], 1)
        self.assertEqual(row["final_action"], "sampled_and_ready_for_safe_state")


if __name__ == "__main__":
    unittest.main()

