import unittest
from model_governance.model_router import route_model_candidate

class TestModelRouter(unittest.TestCase):
    def test_blocks_wrong_market(self):
        r = route_model_candidate(market_type='sportsbook', sport_or_asset_class='sportsbook', model_type='allocation_model', time_horizon='same_day', available_inputs={}, activation_tier='review_queue_ready', risk_gate_result=True, data_quality_result=True, settlement_gate_result=True, human_approval_required=True)
        self.assertFalse(r['allowed'])
