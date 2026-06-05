# Soccer Manual Import Templates

Manual templates remain only for lanes where the free/open automated path was exhausted, policy-limited, manual-only, or still paid/licensed.

## Template File

- `data/manual_import_templates/soccer_remaining_fields_template.csv`

## Safety Notes

- Do not persist raw HTML, raw provider payloads, screenshots, cookies, session values, passwords, or secrets.
- Every imported row must include source name, source URL hash, observed timestamp, cutoff timestamp, and a validation note.
- Use timestamped pregame or historical snapshots only when the lane influences model inputs.

Template rows: 5

## Completed Sports Policy Note

- The combined completed-sports policy review now resolves exact Soccer public-path outcomes for football-data, StatsBomb open data, official league pages, Understat-style mirrors, ClubElo-style paths, FiveThirtyEight archives, paid 360 products, and blocked reference sites.
- Use `data/manual_import_templates/completed_sports_policy_review_template.csv` when you need the path-level blocker, policy-doc coverage, or legal-review requirement alongside the Soccer-specific manual rows.
