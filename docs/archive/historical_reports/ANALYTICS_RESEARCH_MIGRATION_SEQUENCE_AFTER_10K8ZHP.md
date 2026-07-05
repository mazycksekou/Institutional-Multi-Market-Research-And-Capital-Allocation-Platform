# Analytics/Research Migration Sequence After 10K8ZHP

1. Move analytics summaries and governance reporting into `src.analytics`.
2. Move research lane descriptors, experiment metadata, and ablation planning into `src.research`.
3. Keep `model_governance` enforcement gates thin until later proof.
4. Keep AI-adjacent research lanes deferred until `src.ai` is separately proven.
5. Redirect service-layer consumers to the canonical `src.analytics` and `src.research` surfaces.
6. Reclassify wrapper-only legacy files only after import and test proof.

## Deletion Readiness
- No deletion is authorized in this phase.
- Compatibility and proof history remain the blockers to deletion.
