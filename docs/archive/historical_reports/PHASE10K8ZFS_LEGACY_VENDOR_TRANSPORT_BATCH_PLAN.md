# PHASE10K8ZFS_LEGACY_VENDOR_TRANSPORT_BATCH_PLAN

## Summary
This phase creates an ordered transport roadmap for legacy vendor/provider/client/adapter functionality. It does not migrate runtime code. It does not delete modules. It defines where useful behavior should land next and which modules should later become shims or deletion candidates.

## Files Reviewed
- `FULL_VENDOR_REFERENCE_INVENTORY_AFTER_10K8ZFQ.md`
- `VENDOR_FUNCTIONALITY_TRANSPORT_MAP_AFTER_10K8ZFQ.md`
- `VENDOR_MODULE_DELETION_CANDIDATES_AFTER_10K8ZFQ.md`
- `PROVIDER_PRODUCT_GOAL_ALIGNMENT_REPORT_AFTER_10K8ZFQ.md`
- `PHASE10K8ZFQ_VENDOR_MODULE_AUDIT.md`
- `PHASE10K8ZFR_PRODUCTION_MODULE_BOUNDARY_SCAFFOLD.md`
- existing provider, registry, health, normalization, and adapter contract tests

## What Was Decided
- `src/providers` remains the canonical product-category provider boundary.
- `src/connectors` is the future raw data access boundary.
- `src/ai` is the future reasoning/evaluation boundary.
- `src/brokerage` is the future execution boundary.
- The first safe transport batch should target pure provider foundations and keep all legacy paths importable.
- Raw connector logic should be split from normalized provider logic instead of being lumped together.
- Vendor-named modules should become wrappers, shims, or delete candidates after proof.

## What Was Not Changed
- No runtime implementation code moved.
- No live API calls were introduced.
- No broker or trade execution was added.
- No AI calls or model training were added.
- No files were deleted.
- No file moves were performed.

## Current Safety Posture
- The repo remains in a planning-only state.
- The new production boundaries are scaffold-only.
- Existing provider taxonomy tests still validate vendor-neutral categories.
- The transport plan keeps deletion gated behind dependency proof and test redirection.

## Next Recommended Phase
Proceed to the first safe transport implementation batch for provider foundations, then move raw connector logic separately, and only later shrink `automation_scheduler`.

## Required Statement
Useful legacy vendor functionality should be transported into the correct production domain. Vendor-named modules should not remain permanent architecture owners. Deletion is allowed only after dependency proof, test redirection, and safe replacement are complete.
