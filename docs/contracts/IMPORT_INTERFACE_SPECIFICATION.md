
# Import Interface Specification

## Supported Sources

- CSV
- JSON
- Parquet
- SQLite
- DuckDB
- USB folders
- Python modules
- HTTP APIs (disabled)
- compressed archives
- future streaming

## Interface Contract

The import layer should expose a small source-agnostic interface:

- source descriptor
- dataset target
- validation policy
- import result
- provenance record

## Design Rules

- No provider-specific logic in the import interface.
- HTTP API support remains disabled until explicitly enabled by a future phase.
- Imported payloads must move through validation before they are made visible to consumers.
- Archive imports must unpack into the same validation pipeline as direct file imports.

## Suggested Source Descriptor Fields

| Field | Meaning |
| --- | --- |
| `source_kind` | CSV, JSON, Parquet, SQLite, DuckDB, USB, Python, archive, streaming. |
| `source_uri` | Location of the source asset. |
| `dataset_id` | Canonical dataset target. |
| `provider` | Provider label. |
| `market` | Market family. |
| `schema_version` | Expected schema version. |
| `import_mode` | Full, incremental, backfill, replay. |
| `validation_policy` | Required validation preset. |
