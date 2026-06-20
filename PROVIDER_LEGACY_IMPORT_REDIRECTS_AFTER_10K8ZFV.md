# Provider Legacy Import Redirects After 10K8ZFV

| Wrapper path | Redirect target | What now resolves canonically | Safe deletion phase |
| --- | --- | --- | --- |
| `providers/kalshi_provider.py` | `src.providers.prediction_markets.adapters.normalize_prediction_market_quote` | `normalize_kalshi_probability_market` delegates to canonical prediction-market normalization | after downstream callers move |
| `betting_providers/normalization.py` | `src.providers.prediction_markets.adapters` | `normalize_kalshi_event` and `normalize_kalshi_market` delegate to canonical prediction-market normalization | after legacy client/test redirection |
| `betting_providers/normalization.py` | `src.providers.sportsbooks.adapters` | `normalize_sportsbook_event` and `normalize_sportsbook_odds` delegate to canonical sportsbook normalization | after legacy client/test redirection |

## Wrapper Policy
Legacy import paths remain valid during migration. The wrappers are compatibility surfaces, not permanent architecture owners.

