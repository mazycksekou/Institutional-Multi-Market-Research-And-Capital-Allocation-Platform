# AI Scheduler Blocker Map After 10K8ZI8

| File | Classification | Reason |
| --- | --- | --- |
| `automation_scheduler/ai_provider_security.py` | `AI_CREDENTIAL_RISK` | Reads AI env values and governs provider selection. |
| `automation_scheduler/advanced_red_team_provider_policy.py` | `AI_CREDENTIAL_RISK` | Reads env config for deepseek/openai red-team selection. |
| `automation_scheduler/deepseek_reviewer.py` | `AI_RUNTIME_CALL_RISK` | Performs live HTTP client calls. |
| `automation_scheduler/deepseek_profit_lab.py` | `AI_RUNTIME_CALL_RISK` | Performs live HTTP client calls and reads API keys. |
| `automation_scheduler/institutional_deepseek_review.py` | `AI_RUNTIME_CALL_RISK` | Performs live HTTP client calls. |
| `automation_scheduler/deepseek_prompt_contracts.py` | `PROMPT_TEMPLATE_ONLY` | Prompt strings only. |
| `automation_scheduler/deepseek_response_validator.py` | `RESEARCH_METADATA_ONLY` | Deterministic redaction / validation helpers only. |
| `automation_scheduler/advanced_red_team_report.py` | `RESEARCH_METADATA_ONLY` | Deterministic report assembly only. |
| `automation_scheduler/cross_asset_embedding_router.py` | `RESEARCH_METADATA_ONLY` | Deterministic routing metadata only. |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | `RESEARCH_METADATA_ONLY` | Deterministic fallback diagnostics only. |
| `automation_scheduler/baseball_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/basketball_player_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/combat_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/football_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/extreme_signal_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/golf_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/hockey_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/soccer_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/tennis_impact_red_team.py` | `RESEARCH_METADATA_ONLY` | Red-team metadata only. |
| `automation_scheduler/model_recheck_runner.py` | `MIGRATE_TO_SRC_SERVICES_LATER` | Deterministic model-evaluation orchestration. |
| `src/api/automation_deepseek_routes.py` | `MIGRATE_TO_SRC_SERVICES_LATER` | Route exposure only. |
| `main.py` | `UNSAFE_TO_TOUCH` | Bootstrap wiring still imports AI-adjacent routes. |

No scheduler activation occurred in this phase.
No AI/LLM calls occurred.
No deletion occurred.
automation_scheduler remains a decommission target.
DELETE_CANDIDATE_AFTER_PROOF is not claimed in this phase.
