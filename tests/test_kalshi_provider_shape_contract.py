import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.services.streamlit_dashboard_facade import run_scheduler_once
from src.market_intelligence.response_compactor import compact_run_once_response


class TestKalshiProviderShapeContract(unittest.TestCase):
    @patch('src.services.scheduler_runner.SharpSportsbookAdapter.fetch_snapshot')
    @patch('src.services.scheduler_runner.KalshiReadonlyAdapter.fetch_snapshot')
    def test_dollar_shape_fields_are_scheduler_usable_and_missing_prices_not_triggered(self, mock_kalshi_snapshot, mock_sharp_snapshot):
        now = datetime.now(timezone.utc)
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
                    "contract_id": "c_1",
                    "ticker": "KX-1",
                    "yes_price": 0.52,
                    "no_price": 0.48,
                    "yes_bid": 0.51,
                    "yes_ask": 0.53,
                    "no_bid": 0.47,
                    "no_ask": 0.49,
                    "implied_probability": 0.52,
                    "volume": 1200,
                    "open_interest": 900,
                    "liquidity_score": 0.95,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "timestamp": now.isoformat(),
                    "source_payload_redacted": {
                        "ticker": "KX-1",
                        "yes_bid_dollars": 0.51,
                        "yes_ask_dollars": 0.53,
                        "no_bid_dollars": 0.47,
                        "no_ask_dollars": 0.49,
                        "last_price_dollars": 0.52,
                        "open_interest_fp": 900,
                        "volume_fp": 1200,
                    },
                },
                {
                    "contract_id": None,
                    "market_ticker": "KX-2",
                    "yes_bid": 0.40,
                    "yes_ask": 0.44,
                    "no_bid": 0.56,
                    "no_ask": 0.60,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "timestamp": now.isoformat(),
                    "source_payload_redacted": {
                        "market_ticker": "KX-2",
                        "yes_bid_dollars": 0.40,
                        "yes_ask_dollars": 0.44,
                        "no_bid_dollars": 0.56,
                        "no_ask_dollars": 0.60,
                        "last_price_dollars": 0.42,
                        "open_interest_fp": 0,
                        "volume_fp": 0,
                    },
                },
                {
                    "contract_id": None,
                    "marketTicker": "KX-3",
                    "yes_bid": 0.33,
                    "yes_ask": 0.37,
                    "close_time": (now + timedelta(hours=2)).isoformat(),
                    "status": "open",
                    "timestamp": now.isoformat(),
                    "source_payload_redacted": {
                        "marketTicker": "KX-3",
                        "yes_bid_dollars": 0.33,
                        "yes_ask_dollars": 0.37,
                        "no_bid_dollars": 0.63,
                        "no_ask_dollars": 0.67,
                        "last_price_dollars": 0.35,
                        "open_interest_fp": 0,
                        "volume_fp": 0,
                    },
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
                self.assertEqual(result["kalshi_records_received"], 3)
                self.assertEqual(result["kalshi_records_valid"], 3)
                self.assertEqual(result["kalshi_records_rejected"], 0)
                self.assertEqual(result["kalshi_rejected_reason_counts"].get("missing_prices", 0), 0)
                self.assertEqual(result["kalshi_candidates_created"], 3)
                telemetry = result["kalshi_price_field_telemetry"]
                self.assertEqual(telemetry["missing_expected_source_fields"], [])
                self.assertEqual(telemetry["records_with_any_price_signal"], 3)
                self.assertGreaterEqual(telemetry["records_with_bid_ask_midpoint_possible"], 2)

    def test_compact_run_once_response_does_not_expose_raw_payload(self):
        compact = compact_run_once_response(
            {
                "ok": True,
                "status": "dry_run_complete",
                "run_id": "r1",
                "kalshi_price_field_telemetry": {
                    "accepted_source_field_names": ["yes_bid_dollars"],
                    "missing_expected_source_fields": [],
                },
                "provider_payload": {"should_not": "appear"},
                "raw_payload": {"should_not": "appear"},
                "kalshi_records_received": 1,
                "kalshi_records_valid": 1,
            }
        )
        rendered = str(compact)
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("raw_payload", rendered)
        self.assertEqual(compact["kalshi_price_field_telemetry"]["accepted_source_field_names"], ["yes_bid_dollars"])
