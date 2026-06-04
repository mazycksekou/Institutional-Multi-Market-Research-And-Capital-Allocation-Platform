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
        self.assertEqual(report["robots_blocked_count"], 13)

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

    def test_wikidata_user_agent_is_descriptive_not_spoofed(self):
        from automation_scheduler.nfl_coaching_adapters import WIKIDATA_USER_AGENT, WIKIDATA_CONTACT_URL

        self.assertIn("betting-stock-api-research-bot", WIKIDATA_USER_AGENT)
        self.assertIn(WIKIDATA_CONTACT_URL, WIKIDATA_USER_AGENT)
        self.assertNotIn("Mozilla", WIKIDATA_USER_AGENT)
        self.assertNotIn("Chrome", WIKIDATA_USER_AGENT)

    def test_rate_limit_429_is_respected_without_retry(self):
        import urllib.error

        def rate_limited(query):
            raise urllib.error.HTTPError(url="https://query.wikidata.org/sparql", code=429, msg="Too Many Requests", hdrs=None, fp=None)

        adapter = adapter_by_id("wikidata_coaching_seed")
        run = adapter.run_structured_seed_import(allow_structured_seed=True, fetch_fn=rate_limited)
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["blocked_reason"], "structured_seed_rate_limited_HTTP_429")
        self.assertEqual(run["provider_calls_attempted"], 1)
        self.assertEqual(run["downloads_attempted"], 1)
        self.assertEqual(run["downloads_succeeded"], 0)
        self.assertFalse(run["spoofing_used"])
        self.assertFalse(run["browser_impersonation_used"])
        self.assertFalse(run["raw_payload_persisted"])

    def test_forbidden_403_is_respected_without_retry(self):
        import urllib.error

        def forbidden(query):
            raise urllib.error.HTTPError(url="https://query.wikidata.org/sparql", code=403, msg="Forbidden", hdrs=None, fp=None)

        adapter = adapter_by_id("wikidata_coaching_seed")
        run = adapter.run_structured_seed_import(allow_structured_seed=True, fetch_fn=forbidden)
        self.assertEqual(run["blocked_reason"], "structured_seed_forbidden_HTTP_403")
        self.assertEqual(run["provider_calls_attempted"], 1)

    # --- Fallback ladder ---
    def test_wdqs_scheduled_respects_retry_after_and_no_retry_spam(self):
        import email.message
        import urllib.error

        def rate_limited(query):
            hdrs = email.message.Message()
            hdrs["Retry-After"] = "120"
            raise urllib.error.HTTPError(url="https://query.wikidata.org/sparql", code=429, msg="Too Many Requests", hdrs=hdrs, fp=None)

        with tempfile.TemporaryDirectory() as tmp:
            adapter = adapter_by_id("wikidata_coaching_seed")
            run = adapter.run_structured_seed_import_scheduled(allow_structured_seed=True, fetch_fn=rate_limited, base_data_dir=tmp, resume=False)
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["blocked_reason"], "structured_seed_rate_limited_HTTP_429")
        self.assertEqual(run["retry_after_seconds"], 120)
        self.assertIn("next_safe_run_time", run)
        self.assertEqual(run["provider_calls_attempted"], 1)
        self.assertEqual(run["downloads_attempted"], 1)

    def test_entity_api_fallback_exists_and_avoids_sparql(self):
        from automation_scheduler.nfl_coaching_adapters import WikidataEntityApiCoachingAdapter

        adapter = adapter_by_id("wikidata_entity_api")
        self.assertIsInstance(adapter, WikidataEntityApiCoachingAdapter)
        with tempfile.TemporaryDirectory() as tmp:
            check = adapter.team_qid_manifest_check(base_data_dir=tmp)
        self.assertFalse(check["uses_sparql"])
        self.assertEqual(check["teams_in_manifest"], 32)

    def test_entity_api_requires_allow_structured_seed(self):
        adapter = adapter_by_id("wikidata_entity_api")
        with tempfile.TemporaryDirectory() as tmp:
            run = adapter.run_entity_seed_import(allow_structured_seed=False, base_data_dir=tmp)
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["blocked_reason"], "structured_seed_disabled_by_default")

    def test_entity_api_missing_qid_does_not_fabricate(self):
        adapter = adapter_by_id("wikidata_entity_api")
        with tempfile.TemporaryDirectory() as tmp:
            run = adapter.run_entity_seed_import(allow_structured_seed=True, base_data_dir=tmp)
        self.assertEqual(run["blocked_reason"], "team_qid_manifest_empty_needs_manual_qid")
        self.assertEqual(run["records_validated"], 0)

    def test_entity_api_normalizes_with_injected_fetch(self):
        from automation_scheduler.nfl_coaching_adapters import read_team_qid_manifest, team_qid_manifest_path

        entities = {
            "Q221196": {"entities": {"Q221196": {"claims": {"P286": [{"id": "stmt$1", "mainsnak": {"datavalue": {"value": {"id": "Q1226299"}}}, "qualifiers": {"P580": [{"datavalue": {"value": {"time": "+2013-09-08T00:00:00Z"}}}], "P582": [{"datavalue": {"value": {"time": "+2014-09-01T00:00:00Z"}}}]}}]}}}},
            "Q1226299": {"entities": {"Q1226299": {"labels": {"en": {"value": "Andy Reid"}}}}},
        }

        def fetch(qid):
            return entities[qid]

        with tempfile.TemporaryDirectory() as tmp:
            from automation_scheduler.nfl_coaching_adapters import generate_team_qid_manifest_template
            generate_team_qid_manifest_template(base_data_dir=tmp)
            path = team_qid_manifest_path(Path(tmp))
            rows = path.read_text(encoding="utf-8").splitlines()
            rows[1] = "Kansas City Chiefs,KC,Q221196,Wikidata,CC0,"
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            adapter = adapter_by_id("wikidata_entity_api")
            run = adapter.run_entity_seed_import(allow_structured_seed=True, entity_fetch_fn=fetch, label_fetch_fn=fetch, persist_preview=True, base_data_dir=tmp)
            loaded = load_validated_coaching_rows(base_data_dir=tmp)
        self.assertEqual(run["status"], "ok")
        self.assertEqual(run["seasons_covered"], ["2013", "2014"])
        self.assertFalse(run["raw_payload_persisted"])
        self.assertFalse(run["uses_sparql"])
        self.assertTrue(all(r["source_license"] == "CC0" for r in loaded))

    def test_dump_fallback_requires_allow_and_blocks_missing_path(self):
        adapter = adapter_by_id("wikidata_local_dump")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(adapter.run_dump_import(allow_local_dump=False, base_data_dir=tmp)["blocked_reason"], "local_dump_not_authorized")
            missing = adapter.run_dump_import(allow_local_dump=True, base_data_dir=tmp)
        self.assertEqual(missing["blocked_reason"], "dump_path_missing")
        self.assertIn("instructions", missing)
        self.assertFalse(missing["uses_sparql"])

    def test_dump_fallback_streams_local_ndjson(self):
        adapter = adapter_by_id("wikidata_local_dump")
        with tempfile.TemporaryDirectory() as tmp:
            dump = Path(tmp) / "tiny_dump.ndjson"
            dump.write_text(
                '[\n'
                '{"id":"Q221196","claims":{"P286":[{"id":"s1","mainsnak":{"datavalue":{"value":{"id":"Q1226299"}}},"qualifiers":{"P580":[{"datavalue":{"value":{"time":"+2013-09-08T00:00:00Z"}}}]}}]}},\n'
                ']\n',
                encoding="utf-8",
            )
            run = adapter.run_dump_import(dump_path=str(dump), allow_local_dump=True, persist_preview=True, base_data_dir=tmp)
        self.assertEqual(run["status"], "ok")
        self.assertGreater(run["entities_scanned"], 0)
        self.assertFalse(run["raw_dump_rows_persisted"])
        self.assertFalse(run["uses_sparql"])

    def test_wikipedia_table_fallback_requires_attribution_and_no_prose(self):
        adapter = adapter_by_id("wikipedia_coaching_tables")
        with tempfile.TemporaryDirectory() as tmp:
            no_fetch = adapter.run_table_import(allow_structured_seed=True, base_data_dir=tmp)
            self.assertEqual(no_fetch["blocked_reason"], "wikipedia_table_fetch_not_configured")
            self.assertFalse(no_fetch["parses_article_prose"])

            def table_fetch(page_title):
                return [{"team": "Kansas City Chiefs", "staff_name": "Andy Reid", "season": "2024", "staff_role": "Head Coach"}]

            run = adapter.run_table_import(allow_structured_seed=True, table_fetch_fn=table_fetch, persist_preview=True, base_data_dir=tmp)
        self.assertEqual(run["status"], "ok")
        self.assertTrue(run["attribution_required"])
        self.assertFalse(run["parses_article_prose"])
        self.assertEqual(run["license_status"], "cc_by_sa")

    def test_generate_manual_templates(self):
        from automation_scheduler.nfl_coaching_adapters import generate_manual_templates

        with tempfile.TemporaryDirectory() as tmp:
            result = generate_manual_templates(base_data_dir=tmp)
            template_files = [Path(tmp, p) for p in result["templates_written"]]
            exists = all(p.exists() for p in template_files)
        self.assertTrue(exists)
        self.assertEqual(len(result["templates_written"]), 3)
        self.assertIn("team_qid_manifest", result)

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
