# PHASE 10K8ZHO Research Foundation

## Executive Summary
`src.research` is the canonical home for research-lane descriptors, experiment metadata, hypothesis tracking, ablation planning, and non-live research scaffolds.

This phase establishes the package boundary only. It does not activate AI/LLM calls, live data pulls, external writes, or research execution.

## Why Research Is a Production Domain
- Research is a separate planning lane from analytics and backtesting.
- Research needs durable metadata and experiment descriptors.
- Research should remain deterministic and local-only until later execution-proof phases.

## Module Boundary Map
- `src/research/__init__.py`
- `src/research/contracts.py`
- `src/research/lanes.py`
- `src/research/experiments.py`
- `src/research/ablation.py`

## What Belongs in `src.research`
- Research-lane descriptors
- Experiment metadata
- Hypothesis records
- Ablation plan descriptors
- Deterministic local-only helpers

## What Must Not Cross the Boundary
- No DeepSeek/OpenAI/LLM calls
- No model training
- No scraping activation
- No live data pull
- No connector activation
- No external writes
- No dashboard rendering
- No `main.py` rewrite

## Future Migration Strategy
1. Move research lane descriptors and experiment metadata into `src.research`.
2. Keep legacy research stores/schema thin until migration proof is complete.
3. Defer any AI/LLM execution lane until `src.ai` is separately proven.
4. Keep analytics, data, and backtesting as the upstream foundations.

## Safety Guarantees
- Local-only deterministic objects and helpers.
- No network imports.
- No environment credential reads.
- No side effects at import time.
- No live production activation.
- No AI/LLM calls.
- No live data pull.
- No external writes.

## Required Statement
`src.research` is the canonical local-only research ownership boundary. This phase does not authorize AI/LLM calls, live data, brokerage, scraping, or execution behavior.
