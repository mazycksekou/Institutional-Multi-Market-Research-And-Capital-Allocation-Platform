# PHASE10K8ZF7 R2 Archive Pipeline: Bundle + Upload + Verify + Delete Verified Local Raw Data

## Executive Summary
10K8ZF7 implements the gated storage pipeline for local market data archiving.

This phase covers:
- local-only dry-run
- bundle mode writes local jsonl.gz archive and manifest
- upload mode requires explicit --upload
- verify mode checks remote object metadata
- cleanup-plan mode marks eligibility only
- cleanup mode is explicit and gated
- no cleanup runs by default
- verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed

The intended end state is R2 transfer verified and eligible local raw/generated data removed from local storage.
the intended end state is R2 transfer verified and eligible local raw/generated data removed from local storage

## Current HEAD
Current HEAD: `3403493`

## Purpose
Create a safe, auditable R2 archive pipeline that can bundle raw JSON, write a manifest, upload to object storage, verify the remote object, and delete verified local raw/generated files only after explicit cleanup approval.

scripts/r2_archive_pipeline.py

## Scope
The pipeline owns:
- local bundle generation
- manifest generation
- sha256 checksum calculation
- R2 upload adapter boundary
- remote verification
- cleanup-plan marking
- verified local deletion of eligible raw/generated files

## Non-Goals
This phase does not add:
- broker execution
- real trade execution
- live connectors
- scraper actions
- controlled data loader behavior
- backtest runner behavior
- footprint implementation
- ORB integration
- results UI
- database writes without explicit storage phase

## Relationship to 10K8ZF6
10K8ZF6 defined the archive contract and credential policy.
10K8ZF7 implements the first gated pipeline behind that contract.
10K8ZF7 uses local environment variables only and keeps real credentials out of source control.

## Pipeline Modes
- local-only dry-run
- bundle
- manifest-only
- upload
- verify
- cleanup-plan
- cleanup

## Dry-Run Mode
Dry-run mode writes nothing.
It scans candidate local JSON files, computes the planned archive shape, and records skipped files without creating archive output.

## Bundle Mode
bundle mode writes local jsonl.gz archive and manifest.
It aggregates raw JSON into compressed JSONL and writes the archive manifest beside it.
compressed JSONL

## Manifest-Only Mode
manifest-only mode writes the archive manifest without writing the archive bundle.
It is safe for path planning and dry verification of manifest shape.

## Upload Mode
upload mode requires explicit --upload.
It uses R2 credentials from environment variables only and refuses to upload if those variables are missing.

## Verify Mode
verify mode checks remote object metadata.
It confirms the remote object exists and compares the returned object size to the local archive size when available.

## Cleanup-Plan Mode
cleanup-plan mode marks eligibility only.
It does not delete local files and it does not modify source code, tests, fixtures, manifests, or archive files.

## Verified Cleanup Mode
cleanup mode is explicit and gated.
Verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed.

## Archive Output Contract
Required local archive path convention:
- archives/local/{source}/{market}/{yyyy}/{mm}/{dd}/{bundle_name}.jsonl.gz

Required object key policy:
- market-data/{environment}/{source}/{market}/{yyyy}/{mm}/{dd}/{bundle_name}.{ext}
- market-data/local/theoddsapi/nba/2026/01/31/theoddsapi_nba_2026-01-31.jsonl.gz

## Manifest Output Contract
archive manifest
Required manifest output path convention:
- reports/archive_manifests/{archive_id}.json

Required manifest fields:
- archive_id
- environment
- source
- market
- trading_date
- archive_format
- local_archive_path
- r2_bucket_alias
- r2_object_key
- source_file_count
- source_byte_count
- archive_byte_count
- checksum_algorithm
- checksum
- created_at_utc
- uploaded_at_utc
- upload_status
- verification_status
- deletion_eligible
- deletion_performed
- deletion_allowed_by_user
- deletion_completed_at_utc
- deleted_source_file_count
- deleted_source_byte_count
- notes
- source_files
- skipped_invalid_json_count
- skipped_files

