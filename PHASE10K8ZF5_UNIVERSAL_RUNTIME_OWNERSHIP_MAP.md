# PHASE10K8ZF5 Universal Runtime Entrypoint + Canonical Ownership Map

## Executive Summary
10K8ZF5 maps the current repo into one universal system and identifies duplicate-owner risk without moving or deleting code.

The repo is still in research/backtest mode only. The key conclusion is that the canonical future architecture is already visible in the file layout, but ownership is still split across `src/`, `automation_scheduler/`, `research/`, `research_engine/`, `providers/`, `betting_providers/`, `quant_engine.py`, `risk_engine.py`, and root legacy helpers.

Deletion is not allowed in this phase. Do not delete any code until explicitly proven duplicate.

## Senior Systems Engineering Standard
- one universal system
- one canonical owner per concept
- no duplicate math
- no duplicate metrics
- no duplicate signals
- no duplicate risk logic
- no duplicate provider adapters
- no duplicate backtest engines
- no duplicate dashboard-data paths
- Do not delete any code until explicitly proven duplicate

## Current HEAD
Current HEAD: `d201c13`

## Universal Ownership Rule
There must be one canonical owner per concept.
Do not create parallel implementations of math, metrics, signals, providers, backtesting, storage, or dashboard-data logic.
`automation_scheduler/` and `live_market_intelligence/` are migration sources until mapped into canonical owners.
Do not delete legacy code until duplicate status is proven and tests protect the canonical replacement.

## Final Target Architecture
- `src/core/` pure math only
- `src/risk/` bankroll, drawdown, exposure, ruin, sizing
- `src/providers/` API/data vendor adapters only
- `src/markets/` market schemas + feature definitions
- `src/signals/` ORB, footprint, whale flow, RLM, steam, breakouts
- `src/backtester/` engine, fills, slippage, costs, experiment matrix
- `src/metrics/` Sharpe, PBO, CLV, Brier, Gamma PnL
- `src/storage/` local warehouse/repositories
- `src/api/` FastAPI routes only, if kept
- `dashboard/`
- `tests/`
- `docs/`
- `src/signals/footprint.py detects large-flow anomaly`
- `src/signals/opening_range.py detects OR high/low/break/failure`
- `src/backtester/experiment_matrix.py tests with / without / fade / confirm / avoid`
- `src/metrics/ proves whether signal improved or degraded expectancy`

## Runtime Entrypoints
- `main.py` is the backend/API runtime entrypoint.
- `api_server.py` is the deployment adapter for `api_server:app`.
- `streamlit_app.py` is the dashboard runtime entrypoint.
- `scripts/*.ps1` and `scripts/*.py` are operational entrypoints, not canonical application owners.
- `automation_scheduler/__init__.py` is a broad orchestration facade with many callable operations, not a stable final entrypoint.

## Dashboard/UI Ownership
- `streamlit_app.py` is the dashboard entrypoint.
- `automation_scheduler/streamlit_dashboard_data.py` is the current dashboard-data helper layer.
- `dashboard/` does not yet exist in this branch.
- The visible surface is research/backtest mode only.

## Backend/API Ownership
- `main.py` assembles the FastAPI app and registers routes.
- `api_server.py` proxies `main.py` for deployment compatibility.
- `src/api/` is the current backend route package.
- `src/api/schemas/` owns request/response models for the backend surface.

## Core Math Ownership
- `quant_engine.py` is the current canonical owner for EV/edge/fair odds/implied probability where applicable until migrated.
- `src/core/math_utils.py`, `src/core/clv.py`, and `src/core/opportunity_scanner.py` are core math / pricing / scan helpers.
- `src/core/backtester.py` currently mixes model training with walk-forward backtest behavior and overlaps the future backtester boundary.
- `math_models/institutional/` is a parallel math area with possible duplicate math/metric ownership.

