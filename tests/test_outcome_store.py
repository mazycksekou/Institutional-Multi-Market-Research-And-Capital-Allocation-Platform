import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from automation_scheduler.outcome_store import (
    ingest_outcome_records,
    load_outcome_records,
    load_outcome_state,
    validate_outcome_record,
)


class TestOutcomeStore(unittest.TestCase):
    def _record(self, **overrides):
        base = {
            "provider": "kalshi_prediction_market",
            "market_type": "prediction_market",
            "contract_id": "KXTEST",
            "outcome_status": "settled",
            "final_outcome": "yes",
            "settled_at": "2026-05-29T00:00:00+00:00",
            "source": "test_fixture",
        }
        base.update(overrides)
        return base

    def test_valid_local_outcome_records_persist_and_read_latest(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records([self._record()], source="test_fixture", dry_run=True, persist=True, base_data_dir=tmp)
            self.assertTrue(result["local_persistence"])
            self.assertEqual(result["records_valid"], 1)
            self.assertEqual(result["outcome_records_written"], 1)
            state = load_outcome_state(tmp)
            self.assertTrue(state["outcome_read_ok"])
            self.assertEqual(state["items_read_count"], 1)
            self.assertEqual(len(load_outcome_records(tmp)), 1)

    def test_invalid_outcome_status_rejected(self):
        result = ingest_outcome_records([self._record(outcome_status="bad")], source="test_fixture")
        self.assertEqual(result["records_rejected"], 1)
        self.assertEqual(result["rejected_reason_counts"]["unsupported_outcome_status"], 1)

    def test_invalid_final_outcome_rejected(self):
        result = ingest_outcome_records([self._record(final_outcome="maybe")], source="test_fixture")
        self.assertEqual(result["records_rejected"], 1)
        self.assertEqual(result["rejected_reason_counts"]["unsupported_final_outcome"], 1)

    def test_missing_matching_keys_rejected(self):
        record = self._record()
        record.pop("contract_id")
        result = ingest_outcome_records([record], source="test_fixture")
        self.assertEqual(result["records_rejected"], 1)
        self.assertEqual(result["rejected_reason_counts"]["missing_matching_key"], 1)

    def test_duplicate_outcomes_deduped(self):
        with TemporaryDirectory() as tmp:
            first = ingest_outcome_records([self._record()], source="test_fixture", dry_run=True, persist=True, base_data_dir=tmp)
            second = ingest_outcome_records([self._record()], source="test_fixture", dry_run=True, persist=True, base_data_dir=tmp)
            self.assertEqual(first["outcome_records_written"], 1)
            self.assertEqual(second["duplicate_count"], 1)
            self.assertEqual(second["outcome_records_written"], 0)
            self.assertEqual(len(load_outcome_records(tmp)), 1)

    def test_future_settled_at_rejected(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cleaned, reason = validate_outcome_record(self._record(settled_at=future), source="test_fixture")
        self.assertIsNone(cleaned)
        self.assertEqual(reason, "future_settled_at")

    def test_raw_payload_and_secrets_are_not_stored(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records(
                [
                    self._record(
                        notes="x" * 500,
                        provider_payload={"raw": "drop"},
                        api_key="secret",
                    )
                ],
                source="test_fixture",
                dry_run=True,
                persist=True,
                base_data_dir=tmp,
            )
            record = load_outcome_records(tmp)[0]
            rendered = str(record)
            self.assertEqual(result["records_valid"], 1)
            self.assertNotIn("provider_payload", rendered)
            self.assertNotIn("secret", rendered)
            self.assertLessEqual(len(record["notes"]), 240)
