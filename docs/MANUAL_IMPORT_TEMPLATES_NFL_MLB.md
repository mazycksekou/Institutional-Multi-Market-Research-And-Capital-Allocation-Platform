# NFL and MLB Manual Import Templates

This pass creates manual import templates for unresolved NFL and MLB fields that could not be safely populated through approved automated retrieval.

## Template Files

- `data/manual_import_templates/nfl_remaining_fields_template.csv`
- `data/manual_import_templates/mlb_remaining_fields_template.csv`

## Template Columns

- `sport`
- `field_name`
- `entity_level`
- `required_columns`
- `example_row`
- `validation_rules`
- `cutoff_safe_requirement`
- `source_required`
- `source_url_hash_required`
- `notes`

## Usage Notes

- Use the templates only with validated source metadata.
- Do not persist raw HTML, screenshots, cookies, session values, or full provider payloads.
- Include the source URL hash and validation evidence when backfilling manually.
- Keep cutoff-sensitive fields aligned with the appropriate pregame or historical window.

## Completed Sports Policy Note

- The combined completed-sports policy review now classifies unresolved NFL and MLB public paths path-by-path as manual-only, paid/licensed, blocked, duplicate, unavailable, or license-unclear.
- Use `data/manual_import_templates/completed_sports_policy_review_template.csv` when you need the source-policy blocker or legal-review context alongside the sport-specific template rows.