## Risk Ownership
- `risk_engine.py` is the current canonical owner for staking/risk/bankroll policy until migrated.
- `automation_scheduler/drawdown_controls.py`, `automation_scheduler/exposure_limits.py`, `automation_scheduler/budget_gates.py`, `automation_scheduler/hard_gate_policy.py`, `automation_scheduler/risk_of_ruin.py`, and `automation_scheduler/risk_limit_guard.py` overlap the risk-policy surface.
- `model_governance/risk_gate.py`, `model_governance/kelly_gate.py`, and related governance gates overlap risk policy and validation policy.

## Provider Ownership
- `providers/` is a provider adapter package.
- `betting_providers/` is another provider adapter package with overlapping odds/Kalshi/sharp abstractions.
- `automation_scheduler/provider_*.py` files are legacy provider-policy and provider-contract helpers.
- `src/services/enrichment_service.py` and `src/api/provider_status_routes.py` are provider-facing integration surfaces.

## Market Schema/Catalog Ownership
- `automation_scheduler/model_data_field_catalog.py`
- `automation_scheduler/technical_signal_fields.py`
- `automation_scheduler/backtest_schema.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/nfl_open_data_field_catalog.py`
- `automation_scheduler/football_impact_schema.py`

## Signal/Research Ownership
- `src/sports/nba_features.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/line_movement_readiness.py`
- `automation_scheduler/historical_line_movement.py`
- `automation_scheduler/synthetic_line_movement_sandbox.py`
- `automation_scheduler/arbitrage/`
- `research/`
- `research_engine/`
- `orb_backtest.py` is absent in this branch.
- `zero_dte_orb.py` is absent in this branch.

## Backtester/Data Ownership
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/backtest_strategy_profiles.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `src/services/model_backtest_service.py`
- `src/core/backtester.py`

