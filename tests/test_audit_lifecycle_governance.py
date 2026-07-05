import unittest
from pathlib import Path

from scripts.check_audit_lifecycle import collect_audit_lifecycle_report


ROOT = Path(__file__).resolve().parents[1]


class TestAuditLifecycleGovernance(unittest.TestCase):
    def test_policy_and_register_exist(self):
        policy = ROOT / "docs/architecture/AUDIT_LIFECYCLE_POLICY.md"
        register = ROOT / "docs/reports/audits/AUDIT_RETENTION_REGISTER.md"
        checker = ROOT / "scripts/check_audit_lifecycle.py"
        self.assertTrue(policy.exists())
        self.assertTrue(register.exists())
        self.assertTrue(checker.exists())

    def test_register_captures_current_audit_state(self):
        report = collect_audit_lifecycle_report(ROOT)
        self.assertTrue(report["ok"])
        self.assertEqual(report["clear_violations"], [])
        self.assertIn("docs/reports/audits/MISSING_GOVERNANCE_REPORT.md", report["register_entries"])
        self.assertEqual(report["register_entries"]["docs/reports/audits/MISSING_GOVERNANCE_REPORT.md"]["current_state"], "ACTIVE")
        self.assertEqual(report["register_entries"]["docs/archive/historical_reports/OPTIONAL_CI_READINESS_REPORT.md"]["current_state"], "ARCHIVE")
        self.assertEqual(report["register_entries"]["docs/archive/historical_reports/SCHEDULER_NAME_ZERO_EXECUTABLE_REF_PROOF.md"]["recommended_action"], "ARCHIVE")

    def test_ops_check_references_audit_lifecycle_checker(self):
        ops_check = (ROOT / "scripts/ops_check.py").read_text(encoding="utf-8")
        self.assertIn("check_audit_lifecycle.py", ops_check)
        self.assertIn("audit_lifecycle", ops_check)


if __name__ == "__main__":
    unittest.main()
