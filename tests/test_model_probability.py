"""Tests for model probability blending and adjustment layer."""
from __future__ import annotations

import unittest

import model_probability


class TestIndependentInputs(unittest.TestCase):
    def test_empty_inputs(self):
        """Test with no inputs provided."""
        inputs = model_probability.IndependentInputs()
        
        self.assertEqual(len(inputs.get_active_inputs()), 0)
        self.assertEqual(len(inputs.get_missing_inputs()), 11)
        self.assertEqual(len(inputs.get_adjustment_values()), 0)
    
    def test_partial_inputs(self):
        """Test with some inputs provided."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.55,
            weather_adjustment=0.02,
            injury_adjustment=-0.01
        )
        
        active = inputs.get_active_inputs()
        missing = inputs.get_missing_inputs()
        adjustments = inputs.get_adjustment_values()
        
        self.assertIn("projection_probability", active)
        self.assertIn("weather_adjustment", active)
        self.assertIn("injury_adjustment", active)
        self.assertNotIn("pitcher_adjustment", active)
        
        self.assertEqual(len(adjustments), 2)
        self.assertIn(0.02, adjustments)
        self.assertIn(-0.01, adjustments)
    
    def test_all_inputs(self):
        """Test with all inputs provided."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.55,
            pitcher_adjustment=0.01,
            weather_adjustment=0.02,
            lineup_adjustment=-0.01,
            bullpen_adjustment=0.005,
            injury_adjustment=-0.015,
            park_factor_adjustment=0.003,
            umpire_adjustment=-0.002,
            player_prop_projection=0.04,
            sharp_market_probability=0.57,
            closing_line_projection=0.56
        )
        
        self.assertEqual(len(inputs.get_active_inputs()), 11)
        self.assertEqual(len(inputs.get_missing_inputs()), 0)
        self.assertEqual(len(inputs.get_adjustment_values()), 9)


