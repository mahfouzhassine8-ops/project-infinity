# Infinity 2103420 — USER-APPROVED PROTECTED BASELINE LOCK
**Lock authorization:** October 26, 2026. User explicitly said: "go ahead and lock ... 420 ... our new base model."

## Locked identity: SAME ONE-APK / ONE-ICON product
- **Product:** One Android package, `com.projectinfinity.kodi`, one home-screen icon.
- **Protected experience:** Infinity/Kodi 2103420, including all first-party native engine, Home/skin, Search, watched/Continue Playing/Watching, source navigation, Power/Essential-First shutdown, saved data and launch preferences.
- **Cobra:** NOT LOCKED. It may receive separately authorized repairs inside a future higher-version APK, provided Infinity's protected ownership, behavior and data remain unchanged.
- **Shared Choose Your Experience:** Preserve one app icon and existing Ask Every Time, Remember & Launch Infinity, Remember & Launch Cobra, and one-time launch behavior. No separate installed package/launcher icon.
- **Source branch pin:** `lock/infinity-2103420-user-approved-baseline-20261026` created pointing at `883c64a4de6f87077893921454de71bba850235b` (original completed 2103420 code `ddc054583c5e5f3cd04c328e131cb76af8d4728b` plus ONLY the signed build-result receipt file). **DO NOT MOVE or commit to the lock branch.**
- **Signed APK application source:** `ddc054583c5e5f3cd04c328e131cb76af8d4728b`
- **Signed evidence/lock anchor:** `883c64a4de6f87077893921454de71bba850235b`
- **Successful build:** GitHub Actions `40413893227`, artifact `12695160919`, `Infinity-2103420-P0-Original-Signer-40413893227`.
- **Signed APK filename:** `Infinity-2103420-P0-Corrective-SIGNED.apk`; SHA256 `ae641e74bbe0b3360d103254d9bc5425fe1558f625466a99f1da9f16414fef26`
- **Signed complete release artifact SHA256:** `7e8004b793ceebf13da342ec564b934551a057492b8ac56fdaf6746e0b9c9ecb` (outer GitHub Actions artifact ZIP).
- **Permanent certificate SHA256:** `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`; ARM64 install-over, no wipe.
- **Components:** CC 0.3.5.49, Infinity skin 1.0.5.247, UI Repair 0.1.23, Watched Bridge 1.0.21, Rails 0.2.8, Kodi Health Center 2.5.27. Exactly six matching component ZIPs; see `repairs/infinity-final-closure-2103407/p0/SIGNED-420-BUILD-RESULT.json` at the lock anchor for member hashes.

## Actual user Fold acceptance: stated and recorded, NOT synthetic CI inference
User physically installed and operated **2103420** on Samsung Galaxy Fold 8 Ultra, Android 17, and explicitly reported:
1. It **feels snappy**, loads well, and overall runs fine.
2. Essential-First **shutdown works fine**.
3. Power → **ASK EVERY TIME** works correctly.
4. No other issues observed by the user during this session.
The user **explicitly authorized LOCK of 2103420** as the new base.

This acceptance is the user's observed behavior, not a claim of laboratory p95, all-provider regression coverage, strict 16KiB native ELF compatibility, or a measured frame pacing/FPS result. Prior 4KiB ELF PT_LOAD compatibility limit remains documented. Those are not hidden, but the user accepts this currently working Fold baseline.

## The forward-only ownership contract

**Infinity-only update**: create a descendant of this baseline; preserve Cobra-owned code, resources, behavior, settings/data, player, Sports/Multi-View/PiP and existing shared launcher unless a separately authorized modification is essential and specifically proven scoped. No accidental Cobra changes.

**Cobra-only update**: build another APK of the **same package ID and permanent signing certificate**, keeping Infinity 2103420 behavior protected. No changes to Infinity Home, native Kodi runtime, Command Center, Resume Hub, Search, playback, data, Essential-First shutdown, UI/skin and individual Infinity settings/launch preferences. Cobra changes must live in independently owned source/classes/resources/capabilities.

**Shared files and DEX containers**: package-level `AndroidManifest.xml`, signatures and a DEX container may legitimately receive version/packaging/index changes in a future Cobra APK; a simple archive-file SHA difference in a shared container is **not** sufficient proof of Infinity behavior changing. For every future build, preserve each actual protected Infinity class, function, resource and byte-owned member via a reviewed allowlist, per-class/method/source/signature proof, exact Cobra-only scope, and negative cross-experience diff. Conversely, never claim the absence of a code change proves full runtime isolation if shared globals, services, storage or lifecycle behavior can change.

**Shared native code**: do not change any Infinity-owned/shared native runtime or shutdown code in a Cobra-only repair without explicit additional user authorization and a proven Cobra-only mechanism; unresolved cross-owner changes MUST be reported as blockers rather than silently changing Infinity. The user expressly rejected splitting into two apps or duplicating icons. Do not automatically introduce a second process or data migration.

**User data:** Install-over, preserve all original profile databases, progress, saved lists, code signer and credentials. No clean install, data wipe, launch chooser reset, downgrade or unapproved migration.

**Shutdown:** protected and working. User directive: **no repeated new shutdown stress/three-cycle tests as a condition of shipping Cobra-only modifications**. Preserve existing authenticated owners, receipts, write fences and Close handlers. A future real suspected persistence regression must be raised transparently, not concealed for this freeze.

**Changes requiring fresh approval**: Any proposal affecting Infinity behavior, shared native code, persistent storage ownership, chooser behavior, package name, installed icon count, or native shutdown must be identified and explicitly approved before altering the locked baseline. Later user-authorized Infinity updates may be built from 2103420 as a new protected successor with a separate acceptance gate. The lock is a **reference freeze for existing working Infinity**, not a ban on all future APKs or Cobra development.

## Source of truth and limitations
- This lock is an explicit user approval plus a **pinned Git branch** and SHA/packaging digest contract. It does not claim GitHub administration branch-protection or repository ruleset enforcement; do not move the branch by convention.
- The historical protected 2103407 source remains untouched and archived. **2103420 supersedes it as the working accepted Infinity baseline**, not as a rewrite of historical evidence.
- No new shutdown test or APK rebuild performed to record this lock.
- Actual completed signed build evidence: `repairs/infinity-final-closure-2103407/p0/SIGNED-420-BUILD-RESULT.json` and `repairs/infinity-final-closure-2103407/p0/REQUIREMENT-LEDGER.md`.

**Release disposition: INFINITY 2103420 — USER-APPROVED PROTECTED BASELINE. COBRA CORRECTIVE WORK MAY PROCEED ONLY UNDER SEPARATE AUTHORIZATION AND WITHOUT ALTERING INFINITY.**
