# Exact signed Infinity 2103464 — Search crash diagnostic pass and release disposition

## Accepted as **diagnostic evidence**, not APK or user acceptance

- Workflow: `Infinity464 eight real Search All cycles | controlled QA observer only`.
- GitHub Actions run: **42443988873**, **attempt 2**, final conclusion **success**, completed **2026-11-08 04:09:31 UTC**.
- Verified source commit: `2759febb289f9e1eebf4b122f78bdf802646efac`; immutable checkpoint branch: `locks/infinity464-eight-search-qa-pass-20261107`.
- Exact completed attempt-2 evidence artifact **13603118981** (`Infinity464-Eight-Search-AB-42443988873-DIAGNOSTIC-NOT-APK`). Attempt-1 artifact 13602554622 was from a **failed pre-search emulator startup** and is not the PASS evidence.
- The run logged all eight real Search All cycles as PASS: movie **The Matrix**, **Just Friends**, **Inception**, **Toy Story**, **Spirited Away**, **Finding Nemo**; TV **Re:zero** and **SpongeBob**.
- The native Umbrella heading opened successfully in cycles 1 and 8, with real folder-path checks. Eighth cycle displayed eight results across the two native providers. Kodi process PID remained the same. The run printed `PASS_EIGHT_NATIVE_SEARCHES_AND_TWO_REAL_HEADING_ROUTES_QA_ONLY`.
- The ONLY change tested against the original signed APK was a disposable QA observer action that **does not call `xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')` during selection**, while continuing real `SetFocus` and `Input.Select` and checking actual provider destination. The signed APK, Search service, Umbrella, Nixtoons, Cobra and skin were unchanged.

## What the PASS does and does NOT prove

**Supports:** The previously failing eight-query sequence can succeed on the same signed 464 APK with reduced concurrent live-list-item reads by a QA Python observer. This strengthens a Python-to-native GUI list-item lifetime/race hypothesis; it also identifies at least one artificially hazardous observer read that should not be added to production.

**Does NOT prove:** A production root cause; normal Fold Search will never crash; an intrinsic Umbrella or POV defect; safe native locking patch; completion of original full release gates (including watched/Info/Downloads, forward465 recovery, manual dark/light UI and actual Fold). The diagnostic ZIP is **not** an installable update.

## Mandatory next decision, preserving accepted work

1. Compare the **actual production callers** of `xbmc.getInfoLabel('Container.*ListItem*')` during Search All transitions against the QA-only observer. The immediate risky read shown by this experiment was in `android_qa.py`, not yet proven present in production. Avoid shipping the QA change as a purported Infinity fix.
2. Keep existing native full-integration Search and provider implementations intact. Confirm any proposed modification against the exact signed 464 native/source map and actual phone crash evidence; an unjustified global `getInfoLabel` lock could create regressions/deadlocks.
3. Reuse the original signed APK, signing identity, previous passing host/Android evidence. Any installer must be separately signed and released only through the original authorized owner-gated release flow. Do not put QA diagnostics or unapproved third-party code in the APK.
4. If subsequent investigation proves no production change is needed, do **not** manufacture a new APK merely to turn a QA-only improvement into a release. If a production fix is demonstrated, build **one** preserved combined Infinity/Cobra APK with matching recovery and a focused, finite acceptance path; Fold approval stays outstanding.

## Protected checkpoints

- Umbrella/POV host compatibility PASS: run `42435806833`, commit `16af10e42265f9f5155efd54849b25871c50aa0f`, branch `locks/umbrella-pov-native-search-host-pass-20261107`.
- Signed 464 earlier Android pass subset / failed 8th heading (before QA observer change): run `42437719318`; retained record `locks/infinity464-reuse-passed-gates-20261107`.
- Isolated signed 464 first-heading PASS: run `42441430136`.
- This successful eight-cycle diagnostic: run `42443988873` attempt 2.

**No public release made, no full APK acceptance claimed.**
