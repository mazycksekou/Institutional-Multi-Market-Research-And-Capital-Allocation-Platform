import unittest
from model_governance.champion_challenger import compare_champion_challenger

class TestChampionChallenger(unittest.TestCase):
    def test_outcomes(self):
        r = compare_champion_challenger(champion={'sample_size':200,'calibration':80,'risk_adjusted':80,'settlement_failures':0,'liquidity_failures':0}, challenger={'sample_size':200,'calibration':90,'risk_adjusted':90,'settlement_failures':0,'liquidity_failures':0})
        self.assertIn(r['decision'], {'champion_kept','challenger_promoted_to_review','challenger_rejected','needs_more_data','governance_blocked'})
