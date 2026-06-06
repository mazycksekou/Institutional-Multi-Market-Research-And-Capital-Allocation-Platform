# LIVE MARKET SOURCE POLICY STANDARD

Live-market sources are usable only when terms, license, robots rules when applicable, API documentation, and data dictionary evidence allow read-only normalized fact ingestion.

Source decisions:

- `accepted_for_read_only_normalized_ingestion`
- `accepted_for_replay_only`
- `accepted_for_manual_review_only`
- `paid_license_required`
- `policy_blocked`
- `robots_blocked`
- `terms_blocked`
- `login_paywall_captcha_blocked`
- `license_terms_unclear`
- `unavailable_after_exhaustive_search`

Raw provider payloads, raw HTML, screenshots, secrets, logged-in sessions, CAPTCHA flows, and sportsbook automation are blocked unless a future policy explicitly authorizes the exact path.
