# NHL Manual Import Templates

Manual templates remain only for lanes where the free/open automated path was exhausted, policy-limited, or still paid/licensed.

## Template File

- `data/manual_import_templates/nhl_remaining_fields_template.csv`

## Safety Notes

- Do not persist raw HTML, raw provider payloads, screenshots, cookies, session values, passwords, or secrets.
- Every imported row must include source name, source URL hash, observed timestamp, cutoff timestamp, and a validation note.
- Use timestamped pregame or historical snapshots only when the lane influences model inputs.

Template rows: 6

## Completed Sports Policy Note

- The combined completed-sports policy review now records exact NHL public-path outcomes for injuries, officials, public goalie-start pages, line-combination pages, and public xG mirrors.
- Use `data/manual_import_templates/completed_sports_policy_review_template.csv` when you need the path-level policy blocker, missing-policy-doc list, or legal-review status in addition to the NHL-specific template rows.
