# AI/LLM File Inventory After 10K8ZI6

| File | Classification | Import-time credential read | Live call risk | Future canonical target |
| --- | --- | --- | --- | --- |
| `automation_scheduler/ai_provider_security.py` | `AI_CREDENTIAL_RISK` | No | No | `src.ai.readiness` |
| `automation_scheduler/advanced_red_team_provider_policy.py` | `AI_CREDENTIAL_RISK` | No | No | `src.ai.prompt_policy` |
| `automation_scheduler/security_policy.py` | `AI_ADJACENT_METADATA_ONLY` | No | No | `src.ai.contracts` |
| `automation_scheduler/security_readiness_report.py` | `AI_ADJACENT_METADATA_ONLY` | No | No | `src.ai.readiness` |
| `automation_scheduler/deepseek_prompt_contracts.py` | `AI_PROMPT_TEMPLATE_ONLY` | No | No | `src.ai.prompt_policy` |
| `automation_scheduler/deepseek_response_validator.py` | `AI_ADJACENT_METADATA_ONLY` | No | No | `src.ai.contracts` |
| `automation_scheduler/deepseek_daily_report.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` + `src.ai` later |
| `automation_scheduler/deepseek_disagreement_queue.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` + `src.ai` later |
| `automation_scheduler/deepseek_data_pull_check.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` + `src.services` later |
| `automation_scheduler/deepseek_reviewer.py` | `AI_RUNTIME_CALL_RISK` | Yes (runtime) | Yes | `src.ai.disabled_client` later |
| `automation_scheduler/deepseek_profit_lab.py` | `AI_RUNTIME_CALL_RISK` | Yes (runtime) | Yes | `src.ai.disabled_client` later |
| `automation_scheduler/institutional_deepseek_review.py` | `AI_RUNTIME_CALL_RISK` | Yes (runtime) | Yes | `src.services` + `src.ai` later |
| `automation_scheduler/advanced_red_team_report.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.analytics` / `src.ai` later |
| `automation_scheduler/baseball_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/basketball_player_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/combat_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/football_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/extreme_signal_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/golf_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/hockey_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/soccer_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/tennis_impact_red_team.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/cross_asset_embedding_router.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/contrastive_embedding_diagnostics.py` | `AI_RESEARCH_LANE_ONLY` | No | No | `src.research` |
| `automation_scheduler/model_recheck_runner.py` | `MIGRATE_TO_SRC_SERVICES_LATER` | No | No | `src.services` |
| `src/api/automation_deepseek_routes.py` | `MIGRATE_TO_SRC_SERVICES_LATER` | No | No | `src.services` |
| `main.py` | `UNSAFE_TO_TOUCH` | Yes | No | keep as bootstrap shell |
| `config.py` | `AI_CREDENTIAL_RISK` | Yes | No | future config boundary |
| `src/providers/policy/allowlist.py` | `AI_ADJACENT_METADATA_ONLY` | No | No | `src.ai.contracts` |
| `src/providers/policy/secret_policy.py` | `AI_CREDENTIAL_RISK` | No | No | `src.ai.readiness` |

