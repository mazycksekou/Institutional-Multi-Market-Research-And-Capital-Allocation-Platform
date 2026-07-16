# Next Action

## Next Phase

`NFL Production Completion`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened NFL research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.

## Objective

Audit the certified NFL implementation against production-complete requirements.
Reuse the Universal Market Framework as the canonical reusable foundation.
Close only verified NFL production gaps while preserving all certified NFL reference behavior, lineage, provenance, determinism, and point-in-time integrity.
Do not implement another sport, prediction markets, Zero-DTE options, Worldview, capital allocation, paper trading, or live execution in this phase.

## Allowed Actions

- Reuse the canonical Universal Market Framework contracts, registries, lifecycle gates, readiness surfaces, dashboard/query interfaces, and certified NFL reference owners.
- Audit NFL production readiness across certified research completeness, deterministic feature coverage, dashboard completeness, reporting completeness, query completeness, validation completeness, and documentation completeness.
- Close only verified NFL-specific production gaps that sit above the Universal Market Framework and do not duplicate reusable framework logic.
- Preserve dataset-batch references, dataset-row references, feature references, math references, signal references, decision references, backtest references, validation references, research-intelligence references, source certification references, and field-level provenance links.
- Update project status, roadmap, and document indexes when this phase completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not implement another sport.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement Worldview Intelligence.
- Do not implement cross-market intelligence.
- Do not implement universal risk and capital allocation.
- Do not implement live execution.
- Do not implement paper trading.
- Do not duplicate Universal Market Framework logic or create NFL-only replacements for reusable framework assets.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- A verified audit of the certified NFL implementation against production-complete requirements.
- Closed verified NFL production gaps that preserve certified NFL reference behavior and reuse the Universal Market Framework.
- Completed NFL-specific dashboard, reporting, query, validation, and documentation surfaces that do not create parallel reusable systems.
- Updated project status, roadmap, and document indexes when the phase completes.
- Sequencing handoff to the `Covariance and Time-Dependent Risk Capability Audit` after NFL production validation completes.

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
