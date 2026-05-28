import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.later.auto_execution_policy import get_disabled_auto_execution_policy
from automation_scheduler.later.execution_audit_log import append_execution_audit_record, read_execution_audit_records
from automation_scheduler.later.execution_guardrails import get_execution_guardrails
from automation_scheduler.later.execution_readiness_check import check_execution_readiness


class TestLaterAutoExecutionPolicy(unittest.TestCase):
    def test_disabled_policy_and_guardrails(self):
        policy = get_disabled_auto_execution_policy()
        readiness = check_execution_readiness(policy)
        guardrails = get_execution_guardrails()
        self.assertFalse(policy["auto_execution_enabled"])
        self.assertFalse(policy["auto_bet_enabled"])
        self.assertFalse(policy["auto_trade_enabled"])
        self.assertTrue(policy["paper_execution_only"])
        self.assertTrue(policy["human_approval_required"])
        self.assertEqual(readiness["status"], "not_ready")
        self.assertTrue(guardrails["future_only"])

    def test_execution_audit_log_is_paper_only(self):
        with TemporaryDirectory() as tmp:
            append_execution_audit_record({"mode": "paper", "secret": "hide"}, base_data_dir=tmp)
            records = read_execution_audit_records(base_data_dir=tmp)
            self.assertEqual(records[0]["mode"], "paper_or_dry_run_only")
            self.assertEqual(records[0]["record"]["secret"], "[redacted]")
