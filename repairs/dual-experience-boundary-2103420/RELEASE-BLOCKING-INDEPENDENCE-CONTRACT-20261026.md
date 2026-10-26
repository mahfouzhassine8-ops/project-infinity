# INFINITY 2103420 / COBRA — RELEASE-BLOCKING INTERNAL INDEPENDENCE

**Priority:** Architectural prerequisite to *any* Cobra feature repair or simultaneous Infinity/Cobra development.  
**Baseline:** User-approved Infinity 2103420, immutable lock `lock/infinity-2103420-user-approved-baseline-20261026`.  
**Status:** SOURCE INVENTORY / REQUIRED WORK, **NOT IMPLEMENTED**. This file is a document and does not change signed APK behavior, Cobra, shutdown, data, launcher, or manifest.

## User's intended product and hard acceptance

- Exactly **one signed install-over APK**, **one installed package and one app icon**, **one Choose Your Experience** (Remember Infinity, Remember Cobra, Ask Every Time, one-time launch).
- Keep **100% of both experiences' existing features**. Both retain PiP, player, fullscreen and display controls; Infinity's Resume Hub/Search/Essential-First and Cobra's Sports/Multi-View/Pro features remain distinct.
- Changes to Infinity-owned source/data must never silently change Cobra-owned functions; changes to Cobra-owned source/data must never silently change frozen Infinity 2103420. No reset, duplicate installed package, extra icon, split application or unapproved migration.
- Independent **internal component** version/fingerprint, but one monotonically upgraded Android package versionCode and one signing identity. Future APKs must contain the newest approved **both** components; reject stale one-sided builds before signing.
- A literal "nothing shared besides the chooser" is impossible **within one Android package**. The package name, app UID/permissions, AndroidManifest, original signing certificate and installation are necessarily shared; the user is asking for **no mutable feature code/state/runtime crossover**, not a false claim of separate OS sandboxes. The app's process separation does not change its shared app UID. Never claim Android security isolation equivalent to two packages.
- Do not move the protected lock branch. Avoid rewriting the proven Infinity shutdown or performing new repetitive shutdown tests merely to satisfy an artificial gate.

## Grounded read-only inventory of the actual signed 2103420 APK

Artifact: GitHub run `40413893227` / `12695160919`; exact signed APK SHA256 `ae641e74bbe0b3360d103254d9bc5425fe1558f625466a99f1da9f16414fef26`. The manifest and DEX inventory were read from this actual package, not inferred from class names alone.

