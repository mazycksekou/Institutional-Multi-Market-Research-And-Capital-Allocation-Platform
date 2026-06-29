import unittest
from tempfile import TemporaryDirectory

from src.services.streamlit_dashboard_facade import build_review_item
from src.services.streamlit_dashboard_facade import get_default_scheduler_config
from math_models.institutional import ensure_no_banned_language
from math_models.institutional.model_router import get_model_library, institutional_review_fields, route_models


class TestInstitutionalModelRouter(unittest.TestCase):
    def test_all_model_families_registered_and_safe_language(self):
        library = get_model_library()
        self.assertEqual(len(library), 149)
        self.assertTrue(ensure_no_banned_language(library))
        for model in library.values():
            self.assertTrue(model["mathematical_purpose"])
            self.assertTrue(model["required_inputs"])
            self.assertTrue(model["output_fields"])
            self.assertTrue(model["assumptions"])
            self.assertTrue(model["limitations"])
            self.assertEqual(model["activation_status"], "research_only")

    def test_model_router_blocks_wrong_horizon_and_sportsbook_use(self):
        routed = route_models(
            market_type="retirement_portfolio",
            horizon="short_term",
            purpose="allocation",
            available_inputs={
                "expected_returns": [0.08],
                "volatility_estimates": [0.12],
                "constraints": [],
                "asset_universe": ["equity"],
                "asset_value": 100,
                "liability_value": 90,
                "duration_gap": 1,
                "contribution_rate": 0.05,
                "withdrawal_rate": 0.03,
            },
        )
        blocked_reasons = {entry["reason"] for entry in routed["blocked_models"]}
        self.assertIn("allocation_model_blocked_for_short_horizon", blocked_reasons)

        sportsbook_routed = route_models(
            market_type="sportsbook",
            horizon="same_day",
            purpose="allocation",
            available_inputs={},
        )
        self.assertEqual(sportsbook_routed["eligible_models"], [])
        self.assertIn("institutional_models_do_not_create_sportsbook_recommendations", sportsbook_routed["routing_reason"])

    def test_review_queue_fields_are_gated_by_activation_and_relevance(self):
        library = get_model_library()
        model = library["mean_variance_optimization"]
        fields = institutional_review_fields(
            model,
            evidence_score=90,
            input_quality_score=95,
            model_risk_rating="moderate",
            router_reason="eligible_for_long_term_portfolio_review",
            relevant_to_market=True,
        )
        self.assertEqual(fields, {})

        promoted = dict(model)
        promoted["activation_status"] = "review_queue_ready"
        allowed_fields = institutional_review_fields(
            promoted,
            evidence_score=90,
            input_quality_score=95,
            model_risk_rating="moderate",
            router_reason="eligible_for_long_term_portfolio_review",
            relevant_to_market=True,
        )
        self.assertEqual(allowed_fields["institutional_model_family"], "mean_variance_optimization")
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            item = build_review_item(
                {
                    "source": "institutional_model_router",
                    "provider": "internal",
                    "market_type": "stocks_watchlist",
                    "sport_or_symbol": "SPY",
                    "market": "portfolio_review",
                    "selection": "core_allocation",
                    "opportunity_score": 75,
                    **allowed_fields,
                },
                config,
            )
            self.assertEqual(item["institutional_model_family"], "mean_variance_optimization")
            self.assertTrue(item["human_approval_required"])

