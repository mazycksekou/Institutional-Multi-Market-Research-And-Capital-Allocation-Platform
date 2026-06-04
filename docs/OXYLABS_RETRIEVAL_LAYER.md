# Oxylabs Retrieval Layer

This repository keeps Oxylabs fully disabled by default.

## Environment variables

- Residential Proxy: `OXYLABS_PROXY_HOST`, `OXYLABS_PROXY_PORT`, `OXYLABS_PROXY_USERNAME`, `OXYLABS_PROXY_PASSWORD`
- Web Scraper API: `OXYLABS_API_USERNAME`, `OXYLABS_API_PASSWORD`, `OXYLABS_API_ENDPOINT`

## Policy gates

Paid retrieval is only considered when both `AllowOxylabs` and `AllowPaidRetrieval` are explicitly set.
The retrieval policy also requires a source allowlist and a domain allowlist, and rejects the required blocklist.

## Required blocklist

- `pro-football-reference.com`
- `sports-reference.com`
- `football-reference.com`
- `baseball-reference.com`
- `basketball-reference.com`
- `hockey-reference.com`
- `fbref.com`
- `fangraphs.com`
- `ftnfantasy.com`

## Behavior

- No raw HTML is persisted.
- No raw provider payloads are persisted.
- No usernames, passwords, Authorization headers, cookies, or other secrets are written to logs or reports.
- The open-free path remains the default operating mode.
