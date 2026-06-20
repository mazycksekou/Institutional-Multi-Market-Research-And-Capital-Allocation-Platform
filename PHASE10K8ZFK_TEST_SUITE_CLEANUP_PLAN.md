# PHASE10K8ZFK Test Suite Cleanup Plan

## Executive Summary
10K8ZFK is a planning/report phase only. No tests deleted, no tests moved, no tests rewritten, no coverage removed, and no xfail or skip added to hide failures. current gates preserved. behavior unchanged.

The current gates are preserved. This plan classifies the test suite so future cleanup can happen safely before AI integration and before ML integration.

This phase does not authorize deletion.

## Current HEAD
Current HEAD: `777a7bf07500af362877a44894481834abc9b123` (`777a7bf docs: plan provider live market decomposition`).

Inventory snapshot at planning time:
- total test files: 353
- total test functions: 693
- phase-report tests: 73 across the phase families, including 54 active 10K8-family files at inventory time
- storage / R2 / archive tests: 6
- Streamlit / dashboard-data tests: 5
- API route tests: 5 endpoint-focused files
- provider tests: 23
- automation_scheduler tests: 7
- model / backtest tests: 67
- risk / metrics / math tests: 18
- smoke / test wrapper coverage: 4
- tests importing streamlit: 2
- tests importing pandas: 5
- tests importing pyarrow: 0
- tests that may use network primitives: 17
- tests referencing `.env` or credential-like names: 46

## Purpose
Create a professional test-suite cleanup plan before future code migration and before AI/ML integration.

## Scope
This report classifies the current test suite, identifies current critical gates, and defines cleanup waves without changing test behavior.

## Non-Goals
- no tests deleted
- no tests moved
- no tests rewritten
- no coverage removed
- no xfail or skip added to hide failures
- no source behavior changed
- no file deletion
- no file moves
- no public functions removed
- no AI integration
- no ML training
- no backtest runner
- no controlled data loader
- no external API calls
- no live connectors
- no broker execution
- no real trade execution
- no scraper actions
- no credentials committed
- no secrets printed

## Relationship to 10K8ZFF
10K8ZFF defined the canonical ownership map. This cleanup plan maps tests to those future owners so later migrations can keep coverage aligned.

## Relationship to 10K8ZFI
10K8ZFI decomposed `automation_scheduler/`. This plan keeps scheduler-related tests aligned with the same lanes and preserves the current gates.

## Relationship to 10K8ZFJ
10K8ZFJ decomposed provider and live-market-intelligence surfaces. This plan keeps provider tests on a no-network path and defers any cleanup until fake-client coverage is stable.

## Test Inventory
### Top 20 Largest Test Files
| file | lines |
| --- | ---: |
| `tests/test_streamlit_dashboard_data.py` | 1607 |
| `tests/test_response_compactor.py` | 834 |
| `tests/test_tennis_impact_intelligence.py` | 737 |
| `tests/test_sport_analysis_endpoint.py` | 674 |
| `tests/test_golf_impact_intelligence.py` | 673 |
| `tests/test_soccer_impact_intelligence.py` | 653 |
| `tests/test_baseball_impact_intelligence.py` | 642 |
| `tests/test_tennis_model_activation.py` | 639 |
| `tests/test_automation_scheduler_endpoints.py` | 593 |
| `tests/test_hockey_impact_intelligence.py` | 563 |
| `tests/test_open_sports_history_backfill.py` | 520 |
| `tests/test_football_impact_intelligence.py` | 518 |
| `tests/test_open_sports_history_import.py` | 508 |
| `tests/test_sport_model_routing.py` | 508 |
| `tests/test_phase10k8zf7_r2_archive_pipeline.py` | 507 |
| `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py` | 505 |
| `tests/test_multi_sport_model_registry.py` | 487 |
| `tests/test_deepseek_data_pull_check_contract.py` | 486 |
| `tests/test_scheduler_runner.py` | 484 |
| `tests/test_combat_impact_intelligence.py` | 458 |

