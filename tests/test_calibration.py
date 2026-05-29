import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.calibration import (
    build_calibration_report,
    load_outcome_records,
    match_outcomes_to_paper_decisions,
    run_calibration_scaffold,
    summarize_outcome_coverage,
)
from automation_scheduler.paper_decision_ledger import persist_paper_decisions_for_review_items


class TestCalibration(unittest.TestCase):
    def test_insufficient_without_labels(self):
        result = run_calibration_scaffold([{"implied_probability": 0.5}])
        self.assertTrue(result["insufficient_data"])
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["metrics"], {})
        self.assertIn("settlement_results", result["next_required_data"])

    def test_computed_with_labels(self):
        result = run_calibration_scaffold([{"implied_probability": 0.6, "final_outcome": 1}, {"implied_probability": 0.4, "final_outcome": 0}])
        self.assertEqual(result["status"], "metrics_ready")
        self.assertIn("brier_score", result["metrics"])

    def test_outcome_matching_and_partial_coverage(self):
        decisions = [
            {"decision_id": "d1", "review_item_id": "r1", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "implied_probability": 0.7, "liquidity_tier": "low_liquidity", "review_priority_score": 65, "close_time": "2026-06-01T00:00:00+00:00"},
            {"decision_id": "d2", "review_item_id": "r2", "provider": "sharp_sportsbook", "market_type": "sports_pregame_main", "ticker": "S1", "implied_probability": 0.4, "review_priority_score": 55},
        ]
        outcomes = [{"review_item_id": "r1", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "close_time": "2026-06-01T00:00:00+00:00", "final_outcome": 1, "settled_at": "2026-05-29T00:00:00+00:00"}]
        matched = match_outcomes_to_paper_decisions(decisions, outcomes)
        coverage = summarize_outcome_coverage(decisions, outcomes)
        report = build_calibration_report(paper_decisions=decisions, outcome_records=outcomes, review_items=[])
        self.assertEqual(matched[0]["final_outcome"], 1)
        self.assertIsNone(matched[1].get("final_outcome"))
        self.assertEqual(coverage["settled_count"], 1)
        self.assertEqual(report["status"], "partial_calibration")
        self.assertIn("brier_score", report["metrics"])
        self.assertIn("review_priority_bucket_performance", report["metrics"])
        self.assertIn("low_liquidity", report["metrics"]["performance_by_liquidity_tier"])

    def test_close_time_mismatch_prevents_contract_fallback_match(self):
        decisions = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "close_time": "2026-06-01T00:00:00+00:00", "implied_probability": 0.7}
        ]
        outcomes = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "close_time": "2026-06-02T00:00:00+00:00", "final_outcome": 1}
        ]
        matched = match_outcomes_to_paper_decisions(decisions, outcomes)
        self.assertIsNone(matched[0].get("final_outcome"))

    def test_ambiguous_duplicate_outcomes_are_excluded(self):
        decisions = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "implied_probability": 0.7}
        ]
        outcomes = [
            {"outcome_id": "o1", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "settled_at": "2026-05-29T00:00:00+00:00", "final_outcome": "yes"},
            {"outcome_id": "o1", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "settled_at": "2026-05-29T00:00:00+00:00", "final_outcome": "no"},
        ]
        matched = match_outcomes_to_paper_decisions(decisions, outcomes)
        coverage = summarize_outcome_coverage(decisions, outcomes)
        self.assertEqual(matched[0]["outcome_match_status"], "ambiguous")
        self.assertIsNone(matched[0].get("final_outcome"))
        self.assertEqual(coverage["ambiguous_matches_count"], 1)

    def test_newest_duplicate_match_is_used_deterministically(self):
        decisions = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "implied_probability": 0.7}
        ]
        outcomes = [
            {"outcome_id": "old", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "settled_at": "2026-05-28T00:00:00+00:00", "final_outcome": "no"},
            {"outcome_id": "new", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX1", "settled_at": "2026-05-29T00:00:00+00:00", "final_outcome": "yes"},
        ]
        matched = match_outcomes_to_paper_decisions(decisions, outcomes)
        self.assertEqual(matched[0]["matched_outcome_id"], "new")
        self.assertEqual(matched[0]["final_outcome"], "yes")

    def test_no_outcomes_in_store_returns_insufficient_data(self):
        with TemporaryDirectory() as tmp:
            persist_paper_decisions_for_review_items(
                [
                    {
                        "id": "r1",
                        "provider_id": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KX1",
                        "implied_probability": 0.6,
                        "liquidity_tier": "very_low_liquidity",
                        "review_priority_score": 58,
                        "execution_allowed": False,
                    }
                ],
                run_id="run-cal",
                base_data_dir=tmp,
            )
            self.assertEqual(load_outcome_records(tmp), [])
            report = build_calibration_report(base_data_dir=tmp)
            self.assertEqual(report["status"], "insufficient_data")
            self.assertEqual(report["paper_decisions_count"], 1)
            self.assertEqual(report["outcome_records_count"], 0)
            self.assertEqual(report["settled_count"], 0)
            self.assertEqual(report["metrics"], {})
            self.assertEqual(report["liquidity_tier_counts"]["very_low_liquidity"], 1)

    def test_persisted_outcome_moves_report_to_partial_calibration(self):
        with TemporaryDirectory() as tmp:
            persist_paper_decisions_for_review_items(
                [
                    {
                        "id": "r1",
                        "provider_id": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KX1",
                        "implied_probability": 0.6,
                        "liquidity_tier": "low_liquidity",
                        "review_priority_score": 58,
                        "execution_allowed": False,
                    },
                    {
                        "id": "r2",
                        "provider_id": "sharp_sportsbook",
                        "market_type": "sports_pregame_main",
                        "ticker": "S1",
                        "implied_probability": 0.4,
                        "review_priority_score": 55,
                        "execution_allowed": False,
                    },
                ],
                run_id="run-cal",
                base_data_dir=tmp,
            )
            from automation_scheduler.outcome_store import ingest_outcome_records

            ingest_outcome_records(
                [
                    {
                        "provider": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KX1",
                        "outcome_status": "settled",
                        "final_outcome": "yes",
                        "settled_at": "2026-05-29T00:00:00+00:00",
                        "source": "local_manual",
                    }
                ],
                source="local_manual",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            report = build_calibration_report(base_data_dir=tmp)
            self.assertEqual(report["status"], "partial_calibration")
            self.assertEqual(report["outcome_records_count"], 1)
            self.assertEqual(report["matched_outcomes_count"], 1)
            self.assertEqual(report["settled_count"], 1)
            self.assertIn("brier_score", report["metrics"])
