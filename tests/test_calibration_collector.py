import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.calibration import build_calibration_report
from automation_scheduler.calibration_collector import _normalize_records, _select_candidates, collector_policy_from_env, run_collector_cycle, write_daily_report
from automation_scheduler.kalshi_readonly_adapter import KalshiReadonlyAdapter
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
        "volume_fp": "1000",
        "open_interest_fp": "1000",
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
            for idx in range(16):
                records.append(_market(f"KXSHORT{idx}", self._future(hours=2)))
            for idx in range(3):
                records.append(_market(f"KXMED{idx}", self._future(days=3)))
            records.append(_market("KXLONG0", self._future(days=20)))
            result = run_collector_cycle(
                dry_run=True,
                persist_outcomes=False,
                max_new_contracts=20,
                target_daily_new_contracts=20,
                base_data_dir=tmp,
                read_only_records=records,
            )
            self.assertEqual(result["new_contracts_selected"], 20)
            self.assertEqual(result["selected_short_term"], 16)
            self.assertEqual(result["selected_medium_term"], 3)
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
            watchlist_dir = Path(tmp) / "collector_scheduler" / "watchlists"
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
            daily = json.loads((Path(tmp) / "collector_scheduler" / "daily" / f"{datetime.now(timezone.utc).date().isoformat()}.json").read_text(encoding="utf-8"))

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
            self.assertIn("progress_to_100", report)
            self.assertIn("new_contracts_added_today", report)
            self.assertIn("outcomes_persisted_today", report)
            self.assertTrue((Path(tmp) / "collector_scheduler" / "daily" / "2026-05-30.json").exists())
            self.assertTrue((Path(tmp) / "collector_scheduler" / "daily" / "2026-05-30.md").exists())

    def test_high_throughput_target_250_and_hard_cap_500_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [_market(f"KXHI{i}", self._future(hours=2)) for i in range(80)]
            result = run_collector_cycle(
                dry_run=True,
                max_new_contracts=999,
                target_daily_new_contracts=600,
                hard_cap_daily_new_contracts=500,
                max_markets_scanned=25000,
                base_data_dir=tmp,
                read_only_records=records,
            )
            self.assertEqual(result["daily_new_contract_target"], 500)
            self.assertEqual(result["daily_new_contract_hard_cap"], 500)
            self.assertEqual(result["collector_policy"]["max_new_contracts_per_cycle"], 50)
            self.assertEqual(result["new_contracts_selected"], 50)
            self.assertFalse(result["provider_write"])

    def test_unsafe_negative_or_unconfigured_caps_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            negative = run_collector_cycle(
                dry_run=True,
                max_new_contracts=-1,
                target_daily_new_contracts=250,
                base_data_dir=tmp,
                read_only_records=[],
            )
            self.assertFalse(negative["ok"])
            self.assertEqual(negative["status"], "invalid_request")
            unsafe = run_collector_cycle(
                dry_run=True,
                max_new_contracts=50,
                target_daily_new_contracts=250,
                hard_cap_daily_new_contracts=501,
                base_data_dir=tmp,
                read_only_records=[],
            )
            self.assertFalse(unsafe["ok"])
            self.assertIn("hard_cap_daily_new_contracts_exceeds_configured_cap", unsafe["errors"])

    def test_closed_unresolved_rechecked_before_new_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchlist_dir = Path(tmp) / "collector_scheduler" / "watchlists"
            watchlist_dir.mkdir(parents=True)
            item = {
                "provider": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "ticker": "KXRECHECKFIRST",
                "contract_id": "KXRECHECKFIRST",
                "close_time": self._past(hours=1),
                "collector_bucket": "short_term",
                "next_recheck_time": self._past(minutes=10),
            }
            (watchlist_dir / "unresolved.latest.json").write_text(json.dumps({"items": [item]}), encoding="utf-8")
            fetched = {
                "ok": True,
                "status": "ok",
                "ticker": "KXRECHECKFIRST",
                "record": {
                    "ticker": "KXRECHECKFIRST",
                    "contract_id": "KXRECHECKFIRST",
                    "settlement_result": "no",
                    "result": "no",
                    "status": "finalized",
                    "settlement_time": self._past(minutes=5),
                },
            }
            with patch("automation_scheduler.calibration_collector._fetch_public_market_by_ticker", return_value=fetched):
                result = run_collector_cycle(
                    dry_run=False,
                    persist_outcomes=True,
                    max_new_contracts=1,
                    target_daily_new_contracts=250,
                    base_data_dir=tmp,
                    read_only_records=[_market("KXNEWAFTERRECHECK", self._future(hours=2))],
                )
            self.assertEqual(result["records_checked"], 1)
            self.assertEqual(result["outcomes_persisted"], 1)
            self.assertEqual(result["new_contracts_added"], 1)
            self.assertEqual(load_outcome_records(tmp)[0]["final_outcome"], "no")

    def test_unknown_and_price_only_rechecks_do_not_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchlist_dir = Path(tmp) / "collector_scheduler" / "watchlists"
            watchlist_dir.mkdir(parents=True)
            item = {
                "provider": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "ticker": "KXUNKNOWN",
                "contract_id": "KXUNKNOWN",
                "close_time": self._past(hours=1),
                "collector_bucket": "short_term",
                "next_recheck_time": self._past(minutes=10),
            }
            (watchlist_dir / "unresolved.latest.json").write_text(json.dumps({"items": [item]}), encoding="utf-8")
            fetched = {
                "ok": True,
                "status": "ok",
                "ticker": "KXUNKNOWN",
                "record": {
                    "ticker": "KXUNKNOWN",
                    "contract_id": "KXUNKNOWN",
                    "status": "closed",
                    "last_price": 1,
                    "close_time": self._past(hours=1),
                },
            }
            with patch("automation_scheduler.calibration_collector._fetch_public_market_by_ticker", return_value=fetched):
                result = run_collector_cycle(
                    dry_run=False,
                    persist_outcomes=True,
                    max_new_contracts=0,
                    target_daily_new_contracts=250,
                    base_data_dir=tmp,
                    read_only_records=[],
                )
            self.assertEqual(result["outcomes_persisted"], 0)
            self.assertEqual(load_outcome_records(tmp), [])

    def test_exploration_bucket_is_capped_at_ten_percent(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = []
            for idx in range(50):
                row = _market(f"KXLOW{idx}", self._future(hours=2))
                row["volume_fp"] = "10"
                row["open_interest_fp"] = "10"
                records.append(row)
            result = run_collector_cycle(
                dry_run=True,
                max_new_contracts=50,
                target_daily_new_contracts=250,
                base_data_dir=tmp,
                read_only_records=records,
            )
            self.assertEqual(result["new_contracts_selected"], 5)
            self.assertEqual(result["exploration_sample_count"], 5)
            self.assertTrue(all(row.get("exploration_sample") for row in result["selected_contracts"]))

    def test_quality_gates_reject_unsupported_market_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = collector_policy_from_env()
            day_state = {"sampled_tickers": []}
            candidate = {
                "ticker": "KXBADTYPE",
                "contract_id": "KXBADTYPE",
                "market_type": "sportsbook",
                "close_time": self._future(hours=2),
                "yes_price": 0.5,
                "pricing_quality": "complete",
                "pricing_quality_score": 100,
                "liquidity_tier": "adequate_liquidity",
            }
            result = _select_candidates(
                [candidate],
                base_data_dir=tmp,
                day_state=day_state,
                policy=policy,
                max_new_contracts=50,
                target_daily_new_contracts=250,
                include_short_term=True,
                include_medium_term=True,
                include_long_term=True,
            )
            self.assertEqual(result["selected_flat"], [])
            self.assertEqual(result["quality_gate_rejection_count"], 1)
            self.assertIn("unsupported_market_type", result["rejected_reason_counts"])

    def test_provider_rate_limit_triggers_adaptive_throttle(self):
        with tempfile.TemporaryDirectory() as tmp:
            scan = {"status": "provider_error", "markets_scanned": 1, "records": [_market("KXRATE", self._future(hours=2))], "blockers": ["http_429"]}
            with patch("automation_scheduler.calibration_collector._fetch_public_markets", return_value=scan):
                result = run_collector_cycle(
                    dry_run=True,
                    max_new_contracts=50,
                    target_daily_new_contracts=250,
                    base_data_dir=tmp,
                )
            self.assertEqual(result["new_contracts_selected"], 0)
            self.assertIn("provider_rate_or_availability_limit", result["adaptive_throttle_reasons"])

    def test_partial_provider_timeout_reduces_but_does_not_zero_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = _normalize_records([_market(f"KXPARTIAL{i}", self._future(hours=2)) for i in range(50)], KalshiReadonlyAdapter({}))
            scan = {"status": "provider_error", "markets_scanned": 50, "records": records, "blockers": ["read_timeout"]}
            with patch("automation_scheduler.calibration_collector._fetch_public_markets", return_value=scan):
                result = run_collector_cycle(
                    dry_run=True,
                    max_new_contracts=50,
                    target_daily_new_contracts=250,
                    base_data_dir=tmp,
                )
            self.assertEqual(result["effective_max_new_contracts"], 25)
            self.assertEqual(result["new_contracts_selected"], 25)
            self.assertIn("provider_error_throttle", result["adaptive_throttle_reasons"])

    def test_backlog_limit_stops_new_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            watchlist_dir = Path(tmp) / "collector_scheduler" / "watchlists"
            watchlist_dir.mkdir(parents=True)
            rows = [
                {
                    "ticker": f"KXBACKLOG{i}",
                    "contract_id": f"KXBACKLOG{i}",
                    "close_time": self._future(hours=10),
                    "collector_bucket": "short_term",
                }
                for i in range(1000)
            ]
            (watchlist_dir / "unresolved.latest.json").write_text(json.dumps({"items": rows}), encoding="utf-8")
            result = run_collector_cycle(
                dry_run=True,
                max_new_contracts=50,
                target_daily_new_contracts=250,
                base_data_dir=tmp,
                read_only_records=[_market("KXBLOCKEDBYBACKLOG", self._future(hours=2))],
            )
            self.assertEqual(result["new_contracts_selected"], 0)
            self.assertIn("settlement_backlog_limit_reached", result["adaptive_throttle_reasons"])
            self.assertGreaterEqual(result["watchlist_size"], 1000)


if __name__ == "__main__":
    unittest.main()
