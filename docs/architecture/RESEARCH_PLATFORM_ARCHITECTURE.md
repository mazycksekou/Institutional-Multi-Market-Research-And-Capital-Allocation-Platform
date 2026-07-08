
# Research Platform Architecture

## Workspace Scope

The research workspace supports:

- experiments
- feature studies
- provider evaluations
- market studies
- walk-forward studies
- ablation studies

## Artifact Layout

| Area | Purpose |
| --- | --- |
| `data/research/experiments/` | Experiment runs and outputs. |
| `data/research/provider_evaluations/` | Provider comparison studies. |
| `data/research/market_studies/` | Market-specific research artifacts. |
| `data/research/walk_forward/` | Time-ordered validation studies. |
| `data/research/ablation/` | Ablation artifacts and summaries. |

## Runtime Asset Framework

The runtime-facing research asset implementation framework lives in [Research Asset Implementation Framework](./RESEARCH_ASSET_IMPLEMENTATION_FRAMEWORK.md).

The research workspace remains the place for experiment and evidence artifacts.
It does not own the canonical runtime registry, which stays with the shared `src.*` owners and the governing architecture docs.

## Rules

- Research outputs must pin dataset and feature-pack versions.
- Research artifacts should be reproducible without requiring live providers.
- The workspace can consume registry metadata, but it must not own the canonical registry itself.