Default manifest state before upload:
- uploaded_at_utc is null before upload
- upload_status is not_uploaded before upload
- verification_status is not_verified before verification
- deletion_eligible is false before cleanup-plan
- deletion_performed is false by default

## R2 Adapter Boundary
src/storage/archive_manifest.py owns the manifest schema, archive path helpers, object key construction, checksum helpers, and cleanup-gate validation.

src/storage/r2_archive_adapter.py owns the R2 client boundary and keeps boto3 isolated to one file.
boto3 import is isolated to src/storage/r2_archive_adapter.py

## Credential Safety
R2 credentials come from environment variables only.
do not commit R2 access keys
do not commit secret keys
do not commit tokens
Do not commit R2 access keys.
Do not commit secret keys.
Do not commit tokens.
Do not commit credential files.

The implementation must not paste real R2 credentials into source code.

## JSON Handling Rules
The pipeline scans local JSON files recursively from the approved input directory.
It tolerates JSON objects by writing one JSONL line.
It tolerates JSON arrays by writing each array item as one JSONL line.
It records provenance fields in each JSONL line.

Required provenance fields:
- _source_file
- _archive_id
- _trading_date
- _source
- _market
- _environment

## Invalid JSON Handling
Invalid JSON is tolerated and recorded.
The pipeline increments skipped_invalid_json_count and records skipped_files instead of failing the whole bundle.

## Checksum Policy
sha256 is the archive checksum policy.
Archive manifests record checksum_algorithm and checksum for the local archive bundle.

## Object Key Policy
Required object key convention:
- market-data/{environment}/{source}/{market}/{yyyy}/{mm}/{dd}/{bundle_name}.{ext}

Example object key:
- market-data/local/theoddsapi/nba/2026/01/31/theoddsapi_nba_2026-01-31.jsonl.gz

## Upload Verification Policy
verify mode checks remote object metadata.
The pipeline should confirm the object exists and compare remote content length to the local archive size when available.

## Deletion Safety
Deletion is off by default.
Deletion only occurs after:
- upload succeeded
- verification succeeded
- cleanup-plan marked the bundle eligible
- --cleanup is explicitly passed
- --allow-delete-local-raw is explicitly passed

The pipeline must not delete source code, manifests, archives, fixtures, tracked source files, or files outside the approved input directory.

## Final Local Storage Outcome
The intended end state is R2 transfer verified and eligible local raw/generated data removed from local storage.
Fixtures, source code, and archive/manifest artifacts remain preserved unless a later explicit policy changes that.

## Code Ownership Boundary
core math must not import R2 clients directly.
risk logic must not import R2 clients directly.
signals must not import R2 clients directly.
metrics must not import R2 clients directly.
backtester must not import R2 clients directly.
dashboard must not import R2 clients directly.

Future R2 adapter belongs behind src/storage/ or a storage-provider boundary.
End-of-day archive scripts belong in scripts/.
Only tiny deterministic fixtures belong in tests/fixtures/.

## Test Coverage
The focused phase test covers:
- required file existence
- forbidden import checks
- module API presence
- dry-run behavior
- bundle behavior
- manifest-only behavior
- upload behavior with a mocked client
- verify behavior with a mocked client
- cleanup-plan behavior
- verified cleanup behavior in tmp_path

## Acceptance Results
This phase is designed to be accepted only after targeted pytest, full test, smoke, and stat checks pass.

The implementation must also avoid:
- no pandas import
- no pyarrow import
- no streamlit import
- no fastapi import
- no requests import
- no broker execution
- no real trade execution
- no live connectors
- no scraper actions
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language

implementation reviewed in 10K8ZF7

## Next Phase Recommendation
Proceed to 10K8ZF8 R2 Transfer Proof Review + Local Storage Clearance Report
