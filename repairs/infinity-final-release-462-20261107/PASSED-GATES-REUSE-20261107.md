# Infinity 2103464 — immutable passing-gate reuse checkpoint (2026-11-07 EST)

**Purpose:** Preserve proven results without repeating unrelated expensive Android verification. This is a records-only branch; do not mutate the signed APK, original signing identity, skin, native engine, Command Center, Cobra, other providers, or the active final-release branch.

## Separately successful Umbrella/POV source compatibility checks
- Exact host-check source commit: `16af10e42265f9f5155efd54849b25871c50aa0f`
- Preserved branch: `locks/umbrella-pov-native-search-host-pass-20261107` (points at the exact passing source commit)
- GitHub Actions pass: `42435806833` (all steps passed)
- Archived evidence: artifact `13598889647` (`Infinity-Native-Compatibility-Host-42435806833-NOT-APK`).
- This test checks pinned public Umbrella and POV native search contracts, negative isolation from unrelated providers, and source/signability alignment only. It does **not** produce an installer, approve an Android behavior change, or prove a successful Fold test.

## Reusable actual Android gates from the subsequent independent signed-464 QA
- Exact Android QA source commit: `152ae1bed123894af9669640edd2f6508cd80996`
- GitHub Actions run: `42437719318`
- Evidence ZIP artifact: `13601500225` (`Infinity464465-Selected-Android17-42437719318-FOLD-PENDING`)
- Evidence file: `release-android-results/ANDROID-VERIFICATION.json`; status of **whole job**: FAIL_SELECTED_ANDROID_GATE.
- Independently recorded PASS cases in that run:
  - Authenticated existing external component files and preserved user-data sentinel prior to update.
  - Actual signed 2103462→2103464 Android install-over, same UID and all 78 signed module files matching package.
  - Front (1080×2520) and inner (1600×1800) layout snapshots in both system light and dark modes. Screenshots exist, **manual acceptance still pending**.
  - Seven successful actual native Search cycles: The Matrix, Just Friends, Inception, Toy Story, Spirited Away, Finding Nemo, and Re:zero.
  - The Matrix: an actual Umbrella provider heading was successfully selected/opened; this proves one route, not universal reliability.
- In this same run, the next TV Search query `SpongeBob` displayed two provider headings (Umbrella 7 results and WatchNixtoons2 1); then the scripted Umbrella `select-row` command received no observer response before its 160-second deadline.
- Precisely unproven: the eighth heading activation on TV, later watched/Info/Downloads/playback cases, forward 465 recovery, and real Fold acceptance.
- The earlier `controller_access` import failure in prior run `42435881141` was not the failure of `42437719318`: its last failure was `RuntimeError: Timed out: selected select-row; None`.

## Efficient next step and non-waivable boundaries
1. Keep both existing passing checkpoints immutable and link them in release evidence. Do not rerun host-only Umbrella/POV or already-proven signed-module/identity checks unless the exact relevant source or signed inputs change.
2. Diagnose the one unanswered `select-row` observer request using the saved run's Android logs, per-cycle snapshots, XML and request sequence 192. Distinguish an observer hang, a slow provider route, and a genuine blocked Search All heading without fabricating a pass.
3. A targeted replay or narrow runtime check may reduce iteration time. Reusing records does **not** make the failed interaction pass, and GitHub Actions cannot literally resume a prior emulator process between jobs unless an explicitly verified resume mechanism is built.
4. Before **final release acceptance**, require a valid check of the unresolved selected route and other still-unverified mandatory gates, plus user Fold observation where required; never silently waive release conditions to expedite a build.
5. No third-party addon rewrites, no alternate search engine, no modification of regular Movies/TV Shows, Infinity Trakt tracking, Cobra, signing keys, or original prepared 2103464/465 APKs.

This markdown evidence is a fast-path ledger, **not an installer** and **not authorization to ship**.
