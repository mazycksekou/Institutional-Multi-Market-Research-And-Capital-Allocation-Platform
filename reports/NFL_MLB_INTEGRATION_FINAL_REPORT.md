# NFL + MLB Integration Final Report

1. final_verdict: COMPLETE_WITH_POLICY_BLOCKED_SOURCES
2. integration_branch: finish-mlb-completely
3. integration_commit_hash: 018a388dbadabe7429158b7f8e4a65717e8b7773
4. nfl_commit_hash: 7fdf533d0b685dd2d312c489f2aa8b0db94eb4a6
5. mlb_commit_hash: 018a388dbadabe7429158b7f8e4a65717e8b7773
6. nfl_final_status: COMPLETE
7. mlb_final_status: COMPLETE_WITH_POLICY_BLOCKED_SOURCES
8. total_nfl_records: 6461599
9. total_mlb_records: 2233
10. combined_total_records: 6463832
11. oxylabs_residential_proxy_status: {"allow_oxylabs_required": true, "allow_paid_retrieval_required": true, "allowlist_required": true, "blocklist_enforced": true, "disabled_by_default": true, "no_raw_html": true, "no_raw_payloads": true, "no_secret_logging": true, "present": true}
12. oxylabs_web_scraper_api_status: {"allow_oxylabs_required": true, "allow_paid_retrieval_required": true, "allowlist_required": true, "blocklist_enforced": true, "disabled_by_default": true, "no_raw_html": true, "no_raw_payloads": true, "no_secret_logging": true, "present": true}
13. safety_invariant_status: {"actual_bets_submitted": 0, "actual_crypto_swaps_submitted": 0, "actual_orders_submitted": 0, "actual_trades_submitted": 0, "auto_execution_enabled": false, "broker_order_execution_enabled": false, "crypto_trade_execution_enabled": false, "enabled_source_count": 0, "execution_allowed": false, "execution_allowed_count": 0, "kalshi_order_execution_enabled": false, "live_execution_enabled": false, "paid_source_enabled_count": 0, "provider_write": false, "raw_html_persisted": false, "raw_payload_included": false, "raw_screenshot_persisted": false, "secrets_included": false, "sportsbook_bet_execution_enabled": false, "stock_trade_execution_enabled": false}
14. secret_scan_status: {"checked_patterns": ["Authorization:", "Basic auth", "OXYLABS credentials markers", "cookie/session/token markers"], "findings": [], "marker_references": ["docs/OXYLABS_RETRIEVAL_LAYER.md", "tests/test_oxylabs_residential_proxy_adapter.py", "tests/test_oxylabs_web_scraper_api_adapter.py", "automation_scheduler/paid_retrieval_sources.py", "automation_scheduler/oxylabs_residential_proxy_adapter.py", "automation_scheduler/oxylabs_web_scraper_api_adapter.py"], "notes": ["Manual repository scan found marker references only; no committed secret values were found."], "status": "clean"}
15. raw_payload_scan_status: {"checked_patterns": ["raw html", "raw screenshot", "raw payload", ".env tracked", "payload/screenshot/html file names"], "findings": [], "name_scan_hits": [".env.example", "automation_scheduler/arbitrage/draw_market_arbitrage.py", "automation_scheduler/drawdown_controls.py", "automation_scheduler/provider_payload_validator.py", "screenshot_intake.py", "scripts/check_live_payload_contract.ps1", "scripts/live_payloads.ps1", "tests/test_arbitrage_draw_market.py", "tests/test_drawdown_controls.py", "tests/test_live_smoke_payload_contract.py", "tests/test_provider_payload_validator.py", "tests/test_screenshot_analysis.py", "tests/test_screenshot_normalization_parity.py"], "notes": ["Tracked files with payload/screenshot/html-like names were code/tests/docs utilities only; no raw HTML, raw screenshot, or raw provider payload artifacts were found."], "status": "clean"}
16. tests_run: 8
17. tests_passed: 8
18. shared_files_touched: automation_scheduler/derived_feature_backfill_report.py, automation_scheduler/retrieval_policy.py, automation_scheduler/paid_retrieval_sources.py, automation_scheduler/oxylabs_residential_proxy_adapter.py, automation_scheduler/oxylabs_web_scraper_api_adapter.py, docs/OXYLABS_RETRIEVAL_LAYER.md, tests/test_automation_scheduler_scripts.py, tests/test_oxylabs_residential_proxy_adapter.py, tests/test_oxylabs_web_scraper_api_adapter.py, scripts/test_oxylabs_residential_proxy.ps1, scripts/test_oxylabs_web_scraper_api.ps1
19. merge_conflicts_resolved: none
20. remaining_manual_actions: none

## Sport Summaries
- NFL blocked sources: blocked_ftn_charting, blocked_pfr_reference, nflverse, official_nfl_staff_or_news_pages, official_team_press_releases, official_team_staff_pages, open_github_coaching_dataset, research, team_sitemaps
- MLB blocked sources: market_odds_blocked, official_public_web, statcast_public_data
- NFL research sources: manual_csv_import, wikidata_coaching_seed, wikidata_entity_api, wikidata_local_dump, wikipedia_coaching_seed, wikipedia_coaching_tables
- MLB research sources: lahman_database, manual_csv_import, mlb_stats_api, wikidata_wikipedia_seed