### Risk Signals In The Suite
- tests importing streamlit: `tests/test_phase10k2_sports_snapshot_pipeline.py`, `tests/test_phase10k8zf0a_frozen_test_contract_reset.py`
- tests importing pandas: `tests/test_phase10k3_runtime_csv_migration_plan.py`, `tests/test_phase10k8w_full_0dte_paper_pipeline_ui.py`, `tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py`, `tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py`, `tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py`
- tests importing pyarrow: none found
- tests that may use network primitives: `tests/test_advanced_red_team.py`, `tests/test_data_source_endpoints.py`, `tests/test_deepseek_reviewer.py`, `tests/test_institutional_deepseek_review.py`, `tests/test_live_smoke_payload_contract.py`, `tests/test_kalshi_readonly_adapter.py`, `tests/test_ncaaf_collegefootballdata_adapter.py`, `tests/test_nfl_open_data_backfill.py`, `tests/test_nfl_open_data_adapters.py`, `tests/test_ops_workflow.py`, `tests/test_open_sports_history_import.py`, `tests/test_open_sports_history_backfill.py`, `tests/test_phase10k2_sports_snapshot_pipeline.py`, `tests/test_security_framework.py`, `tests/test_screenshot_analysis.py`, `tests/test_deepseek_profit_lab.py`, `tests/test_sharp_sportsbook_adapter.py`
- tests referencing `.env` or credential-like names: 46 files

## Test Classification Method
The test suite is classified by the role of the test file, the runtime surface it touches, and the cleanup risk it creates.

