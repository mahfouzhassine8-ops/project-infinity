# Infinity 502 — OWNER FINAL DIRECTIVE: complete entire authorized scope before ONE signed QA APK

**Owner's latest explicit instruction, 2026-11-16:** "**Then it must complete everything.**" This **supersedes any earlier proposal to produce a partial/incomplete QA APK as soon as the native engine passes**. The prior fast-QA idea is withdrawn; no partial QA APK, no separately released video-lock test APK, and no repeated "almost done" release. The original six numbered repairs stay intact and the previously approved TWO crash cases remain narrow additions. Continue work on the EXISTING 502-derived six-repair branch, not from scratch.

## Exact scope and required closure

1. **Shutdown:** Correct verified remaining SQLite/checkpoint/native retirement issues and establish safe complete shutdown and clean same-profile restart. Retain already-shipped 502 shutdown observer and CPython GIL fixes.
2. **Otaku → Infinity Trakt → Watchlist:** Correct proven first-party typed-identity/selection handoff while preserving provider-native search, existing Watchlist flow and valid IDs.
3. **Movies + TV Continue Playing:** **ROOT CAUSE FIRST.** Determine why saved original destination stopped working and why previously visible cards disappeared; preserve and audit authoritative `continue-watching.json` without destruction. Restore legitimate original navigation, resume/progress and card projections before improving the already-designed **universal**, provider-neutral emergency fallback. Never hardwire Seren or invent identities.
4. **Empty Shell and component mismatches:** Complete actually loaded startup/health/plugin lifecycle repair and cross-component/version audit, **correct every proven scoped first-party mismatch**, and independently verify end-to-end. Do not downgrade functional updated provider internals or reset profiles.
5. **Approved Video Lock and larger VideoOSD icons:** Finalize native+Android integration and two-second intentional unlock across fold/rotation/Back/PiP; ensure existing controls, order, gestures, scrolling, player behavior and PiP behavior are preserved. Retain prior passed native and focused Android evidence; rerun only checks relevant to changed source.
6. **Actual Cast playback on TV:** Prove media loads and plays to receiver rather than returning TV to home. Preserve signed502 discovery and existing transport/codec work; fix only established actual playback-hand-off problems.
7. **Not an expanded general workstream—two narrowly OWNER-AUTHORIZED crash incidents incorporated into the six-repair acceptance gate:** (A) stop-adjacent 04:40 native C++ pure-virtual abort (lifetime correction pending updated ARM64/Android validation); (B) Mark-Watched-adjacent 04:53 SIGSEGV (missing full tombstone; real root cause and watched-state persistence UNKNOWN). Investigate and apply focused, evidence-backed fixes to BOTH; verify Stop and Mark Watched behavior, persistence and no abnormal exit. Do not assume common cause or alter user playback/watched records.

## Build and acceptance order — no partial APK

- The currently running combined native ARM64 build may finish; if PASS **reuse** it, but that pass by itself **does not authorize QA signing**. If it fails, repair specific blocking code without unnecessary full retests.
- **Finish all six and both crash corrections to engineering acceptance**, or report an explicit blocked item with precisely what missing source evidence is required. DO NOT call a blocked or unproven item completed. Do not silently drop #1, #2, #3, #4, #6 or crash B just because #5 passed.
- Prefer one integrated implementation pass, reuse previous passing host/ABI/Android tests, no redundant heavy/blanket verification. Run narrowly scoped negative/positive tests when source changes require them. Never remove real release-safety checks to conserve usage.
- After implementation and engineering checks are complete, assemble and original-sign **ONE** integrated 502-derived QA test APK (unique versionCode above installed build, original package/certificate) and a matching non-destructive recovery approach. Mandatory baseline 502 source/member diff, ABI, signing, install-over and Cobra 2103445 / all out-of-scope preservation proof.
- The QA build is for **physical Fold acceptance**; real-device validation can occur only *after* an APK exists. Do not falsely claim Fold acceptance in advance. If some user-only runtime evidence is indispensable to determining a cause before coding, request the single minimum evidence item, not a data reset or speculative patch.
- Do NOT start partial QA APK assembly simply because the native engine passes. When everything is engineering-complete, build promptly rather than holding the signed candidate for repetitive test loops.

## Authority hierarchy

This file is the latest explicit owner release-timing directive. The only permitted work is the six numbered repairs plus the two exact owner-reported abnormal exits, with their minimally necessary first-party dependencies. **Every other feature and file remains strictly preserved, including Cobra.** The protected original-signed 2103502 is the baseline, with no uninstall/data clearing, cache reset workaround, guesswork, general refactors, third-party patches or signature changes.

**Status at instruction authoring:** This is a scope/release-gate instruction, **NOT proof work completed**. Full integrated QA APK has NOT been produced by writing this file.