## Metrics/Reporting Ownership
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/calibration_tracker.py`
- `model_governance/governance_report.py`
- `model_governance/model_validation_report.py`

## Storage/History Ownership
- `research/market_research_store.py`
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/paper_trade_ledger.py`
- `automation_scheduler/paper_decision_ledger.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `model_governance/governance_audit_log.py`

## automation_scheduler Migration Source Map
`automation_scheduler/` is a migration source until mapped into canonical owners.
It currently mixes:
- dashboard-data helpers
- legacy provider adapters
- backtest helpers
- storage/history helpers
- metrics/reporting helpers
- signal/research helpers
- risk-policy helpers
- orchestration and gating utilities

## live_market_intelligence Migration Source Map
`live_market_intelligence/` is a migration source until mapped into canonical owners.
No tracked files currently exist in that directory in this branch.

## research and research_engine Migration Source Map
- `research/market_research_store.py` is a storage/history surface.
- `research/market_research_schema.py` is a storage/schema surface.
- `research_engine/evidence_scorecard.py` is an evidence/metrics surface.
- `research_engine/decision_committee.py` is a governance/review surface.

## providers and betting_providers Migration Source Map
- `providers/` contains provider adapters for odds and Kalshi-style data.
- `betting_providers/` contains overlapping provider adapters and normalization helpers.
- `providers/` is the cleaner candidate for canonical provider ownership later.

## Root File Ownership Map
| Current path | Current role | Final target owner | Classification | Duplicate-risk category | Migration action later | Evidence | Must-not-touch-yet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `main.py` | FastAPI app assembly and route registration | `src/api/` future app-factory surface | backend_api | possible_duplicate_api_route | keep_as_canonical | imports and registers API routes | yes |
| `api_server.py` | Deployment adapter for `api_server:app` | compatibility shim around backend API | backend_api | possible_duplicate_api_route | keep_as_compatibility_shim_later | dynamic import proxy to `main` | yes |
| `streamlit_app.py` | Streamlit operator dashboard | `dashboard/` later or retained dashboard entrypoint | dashboard_ui | possible_duplicate_dashboard_data | keep_as_canonical | Streamlit UI and dashboard helper imports | yes |
| `quant_engine.py` | EV, edge, Kelly, implied probability, fixture math | `src/core/` | core_math | possible_duplicate_math | keep_as_canonical | math and paper-only fixture evaluation functions | yes |
| `risk_engine.py` | staking, bankroll, exposure, ruin policy | `src/risk/` | risk_policy | possible_duplicate_risk | keep_as_canonical | bankroll/exposure/risk functions | yes |
| `kalshi_client.py` | root-level provider adapter | `src/providers/` later | provider_adapter | possible_duplicate_provider | move_to_src_providers_later | direct client naming | yes |
| `sharp_client.py` | root-level provider adapter | `src/providers/` later | provider_adapter | possible_duplicate_provider | move_to_src_providers_later | direct client naming | yes |
| `market_pricing.py` | root-level pricing math | `src/core/` later | core_math | possible_duplicate_math | move_to_src_core_later | market pricing naming | yes |
| `model_probability.py` | root-level probability helper | `src/core/` later | core_math | possible_duplicate_math | move_to_src_core_later | model probability naming | yes |
| `bet_decision_engine.py` | root-level decision helper | `src/backtester/` or `src/risk/` later | unknown_review_required | possible_duplicate_risk | must_not_touch_until_tests_cover | decision logic naming | yes |
| `full_board_engine.py` | root-level board engine | `src/markets/` or `src/backtester/` later | unknown_review_required | possible_duplicate_backtest | must_not_touch_until_tests_cover | board engine naming | yes |
| `parlay_engine.py` | root-level bet aggregation engine | `src/core/` or `src/backtester/` later | unknown_review_required | possible_duplicate_backtest | must_not_touch_until_tests_cover | parlay engine naming | yes |
| `logbook_engine.py` | root-level log/history helper | `src/storage/` later | storage_history | possible_duplicate_storage | move_to_src_storage_later | logbook naming | yes |
| `asian_markets.py` | root-level market helper | `src/markets/` later | market_schema_catalog | possible_duplicate_signal | move_to_src_markets_later | market-specific naming | yes |
| `config.py` | application configuration | keep at root for now | unknown_review_required | no_duplicate_risk_identified | keep_as_canonical | app config file | yes |
| `openapi.yaml` | API contract artifact | `src/api/` or docs later | backend_api | possible_duplicate_api_route | keep_as_canonical | OpenAPI artifact | yes |
| `README.md` | project contract | docs | docs_phase_artifact | no_duplicate_risk_identified | move_to_docs_later | current contract doc | yes |

## Duplicate Math Risk Map
Candidate files:
- `src/core/math_utils.py`
- `quant_engine.py`
- `automation_scheduler/ev_line_shopper.py`
- `automation_scheduler/no_vig_pricing.py`
- `betting_providers/normalization.py`
- `math_models/institutional/*.py`

Suspected overlap:
- implied probability
- EV
- Kelly / stake sizing
- fair odds / break-even math
- odds normalization

Evidence found:
- `src/core/math_utils.py` defines implied probability, EV, Kelly, and fair-odds helpers.
- `quant_engine.py` duplicates implied probability, EV, Kelly, and fixture evaluation behavior.
- `automation_scheduler/ev_line_shopper.py` and `automation_scheduler/no_vig_pricing.py` also call into EV/odds math.

Final canonical owner target:
- `src/core/` for pure math
- `quant_engine.py` remains compatibility owner until migration completes

Deletion allowed now:
- NO

## Duplicate Metrics Risk Map
Candidate files:
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/performance_metrics.py`
- `model_governance/governance_report.py`
- `model_governance/model_validation_report.py`
- `research_engine/evidence_scorecard.py`

Suspected overlap:
- CLV
- Sharpe / backtest reporting
- calibration / validation summaries
- governance scorecards

Evidence found:
- `automation_scheduler/model_performance_report.py` is the current report generator.
- `automation_scheduler/clv_tracker.py` duplicates CLV reporting logic.
- `model_governance/*report.py` files produce validation/report artifacts that overlap metrics/reporting ownership.

Final canonical owner target:
- `src/metrics/` future
- `automation_scheduler/model_performance_report.py` remains a source until migration

Deletion allowed now:
- NO

## Duplicate Signals Risk Map
Candidate files:
- `src/sports/nba_features.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/line_movement_readiness.py`
- `automation_scheduler/historical_line_movement.py`
- `automation_scheduler/synthetic_line_movement_sandbox.py`
- `automation_scheduler/arbitrage/`
- `research/`
- `research_engine/`
- `automation_scheduler/football_impact_*`
- `automation_scheduler/basketball_*`
- `automation_scheduler/hockey_*`
- `automation_scheduler/baseball_*`
- `automation_scheduler/golf_*`
- `automation_scheduler/combat_*`
- `automation_scheduler/tennis_*`

Suspected overlap:
- feature generation
- line movement signals
- ablation/research experiments
- arbitrage detections
- sport-specific signal packs

Evidence found:
- `src/sports/nba_features.py` builds training/live features.
- `automation_scheduler/feature_ablation_lab.py` and `line_movement_*` own feature research utilities.
- `automation_scheduler/synthetic_line_movement_sandbox.py` is explicit sandbox logic.

Final canonical owner target:
- `src/signals/` future
- `src/markets/` for schema/feature definitions

Deletion allowed now:
- NO

## Duplicate Risk Logic Map
Candidate files:
- `risk_engine.py`
- `automation_scheduler/drawdown_controls.py`
- `automation_scheduler/exposure_limits.py`
- `automation_scheduler/budget_gates.py`
- `automation_scheduler/hard_gate_policy.py`
- `model_governance/risk_gate.py`
- `model_governance/kelly_gate.py`
- `automation_scheduler/liquidity_risk.py`
- `automation_scheduler/balance_sheet_risk.py`
- `automation_scheduler/institutional_risk_engine.py`

Suspected overlap:
- bankroll sizing
- drawdown caps
- exposure limits
- Kelly gating
- risk-of-ruin logic

Evidence found:
- `risk_engine.py` owns bankroll/risk functions.
- `automation_scheduler/drawdown_controls.py` and `exposure_limits.py` implement overlapping policy gates.
- `model_governance/risk_gate.py` and `kelly_gate.py` duplicate policy logic.

Final canonical owner target:
- `src/risk/` future
- `risk_engine.py` remains compatibility owner until migration completes

Deletion allowed now:
- NO

## Duplicate Provider Risk Map
Candidate files:
- `providers/`
- `betting_providers/`
- `automation_scheduler/provider_*.py`
- `src/services/enrichment_service.py`
- `src/api/provider_status_routes.py`
- `kalshi_client.py`
- `sharp_client.py`

Suspected overlap:
- provider adapters
- odds normalization
- provider routing
- provider health/status

Evidence found:
- `providers/` and `betting_providers/` both expose adapter-style integrations.
- `automation_scheduler/provider_*` files define provider contracts and policies.
- `src/services/enrichment_service.py` and `src/api/provider_status_routes.py` consume provider adapters.

Final canonical owner target:
- `src/providers/` future

Deletion allowed now:
- NO

## Duplicate Backtest Risk Map
Candidate files:
- `src/core/backtester.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/backtest_strategy_profiles.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `src/services/model_backtest_service.py`
- `automation_scheduler/backtest_schema.py`

Suspected overlap:
- historical simulation
- dataset building
- walk-forward execution
- bankroll simulation
- schema validation for backtest rows

Evidence found:
- `src/core/backtester.py` already mixes model training and walk-forward backtesting.
- `automation_scheduler/backtesting_engine.py` and `backtest_dataset_builder.py` own historical backtest data flow.
- `src/services/model_backtest_service.py` wraps backtest execution for backend use.

Final canonical owner target:
- `src/backtester/` future

Deletion allowed now:
- NO

## Duplicate Storage Risk Map
Candidate files:
- `research/market_research_store.py`
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/paper_trade_ledger.py`
- `automation_scheduler/paper_decision_ledger.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `model_governance/governance_audit_log.py`
- `data/`
- `reports/`
- `models/compressed/basketball_nba_v1.joblib`

Suspected overlap:
- local storage
- historical record keeping
- experiment history
- paper-ledger style persistence

Evidence found:
- `research/market_research_store.py` is a store/schema layer.
- `automation_scheduler/experiment_history_store.py` and the ledger files record run/history artifacts.
- `models/compressed/basketball_nba_v1.joblib` is a tracked binary artifact, not source code.

Final canonical owner target:
- `src/storage/` future

Deletion allowed now:
- NO

## Duplicate Dashboard-Data Risk Map
Candidate files:
- `streamlit_app.py`
- `automation_scheduler/streamlit_dashboard_data.py`

Suspected overlap:
- UI payload shaping
- readiness display data
- dashboard helper logic

Evidence found:
- `streamlit_app.py` imports multiple helpers from `automation_scheduler/streamlit_dashboard_data.py`.
- `automation_scheduler/streamlit_dashboard_data.py` is a large pure-data helper layer for dashboard content.

Final canonical owner target:
- `dashboard/` future or retained `streamlit_app.py` entrypoint with a thinner helper package

Deletion allowed now:
- NO

## Duplicate API Route Risk Map
Candidate files:
- `main.py`
- `api_server.py`
- `src/api/`
- `src/api/*routes*.py`
- `src/api/schemas/*.py`

Suspected overlap:
- route registration
- request/response schemas
- backend API assembly

Evidence found:
- `main.py` assembles FastAPI and registers routes.
- `api_server.py` is a dynamic proxy adapter to `main.py`.
- `src/api/` is the backend route package.

Final canonical owner target:
- `src/api/`

Deletion allowed now:
- NO

## Must-Not-Delete-Yet List
- `main.py`
- `api_server.py`
- `streamlit_app.py`
- `quant_engine.py`
- `risk_engine.py`
- `src/api/`
- `src/core/`
- `src/services/model_backtest_service.py`
- `automation_scheduler/`
- `research/`
- `research_engine/`
- `providers/`
- `betting_providers/`
- `model_governance/`
- `math_models/`
- `models/compressed/basketball_nba_v1.joblib`
- `data/`
- `reports/`
- `PHASE10K8ZF*` docs

## Future Migration Actions
1. Keep as canonical where the repo already has stable ownership.
2. Move core math to `src/core/` and `src/metrics/` later.
3. Move risk policy to `src/risk/` later.
4. Move provider adapters to `src/providers/` later.
5. Move market schemas to `src/markets/` later.
6. Move signal/research logic to `src/signals/` later.
7. Move backtest execution to `src/backtester/` later.
8. Move storage/history to `src/storage/` later.
9. Keep legacy modules as compatibility shims only until tests protect replacements.

## Pre-Backtest Universal System Gates
- pre-backtest cleanup must finish before controlled data loader or backtest runner
- no broker execution
- no real trade execution
- no live connectors
- no API calls without explicit provider phase
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language
- Deletion is not allowed in this phase.

## Next Phase Recommendation
Proceed to 10K8ZF6 Duplicate Code / Math / Metrics / Signal Evidence Scan.

## Required Audit Strings
- 10K8ZF5
- Universal Runtime Entrypoint + Canonical Ownership Map
- senior-systems-engineer quality
- one universal system
- one canonical owner per concept
- no duplicate math
- no duplicate metrics
- no duplicate signals
- no duplicate risk logic
- no duplicate provider adapters
- no duplicate backtest engines
- no duplicate dashboard-data paths
- Do not delete any code until explicitly proven duplicate
- automation_scheduler/ is a migration source until mapped into canonical owners
- live_market_intelligence/ is a migration source until mapped into canonical owners
- src/core/
- src/risk/
- src/providers/
- src/markets/
- src/signals/
- src/backtester/
- src/metrics/
- src/storage/
- src/api/
- dashboard/
- src/signals/footprint.py detects large-flow anomaly
- src/signals/opening_range.py detects OR high/low/break/failure
- src/backtester/experiment_matrix.py tests with / without / fade / confirm / avoid
- src/metrics/ proves whether signal improved or degraded expectancy
- Data
- Validation
- Strategy Research
- Backtest
- Results / Metrics
- Later: Live Model Testing
- pre-backtest cleanup must finish before controlled data loader or backtest runner
- no broker execution
- no real trade execution
- no live connectors
- no API calls without explicit provider phase
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF5
