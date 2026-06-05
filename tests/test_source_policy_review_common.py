import unittest

from automation_scheduler.source_policy_review_common import (
    completed_sports_allowed_domains,
    completed_sports_allowed_source_ids,
    completed_sports_candidate_source_catalog,
)


class TestSourcePolicyReviewCommon(unittest.TestCase):
    def test_catalog_has_expected_sports_and_candidates(self):
        rows = completed_sports_candidate_source_catalog()
        sports = {row["sport"] for row in rows}
        self.assertIn("nfl", sports)
        self.assertIn("mlb", sports)
        self.assertIn("soccer", sports)
        self.assertGreaterEqual(len(rows), 30)

    def test_allowed_domains_and_source_ids_cover_catalog(self):
        domains = completed_sports_allowed_domains()
        source_ids = completed_sports_allowed_source_ids()
        sample = completed_sports_candidate_source_catalog()[0]
        self.assertIn(sample["source_id"], source_ids)
        self.assertTrue(any(sample["source_domain"] in domain for domain in domains))


if __name__ == "__main__":
    unittest.main()

