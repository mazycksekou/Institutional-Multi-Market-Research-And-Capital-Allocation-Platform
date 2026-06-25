from __future__ import annotations

import inspect
import unittest

from automation_scheduler.cross_asset_embedding_router import route_cross_asset_embedding
from automation_scheduler.manifold_review_queue import build_manifold_review_queue
from automation_scheduler.market_state_graph import infer_graph_asset_type
from automation_scheduler.prediction_market_manifold_mapper import map_prediction_market
from src.market_intelligence import build_market_intelligence_report


class TestPhase10K8ZL6MarketIntelligenceRuntimeTestRedirection(unittest.TestCase):
    def test_wrappers_import_canonical_modules(self):
        modules = [
            "automation_scheduler.cross_asset_embedding_router",
            "automation_scheduler.manifold_review_queue",
            "automation_scheduler.market_state_graph",
            "automation_scheduler.prediction_market_manifold_mapper",
        ]
        for module_name in modules:
            module = __import__(module_name, fromlist=["*"])
            source = inspect.getsource(module)
            self.assertIn("src.market_intelligence", source)

    def test_runtime_wrappers_still_work(self):
        self.assertEqual(route_cross_asset_embedding({"asset_type": "stock", "price": 10})["status"], "cross_asset_embedding_routed")
        self.assertEqual(build_manifold_review_queue([], persist=False)["status"], "manifold_review_complete")
        self.assertEqual(map_prediction_market({"yes_price": 0.54})["status"], "prediction_market_map_complete")
        self.assertEqual(infer_graph_asset_type({"asset_type": "prediction_market"}), "prediction_market")

    def test_canonical_builder_still_imports_safely(self):
        report = build_market_intelligence_report({"market": "sports", "confidence": 50})
        self.assertEqual(report["market"], "sports")
        self.assertFalse(report.get("provider_write", False))