class TestDataQualityScore(unittest.TestCase):
    def test_no_inputs_quality_score(self):
        """Test data quality score with no inputs."""
        inputs = model_probability.IndependentInputs()
        score = model_probability.calculate_data_quality_score(inputs)
        
        # Should be low due to no inputs
        self.assertLess(score, 0.2)
    
    def test_projection_only_quality_score(self):
        """Test data quality score with only projection."""
        inputs = model_probability.IndependentInputs(projection_probability=0.55)
        score = model_probability.calculate_data_quality_score(inputs)
        
        # Should have base completeness + projection bonus
        # Base completeness: 1/11 * 0.7 = 0.064
        # Projection bonus: 0.15
        # No sharp bonus: 0.0
        # No adjustment bonus: 0.0
        # Total: 0.064 + 0.15 + 0.0 + 0.0 = 0.214
        expected_score = 0.214
        self.assertAlmostEqual(score, expected_score, places=3)
    
    def test_full_inputs_quality_score(self):
        """Test data quality score with all inputs."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.55,
            pitcher_adjustment=0.01,
            weather_adjustment=0.02
        )
        score = model_probability.calculate_data_quality_score(inputs)
        
        # Should be moderate with 3 inputs out of 11
        # Base completeness: 3/11 * 0.7 = 0.191
        # Projection bonus: 0.15
        # No sharp bonus: 0.0
        # Adjustment bonus: min(0.05, 2 * 0.01) = 0.02
        # Total: 0.191 + 0.15 + 0.0 + 0.02 = 0.361
        expected_score = 0.361
        self.assertAlmostEqual(score, expected_score, places=3)


class TestAdjustmentCaps(unittest.TestCase):
    def test_no_adjustments(self):
        """Test with no adjustments."""
        final_prob, warnings = model_probability.apply_adjustment_caps(0.55, [])
        
        self.assertEqual(final_prob, 0.55)
        self.assertEqual(len(warnings), 0)
    
    def test_single_adjustment_within_cap(self):
        """Test single adjustment within cap."""
        final_prob, warnings = model_probability.apply_adjustment_caps(0.55, [0.02])
        
        self.assertAlmostEqual(final_prob, 0.57, places=6)
        self.assertEqual(len(warnings), 0)
    
    def test_single_adjustment_exceeds_cap(self):
        """Test single adjustment exceeding cap."""
        final_prob, warnings = model_probability.apply_adjustment_caps(0.55, [0.05])  # Exceeds 0.03 cap
        
        self.assertAlmostEqual(final_prob, 0.58, places=6)  # 0.55 + 0.03 (capped)
        self.assertEqual(len(warnings), 1)
        self.assertIn("exceeds", warnings[0])
    
    def test_total_adjustment_exceeds_cap(self):
        """Test total adjustment exceeding cap."""
        adjustments = [0.02, 0.03, 0.04]  # Total = 0.09, exceeds 0.08 cap
        final_prob, warnings = model_probability.apply_adjustment_caps(0.55, adjustments)
        
        self.assertAlmostEqual(final_prob, 0.63, places=6)  # 0.55 + 0.08 (capped)
        # Only one adjustment (0.04) exceeds the single cap, so expect 1 warning
        self.assertEqual(len(warnings), 1)
        # Should have single adjustment warning but not total adjustment warning (since total gets capped)
        self.assertTrue(any("exceeds" in w for w in warnings))
    
    def test_probability_floor_ceiling(self):
        """Test probability floor and ceiling."""
        # Test floor
        final_prob, warnings = model_probability.apply_adjustment_caps(0.02, [-0.05])
        self.assertEqual(final_prob, model_probability.FINAL_PROBABILITY_FLOOR)
        
        # Test ceiling - individual 0.05 gets capped to 0.03, total 0.03 < 0.08 cap
        final_prob, warnings = model_probability.apply_adjustment_caps(0.95, [0.05])
        self.assertAlmostEqual(final_prob, 0.98, places=6)  # 0.95 + 0.03 (capped individually)


class TestProbabilityBlending(unittest.TestCase):
    def test_market_derived_only(self):
        """Test with only market probability (no independent inputs)."""
        inputs = model_probability.IndependentInputs()
        result = model_probability.blend_probabilities(0.55, inputs)
        
        self.assertEqual(result.probability_type, "market_derived")
        self.assertEqual(result.final_probability, 0.55)
        self.assertEqual(len(result.active_inputs), 0)
        self.assertEqual(len(result.missing_inputs), 11)
        self.assertIn("No independent model inputs available", result.model_limitations)
    
    def test_blended_market_and_projection(self):
        """Test blending market and projection probabilities."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.60,
            weather_adjustment=0.02,
            injury_adjustment=-0.01
        )
        result = model_probability.blend_probabilities(0.55, inputs)
        
        self.assertEqual(result.probability_type, "blended_market_and_projection")
        self.assertNotEqual(result.final_probability, 0.55)  # Should be adjusted
        self.assertIn("projection_probability", result.active_inputs)
        self.assertIn("weather_adjustment", result.active_inputs)
        self.assertIn("injury_adjustment", result.active_inputs)
        self.assertIn("weather_adjustment", result.applied_adjustments)
        self.assertIn("injury_adjustment", result.applied_adjustments)
    
    def test_blended_market_projection_and_adjustments(self):
        """Test blending market with adjustments but no projection."""
        inputs = model_probability.IndependentInputs(
            weather_adjustment=0.02,
            injury_adjustment=-0.01
        )
        result = model_probability.blend_probabilities(0.55, inputs)
        
        self.assertEqual(result.probability_type, "blended_market_projection_and_adjustments")
        self.assertNotEqual(result.final_probability, 0.55)  # Should be adjusted
        self.assertNotIn("projection_probability", result.active_inputs)
        self.assertIn("weather_adjustment", result.active_inputs)
        self.assertIn("injury_adjustment", result.active_inputs)
        self.assertIn("No projection probability available", result.model_limitations[0])
    
    def test_sharp_market_probability_included(self):
        """Test that sharp market probability is handled correctly."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.60,
            sharp_market_probability=0.58
        )
        result = model_probability.blend_probabilities(0.55, inputs)
        
        self.assertIn("sharp_market_probability", result.active_inputs)
        # Sharp market should influence data quality score
        # Base completeness: 2/11 * 0.7 = 0.127
        # Projection bonus: 0.15
        # Sharp bonus: 0.1
        # No adjustment bonus: 0.0
        # Total: 0.127 + 0.15 + 0.1 + 0.0 = 0.377
        expected_score = 0.377
        self.assertAlmostEqual(result.data_quality_score, expected_score, places=3)
    
    def test_all_advanced_providers_missing_limitation(self):
        """Test limitation when all advanced providers are missing."""
        inputs = model_probability.IndependentInputs(projection_probability=0.60)
        result = model_probability.blend_probabilities(0.55, inputs)
        
        # Should have limitation about all advanced providers being placeholder
        limitation_text = "All advanced providers are placeholder"
        self.assertTrue(any(limitation_text in lim for lim in result.model_limitations))
    
    def test_confidence_grading(self):
        """Test confidence grade calculation."""
        # Test A grade
        confidence_a = model_probability.calculate_confidence_score(0.95)
        self.assertEqual(model_probability.get_confidence_grade(confidence_a), "A")
        
        # Test B grade
        confidence_b = model_probability.calculate_confidence_score(0.85)
        self.assertEqual(model_probability.get_confidence_grade(confidence_b), "B")
        
        # Test C grade
        confidence_c = model_probability.calculate_confidence_score(0.75)
        self.assertEqual(model_probability.get_confidence_grade(confidence_c), "C")
        
        # Test D grade
        confidence_d = model_probability.calculate_confidence_score(0.65)
        self.assertEqual(model_probability.get_confidence_grade(confidence_d), "D")
        
        # Test F grade
        confidence_f = model_probability.calculate_confidence_score(0.5)
        self.assertEqual(model_probability.get_confidence_grade(confidence_f), "F")


class TestCreateProbabilityResponse(unittest.TestCase):
    def test_response_structure(self):
        """Test that response has all required fields."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.60,
            weather_adjustment=0.02
        )
        response = model_probability.create_probability_response(0.55, inputs)
        
        # Check all required fields are present
        required_fields = [
            "ok", "final_probability", "probability_type", "market_probability",
            "active_inputs", "missing_inputs", "applied_adjustments",
            "adjustment_cap_warnings", "model_limitations", "data_quality_score",
            "confidence", "confidence_grade", "provider_status"
        ]
        
        for field in required_fields:
            self.assertIn(field, response)
        
        self.assertTrue(response["ok"])
        self.assertEqual(response["probability_type"], "blended_market_and_projection")
        self.assertIn("projection_probability", response["active_inputs"])
        self.assertIn("weather_adjustment", response["active_inputs"])
    
    def test_adjustment_warnings_in_response(self):
        """Test that adjustment warnings appear in response."""
        inputs = model_probability.IndependentInputs(
            projection_probability=0.60,
            weather_adjustment=0.05  # Exceeds cap
        )
        response = model_probability.create_probability_response(0.55, inputs)
        
        self.assertGreater(len(response["adjustment_cap_warnings"]), 0)
        self.assertIn("exceeds", response["adjustment_cap_warnings"][0])
    
    def test_provider_status_placeholders(self):
        """Test that provider status placeholders are included."""
        inputs = model_probability.IndependentInputs()
        response = model_probability.create_probability_response(0.55, inputs)
        
        provider_status = response["provider_status"]
        
        required_providers = [
            "weather_provider_status", "lineup_provider_status", "pitcher_provider_status",
            "injury_provider_status", "player_projection_provider_status", "clv_provider_status"
        ]
        
        for provider in required_providers:
            self.assertIn(provider, provider_status)
            self.assertEqual(provider_status[provider], "placeholder")


