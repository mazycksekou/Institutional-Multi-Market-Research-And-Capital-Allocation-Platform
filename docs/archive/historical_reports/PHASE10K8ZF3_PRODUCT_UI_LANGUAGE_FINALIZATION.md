# PHASE10K8ZF3 Product UI Language Finalization

## Executive Summary
10K8ZF3 retires hidden legacy source-text blocks from `streamlit_app.py` and finalizes the visible product surface around canonical research/backtest wording.

## Product Decision
The new product contract supersedes obsolete fake/paper/testing-room public-copy assertions.

## Hidden Compatibility Text Retired
Hidden legacy source-text blocks retired. Obsolete fake/paper/testing-room product copy removed.

## Tests Updated
The targeted tests now assert canonical research_backtest wording instead of obsolete hidden compatibility tokens.

## Canonical Product Language
Canonical research_backtest wording is the visible product surface.

## Legacy Alias Boundary
Paper names may remain only as backward-compatible helper aliases.

## Safety Guardrails Preserved
Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.

## Backtest Path Requirement
There is no separate paper workflow.
One canonical workflow remains:

Data
-> Validation
-> Strategy Research
-> Backtest
-> Results / Metrics
-> Later: Live Model Testing

## Live Model Testing Boundary
Later: Live Model Testing is the future downstream step, not a live execution permission.

## Broker Boundary
no broker execution
no real trade execution

## Connector Boundary
no live connectors

## API Boundary
no API calls

## Database Write Boundary
no database writes

## Pre-Backtest Cleanup Requirement
Pre-backtest cleanup must happen before controlled data loader or backtest runner.

## Next Phase Recommendation
Proceed to 10K8ZF4 Pre-Backtest Repo Cleanup Inventory.

## Audit Notes
- 10K8ZF3
- Product UI Language Finalization
- hidden legacy source-text blocks retired
- obsolete fake/paper/testing-room product copy removed
- canonical research_backtest wording is the visible product surface
- paper names may remain only as backward-compatible helper aliases
- no separate paper workflow
- one canonical workflow
- Data
- Validation
- Strategy Research
- Backtest
- Results / Metrics
- Later: Live Model Testing
- Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.
- pre-backtest cleanup must happen before controlled data loader or backtest runner
- no broker execution
- no real trade execution
- no live connectors
- no API calls
- no database writes
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF3
