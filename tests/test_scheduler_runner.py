import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

from automation_scheduler import get_scheduler_review_queue
from automation_scheduler.paper_decision_ledger import load_paper_decisions
from automation_scheduler.scheduler_runner import run_scheduler_once


class TestSchedulerRunner(unittest.TestCase):
    def test_dry_run_only(self):
        with TemporaryDirectory() as tmp:
            result = run_scheduler_once(base_data_dir=tmp, dry_run=True, injected_data={"skipped_items": ["a"]})
            self.assertTrue(result["dry_run"])
            self.assertFalse(result["auto_execution_enabled"])
            self.assertIn("report_path", result)
            self.assertIn("records_received", result)
            self.assertEqual(result["review_queue_storage_backend"], "file")
            self.assertIn("review_queue_items_written", result)
            self.assertIn("review_queue_write_path", result)
            skipped = [row for row in result.get("skipped_items", []) if isinstance(row, dict)]
            kalshi_skips = [row for row in skipped if row.get("provider_id") == "kalshi_prediction_market"]
            self.assertTrue(kalshi_skips)

    @patch("src.services.odds_runtime_bridge.SharpSportsbookAdapter.fetch_snapshot")
    @patch("src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.validate_config")
    @patch("src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.fetch_snapshot")
    def test_kalshi_candidates_flow_to_review_queue_with_safety_flags(self, mock_kalshi_snapshot, mock_kalshi_validate_config, mock_sharp_snapshot):
        now = datetime.now(timezone.utc)
        mock_kalshi_validate_config.return_value = {
            "ok": True,
            "status": "ready",
            "blockers": [],
            "credential_status": "ok",
            "live_reads_enabled": True,
            "provider_enabled": True,
            "live_calls_enabled": True,
            "provider_live_calls_enabled": True,
            "dry_run": True,
            "read_only_mode": True,
        }
        mock_sharp_snapshot.return_value = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "sharp_sportsbook",
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "records": [],
            "schema_version": "automation_scheduler.v1.sharp_sportsbook.v1",
            "timestamp": now.isoformat(),
        }
        mock_kalshi_snapshot.return_value = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "kalshi_prediction_market",
            "records_received": 5,
            "records_valid": 5,
            "records_rejected": 0,
            "schema_version": "automation_scheduler.v1.kalshi_prediction_market.v1",
            "records": [
                {
                    "provider_id": "kalshi_prediction_market",
                    "market_id": "m_1",
                    "event_id": "e_1",
                    "event_title": "Event 1",
                    "contract_id": "c_1",
                    "contract_title": "Contract 1",
                    "ticker": "KXEVENT-1",
                    "yes_bid": 0.48,
                    "yes_ask": 0.52,
                    "no_bid": 0.48,
                    "no_ask": 0.52,
                    "yes_price": 0.50,
                    "no_price": 0.50,
                    "implied_probability": 0.50,
                    "volume": 2000,
                    "open_interest": 1800,
                    "liquidity_score": 0.82,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "provider_id": "kalshi_prediction_market",
                    "market_id": "m_2",
                    "event_id": "e_2",
                    "event_title": "Event 2",
                    "contract_id": "c_2",
                    "contract_title": "Contract 2",
                    "ticker": "KXEVENT-2",
                    "yes_bid": 0.49,
                    "yes_ask": 0.53,
                    "no_bid": 0.47,
                    "no_ask": 0.51,
                    "yes_price": 0.51,
                    "no_price": 0.49,
                    "implied_probability": 0.51,
                    "volume": 10,
                    "open_interest": 20,
                    "liquidity_score": 0.10,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "provider_id": "kalshi_prediction_market",
                    "market_id": "m_3",
                    "event_id": "e_3",
                    "event_title": "Event 3",
                    "contract_id": "c_3",
                    "contract_title": "Contract 3",
                    "ticker": "KXEVENT-3",
                    "yes_price": 0.52,
                    "no_price": 0.48,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                },
                {
                    "provider_id": "kalshi_prediction_market",
                    "market_id": "m_4",
                    "event_id": "e_4",
                    "event_title": "Event 4",
                    "contract_id": "c_4",
                    "contract_title": "Contract 4",
                    "ticker": "KXEVENT-4",
                    "yes_price": 0.55,
                    "no_price": 0.45,
                    "close_time": (now - timedelta(minutes=1)).isoformat(),
                    "status": "settled",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "provider_id": "kalshi_prediction_market",
                    "market_id": "m_5",
                    "event_id": "e_5",
                    "event_title": "Event 5",
                    "contract_id": "c_5",
                    "contract_title": "Contract 5",
                    "ticker": "KXEVENT-5",
                    "yes_price": None,
                    "no_price": None,
                    "yes_bid": 0.40,
                    "yes_ask": 0.42,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
            ],
            "timestamp": now.isoformat(),
        }
        with patch.dict(
            "os.environ",
            {
                "SHARP_PROVIDER_ENABLED": "true",
                "SHARP_LIVE_READS_ENABLED": "true",
                "SHARP_API_KEY": "sharp_test_key_123",
                "KALSHI_PROVIDER_ENABLED": "true",
                "KALSHI_LIVE_READS_ENABLED": "true",
                "KALSHI_API_KEY": "kalshi_test_key_123",
                "KALSHI_API_SECRET": "placeholder",
            },
            clear=False,
        ):
            with patch(
                "automation_scheduler.scheduler_runner._collect_provider_placeholders",
                return_value={
                    "snapshots": [],
                    "skipped": [],
                    "health": {},
                    "sharp_snapshot": mock_sharp_snapshot.return_value,
                    "kalshi_snapshot": mock_kalshi_snapshot.return_value,
                },
            ):
                with TemporaryDirectory() as tmp:
                    result = run_scheduler_once(base_data_dir=tmp, dry_run=True)
                    queue = get_scheduler_review_queue(base_data_dir=tmp)
                    kalshi_items = [item for item in queue["items"] if item.get("provider_id") == "kalshi_prediction_market"]

                    self.assertEqual(result["kalshi_records_received"], 5)
                    self.assertEqual(result["kalshi_records_valid"], 3)
                    self.assertEqual(result["kalshi_records_rejected"], 2)
                    self.assertEqual(result["kalshi_rejected_reason_counts"]["stale_market"], 1)
                    self.assertEqual(result["kalshi_rejected_reason_counts"]["closed_or_settled_market"], 1)
                    self.assertEqual(result["kalshi_flagged_low_liquidity_count"], 1)
                    self.assertEqual(result["kalshi_flagged_partial_pricing_count"], 1)
                    self.assertEqual(result["kalshi_liquidity_tier_counts"]["very_low_liquidity"], 1)
                    self.assertEqual(result["kalshi_missing_liquidity_count"], 1)
                    self.assertGreaterEqual(result["kalshi_candidates_created"], 3)
                    self.assertGreaterEqual(result["review_queue_items_written"], 3)
                    self.assertEqual(result["review_queue_storage_backend"], "file")
                    self.assertEqual(len(kalshi_items), 3)
                    self.assertEqual(queue["summary"]["kalshi_candidate_count"], 3)
                    self.assertEqual(queue["summary"]["prediction_market_count"], 3)
                    self.assertEqual(queue["summary"]["review_only_count"], 3)
                    self.assertEqual(queue["summary"]["execution_allowed_count"], 0)
                    self.assertEqual(queue["summary"]["flagged_low_liquidity_count"], 1)
                    self.assertEqual(queue["summary"]["low_liquidity_count"], 1)
                    self.assertEqual(queue["summary"]["missing_liquidity_count"], 1)
                    self.assertIn("liquidity_tier_counts", queue["summary"])
                    self.assertIn("average_review_priority_score", queue["summary"])
                    self.assertEqual(queue["summary"]["flagged_partial_pricing_count"], 1)
                    self.assertEqual(queue["summary"]["total_count"], 3)
                    self.assertEqual(queue["items"][0]["provider_id"], "kalshi_prediction_market")
                    self.assertEqual(queue["storage_backend"], "file")
                    self.assertTrue(queue["queue_read_ok"])
                    self.assertTrue(all(item.get("review_priority_score") is not None for item in kalshi_items))
                    self.assertTrue(all(item.get("liquidity_policy_version") == "kalshi_liquidity_policy_v2" for item in kalshi_items))
                    self.assertTrue(all(item.get("recommendation_status") == "review_only" for item in kalshi_items))
                    self.assertTrue(all(item.get("execution_allowed") is False for item in kalshi_items))
                    self.assertTrue(all(item.get("auto_execution_enabled") is False for item in kalshi_items))
                    paper_decisions = load_paper_decisions(tmp)
                    self.assertEqual(len(paper_decisions), queue["summary"]["total_count"])
                    self.assertTrue(all(decision["paper_only"] for decision in paper_decisions))
                    self.assertTrue(all(decision["execution_allowed"] is False for decision in paper_decisions))
                    self.assertTrue(all(decision.get("review_priority_score") is not None for decision in paper_decisions))

    @patch("automation_scheduler.scheduler_runner.monitor_kalshi_market")
    @patch("automation_scheduler.scheduler_runner._evaluate_kalshi_review_candidates")
    @patch("automation_scheduler.scheduler_runner._evaluate_sharp_review_candidates")
    @patch("automation_scheduler.scheduler_runner._collect_provider_placeholders")
    def test_run_once_persists_paper_decisions_for_sharp_and_kalshi_review_items(
        self,
        mock_collect,
        mock_sharp_eval,
        mock_kalshi_eval,
        mock_monitor,
    ):
        mock_collect.return_value = {
            "sharp_snapshot": {"records": []},
            "kalshi_snapshot": {"records": []},
            "skipped": [],
            "health": [],
            "snapshots": [],
        }
        mock_sharp_eval.return_value = {
            "records_received": 1,
            "records_valid": 1,
            "records_rejected": 0,
            "candidates": [
                {
                    "source": "test",
                    "provider_id": "sharp_sportsbook",
                    "provider": "sharp_sportsbook",
                    "source_type": "sportsbook",
                    "market_type": "sports_pregame_main",
                    "sport_or_symbol": "MLB",
                    "event_id": "evt-sharp",
                    "event_name": "Sharp Event",
                    "market": "moneyline",
                    "selection": "Team A",
                    "implied_probability": 0.52,
                    "opportunity_score": 60,
                    "reason_codes": ["watch"],
                    "recommendation_status": "review_only",
                    "execution_allowed": False,
                }
            ],
            "blockers": [],
        }
        mock_kalshi_eval.return_value = {
            "records_received": 1,
            "records_valid": 1,
            "records_rejected": 0,
            "candidates": [
                {
                    "source": "test",
                    "provider_id": "kalshi_prediction_market",
                    "provider": "kalshi_prediction_market",
                    "source_type": "prediction_market",
                    "market_type": "prediction_market",
                    "sport_or_symbol": "prediction_market",
                    "market": "KX",
                    "selection": "Contract",
                    "ticker": "KX",
                    "contract_id": "KX",
                    "yes_price": 0.55,
                    "price_source": "direct_price",
                    "implied_probability": 0.55,
                    "liquidity_tier": "low_liquidity",
                    "liquidity_score": 40,
                    "review_priority_score": 62,
                    "opportunity_score": 62,
                    "reason_codes": ["prediction_market_review_only"],
                    "recommendation_status": "review_only",
                    "execution_allowed": False,
                    "human_approval_required": True,
                }
            ],
            "rejected_reason_counts": {},
            "flagged_low_liquidity_count": 1,
            "flagged_partial_pricing_count": 0,
            "price_field_telemetry": {"liquidity_tier_counts": {"low_liquidity": 1}, "records_missing_liquidity": 0},
            "blockers": [],
        }
        mock_monitor.return_value = {"candidates": []}
        with TemporaryDirectory() as tmp:
            result = run_scheduler_once(base_data_dir=tmp, dry_run=True)
            decisions = load_paper_decisions(tmp)
            providers = {decision["provider"] for decision in decisions}
            self.assertEqual(result["review_queue_items_written"], 2)
            self.assertEqual(result["paper_decisions_written"], 2)
            self.assertEqual(result["paper_ledger_storage_backend"], "file")
            self.assertEqual(providers, {"sharp_sportsbook", "kalshi_prediction_market"})
            self.assertEqual(result["calibration"]["status"], "insufficient_data")

    @patch("src.services.odds_runtime_bridge.SharpSportsbookAdapter.fetch_snapshot")
    @patch("src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.validate_config")
    @patch("src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.fetch_snapshot")
    def test_kalshi_field_shape_variants_and_telemetry(self, mock_kalshi_snapshot, mock_kalshi_validate_config, mock_sharp_snapshot):
        now = datetime.now(timezone.utc)
        mock_kalshi_validate_config.return_value = {
            "ok": True,
            "status": "ready",
            "blockers": [],
            "credential_status": "ok",
            "live_reads_enabled": True,
            "provider_enabled": True,
            "live_calls_enabled": True,
            "provider_live_calls_enabled": True,
            "dry_run": True,
            "read_only_mode": True,
        }
        mock_sharp_snapshot.return_value = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "sharp_sportsbook",
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "records": [],
            "schema_version": "automation_scheduler.v1.sharp_sportsbook.v1",
            "timestamp": now.isoformat(),
        }
        mock_kalshi_snapshot.return_value = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "kalshi_prediction_market",
            "records_received": 5,
            "records_valid": 5,
            "records_rejected": 0,
            "schema_version": "automation_scheduler.v1.kalshi_prediction_market.v1",
            "records": [
                {
                    "contractId": "c_direct",
                    "marketTicker": "KX-DIRECT",
                    "yes_price": "55",
                    "no_price": "45",
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "contract_id": "c_camel",
                    "ticker": "KX-CAMEL",
                    "yesBid": "0.47",
                    "yesAsk": "0.53",
                    "noBid": "0.47",
                    "noAsk": "0.53",
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "contract_id": "c_alias",
                    "market_ticker": "KX-ALIAS",
                    "bid_yes": 0.45,
                    "ask_yes": 0.47,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "contractId": "c_nested",
                    "eventTicker": "KX-NESTED",
                    "pricing": {"yes_bid": 0.40, "yes_ask": 0.42, "no_bid": 0.58, "no_ask": 0.60},
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
                {
                    "contract_id": "c_missing",
                    "ticker": "KX-MISSING",
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "settlement_rule": "official_results",
                    "timestamp": now.isoformat(),
                },
            ],
            "timestamp": now.isoformat(),
        }
        with patch.dict(
            "os.environ",
            {
                "SHARP_PROVIDER_ENABLED": "true",
                "SHARP_LIVE_READS_ENABLED": "true",
                "SHARP_API_KEY": "sharp_test_key_123",
                "KALSHI_PROVIDER_ENABLED": "true",
                "KALSHI_LIVE_READS_ENABLED": "true",
                "KALSHI_API_KEY": "kalshi_test_key_123",
                "KALSHI_API_SECRET": "placeholder",
            },
            clear=False,
        ):
            with patch(
                "automation_scheduler.scheduler_runner._collect_provider_placeholders",
                return_value={
                    "snapshots": [],
                    "skipped": [],
                    "health": {},
                    "sharp_snapshot": mock_sharp_snapshot.return_value,
                    "kalshi_snapshot": mock_kalshi_snapshot.return_value,
                },
            ):
                with TemporaryDirectory() as tmp:
                    result = run_scheduler_once(base_data_dir=tmp, dry_run=True)
                    self.assertEqual(result["kalshi_records_received"], 5)
                    self.assertGreaterEqual(result["kalshi_records_valid"], 4)
                    self.assertLess(result["kalshi_records_rejected"], result["kalshi_records_received"])
                    self.assertEqual(result["kalshi_rejected_reason_counts"].get("missing_prices", 0), 1)
                    self.assertGreater(result["kalshi_candidates_created"], 0)
                    telemetry = result["kalshi_price_field_telemetry"]
                    self.assertEqual(telemetry["total_kalshi_records_seen"], 5)
                    self.assertGreaterEqual(telemetry["records_with_any_price_signal"], 4)
                    self.assertGreaterEqual(telemetry["records_with_direct_yes_price"], 1)
                    self.assertGreaterEqual(telemetry["records_with_bid_ask_midpoint_possible"], 2)
                    self.assertIn("yes_price", telemetry["first_record_safe_field_names"])
                    self.assertIn("liquidity_threshold_used", telemetry)
                    self.assertIn("records_flagged_low_liquidity", telemetry)
                    self.assertEqual(telemetry["liquidity_policy_version"], "kalshi_liquidity_policy_v2")
                    self.assertIn("liquidity_source_counts", telemetry)
                    self.assertIn("liquidity_tier_counts", telemetry)

    @patch("src.services.odds_runtime_bridge.SharpSportsbookAdapter.fetch_snapshot")
    @patch("src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.validate_config")
    @patch("src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.fetch_snapshot")
    def test_kalshi_low_liquidity_diagnostics_distinguish_missing_vs_threshold(self, mock_kalshi_snapshot, mock_kalshi_validate_config, mock_sharp_snapshot):
        now = datetime.now(timezone.utc)
        mock_kalshi_validate_config.return_value = {
            "ok": True,
            "status": "ready",
            "blockers": [],
            "credential_status": "ok",
            "live_reads_enabled": True,
            "provider_enabled": True,
            "live_calls_enabled": True,
            "provider_live_calls_enabled": True,
            "dry_run": True,
            "read_only_mode": True,
        }
        mock_sharp_snapshot.return_value = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "sharp_sportsbook",
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "records": [],
            "timestamp": now.isoformat(),
        }
        mock_kalshi_snapshot.return_value = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "kalshi_prediction_market",
            "records_received": 3,
            "records_valid": 3,
            "records_rejected": 0,
            "records": [
                {
                    "contract_id": "c_ok",
                    "ticker": "KX-OK",
                    "yes_price": 0.51,
                    "no_price": 0.49,
                    "yes_bid": 0.50,
                    "yes_ask": 0.52,
                    "no_bid": 0.48,
                    "no_ask": 0.50,
                    "volume": 5000,
                    "open_interest": 4000,
                    "liquidity_score": 0.95,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "timestamp": now.isoformat(),
                    "source_payload_redacted": {"volume_fp": 5000, "open_interest_fp": 4000, "yes_bid_dollars": 0.50, "yes_ask_dollars": 0.52, "no_bid_dollars": 0.48, "no_ask_dollars": 0.50, "last_price_dollars": 0.51},
                },
                {
                    "contract_id": "c_threshold",
                    "ticker": "KX-THRESH",
                    "yes_price": 0.40,
                    "no_price": 0.60,
                    "yes_bid": 0.39,
                    "yes_ask": 0.41,
                    "no_bid": 0.59,
                    "no_ask": 0.61,
                    "volume": 0,
                    "open_interest": 0,
                    "liquidity_score": 0.9,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "timestamp": now.isoformat(),
                    "source_payload_redacted": {"volume_fp": 0, "open_interest_fp": 0, "yes_bid_dollars": 0.39, "yes_ask_dollars": 0.41, "no_bid_dollars": 0.59, "no_ask_dollars": 0.61, "last_price_dollars": 0.40},
                },
                {
                    "contract_id": "c_missing",
                    "ticker": "KX-MISS",
                    "yes_price": 0.45,
                    "no_price": 0.55,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "timestamp": now.isoformat(),
                    "source_payload_redacted": {"yes_bid_dollars": 0.44, "yes_ask_dollars": 0.46, "no_bid_dollars": 0.54, "no_ask_dollars": 0.56, "last_price_dollars": 0.45},
                },
            ],
            "timestamp": now.isoformat(),
        }
        with patch.dict(
            "os.environ",
            {
                "SHARP_PROVIDER_ENABLED": "true",
                "SHARP_LIVE_READS_ENABLED": "true",
                "SHARP_API_KEY": "sharp_test_key_123",
                "KALSHI_PROVIDER_ENABLED": "true",
                "KALSHI_LIVE_READS_ENABLED": "true",
                "KALSHI_API_KEY": "kalshi_test_key_123",
                "KALSHI_API_SECRET": "placeholder",
            },
            clear=False,
        ):
            with patch(
                "automation_scheduler.scheduler_runner._collect_provider_placeholders",
                return_value={
                    "snapshots": [],
                    "skipped": [],
                    "health": {},
                    "sharp_snapshot": mock_sharp_snapshot.return_value,
                    "kalshi_snapshot": mock_kalshi_snapshot.return_value,
                },
            ):
                with TemporaryDirectory() as tmp:
                    result = run_scheduler_once(base_data_dir=tmp, dry_run=True)
                    telemetry = result["kalshi_price_field_telemetry"]
                    self.assertEqual(telemetry["records_flagged_low_liquidity"], 1)
                    self.assertEqual(telemetry["records_low_liquidity_due_to_threshold"], 1)
                    self.assertEqual(telemetry["records_low_liquidity_due_to_missing_liquidity"], 1)
                    self.assertEqual(telemetry["records_missing_liquidity"], 1)
                    self.assertEqual(telemetry["records_with_volume"], 1)
                    self.assertEqual(telemetry["records_with_open_interest"], 1)
                    self.assertEqual(telemetry["records_with_liquidity"], 2)
