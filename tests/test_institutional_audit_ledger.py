import tempfile
import unittest

from automation_scheduler.institutional_audit_ledger import append_audit_record, load_audit_records


class TestInstitutionalAuditLedger(unittest.TestCase):
    def test_audit_records_are_redacted_and_safety_flags_are_forced(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = append_audit_record(
                action_type="execution_simulation",
                run_id="run-1",
                asset_class="prediction_market",
                provider="kalshi_prediction_market",
                source_record_id="candidate-1",
                input_payload={"api_key": "secret", "provider_payload": {"raw": "drop"}},
                output_payload={"provider_write": True, "actual_order_submitted": True},
                safety_flags={"provider_write": True, "actual_order_submitted": True, "simulated_ticket_created": True},
                base_data_dir=tmp,
            )
            loaded = load_audit_records(base_data_dir=tmp)
        self.assertTrue(result["ok"])
        self.assertEqual(loaded["total_count"], 1)
        record = loaded["items"][0]
        self.assertFalse(record["provider_write"])
        self.assertFalse(record["actual_order_submitted"])
        self.assertTrue(record["user_command_required"])
        self.assertNotIn("secret", str(record))
        self.assertNotIn("provider_payload", str(record))


if __name__ == "__main__":
    unittest.main()
