# `.gitignore` Source Safety Proof

The repository ignore rules were narrowed so they no longer hide `src/**/*.py`.

Fix applied:

- Removed the broad `*data` pattern
- Root-anchored local output directories like `/data/`, `/reports/`, `/archives/`, and `/artifacts/`

Verification:

- `git check-ignore -v src/data/local_platform.py` returns no match
- `scripts/check_architecture.py` reports `ignored_source_files: 0`

