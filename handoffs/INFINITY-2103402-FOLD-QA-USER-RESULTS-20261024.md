# Infinity 2103402 — User-reported physical Galaxy Fold QA findings

**Recorded:** 2026-10-24. **Source:** user statements in ChatGPT after installing the separately signed functional QA package. This is a user report, not independent automation or instrumented measurements.

**Tested build:** Infinity 2103402 Functional Corrective QA, GitHub Actions signed package run `40144024130`, artifact `12579354598`. The original-behavior, same-version signed rollback package is run `40144132183`. Baseline remains **2103401** at source `1738478709cd8881f7ad4a524e7abbbc82b5d79c`, build `40089463702`; Cobra remains off limits.

## User-confirmed PASS (physical Fold)
1. **Option B short descriptions:** PASS; short-description layout behaves as intended.
2. **Option B vertical scrolling:** PASS; user confirms long text scrolls vertically.
3. **Clock including AM/PM:** PASS.
4. **Playback time-label readability:** PASS.
5. **Play/Pause visual appearance:** PASS.

These five user-tested behaviors are accepted **for this installed QA candidate**. Do not reopen or redesign them without a reproducible regression.

## Physical observations requiring correction

### Home reload after playback — user-reported FAIL, partial speed improvement
The user played a movie and returned to Home. Home content/poster rails were not immediately retained, but instead repopulated. Reload seemed shorter than the earlier ~40–45-second delay, but the required seamless immediate restore was **not achieved**. Previously staged command-center revision suppression addresses just one invalidation source; do not label the full Home restoration behavior fixed.

**Provenance discrepancy:** a subsequent automatically composed checkbox summary marked Home `NOT TESTED`, but the user's preceding independent first-person description explicitly describes having performed the test and observing Home reload. Record it as **observed FAIL (timing unmeasured)**. A dedicated controlled timing/return cycle is still pending.

**Required correction:** identify the actual post-playback invalidation/reload owner and avoid unnecessary directory refetch for unchanged cached Home content. Preserve legitimate refresh and source changes; do not hardcode cached assets or alter provider/resume semantics. Measure cold and warm return independently.

### TV-series Continue Playing — new missing-items report
After the 2103402 functional QA installation, the user reports that previously shown entries in the **TV-show Continue Playing** section no longer appear. No claim of deleted records, watcher data loss, or a source-level causation has been established.

**Required correction and safety:** first determine whether entries are present in local persistence but hidden, filtered, or failing to render; compare this QA against locked 2103401 behavior. Avoid database resets, migrations, bulk recreation, destructive reindexing, disabling provider ownership, or attempts to simulate entries. Preserve watched progress, movie Continue Playing, TV episode identity, and existing routes. Diagnose whether difference comes from UI revisions, skin widget routes, query filtering, startup visibility, or unrelated app state before modifying anything.

## Not part of this QA acceptance
Search SIGBUS cause remains unresolved. Provider chooser compactness/Cancel/[B] label, Information focus return, and Java/native Health Center diagnostic integration were not implemented in the functional QA package. Do not mark these as tested or fixed; do not mix their native/DEX changes into an isolated Home/TV correction without separate evidence and approval.

## Preservation and release instructions
- Preserve all five physically passing corrections unchanged.
- Keep accepted 2103401 source and signed package immutable; Cobra remains 100% untouched.
- No user-data wipe, uninstall, Start Fresh, or irreversible database repair.
- Keep updates isolated, fail closed on original file hashes/member boundaries, verify version/signature/install-over.
- User's highest-priority new actionable observations are Home return not retaining posters and TV-show Continue Playing missing entries.
- This results record is documentation only; it does not authorize speculative edits or imply a new APK has been generated.
