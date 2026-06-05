# Basketball Manual Import Templates

Manual templates cover unresolved basketball lanes that are paid, terms-review gated, or manual-only.

## Template Files

- `data/manual_import_templates/nba_remaining_fields_template.csv`
- `data/manual_import_templates/wnba_remaining_fields_template.csv`
- `data/manual_import_templates/ncaab_remaining_fields_template.csv`
- `data/manual_import_templates/ncaaw_remaining_fields_template.csv`

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

## Safety Notes

- Do not persist raw HTML, screenshots, raw provider payloads, cookies, session values, or secrets.
- Every manual import needs source name, source URL hash, validation note, and a cutoff timestamp.
- Basketball modules remain separate: NBA, WNBA, NCAAB, and NCAAW are not merged.

Template rows: 21
