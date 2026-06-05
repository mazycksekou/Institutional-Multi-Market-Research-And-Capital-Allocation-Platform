import unittest

from automation_scheduler.nhl_source_exhaustion_query_builder import build_nhl_source_exhaustion_query_plan


class TestNhlSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_every_lane_gets_broad_query_plan(self):
        plan = build_nhl_source_exhaustion_query_plan()
        self.assertTrue(plan["ok"])
        for lane_key, rows in plan["lane_query_index"].items():
            self.assertGreaterEqual(len(rows), 10, lane_key)
        required = {
            "official_league_team",
            "public_api_docs",
            "github_open_source",
            "csv_parquet_archive",
            "public_pdf_media_guide",
            "structured_wiki_supplemental",
            "dataset_catalog_index",
            "source_specific_terminology",
        }
        self.assertTrue(required.issubset(set(plan["query_families"])))


if __name__ == "__main__":
    unittest.main()
