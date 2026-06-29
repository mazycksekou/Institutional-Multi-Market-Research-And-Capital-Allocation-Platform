import unittest

import src.core.quant_engine as quant_engine


class TestQuantEngineFoundation(unittest.TestCase):
    def test_odds_probability_edge_ev_and_kelly(self):
        self.assertAlmostEqual(quant_engine.american_to_decimal(-110), 1.9090909, places=6)
        self.assertAlmostEqual(quant_engine.decimal_to_implied_probability(2.0), 0.5)
        self.assertAlmostEqual(quant_engine.implied_probability_from_american(-110), 0.5238095, places=6)
        self.assertEqual(quant_engine.fair_odds_american_from_probability(0.6), -150)
        self.assertAlmostEqual(quant_engine.edge_percentage(0.55, 0.52), 3.0)
        self.assertGreater(quant_engine.expected_value_per_100(-110, 0.55), 0)
        self.assertGreater(quant_engine.full_kelly_percent(-110, 0.55), 0)
        self.assertGreater(quant_engine.fractional_kelly_percent(-110, 0.55, 0.25), 0)

    def test_risk_profile_and_stake_caps(self):
        conservative = quant_engine.risk_profile_settings("conservative")
        aggressive = quant_engine.risk_profile_settings("aggressive")
        self.assertLess(conservative["max_bankroll_pct"], aggressive["max_bankroll_pct"])
        stake = quant_engine.suggested_stake_with_risk_controls(1000, -110, 0.6, "conservative")
        self.assertLessEqual(stake, 10)

    def test_quant_component_foundation_has_required_architecture_fields(self):
        component = quant_engine.quant_engine_component_foundation()
        for field in [
            "component_name",
            "component_status",
            "required_inputs",
            "optional_inputs",
            "missing_inputs",
            "data_provider_needs",
            "backtest_requirements",
            "calibration_requirements",
            "no_bet_flags",
            "output_fields",
            "notes",
        ]:
            self.assertIn(field, component)
        self.assertIn(component["component_status"], {"inactive_missing_data", "research_mode_not_bettable", "active"})


if __name__ == "__main__":
    unittest.main()
