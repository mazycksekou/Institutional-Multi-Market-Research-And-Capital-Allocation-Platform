import unittest

from automation_scheduler.mlb_structured_seed_adapters import (
    WikidataMlbSeedAdapter,
    WikipediaMlbSeedAdapter,
    adapter_by_id,
    build_mlb_structured_seed_adapter_report,
)
from automation_scheduler.mlb_structured_seed_sources import (
    build_mlb_structured_seed_source_report,
    mlb_structured_seed_sources,
)


class TestMlbStructuredSeedAdapters(unittest.TestCase):
    def test_structured_seed_source_report_distinguishes_cc0_and_supplemental_only(self):
        report = build_mlb_structured_seed_source_report()
        self.assertEqual(report["structured_seed_sources_checked"], len(mlb_structured_seed_sources()))
        self.assertIn("wikidata_mlb_seed", report["structured_seed_sources_used"])
        blocked = {row["source_id"]: row for row in report["structured_seed_sources_blocked"]}
        self.assertIn("wikipedia_mlb_seed", blocked)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])

    def test_adapter_by_id_returns_expected_types(self):
        wikidata = adapter_by_id("wikidata_mlb_seed")
        wikipedia = adapter_by_id("wikipedia_mlb_seed")
        self.assertIsInstance(wikidata, WikidataMlbSeedAdapter)
        self.assertIsInstance(wikipedia, WikipediaMlbSeedAdapter)

    def test_adapter_report_exposes_readonly_seed_flags(self):
        report = build_mlb_structured_seed_adapter_report()
        self.assertTrue(report["ok"])
        self.assertIn("wikidata_license_status", report)
        self.assertFalse(report["wikipedia_parses_article_prose"])
        self.assertTrue(report["wikipedia_attribution_required"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])


if __name__ == "__main__":
    unittest.main()
