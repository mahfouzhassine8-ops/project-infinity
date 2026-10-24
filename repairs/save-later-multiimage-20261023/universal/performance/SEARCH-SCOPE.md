# Search loading and refresh — focused performance addendum

Authority: submitted Critical Performance / Refresh / Responsive Addendum, continuing c0dba465 and signed QA33. Current build remains independent.

Selected source-only measurement before execution:
`python3 repairs/save-later-multiimage-20261023/universal/performance/profile_search.py --phase before`

Measurements use actual signed33 infinity_search.py bytes, committed34 source, actual reviewed POV6.10.22 and specialty provider source fixtures. Kodi calls, dialog and provider execution are stubbed. Capture actual Python Search/discovery entrypoint timings, file reads/bytes, filesystem operations, and cProfile hot functions. No Android/frame pacing/GUI smoothness claim; no application execution, provider execution, shutdown scenario, or unrelated suite.

Changes and exact correction-specific regression tests will be selected here before execution if the profile supports an implementation change. Existing19 checks will not be rerun without a direct correction-specific reason.

Profile finding: current34 called the original capability verifier17 times and read54 provider files during one cold4-provider inventory, including repeated manifest/router processing across alternative contracts. A normal selected-provider submission added8 source reads before dispatching only the first-party results handler; that handler independently discovers and validates again.

Selected changes: request-local source/shape reuse across candidate contracts, manifest entrypoint filtering and per-entrypoint refresh stamps, removal of the redundant selected-provider pre-dispatch hash only. Retain native enabled-state checks, raw source validation immediately before/after actual provider request, two-second on-access inventory refresh, forced enumeration on submission/recovery, and fail-closed update behavior.

Selected exact correction-specific tests before execution:
`python3 repairs/save-later-multiimage-20261023/universal/performance/test_search_performance.py`

Tests compare actual reviewed fixture capability output against committed34; verify shared-source processing once, unrelated-entrypoint stamp exclusion, same-version and manifest updates, disable/removal, wrong identity/symlinks, and actual source validation at the first-party dispatch boundary. No broad prior19-suite rerun.

Selected follow-up source-only profile:
`python3 repairs/save-later-multiimage-20261023/universal/performance/profile_search.py --phase after`
