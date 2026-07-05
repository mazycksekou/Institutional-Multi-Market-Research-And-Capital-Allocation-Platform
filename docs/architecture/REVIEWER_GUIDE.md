# Reviewer Guide

This guide is for business reviewers, technical partners, and investors who want to understand the repository quickly without reading the entire codebase.

## What the Platform Is

- A market-intelligence and analysis platform with canonical runtime ownership under `src/`
- A repository that separates runtime code, contracts, documentation, tests, and scripts
- A project that keeps proprietary implementation details private while exposing a vendor-neutral public contract

## What to Look At First

1. `docs/architecture/SYSTEM_OVERVIEW.md`
2. `docs/architecture/FINAL_REPOSITORY_STRUCTURE.md`
3. `docs/architecture/CANONICAL_OWNERSHIP_MAP.md`
4. `docs/contracts/CONTRACT_INDEX.md`
5. `docs/operations/VALIDATION_RUNBOOK.md`

## How to Validate the Repo

- Run the local governance scripts
- Run the smoke suite
- Review the architecture and contract docs
- Confirm the branch is clean before trusting a checkpoint

## What Is Production-Ready

- The repository structure is disciplined
- Governance checks are executable
- Public contract language is vendor-neutral
- Proprietary logic is kept behind internal ownership boundaries

## What Still Requires Care

- Any future live provider or broker integration
- Any schema-tightening that could break clients
- Any change to the public API contract

## What Reviewers Should Expect

- Clear ownership
- Clear validation
- Clear documentation of tradeoffs
- No hidden runtime behavior in docs or scripts
