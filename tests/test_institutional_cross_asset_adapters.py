import json
import tempfile
import unittest
from pathlib import Path

from src.services.streamlit_dashboard_facade import normalize_major_asset_record, normalize_prediction_market_record, normalize_sportsbook_record, normalize_stock_record, read_existing_outputs


class TestInstitutionalCrossAssetAdapters(unittest.TestCase):
    def test_maps_kalshi_record_and_preserves_existing_scores(self):
        record = normalize_prediction_market_record(
            {
                "id": "review-1",
                "provider_id": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "contract_id": "KXTEST",
                "ticker": "KXTEST",
                "yes_bid": 0.40,
                "yes_ask": 0.42,
                "yes_price": 0.41,
                "volume": 1000,
                "open_interest": 1200,
                "liquidity_score": 88.0,
                "pricing_quality_score": 97.0,
                "risk_score": 12.0,
                "review_priority_score": 76.0,
                "created_at": "2026-05-30T12:00:00+00:00",
            }
        )
        self.assertEqual(record["asset_class"], "prediction_market")
        self.assertEqual(record["provider"], "kalshi_prediction_market")
        self.assertEqual(record["liquidity_score"], 88.0)
        self.assertEqual(record["pricing_quality_score"], 97.0)
        self.assertFalse(record["execution_allowed"])
        self.assertNotIn("provider_payload", str(record))

    def test_price_never_creates_outcome(self):
        record = normalize_prediction_market_record(
            {
                "id": "review-1",
                "provider_id": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "contract_id": "KXTEST",
                "yes_bid": 0.99,
                "yes_ask": 1.0,
                "status": "closed",
                "created_at": "2026-05-30T12:00:00+00:00",
            }
        )
        self.assertEqual(record["outcome_status"], "pending")
        self.assertIsNone(record["final_outcome"])

    def test_stock_record_distinguishes_financial_quality_from_trading_liquidity(self):
        strong = normalize_stock_record(
            {
                "symbol": "ABC",
                "observed_price": 100,
                "bid": 99.95,
                "ask": 100.05,
                "volume": 1000000,
                "dollar_volume": 100000000,
                "quick_ratio": 2.0,
                "current_ratio": 2.5,
                "debt_to_cash": 0.4,
                "observed_at": "2026-05-30T12:00:00+00:00",
            }
        )
        weak = normalize_stock_record(
            {
                "symbol": "XYZ",
                "observed_price": 10,
                "bid": 9.5,
                "ask": 10.5,
                "volume": 100,
                "quick_ratio": 0.3,
                "current_ratio": 0.5,
                "debt_to_cash": 5,
                "observed_at": "2026-05-30T12:00:00+00:00",
            }
        )
        self.assertGreater(strong["financial_quality_score"], weak["financial_quality_score"])
        self.assertGreater(strong["liquidity_score"], weak["liquidity_score"])
        self.assertFalse(strong["execution_allowed"])

    def test_sportsbook_record_maps_without_bet_path(self):
        record = normalize_sportsbook_record(
            {
                "id": "sports-1",
                "provider_id": "sharp_sportsbook",
                "market_type": "spread",
                "selection": "Team A -3.5",
                "best_odds": -110,
                "books_compared": 1,
                "created_at": "2026-05-30T12:00:00+00:00",
            }
        )
        self.assertEqual(record["asset_class"], "sportsbook")
        self.assertFalse(record["execution_allowed"])
        self.assertIn("low_book_count", record["reason_codes"])

    def test_major_asset_hooks_require_explicit_final_price_for_return(self):
        record = normalize_major_asset_record(
            {
                "asset_class": "bond",
                "symbol": "TLT",
                "observed_price": 90,
                "bid": 89.99,
                "ask": 90.01,
                "duration": 16,
                "risk_flags": ["duration_risk"],
                "observed_at": "2026-05-30T12:00:00+00:00",
            },
            asset_class="bond",
        )
        self.assertEqual(record["asset_class"], "bond")
        self.assertIsNone(record["final_price"])
        self.assertIsNone(record["return_pct"])
        self.assertFalse(record["execution_allowed"])

    def test_read_existing_outputs_handles_missing_optional_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_queue").mkdir()
            (root / "review_queue" / "latest.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "review-1",
                                "provider_id": "kalshi_prediction_market",
                                "market_type": "prediction_market",
                                "contract_id": "KXTEST",
                                "yes_bid": 0.4,
                                "yes_ask": 0.42,
                                "created_at": "2026-05-30T12:00:00+00:00",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out = read_existing_outputs(base_data_dir=tmp, asset_classes=["prediction_market", "stock", "sportsbook"])
        self.assertEqual(out["source_counts"]["prediction_market"], 1)
        self.assertEqual(out["source_counts"]["sportsbook"], 0)
        self.assertEqual(out["unavailable"]["stock"], "no_stock_sidecar_outputs_found")


if __name__ == "__main__":
    unittest.main()
