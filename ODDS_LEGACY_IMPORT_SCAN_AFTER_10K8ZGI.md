# Odds Legacy Import Scan After 10K8ZGI

## Before Redirection
The remaining odds runtime consumer files owned their own odds metadata and did not reference the canonical disabled connector boundary.

## After Redirection
Each of the following files now imports `src.connectors.odds_data` metadata:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `src/providers/provider_router.py`

## Findings
- The canonical disabled odds connector boundary is import-safe.
- The legacy odds runtime modules remain importable.
- The redirection is additive and does not rely on import-time credential access.
- No deletion occurred.
- No live calls were made.
- No credentials were read at import time.

## Import-Scan Notes
- `src.connectors.odds_data` remains the canonical disabled landing zone.
- The runtime consumer files retain their live-method implementations for now.
- `providers.odds_provider_router.py` and `betting_providers.provider_router.py` remain deleted and are not reintroduced.

## Conclusion
The odds runtime consumer import scan now shows canonical connector references in the remaining legacy odds runtime surfaces, which is the proof step needed before later deletion work.
