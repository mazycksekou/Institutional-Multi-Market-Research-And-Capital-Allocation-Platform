import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from automation_scheduler.outcome_store import (
    ingest_outcome_records,
    load_outcome_records,
    load_outcome_state,
    validate_outcome_record,
)
from automation_scheduler.settlement_discovery import (
    build_outcome_completion_report,
    classify_kalshi_settlement,
    discover_kalshi_settlements_for_pending_rows,
    validate_imported_outcome_rows,
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
            "source": "local_manual",
        }
        base.update(overrides)
        return base

    def test_valid_local_outcome_records_persist_and_read_latest(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records([self._record()], source="local_manual", dry_run=False, persist=True, base_data_dir=tmp)
            self.assertTrue(result["local_persistence"])
            self.assertEqual(result["records_valid"], 1)
            self.assertEqual(result["outcome_records_written"], 1)
            state = load_outcome_state(tmp)
            self.assertTrue(state["outcome_read_ok"])
            self.assertEqual(state["items_read_count"], 1)
            self.assertEqual(len(load_outcome_records(tmp)), 1)

    def test_invalid_outcome_status_rejected(self):
        result = ingest_outcome_records([self._record(outcome_status="bad")], source="local_manual")
        self.assertEqual(result["records_rejected"], 1)
        self.assertEqual(result["rejected_reason_counts"]["unsupported_outcome_status"], 1)

    def test_invalid_final_outcome_rejected(self):
        result = ingest_outcome_records([self._record(final_outcome="maybe")], source="local_manual")
        self.assertEqual(result["records_rejected"], 1)
        self.assertEqual(result["rejected_reason_counts"]["unsupported_final_outcome"], 1)

    def test_missing_matching_keys_rejected(self):
        record = self._record()
        record.pop("contract_id")
        result = ingest_outcome_records([record], source="local_manual")
        self.assertEqual(result["records_rejected"], 1)
        self.assertEqual(result["rejected_reason_counts"]["missing_matching_key"], 1)

    def test_duplicate_outcomes_deduped(self):
        with TemporaryDirectory() as tmp:
            first = ingest_outcome_records([self._record()], source="local_manual", dry_run=False, persist=True, base_data_dir=tmp)
            second = ingest_outcome_records([self._record()], source="local_manual", dry_run=False, persist=True, base_data_dir=tmp)
            self.assertEqual(first["outcome_records_written"], 1)
            self.assertEqual(second["duplicate_count"], 1)
            self.assertEqual(second["outcome_records_written"], 0)
            self.assertEqual(len(load_outcome_records(tmp)), 1)

    def test_future_settled_at_rejected(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cleaned, reason = validate_outcome_record(self._record(settled_at=future), source="local_manual")
        self.assertIsNone(cleaned)
        self.assertEqual(reason, "future_settled_at")

    def test_dry_run_accepts_test_fixture_without_persisting(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records(
                [self._record(source="test_fixture")],
                source="test_fixture",
                dry_run=True,
                persist=True,
                base_data_dir=tmp,
            )
            self.assertEqual(result["records_valid"], 1)
            self.assertFalse(result["persisted"])
            self.assertFalse(result["local_persistence"])
            self.assertEqual(result["persistence_blocked_reason"], "dry_run")
            self.assertEqual(load_outcome_records(tmp), [])

    def test_dry_run_required_before_local_persistence(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records(
                [
                    self._record(
                        source="read_only_settlement",
                        evidence_type="explicit_settlement_field",
                        evidence_summary="field_names:settlement_result",
                    )
                ],
                source="read_only_settlement",
                dry_run=True,
                persist=True,
                base_data_dir=tmp,
            )
            self.assertEqual(result["records_valid"], 1)
            self.assertFalse(result["persisted"])
            self.assertFalse(result["local_persistence"])
            self.assertEqual(result["outcome_records_written"], 0)
            self.assertEqual(result["persistence_blocked_reason"], "dry_run")
            self.assertEqual(load_outcome_records(tmp), [])

    def test_persisted_live_records_reject_test_fixture_source(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records(
                [self._record(source="test_fixture")],
                source="test_fixture",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            self.assertEqual(result["records_valid"], 0)
            self.assertEqual(result["records_rejected"], 1)
            self.assertEqual(result["rejected_reason_counts"]["non_real_source_not_persistable"], 1)
            self.assertFalse(result["persisted"])
            self.assertEqual(load_outcome_records(tmp), [])

    def test_read_only_settlement_source_can_persist_when_valid(self):
        with TemporaryDirectory() as tmp:
            result = ingest_outcome_records(
                [self._record(source="read_only_settlement", evidence_type="explicit_settlement_field", evidence_summary="field_names:settlement_result")],
                source="read_only_settlement",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            self.assertEqual(result["records_valid"], 1)
            self.assertTrue(result["persisted"])
            stored = load_outcome_records(tmp)[0]
            self.assertEqual(stored["source"], "read_only_settlement")
            self.assertEqual(stored["evidence_type"], "explicit_settlement_field")

    def test_unknown_labels_rejected_for_real_outcomes(self):
        status_result = ingest_outcome_records([self._record(outcome_status="unknown")], source="local_manual")
        final_result = ingest_outcome_records([self._record(final_outcome="unknown")], source="local_manual")
        self.assertEqual(status_result["rejected_reason_counts"]["unsupported_outcome_status"], 1)
        self.assertEqual(final_result["rejected_reason_counts"]["unsupported_final_outcome"], 1)

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
                source="local_manual",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            record = load_outcome_records(tmp)[0]
            rendered = str(record)
            self.assertEqual(result["records_valid"], 1)
            self.assertNotIn("provider_payload", rendered)
            self.assertNotIn("secret", rendered)
            self.assertLessEqual(len(record["notes"]), 240)

    def test_incomplete_pending_rows_do_not_create_completion_candidates(self):
        report = build_outcome_completion_report(
            pending_rows=[
                {
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "contract_id": "KXTEST",
                    "outcome_status": None,
                    "final_outcome": None,
                    "settled_at": None,
                    "source": "local_manual",
                }
            ],
            read_only_records=[],
            use_kalshi_snapshot=False,
        )
        self.assertEqual(report["completion_candidates_count"], 0)
        self.assertEqual(report["pending_diagnostics"]["rows_missing_final_outcome"], 1)

    def test_kalshi_read_only_explicit_yes_and_no_map_to_outcomes(self):
        pending = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXYES"},
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXNO"},
        ]
        report = discover_kalshi_settlements_for_pending_rows(
            pending,
            read_only_records=[
                {"contract_id": "KXYES", "settlement_result": "yes", "status": "settled", "settlement_time": "2026-05-29T00:00:00+00:00", "yes_price": 0.01},
                {"contract_id": "KXNO", "settlement_result": "no", "status": "settled", "settlement_time": "2026-05-29T00:00:00+00:00", "yes_price": 0.99},
            ],
        )
        outcomes = {row["contract_id"]: row["final_outcome"] for row in report["completion_candidates"]}
        self.assertEqual(outcomes["KXYES"], "yes")
        self.assertEqual(outcomes["KXNO"], "no")
        self.assertEqual(report["settled_yes_count"], 1)
        self.assertEqual(report["settled_no_count"], 1)

    def test_kalshi_closed_without_result_and_current_price_do_not_persist(self):
        classification = classify_kalshi_settlement({"contract_id": "KX", "status": "closed", "yes_price": 1.0})
        self.assertEqual(classification["classification"], "unknown")
        report = discover_kalshi_settlements_for_pending_rows(
            [{"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KX"}],
            read_only_records=[{"contract_id": "KX", "status": "closed", "yes_price": 1.0, "close_time": "2026-05-29T00:00:00+00:00"}],
        )
        self.assertEqual(report["completion_candidates_count"], 0)
        self.assertEqual(report["unknown_count"], 1)

    def test_kalshi_not_settled_market_does_not_create_candidate(self):
        report = discover_kalshi_settlements_for_pending_rows(
            [{"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXOPEN"}],
            read_only_records=[{"contract_id": "KXOPEN", "status": "active", "yes_price": 0.99}],
        )
        self.assertEqual(report["completion_candidates_count"], 0)
        self.assertEqual(report["not_settled_count"], 1)

    def test_imported_file_valid_and_invalid_rows(self):
        result = validate_imported_outcome_rows(
            [
                self._record(source="imported_file"),
                self._record(source="test_fixture"),
                self._record(source="imported_file", contract_id=None, ticker=None),
            ]
        )
        self.assertEqual(result["valid_rows"], 1)
        self.assertEqual(result["rejected_rows"], 2)
        self.assertEqual(result["rejected_reason_counts"]["non_real_source_not_persistable"], 1)
        self.assertEqual(result["rejected_reason_counts"]["missing_matching_key"], 1)
