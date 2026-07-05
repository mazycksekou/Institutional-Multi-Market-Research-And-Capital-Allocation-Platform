import unittest

from src.services.streamlit_dashboard_facade import _default_coverage, _source
from src.services.streamlit_dashboard_facade import score_lane, score_source


class TestSourceQualityScoring(unittest.TestCase):
    def test_missing_source_gives_high_research_priority(self):
        scores = score_lane({"source_candidates": [], "verified_sources": [], "future_source_candidates": []})
        self.assertEqual(scores["coverage_score"], 0)
        self.assertGreaterEqual(scores["external_research_priority_score"], 90)

    def test_missing_outcomes_lowers_calibration_value(self):
        without_outcomes = _source(
            source_id="no_outcomes",
            source_name="No outcomes",
            lane_id="test",
            source_access_type="open_public",
            current_phase_allowed=True,
            requires_terms_review=False,
            coverage=_default_coverage(historical=True),
            model_inputs_supported=["schedule"],
            join_keys=["event_id"],
        )
        with_outcomes = _source(
            source_id="with_outcomes",
            source_name="With outcomes",
            lane_id="test",
            source_access_type="open_public",
            current_phase_allowed=True,
            requires_terms_review=False,
            coverage=_default_coverage(historical=True, final_results=True),
            model_inputs_supported=["schedule", "final_results"],
            join_keys=["event_id"],
            outcome_fields_available=["final_result"],
        )
        self.assertLess(
            without_outcomes["quality"]["outcome_availability_score"],
            with_outcomes["quality"]["outcome_availability_score"],
        )

    def test_missing_historical_data_lowers_backfill_score(self):
        source = _source(
            source_id="live_only",
            source_name="Live only",
            lane_id="test",
            source_access_type="open_public",
            current_phase_allowed=True,
            requires_terms_review=False,
            coverage=_default_coverage(live=True),
            model_inputs_supported=["timestamp"],
        )
        self.assertLess(source["quality"]["historical_depth_score"], 50)

    def test_unknown_terms_caps_quality_tier(self):
        source = _source(
            source_id="terms_unknown",
            source_name="Terms unknown",
            lane_id="test",
            source_access_type="open_public",
            current_phase_allowed=True,
            requires_terms_review=True,
            coverage=_default_coverage(historical=True, final_results=True),
            model_inputs_supported=["final_results"],
            join_keys=["event_id"],
        )
        self.assertEqual(source["quality"]["quality_tier"], "candidate")
        self.assertGreaterEqual(source["quality"]["terms_risk_score"], 70)

    def test_no_stable_join_keys_lowers_join_quality(self):
        source = _source(
            source_id="no_join",
            source_name="No join",
            lane_id="test",
            source_access_type="open_public",
            current_phase_allowed=True,
            requires_terms_review=False,
            coverage=_default_coverage(historical=True, final_results=True),
            model_inputs_supported=["final_results"],
            join_keys=[],
        )
        self.assertLess(source["quality"]["join_quality_score"], 25)

    def test_future_vendor_candidate_current_usability_is_zero(self):
        source = _source(
            source_id="future_vendor",
            source_name="Future Vendor",
            lane_id="test",
            source_access_type="institutional_vendor_candidate",
            future_source_candidate=True,
            coverage=_default_coverage(historical=True, live=True, final_results=True),
            model_inputs_supported=["schedule", "final_results"],
            join_keys=["event_id"],
            outcome_fields_available=["final_result"],
        )
        quality = score_source(source, ["schedule", "final_results"])
        self.assertEqual(quality["current_phase_usability_score"], 0)
        self.assertGreater(quality["future_value_score"], 0)

    def test_trial_sources_are_unusable_current_phase(self):
        source = _source(
            source_id="trial",
            source_name="Trial",
            lane_id="test",
            source_access_type="free_tier",
            current_phase_allowed=True,
            trial_only=True,
            credit_card_required=True,
            coverage=_default_coverage(live=True),
        )
        self.assertFalse(source["current_phase_allowed"])
        self.assertEqual(source["quality"]["current_phase_usability_score"], 0)

    def test_crypto_priority_candidate_scores_signal_depth(self):
        source = _source(
            source_id="crypto_priority",
            source_name="Crypto Priority",
            lane_id="cryptocurrency_edge_lab",
            module="cryptocurrency_edge_lab",
            source_category="crypto",
            source_access_type="open_public",
            requires_terms_review=False,
            coverage=_default_coverage(historical=True, live=True, order_book=True, onchain=True, dex=True, final_results=True),
            model_inputs_supported=["ohlcv", "order_book_depth", "onchain_signals", "dex_liquidity", "stablecoin_flows"],
            join_keys=["asset_symbol", "timestamp"],
            outcome_fields_available=["forward_return"],
            historical_backfill_fields_available=["timestamp", "close"],
        )
        self.assertGreaterEqual(source["quality"]["crypto_signal_value_score"], 70)
        self.assertGreaterEqual(source["quality"]["calibration_value_score"], 70)
        self.assertIn(source["quality"]["quality_tier"], {"candidate", "research_only", "high_priority_adapter", "institutional_priority"})

    def test_stock_priority_candidate_scores_fundamental_depth(self):
        source = _source(
            source_id="stock_priority",
            source_name="Stock Priority",
            lane_id="institutional_stock_pro_analyst",
            module="institutional_stock_pro_analyst",
            source_category="stock/fundamentals",
            source_access_type="open_public",
            requires_terms_review=False,
            coverage=_default_coverage(historical=True, live=True, fundamentals=True, filings=True, earnings=True, final_results=True),
            model_inputs_supported=["fundamentals", "sec_filings", "earnings", "valuation"],
            join_keys=["symbol", "cik"],
            outcome_fields_available=["final_price"],
            historical_backfill_fields_available=["filing_date", "period_end"],
        )
        self.assertGreaterEqual(source["quality"]["stock_signal_value_score"], 70)
        self.assertGreaterEqual(source["quality"]["SEC_mapping_score"], 80)


if __name__ == "__main__":
    unittest.main()
