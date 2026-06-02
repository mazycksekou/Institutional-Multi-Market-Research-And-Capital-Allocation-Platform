import unittest

from automation_scheduler.broker_quality_scoring import build_broker_quality_report, score_broker_provider


class TestBrokerQualityScoring(unittest.TestCase):
    def test_broker_quality_statuses_are_research_only_outputs(self):
        scored = score_broker_provider(
            {
                "broker_name": "Paper Broker",
                "provider_type": "broker_research",
                "asset_types_supported": ["stock", "etf"],
                "api_reliability_score": 90,
                "uptime_score": 92,
                "latency_score": 85,
                "order_type_support_score": 88,
                "fee_score": 80,
                "spread_quality_score": 82,
                "slippage_risk_score": 20,
                "paper_or_sandbox_support": True,
                "execution_restriction_risk": 20,
                "compliance_risk_score": 15,
            }
        )
        self.assertEqual(scored["broker_status"], "SANDBOX_READY")
        self.assertFalse(scored["enabled"])
        self.assertFalse(scored["provider_write"])
        self.assertFalse(scored["execution_allowed"])

    def test_compliance_risk_not_approved(self):
        scored = score_broker_provider({"broker_name": "Risky", "compliance_risk_score": 90})
        self.assertEqual(scored["broker_status"], "NOT_APPROVED")

    def test_report_is_safe(self):
        report = build_broker_quality_report()
        self.assertGreaterEqual(report["broker_count"], 1)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
