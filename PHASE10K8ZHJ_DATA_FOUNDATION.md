# PHASE 10K8ZHJ Data Foundation

## Executive Summary

This phase creates the first canonical `src.data` foundation while keeping the
repo fully local-only and behavior-preserving. The new package owns dataset
contracts, metadata, source registry helpers, validation helpers, and a
local-only loader shell.

## Current HEAD

Starting HEAD for this phase:

`a3c48605cf28a84eeeb2d80fcbd19e2ce0abe17a`

## Why `src.data` Exists

`src.data` is the canonical home for:

- local dataset contracts
- dataset metadata
- source registry helpers
- validation helpers
- local-only loader boundaries

It is intentionally separate from `src.backtesting`, `src.core`, `src.services`,
`src.analytics`, and `src.research`.

## What This Phase Does Not Do

- no live data activation
- no network calls
- no credential reads
- no scraping
- no external writes
- no database migration
- no data download
- no AI/LLM implementation
- no brokerage/live execution

## Files Created

- `src/data/__init__.py`
- `src/data/contracts.py`
- `src/data/metadata.py`
- `src/data/source_registry.py`
- `src/data/validation.py`
- `src/data/local_loader.py`

## Import-Safety Guarantees

- `src.data` imports without network dependencies.
- local-only loaders reject remote/live sources.
- registry helpers are in-memory only.
- validation is deterministic and local-only.

## Validation Summary

The foundation exposes enough structure to:

- create dataset metadata
- register and list local sources
- reject remote/live source descriptors in the local loader
- detect missing metadata fields

## Test Summary

The phase proof test validates import safety, local registry behavior, local
loader rejection of non-local sources, and missing-field validation.

## Next Recommended Phase

Continue with `src.backtesting` foundation work, then move toward analytics and
research ownership mapping.
