# Phase 10K8ZHD - Decision and Bet Log Audit

## Executive Summary
Decision orchestration now belongs in `src/services/decision_engine.py`, and the pure numeric pieces belong in `src/core`.

`bet_log.py` remains a root-level storage/compatibility shell until a dedicated storage plan exists.
`bet_decision_engine.py` remains a compatibility shell until callers are fully redirected.

## Classification Summary

- `src/services/decision_engine.py`: `SERVICE_ORCHESTRATION_OWNER`
- `bet_decision_engine.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `bet_log.py`: `COMPATIBILITY_SHIM_CANDIDATE`

## Core vs Service Boundaries

- Decision orchestration: `src/services/decision_engine.py`
- Math/risk/pricing: `src/core`
- Bet logging: root-level storage shell for now
- No external writes, no broker execution, and no database rewrite are authorized here

## Required Statement
Decision orchestration belongs in `src/services/decision_engine.py`. Pure math belongs in `src/core`, and `bet_log.py` remains a compatibility/storage shell until a dedicated service/storage plan exists.
