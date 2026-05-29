# Local Outcome Ingestion Template

Use this guide when adding real local settlement/outcome records for paper-decision calibration.

Safety rules:
- Use only real settled, void, or cancelled outcomes from a trusted local/manual or imported-file source.
- Do not use `test_fixture` as a real outcome source.
- Do not infer outcomes from current prices, last traded prices, bid/ask quotes, or model scores.
- Prefer `decision_id` or `review_item_id` when available so matching is exact.
- Local ingestion writes only local outcome files; `provider_write` must remain `false`.
- Outcome ingestion does not enable trading, order placement, execution, auto-betting, or auto-trading.

Required fields:
- `provider`
- `market_type`
- At least one matching key: `decision_id`, `review_item_id`, `contract_id`, `ticker`, or `run_id` plus `ticker`/`contract_id`
- `outcome_status`: `settled`, `void`, or `cancelled`
- `final_outcome`: `yes`, `no`, `win`, `loss`, `push`, or `void`
- `settled_at`: ISO-8601 timestamp in the past
- `source`: `local_manual` or `imported_file`

Dry-run validation:

```json
{
  "dry_run": true,
  "records": [
    {
      "provider": "kalshi_prediction_market",
      "market_type": "prediction_market",
      "decision_id": "decision_REPLACE_WITH_REAL_ID",
      "outcome_status": "settled",
      "final_outcome": "yes",
      "settled_at": "2026-05-29T00:00:00+00:00",
      "source": "local_manual"
    }
  ]
}
```

Persist after dry-run passes:

```json
{
  "dry_run": false,
  "persist": true,
  "records": [
    {
      "provider": "kalshi_prediction_market",
      "market_type": "prediction_market",
      "decision_id": "decision_REPLACE_WITH_REAL_ID",
      "outcome_status": "settled",
      "final_outcome": "yes",
      "settled_at": "2026-05-29T00:00:00+00:00",
      "source": "local_manual"
    }
  ]
}
```

Kalshi settled yes/no contract example:

```json
{
  "provider": "kalshi_prediction_market",
  "market_type": "prediction_market",
  "contract_id": "KX_REPLACE_WITH_REAL_CONTRACT",
  "outcome_status": "settled",
  "final_outcome": "yes",
  "settled_at": "2026-05-29T00:00:00+00:00",
  "source": "local_manual"
}
```

Sharp sportsbook win/loss/push example:

```json
{
  "provider": "sharp_sportsbook",
  "market_type": "sports_pregame_main",
  "review_item_id": "review_REPLACE_WITH_REAL_ID",
  "outcome_status": "settled",
  "final_outcome": "win",
  "settled_at": "2026-05-29T00:00:00+00:00",
  "source": "imported_file"
}
```

Void/cancelled example:

```json
{
  "provider": "sharp_sportsbook",
  "market_type": "sports_pregame_main",
  "ticker": "REPLACE_WITH_REAL_TICKER_OR_EVENT_KEY",
  "outcome_status": "void",
  "final_outcome": "void",
  "settled_at": "2026-05-29T00:00:00+00:00",
  "source": "local_manual"
}
```
