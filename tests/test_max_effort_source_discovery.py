import tempfile
import unittest
from pathlib import Path

from automation_scheduler.max_effort_source_discovery import (
    build_remaining_field_gap_index,
    build_source_discovery_log,
    write_source_discovery_log,
)
from automation_scheduler.source_discovery_result_ranker import rank_source_candidates


class TestMaxEffortSourceDiscovery(unittest.TestCase):
    def test_gap_index_and_discovery_log_counts(self):
        gap_index = build_remaining_field_gap_index()
        discovery = build_source_discovery_log(allow_oxylabs=True, allow_paid_retrieval=True)

        self.assertEqual(gap_index["gap_rows_total"], 273)
        self.assertEqual(
            gap_index["gap_index_counts"],
            {
                "true_policy_blocked": 41,
                "fill_now_with_known_source": 161,
                "needs_schema_refactor": 33,
                "needs_manual_csv": 32,
                "needs_paid_retrieval": 6,
            },
        )
        self.assertEqual(discovery["source_queries_run_count"], 3883)
        self.assertEqual(discovery["sources_discovered_count"], 3883)
        self.assertEqual(discovery["sources_accepted_count"], 3849)
        self.assertEqual(discovery["sources_rejected_count"], 34)
        self.assertEqual(discovery["paid_source_enabled_count"], 1)
        self.assertGreaterEqual(discovery["source_discovery_log_entries"][0]["rank_score"], discovery["source_discovery_log_entries"][-1]["rank_score"])

        ranked = rank_source_candidates(
            [
                {"policy_status": "blocked_terms", "confidence": 0.9, "estimated_coverage": 1.0, "accepted_or_rejected": "rejected"},
                {"policy_status": "approved_open_free", "confidence": 0.1, "estimated_coverage": 0.1},
            ]
        )
        self.assertEqual(ranked[0]["policy_status"], "approved_open_free")
        self.assertGreater(ranked[0]["rank_score"], ranked[1]["rank_score"])

    def test_write_source_discovery_log_creates_expected_paths(self):
        report = build_source_discovery_log(allow_oxylabs=True, allow_paid_retrieval=True)
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_source_discovery_log(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())
            self.assertTrue(paths["latest_json_path"].endswith("MAX_EFFORT_SOURCE_DISCOVERY_LOG.json"))
            self.assertTrue(paths["latest_markdown_path"].endswith("MAX_EFFORT_SOURCE_DISCOVERY_LOG.md"))


if __name__ == "__main__":
    unittest.main()
