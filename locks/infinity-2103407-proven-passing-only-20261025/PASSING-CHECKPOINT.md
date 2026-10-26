# Infinity 2103407 — Verified-Passing-Only Source Checkpoint

**Authoritative instruction:** Preserve only proven working source and evidence. This is NOT a final Infinity production lock, acceptance of broken modules, or certification that all native crash types are fixed.

## Exact source reference

- Repository: mahfouzhassine8-ops/project-infinity
- Dedicated preserved source branch: lock/infinity-2103407-proven-passing-only-20261025
- EXACT signed-source commit: 0e8739d2d0e1be0ab8f127519b526556426fb160
- GitHub branch comparison against that SHA: identical, 0 commits ahead / 0 behind, zero changed files.
- Completed full package QA run: 40230842944 (SUCCESS)
- Signed GitHub artifact ID: 12613590219
- Signed GitHub artifact name: Infinity-2103407-SEARCH-SINGLE-FLIGHT-ORIGINAL-SIGNER-QA
- Artifact archive digest reported by GitHub: sha256:bfc2a55e799f767bd01d535a3bdb77b65b91c9336755627f9b2297bfa3766baa
- Android versionCode: 2103407; package: com.projectinfinity.kodi; ABI: ARM64.
- Verified original permanent signing certificate SHA256: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7
- Previous signed parents preserved as separate historical references: 2103406 run 40191243446, 2103405 run 40184543219.
- The dedicated branch is a reference, NOT a GitHub-enforced protected or immutable ref. No branch-protection configuration is claimed; verify rulesets separately before claiming enforcement. The SHA and artifact hashes are immutable content identities.

## Exact deliverable checksums

The signed run artifact contains these five files; their contents were independently SHA256 checked against SHA256SUMS after retrieving the full bundle:

| Artifact member | SHA256 |
|---|---|
| Infinity-2103407-Search-Single-Flight-SIGNED-QA.apk | 3616c4e69c976bd63b36170d4dbbd9b190a7ec2eace4bc0c34c3c72f7f9e8578 |
| script.infinity.commandcenter-0.3.5.39-2103407-QA.zip | 085626880963b4ae43870ff7fb57746d45dfa3ea7ce56ea2dd6be7fe53768fcf |
| script.infinity.watchedbridge-1.0.20-2103407-QA.zip | 42a03a9c3c8452d8f1f8cffc651c2805902bf9376b18975e8828af023218f55a |
| script.infinity.uirepair-0.1.22-2103407-QA.zip | f37749294e5f3f0a6f431fbbe06c728e7ea3e08f7f455bcde5cf080739a222a7 |
| skin.infinity.diggz-1.0.5.243.zip | 0adfed89f1d5384a3fa3a023152c7c2a094ef2edb6dd60129f336fe3b7cb9ef9 |

## PASS evidence only — exact confidence levels

### PASS: original signed build integration and source integrity (GitHub)

- GitHub run 40230842944 completed successfully: baseline SHA verification, exact scoped Search source patch, seven targeted deterministic overload/cancel/worker tests, signed APK/component parity, original certificate, Android versionCode, source and native immutable-RODATA hash owner verification, and Cobra payload change guard.
- The 2103407 packaging receipt declares the exact ten changed content members compared with 2103406; these are the Search source, native read-only integrity hashes, relevant addon versions/reciprocal integrity metadata, and AndroidManifest. All other packaged members including libinfinitycrash.so and skin were unchanged. No claim that native code instruction changes caused the Search repair.
- There is NO claim that Github host tests exercise real device providers, touch or Android frame pacing.

### PROVISIONAL Fold PASS: Search overload behavior in signed 2103407

- User reported stressing Search "as much as I can" for approximately one minute on the physical Samsung Fold Android 17 after installing 2103407; there was NO crash during that period.
- Existing 2103406 signed Search code was shown in deterministic tests to launch two simultaneous native directory RPC workers across independent invokers; reviewed 2103407 single-flight guard admits only one and rejects a second while busy, limits cancellation signaling and preserves worker lifetime.
- This is a real, valuable **user-confirmed positive scenario**, but DOES NOT prove no possible future SIGSEGV, destroyed-mutex crash, deadlock, or prolonged memory leak. Full final Search hardening and extended negative cases remain OPEN.

### PRIOR user-confirmed PASS: WatchNixtoons2 native Infinity Tracked on 2103405

- The user confirmed the WatchNixtoons2 long-hold/native Infinity Tracked menu finally opened after the 2103405 context registration repair.
- Signed run 40184543219 passed original source/native package compatibility and five scoped menu tests. The 2103407 packaging receipt states WatchNixtoons2 Infinity Tracked content was unchanged by the 2103407 Search-only delta; intermediate 2103406 remained recorder-only.
- This is a **preserved working reference**, NOT a claim that the full provider/Movies/TV system-wide long-hold contract passed in 2103407. Physically re-check the working menu in the final integration before promoting a new version.

### PRESERVE from earlier user reports, but not current release-wide green

- Earlier physical reports confirmed Otaku and Kodi Favorites working and Continue Playing reappearing. These remain protected regression expectations. Exact full 2103407 Fold coverage for all their routes is not demonstrated in this lock receipt.
- SIGABRT Crash Recorder rebuild and packaging gates passed for 2103406 and persisted in 2103407; actual device SIGABRT traceback improvement was NOT independently verified during a fatal abort.

## OPEN / NOT ACCEPTED

- Actual Infinity Movies and Infinity TV press-and-hold failure, plus system-wide touch selection/activation/context inconsistency.
- Unified Command Center migration (existing Watched Bridge/UI Repair/Rails are still separately installed components).
- Essential-First Shutdown: 2103407 Command Center addon version 0.3.5.39 vs checkpoint_runtime expected 0.3.5.38; recurring 25-second shutdown deadline and Python writer retirement; no evidence of correct full essential-authorized termination.
- Startup, loading, provider refresh, Home warm poster retention, effective display refresh rate, frame pacing and CPU/RSS speedups require measured before/after evidence.
- Previously approved UI popup/Option B/OSD and end-to-end visual stability are not certified as completely fixed.
- No final user-approved release freeze or full physical Fold acceptance. No overall "all green" claim.

## Freeze instructions for final engineering brief

Do NOT modify or move this source branch, signed artifacts or old rollback references while developing final corrections. Branch from the exact pinned signed source to an isolated final-fix branch. Every proposed runtime edit needs a source owner, reproduced defect, negative control, touched-file/member diff, protected no-touch proof and separate final acceptance. Scope is frozen; Cobra completely off limits; no process or user-data wipe.

**This document itself is documentation only; it does not modify or accept current runtime behavior.**
