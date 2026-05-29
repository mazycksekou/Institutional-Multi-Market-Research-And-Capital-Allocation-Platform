import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

from automation_scheduler import get_scheduler_review_queue
from automation_scheduler.scheduler_runner import run_scheduler_once


class TestSchedulerRunner(unittest.TestCase):
    def test_dry_run_only(self):
        with TemporaryDirectory() as tmp:
            result = run_scheduler_once(base_data_dir=tmp, dry_run=True, injected_data={"skipped_items": ["a"]})
            self.assertTrue(result["dry_run"])
            self.assertFalse(result["auto_execution_enabled"])
            self.assertIn("report_path", result)
            self.assertIn("records_received", result)
            skipped = [row for row in result.get("skipped_items", []) if isinstance(row, dict)]
            kalshi_skips = [row for row in skipped if row.get("provider_id") == "kalshi_prediction_market"]
            self.assertTrue(kalshi_skips)

    @patch("automation_scheduler.scheduler_runner.SharpSportsbookAdapter.fetch_snapshot")
    @patch("automation_scheduler.scheduler_runner.KalshiReadonlyAdapter.fetch_snapshot")
    def test_kalshi_candidates_flow_to_review_queue_with_safety_flags(self, mock_kalshi_snapshot, mock_sharp_snapshot):
        now = datetime.now(timezone.utc)
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
            with TemporaryDirectory() as tmp:
                result = run_scheduler_once(base_data_dir=tmp, dry_run=True)
                queue = get_scheduler_review_queue(base_data_dir=tmp)
                kalshi_items = [item for item in queue["items"] if item.get("provider_id") == "kalshi_prediction_market"]

                self.assertEqual(result["kalshi_records_received"], 5)
                self.assertEqual(result["kalshi_records_valid"], 3)
                self.assertEqual(result["kalshi_records_rejected"], 2)
                self.assertEqual(result["kalshi_rejected_reason_counts"]["stale_market"], 1)
                self.assertEqual(result["kalshi_rejected_reason_counts"]["closed_or_settled_market"], 1)
                self.assertEqual(result["kalshi_flagged_low_liquidity_count"], 2)
                self.assertEqual(result["kalshi_flagged_partial_pricing_count"], 1)
                self.assertGreaterEqual(result["kalshi_candidates_created"], 3)
                self.assertEqual(len(kalshi_items), 3)
                self.assertEqual(queue["summary"]["kalshi_candidate_count"], 3)
                self.assertEqual(queue["summary"]["prediction_market_count"], 3)
                self.assertEqual(queue["summary"]["review_only_count"], 3)
                self.assertEqual(queue["summary"]["execution_allowed_count"], 0)
                self.assertEqual(queue["summary"]["flagged_low_liquidity_count"], 2)
                self.assertEqual(queue["summary"]["flagged_partial_pricing_count"], 1)
                self.assertTrue(all(item.get("recommendation_status") == "review_only" for item in kalshi_items))
                self.assertTrue(all(item.get("execution_allowed") is False for item in kalshi_items))
                self.assertTrue(all(item.get("auto_execution_enabled") is False for item in kalshi_items))

    @patch("automation_scheduler.scheduler_runner.SharpSportsbookAdapter.fetch_snapshot")
    @patch("automation_scheduler.scheduler_runner.KalshiReadonlyAdapter.fetch_snapshot")
    def test_kalshi_field_shape_variants_and_telemetry(self, mock_kalshi_snapshot, mock_sharp_snapshot):
        now = datetime.now(timezone.utc)
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
