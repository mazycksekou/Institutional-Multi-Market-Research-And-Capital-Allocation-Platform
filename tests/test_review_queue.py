import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from automation_scheduler import get_scheduler_review_queue
from automation_scheduler.review_queue import (
    build_review_item,
    filter_review_items,
    list_active_review_items,
    load_review_queue_state,
    persist_review_queue_snapshot,
    summarize_review_items,
    upsert_review_item,
)
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
            queue_path = Path(config["paths"]["review_queue"]) / "review_queue.json"
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
            with queue_path.open("w", encoding="utf-8") as handle:
                json.dump([stale_item], handle)
            self.assertEqual(list_active_review_items(config), [])

    def test_filter_and_summary(self):
        items = [
            {"provider_id": "kalshi_prediction_market", "market_type": "prediction_market", "recommendation_status": "review_only", "execution_allowed": False, "low_liquidity": True, "partial_pricing": True, "reason_codes": ["partial_pricing"], "liquidity_tier": "low_liquidity", "review_priority_score": 72},
            {"provider_id": "sharp_sportsbook", "market_type": "sports_pregame_main", "recommendation_status": "review_only", "execution_allowed": False, "low_liquidity": False, "partial_pricing": False, "reason_codes": ["watch"], "review_priority_score": 50},
        ]
        only_kalshi = filter_review_items(items, provider="kalshi_prediction_market")
        self.assertEqual(len(only_kalshi), 1)
        summary = summarize_review_items(items, rejected_reason_counts={"missing_prices": 2})
        self.assertEqual(summary["kalshi_candidate_count"], 1)
        self.assertEqual(summary["flagged_partial_pricing_count"], 1)
        self.assertEqual(summary["low_liquidity_count"], 1)
        self.assertEqual(summary["liquidity_tier_counts"]["low_liquidity"], 1)
        self.assertEqual(summary["high_priority_count"], 1)
        self.assertGreater(summary["average_review_priority_score"], 0)
        self.assertEqual(summary["rejected_reason_counts"]["missing_prices"], 2)

    def test_persisted_queue_roundtrip_and_metadata(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            items = [
                {"id": "k1", "provider_id": "kalshi_prediction_market", "market_type": "prediction_market", "execution_allowed": False},
                {"id": "s1", "provider_id": "sharp_sportsbook", "market_type": "sports_pregame_main", "execution_allowed": False},
            ]
            meta = persist_review_queue_snapshot(config, items, run_id="run-123", summary={"total_count": 2})
            state = load_review_queue_state(config)
            self.assertEqual(meta["storage_backend"], "file")
            self.assertEqual(state["storage_backend"], "file")
            self.assertTrue(state["queue_read_ok"])
            self.assertEqual(state["latest_run_id"], "run-123")
            self.assertEqual(state["items_read_count"], 2)
            self.assertEqual(len(state["items"]), 2)
            self.assertTrue(str(state["queue_read_path"]).endswith("latest.json"))
            self.assertNotIn(":", str(meta["queue_write_path"]))

    def test_missing_queue_storage_returns_safe_empty(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            state = load_review_queue_state(config)
            self.assertEqual(state["items"], [])
            self.assertEqual(state["items_read_count"], 0)
            self.assertTrue(state["queue_read_ok"])
            self.assertEqual(state["storage_backend"], "file")

    def test_malformed_queue_storage_is_safe(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            queue_dir = Path(config["paths"]["review_queue"])
            queue_dir.mkdir(parents=True, exist_ok=True)
            (queue_dir / "latest.json").write_text("{not-json", encoding="utf-8")
            (queue_dir / "review_queue.json").write_text("{still-not-json", encoding="utf-8")
            state = load_review_queue_state(config)
            self.assertEqual(state["items"], [])
            self.assertEqual(state["items_read_count"], 0)
            self.assertFalse(state["queue_read_ok"])
            self.assertEqual(state["queue_error_category"], "malformed_queue_storage_files")

    def test_get_scheduler_review_queue_reads_persisted_items_and_filters(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            persist_review_queue_snapshot(
                config,
                [
                    {
                        "id": "kalshi-1",
                        "provider_id": "kalshi_prediction_market",
                        "market_type": "prediction_market",
                        "recommendation_status": "review_only",
                        "execution_allowed": False,
                        "low_liquidity": True,
                        "missing_liquidity": False,
                        "liquidity_policy_version": "kalshi_liquidity_policy_v2",
                        "liquidity_source": "volume_open_interest_proxy",
                        "liquidity_tier": "low_liquidity",
                        "liquidity_score": 30,
                        "spread_score": 95,
                        "pricing_quality_score": 100,
                        "risk_score": 42,
                        "confidence_score": 65,
                        "review_priority_score": 72,
                        "partial_pricing": True,
                        "reason_codes": ["partial_pricing"],
                        "provider_payload": {"raw": "omit"},
                        "api_key": "secret",
                    },
                    {
                        "id": "sharp-1",
                        "provider_id": "sharp_sportsbook",
                        "market_type": "sports_pregame_main",
                        "recommendation_status": "review_only",
                        "execution_allowed": False,
                        "low_liquidity": False,
                        "partial_pricing": False,
                        "reason_codes": ["watch"],
                    },
                ],
                run_id="run-queue",
                summary={"total_count": 2},
            )
            all_items = get_scheduler_review_queue(base_data_dir=tmp, limit=10)
            self.assertEqual(all_items["summary"]["total_count"], 2)
            self.assertEqual(all_items["summary"]["kalshi_candidate_count"], 1)
            self.assertEqual(all_items["summary"]["sharp_candidate_count"], 1)
            self.assertEqual(all_items["summary"]["review_only_count"], 2)
            self.assertEqual(all_items["summary"]["execution_allowed_count"], 0)
            self.assertEqual(all_items["summary"]["low_liquidity_count"], 1)
            self.assertEqual(all_items["summary"]["missing_liquidity_count"], 0)
            self.assertEqual(all_items["summary"]["liquidity_tier_counts"]["low_liquidity"], 1)
            self.assertEqual(all_items["summary"]["high_priority_count"], 1)
            self.assertEqual(all_items["storage_backend"], "file")
            self.assertTrue(all_items["queue_read_ok"])
            self.assertEqual(all_items["items"][0]["liquidity_policy_version"], "kalshi_liquidity_policy_v2")
            self.assertEqual(all_items["items"][0]["review_priority_score"], 72)
            kalshi_only = get_scheduler_review_queue(base_data_dir=tmp, provider="kalshi_prediction_market", limit=10)
            self.assertEqual(kalshi_only["summary"]["total_count"], 1)
            self.assertEqual(kalshi_only["summary"]["kalshi_candidate_count"], 1)
            prediction_only = get_scheduler_review_queue(base_data_dir=tmp, market_type="prediction_market", limit=10)
            self.assertEqual(prediction_only["summary"]["total_count"], 1)
            self.assertEqual(prediction_only["summary"]["prediction_market_count"], 1)
            rendered = str(all_items["items"])
            self.assertNotIn("provider_payload", rendered)
            self.assertNotIn("secret", rendered)
