# Phase 9 Ledger / Review Response Path Patch

Generated: 2026-06-12T15:23:12

## Search Matches

| File | Line | Text |
|---|---:|---|
| `src\api\automation_deepseek_routes.py` | 37 | `review_queue_summary=payload.review_queue_summary,` |
| `src\api\automation_deepseek_routes.py` | 63 | `review_queue_summary=payload.review_queue_summary,` |
| `src\api\automation_review_outcomes_routes.py` | 24 | `compact_review_queue_response_dep: Any,` |
| `src\api\automation_review_outcomes_routes.py` | 39 | `compact_review_queue_response = compact_review_queue_response_dep` |
| `src\api\automation_review_outcomes_routes.py` | 44 | `async def get_automation_scheduler_review_queue(` |
| `src\api\automation_review_outcomes_routes.py` | 52 | `queue = automation_scheduler.get_scheduler_review_queue(` |
| `src\api\automation_review_outcomes_routes.py` | 59 | `compact = compact_review_queue_response(queue, limit=cap)` |
| `src\api\automation_small_account_routes.py` | 22 | `compact_pattern_review_queue_response_dep: Any,` |
| `src\api\automation_small_account_routes.py` | 37 | `compact_pattern_review_queue_response = compact_pattern_review_queue_response_dep` |
| `src\api\automation_small_account_routes.py` | 68 | `async def get_small_account_pattern_review_queue_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):` |
| `src\api\automation_small_account_routes.py` | 70 | `payload = automation_scheduler.get_small_account_pattern_review_queue(limit=cap)` |
| `src\api\automation_small_account_routes.py` | 71 | `compact = compact_pattern_review_queue_response(payload, limit=cap)` |
| `src\api\schemas\automation.py` | 87 | `review_queue_summary: dict[str, Any] = Field(default_factory=dict)` |
| `src\api\schemas\automation.py` | 107 | `review_queue_summary: dict[str, Any] = Field(default_factory=dict)` |
| `tests\test_automation_scheduler_endpoints.py` | 22 | `def test_review_queue_endpoint_compact_default(self):` |
| `tests\test_data_intelligence_stack.py` | 49 | `"affects_review_queue",` |
| `tests\test_data_intelligence_stack.py` | 63 | `def test_research_only_models_cannot_affect_review_queue_or_execution(self):` |
| `tests\test_data_intelligence_stack.py` | 68 | `self.assertFalse(model["affects_review_queue"])` |
| `tests\test_data_intelligence_stack.py` | 154 | `self.assertFalse(lane["affects_review_queue"])` |
| `tests\test_data_intelligence_stack.py` | 181 | `self.assertFalse(routed["affects_review_queue"])` |
| `tests\test_data_paths.py` | 15 | `get_paper_ledger_dir,` |
| `tests\test_data_paths.py` | 16 | `get_review_queue_dir,` |
| `tests\test_data_paths.py` | 40 | `get_review_queue_dir(): "review_queue",` |
| `tests\test_data_paths.py` | 41 | `get_paper_ledger_dir(): "paper_ledger",` |
| `tests\test_deepseek_data_pull_check_contract.py` | 254 | `{"_source_record_type": "review_queue", "market_type": "prediction_market", "ticker": "KX2", "yes_bid": 0.98},` |
| `tests\test_deepseek_profit_lab.py` | 277 | `summaries={"review_queue_summary": {"total_count": 0}, "disagreement_summary": {"count": 0}},` |
| `tests\test_ev_line_shopper.py` | 12 | `from automation_scheduler.review_queue import build_review_item, upsert_review_item` |
| `tests\test_ev_line_shopper.py` | 36 | `def test_review_queue_stores_ev_fields(self):` |
| `tests\test_extreme_randomness_diagnostics.py` | 207 | `self.assertEqual(strategy["review_queue_effect"], "downgrade_only")` |
| `tests\test_institutional_cross_asset_adapters.py` | 129 | `(root / "review_queue").mkdir()` |
| `tests\test_institutional_cross_asset_adapters.py` | 130 | `(root / "review_queue" / "latest.json").write_text(` |
| `tests\test_institutional_cross_asset_lab.py` | 13 | `(root / "review_queue").mkdir(parents=True, exist_ok=True)` |
| `tests\test_institutional_cross_asset_lab.py` | 15 | `(root / "paper_ledger").mkdir(parents=True, exist_ok=True)` |
| `tests\test_institutional_cross_asset_lab.py` | 50 | `(root / "review_queue" / "latest.json").write_text(json.dumps(review), encoding="utf-8")` |
| `tests\test_institutional_cross_asset_lab.py` | 57 | `before_review = (root / "review_queue" / "latest.json").read_text(encoding="utf-8")` |
| `tests\test_institutional_cross_asset_lab.py` | 67 | `after_review = (root / "review_queue" / "latest.json").read_text(encoding="utf-8")` |
| `tests\test_institutional_model_router.py` | 4 | `from automation_scheduler.review_queue import build_review_item` |
| `tests\test_institutional_model_router.py` | 52 | `def test_review_queue_fields_are_gated_by_activation_and_relevance(self):` |
| `tests\test_institutional_model_router.py` | 66 | `promoted["activation_status"] = "review_queue_ready"` |
| `tests\test_model_router.py` | 6 | `r = route_model_candidate(market_type='sportsbook', sport_or_asset_class='sportsbook', model_type='allocation_model', time_horizon='same_day', available_inputs={}, activation_tier='review_queue_ready', risk_gate_result=True, data_quality_result=True, settlement_gate_result=True, human_approval_required=True)` |
| `tests\test_model_router_registry.py` | 12 | `activation_tier="review_queue_ready",` |
| `tests\test_model_router_registry.py` | 22 | `activation_tier="review_queue_ready",` |
| `tests\test_model_router_registry.py` | 32 | `activation_tier="review_queue_ready",` |
| `tests\test_nfl_historical_pattern_lab.py` | 305 | `self.assertFalse(report["paper_ledger_written"])` |
| `tests\test_nfl_historical_pattern_lab.py` | 310 | `self.assertFalse((Path(tmp) / "paper_ledger").exists())` |
| `tests\test_nfl_historical_pattern_validation.py` | 314 | `self.assertFalse(report["paper_ledger_written"])` |
| `tests\test_nfl_open_data_backfill.py` | 101 | `def test_no_outcome_paper_ledger_or_calibration_writes_in_module(self):` |
| `tests\test_nfl_open_data_backfill.py` | 103 | `self.assertNotIn("get_paper_ledger_dir", source)` |
| `tests\test_nfl_open_data_backfill.py` | 107 | `self.assertNotIn("paper_ledger", source)` |
| `tests\test_nfl_open_data_backfill.py` | 218 | `self.assertNotIn("paper_ledger", source)` |
| `tests\test_outcome_migration.py` | 245 | `self.assertEqual(report["paper_ledger_records_count"], 1)` |
| `tests\test_outcome_reconciliation.py` | 90 | `self.assertEqual(result["recommendation"], "fix_paper_ledger_matching_before_import")` |
| `tests\test_paper_trade_ledger.py` | 6 | `load_paper_ledger,` |
| `tests\test_paper_trade_ledger.py` | 8 | `summarize_paper_ledger,` |
| `tests\test_paper_trade_ledger.py` | 63 | `summary = summarize_paper_ledger(base_dir=tmp)` |
| `tests\test_paper_trade_ledger.py` | 81 | `ledger = load_paper_ledger(base_dir=tmp)` |
| `tests\test_pattern_review_queue.py` | 4 | `from automation_scheduler.pattern_review_queue import (` |
| `tests\test_pattern_review_queue.py` | 6 | `load_pattern_review_queue,` |
| `tests\test_pattern_review_queue.py` | 7 | `persist_pattern_review_queue,` |
| `tests\test_pattern_review_queue.py` | 115 | `persist_pattern_review_queue([item], base_data_dir=tmp)` |
| `tests\test_pattern_review_queue.py` | 116 | `loaded = load_pattern_review_queue(base_data_dir=tmp)` |
| `tests\test_response_compactor.py` | 20 | `compact_health_response, compact_review_queue_response, compact_run_once_response,` |
| `tests\test_response_compactor.py` | 31 | `"review_queue_count": 20,` |
| `tests\test_response_compactor.py` | 34 | `"review_queue_storage_backend": "file",` |
| `tests\test_response_compactor.py` | 35 | `"review_queue_latest_run_id": "run-1",` |
| `tests\test_response_compactor.py` | 36 | `"review_queue_read_ok": True,` |
| `tests\test_response_compactor.py` | 58 | `self.assertEqual(c["review_queue_storage_backend"], "file")` |
| `tests\test_response_compactor.py` | 59 | `self.assertEqual(c["review_queue_latest_run_id"], "run-1")` |
| `tests\test_response_compactor.py` | 60 | `self.assertTrue(c["review_queue_read_ok"])` |
| `tests\test_response_compactor.py` | 221 | `c = compact_review_queue_response(p, limit=10)` |
| `tests\test_response_compactor.py` | 268 | `def test_review_queue_compact_includes_kalshi_summary_and_review_only_execution_safety(self):` |
| `tests\test_response_compactor.py` | 296 | `"queue_read_path": "review_queue/latest.json",` |
| `tests\test_response_compactor.py` | 337 | `c = compact_review_queue_response(payload, limit=10)` |
| `tests\test_response_compactor.py` | 370 | `"review_queue_items_written": 2,` |
| `tests\test_response_compactor.py` | 371 | `"review_queue_storage_backend": "file",` |
| `tests\test_response_compactor.py` | 372 | `"review_queue_write_path": "review_queue/latest.json",` |
| `tests\test_response_compactor.py` | 373 | `"review_queue_latest_run_id": "run-2",` |
| `tests\test_response_compactor.py` | 380 | `"paper_ledger_storage_backend": "file",` |
| `tests\test_response_compactor.py` | 381 | `"paper_ledger_write_path": "paper_ledger/latest.json",` |
| `tests\test_response_compactor.py` | 382 | `"paper_ledger_latest_run_id": "run-2",` |
| `tests\test_response_compactor.py` | 391 | `self.assertEqual(c["review_queue_items_written"], 2)` |
| `tests\test_response_compactor.py` | 392 | `self.assertEqual(c["review_queue_storage_backend"], "file")` |
| `tests\test_response_compactor.py` | 394 | `self.assertEqual(c["paper_ledger_storage_backend"], "file")` |
| `tests\test_review_queue.py` | 7 | `from automation_scheduler import get_scheduler_review_queue` |
| `tests\test_review_queue.py` | 8 | `from automation_scheduler.review_queue import (` |
| `tests\test_review_queue.py` | 12 | `load_review_queue_state,` |
| `tests\test_review_queue.py` | 13 | `persist_review_queue_snapshot,` |
| `tests\test_review_queue.py` | 42 | `self.assertIn("review_queue_gate_result", saved)` |
| `tests\test_review_queue.py` | 47 | `queue_path = Path(config["paths"]["review_queue"]) / "review_queue.json"` |
| `tests\test_review_queue.py` | 103 | `meta = persist_review_queue_snapshot(config, items, run_id="run-123", summary={"total_count": 2})` |
| `tests\test_review_queue.py` | 104 | `state = load_review_queue_state(config)` |
| `tests\test_review_queue.py` | 117 | `state = load_review_queue_state(config)` |
| `tests\test_review_queue.py` | 126 | `queue_dir = Path(config["paths"]["review_queue"])` |
| `tests\test_review_queue.py` | 129 | `(queue_dir / "review_queue.json").write_text("{still-not-json", encoding="utf-8")` |
| `tests\test_review_queue.py` | 130 | `state = load_review_queue_state(config)` |
| `tests\test_review_queue.py` | 136 | `def test_get_scheduler_review_queue_reads_persisted_items_and_filters(self):` |
| `tests\test_review_queue.py` | 139 | `persist_review_queue_snapshot(` |
| `tests\test_review_queue.py` | 178 | `all_items = get_scheduler_review_queue(base_data_dir=tmp, limit=10)` |
| `tests\test_review_queue.py` | 192 | `kalshi_only = get_scheduler_review_queue(base_data_dir=tmp, provider="kalshi_prediction_market", limit=10)` |
| `tests\test_review_queue.py` | 195 | `prediction_only = get_scheduler_review_queue(base_data_dir=tmp, market_type="prediction_market", limit=10)` |
| `tests\test_review_queue_gate.py` | 2 | `from model_governance.review_queue_gate import evaluate_review_queue_gate` |
| `tests\test_review_queue_gate.py` | 6 | `r = evaluate_review_queue_gate(activation_tier='paper_trade_ready', evidence_score=90, input_quality_score=90, model_risk_rating='low', stale_data=False, settlement_mismatch=False)` |
| `tests\test_review_queue_gate.py` | 7 | `self.assertFalse(r['can_enter_review_queue'])` |
| `tests\test_scheduler_runner.py` | 6 | `from automation_scheduler import get_scheduler_review_queue` |
| `tests\test_scheduler_runner.py` | 19 | `self.assertEqual(result["review_queue_storage_backend"], "file")` |
| `tests\test_scheduler_runner.py` | 20 | `self.assertIn("review_queue_items_written", result)` |
| `tests\test_scheduler_runner.py` | 21 | `self.assertIn("review_queue_write_path", result)` |
| `tests\test_scheduler_runner.py` | 28 | `def test_kalshi_candidates_flow_to_review_queue_with_safety_flags(self, mock_kalshi_snapshot, mock_sharp_snapshot):` |
| `tests\test_scheduler_runner.py` | 161 | `queue = get_scheduler_review_queue(base_data_dir=tmp)` |
| `tests\test_scheduler_runner.py` | 174 | `self.assertGreaterEqual(result["review_queue_items_written"], 3)` |
| `tests\test_scheduler_runner.py` | 175 | `self.assertEqual(result["review_queue_storage_backend"], "file")` |
| `tests\test_scheduler_runner.py` | 187 | `limited_queue = get_scheduler_review_queue(base_data_dir=tmp, limit=1)` |
| `tests\test_scheduler_runner.py` | 287 | `self.assertEqual(result["review_queue_items_written"], 2)` |
| `tests\test_scheduler_runner.py` | 289 | `self.assertEqual(result["paper_ledger_storage_backend"], "file")` |
| `tests\test_sharp_cross_book_review_queue.py` | 7 | `from automation_scheduler import get_scheduler_review_queue` |
| `tests\test_sharp_cross_book_review_queue.py` | 8 | `from automation_scheduler.response_compactor import compact_review_queue_response` |
| `tests\test_sharp_cross_book_review_queue.py` | 74 | `queue_payload = get_scheduler_review_queue(base_data_dir=tmp)` |
| `tests\test_sharp_cross_book_review_queue.py` | 75 | `compact = compact_review_queue_response(queue_payload)` |
| `tests\test_sharp_scheduler_flow.py` | 7 | `from automation_scheduler import get_scheduler_review_queue` |
| `tests\test_sharp_scheduler_flow.py` | 102 | `queue = get_scheduler_review_queue(base_data_dir=tmp)` |
| `tests\test_small_account_endpoints.py` | 95 | `self.assertGreaterEqual(payload["review_queue_count"], 1)` |

## Files Changed
- `tests\test_response_compactor.py`

PATCH_APPLIED: `True`
