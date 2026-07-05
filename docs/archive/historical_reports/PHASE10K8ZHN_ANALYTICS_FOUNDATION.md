# PHASE 10K8ZHN Analytics Foundation

## Executive Summary
`src.analytics` is the canonical home for local, deterministic analytics summaries. It owns reporting, attribution, calibration summaries, governance summaries, performance analytics, and model evaluation summaries.

This phase establishes the package boundary only. It does not activate live data, AI/LLM behavior, brokerage execution, or dashboard rendering.

## Why Analytics Is a Production Domain
- Analytics is downstream of `src.data` and `src.backtesting`.
- Analytics is upstream of model-governance review, reporting, and future AI/brokerage decisions.
- Analytics should own summary objects, not enforcement or live execution.

## Module Boundary Map
- `src/analytics/__init__.py`
- `src/analytics/contracts.py`
- `src/analytics/performance.py`
- `src/analytics/attribution.py`
- `src/analytics/governance.py`

## What Belongs in `src.analytics`
- Reporting summaries
- Attribution summaries
- Calibration summaries
- Governance summaries
- Performance analytics
- Model evaluation summaries

## What Must Not Cross the Boundary
- No live data fetches
- No AI/LLM calls
- No credential reads
- No scraping activation
- No broker execution
- No bet execution
- No trade execution
- No connector activation
- No dashboard rendering
- No `main.py` rewrite

## Future Migration Strategy
1. Keep hard math/probability/pricing/risk in `src.core`.
2. Move reporting and summary helpers into `src.analytics`.
3. Keep `model_governance` enforcement and approval gates thin until proof-backed migration is ready.
4. Defer AI/LLM integration until analytics, data, and research boundaries are canonical.

## Safety Guarantees
- Local-only deterministic objects and helpers.
- No network imports.
- No environment credential reads.
- No side effects at import time.
- No live production activation.
- No live API calls.
- No broker execution.
- No AI/LLM calls.

## Required Statement
`src.analytics` is the canonical local-only analytics ownership boundary. This phase does not authorize live data, AI/LLM, brokerage, scraping, or execution behavior.
