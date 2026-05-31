import unittest

from automation_scheduler.data_source_registry import CRYPTO_EDGE_SCORING_DIMENSIONS, CRYPTO_FORBIDDEN_ACTIONS, build_registry, build_source_priorities


class TestCryptoEdgeLabRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = build_registry()
        self.lanes = {lane["lane_id"]: lane for lane in self.registry["lanes"]}
        self.sources = {source["source_id"]: source for source in self.registry["sources"]}

    def test_crypto_edge_lab_lane_exists_and_has_highest_priority(self):
        lane = self.lanes["cryptocurrency_edge_lab"]
        self.assertEqual(lane["module_priority"], "highest")
        self.assertEqual(lane["module_status"], "planning_registry_only")
        self.assertEqual(lane["adapter_status"], "not_started")
        self.assertFalse(lane["enabled"])
        self.assertFalse(lane["provider_write"])
        self.assertFalse(lane["execution_allowed"])
        for score in CRYPTO_EDGE_SCORING_DIMENSIONS:
            self.assertIn(score, lane["planned_scores"])
        self.assertIn("no guaranteed wins", lane["strategy_language"])

    def test_crypto_sources_are_disabled_and_forbid_execution_actions(self):
        required = {
            "coingecko_crypto_prices",
            "coincap_crypto_prices",
            "binance_public_market_data",
            "defillama",
            "etherscan_onchain",
        }
        self.assertTrue(required.issubset(self.sources))
        for source_id in required:
            source = self.sources[source_id]
            self.assertFalse(source["enabled"])
            self.assertFalse(source["provider_write"])
            self.assertFalse(source["execution_allowed"])
            self.assertFalse(source["crypto_trade_execution_enabled"])
            self.assertFalse(source["raw_payload_persistence_allowed"])
        for source_id in ("binance_public_market_data", "coinbase_public_market_data", "kraken_public_market_data", "okx_public_market_data"):
            forbidden = set(self.sources[source_id]["forbidden_actions"])
            self.assertTrue(set(CRYPTO_FORBIDDEN_ACTIONS).issubset(forbidden))

    def test_crypto_priority_candidates_rank_high(self):
        priorities = build_source_priorities(limit=20)
        top_ids = {row["source_id"] for row in priorities["priorities"][:20]}
        self.assertIn("coingecko_crypto_prices", top_ids)
        self.assertIn("binance_public_market_data", top_ids)
        self.assertIn("defillama", top_ids)


if __name__ == "__main__":
    unittest.main()

