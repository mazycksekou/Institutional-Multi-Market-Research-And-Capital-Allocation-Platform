import unittest

from automation_scheduler.data_source_registry import STOCK_ANALYST_SCORING_DIMENSIONS, build_env_var_registry, build_registry, build_source_priorities


class TestInstitutionalStockProAnalystRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = build_registry()
        self.lanes = {lane["lane_id"]: lane for lane in self.registry["lanes"]}
        self.sources = {source["source_id"]: source for source in self.registry["sources"]}

    def test_stock_pro_analyst_lane_exists_and_is_planning_only(self):
        lane = self.lanes["institutional_stock_pro_analyst"]
        self.assertEqual(lane["module_priority"], "high")
        self.assertEqual(lane["module_status"], "planning_registry_only")
        self.assertEqual(lane["adapter_status"], "not_started")
        self.assertFalse(lane["enabled"])
        self.assertFalse(lane["provider_write"])
        self.assertFalse(lane["execution_allowed"])
        for score in STOCK_ANALYST_SCORING_DIMENSIONS:
            self.assertIn(score, lane["planned_scores"])

    def test_stock_sources_are_disabled_and_market_data_only_when_broker_capable(self):
        for source_id in ("alpha_vantage_market_data", "financial_modeling_prep_market_data", "sec_edgar_data", "fred_macro_rates"):
            self.assertIn(source_id, self.sources)
            self.assertFalse(self.sources[source_id]["enabled"])
            self.assertFalse(self.sources[source_id]["provider_write"])
            self.assertFalse(self.sources[source_id]["execution_allowed"])
            self.assertFalse(self.sources[source_id]["raw_payload_persistence_allowed"])
        for source_id in ("tradier_market_data_only", "alpaca_market_data_only"):
            forbidden = set(self.sources[source_id]["forbidden_actions"])
            self.assertTrue({"place_order", "cancel_order", "modify_order", "trade", "withdraw", "deposit"}.issubset(forbidden))

    def test_stock_env_vars_are_names_only(self):
        env_report = build_env_var_registry(module="institutional_stock_pro_analyst")
        names = {row["env_var_name"] for row in env_report["env_vars"]}
        self.assertIn("ALPHA_VANTAGE_API_KEY", names)
        self.assertIn("SEC_USER_AGENT", names)
        self.assertTrue(all(row["secret_value_redacted"] for row in env_report["env_vars"]))
        self.assertNotIn("key_value", str(env_report).lower())

    def test_stock_priorities_include_stock_candidates(self):
        priorities = build_source_priorities(module="institutional_stock_pro_analyst", limit=50)
        source_ids = {row["source_id"] for row in priorities["priorities"]}
        self.assertIn("sec_edgar_data", source_ids)
        self.assertIn("alpha_vantage_market_data", source_ids)


if __name__ == "__main__":
    unittest.main()