| test file | primary category | secondary category if any | imports high-risk dependency yes/no | external call risk | fixture/fake-client coverage yes/no/unknown | current gate importance | duplicate/stale risk | cleanup priority | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/test_phase10k8*.py`, `tests/test_phase10k7*.py`, `tests/test_phase10k6*.py`, `tests/test_phase10k5*.py`, `tests/test_phase10k4*.py`, `tests/test_phase10k3*.py`, `tests/test_phase10k2*.py` | phase-report tests | smoke gate snapshots | no | none | yes | critical | low | P0 | keep for now as migration guardrails; consolidate only after phase freeze |
| `tests/test_phase10k8zf7_r2_archive_pipeline.py`, `tests/test_phase10k8zf8_r2_transfer_proof_report.py`, `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py`, `tests/test_phase10k8zf9c_headerless_csv_final_deletion.py`, `tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py`, `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py` | storage / R2 / archive tests | daily hygiene | no | none | yes | critical | low | P0 | keep critical; keep fake clients only and no network |
| `tests/test_streamlit_dashboard_data.py`, `tests/test_line_movement_data_quality_dashboard.py`, `tests/test_phase10k6b_dashboard_navigation_plan_contract.py`, `tests/test_phase10k6k_controlled_dashboard_shell_review.py`, `tests/test_phase10k8zc_dashboard_product_lane_cleanup.py` | Streamlit / dashboard-data tests | product-language checks | yes | none | unknown | high | medium | P1 | split oversized coverage later; keep text-only checks and avoid importing streamlit where possible |
| `tests/test_automation_scheduler_endpoints.py`, `tests/test_data_source_endpoints.py`, `tests/test_sport_analysis_endpoint.py`, `tests/test_outcome_import_endpoint.py`, `tests/test_small_account_endpoints.py` | API route tests | endpoint wiring | no | possible | yes | high | medium | P1 | keep FastAPI tests focused on route wiring and no external calls |
| `tests/test_sharp_sportsbook_adapter.py`, `tests/test_kalshi_readonly_adapter.py`, `tests/test_kalshi_market_provider.py`, `tests/test_kalshi_provider_shape_contract.py`, `tests/test_sportsbook_odds_provider.py`, `tests/test_sharp_scheduler_flow.py`, `tests/test_sharp_cross_book_review_queue.py`, `tests/test_provider_registry.py`, `tests/test_provider_health.py`, `tests/test_provider_secret_policy.py` | provider tests | no-network hardening | yes | possible | yes | high | medium | P1 | keep fake-client coverage, block live calls, and reduce duplicate adapter assertions later |
| `tests/test_scheduler_runner.py`, `tests/test_collector_scheduled_runner.py`, `tests/test_ops_workflow.py`, `tests/test_automation_scheduler_endpoints.py`, `tests/test_phase10k8zfh_safe_migration_batch_2_boundary_guards.py`, `tests/test_phase10k8zfi_automation_scheduler_decomposition_plan.py` | automation_scheduler tests | orchestration boundary | no | possible | yes | high | medium | P1 | align later with orchestration-only ownership; keep current safety checks |
| `tests/test_open_sports_history_import.py`, `tests/test_open_sports_history_backfill.py`, `tests/test_sport_model_routing.py`, `tests/test_multi_sport_model_registry.py`, `tests/test_tennis_model_activation.py`, `tests/test_phase10k8zf0_canonical_research_backtest_workflow_migration_plan.py` | model / backtest tests | historical replay | no | possible | unknown | high | medium | P1 | keep until scenario-based backtest contract exists and wrappers are stable |
| `tests/test_odds_math.py`, `tests/test_kelly*.py`, `tests/test_response_compactor.py`, `tests/test_security_framework.py`, `tests/test_phase10k8ze_institutional_market_metric_catalog.py` | risk / metrics / math tests | policy and math helpers | no | none | yes | medium | low | P2 | map later to `src/core/`, `src/risk/`, and `src/metrics/` after canonical extraction |
| `tests/conftest.py`, `tests/test_live_smoke_payload_contract.py`, `tests/test_phase10k8j_controlled_pipeline_smoke_review.py`, `tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py` | smoke / test wrapper coverage | shared fixtures | no | none | yes | critical | low | P0 | keep stable; do not hide failures with wrapper changes |
| `tests/test_model_router.py`, `tests/test_model_router_registry.py`, `tests/test_institutional_model_router.py`, `tests/test_streamlit_dashboard_data.py`, `tests/test_response_compactor.py` | stale / duplicate / manual-review tests | oversized or overlapping assertions | no | none | unknown | medium | high | manual-review | review after migration freeze; do not delete yet |

## Phase-Report Tests
The phase-report family is a current critical gate because it proves the cleanup sequence and ownership map stayed intact. The 10K8 family is the active guardrail set, and the earlier phase families remain part of the broader historical chain.

Examples:
- `tests/test_phase10k8zf7_r2_archive_pipeline.py`
- `tests/test_phase10k8zf8_r2_transfer_proof_report.py`
- `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py`
- `tests/test_phase10k8zf9c_headerless_csv_final_deletion.py`
- `tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py`
- `tests/test_phase10k8zfe_duplicate_code_evidence_scan.py`
- `tests/test_phase10k8zfe1_universal_product_language_alignment.py`
- `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`
- `tests/test_phase10k8zff_canonical_owner_decision_report.py`
- `tests/test_phase10k8zfg_safe_migration_batch_1.py`
- `tests/test_phase10k8zfh_safe_migration_batch_2_boundary_guards.py`
- `tests/test_phase10k8zfi_automation_scheduler_decomposition_plan.py`
- `tests/test_phase10k8zfj_provider_live_market_decomposition_plan.py`

## Storage / R2 / Archive Tests
These are critical gates. They protect the archive path, manifest path, cleanup safety, and daily hygiene workflow.

Examples:
- `tests/test_phase10k8zf7_r2_archive_pipeline.py`
- `tests/test_phase10k8zf8_r2_transfer_proof_report.py`
- `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py`
- `tests/test_phase10k8zf9c_headerless_csv_final_deletion.py`
- `tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py`
- `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`

## Streamlit / Dashboard-Data Tests
This lane is high-friction because the largest file in the suite is here. It should stay intact for now, but later cleanup should split the assertions by concern rather than deleting coverage.

Examples:
- `tests/test_streamlit_dashboard_data.py`
- `tests/test_line_movement_data_quality_dashboard.py`
- `tests/test_phase10k6b_dashboard_navigation_plan_contract.py`
- `tests/test_phase10k6k_controlled_dashboard_shell_review.py`
- `tests/test_phase10k8zc_dashboard_product_lane_cleanup.py`

## API Route Tests
API route tests should stay thin and use local FastAPI testing surfaces only. The plan is to keep route wiring separate from business logic.

Examples:
- `tests/test_automation_scheduler_endpoints.py`
- `tests/test_data_source_endpoints.py`
- `tests/test_sport_analysis_endpoint.py`
- `tests/test_outcome_import_endpoint.py`
- `tests/test_small_account_endpoints.py`

## Provider Tests
Provider tests must move to a fake-client stance before any cleanup wave removes duplication. This category is the main no-network test policy enforcement point.

Examples:
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_kalshi_provider_shape_contract.py`
- `tests/test_sportsbook_odds_provider.py`
- `tests/test_sharp_scheduler_flow.py`
- `tests/test_sharp_cross_book_review_queue.py`
- `tests/test_provider_registry.py`
- `tests/test_provider_health.py`
- `tests/test_provider_secret_policy.py`

## automation_scheduler Tests
These are still high-value because `automation_scheduler/` remains the operational shell while the canonical owners stabilize.

Examples:
- `tests/test_scheduler_runner.py`
- `tests/test_collector_scheduled_runner.py`
- `tests/test_ops_workflow.py`
- `tests/test_automation_scheduler_endpoints.py`
- `tests/test_phase10k8zfh_safe_migration_batch_2_boundary_guards.py`
- `tests/test_phase10k8zfi_automation_scheduler_decomposition_plan.py`

## Model / Backtest Tests
These tests are still important because backtest behavior is not being rewritten yet. They should remain in place until the scenario-based backtest contract exists.

