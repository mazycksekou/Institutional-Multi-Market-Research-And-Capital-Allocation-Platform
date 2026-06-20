# LEGACY_DELETE_AND_SHIM_QUEUE_AFTER_10K8ZFS

## Executive Summary
This queue separates temporary shims, delete-later candidates, and modules that must stay intact until migration proof exists. It is a planning artifact only. No deletion is authorized in this phase.

## Temporary Shim Candidates
- `betting_providers/provider_router.py`
- `betting_providers/__init__.py`
- `providers/odds_provider_router.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `providers/base_provider.py`
- `automation_scheduler/provider_*`
- `automation_scheduler/kalshi_*`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `kalshi_client.py`
- `sharp_client.py`

These should stay as thin compatibility layers until importer scans and wrapper tests are clean.

## Delete After Migration
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `providers/odds_provider_router.py`
- `kalshi_client.py`
- `sharp_client.py`
- `automation_scheduler/provider_contracts.py` after canonical replacement
- `automation_scheduler/provider_registry.py` after canonical replacement
- `automation_scheduler/provider_health.py` after canonical replacement
- `automation_scheduler/provider_adapter_base.py` after canonical replacement
- `automation_scheduler/provider_normalization_contract.py` after canonical replacement
- `automation_scheduler/provider_payload_validator.py` after canonical replacement
- `automation_scheduler/provider_secret_policy.py` after canonical replacement
- `automation_scheduler/provider_allowlist.py` after canonical replacement
- `automation_scheduler/provider_write_firewall.py` after canonical replacement
- `automation_scheduler/kalshi_adapter_contract.py` after canonical replacement
- `automation_scheduler/sportsbook_adapter_contract.py` after canonical replacement

## Delete Only After Tests Are Rewritten
- `tests/test_kalshi_*`
- `tests/test_sharp_*`
- `tests/test_sportsbook_*`
- any provider-specific tests that hard-code vendor ownership instead of category ownership

## Not To Be Deleted Yet
- `main.py`
- `src/api/provider_status_routes.py`
- `src/api/model_card_service.py`
- `src/services/enrichment_service.py`
- `screenshot_intake.py`
- `src/providers/*` scaffolds
- `src/ai/*` scaffolds
- `src/brokerage/*` scaffolds
- `src/connectors/*` scaffolds

## Non-Goal But Still Need Proof Before Deletion
- AI/vendor policy references such as `automation_scheduler/ai_provider_security.py`
- brokerage/execution scaffolds such as `automation_scheduler/institutional_execution_desk.py`
- connector/source adapters such as `automation_scheduler/nfl_open_data_adapters.py`

These should be transported into their new production boundaries, not deleted.

## Legacy Vendor Docs To Rewrite
- `README.md` sections that still frame vendor names as architecture owners
- `.env.example` vendor-specific environment keys where they appear as primary ownership
- historical phase docs that should now point to product-category and production-boundary ownership instead of vendor ownership

## Legacy Vendor Tests To Rename Or Generalize
- `tests/test_kalshi_*`
- `tests/test_sharp_*`
- `tests/test_sportsbook_*`
- any test that depends on a vendor-specific string when a product-category assertion would be more stable

## Queue Rules
1. Add a shim before removing a working legacy path.
2. Rewrite tests before deleting the vendor module they target.
3. Never delete a compatibility surface until importer scans are clean.
4. Keep the future production domains as scaffolds, not deletion candidates.

## Outcome Goal
Delete only after dependency proof, test redirection, and safe replacement are complete.
