# Infinity 2103403 corrective gate — 2026-10-25

## Locked reference
- Signed APK: Infinity 2103402 WatchNixtoons2 Universal Trakt QA
- Workflow run: 40167419559; signed artifact ID: 12588853787
- Reference commit: d18be1893beca4c487583d9bd59f2db05383b0ba
- Cobra and all unrelated Infinity components are fully off limits.
- Do not replace the approved baseline or clear user data.

## WatchNixtoons2 exact-route tracking
- Physical Fold video: WatchNixtoons2 context menu displayed; after Save for Later the selected action entered the verified-provider dialog. Watchlist exhibited the same shared path according to the user.
- Confirmed code gap: no durable verified identity mapping exists unless an independent tracking action actually creates a source-bound row, and exact_previous does not inspect Custom Lists.
- Proposed guarded patch: repair script hotfix_2103403.py; requires explicit typed-ID confirmation, saves a standalone exact-provider-route link within existing Essential-First protected local Resume Hub JSON, and fails closed for conflicting identity, source drift, unsupported schema, or maximum link count. No title-based guessing or provider edits.
- Host verification: seven targeted flow/cancellation/conflict tests and five real Resume Hub mutation paths; results from workflow infinity-2103403-tracking-host-gate.yml. This is not physical device acceptance.
- This mapping alone is not evidence that the full provider verification workflow has passed physical Fold tests.

## Search crash
- Local time: 2026-10-25 02:16:29 -04:00.
- APK: 2103402, Android 17 (API 37), Fold.
- Crash snapshot: pid 20410, tid 27720, SIGSEGV (signal 11), si_code 1, fault_address 0x2c.
- Captured PC: 0x6e063c6104; LR: 0x6e06cc1ee8.
- Android exit history: matching signal/exit around 02:16:30.
- Native snapshot includes a compile-time constant string, NOT a measured SHA of the loaded libkodi.so. Mismatched constant alone does not establish a component mismatch.
- Missing: complete tombstone or process memory map for pid 20410. Without an address-base mapping, do NOT pretend to attribute PC to a function.
- Crash recorder source saves native-maps-<pid>.txt in the app-private infinity-native-diagnostics folder on process initialization. The Android chooser diagnostic ZIP does not export it.
- The installed Health Center Crash Center Export latest incident / diagnostics is explicitly written to export preserved native-maps-* files, if still present. Use its ZIP to correlate exact pid and native ELF.
- Search SIGSEGV root cause UNPROVEN; no speculative native fix, diagnostic bypass or re-signing as an accepted release.

## Acceptance gates
1. Resolve Search root fault to actual symbols/source, implement and verify narrow correction.
2. Host + Android 17 verification of tracking and repeated Search use; no cross-provider identity guessing.
3. Verify all previously approved features and Cobra byte-preservation.
4. Build matching ARM64 QA from exact source, original permanent signing certificate, matching component ZIPs, no data loss.
5. Physical Fold acceptance before final lock.

Status: tracking code staged and host verified; Search native repair blocked on mapped crash evidence; no completed corrective release.
