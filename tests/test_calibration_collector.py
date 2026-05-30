import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.calibration import build_calibration_report
from automation_scheduler.calibration_collector import run_collector_cycle, write_daily_report
from automation_scheduler.outcome_store import ingest_outcome_records, load_outcome_records
from automation_scheduler.paper_decision_ledger import persist_paper_decisions_for_review_items


def _market(ticker, close_time, *, price="0.5000", status="active"):
    row = {
        "ticker": ticker,
        "title": f"{ticker} title",
        "event_ticker": f"{ticker}-EVENT",
        "close_time": close_time,
        "expiration_time": close_time,
        "status": status,
        "rules_primary": "Explicit market rules.",
        "volume_fp": "100",
        "open_interest_fp": "100",
        "yes_bid_dollars": "0.4000",
        "yes_ask_dollars": "0.6000",
        "no_bid_dollars": "0.4000",
        "no_ask_dollars": "0.6000",
    }
    if price is not None:
        row["last_price_dollars"] = price
    return row


class TestCalibrationCollector(unittest.TestCase):
    def _future(self, **kwargs):
        return (datetime.now(timezone.utc) + timedelta(**kwargs)).isoformat().replace("+00:00", "Z")

    def _past(self, **kwargs):
        return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat().replace("+00:00", "Z")

    def test_selects_up_to_max_and_splits_buckets(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = []
            for idx in range(7):
                records.append(_market(f"KXSHORT{idx}", self._future(hours=2)))
            for idx in range(2):
                records.append(_market(f"KXMED{idx}", self._future(days=3)))
            records.append(_market("KXLONG0", self._future(days=10)))
            result = run_collector_cycle(
                dry_run=True,
                persist_outcomes=False,
                max_new_contracts=10,
                target_daily_new_contracts=10,
                base_data_dir=tmp,
                read_only_records=records,
            )
            self.assertEqual(result["new_contracts_selected"], 10)
            self.assertEqual(result["selected_short_term"], 7)
            self.assertEqual(result["selected_medium_term"], 2)
            self.assertEqual(result["selected_long_term"], 1)
            self.assertEqual(result["daily_new_contracts_remaining"], 0)
            self.assertFalse(result["provider_write"])
            self.assertEqual(result["execution_allowed_count"], 0)

    def test_handles_fewer_available_and_excludes_invalid_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [
                _market("KXOK", self._future(hours=3)),
                _market("KXNOCLOSE", None),
                _market("KXNOPRICE", self._future(hours=3), price=None),
            ]
            records[1].pop("close_time")
            for key in ("yes_bid_dollars", "yes_ask_dollars", "no_bid_dollars", "no_ask_dollars"):
                records[2].pop(key)
            result = run_collector_cycle(
                dry_run=True,
                max_new_contracts=100,
                target_daily_new_contracts=100,
                base_data_dir=tmp,
                read_only_records=records,
            )
            self.assertEqual(result["new_contracts_selected"], 1)
            self.assertEqual(result["eligible_contracts_found"], 1)
            self.assertIn("missing_close_time", result["selection_rejected_reason_counts"])
            self.assertIn("missing_price_signal", result["selection_rejected_reason_counts"])

    def test_dedupes_repeated_tickers_and_daily_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [
                _market("KXDUP", self._future(hours=3)),
                _market("KXDUP", self._future(hours=3)),
                _market("KXOTHER", self._future(hours=3)),
            ]
            result = run_collector_cycle(
                dry_run=True,
                max_new_contracts=25,
                target_daily_new_contracts=1,
                base_data_dir=tmp,
                read_only_records=records,
            )
            self.assertEqual(result["new_contracts_selected"], 1)
            self.assertEqual(result["daily_new_contracts_remaining"], 0)
            self.assertGreaterEqual(result["duplicate_contracts_skipped"], 1)

    def test_persists_only_explicit_rechecked_outcomes_after_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            close_time = self._past(hours=1)
            watchlist_dir = Path(tmp) / "outcomes" / "watchlists"
            watchlist_dir.mkdir(parents=True)
            item = {
                "provider": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "ticker": "KXDUE",
                "contract_id": "KXDUE",
                "close_time": close_time,
                "run_id": "collector_test",
                "review_item_id": "review_1",
                "decision_id": "decision_1",
                "collector_bucket": "short_term",
                "next_recheck_time": self._past(minutes=30),
                "last_checked_at": None,
                "recheck_count": 0,
            }
            (watchlist_dir / "unresolved.latest.json").write_text(json.dumps({"items": [item]}), encoding="utf-8")
            fetched = {
                "ok": True,
                "status": "ok",
                "ticker": "KXDUE",
                "record": {
                    "ticker": "KXDUE",
                    "contract_id": "KXDUE",
                    "settlement_result": "yes",
                    "result": "yes",
                    "status": "finalized",
                    "settlement_time": self._past(minutes=5),
                },
            }
            with patch("automation_scheduler.calibration_collector._fetch_public_market_by_ticker", return_value=fetched):
                result = run_collector_cycle(
                    dry_run=False,
                    persist_outcomes=True,
                    max_new_contracts=0,
                    target_daily_new_contracts=100,
                    base_data_dir=tmp,
                    read_only_records=[],
                )
            self.assertEqual(result["dry_run_ingest"]["records_valid"], 1)
            self.assertEqual(result["outcomes_persisted"], 1)
            self.assertEqual(load_outcome_records(tmp)[0]["final_outcome"], "yes")
            self.assertFalse(result["provider_write"])

    def test_collector_preserves_historical_matches_and_daily_matches_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            persist_paper_decisions_for_review_items(
                [
                    {
                        "id": "historical-review",
                        "provider_id": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KXHIST",
                        "ticker": "KXHIST",
                        "implied_probability": 0.7,
                        "execution_allowed": False,
                    }
                ],
                run_id="close_soon_historical",
                base_data_dir=tmp,
            )
            ingest_outcome_records(
                [
                    {
                        "provider": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "contract_id": "KXHIST",
                        "ticker": "KXHIST",
                        "review_item_id": "historical-review",
                        "run_id": "close_soon_historical",
                        "outcome_status": "settled",
                        "final_outcome": "no",
                        "settled_at": "2026-05-29T00:00:00+00:00",
                        "source": "read_only_settlement",
                        "evidence_type": "explicit_settlement_field",
                    }
                ],
                source="read_only_settlement",
                dry_run=False,
                persist=True,
                base_data_dir=tmp,
            )
            result = run_collector_cycle(
                dry_run=False,
                persist_outcomes=True,
                max_new_contracts=0,
                target_daily_new_contracts=0,
                base_data_dir=tmp,
                read_only_records=[],
            )
            calibration = build_calibration_report(base_data_dir=tmp)
            daily = json.loads((Path(tmp) / "outcomes" / "collector" / "daily" / f"{datetime.now(timezone.utc).date().isoformat()}.json").read_text(encoding="utf-8"))

            self.assertEqual(result["matched_outcomes_count"], calibration["matched_outcomes_count"])
            self.assertEqual(daily["matched_outcomes_count"], calibration["matched_outcomes_count"])
            self.assertEqual(calibration["matched_outcomes_count"], 1)
            self.assertEqual(calibration["paper_decisions_count"], 1)
            self.assertFalse(result["provider_write"])
            self.assertEqual(result["execution_allowed_count"], 0)

    def test_daily_report_writes_compact_safety_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = write_daily_report(tmp, day="2026-05-30", calibration_report={"status": "insufficient_data", "coverage_rate": 0, "matched_outcomes_count": 0, "warnings": ["insufficient_sample"], "next_required_data": ["settlement_results"]})
            self.assertEqual(report["provider_write"], False)
            self.assertEqual(report["execution_allowed_count"], 0)
            self.assertTrue((Path(tmp) / "outcomes" / "collector" / "daily" / "2026-05-30.json").exists())
            self.assertTrue((Path(tmp) / "outcomes" / "collector" / "daily" / "2026-05-30.md").exists())


if __name__ == "__main__":
    unittest.main()
