from __future__ import annotations

import inspect
import unittest

from src.market_intelligence.options import (
    build_options_intelligence_report,
    classify_dte_bucket,
    compute_gex,
    compute_net_gex,
    compute_vanna,
    compute_vanna_exposure,
    floor_time_to_expiry,
)


class TestPhase10K8ZL5Options0DTEGexVannaFoundation(unittest.TestCase):
    def test_core_formulas(self):
        call = compute_gex(oi=10, gamma=0.1, price=100, option_type="call")
        put = compute_gex(oi=10, gamma=0.1, price=100, option_type="put")
        self.assertGreater(call, 0)
        self.assertLess(put, 0)
        self.assertAlmostEqual(compute_net_gex([{"open_interest": 10, "gamma": 0.1, "strike": 100, "underlying_price": 100, "option_type": "call"}]), call)
        self.assertAlmostEqual(compute_vanna(d2=0.2, sigma=0.4, gamma=0.1), -(0.2 / 0.4) * 0.1)
        self.assertAlmostEqual(compute_vanna_exposure(oi=10, d2=0.2, sigma=0.4, gamma=0.1, price=100), 10 * 100 * (-(0.2 / 0.4) * 0.1) * 100 * 0.01)

    def test_0dte_behavior_and_bucketing(self):
        self.assertEqual(floor_time_to_expiry(0), 0.0)
        self.assertEqual(floor_time_to_expiry(0.4), 1.0)
        self.assertEqual(classify_dte_bucket(1), "0-2 DTE")
        self.assertEqual(classify_dte_bucket(5), "Weekly")
        self.assertEqual(classify_dte_bucket(20), "Monthly")
        self.assertEqual(classify_dte_bucket(60), "Long Dated")

    def test_intelligence_report_ignores_expired_and_builds_profiles(self):
        report = build_options_intelligence_report(
            {
                "symbol": "ABC",
                "underlying_price": 100,
                "contracts": [
                    {"option_type": "call", "open_interest": 10, "gamma": 0.1, "strike": 100, "days_to_expiry": 5},
                    {"option_type": "put", "open_interest": 12, "gamma": 0.2, "strike": 95, "days_to_expiry": 0},
                ],
            }
        )
        self.assertEqual(report["gex_profile"], 10000.0)
        self.assertIn("call_wall", report)
        self.assertIn("put_wall", report)
        self.assertIn("gamma_flip", report)
        self.assertIn("gex_by_tenor", report)
        self.assertIn("expected_pinning", report)
        self.assertIn("trend_probability", report)

