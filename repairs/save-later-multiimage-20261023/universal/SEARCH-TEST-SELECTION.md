# Authorized Search-only checks

User submission dated 2026-10-24 authorizes dynamic provider Search, Enter and
Search-button submissions, cancellation, History and Home responsiveness.

Selected before execution: `python3 -m unittest -v test_search_input` from this
directory. These five host cases check the actual reference UI's selector
contract (TextView, dynamic label and post-selection content description).
They do not execute Android or establish that the reported Fold freeze is fixed.

Java compilation and DEX package preservation are build/integrity checks for
the Infinity-only Search helper, not behavioral acceptance. No Close, shutdown,
reopen, Android 15 or unrelated runtime check is selected.

Additional selected before execution: four focused route/attribution cases in
`test_search_input.SearchResultContract`. They require the exact CC bounded
single-provider route and reject a wrong provider, category, action, query,
unattributed title or incomplete Search All provider inventory. The API37
runner is routed to the corrected actual TextView input driver. Runtime remains
NOT RUN until the separately selected API37 workflow executes.
