import json
import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from automation_scheduler.review_queue import build_review_item, list_active_review_items, upsert_review_item
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestReviewQueue(unittest.TestCase):
    def test_threshold_buckets_and_human_approval(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            candidate = {
                "source": "odds_line_monitor",
                "provider": "sportsbooks",
                "market_type": "sports_pregame_main",
                "sport_or_symbol": "NBA",
                "market": "moneyline",
                "selection": "Team A",
                "field_scores": {"edge_score": 8, "confidence_score": 8, "liquidity_score": 7, "movement_score": 8, "data_quality_score": 8, "market_depth_score": 7, "timing_score": 8, "model_fit_score": 7, "risk_score": 7, "volatility_score": 6, "source_consensus_score": 7, "execution_feasibility_score": 7, "expected_roi_score": 8},
                "opportunity_score": 86,
                "confidence": 0.8,
                "risk": 0.2,
                "liquidity": 0.7,
            }
            item = build_review_item(candidate, config)
            saved = upsert_review_item(config, item)
            self.assertEqual(saved["recommended_action"], "urgent_review")
            self.assertTrue(saved["human_approval_required"])
            self.assertIn("governance_status", saved)
            self.assertIn("review_queue_gate_result", saved)

    def test_stale_and_market_closed_items_drop_out(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            queue_path = config["paths"]["review_queue"] + "\\review_queue.json"
            stale_item = {
                "schema_version": config["schema_version"],
                "id": "item1",
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "updated_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "source": "scheduler",
                "market_type": "news_events",
                "sport_or_symbol": "AAPL",
                "market": "headline",
                "selection": "earnings",
                "odds_or_price": None,
                "movement": {},
                "field_scores": {},
                "opportunity_score": 80,
                "confidence": 0.7,
                "risk": 0.2,
                "liquidity": 0.3,
                "recommended_action": "review_required",
                "recheck_after_seconds": 300,
                "stale_after_seconds": 60,
                "human_approval_required": True,
                "auto_execution_enabled": False,
                "reason": "",
                "blockers": [],
                "provider": "news_provider",
                "market_close_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "status": "active",
            }
            with open(queue_path, "w", encoding="utf-8") as handle:
                json.dump([stale_item], handle)
            self.assertEqual(list_active_review_items(config), [])
