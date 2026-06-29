import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.services.streamlit_dashboard_facade import build_import_plan, build_outcome_identity, build_kalshi_outcome_migration_package, compare_migration_package_to_render, dedupe_migration_outcomes, discover_local_outcome_records, import_local_settlement_records, validate_migration_outcome, write_migration_package
from src.services.streamlit_dashboard_facade import outcome_migration as migration_module
from src.services.streamlit_dashboard_facade import build_calibration_report
from src.services.streamlit_dashboard_facade import ingest_outcome_records, load_outcome_records
from src.services.streamlit_dashboard_facade import load_paper_decisions
from src.services.streamlit_dashboard_facade import persist_paper_decisions_for_review_items


class TestOutcomeMigration(unittest.TestCase):
    def _outcome_record(self, **overrides):
        row = {
            "provider": "kalshi_prediction_market",
            "market_type": "prediction_market",
            "ticker": "KXTEST",
            "contract_id": "KXTEST",
            "decision_id": "decision_1",
            "review_item_id": "review_1",
            "run_id": "kalshi_calibration_test",
            "outcome_status": "settled",
            "final_outcome": "yes",
            "settled_at": "2026-05-29T00:00:00+00:00",
            "source": "read_only_settlement",
            "evidence_type": "explicit_settlement_field",
        }
        row.update(overrides)
        return row

    def test_identity_is_stable(self):
        left = self._outcome_record()
        right = self._outcome_record(final_outcome="yes", settled_at="2026-05-29T00:01:00+00:00")
        self.assertEqual(build_outcome_identity(left), build_outcome_identity(right))

    def test_dedupe_collapses_latest_legacy_and_items_duplicates(self):
        records = [self._outcome_record(), self._outcome_record(), self._outcome_record()]
        result = dedupe_migration_outcomes(records)
        self.assertEqual(result["records_valid"], 1)
        self.assertEqual(result["duplicate_count"], 2)
        self.assertEqual(result["records_rejected"], 0)

    def test_discovery_can_read_current_and_legacy_paths(self):
        with TemporaryDirectory() as tmp:
            current = Path(tmp) / "outcomes" / "latest.json"
            legacy = Path(tmp) / "outcomes" / "collector" / "items" / "legacy_cycle.json"
            current.parent.mkdir(parents=True)
            legacy.parent.mkdir(parents=True)
            current.write_text(json.dumps({"items": [self._outcome_record(ticker="KXCUR", contract_id="KXCUR")]}), encoding="utf-8")
            legacy.write_text(json.dumps({"items": [self._outcome_record(ticker="KXLEG", contract_id="KXLEG")]}), encoding="utf-8")

            discovered = discover_local_outcome_records(source_paths=[current, legacy])
            tickers = {row["ticker"] for row in discovered["records"]}

        self.assertEqual(discovered["records_found"], 2)
        self.assertEqual(tickers, {"KXCUR", "KXLEG"})

    def test_invalid_records_rejected(self):
        cases = [
            (self._outcome_record(final_outcome="maybe"), "unsupported_final_outcome"),
            (self._outcome_record(outcome_status="pending"), "unsupported_outcome_status"),
            (self._outcome_record(ticker=None, contract_id=None), "missing_matching_key"),
            (self._outcome_record(settled_at=None), "missing_or_invalid_settled_at"),
            (self._outcome_record(raw_payload={"x": 1}), "raw_payload_field_rejected"),
            (self._outcome_record(api_secret="secret"), "secret_like_field_rejected"),
            (self._outcome_record(evidence_type="inferred_settlement"), "inferred_outcomes_rejected"),
        ]
        for record, reason in cases:
            with self.subTest(reason=reason):
                result = validate_migration_outcome(record)
                self.assertFalse(result["ok"])
                self.assertEqual(result["reason"], reason)

    def test_package_builder_reads_historical_paths_and_supporting_paper(self):
        with TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                first = ingest_outcome_records([self._outcome_record(ticker="KX1", contract_id="KX1")], source="read_only_settlement", dry_run=False, persist=True, base_data_dir=tmp)
                ingest_outcome_records([self._outcome_record(ticker="KX2", contract_id="KX2", final_outcome="no", settled_at="2026-05-29T00:02:00+00:00")], source="read_only_settlement", dry_run=False, persist=True, base_data_dir=tmp)
                persist_paper_decisions_for_review_items(
                    [
                        {"id": "review_1", "provider_id": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KX1", "contract_id": "KX1"},
                        {"id": "review_2", "provider_id": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KX2", "contract_id": "KX2"},
                    ],
                    run_id="kalshi_calibration_test",
                    base_data_dir=tmp,
                )
                latest_path = Path(tmp) / "outcomes" / "latest.json"
                latest = json.loads(latest_path.read_text(encoding="utf-8"))
                latest["items"] = [row for row in latest["items"] if row["contract_id"] == "KX2"]
                latest_path.write_text(json.dumps(latest), encoding="utf-8")

                package = build_kalshi_outcome_migration_package()
                self.assertEqual(first["outcome_records_written"], 1)
                self.assertEqual(package["records_valid"], 2)
                self.assertEqual(package["final_outcome_counts"], {"no": 1, "yes": 1})
                self.assertEqual(package["logical_duplicate_count"], 0)
                self.assertEqual(package["supporting_paper_decision_count"], 2)

    def test_write_package_outputs_compact_files(self):
        with TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"AUTOMATION_DATA_DIR": tmp}, clear=False):
                package = {
                    "run_id": "kalshi_outcome_migration_test",
                    "created_at": "2026-05-29T00:00:00+00:00",
                    "records_valid": 1,
                    "records_rejected": 0,
                    "duplicate_count": 0,
                    "final_outcome_counts": {"yes": 1},
                    "records": [self._outcome_record()],
                    "supporting_paper_decisions": [],
                    "raw_payload_included": False,
                    "secrets_included": False,
                }
                result = write_migration_package(package)
                for key in ("latest_path", "item_path", "daily_json_path", "daily_markdown_path"):
                    self.assertTrue(Path(result[key]).exists())
                text = Path(result["latest_path"]).read_text(encoding="utf-8")
                self.assertNotIn('"raw_payload":', text)
                self.assertNotIn('"api_key":', text)

    def test_compare_and_import_plan_report_local_render_delta(self):
        package = {"records": [self._outcome_record(ticker="KX1", contract_id="KX1"), self._outcome_record(ticker="KX2", contract_id="KX2")], "duplicate_count": 0, "records_rejected": 0}
        render_state = {"total_count": 2, "records": [self._outcome_record(ticker="KX2", contract_id="KX2"), self._outcome_record(ticker="KX3", contract_id="KX3")]}

        comparison = compare_migration_package_to_render(package, render_state)
        plan = build_import_plan(package, render_state)

        self.assertEqual(comparison["overlap_count"], 1)
        self.assertEqual(comparison["local_only_count"], 1)
        self.assertEqual(comparison["render_only_count"], 1)
        self.assertEqual(plan["would_insert_count"], 1)
        self.assertEqual(plan["projected_outcomes_after_import"], 3)
        self.assertEqual(plan["recommendation"], "dry_run_import")

    def test_import_dry_run_and_persist_false_write_nothing(self):
        with TemporaryDirectory() as tmp:
            paper = {"decision_id": "decision_1", "review_item_id": "review_1", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXTEST", "contract_id": "KXTEST", "execution_allowed": False, "paper_only": True}
            dry_run = import_local_settlement_records(
                [self._outcome_record()],
                supporting_paper_decisions=[paper],
                dry_run=True,
                persist=False,
                base_data_dir=tmp,
            )
            persist_false = import_local_settlement_records(
                [self._outcome_record()],
                supporting_paper_decisions=[paper],
                dry_run=False,
                persist=False,
                base_data_dir=tmp,
            )

            self.assertEqual(dry_run["would_insert_count"], 1)
            self.assertEqual(dry_run["matched_paper_decision_count"], 1)
            self.assertEqual(persist_false["would_insert_count"], 1)
            self.assertEqual(load_outcome_records(tmp), [])
            self.assertEqual(load_paper_decisions(tmp), [])

    def test_import_persists_union_once_and_preserves_existing(self):
        with TemporaryDirectory() as tmp:
            ingest_outcome_records(
                [self._outcome_record(ticker="KXEXISTING", contract_id="KXEXISTING")],
                source="read_only_settlement",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            paper = {"decision_id": "decision_new", "review_item_id": "review_new", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXNEW", "contract_id": "KXNEW", "execution_allowed": False, "paper_only": True}
            result = import_local_settlement_records(
                [
                    self._outcome_record(ticker="KXEXISTING", contract_id="KXEXISTING"),
                    self._outcome_record(ticker="KXNEW", contract_id="KXNEW", decision_id="decision_new", review_item_id="review_new"),
                ],
                supporting_paper_decisions=[paper],
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )

            stored_tickers = {row["ticker"] for row in load_outcome_records(tmp)}
            self.assertEqual(result["duplicate_count"], 1)
            self.assertEqual(result["would_insert_count"], 1)
            self.assertEqual(result["inserted_count"], 1)
            self.assertEqual(result["supporting_paper_decisions_written"], 1)
            self.assertEqual(stored_tickers, {"KXEXISTING", "KXNEW"})

            second = import_local_settlement_records(
                [
                    self._outcome_record(ticker="KXEXISTING", contract_id="KXEXISTING"),
                    self._outcome_record(ticker="KXNEW", contract_id="KXNEW", decision_id="decision_new", review_item_id="review_new"),
                ],
                supporting_paper_decisions=[paper],
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )

            self.assertEqual(second["duplicate_count"], 2)
            self.assertEqual(second["would_insert_count"], 0)
            self.assertEqual(second["inserted_count"], 0)
            self.assertEqual(len(load_outcome_records(tmp)), 2)

    def test_import_blocks_unmatched_outcomes_before_persist(self):
        with TemporaryDirectory() as tmp:
            result = import_local_settlement_records(
                [self._outcome_record(ticker="KXUNMATCHED", contract_id="KXUNMATCHED")],
                supporting_paper_decisions=[],
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "unmatched_paper_decisions")
            self.assertEqual(result["unmatched_count"], 1)
            self.assertEqual(load_outcome_records(tmp), [])

    def test_imported_supporting_paper_decisions_are_visible_to_calibration(self):
        with TemporaryDirectory() as tmp:
            paper = {"decision_id": "decision_1", "review_item_id": "review_1", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXTEST", "contract_id": "KXTEST", "execution_allowed": False, "paper_only": True}
            result = import_local_settlement_records(
                [self._outcome_record()],
                supporting_paper_decisions=[paper],
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            report = build_calibration_report(base_data_dir=tmp)

            self.assertEqual(result["inserted_count"], 1)
            self.assertEqual(result["projected_matched_outcomes_count"], 1)
            self.assertEqual(report["outcome_records_count"], 1)
            self.assertEqual(report["paper_ledger_records_count"], 1)
            self.assertEqual(report["matched_outcomes_count"], 1)
            self.assertEqual(report["unmatched_outcomes_count"], 0)

    def test_transactional_write_rolls_back_partial_replace(self):
        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            first.write_text(json.dumps({"old": 1}), encoding="utf-8")
            second.write_text(json.dumps({"old": 2}), encoding="utf-8")
            original_replace = Path.replace
            calls = {"count": 0}

            def flaky_replace(path, target):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("forced transaction failure")
                return original_replace(path, target)

            with patch.object(Path, "replace", flaky_replace):
                with self.assertRaises(OSError):
                    migration_module._transactional_write_json(
                        [
                            (first, {"new": 1}),
                            (second, {"new": 2}),
                        ]
                    )

            self.assertEqual(json.loads(first.read_text(encoding="utf-8")), {"old": 1})
            self.assertEqual(json.loads(second.read_text(encoding="utf-8")), {"old": 2})

    def test_import_write_failure_rolls_back_outcomes_and_paper_decisions(self):
        with TemporaryDirectory() as tmp:
            ingest_outcome_records(
                [self._outcome_record(ticker="KXEXISTING", contract_id="KXEXISTING")],
                source="read_only_settlement",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            paper = {"decision_id": "decision_new", "review_item_id": "review_new", "provider": "kalshi_prediction_market", "market_type": "prediction_market", "ticker": "KXNEW", "contract_id": "KXNEW", "execution_allowed": False, "paper_only": True}
            original_replace = Path.replace
            calls = {"count": 0}

            def flaky_replace(path, target):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("forced import transaction failure")
                return original_replace(path, target)

            with patch.object(Path, "replace", flaky_replace):
                result = import_local_settlement_records(
                    [self._outcome_record(ticker="KXNEW", contract_id="KXNEW", decision_id="decision_new", review_item_id="review_new")],
                    supporting_paper_decisions=[paper],
                    dry_run=False,
                    persist=True,
                    base_data_dir=tmp,
                )

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "persistence_failed")
            self.assertEqual(result["inserted_count"], 0)
            self.assertEqual({row["ticker"] for row in load_outcome_records(tmp)}, {"KXEXISTING"})
            self.assertEqual(load_paper_decisions(tmp), [])


if __name__ == "__main__":
    unittest.main()
