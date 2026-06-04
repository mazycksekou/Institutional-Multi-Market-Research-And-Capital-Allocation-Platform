import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_coaching_sources import (
    COACHING_TARGET_FIELDS,
    MIN_CRAWL_DELAY_SECONDS,
    RESEARCH_USER_AGENT,
    build_nfl_coaching_source_report,
    classify_coaching_source,
    nfl_coaching_sources,
    write_nfl_coaching_source_report,
)
from automation_scheduler.nfl_coaching_adapters import (
    NflCoachingAdapter,
    adapter_by_id,
    build_nfl_coaching_ingestion_report,
)


class TestNflCoachingSources(unittest.TestCase):
    def test_all_coaching_sources_disabled_by_default(self):
        for source in nfl_coaching_sources():
            self.assertFalse(source["enabled"])

    def test_coaching_source_does_not_spoof_user_agent(self):
        for source in nfl_coaching_sources():
            self.assertEqual(source["user_agent"], RESEARCH_USER_AGENT)
            self.assertFalse(source["spoofing_required"])
        adapter = NflCoachingAdapter(nfl_coaching_sources()[0])
        self.assertFalse(adapter.spoofs_user_agent)
        self.assertEqual(adapter.user_agent, "betting-stock-api-research-bot/0.1")

    def test_crawl_delay_at_least_three_seconds(self):
        for source in nfl_coaching_sources():
            self.assertGreaterEqual(source["crawl_delay_seconds"], MIN_CRAWL_DELAY_SECONDS)
        adapter = NflCoachingAdapter(nfl_coaching_sources()[0])
        self.assertGreaterEqual(adapter.crawl_delay_seconds, 3)

    def test_coaching_source_stores_no_raw_html(self):
        for source in nfl_coaching_sources():
            self.assertFalse(source["persists_raw_html"])
            self.assertTrue(source["stores_compact_facts_only"])
        report = build_nfl_coaching_ingestion_report()
        self.assertFalse(report["raw_html_persisted"])
        for run in report["coaching_runs"]:
            self.assertFalse(run["raw_html_persisted"])
            self.assertFalse(run["fetch_attempted"])

    def test_robots_disallow_blocks_source(self):
        classified = classify_coaching_source(
            {"robots_review_status": "disallows_automated_collection", "automation_allowed": True, "structured_data_available": True, "terms_review_status": "terms_unclear", "source_kind": "html_pages"}
        )
        self.assertEqual(classified["blocker"], "robots_disallows_automation")
        self.assertFalse(classified["current_phase_allowed"])

    def test_unverified_license_blocks_open_file(self):
        classified = classify_coaching_source(
            {"source_kind": "open_data_file", "license_status": "license_unverified", "automation_allowed": True, "structured_data_available": True, "terms_review_status": "research_required"}
        )
        self.assertEqual(classified["blocker"], "license_unverified")

    def test_coaching_lane_blocked_with_precise_reason(self):
        report = build_nfl_coaching_source_report()
        self.assertFalse(report["nfl_coaching_data_available"])
        self.assertEqual(report["nfl_coaching_data_blocked_reason"], "no_confirmed_open_terms_safe_coaching_source")
        self.assertEqual(report["coaching_target_fields"], COACHING_TARGET_FIELDS)

    def test_adapter_ingestion_is_blocked_and_safe(self):
        adapter = adapter_by_id("official_team_staff_pages")
        with tempfile.TemporaryDirectory() as tmp:
            run = adapter.run_ingestion(base_data_dir=tmp)
        self.assertEqual(run["status"], "blocked")
        self.assertFalse(run["fetch_attempted"])
        self.assertEqual(run["coaching_fields_ingested"], [])
        self.assertEqual(run["records_validated"], 0)
        self.assertEqual(run["provider_calls_attempted"], 0)
        self.assertEqual(run["downloads_attempted"], 0)
        self.assertFalse(run["provider_write"])
        self.assertFalse(run["execution_allowed"])
        self.assertFalse(run["raw_payload_included"])
        self.assertFalse(run["secrets_included"])

    def test_report_writes_without_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_coaching_source_report(base_data_dir=tmp)
            paths = write_nfl_coaching_source_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()
        self.assertTrue(latest_exists)
        self.assertIn("data_sources/nfl_open_data/coaching_sources/latest.json", paths["latest_json_path"])
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_payload", rendered)


if __name__ == "__main__":
    unittest.main()
