# Repository Independence Scorecard

## Executive Answer

Yes. This repository is machine-independent enough for a permanent switch from the current Windows laptop to a future Mac without redesigning the repository.

The canonical workflow is Python-first and works from macOS Terminal, Linux shells, Windows shells, GitHub Actions, and Render. PowerShell, Task Scheduler, and other OS-specific surfaces remain only as optional wrappers or documentation examples.

The remaining gaps are not machine-switch blockers. They are product or environment follow-up items such as live provider signoff, external service configuration, and future NFL/backtesting work.

## Evidence Snapshot

Validation and governance checks currently pass:

- `python scripts/check_repo_preflight.py --start-task --include-ops`
- `python scripts/check_root_markdown.py`
- `python scripts/check_openapi_contract.py --output text`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_audit_lifecycle.py`
- `python scripts/check_document_lifecycle.py`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python -m compileall src tests scripts`
- `pytest -m smoke -q`

Repository preflight reports:

- branch: `phase-6-api-slimming`
- upstream: `origin/phase-6-api-slimming`
- working tree clean: yes
- index clean: yes
- ahead/behind: `0/0`

## Canonical Toolchain

| Tool | Status | Why |
| --- | --- | --- |
| Python | REQUIRED | All canonical validation and governance scripts are Python-first. |
| Git | REQUIRED | Preflight, branch safety, and repo-state checks require it. |
| pytest | REQUIRED | Smoke and targeted validation use it. |
| pip / virtualenv | REQUIRED | Needed to install the documented dependencies. |
| Streamlit | OPTIONAL | Only required for the dashboard entrypoint. |
| PowerShell | WINDOWS CONVENIENCE | Optional wrappers and Windows examples only. |
| Bash / shell | OPTIONAL | Useful on macOS/Linux, but not required by canonical repo logic. |
| GitHub CLI | OPTIONAL | Helpful for PR workflows, not required by repository correctness. |
| Render tooling | OPTIONAL | Only needed for Render-specific workflows. |
| Docker | OPTIONAL | Useful for deployment parity, not required for the canonical local workflow. |

## Scorecard

| Category | Status | Evidence | Blocker Status | Recommended Follow-Up |
| --- | --- | --- | --- | --- |
| Runtime Independence | PASS | `src/` runtime code is free of Windows-only runtime dependencies; preflight, architecture, and compileall pass. Optional wrappers live outside runtime ownership. | No blocker | Keep runtime code Python/pathlib-first. |
| Development Independence | PASS | `docs/development/ONBOARDING.md`, `docs/operations/VALIDATION_RUNBOOK.md`, and `docs/operations/OPS_WORKFLOW.md` describe a Python-first workflow that works from macOS Terminal. | No blocker | Preserve optional wrappers as convenience only. |
| Tool Independence | PASS | Canonical workflow requires Python, Git, and pytest; optional tools are documented as optional. | No blocker | Keep required-tool documentation synchronized with scripts. |
| Environment Independence | PASS | `.env.example` uses placeholders, not real secrets or absolute local paths. | No blocker | Continue avoiding machine-specific config. |
| Repository Independence | PASS | `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`, ownership maps, dependency maps, onboarding, standards, and governance docs exist. | No blocker | Keep these docs current as the repo grows. |
| Validation Independence | PASS | Governance checks are local scripts, and all core validation commands passed. | No blocker | Keep validation scripts authoritative. |
| CI Independence | PASS | `.github/workflows/repository-validation.yml` calls repository scripts rather than duplicating logic, and uses full checkout history. | No blocker | Keep CI as a wrapper around local checks. |
| Documentation Independence | PASS | Active docs are Python-first and mark Windows paths as optional examples or wrappers. | No blocker | Preserve OS-neutral phrasing in new docs. |
| Operating System Independence | PASS | Active repo workflows run on macOS, Windows, Linux, GitHub Actions, and Render in documented form; OS-specific surfaces are optional. | No blocker | Keep Task Scheduler / PowerShell examples optional. |
| Future Independence | PASS | A new Mac or Windows reinstall does not require repo redesign; development can continue from a fresh clone. | No blocker | Keep setup reproducible with docs and scripts. |
| Platform Independence | PARTIAL | Repository structure and governance support future NFL/backtesting/product work, but the product features themselves are still future phases. | Not a machine blocker | Start the next product phase when ready. |
| Knowledge Independence | PASS | Major decisions are captured in architecture docs, ADRs, ownership maps, standards, runbooks, and indexes. | No blocker | Prefer doc updates over tribal knowledge. |
| Convenience-vs-Standard Discipline | PASS | Python commands are canonical; PowerShell/Bash/Task Scheduler examples are optional. | No blocker | Avoid making convenience wrappers the only path. |
| Tribal Knowledge Removal | PASS | Searchable docs now explain the workflow; lingering phrasing is instructional rather than “works on my machine” tribal knowledge. | No blocker | Convert future manual steps into scripts or documented rules. |
| Stop Condition / Product-Work Readiness | PASS | Repository modernization is complete enough to stop infrastructure cleanup and move to product work. | No blocker | Next major phase should be NFL/backtesting/product development. |

## Runtime Independence Notes

Evidence from active runtime and entrypoint scans:

- no required runtime code depends on PowerShell
- no required runtime code depends on Windows Task Scheduler
- no required runtime code uses hardcoded local Windows paths
- thin root entrypoints remain thin and delegate into `src.*`
- path handling is already normalized around repository-relative or `pathlib`-based paths

The only Windows-specific surfaces that remain are optional convenience wrappers or optional scheduling examples:

- `scripts/*.ps1`
- `scripts/install_json_audit_scheduled_task.py`
- `scripts/uninstall_json_audit_scheduled_task.py`
- Task Scheduler examples in scheduler docs

## Development Independence Notes

The canonical developer workflow is Python-first:

1. clone the repo
2. install Python dependencies
3. run the repository scripts
4. validate with compileall, smoke, ops, and preflight

PowerShell is not required for normal development. It is available only for Windows convenience wrappers and a few optional live-helper entrypoints.

## Environment Independence Notes

The repository does not require:

- usernames
- drive letters
- absolute workstation paths
- real secrets in example config
- machine-local configuration to understand the repo

The `.env.example` file uses placeholder values and clearly separates optional feature flags from required secrets.

## Operating System Independence Notes

Supported development environments are documented as:

- Windows
- macOS
- Linux
- GitHub Actions
- Render

Current OS-specific surfaces are classified as follows:

- optional: PowerShell wrappers
- optional: Windows Task Scheduler examples
- optional: live smoke helper wrappers
- documentation example: `schtasks` snippets
- required blocker: none

## Validation Independence Notes

Validation is repo-owned, reproducible, and not tied to one workstation.

The canonical checks are the repository scripts and smoke tests, not ad hoc manual commands.

## Future Work and Remaining Non-Blocking Gaps

These items remain future work but do not block a Mac migration:

- live provider/environment signoff
- rate limiting / external observability maturation
- product capability work such as NFL/backtesting and future market expansion
- any deployment-specific review required by a target environment

## Decision

For a principal systems engineer, the repository is done enough to switch development machines permanently.

The correct next step is:

1. clone the repo on the new Mac
2. install the documented Python toolchain
3. run the same repository scripts and validations
4. continue product work from the canonical `src/` architecture

If a future task needs PowerShell or Task Scheduler, those remain available as optional wrappers only.

