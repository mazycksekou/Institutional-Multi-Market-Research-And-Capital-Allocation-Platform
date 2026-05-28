import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from model_governance.governance_audit_log import write_governance_audit_record


class TestGovernanceAuditLog(unittest.TestCase):
    def test_governance_audit_log_writes_valid_json(self):
        with TemporaryDirectory() as tmp:
            record = write_governance_audit_record(
                model_id="sportsbook_side_total",
                action="promotion_review",
                previous_tier="review_queue_ready",
                new_tier="active_scoring_ready",
                gate_results={"calibration_score": 82},
                decision="approved",
                reason="all gates passed",
                base_data_dir=tmp,
            )
            saved = json.loads(Path(record["path"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["schema_version"], "model_governance.v1")
            self.assertTrue(saved["human_approval_required"])
            self.assertFalse(saved["auto_execution_enabled"])

