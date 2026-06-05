# Combat Source Policy Review

This document records the final source-policy state for the Combat Sports free/open exhaustion pass.

## Final Source States

- Open Boxing data repository: final_state=free_open_backfilled decision=accepted_for_automated_normalized_backfill blocker_or_allowance=MIT-licensed Open Boxing repository and public API/docs allow normalized boxing backfill within this pass.
- Wikidata combat sports fighter entities: final_state=free_open_metadata_only decision=accepted_for_metadata_only blocker_or_allowance=Structured fighter metadata is allowed for attribution-preserving metadata-only use.
- Wikipedia combat sports entity tables: final_state=free_open_metadata_only decision=accepted_for_metadata_only blocker_or_allowance=Wikipedia tables remain metadata-only supplemental sources with attribution retained.
- UFC official weigh-in and news pages: final_state=manual_import_required decision=accepted_for_manual_import_only blocker_or_allowance=UFC terms prohibit automated systems on the service, so official weigh-in use remains manual-only here.
- UFC official event pages: final_state=manual_import_required decision=accepted_for_manual_import_only blocker_or_allowance=Official UFC event pages remain manual-only because automated systems are restricted and timestamp review is required.
- State athletic commission public records: final_state=manual_import_required decision=accepted_for_manual_import_only blocker_or_allowance=Commission records can support timestamped manual imports, but not automated normalized extraction in this pass.
- UFC Stats event, fighter, and bout detail pages: final_state=policy_blocked decision=rejected_policy_blocked blocker_or_allowance=No compliant automated extraction path for UFC-owned stats pages was approved in this pass.
- Tapology event and fighter pages: final_state=policy_blocked decision=rejected_policy_blocked blocker_or_allowance=Tapology remains blocked until an exact path is explicitly approved after policy review.
- Sherdog fighter and event pages: final_state=policy_blocked decision=rejected_policy_blocked blocker_or_allowance=Sherdog remains blocked until an exact path is explicitly approved after policy review.
- ESPN MMA pages: final_state=policy_blocked decision=rejected_policy_blocked blocker_or_allowance=ESPN MMA pages were reviewed but not approved for automated extraction in this pass.
- BoxRec record pages: final_state=login_paywall_captcha_blocked decision=rejected_login_paywall_captcha blocker_or_allowance=BoxRec is treated as login/terms blocked for automated use in this pass.
- Kaggle combat dataset catalog: final_state=login_paywall_captcha_blocked decision=rejected_login_paywall_captcha blocker_or_allowance=Kaggle catalog access remains account-gated and not suitable for compliant free/open automation.
- GitHub UFC stats API wrapper repo: final_state=license_terms_unclear decision=license_terms_unclear blocker_or_allowance=The wrapper repo is public, but downstream rights remain unclear because it derives from UFC-owned stats surfaces.
- GitHub MMA data scraper bundle repo: final_state=license_terms_unclear decision=license_terms_unclear blocker_or_allowance=The public repo combines scraped UFC, Sherdog, and Wikipedia inputs, so downstream rights remain unclear.
- Paid MMA/boxing tracking vendor page: final_state=paid_subscription_required decision=rejected_terms_blocked blocker_or_allowance=Tracking, punch-level, and broader round microdata remain licensed vendor lanes after exhausting free/open paths.
