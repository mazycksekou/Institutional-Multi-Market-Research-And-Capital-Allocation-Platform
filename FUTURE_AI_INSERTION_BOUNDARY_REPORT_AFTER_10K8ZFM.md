# FUTURE_AI_INSERTION_BOUNDARY_REPORT_AFTER_10K8ZFM

## Executive Summary
This audit phase is specifically about finding the safest future insertion points for AI planning, not about implementing AI. The repo is still in a pre-AI, pre-LLM, pre-ML, pre-backtest, pre-controlled-loader state for product work. The canonical-owner map and the scheduler/provider boundaries must be stabilized first.

> No AI integration, commercial LLM integration, ML training, backtest runner, controlled data loader, or live connector work is authorized in this phase.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## Purpose
Define where AI could eventually sit conceptually, what must exist before AI planning, and which boundaries are currently too unstable to accept AI logic.

## Scope
- conceptual placement only
- boundary and contract review only
- no runtime changes
- no AI/LLM/ML implementation
- no data-loader, broker, trade, or scraper work

## Non-Goals
- no model training
- no inference service implementation
- no prompt orchestration implementation
- no evaluation runner implementation
- no backtest runner changes
- no controlled data-loader changes
- no live connector changes
- no external API calls

## Where AI Could Eventually Fit Conceptually
The safest conceptual insertion points are advisory layers that sit on top of stable canonical owners:
- `src/core/` for pure math and pricing features that an AI system may read but not own
- `src/risk/` for policy inputs, guardrails, and sizing constraints
- `src/providers/` for normalized provider adapters and contracts
- `src/metrics/` for evaluation and reporting metrics
- `src/backtester/` for offline evaluation and scenario testing
- `src/storage/` for manifest, archive, and result-store contracts
- `src/api/` for route surfaces that expose advisory results
- `streamlit_app.py` as a shell over dashboard-data helpers
- `automation_scheduler/` only as a temporary orchestration shell

Potentially, a future AI layer could live in a dedicated `src/ai/` or `research_engine/` style advisory package, but only after the canonical owners above are stable and the repo has fake-client/no-network evaluation coverage.

## Where AI Must Not Be Inserted Yet
- `main.py` should not gain AI decision logic
- `api_server.py` should remain a proxy only
- `streamlit_app.py` should not become an AI execution engine
- `automation_scheduler/provider_*` should not become AI-driven live connectors
- `scripts/daily_data_hygiene.py` should not call AI for cleanup decisions
- `scripts/r2_archive_pipeline.py` should not use AI to decide what to delete
- `src/storage/*` should not become an AI policy engine
- `src/api/*` should not hide AI side effects behind route registration

## Canonical Owners That Should Exist Before AI Enters
AI planning should wait until these owners are real and stable:
- `src/core/`
- `src/risk/`
- `src/providers/`
- `src/metrics/`
- `src/backtester/`
- `src/storage/`
- `src/api/`
- `streamlit_app.py` shell over dashboard-data helpers
- `automation_scheduler/` as orchestration only

## Missing Data Contracts
AI planning still lacks a few hardened contracts:
- provider normalization contract
- provider health/status contract
- canonical event/market schema contract
- risk preset contract that stays separate from scenario mode
- scenario backtest contract for missing-data handling
- archive manifest contract for cleanup eligibility
- metrics/evaluation contract for offline model comparison
- observability contract for when AI outputs are advisory versus executable

## Missing Safety Rails
Some safety rails already exist, but they are still incomplete for AI planning:
- no-network test policy is not yet universal
- fake-client-only provider tests are not yet universal
- secret redaction exists but needs continued enforcement
- provider allowlist / secret policy / write firewall are present but still live in legacy scheduler space
- no AI output should be able to trigger deletion, upload, trade, or connector actions
- explicit human-approval gates should remain mandatory for any future external action

## Evaluation / Backtesting Gaps
AI should not enter until the repo has stable offline evaluation boundaries:
- canonical backtester ownership must be settled
- scenario-based backtest semantics must be isolated from risk preset semantics
- model performance and calibration metrics should live in a canonical metrics owner
- behavior-equivalence tests are needed for wrapper migrations before AI is introduced
- no live or commercial AI output should be used as a trading or broker signal

## Observability Gaps
The repo still needs stronger observability before AI planning can be safe:
- no canonical `src/metrics/` package yet
- reporting logic is still spread across scheduler and governance modules
- provider health/snapshot reporting is still partially in scheduler code
- dashboard and API reporting are still coupled to legacy helper locations
- no repo-wide AI audit trail or decision lineage exists yet

## Credential / Policy Controls That Must Exist First
- `.r2.env` must remain ignored and untracked
- secrets must not be committed to source, tests, or docs
- provider secret policy should remain the gate for any future live connector surface
- no live connector may be added without explicit phase approval
- no AI component should read raw credentials directly
- any future AI system must use the same local-only, no-secret-printing discipline as the rest of the repo

## Safe Insertion Boundaries Later
If and when AI planning is authorized in a later phase, the safest insertion order is:
1. canonical owners and contracts stabilize
2. fake-client and no-network tests pass for providers and scheduler wrappers
3. offline evaluation harness exists in the canonical backtest/metrics layers
4. observability and audit logging are standardized
5. AI can be added as advisory analysis only, with no direct execution rights

## Required Statement
No AI integration, commercial LLM integration, ML training, backtest runner, controlled data loader, or live connector work is authorized in this phase.

## Conclusion
The repo is not ready for AI implementation yet, but it is now better mapped for future AI planning. The safe boundary is advisory analysis on top of canonical owners, after the ownership split and no-network evaluation contracts are complete.
