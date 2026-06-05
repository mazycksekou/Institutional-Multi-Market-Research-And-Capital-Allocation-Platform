import unittest

from automation_scheduler.soccer_source_exhaustion_query_builder import build_soccer_source_exhaustion_query_plan


class TestSoccerSourceExhaustionQueryBuilder(unittest.TestCase):
    def test_query_plan_contains_required_families_and_breadth(self):
        report = build_soccer_source_exhaustion_query_plan()
        self.assertTrue(report["ok"])
        families = set(report["query_families"])
        self.assertTrue(
            {
                "official_league_team",
                "public_api_docs",
                "github_open_source",
                "csv_parquet_archive",
                "public_pdf_media_guide",
                "structured_wiki_supplemental",
                "dataset_catalog_index",
                "source_specific_terminology",
            }.issubset(families)
        )
        for rows in report["lane_query_index"].values():
            self.assertGreaterEqual(len(rows), 10)


if __name__ == "__main__":
    unittest.main()