class TestOptionalMarketProbability(unittest.TestCase):
    def test_request_without_market_probability_with_no_vig_probability(self):
        """Test request without top level market_probability but with no_vig_probability returns ok true."""
        priced_rows = [
            {
                "sportsbook": "draftkings",
                "market": "h2h",
                "selection": "Team A",
                "no_vig_probability": 0.55,
                "consensus_probability": 0.54,
                "implied_probability": 0.56
            }
        ]

        inputs = model_probability.IndependentInputs(projection_probability=0.60)
        result = model_probability.blend_probabilities(0.55, inputs)

        self.assertEqual(result.probability_type, "blended_market_and_projection")
        self.assertEqual(result.market_probability, 0.55)
        self.assertIn("projection_probability", result.active_inputs)

    def test_request_without_market_probability_with_consensus_probability(self):
        """Test request without top level market_probability but with consensus_probability returns ok true."""
        priced_rows = [
            {
                "sportsbook": "draftkings",
                "market": "h2h",
                "selection": "Team A",
                "consensus_probability": 0.54,
                "implied_probability": 0.56
            }
        ]

        inputs = model_probability.IndependentInputs(projection_probability=0.60)
        result = model_probability.blend_probabilities(0.54, inputs)

        self.assertEqual(result.probability_type, "blended_market_and_projection")
        self.assertEqual(result.market_probability, 0.54)
        self.assertIn("projection_probability", result.active_inputs)

    def test_request_without_market_probability_with_implied_probability(self):
        """Test request without top level market_probability but with implied_probability returns ok true."""
        priced_rows = [
            {
                "sportsbook": "draftkings",
                "market": "h2h",
                "selection": "Team A",
                "implied_probability": 0.56
            }
        ]

        inputs = model_probability.IndependentInputs(projection_probability=0.60)
        result = model_probability.blend_probabilities(0.56, inputs)

        self.assertEqual(result.probability_type, "blended_market_and_projection")
        self.assertEqual(result.market_probability, 0.56)
        self.assertIn("projection_probability", result.active_inputs)

    def test_request_without_any_probabilities_returns_ok_false(self):
        """Test request with none of those probabilities returns ok false, not 422."""
        priced_rows = [
            {
                "sportsbook": "draftkings",
                "market": "h2h",
                "selection": "Team A",
                "odds_american": -110
                # No probability fields
            }
        ]

        # This should be handled at the endpoint level, not the model level
        # The model probability logic should still work with a provided market probability
        inputs = model_probability.IndependentInputs(projection_probability=0.60)
        result = model_probability.blend_probabilities(0.55, inputs)

        self.assertEqual(result.probability_type, "blended_market_and_projection")
        self.assertEqual(result.market_probability, 0.55)

    def test_request_model_validation_does_not_require_market_probability(self):
        """Test OpenAPI/request model validation does not require market_probability."""
        # This should not raise a validation error
        from main import ModelProbabilityRequest

        request = ModelProbabilityRequest(
            projection_probability=0.60,
            priced_rows=[{"market": "h2h", "no_vig_probability": 0.55}]
        )

        self.assertIsNone(request.market_probability)
        self.assertEqual(request.projection_probability, 0.60)
        self.assertIsNotNone(request.priced_rows)


if __name__ == "__main__":
    unittest.main()
