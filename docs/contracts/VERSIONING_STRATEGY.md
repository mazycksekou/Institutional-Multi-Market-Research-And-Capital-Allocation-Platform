
# Versioning Strategy

## Versioned Surfaces

The repository version-controls the following surfaces:

- datasets
- feature packs
- schemas
- provider mappings
- model inputs
- backtest rows
- Streamlit layouts

## Rules

| Surface | Version key | Change rule |
| --- | --- | --- |
| Datasets | `dataset_version` | Bump when content, schema, or normalization changes. |
| Schemas | `schema_version` | Bump on incompatible structure changes. |
| Feature packs | `feature_pack_version` | Bump when inputs, transforms, or semantics change. |
| Provider mappings | `provider_map_version` | Bump when source-to-field mapping changes. |
| Model inputs | `model_input_version` | Bump when model-ready input shape changes. |
| Backtest rows | `backtest_row_version` | Bump when replay semantics or leakage protection changes. |
| Streamlit layouts | `layout_version` | Bump when dashboard layout or widget contracts change. |

## Compatibility Policy

- Backward-compatible additions may retain the major version.
- Incompatible changes require a major version bump and a migration note.
- Consumers must declare accepted version ranges explicitly.
- No anonymous changes: every published artifact must carry a version id.
