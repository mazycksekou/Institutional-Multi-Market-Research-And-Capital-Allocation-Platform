import csv
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_coaching_adapters import (
    ManualCsvCoachingImportAdapter,
    NflCoachingAdapter,
    WikidataCoachingSeedAdapter,
    WikipediaCoachingSeedAdapter,
    adapter_by_id,
    build_nfl_coaching_ingestion_report,
    classify_coaching_role,
    expand_coaching_dates_to_team_seasons,
    load_validated_coaching_rows,
    validate_record_shape,
)
from automation_scheduler.nfl_coaching_sources import RESEARCH_USER_AGENT, coaching_source_by_id


def _fake_wikidata(query):
    return {
        "results": {
            "bindings": [
                {
                    "teamLabel": {"value": "Kansas City Chiefs"},
                    "team": {"value": "http://www.wikidata.org/entity/Q221196"},
                    "coachLabel": {"value": "Andy Reid"},
                    "coach": {"value": "http://www.wikidata.org/entity/Q1226299"},
                    "start": {"value": "+2013-09-08T00:00:00Z"},
                    "end": {"value": "+2015-09-01T00:00:00Z"},
                },
                {"teamLabel": {"value": "Chiefs"}, "coachLabel": {"value": ""}},
            ]
        }
    }


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class TestNflCoachingAdapters(unittest.TestCase):
    def test_crawler_uses_truthful_user_agent_and_no_spoofing(self):
        adapter = adapter_by_id("official_team_staff_pages")
        self.assertEqual(adapter.user_agent, RESEARCH_USER_AGENT)
        self.assertFalse(adapter.spoofs_user_agent)
        self.assertFalse(adapter.browser_impersonation_used)
        self.assertNotIn("Mozilla", adapter.user_agent)

    def test_crawl_delay_at_least_three(self):
        for source_id in ("official_team_staff_pages", "official_team_press_releases"):
            adapter = adapter_by_id(source_id)
            self.assertGreaterEqual(adapter.crawl_delay_seconds, 3)

    def test_crawler_enforces_max_pages_per_domain(self):
        adapter = adapter_by_id("official_team_staff_pages")
        crawl = adapter.crawl_allowed_pages(allow_crawl=True)
        self.assertLessEqual(crawl["max_pages_per_domain"], 25)
        self.assertEqual(crawl["pages_fetched"], 0)
        self.assertFalse(crawl["fetch_attempted"])

    def test_robots_disallow_blocks_crawling(self):
        adapter = adapter_by_id("official_team_staff_pages")
        crawl = adapter.crawl_allowed_pages(allow_crawl=True)
        self.assertFalse(crawl["allowed"])
        self.assertFalse(crawl["raw_html_persisted"])

    def test_terms_unclear_blocks_crawling(self):
        adapter = adapter_by_id("official_team_press_releases")
        decision = adapter.validate_source_allowed(allow_crawl=True)
        self.assertFalse(decision["allowed"])

    def test_crawl_not_authorized_without_allow_crawl(self):
        adapter = adapter_by_id("official_nfl_staff_or_news_pages")
        crawl = adapter.crawl_allowed_pages(allow_crawl=False)
        self.assertFalse(crawl["allowed"])

    def test_raw_html_never_persisted(self):
        report = build_nfl_coaching_ingestion_report()
        self.assertFalse(report["raw_html_persisted"])
        for run in report["coaching_runs"]:
            self.assertFalse(run.get("raw_html_persisted", False))
            self.assertFalse(run.get("fetch_attempted", False))

    def test_manual_import_works_with_flag(self):
        rows = [
            {"team": "KC", "season": "2023", "staff_name": "Andy Reid", "staff_role": "Head Coach", "source_label": "manual", "source_license": "CC0"},
            {"team": "KC", "season": "2024", "staff_name": "Andy Reid", "staff_role": "Head Coach", "source_label": "manual", "source_license": "CC0"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            _write_csv(Path(tmp) / "manual_imports" / "nfl_coaching" / "kc.csv", rows)
            adapter = ManualCsvCoachingImportAdapter(coaching_source_by_id("manual_csv_import"))
            run = adapter.run_manual_import(allow_manual_import=True, persist_preview=True, base_data_dir=tmp)
            loaded = load_validated_coaching_rows(base_data_dir=tmp)
        self.assertEqual(run["records_validated"], 2)
        self.assertEqual(run["records_rejected"], 0)
        self.assertFalse(run["raw_html_persisted"])
        self.assertEqual(len(loaded), 2)

    def test_manual_import_blocked_without_flag(self):
        adapter = ManualCsvCoachingImportAdapter(coaching_source_by_id("manual_csv_import"))
        with tempfile.TemporaryDirectory() as tmp:
            run = adapter.run_manual_import(allow_manual_import=False, base_data_dir=tmp)
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["records_validated"], 0)

    def test_manual_import_rejects_missing_license(self):
        rows = [{"team": "KC", "season": "2024", "staff_name": "Coach X", "staff_role": "Head Coach", "source_label": "manual"}]
        with tempfile.TemporaryDirectory() as tmp:
            _write_csv(Path(tmp) / "manual_imports" / "nfl_coaching" / "x.csv", rows)
            adapter = ManualCsvCoachingImportAdapter(coaching_source_by_id("manual_csv_import"))
            run = adapter.run_manual_import(allow_manual_import=True, base_data_dir=tmp)
        self.assertEqual(run["records_validated"], 0)
        self.assertEqual(run["records_rejected"], 1)
        self.assertEqual(run["rejected"][0]["reason"], "missing_source_license")

    def test_validate_record_shape(self):
        ok, _ = validate_record_shape({"team": "KC", "season": "2024", "staff_name": "A", "staff_role": "Head Coach"})
        self.assertTrue(ok)
        bad_season, reason = validate_record_shape({"team": "KC", "season": "x", "staff_name": "A", "staff_role": "HC"})
        self.assertFalse(bad_season)
        self.assertEqual(reason, "invalid_season")
        no_license, reason2 = validate_record_shape({"team": "KC", "season": "2024", "staff_name": "A", "staff_role": "HC"}, require_license=True)
        self.assertFalse(no_license)
        self.assertEqual(reason2, "missing_source_license")

    def test_ambiguous_role_maps_to_unknown(self):
        self.assertEqual(classify_coaching_role("Pass Game Coordinator")["role_group"], "unknown")
        self.assertEqual(classify_coaching_role("Head Coach")["role_group"], "head_coach")
        self.assertEqual(classify_coaching_role("Defensive Coordinator")["role_group"], "defensive_coordinator")
        self.assertTrue(classify_coaching_role("Interim Head Coach")["interim_flag"])

    def test_ingestion_report_safety(self):
        report = build_nfl_coaching_ingestion_report()
        self.assertFalse(report["spoofing_used"])
        self.assertFalse(report["browser_impersonation_used"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertEqual(report["robots_blocked_count"], 10)

    def test_metadata_check_does_not_fetch(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        metadata = adapter.run_metadata_check()
        self.assertFalse(metadata["robots"]["fetched"])
        self.assertEqual(metadata["provider_calls_attempted"], 0)
        self.assertEqual(metadata["downloads_attempted"], 0)
        self.assertFalse(metadata["raw_html_persisted"])

    # --- Wikidata structured seed ---
    def test_wikidata_seed_requires_allow_structured_seed(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        blocked = adapter.run_structured_seed_import(allow_structured_seed=False, fetch_fn=_fake_wikidata)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["blocked_reason"], "structured_seed_disabled_by_default")
        self.assertEqual(blocked["downloads_attempted"], 0)

    def test_wikidata_seed_imports_and_expands_seasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = adapter_by_id("wikidata_coaching_seed")
            run = adapter.run_structured_seed_import(allow_structured_seed=True, max_records=500, persist_preview=True, fetch_fn=_fake_wikidata, base_data_dir=tmp)
            loaded = load_validated_coaching_rows(base_data_dir=tmp)
        self.assertEqual(run["status"], "ok")
        self.assertEqual(run["records_validated"], 3)  # 2013,2014,2015 seasons
        self.assertEqual(run["seasons_covered"], ["2013", "2014", "2015"])
        self.assertEqual(run["teams_covered"], ["Kansas City Chiefs"])
        self.assertEqual(run["downloads_attempted"], 1)
        self.assertEqual(run["downloads_succeeded"], 1)
        self.assertFalse(run["raw_html_persisted"])
        self.assertFalse(run["raw_payload_persisted"])
        self.assertEqual(len(loaded), 3)
        self.assertTrue(all(row["source_license"] == "CC0" for row in loaded))

    def test_tiny_sample_enforces_max_records(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        run = adapter.run_tiny_sample(allow_structured_seed=True, max_records=2, fetch_fn=_fake_wikidata)
        self.assertEqual(run["max_records"], 2)
        self.assertLessEqual(run["records_validated"], 2)

    def test_structured_seed_enforces_max_records(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        run = adapter.run_structured_seed_import(allow_structured_seed=True, max_records=1, fetch_fn=_fake_wikidata)
        self.assertLessEqual(run["records_validated"], 1)

    def test_wikidata_metadata_check_no_download(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        metadata = adapter.run_metadata_check()
        self.assertEqual(metadata["downloads_attempted"], 0)
        self.assertEqual(metadata["provider_calls_attempted"], 0)

    def test_normalized_records_require_source_and_license(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        rows = adapter.normalize_wikidata_records(_fake_wikidata("")["results"]["bindings"])
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row["source_license"], "CC0")
            self.assertEqual(row["provenance_label"], "Wikidata")
            self.assertIn("source_entity_id", row)

    def test_missing_coach_name_is_dropped_not_fabricated(self):
        adapter = adapter_by_id("wikidata_coaching_seed")
        rows = adapter.normalize_wikidata_records(_fake_wikidata("")["results"]["bindings"])
        self.assertTrue(all(row["staff_name"] for row in rows))

    def test_missing_dates_do_not_fabricate_season(self):
        expanded = expand_coaching_dates_to_team_seasons({"team": "KC", "staff_name": "X", "staff_role": "Head Coach"})
        self.assertEqual(expanded[0]["season"], "")
        self.assertEqual(expanded[0]["season_resolution_status"], "requires_season_expansion")

    def test_date_to_season_expansion_with_clear_bounds(self):
        expanded = expand_coaching_dates_to_team_seasons({"start_date": "2013-09-08", "end_date": "2014-09-01"})
        self.assertEqual([row["season"] for row in expanded], ["2013", "2014"])

    def test_wikipedia_adapter_is_supplemental_only(self):
        adapter = adapter_by_id("wikipedia_coaching_seed")
        self.assertIsInstance(adapter, WikipediaCoachingSeedAdapter)
        run = adapter.run_structured_seed_import(allow_structured_seed=True)
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["blocked_reason"], "supplemental_only_no_record_ingestion")
        self.assertFalse(run["attribution"]["parses_article_prose"])
        self.assertTrue(run["attribution"]["attribution_required"])
        self.assertEqual(run["records_validated"], 0)


if __name__ == "__main__":
    unittest.main()
