import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.services.streamlit_dashboard_facade import ingest_outcome_records, load_outcome_records
from src.services.streamlit_dashboard_facade import load_paper_decisions
from tests.support.action_imports import app


class TestOutcomeImportEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _outcome_record(self, **overrides):
        row = {
            "source": "read_only_settlement",
            "provider": "kalshi_prediction_market",
            "provider_id": "kalshi_prediction_market",
            "market_type": "prediction_market",
            "ticker": "KXENDPOINT",
            "contract_id": "KXENDPOINT",
            "paper_decision_id": "decision_endpoint",
            "review_decision_id": "review_endpoint",
            "final_outcome": "yes",
            "outcome_status": "settled",
            "settled_at": "2026-05-29T00:00:00+00:00",
            "evidence_type": "explicit_settlement_field",
            "evidence_summary": "endpoint test explicit settlement",
            "migration_version": "kalshi_outcome_migration_v1",
        }
        row.update(overrides)
        return row

    def _paper(self, **overrides):
        row = {
            "decision_id": "decision_endpoint",
            "review_item_id": "review_endpoint",
            "provider": "kalshi_prediction_market",
            "market_type": "prediction_market",
            "ticker": "KXENDPOINT",
            "contract_id": "KXENDPOINT",
            "execution_allowed": False,
            "paper_only": True,
        }
        row.update(overrides)
        return row

    def _post(self, payload, headers=None):
        return self.client.post("/api/automation/outcomes/import-local-settlements", json=payload, headers=headers or {})

    def test_dry_run_import_writes_nothing_and_reports_matching(self):
        with TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = self._post(
                    {
                        "dry_run": True,
                        "persist": False,
                        "source": "local_repo_migration",
                        "migration_version": "kalshi_outcome_migration_v1",
                        "records": [self._outcome_record()],
                        "supporting_paper_decisions": [self._paper()],
                    }
                )
                payload = response.json()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(payload["records_received"], 1)
                self.assertEqual(payload["records_valid"], 1)
                self.assertEqual(payload["would_insert_count"], 1)
                self.assertEqual(payload["inserted_count"], 0)
                self.assertEqual(payload["matched_paper_decision_count"], 1)
                self.assertEqual(payload["unmatched_count"], 0)
                self.assertEqual(payload["projected_render_outcome_count"], 1)
                self.assertEqual(payload["projected_matched_outcomes_count"], 1)
                self.assertFalse(payload["provider_write"])
                self.assertFalse(payload["execution_allowed"])
                self.assertEqual(payload["execution_allowed_count"], 0)
                self.assertFalse(payload["raw_payload_included"])
                self.assertFalse(payload["secrets_included"])
                self.assertEqual(load_outcome_records(tmp), [])
                self.assertEqual(load_paper_decisions(tmp), [])

    def test_persist_false_writes_nothing_even_when_dry_run_false(self):
        with TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = self._post(
                    {
                        "dry_run": False,
                        "persist": False,
                        "source": "local_repo_migration",
                        "migration_version": "kalshi_outcome_migration_v1",
                        "records": [self._outcome_record()],
                        "supporting_paper_decisions": [self._paper()],
                    }
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["inserted_count"], 0)
                self.assertEqual(load_outcome_records(tmp), [])
                self.assertEqual(load_paper_decisions(tmp), [])

    def test_persist_requires_collector_token_and_does_not_expose_secret(self):
        with TemporaryDirectory() as tmp:
            env = {"AUTOMATION_DATA_DIR": tmp, "COLLECTOR_CRON_TOKEN": "endpoint-secret"}
            with patch.dict(os.environ, env, clear=False):
                response = self._post(
                    {
                        "dry_run": False,
                        "persist": True,
                        "source": "local_repo_migration",
                        "migration_version": "kalshi_outcome_migration_v1",
                        "records": [self._outcome_record()],
                        "supporting_paper_decisions": [self._paper()],
                    }
                )

                self.assertEqual(response.status_code, 401)
                self.assertNotIn("endpoint-secret", response.text)
                self.assertFalse(response.json()["detail"]["provider_write"])
                self.assertFalse(response.json()["detail"]["execution_allowed"])

    def test_persist_import_unions_new_records_and_skips_existing(self):
        with TemporaryDirectory() as tmp:
            env = {"AUTOMATION_DATA_DIR": tmp, "COLLECTOR_CRON_TOKEN": "endpoint-secret"}
            with patch.dict(os.environ, env, clear=False):
                ingest_outcome_records(
                    [self._outcome_record(ticker="KXEXISTING", contract_id="KXEXISTING")],
                    source="read_only_settlement",
                    dry_run=False,
                    persist=True,
                    base_data_dir=tmp,
                )
                response = self._post(
                    {
                        "dry_run": False,
                        "persist": True,
                        "source": "local_repo_migration",
                        "migration_version": "kalshi_outcome_migration_v1",
                        "records": [
                            self._outcome_record(ticker="KXEXISTING", contract_id="KXEXISTING"),
                            self._outcome_record(ticker="KXNEW", contract_id="KXNEW", paper_decision_id="decision_new", review_decision_id="review_new"),
                        ],
                        "supporting_paper_decisions": [
                            self._paper(decision_id="decision_new", review_item_id="review_new", ticker="KXNEW", contract_id="KXNEW")
                        ],
                    },
                    headers={"X-Collector-Token": "endpoint-secret"},
                )
                payload = response.json()
                stored_tickers = {row["ticker"] for row in load_outcome_records(tmp)}

                self.assertEqual(response.status_code, 200)
                self.assertEqual(payload["duplicate_count"], 1)
                self.assertEqual(payload["would_insert_count"], 1)
                self.assertEqual(payload["inserted_count"], 1)
                self.assertEqual(payload["render_outcomes_after_import_if_persisted"], 2)
                self.assertEqual(stored_tickers, {"KXEXISTING", "KXNEW"})

    def test_persist_import_write_failure_rolls_back_atomically(self):
        with TemporaryDirectory() as tmp:
            env = {"AUTOMATION_DATA_DIR": tmp, "COLLECTOR_CRON_TOKEN": "endpoint-secret"}
            with patch.dict(os.environ, env, clear=False):
                with patch('src.data.outcome_migration._transactional_write_json', side_effect=OSError("forced atomic failure")):
                    response = self._post(
                        {
                            "dry_run": False,
                            "persist": True,
                            "source": "local_repo_migration",
                            "migration_version": "kalshi_outcome_migration_v1",
                            "records": [self._outcome_record()],
                            "supporting_paper_decisions": [self._paper()],
                        },
                        headers={"X-Collector-Token": "endpoint-secret"},
                    )
                payload = response.json()

                self.assertEqual(response.status_code, 200)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["status"], "persistence_failed")
                self.assertEqual(payload["inserted_count"], 0)
                self.assertEqual(load_outcome_records(tmp), [])
                self.assertEqual(load_paper_decisions(tmp), [])

    def test_invalid_raw_payload_and_secret_like_fields_are_rejected_safely(self):
        with TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                response = self._post(
                    {
                        "dry_run": True,
                        "persist": False,
                        "source": "local_repo_migration",
                        "migration_version": "kalshi_outcome_migration_v1",
                        "records": [self._outcome_record(raw_payload={"provider": "body"}, api_secret="secret")],
                        "supporting_paper_decisions": [],
                    }
                )
                payload = response.json()

                self.assertEqual(response.status_code, 200)
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["records_rejected"], 1)
                self.assertIn("raw_payload_field_rejected", payload["rejected_reason_counts"])
                self.assertNotIn("body", response.text)
                self.assertNotIn("api_secret", response.text)


if __name__ == "__main__":
    unittest.main()
