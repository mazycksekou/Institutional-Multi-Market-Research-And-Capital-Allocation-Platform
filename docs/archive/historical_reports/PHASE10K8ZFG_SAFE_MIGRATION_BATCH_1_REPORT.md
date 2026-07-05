# PHASE10K8ZFG Safe Migration Batch 1 Report

## Executive Summary
10K8ZFG is a compatibility migration batch built from the 10K8ZFF canonical ownership map. This is a compatibility migration only. This phase does not authorize deletion.

The batch stays low risk: no files deleted, no files moved, no public functions removed, and no source wrappers changed in this batch. The existing old import path is preserved through the current wrapper surface, and the behavior of the math helpers remains unchanged.

## Current HEAD
Current HEAD before patch: `b94193b11ed388a77dd6d5f647f5021b2f3ea869`

## Purpose
Validate the safest canonical-owner boundary first, prove wrapper compatibility, and keep the migration direction aligned to the canonical ownership map without widening scope.

## Scope
- Follow the canonical owner decisions from 10K8ZFF
- Keep this batch limited to compatibility evidence
- Preserve old import paths and wrapper behavior
- Preserve the daily data hygiene scheduler and the product-language alignment

## Non-Goals
- no files deleted
- no files moved
- no public functions removed
- no AI integration
- no ML training
- no backtest runner
- no controlled data loader
- no broker execution
- no real trade execution
- no scraper actions
- no code migrated without tests

## Relationship to 10K8ZFE
10K8ZFE identified duplicate-risk across math, metrics, signals, risk, providers, backtest, storage, API, dashboard data, and orchestration. This batch only touches the safest compatibility boundary from that evidence.

## Relationship to 10K8ZFF
10K8ZFF created the canonical ownership map and migration direction. This batch uses that canonical owner guidance and keeps the old import path preserved while proving the wrapper surface still matches the canonical helpers.

## Relationship to 10K8ZFE1
10K8ZFE1 aligned user-facing language so that Aggressive paper only became Aggressive, with risk preset controls sizing and scenario mode controls missing-data handling. That separation stays intact.

## Relationship to 10K8ZFE2
10K8ZFE2 added the daily data hygiene scheduler. It remains operational, dry-run by default, and advisory only.

## Migration Strategy
- Treat `src/core/` as the canonical owner for pure odds and EV math
- Keep `automation_scheduler/odds_math.py` as the compatibility wrapper surface for now
- Add tests that prove old import path preserved and behavior unchanged
- Defer all higher-risk ownership moves to later batches

## Canonical Owner Inputs
- canonical owner: `src/core/`
- canonical ownership map: `PHASE10K8ZFF_CANONICAL_OWNER_DECISION_REPORT.md`
- migration direction: move pure math into canonical packages and keep wrappers stable until callers are ready
- old import path preserved: yes
- wrapper preserved: yes

## Files Changed
- `PHASE10K8ZFG_SAFE_MIGRATION_BATCH_1_REPORT.md`
- `tests/test_phase10k8zfg_safe_migration_batch_1.py`

## Functions Migrated Or Wrapped
None in this batch. The compatibility layer already delegates to `src.core.math_utils`, and this batch only proves the existing wrapper behavior.

## Functions Deferred
- metrics / performance helpers
- signals / features helpers
- risk helpers
- providers / data adapter helpers
- backtest helpers
- storage / ledger / archive helpers
- API route wiring
- dashboard data transforms
- orchestration / scheduler business logic

## Compatibility Guarantees
- old import path preserved
- wrapper preserved
- behavior unchanged
- no public functions removed
- no code migrated without tests

The current `automation_scheduler/odds_math.py` wrapper surface forwards the core odds and EV helpers to `src.core.math_utils` for:
- american_to_decimal
- american_to_implied_probability
- decimal_to_implied_probability
- decimal_to_american
- remove_two_way_vig
- calculate_payout
- calculate_profit_loss
- calculate_ev
- calculate_ev_percent
- calculate_roi
- normalize_probability

## Behavior Preservation Evidence
The focused test compares representative wrapper calls against the canonical math helpers for:
- positive American odds
- negative American odds
- implied probability
- decimal conversion
- no-vig if wrapper exists
- EV if wrapper exists

That evidence shows behavior unchanged for the compatibility surface used in this batch.

## Must-Not-Delete-Yet Compliance
must_not_delete_yet complied. The batch keeps the current compatibility and operational surface in place and does not touch any deletion-sensitive paths.

## Daily Hygiene Scheduler Preservation
The daily data hygiene scheduler remains operational. It is dry-run by default, execute requires explicit flags, archive before delete is still required, manifest-listed files only are eligible for cleanup, and the agent is advisory only.

## Risk Preset / Scenario Language Preservation
The product language remains aligned:
- risk preset controls sizing
- scenario mode controls missing-data handling

The user-facing label is Aggressive, not Aggressive paper only.

## Safety Gate Results
- This phase does not authorize deletion.
- no files deleted
- no files moved
- no public functions removed
- no code migrated without tests
- source code was preserved
- tests/fixtures were preserved
- manifests were preserved
- archives were preserved
- tracked files were preserved

## Tests Run
- `pytest tests/test_phase10k8zfg_safe_migration_batch_1.py -q`
- `pytest tests/test_phase10k8zff_canonical_owner_decision_report.py -q`
- `pytest tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py -q`
- `pytest tests/test_phase10k8zfe1_universal_product_language_alignment.py -q`
- `pytest tests/test_phase10k8zfe_duplicate_code_evidence_scan.py -q`
- `pytest tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py -q`
- `pytest tests/test_phase10k8zf9c_headerless_csv_final_deletion.py -q`
- `pytest tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py -q`
- `pytest tests/test_phase10k8zf9_full_r2_transfer_report.py -q`
- `pytest tests/test_phase10k8zf8_r2_transfer_proof_report.py -q`
- `pytest tests/test_phase10k8zf7_r2_archive_pipeline.py -q`
- `test`
- `smoke`
- `stat`

## Acceptance Results
This compatibility migration batch is intentionally narrow and safe. It keeps the canonical owner boundary stable, preserves old import paths, and proves wrapper behavior against the canonical math helpers without changing source behavior.

## Next Phase Recommendation
Proceed to 10K8ZFH Safe Migration Batch 2

