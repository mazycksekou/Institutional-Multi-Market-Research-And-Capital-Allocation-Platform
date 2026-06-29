from __future__ import annotations

import inspect
import unittest

from src.services.streamlit_dashboard_facade import route_cross_asset_embedding
from src.services.streamlit_dashboard_facade import build_manifold_review_queue
from src.services.streamlit_dashboard_facade import infer_graph_asset_type
from src.services.streamlit_dashboard_facade import map_prediction_market
from src.market_intelligence import build_market_intelligence_report


class TestPhase10K8ZL6MarketIntelligenceRuntimeTestRedirection(unittest.TestCase):
    def test_wrappers_import_canonical_modules(self):
        modules = [
            'src.automation_scheduler_legacy.cross_asset_embedding_router',
            'src.automation_scheduler_legacy.manifold_review_queue',
            'src.automation_scheduler_legacy.market_state_graph',
            'src.automation_scheduler_legacy.prediction_market_manifold_mapper',
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

