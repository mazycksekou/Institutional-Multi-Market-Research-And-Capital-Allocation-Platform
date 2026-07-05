# Phase 10K8ZJ4 Live Ledger Persistence Boundary Plan

## Status

`src.brokerage.ledger` is the canonical local in-memory/model ledger.
`src.services.ledger_service` is the canonical local file-backed audit/performance store.
`automation_scheduler/paper_trade_ledger.py`, `automation_scheduler/paper_decision_ledger.py`, and `bet_log.py` remain compatibility inputs only.

## Future Target

Live ledger persistence remains disabled and will require an explicit approval and activation phase later.

## Why Disabled

No live persistence, no external writes, and no production activation are allowed in this phase.

