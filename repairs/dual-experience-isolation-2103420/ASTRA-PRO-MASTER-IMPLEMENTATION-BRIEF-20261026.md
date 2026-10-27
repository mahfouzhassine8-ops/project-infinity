# ASTRA PRO EXTRA HIGH / GPT-6.1 WORK — INFINITY + COBRA TRUE INTERNAL SEPARATION
## SINGLE APK, ONE ICON, TWO INDEPENDENT EXPERIENCES, ZERO APPROVED-CODE ROLLBACKS

**AUTHORIZATION: PROCEED NOW — INVENTORY, ARCHITECT, IMPLEMENT, INTEGRATE, ENFORCE, VERIFY, BUILD AND DELIVER THE ISOLATION FOUNDATION.**

**Priority:** Critical / prerequisite to all new Cobra feature corrections and simultaneous Infinity/Cobra work.  
**Repository:** `mahfouzhassine8-ops/project-infinity`  
**Dedicated implementation branch:** `work/infinity-cobra-isolation-from-2103420-20261026`  
**Starting exact frozen commit:** `883c64a4de6f87077893921454de71bba850235b` (the signed 2103420 code at `ddc054583c5e5f3cd04c328e131cb76af8d4728b`, followed by build receipt only).  
**Protected lock — NEVER MODIFY:** `lock/infinity-2103420-user-approved-baseline-20261026`.  
**Locked APK SHA256:** `ae641e74bbe0b3360d103254d9bc5425fe1558f625466a99f1da9f16414fef26`.  
**Original permanent signing certificate SHA256:** `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.  
**Successful baseline signed build:** run `40413893227`, artifact `12695160919`.  
**Android package must remain:** `com.projectinfinity.kodi`.  
**Physical user baseline:** Samsung Galaxy Fold 8 Ultra, Android 17 / API 37. User approved Infinity 2103420: snappy Home, working PiP/player/Continue, Essential-First shutdown, one-tap Ask Every Time.

**MISSION.** Deliver the internal separation and automatic anti-rollback release system that should have existed from the start. Keep exactly **one installed Android app, one home-screen icon, one signed install-over APK, and the unchanged Choose Your Experience interface**. Internally, develop and version Infinity and Cobra separately so changing either one's features (PiP, player, navigation, settings, etc.) does not modify or revert the other one's approved implementation or data. Work on both tracks concurrently if desired, but publish only integrated APKs containing the latest **approved** version of both.

**Do not produce another audit-only handoff, and do not substitute a directory layout diagram for working code and a real build gate.** Astra owns the architecture, dependency review and independent acceptance audit. A single GPT-6.1 Work implementation owner performs repository edits, integration and original-key signing; coordinate through explicit checkpoints, never competing pushes to the same branch. If a single capable session can do both, it may implement and review in sequence with independent source/proof artifacts. This handoff does NOT authorize Cobra feature repairs, Infinity redesign, or destructive storage/process migration.

**Scope clarification against old Infinity-only work rules:** Earlier `AGENTS.md` and Infinity corrective handoffs say "COBRA IS OFF LIMITS" because those assignments prohibited accidental Cobra changes. **This new explicit user authorization allows ONLY the minimum Cobra-owned code/build/data-ownership restructuring needed to establish independence, while preserving Cobra's exact existing behavior.** It does NOT authorize Cobra feature fixes, Infinity rewrites, shared native changes, new shutdown tests, or unilateral release. If an implementation conflict cannot be isolated, document it and stop that particular edit. Do not silently treat old Infinity-only "no Cobra edits" as preventing all authorized boundary engineering; equally, do not treat this scope clarification as a blanket permission to redesign Cobra.

### 1. Fixed product invariants — MUST NOT CHANGE

- ONE APK, ONE `com.projectinfinity.kodi` app identity, ONE launcher icon, original permanent signer, monotonic package `versionCode`, ONE Choose Your Experience with its remembered Infinity / remembered Cobra / Ask Every Time / one-time launch options. NO second package, launcher alias icon, split APK distributed as another app, dual-install, changed user-visible launcher, or duplicated home-screen icon.
- Preserve **100% of Infinity 2103420**: Kodi engine, Home/skin, Search, Resume Hub, Continue Playing/Watching, watched/favorites/lists/provider identity, player, PiP, fullscreen/background audio/rotation, Health Center, fast loading and proven Essential-First Power shutdown. Do not delete an Infinity feature because Cobra also has it.
- Preserve **100% of the currently bundled Cobra experience**: Cobra player and PiP, fullscreen, Sports, Multi-View, Pro/Mobile modes, settings, preview/audio, navigation, timers/recording/reminders and any other shipped behavior. Distinct implementations may use the same Android OS APIs; do not remove/reassign features.
- Keep all installed user data, application UID, source/profile databases, cached metadata, settings, launch preference and original package signing continuity. **Install over; no uninstall, app-data clear, profile reset, forced downgrade, unapproved data migration or cosmetic redesign.**
- Freeze working shutdown. No new shutdown scenario/three-cycle or mandatory shutdown workflow added to the architecture packaging gate. Preserve all original shutdown-owned code, native/Java receipts, guards, normal Close behavior and saved-state ownership. If a proposed process or manifest change would alter shutdown dependencies, **stop that part and record the exact conflict** rather than silently crossing the freeze. Deliver unaffected isolation/release protections separately.

### 2. What “fully independent inside one APK” CAN and CANNOT mean

Aim for **no cross-experience mutable feature implementation, state, version or update coupling**. A Cobra-only update must not alter an Infinity-owned method, native function, resource, PiP contract, playback state, database, setting or startup/shutdown route; and vice versa. Every exception must be explicitly owner-classified, reviewed and blocked until approved.

This is NOT two Android sandboxes. One APK necessarily shares app ID, signing identity, Android UID/permissions, manifest/packaging, the launcher shell and minimal stable OS adapters. Two separate Gradle library modules or asset trees do NOT magically separate processes, data or OS permissions. Be truthful about this necessary shared **container** while removing unnecessary feature-code and mutable-state sharing. No promise of mathematically impossible zero possible runtime influence from an Android system service.

### 3. Non-negotiable first step: inventory THE ACTUAL signed 2103420

Read the immutable signed APK (not speculative source), its six matching ZIPs, manifest components/process declarations, all DEX class/method references, native `.so`/JNI entrypoints, Kodi/Python addons/skin XML and every file/provider/service/database/prefs key/worker touching either experience.

Produce machine-readable ownership/provenance inventories and a human-readable graph, classifying **each actual member and cross-call** as:
`INFINITY`, `COBRA`, `CHOOSER_SHELL`, `MINIMAL_ANDROID_CONTRACT`, or `UNRESOLVED`.
Do NOT use prefixes like `Cobra*` as the sole classifier: trace actual call sites, static singletons, callbacks, PiP/media-session/audio-focus behavior, native shared libraries, broadcast receivers, Boot/alarms, dependency injection, shared UID private directories and preferences.

Known overlap requiring investigation: `Main` runs in `:kodi`; `InfinityLiveActivity` (Cobra) and `InfinityCloseGuardService` (Infinity) are currently in the default process with `Splash` unless independently reconfigured. Several Cobra and Infinity Java classes are in `classes.dex` together. **DEX coexistence itself isn't behavior coupling**; the shared mutable calls/process/global state need actual mapping. Preserve the entire frozen close route.

First implementation checkpoint: complete member/owner graph, unknowns, exact source/member fingerprints, and a list of truly shared mutable dependency edges to eliminate. Unclassified or unreviewed cross-owner writes/behaviors are blockers, not accepted as “already separated.”

### 4. Actually create independent module boundaries, without rewriting the app

Prefer two **library/source/asset feature modules** packaged into ONE base Android application when compatible with the existing custom Kodi/native APK build:
- `infinity-core`: Infinity native/Kodi and first-party services, player/PiP/UI, Resume Hub, profiles/settings, native shutdown ownership.
- `cobra-core`: Cobra player/PiP/Sports/Multi-View/Pro/mobile, services, settings, assets and all Cobra-owned data.
- `app-shell`: current one app icon, unchanged experience chooser and authoritative launch preference.
- `platform-contract`: only minimal versioned Android interfaces that must be shared (e.g. approved OS PiP/permission entry and well-defined startup/IPC messages), with **no mutable Infinity/Cobra feature state**.

**Do not assume this repo currently uses conventional Gradle.** If a wholesale Gradle conversion would threaten the signed native engine, hashed Command Center source, APK DEX integrity or shutdown, use reproducible asset/module boundaries and the current signed raw-APK assembler instead. Do NOT create two `com.android.application` IDs or two installed packages. Each feature module must have a clear entry contract and independently signed/hashed member inventory. The other feature must never import its mutable implementations.

Separate per-experience persistent state ownership and namespace; avoid migrations when existing separate paths suffice. Before relocating any settings/DB/cache, prove lossless identity, versioned migration, stable rollback and install-over durability on disposable copy—not the user's actual files. Cross-module transactions/callbacks may only use a documented minimal interface and must never write the other module's private state.

Consider a Cobra-only Android `:cobra` process **only after** tracing Cobra services, PiP, recording/reminders, shared app process globals, chooser IPC and Infinity `InfinityCloseGuardService`. Do not change process attributes of the launcher or shutdown coordinator under this authorization. If a truly independent Cobra process requires changing protected lifecycle behavior, stop and seek explicit scope approval; the existing good Infinity close cannot become collateral damage.

For the structural refactor stage, the **default expectation is byte/function-equivalent original functionality**, not “improvements.” Identity-preserving movement of code may alter global DEX container bytes or resource indices; prove each protected class/function/resource unchanged by canonical method/source fingerprints and binding resolution, not by blindly comparing only whole `classes.dex` hashes.

### 5. Build REAL independent versions + one centralized integrated-release authority

Implement an executable release registry/lock ledger and deterministic assembler, stored in the repository and consulted by the signing pipeline:
- `app_versionCode` (monotonic single Android package), original cert SHA and package ID.
- `infinity_component_version`, `cobra_component_version`, each approved source commit, exact member/method/resource digest set, settings/schema version, owner manifest, combined release source and signed artifact digest.
- Initial state: Infinity **2103420** is approved; Cobra is **the exact Cobra implementation bundled in signed 2103420**. Do not invent an already existing independently numbered Cobra version. Assign an initial internal Cobra component baseline label from the actual inventory.

**Every time an APK is about to be signed, a hard release gate must confirm it includes the latest approved versions of BOTH**. Source branch names or highest APK versionCode alone are never enough. Use actual packaged contents and pinned fingerprints, including identity of unchanged owners inside shared DEX/manifest containers. Fail closed on an unowned change, missing module, mutable cross-owner import, source/signature/hash mismatch, stale side, deprecated settings payload, unexpected dual launcher, or lower/equal APK versionCode incompatible with the approved release policy. Do NOT “continue-on-error” an owner mismatch.

Parallel development is allowed; **parallel independently installable APK releases are NOT**. One coordinator integrates the latest accepted Infinity and Cobra branches, rebases/reconciles against the most recently approved combined artifact, builds one original-key APK and publishes it only after required owner checks. An old-base Cobra APK containing outdated Infinity code must be rejected even if it has a larger Android package versionCode. Same rule in reverse. Save the accepted combined version pointer **only after explicit user acceptance**; unfinished builds must not replace it.

Demonstrate these negative and positive combinations with controlled test module changes (illustrative, not assigned versions):
- `App421 = Infinity421 + Cobra420` (Cobra fingerprint unchanged).
- `App422 = Infinity421 + Cobra422` (Infinity421 fingerprint unchanged).
- Attempted `App423 = Infinity420 + Cobra423` MUST FAIL at packaging/signing before user installation.
- Attempted unexpected change to approved Infinity PiP/Resume/shutdown during a Cobra-only update MUST FAIL. Reverse Cobra-preservation control during an Infinity-only update MUST FAIL.
- A deliberately altered common manifest entry, shared runtime callback or persistence ownership that affects the non-target experience MUST FAIL or be explicitly gated for a separate authorization.

### 6. Focused real-world acceptance, NOT stress theater

Do not rerun generic 50/30/20 cycles or introduce new shutdown tests to make this architecture “pass.” Source/member/DEX fingerprints and deliberate negative build controls are mandatory. For changed feature routing, use a **small realistic representative smoke walkthrough** with synthetic/disposable profile state only (not production data):
- One app icon opens the same chooser and obeys Ask/remembered Infinity/remembered Cobra/just once.
- Infinity launch retains actual Home, Search, Continue Playing/Watching, player and PiP; Cobra launch retains its player/PiP/Sports/Multi-View/Pro as currently supported. Check inactive experience does not initialize unintended background workers or write the other side's state.
- Cross-owner settings and progress remain identical before/after the OTHER experience's update. Verify with exact inventory/readback, not just an unchanged UI screenshot.
- Release-assembler positive/negative rollback tests above, using independently developed module branches and exactly one integrated install-over APK.

**Do not claim device acceptance from source proofs.** The user tests the candidate on the physical Fold ONCE after the internal separation and safeguards are implemented and the signed APK is prepared. The already-user-approved working 2103420 is the rollback/reference source; do not suggest Android uninstall, data wipe, unsafe downgrade or a second installed package.

### 7. Actual deliverables — no paperwork-only finish

Produce and commit:
1. `OWNERSHIP-MAP.json`: every APK/runtime owned member, stable interface, cross-process/cross-state call, exact hash, unresolved edge and owner.
2. Source/build modularization actually wired into the production packaging pipeline (Gradle libraries only where compatible, otherwise deterministic signed asset/module assembly), with no lost Infinity or Cobra feature.
3. A checked-in **per-experience release manifest + accepted-combined-release registry**, a real build/signing anti-rollback gate and its negative-control executable tests; no arbitrary installer can be magically controlled, so apply this guarantee to the official signed release pipeline.
4. A complete **before/after protection ledger** identifying unchanged Infinity 2103420 code/data contracts, unchanged Cobra code/data contract, allowed shared shell changes, signer/package identity, and exact exceptions, with no hidden shared-process risk.
5. ONE permanently signed install-over APK of the SAME app, same one icon and chooser, exact matched components, full SHA256, owner/version manifest, build run, simple installation order, and a brief truthful `READY_FOR_FOLD_CHECK` / `BLOCKED_BY_<EXACT_REASON>` status.
6. Final physical Fold acceptance requested only once the candidate is meaningful. No automatic lock/promotion before the user approves it.

### 8. Execution control and non-negotiable failure policy

Astra Pro Extra High should first **approve the concrete owner map and minimal isolation seam**, then have exactly one Work implementation owner integrate code and release guards on this dedicated branch. Do not launch parallel autonomous branches that overwrite each other's commits or move the locked source. The implementer must finish implementation/build, not simply produce yet another planning document.

Where actual source proves the current shared runtime makes a specific change unsafe, **stop only that operation**, identify the exact classes/process/service and propose a safe alternate isolation method. Continue independent ownership/release-gate work rather than declaring the entire goal impossible. Never secretly change working shutdown, shared Cobra/Infinity player functions or persistent data. No automatic Cobra feature-correction scope is granted until isolation is demonstrably complete.

**FINAL ACCEPTANCE SENTENCE TO DEMONSTRATE WITH REAL ARTIFACTS:**  
“One installed APK, one icon and the existing Choose Your Experience; Infinity and Cobra each retain their own features/state/version; a Cobra-only update preserves approved Infinity exactly, an Infinity-only update preserves approved Cobra exactly, and a stale combined APK is rejected before signing.”

**Documentation used for Android constraints:** https://developer.android.com/guide/components/processes-and-threads.html ; https://developer.android.com/studio/projects/android-library ; https://developer.android.com/google/play/app-updates
