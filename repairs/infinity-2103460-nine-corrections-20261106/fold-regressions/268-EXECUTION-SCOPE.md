# Selected final handoff verification — 2026-11-07

Execute the owner's full 6_1 handoff on the existing protected branch.
Confirmed device reference remains APK462 / skin262 / CC61. Preserve the
four physical passes and all six runtime corrections already reviewed.

Before testing: review and tighten only the Search handoff's final profile/
abort check and privacy-safe first-party trace stages. The trace may identify
form, heading publication, handler entry, endOfDirectory return and builtin
request/return. None of these proves a native touch or rendered destination.
No additional provider calls, observers, workers or diagnostic file writes.
Strict aggregate settings/source/cancellation/ABA checks remain unchanged.

Selected checks: actual test_search_correction.py except its obsolete source
inventory and old cache-race refusal assertion (the current inventory check and
test_search_cache_race.py verify those reviewed changes),
test_search_cache_race.py, current test_search_handoff_268.py with added final
profile/abort, output counts/empty/error, dispatch-failure and trace privacy
cases; existing integrated ProviderDispatch/WatchedActions/SkinAndProtectedPasses
cases updated only for the reviewed handoff source inventory. Run these once
after integration and retain failures. Preflight runs its selected handoff gate
again against the exact committed signing source. Changed CC requires six fresh
real-Java installer/recovery cases in the original signing workflow.

Final downloaded-artifact check: exact current268/269 envelope/signature, full
CC/native verifier, skin948 hashes, exact member differences and262 recovery.
Original workflow/key/authority/installer/native/Cobra/Preview remain unchanged.
No unrelated shutdown suite, APK build or automatic installation/lock.
Actual Android/Fold, complete settings-write coverage and current crash cause
remain NOT RUN/unresolved; do not turn them into host-test passes.
