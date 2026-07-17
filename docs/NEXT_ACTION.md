# Next Action

## Next Phase

`Covariance and Time-Dependent Risk Capability Audit`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened NFL research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.
`NFL Production Completion` audited the certified NFL implementation against production-complete requirements, reused the Universal Market Framework, added the canonical production audit/report/query surface, and preserved all certified NFL reference behavior.
Close only verified NFL production gaps remained the governing closure rule for the completed NFL Production Completion phase.

## Objective

Inspect the repository before implementation and determine existing, partial, missing, duplicated, or deferred support for covariance, correlation, and time-dependent risk capabilities.
Audit only. Do not implement covariance or risk-engine functionality in this phase.
Preserve all certified NFL reference behavior, lineage, provenance, determinism, and point-in-time integrity while identifying the canonical owners, extension seams, and blockers for later implementation.

## Allowed Actions

- Audit existing support for covariance and correlation.
- Audit existing support for rolling and exponentially weighted covariance.
- Audit existing support for covariance stability and regime detection.
- Audit existing support for cross-market and strategy covariance.
- Audit existing support for holding-period and forecast-horizon risk.
- Audit existing support for confidence and freshness decay.
- Audit existing support for overnight, weekend, event, expiration, and liquidity risk.
- Audit existing support for time-to-event and time-to-expiration risk.
- Audit existing support for risk-horizon normalization and attribution.
- Reuse canonical owners, readiness surfaces, and certified NFL reference evidence while identifying extension seams only.
- Update project status, sequencing, and document indexes when the audit completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not implement covariance or the risk engine.
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

- A verified repository audit covering existing, partial, missing, duplicated, and deferred covariance and time-dependent risk support.
- A canonical owner and extension-seam inventory for later implementation.
- A blocker ledger that preserves the certified NFL reference implementation and the Universal Market Framework boundaries.
- Updated project status, sequencing, and document indexes when the audit completes.

## Validation Commands

- `python scripts/check_root_markdown.py`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_document_lifecycle.py --output text`
- `git diff --check`