Manifest `com.projectinfinity.kodi` currently registers:
- `com.projectinfinity.kodi.Splash` (shared/default app process, launcher).
- `com.projectinfinity.kodi.Main` (`android:process=":kodi"`, `supportsPictureInPicture=true`); `InfinityKodiEntryActivity`, `InfinityPowerControlActivity` and most native Kodi content providers/services also run `:kodi`.
- `com.projectinfinity.kodi.InfinityLiveActivity` (existing Cobra/live experience, **no separate process attribute**, so main/default process, `supportsPictureInPicture=true`).
- `com.projectinfinity.kodi.InfinityCloseGuardService` (**no separate process attribute**, so same main/default process as Cobra's activity and Splash).
- `InfinityCobraRecordingService`, `CobraSportsReminderJob`, `InfinityCobraBootReceiver`, `InfinityCobraReminderReceiver` (all presently without dedicated process attribute).
- `InfinityAskEveryTimeActivity` (existing main/default preference action).

DEX packaging: `classes.dex` includes both many `Cobra*`/Cobra-support classes and `Infinity*`/platform coordinator classes in one DEX container; `classes2.dex`, `classes3.dex` and new `classes4.dex` are also in same APK. Merely renaming/copying DEX or comparing only the `classes.dex` file SHA cannot prove or create behavior independence.

**Current finding:** Existing Infinity native process is partly separate; **Cobra activity still shares the main app process with chooser and Infinity CloseGuard**. There is no established fully separated ownership + cross-update anti-rollback release machinery. Do not state that users already have zero functional sharing, nor that moving Cobra to `:cobra` is automatically safe.

## Required implementation stages — execute BEFORE Cobra fixes

### 1. Actual ownership + call/data-flow map (freeze 2103420)

From the actual signed baseline, enumerate every meaningful class/method, native library entry, package member/resource, skin XML and addon, activity/service/receiver/provider, PiP/player/audio/display/recording callbacks, file path, SharedPreferences key, DB and background job. Classify owners as `INFINITY`, `COBRA`, `LAUNCHER`, or `SHARED_ANDROID_CONTAINER`; no unclassified code may ship under a purported Cobra-only/Infinity-only correction.

Map **actual cross-owner calls and shared mutable state** (including code that exists under neutral names or `InfinityCobra*` classes, global singletons, pref keys, UID-private file paths, and calls through shared Android services). Only treating a class name prefixed Cobra as isolated is insufficient.

### 2. Separate changeable runtime and state, without losing features

- Isolate Cobra-owned player, PiP, Sports, Multi-View, data/settings/cache/worker/lifecycle from Infinity-owned player, PiP, Search, Resume Hub, shutdown, data/settings/cache. Each can use Android SDK services without using the other's mutable implementation.
- Keep launcher only as experience decision and existing preference owner. Reuse stable explicit launch protocol; avoid any extra default-process initiation of the other experience.
- Investigate the concrete current overlap: Cobra's main-process `InfinityLiveActivity` and background components vs Infinity's `InfinityCloseGuardService` in same default process. A dedicated `:cobra` process is a **possible** containment mechanism, not an automatic change. Examine IPC, lifetime, PiP, media/audio focus, service, boot, alarms, provider and legacy data use first. Manifest/process edits can affect shutdown even if its own bytecode is unchanged; do not execute such an edit without explicit authority to cross the locked shared lifecycle boundary.
- Use separate namespaced persistence and authenticated owner checks while preserving legacy values. Do **not** move/reinitialize user data or copy it into a new profile before validated, reversible migration. A separate process does NOT give separate UID or filesystem security boundary.

### 3. Independent versions + mandatory integrated release assembler (not independent APK installs)

Track `infinity_component_version`, `cobra_component_version`, each approved source tree/member/classes/resource digest set, integration commit and current app versionCode, all bound to **one original signing identity**.

Every candidate APK must:
1. Start from **latest approved combined release**, not solely the original 2103420 fork, for its unchanged side.
2. Contain current approved source and exact fingerprints for the experience **not** being updated, including method-level checks when a shared DEX container is repackaged.
3. Reject any downgrade, missing member, changed unowned member, unexpected cross-owner call, changed persistent schema/UID path, manifest misrouting, certificate mismatch or fallback to an older branch—even if total APK versionCode increased.
4. Combine concurrent Infinity and Cobra changes into a **single newer signed APK** before installation; the APK must retain latest approved version of both. Independently built old-base APKs are engineering inputs ONLY, never distributable sequential install-over updates.
5. Explain every approved exception and provide a summary: `APK 421 = Infinity421/Cobra420`; `APK422 = Infinity421/Cobra422`. These are illustrative numbers, not assigned releases.

Protect private signing material; note that such a CI rule protects releases made through the controlled builder, not arbitrary externally signed/sideloaded APKs. Only a **single release authority** can enforce this workflow.

### 4. Proof required before claiming the boundary exists

- Read-only hash-verified unchanged 2103420 parent; no Cobra remediation feature is allowed to quietly rewrite Infinity's fixed player, PiP, Home, data, shutdown or chooser.
- Two *separate* scoped change simulations/candidates: an Infinity-only change must preserve all approved Cobra-owned members and Cobra state; a Cobra-only change must preserve all approved Infinity-owned members/state. Negative controls deliberately modify the non-target owner's class/settings/manifest to confirm build fails.
- Assert selected experience never starts unneeded workers/services in the other experience, excluding specifically authorized shared launcher/coordinator and Android package constraints.
- Realistic smoke checks: Cobra PiP/Pro/Sports/Multi-View and Infinity PiP/Continue/launch preferences work unchanged, with no cross owner state corruption. Keep normal user data untouched. Source equality alone is not enough if shared process state/manifest changed.
- Existing user-confirmed 2103420 **Essential-First shutdown stays frozen**; do NOT add shutdown-stress suites or mutate native persistence solely to make a release test green. If a proposed process boundary changes shutdown's dependency graph, stop and surface the conflict, not fake an unchanged result.
- Report actual `OWNERSHIP COMPLETE`, `RUNTIME ISOLATION COMPLETE`, `ANTI-ROLLBACK RELEASE GATE COMPLETE`, `CROSS-EXPERIENCE NEGATIVE CONTROLS PASS` with exact signed artifact evidence. Do NOT say `100% isolated` if any significant cross-owner mutable dependency remains.

**No new Cobra correction APK should be declared safe for installation until the ownership and release safeguards have real implementation and evidence.**

## Locked baseline and user boundary

Never create a second icon, new app ID, separate installed APK or rewrite shared chooser. Infinity 2103420 is a working accepted user baseline; when sharing is unavoidably tied to the existing shutdown or Android container, document that actual technical limitation and seek explicit scope authorization instead of misrepresenting it as zero sharing. This document alone does **not** establish or implement these safeguards.
