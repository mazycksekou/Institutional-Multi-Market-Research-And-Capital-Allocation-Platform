# Phase 10K8ZHF - Dashboard and Entrypoint Ownership Audit

## Executive Summary
The dashboard and bootstrap files are not deletion candidates. They are shell boundaries:

- `main.py` is the bootstrap/orchestration entrypoint.
- `streamlit_app.py` is the display/UI entrypoint.

main.py is not a deletion candidate. streamlit_app.py is not a deletion candidate.

Both still contain compatibility-era glue, but neither should be rewritten wholesale in this phase.

## Ownership Summary

- `main.py`: `KEEP_ENTRYPOINT_OR_DASHBOARD`
- `streamlit_app.py`: `KEEP_ENTRYPOINT_OR_DASHBOARD`

## Boundary Notes

- `main.py` currently wires services, API route registration, and compatibility wrappers together.
- `streamlit_app.py` is display-only long term and should stay a UI shell.
- Dashboard code should call services rather than importing core logic directly where avoidable.
- No connector ownership belongs in the dashboard.

## Required Statement
`main.py` is not a deletion candidate, and `streamlit_app.py` is not a deletion candidate. They remain bootstrap/display shells while the rest of the architecture thins underneath them.
