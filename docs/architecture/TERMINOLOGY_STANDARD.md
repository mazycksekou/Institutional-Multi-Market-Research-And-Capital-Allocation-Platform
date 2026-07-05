# Terminology Standard

## Purpose
This repository uses a shared terminology policy so that wording stays consistent without collapsing distinct responsibilities into the same label.

## Canonical Meanings

### Public API contract
The external machine-readable API interface exposed to clients.

### Client integration
Any external system, script, dashboard, workflow, or consumer that calls the platform.

### Model provider
A company, service, local runtime, or internal engine that provides model inference.

### Data provider
A source of market, sports, odds, financial, contextual, or other reference data.

### Connector
A module that retrieves, normalizes, or interfaces with an external data or service source.

### Adapter
A compatibility layer that translates one interface into another.

### Provider adapter
A bridge between provider-specific behavior and canonical internal contracts.

### Model runtime
The execution environment or service responsible for running inference.

### Analysis route
A public or internal API route that returns platform analysis.

### Market Intelligence Platform
The platform as a whole.

### Proprietary model logic
Internal algorithms, features, weights, calibration, ranking, scoring, and decision logic that are not exposed by the public API.

## Terms That Must Not Be Collapsed

### provider
This can mean a data provider, a model provider, a sportsbook provider, or a connector provider. Keep the meaning tied to the local context.

### model
This can mean an ML model, a data model, a schema model, or a business model. Do not standardize blindly.

### runtime
This can mean app runtime, model runtime, deployment runtime, or execution runtime. Preserve the specific meaning.

### connector
This can mean a data connector, API connector, broker connector, feed connector, or integration adapter. Preserve the specific meaning.

### client
This can mean an external client, an HTTP client, or a language-model client. Preserve the specific meaning.

### action
This can mean an API action, an automation action, or a user action. Preserve the specific meaning.

### OpenAPI
The API specification standard. OpenAPI is not OpenAI.

## Standardization Guidance
- Standardize public-facing wording when the meaning is clear and no code identifier is affected.
- Keep package names, class names, function names, import paths, and filenames unchanged unless a safe refactor has been validated.
- Preserve historical records and technical compatibility references when they are factual and useful.
- Use neutral platform wording in public docs:
  - public API contract
  - client integration
  - model provider
  - data provider
  - analysis route
  - market intelligence platform

## Examples
- `Custom GPT Actions` -> `public API contract`
- `GPT route` -> `analysis route`
- `ChatGPT integration` -> `client integration`
- `OpenAI-specific client` -> `external client`
- `vendor runtime` -> `model runtime`
- `proprietary provider` -> `model provider`
- `inference provider` -> `model provider`
- `external AI service` -> `external model provider`

## Notes
- Historical archives may preserve older vendor or product wording as evidence.
- Tests may intentionally assert that banned branding terms do not appear in the public contract.
- Code identifiers should not be renamed for wording preference alone.

