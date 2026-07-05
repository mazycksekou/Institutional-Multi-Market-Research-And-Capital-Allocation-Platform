import unittest

from src.analytics.model_governance.model_router_registry import route_registered_models


class TestModelRouterRegistry(unittest.TestCase):
    def test_router_blocks_wrong_market_and_horizon(self):
        routed = route_registered_models(
            market_type="stocks",
            model_purpose="probability_estimation",
            time_horizon="same_day",
            activation_tier="review_queue_ready",
            available_inputs={},
        )
        blocked = {entry["reason"] for entry in routed["blocked_models"]}
        self.assertIn("wrong_market_type", blocked)

        retirement = route_registered_models(
            market_type="sportsbook",
            model_purpose="allocation",
            time_horizon="same_day",
            activation_tier="review_queue_ready",
            available_inputs={},
        )
        self.assertIn("retirement_and_allocation_models_blocked_for_short_term_trade", retirement["routing_reason"])

    def test_router_blocks_prediction_market_settlement_failure(self):
        routed = route_registered_models(
            market_type="prediction_markets",
            model_purpose="pricing_dislocation",
            time_horizon="same_day",
            activation_tier="review_queue_ready",
            available_inputs={
                "market_price": 0.55,
                "sportsbook_price": 0.5,
                "resolution_rules": "documented",
            },
            settlement_rule_confidence=50,
        )
        self.assertEqual(routed["eligible_models"], [])
        self.assertIn("prediction_market_settlement_risk_failure", routed["routing_reason"])

