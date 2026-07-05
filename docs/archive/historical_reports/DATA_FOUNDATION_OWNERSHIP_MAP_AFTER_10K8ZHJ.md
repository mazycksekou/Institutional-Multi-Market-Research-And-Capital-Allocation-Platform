# Data Foundation Ownership Map After 10K8ZHJ

## Canonical Owner

`src.data`

## Module Map

| Canonical Module | Responsibility | Notes |
| --- | --- | --- |
| `src/data/__init__.py` | Package export surface | Import-safe umbrella |
| `src/data/contracts.py` | Dataset and source descriptors | Pure dataclasses only |
| `src/data/metadata.py` | Metadata construction helpers | Local-only metadata assembly |
| `src/data/source_registry.py` | In-memory source registry | No persistent side effects |
| `src/data/validation.py` | Field and source validation | Deterministic validation helpers |
| `src/data/local_loader.py` | Local-only loader shell | Rejects remote/live sources |

## Ownership Notes

- Dataset metadata belongs here, not in services or API routes.
- Source registration belongs here, not in `automation_scheduler`.
- Validation belongs here as a pure local contract.
- Loader behavior is explicitly local-only and does not fetch from the network.

## What Is Not Owned Here

- live ingestion
- data download
- scraping
- storage migration
- analytics/reporting
- replay or simulation execution