Examples:
- `tests/test_open_sports_history_import.py`
- `tests/test_open_sports_history_backfill.py`
- `tests/test_sport_model_routing.py`
- `tests/test_multi_sport_model_registry.py`
- `tests/test_tennis_model_activation.py`
- `tests/test_phase10k8zf0_canonical_research_backtest_workflow_migration_plan.py`

## Risk / Metrics / Math Tests
These tests are the guardrails for odds conversion, EV, Kelly, CLV, and related policy math. Cleanup here should happen only after canonical owner extraction is proven.

Examples:
- `tests/test_odds_math.py`
- `tests/test_response_compactor.py`
- `tests/test_security_framework.py`
- `tests/test_phase10k8ze_institutional_market_metric_catalog.py`

## Smoke / Test Wrapper Coverage
This lane is critical because it protects the whole suite and the wrapper commands.

Examples:
- `tests/conftest.py`
- `tests/test_live_smoke_payload_contract.py`
- `tests/test_phase10k8j_controlled_pipeline_smoke_review.py`
- `tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py`

## Stale / Duplicate / Manual-Review Tests
These tests are not deletion candidates yet. They are review candidates because they are large, overlapping, or likely to duplicate newer guardrails.

Examples:
- `tests/test_streamlit_dashboard_data.py` - 1607 lines and broad dashboard assertions
- `tests/test_response_compactor.py` - 834 lines and broad helper coverage
- `tests/test_model_router.py`, `tests/test_model_router_registry.py`, `tests/test_institutional_model_router.py` - likely overlapping router coverage
- `tests/test_sharp_sportsbook_adapter.py` and `tests/test_sharp_scheduler_flow.py` - overlapping Sharp behavior
- `tests/test_kalshi_readonly_adapter.py`, `tests/test_kalshi_market_provider.py`, `tests/test_kalshi_provider_shape_contract.py` - overlapping Kalshi behavior

## Critical Gates To Preserve
The current gates preserved are:
- all phase-report tests
- storage / R2 / archive tests
- Streamlit / dashboard-data tests
- API route tests
- provider tests
- automation_scheduler tests
- model / backtest tests
- risk / metrics / math tests
- smoke / test wrapper coverage
- `tests/conftest.py`

## Cleanup Waves
### Test Wave 0
Preserve current gates. No deletion, no movement, no rewriting.

### Test Wave 1
No-network hardening. Provider, live, and API tests must use fake clients only and must detect accidental external calls.

### Test Wave 2
Split oversized dashboard tests later. Preserve coverage and avoid importing streamlit where possible.

### Test Wave 3
Phase-report consolidation review after migration freeze. Do not consolidate yet.

### Test Wave 4
Storage / R2 / archive safety tests remain critical. Keep manifest and cleanup guards intact.

### Test Wave 5
Map tests to canonical owners for math, risk, metrics, providers, backtest, storage, and API after the source migration waves stabilize.

### Test Wave 6
Slow / fragile test review. Find local-state dependencies and avoid hiding failures with xfail or skip.

### Test Wave 7
Pre-AI / ML test gate. Define the tests that must pass before commercial LLM or ML integration work begins.

### Test Wave 8
Deletion candidate review only after coverage mapping, duplicate proof, and explicit approval.

## No-Network Test Policy
- fake clients only for provider and live-adjacent code
- no external API calls from tests
- no live connectors
- no credentials committed
- no secrets printed
- keep network primitives patched or redirected in tests that touch provider code

## Must-Not-Delete-Yet Test List
The following test groups must stay in place:
- phase-report tests
- storage / R2 / archive tests
- Streamlit / dashboard-data tests
- API route tests
- provider tests
- automation_scheduler tests
- model / backtest tests
- risk / metrics / math tests
- smoke / test wrapper coverage
- `tests/conftest.py`

This phase does not authorize deletion.

## Unsafe Actions
- deleting tests to reduce the suite size
- moving tests before ownership boundaries are stable
- rewriting assertions to hide regressions
- adding xfail or skip to suppress failures
- dropping fake-client coverage from provider or live-adjacent tests
- removing phase-report tests before the migration freeze
- introducing live API calls in tests

## Acceptance Results
- current gates preserved: yes
- no-network test policy documented: yes
- test categories covered: yes
- cleanup waves created: yes
- daily data hygiene scheduler remains operational: yes
- dry-run by default: yes
- agent is advisory only: yes
- agent does not directly delete files: yes
- no AI integration: yes
- no ML training: yes
- no backtest runner: yes
- no controlled data loader: yes
- no broker execution: yes
- no real trade execution: yes
- no scraper actions: yes
- no credentials committed: yes
- no secrets printed: yes

## Next Phase Recommendation
Proceed to 10K8ZFL Pre-AI Integration Repo Freeze
