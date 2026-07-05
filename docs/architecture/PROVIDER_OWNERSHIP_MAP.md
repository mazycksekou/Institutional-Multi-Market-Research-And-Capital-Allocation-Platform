# Provider Ownership Map

## Canonical Provider Responsibilities

| Provider responsibility | Canonical owner | Notes |
| --- | --- | --- |
| Provider contracts and registry | `src.providers` | Provider-facing API surface |
| Provider policy and allowlists | `src.providers` with security gates in `src.security` | Policy should not live in duplicate wrappers |
| Provider-facing adapters | `src.providers` and `src.connectors` | Keep adapters thin and explicit |
| Provider metadata and classification | `src.data` / `src.providers` | Use canonical data contracts for storage |

## Guidance

- A provider is not the same as a connector.
- A provider may be a data source, a model service, or another external boundary.
- If a provider-specific implementation starts to own reusable behavior, promote that reusable behavior into the correct canonical package rather than duplicating it.
