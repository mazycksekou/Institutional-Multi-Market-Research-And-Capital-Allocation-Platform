# Phase 8B Run Once Exact Payload Report

Generated: 2026-06-12T15:16:50

- HEAD: `f7e2cd9`
- Git clean at start: `True`

## Safety Environment
- PAPER_TRADING: `1`
- DRY_RUN: `1`
- DISABLE_LIVE_BETS: `1`
- ACTION_API_KEY: `SET`
- ODDS_API_KEY: `MISSING`
- THE_ODDS_API_KEY: `MISSING`
- DEEPSEEK_API_KEY: `MISSING`

## Route Signature
- endpoint: `run_automation_scheduler_once`
- signature: `(payload: 'AutomationRunOnceRequest', verbose: 'bool' = Query(False), include_debug: 'bool' = Query(False), limit: 'int' = Query(10))`

## Body Model
- body model: `None detected`

## Exact Payload Attempted
```json
{}
```

## Run Once Response
- status_code: `200`
- ok: `True`
- error: `None`
- detail: `None`
- keys: `['auto_execution_enabled', 'blockers', 'calibration_coverage_rate', 'calibration_settled_count', 'calibration_status', 'candidates_created', 'dry_run', 'human_approval_required', 'kalshi_average_review_priority_score', 'kalshi_blockers', 'kalshi_candidates_created', 'kalshi_flagged_low_liquidity_count', 'kalshi_flagged_partial_pricing_count', 'kalshi_high_priority_count', 'kalshi_liquidity_tier_counts', 'kalshi_missing_liquidity_count', 'kalshi_price_field_telemetry', 'kalshi_records_received', 'kalshi_records_rejected', 'kalshi_records_valid', 'kalshi_rejected_reason_counts', 'kalshi_watch_items_created', 'ok', 'paper_decisions_count', 'paper_decisions_written', 'paper_ledger_latest_run_id', 'paper_ledger_storage_backend', 'paper_ledger_write_path', 'records_received', 'records_rejected', 'records_valid', 'report_id', 'report_path', 'review_queue_items_written', 'review_queue_last_updated_at', 'review_queue_latest_run_id', 'review_queue_storage_backend', 'review_queue_write_path', 'review_required_count', 'run_id', 'sharp_blockers', 'sharp_candidates_created', 'sharp_records_received', 'sharp_records_rejected', 'sharp_records_valid', 'status', 'watch_recheck_count']`
```json
{
  "auto_execution_enabled": false,
  "blockers": [],
  "calibration_coverage_rate": 0.0,
  "calibration_settled_count": 0,
  "calibration_status": "insufficient_data",
  "candidates_created": 100,
  "dry_run": true,
  "human_approval_required": true,
  "kalshi_average_review_priority_score": 59.2252,
  "kalshi_blockers": [],
  "kalshi_candidates_created": 100,
  "kalshi_flagged_low_liquidity_count": 100,
  "kalshi_flagged_partial_pricing_count": 0,
  "kalshi_high_priority_count": 0,
  "kalshi_liquidity_tier_counts": {
    "low_liquidity": 99,
    "very_low_liquidity": 1
  },
  "kalshi_missing_liquidity_count": 0,
  "kalshi_price_field_telemetry": {
    "accepted_source_field_names": [
      "last_price_dollars",
      "no_ask_dollars",
      "no_bid_dollars",
      "open_interest_fp",
      "volume_fp",
      "yes_ask_dollars",
      "yes_bid_dollars"
    ],
    "first_record_safe_field_names": [
      "contract_id",
      "no_ask",
      "no_bid",
      "no_price",
      "ticker",
      "yes_ask",
      "yes_bid",
      "yes_price"
    ],
    "liquidity_policy_version": "kalshi_liquidity_policy_v2",
    "liquidity_signal_field_count": 3,
    "liquidity_source_counts": {
      "volume_open_interest_proxy": 100
    },
    "liquidity_threshold_used": {
      "low": 45.0,
      "moderate": 70.0,
      "very_low": 20.0
    },
    "liquidity_tier_counts": {
      "low_liquidity": 99,
      "very_low_liquidity": 1
    },
    "missing_expected_source_fields": [],
    "nested_pricing_object_presence_counts": {
      "market": 0,
      "prices": 0,
      "pricing": 0
    },
    "pricing_signal_field_count": 5,
    "records_flagged_low_liquidity": 100,
    "records_low_liquidity_due_to_missing_liquidity": 0,
    "records_low_liquidity_due_to_status": 0,
    "records_low_liquidity_due_to_threshold": 100,
    "records_missing_all_price_signals": 0,
    "records_missing_liquidity": 0,
    "records_with_any_price_signal": 100,
    "records_with_bid_ask_midpoint_possible": 100,
    "records_with_direct_liquidity": 100,
    "records_with_direct_no_price": 100,
    "records_with_direct_yes_price": 100,
    "records_with_liquidity": 100,
    "records_with_liquidity_proxy": 100,
    "records_with_no_ask": 100,
    "records_with_no_bid": 100,
    "records_with_open_interest": 0,
    "records_with_volume": 0,
    "records_with_yes_ask": 100,
    "records_with_yes_bid": 100,
    "source_payload_field_presence_counts": {
      "best_ask_no": 0,
      "best_ask_yes": 0,
      "best_bid_no": 0,
      "best_bid_yes": 0,
      "lastPriceNo": 0,
      "lastPriceYes": 0,
      "last_price_dollars": 100,
      "last_price_no": 0,
      "last_price_yes": 0,
      "liquidity_dollars": 100,
      "no": 0,
      "noAsk": 0,
      "noBid": 0,
      "noPrice": 0,
      "no_ask": 0,
      "no_ask_dollars": 100,
      "no_bid": 0,
      "no_bid_dollars": 100,
      "no_price": 0,
      "open_interest": 0,
      "open_interest_fp": 100,
      "priceNo": 0,
      "priceYes": 0,
      "price_no": 0,
      "price_yes": 0,
      "volume": 0,
      "volume_fp": 100,
      "yes": 0,
      "yesAsk": 0,
      "yesBid": 0,
      "yesPrice": 0,
      "yes_ask": 0,
      "yes_ask_dollars": 100,
      "yes_bid": 0,
      "yes_bid_dollars": 100,
      "yes_price": 0
    },
    "source_payload_first_record_safe_field_names": [
      "can_close_early",
      "close_time",
      "created_time",
      "custom_strike",
      "event_ticker",
      "expected_expiration_time",
      "expiration_time",
      "expiration_value",
      "fractional_trading_enabled",
      "is_provisional",
      "last_price_dollars",
      "latest_expiration_time",
      "liquidity_dollars",
      "market_type",
      "mve_collection_ticker",
      "mve_selected_legs",
      "no_ask_dollars",
      "no_bid_dollars",
      "no_sub_title",
      "notional_value_dollars",
      "open_interest_fp",
      "open_time",
      "previous_price_dollars",
      "previous_yes_ask_dollars",
      "previous_yes_bid_dollars",
      "price_level_structure",
      "price_ranges",
      "response_price_units",
      "result",
      "rules_primary",
      "rules_secondary",
      "settlement_timer_seconds",
      "status",
      "strike_type",
      "ticker",
      "title",
      "updated_time",
      "volume_24h_fp",
      "volume_fp",
      "yes_ask_dollars",
      "yes_ask_size_fp",
      "yes_bid_dollars",
      "yes_bid_size_fp",
      "yes_sub_title"
    ],
    "source_payload_nested_object_presence_counts": {
      "market": 0,
      "prices": 0,
      "pricing": 0
    },
    "top_level_field_presence_counts": {
      "askNo": 0,
      "askYes": 0,
      "ask_no": 0,
      "ask_yes": 0,
      "bidNo": 0,
      "bidYes": 0,
      "bid_no": 0,
      "bid_yes": 0,
      "contractId": 0,
      "contract_id": 100,
      "eventTicker": 0,
      "event_ticker": 0,
      "market": 0,
      "marketTicker": 0,
      "market_ticker": 0,
      "no": 0,
      "noAsk": 0,
      "noAskPrice": 0,
      "noBid": 0,
      "noBidPrice": 0,
      "noLastPrice": 0,
      "noPrice": 0,
      "no_ask": 100,
      "no_ask_price": 0,
      "no_bid": 100,
      "no_bid_price": 0,
      "no_last_price": 0,
      "no_price": 100,
      "priceNo": 0,
      "priceYes": 0,
      "price_no": 0,
      "price_yes": 0,
      "prices": 0,
      "pricing": 0,
      "ticker": 100,
      "yes": 0,
      "yesAsk": 0,
      "yesAskPrice": 0,
      "yesBid": 0,
      "yesBidPrice": 0,
      "yesLastPrice": 0,
      "yesPrice": 0,
      "yes_ask": 100,
      "yes_ask_price": 0,
      "yes_bid": 100,
      "yes_bid_price": 0,
      "yes_last_price": 0,
      "yes_price": 100
    },
    "total_kalshi_records_seen": 100,
    "unexpected_source_field_count": 37
  },
  "kalshi_records_received": 100,
  "kalshi_records_rejected": 0,
  "kalshi_records_valid": 100,
  "kalshi_rejected_reason_counts": {},
  "kalshi_watch_items_created": 100,
  "ok": true,
  "paper_decisions_count": 700,
  "paper_decisions_written": 300,
  "paper_ledger_latest_run_id": "run_25533c9ec51a",
  "paper_ledger_storage_backend": "file",
  "paper_ledger_write_path": "paper_ledger/latest.json",
  "records_received": 100,
  "records_rejected": 0,
  "records_valid": 100,
  "report_id": "run_25533c9ec51a",
  "report_path": "C:\\Users\\user\\betting-stock-api-code-integration\\betting stock api code intergration\\data\\reports\\scheduler_run_run_25533c9ec51a.json",
  "review_queue_items_written": 300,
  "review_queue_last_updated_at": "2026-06-12T19:17:02.017664+00:00",
  "review_queue_latest_run_id": "run_25533c9ec51a",
  "review_queue_storage_backend": "file",
  "review_queue_write_path": "review_queue/latest.json",
  "review_required_count": 0,
  "run_id": "run_25533c9ec51a",
  "sharp_blockers": [],
  "sharp_candidates_created": 0,
  "sharp_records_received": 0,
  "sharp_records_rejected": 0,
  "sharp_records_valid": 0,
  "status": "dry_run_complete",
  "watch_recheck_count": 100
}
```

## Phase 8B Result
OVERALL_OK: `True`
Run-once accepted the exact schema payload in dry-run/paper-safe mode.
