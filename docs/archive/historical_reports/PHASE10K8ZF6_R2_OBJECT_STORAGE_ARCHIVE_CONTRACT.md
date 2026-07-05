# PHASE10K8ZF6 Local Data Object Storage Archive Contract + R2 Credential Policy

## Executive Summary
10K8ZF6 defines the Local Data Object Storage Archive Contract before any R2 upload adapter, end-of-day upload job, duplicate-code cleanup, source migration, controlled data loader, backtest runner, footprint implementation, ORB integration, or results UI.

This phase is documentation, contract, and safety-test only.

This R2 Object Storage Archive Contract establishes the canonical archive policy for the next implementation phases.

The operating rule is simple:
- R2 object storage is the archive layer.
- R2 is not the live application database.
- do not upload thousands of tiny JSON files.
- aggregate raw JSON into daily archive bundles.
- one object per date/source/market bundle.
- manifest required before upload.
- upload verification required before local deletion.
- local deletion is off by default.

10K8ZF6 performs no upload.
R2 credentials are first used by implementation phases 10K8ZF8 and 10K8ZF9.

## Current HEAD
Current HEAD before this phase: `72181ac8f6304988174deaba011777e31b8b22e0`

## Product Decision
The product decision is to treat local market data as a staged archive workload, not as live application storage.

This means:
- local data may be bundled for later archival
- archive metadata must be explicit and auditable
- destructive cleanup is blocked until verification gates pass
- implementation must stay out of core math, risk, signals, metrics, backtester, and dashboard code

## R2 Object Storage Role
R2 object storage is the archive layer for large local market data bundles.

R2 is appropriate for:
- compressed daily archive bundles
- immutable historical archive objects
- manifest-driven retention workflows

R2 is not appropriate for:
- live application state
- transaction processing
- database-style random reads and writes
- per-row or per-file tiny-object fanout

## Not a Database Boundary
R2 is not the live application database.

The repository must not treat object storage as a substitute for:
- source-of-truth runtime state
- relational query storage
- backtest execution state
- deterministic fixture data

The archive layer is for export and preservation, not for live computation.

## Local Data Context
The repo already contains local-only trees such as:
- `data/`
- `reports/`

Per the current repository policy, those trees are ignored local artifacts and may contain generated outputs, runtime state, historical bundles, or audit material.

They are not product source code.
They must be reviewed before any cleanup, but not deleted in this phase.

## Archive Eligibility Rules
Data is eligible for future archive when it is:
- local-only market data output
- generated raw JSON suitable for bundling
- not required as a deterministic test fixture
- not used by core math or strategy code paths
- not the canonical source for live runtime state

Eligible content should generally be bundled by:
- trading date
- source
- market
- environment

## Non-Archive / Must-Keep Rules
Data is not eligible for archive when it is:
- deterministic test input
- a tiny fixture required by tests
- a source file or code asset
- a live runtime dependency
- a canonical local state file used by a deterministic workflow

Keep these categories local until a later migration decision explicitly changes them:
- deterministic fixtures
- test-owned fixture files
- essential local config without credentials

## Deterministic Fixture Policy
Only tiny deterministic fixtures belong in tests/fixtures/.
only tiny deterministic fixtures belong in tests/fixtures/.

Fixtures that are part of deterministic tests must stay local to the test suite and must not be swept into the archive workflow just because they look like generated data.

## Daily Archive Bundle Format
The daily archive bundle format should be a compressed JSON Lines bundle, typically `jsonl.gz`, with a manifest recorded alongside it.

This keeps the archive format:
- append-friendly at generation time
- easy to validate by count and checksum
- compact enough to avoid thousands of tiny objects

The intended behavior is to aggregate raw JSON into daily archive bundles before upload.

## Object Key Naming Convention
Use this object key pattern:

`market-data/{environment}/{source}/{market}/{yyyy}/{mm}/{dd}/{bundle_name}.{ext}`

Example:

`market-data/local/theoddsapi/nba/2026/01/31/theoddsapi_nba_2026-01-31.jsonl.gz`

This convention encodes:
- environment
- source
- market
- trading date
- bundle identity
- archive extension

## Archive Manifest Contract
Every archive bundle must have a manifest.

Required manifest fields:
- `archive_id`
- `environment`
- `source`
- `market`
- `trading_date`
- `archive_format`
- `local_archive_path`
- `r2_bucket_alias`
- `r2_object_key`
- `source_file_count`
- `source_byte_count`
- `archive_byte_count`
- `checksum_algorithm`
- `checksum`
- `created_at_utc`
- `uploaded_at_utc`
- `upload_status`
- `verification_status`
- `deletion_eligible`
- `deletion_performed`
- `notes`

