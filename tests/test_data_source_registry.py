import unittest

from automation_scheduler.data_source_registry import MANDATORY_LANES, build_registry_report


class TestDataSourceRegistry(unittest.TestCase):
    def setUp(self):
        self.report = build_registry_report()
        self.lanes = {lane["lane_id"]: lane for lane in self.report["lanes"]}
        self.sources = self.report["sources"]

    def test_every_supported_module_has_lane(self):
        expected = {lane["lane_id"] for lane in MANDATORY_LANES}
        self.assertEqual(set(self.lanes), expected)
        self.assertEqual(self.report["total_lanes"], len(expected))

    def test_empty_lanes_are_present_and_need_research(self):
        for lane_id in ("officials", "injuries", "lineups", "news_context"):
            lane = self.lanes[lane_id]
            self.assertEqual(lane["source_candidates"], [])
            self.assertEqual(lane["lane_status"], "needs_external_research")
            self.assertEqual(lane["adapter_status"], "blocked_pending_source")

    def test_blocked_and_future_lanes_keep_adapters_disabled(self):
        for lane in self.report["lanes"]:
            if lane["lane_status"] in {"needs_external_research", "future_vendor_needed"}:
                self.assertEqual(lane["adapter_status"], "blocked_pending_source")
        future_sources = [src for src in self.sources if src["future_source_candidate"]]
        self.assertGreater(len(future_sources), 0)
        self.assertTrue(all(src["enabled"] is False for src in future_sources))

    def test_access_policy_disables_restricted_candidates(self):
        restricted = {
            "paid_candidate",
            "partner_candidate",
            "institutional_vendor_candidate",
            "broker_data_candidate",
            "sportsbook_account_candidate",
            "internal_proprietary_candidate",
        }
        for source in self.sources:
            if source["source_access_type"] in restricted:
                self.assertFalse(source["enabled"])
                self.assertFalse(source["current_phase_allowed"])
            if source["trial_only"] or source["credit_card_required"]:
                self.assertFalse(source["current_phase_allowed"])
                self.assertFalse(source["enabled"])
            if source["requires_terms_review"]:
                self.assertFalse(source["enabled"])
            if source["enabled"]:
                self.assertEqual(source["approval_status"], "approved_for_research")
                self.assertTrue(source["current_phase_allowed"])

    def test_source_shape_and_safety_flags(self):
        source = self.sources[0]
        for key in (
            "source_id",
            "display_name",
            "module_lane",
            "source_category",
            "source_access_type",
            "auth_type",
            "env_var_name",
            "current_phase_allowed",
            "future_source_candidate",
            "approval_status",
            "enabled",
            "provider_write",
            "execution_allowed",
            "raw_payload_persistence_allowed",
            "coverage",
            "freshness",
            "limits",
            "legal_terms",
            "model_mapping",
            "quality",
        ):
            self.assertIn(key, source)
        self.assertFalse(self.report["provider_write"])
        self.assertFalse(self.report["execution_allowed"])
        self.assertFalse(self.report["live_execution_enabled"])

    def test_expanded_public_api_sources_are_registered_and_disabled(self):
        source_ids = {source["source_id"] for source in self.sources}
        for source_id in (
            "collegefootballdata_ncaaf",
            "mlb_stats_api",
            "nhl_public_api",
            "coingecko_crypto_prices",
            "binance_public_market_data",
            "defillama",
            "alpha_vantage_market_data",
            "sec_edgar_data",
            "fred_macro_rates",
            "open_meteo",
            "marketaux",
        ):
            self.assertIn(source_id, source_ids)
        for source in self.sources:
            self.assertFalse(source["enabled"])
            self.assertFalse(source["provider_write"])
            self.assertFalse(source["execution_allowed"])
            self.assertFalse(source["raw_payload_persistence_allowed"])


if __name__ == "__main__":
    unittest.main()
