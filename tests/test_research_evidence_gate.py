import unittest
from src.analytics.model_governance.research_evidence_gate import evaluate_research_evidence_gate

class TestResearchEvidenceGate(unittest.TestCase):
    def test_blocks_weak(self):
        r = evaluate_research_evidence_gate(evidence_score=60, mathematical_definition_exists=False, input_availability=False, out_of_sample_testability=False, risk_control_support=False, no_guarantee_language=True)
        self.assertEqual(r['research_evidence_gate_result'], 'blocked_by_governance')
