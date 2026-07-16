# Next Action

## Next Phase

`Supported sports, prediction markets, and Zero-DTE research implementations`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened NFL research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.

Historical handoff objective preserved for audit compatibility: Build the first reusable Universal Market Framework on top of the certified NFL research pipeline and the deterministic Research Intelligence layer.

## Objective

Use the Universal Market Framework as the governed onboarding boundary for future supported sports, prediction markets, and Zero-DTE research implementations.
Future implementation must satisfy the reusable profile contracts, lifecycle gates, readiness surfaces, parity checks, and dashboard/query interfaces before activating a new market profile.
The certified NFL evidence chain and Research Intelligence outputs remain immutable reference behavior.
Do not ingest paid or live data, do not add paper trading or live execution, and do not bypass the certified NFL reference path in the next phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, certification, lifecycle, feature registry, math engine, signal, decision, baseline-backtesting, pipeline-validation, and research-intelligence owners.
- Extract shared contracts, registries, and dashboard-ready framework surfaces from the certified NFL path without mutating the certified NFL outputs.
- Preserve dataset-batch references, dataset-row references, feature references, math references, signal references, decision references, backtest references, validation references, research-intelligence references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, certified dataset, feature engine, signal engine, decision engine, backtest engine, or Research Intelligence engine for the NFL path.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement walk-forward validation yet.
- Do not implement paper trading yet.
- Do not implement live execution.
- Do not activate additional markets before the shared framework contract is in place.
- Do not add machine learning, optimization, or parameter tuning.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for Universal Market Framework work on the certified NFL path.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Shared Universal Market Framework contracts derived from the certified NFL research path.
- Preserved deterministic NFL outputs and readiness evidence while framework seams are generalized.
- Dashboard-ready framework and readiness reporting that keeps the certified NFL path as the reference implementation.

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest -m smoke -q`
- `python scripts/check_root_markdown.py`
- `python scripts/check_openapi_contract.py --output text`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_audit_lifecycle.py`
- `python scripts/check_document_lifecycle.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python scripts/check_repo_preflight.py --before-commit --include-ops`
- `python scripts/check_repo_preflight.py --before-push --include-ops`
- `python scripts/check_repo_preflight.py --end-task --include-ops`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File .\\scripts\\run_tests.ps1 -Mode full`
