# Data Source Registry Map After 10K8ZHJ

## Registry Scope

The registry is intentionally in-memory and local-only.

## Current API

- `register_local_source()`
- `list_local_sources()`
- `get_local_source()`
- `reset_local_source_registry()`
- `LocalSourceRegistry`

## Registry Rules

- only local sources may be registered
- remote/live sources are rejected
- no credentials are read
- no network access is attempted
- no persistence is performed

## Expected Registry Usage

The registry is the canonical place to describe local dataset source
availability before backtesting, analytics, or research layers consume it.

