# System Overview

The repository implements a market-intelligence and analysis platform with canonical runtime ownership under `src/`.

## What the System Does

- Ingests or models market, sports, odds, and related reference data through canonical data contracts
- Provides public API surfaces for analysis and operational access
- Supports backtesting, research, governance, and dashboard presentation
- Keeps proprietary implementation details private behind internal modules and local validation

## How the Repository Is Organized

- `src/` contains runtime/application code and runtime assets
- `tests/` contains automated validation
- `scripts/` contains local validation and operational tooling
- `docs/` contains architecture, contracts, operations, reports, and historical archives
- Root entrypoints remain thin and only dispatch into canonical `src.*` modules

## What New Contributors Should Know

- Do not create duplicate ownership for the same responsibility
- Do not add vendor-branded public wording unless a factual historical reference is required
- Do not expose proprietary logic in public contracts or docs
- Prefer reuse and promotion of existing canonical code over creating parallel systems

## Proprietary Boundary

- Public docs and contracts may describe the platform interface
- Internal algorithms, feature engineering, model weights, calibration, and decision logic remain private to the runtime packages
- Validation should prove behavior without revealing implementation details

## Where to Start

- Architecture map: `docs/architecture/FINAL_REPOSITORY_STRUCTURE.md`
- Terminology policy: `docs/architecture/TERMINOLOGY_STANDARD.md`
- OpenAPI governance: `docs/architecture/OPENAPI_CONTRACT_GOVERNANCE.md`
- Repository governance: `docs/architecture/DOCUMENTATION_GOVERNANCE.md`