Manifest policy:
- manifest required before upload
- manifest should record source provenance
- manifest should record checksum and object size
- manifest should record upload and verification timestamps
- manifest should record deletion state transitions
- manifest is the audit trail for archive lifecycle decisions

## Upload Verification Contract
Upload verification required before local deletion.

Verification should confirm:
- the remote object key exists
- the remote object size matches the archive byte count or an equivalent trusted size check
- the checksum or checksum-equivalent verification passed
- the manifest upload status is marked successful
- the manifest verification status is marked successful

If verification fails, the archive remains local.

## Local Deletion Eligibility Contract
Local deletion is off by default.

Deletion may be considered only when all of the following are true:
- source file is ignored by git
- source file is listed in manifest
- archive was created successfully
- upload completed successfully
- remote object verification passed
- checksum or size verification exists
- source file is not referenced by tests
- source file is not under tests/fixtures/
- source file is not required for deterministic test runs
- user explicitly enables cleanup mode

If any gate fails, deletion is blocked.

## R2 Credential Timing
R2 credentials are first used by implementation phases 10K8ZF8 and 10K8ZF9.

10K8ZF6 documents the policy only.
10K8ZF6 performs no upload.
10K8ZF6 does not require real credentials.

## Required R2 Environment Variables
The later implementation phases should expect these environment variables:
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`

These names are examples of the future contract only.
Real values belong only in local environment variables or ignored local config.

## Credential and Secret Policy
Credentials and secrets must obey these rules:
- credentials must come from environment variables or ignored local config only
- do not commit R2 access keys
- do not commit secret keys
- do not commit tokens
- do not commit credential files
- do not paste real R2 credentials into source code
- do not paste real R2 credentials into README examples
- do not paste real R2 credentials into tests
- do not paste real R2 credentials into committed config

Credential files and local secret files must never be committed.

## Code Ownership Boundary
The archive contract must not be implemented inside:
- core math
- risk logic
- signals
- metrics
- backtester
- dashboard

Those layers must stay free of direct R2 client dependencies.
- core math must not import R2 clients directly
- risk logic must not import R2 clients directly
- signals must not import R2 clients directly
- metrics must not import R2 clients directly
- backtester must not import R2 clients directly
- dashboard must not import R2 clients directly

## Future src/storage Boundary
Future R2 adapter code belongs behind src/storage/ or a storage-provider boundary.
future R2 adapter belongs behind src/storage/ or a storage-provider boundary.

That boundary should own:
- archive contracts
- manifest helpers
- upload verification helpers
- deletion-gate helpers
- provider-specific object storage plumbing

## Future scripts Boundary
End-of-day archive scripts belong in scripts/.
end-of-day archive scripts belong in scripts/.

Future scripts may orchestrate:
- bundle creation
- manifest generation
- dry-run validation
- upload verification
- cleanup gating

They must not be placed in core math, risk, signals, metrics, backtester, or dashboard files.

## Forbidden Imports Boundary
The following layers must never import R2 clients directly:
- core math
- risk logic
- signals
- metrics
- backtester
- dashboard

The archive adapter must be isolated behind storage boundaries so those layers remain pure and testable.

## End-of-Day Archive Flow
Safe end-of-day flow:
1. collect local raw JSON from the approved local data tree
2. validate that the data is eligible for archive
3. aggregate raw JSON into daily archive bundles
4. write the archive bundle and manifest locally
5. run dry-run validation
6. upload the bundle
7. verify the remote object
8. record verification status in the manifest
9. only then decide whether deletion is eligible

The implementation phase must preserve a dry-run mode.
dry-run mode required for implementation phase
No real upload in 10K8ZF6.
no real upload in 10K8ZF6
No local deletion in 10K8ZF6.
no local deletion in 10K8ZF6

## Failure and Retry Policy
Failures should be non-destructive.

If upload or verification fails:
- keep local data
- retain the manifest
- mark the status as failed or pending review
- require an explicit retry

Retry behavior should be idempotent at the archive-object and manifest level where possible.

## Audit Log / Manifest Policy
The manifest is the archive audit log.
The archive manifest is the audit log.

It should preserve:
- checksum
- object key
- object size
- upload timestamp
- source file count
- source byte count
- verification state
- deletion state

This creates a deterministic record for future cleanup review and provenance audits.

## Pre-Backtest Cleanup Impact
Pre-backtest cleanup must finish before controlled data loader or backtest runner.
pre-backtest cleanup must finish before controlled data loader or backtest runner.

That means archive work can help reduce clutter, but it must not remove data needed by:
- deterministic tests
- controlled data loader preparation
- backtest replay
- local audit trails

The cleanup boundary must be proven, not assumed.

## Next Phase Recommendation
Proceed to 10K8ZF7 Daily Data Aggregation Script

## Non-Negotiable Safety Notes
- no broker execution
- no real trade execution
- no live connectors
- no API calls without explicit provider phase
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF6
