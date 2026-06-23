# Phase 10K8ZH4 - Core Pricing Extraction

## Executive Summary
Pricing ownership is canonical in `src/core/pricing.py`.
Legacy wrappers `market_pricing.py` and `quant_engine.py` remain importable for compatibility.
The extraction is pure Python only and keeps live execution out of scope.

## Current HEAD
`11c1432442d070500cc4853bc3acab79845cf908`

## Scope
- American odds to decimal
- Decimal odds to implied probability
- American odds to implied probability
- Fair odds from probability
- No-vig probability helpers
- Expected value and edge helpers
- Payout and profit units
- Price normalization helpers

## Ownership Map
- Canonical target: `src/core/pricing.py`
- Compatibility wrappers: `market_pricing.py`, `quant_engine.py`
- Out of scope: connectors, providers, dashboard, main, live execution

## Compatibility Report
Root wrappers keep their public imports while the canonical module owns the shared math.
No live API calls, credential reads, or broker behavior are introduced.

