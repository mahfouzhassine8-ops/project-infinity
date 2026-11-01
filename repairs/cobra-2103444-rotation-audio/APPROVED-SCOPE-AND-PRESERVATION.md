# COBRA — 2103444-Preserved Rotation + Fullscreen Audio Refinements

**Authorization: PROCEED WITH THESE TWO REFINEMENTS ONLY; investigate, implement, verify, build an original-key signed install-over APK with matching components. No unrelated changes.**

**This document is the authoritative post-2103444 feature/preservation scope.** It supersedes the outdated **2103442 baseline** language in the earlier rotation/audio draft, but does **not** reopen the completed quality-refresh workstreams or authorize broad additional changes.

## Exact protected starting point

- Repository: `mahfouzhassine8-ops/project-infinity`
- Dedicated working branch: `work/cobra-2103444-rotation-audio-preserved-20261101`
- **Signed/current user-approved combined baseline: 2103444**
- Locked reference: `lock/infinity-cobra-2103444-user-approved-20261101` (must NEVER move, replace or edit)
- **Exact original signed source: `1b7a4ef16524854fab77a1c974538aee8a1132bb`**
- Signed `Infinity-2103444-Combined-Original-Signer.apk` SHA-256: `38dff935ffc0967e2c16e8d61e6e4bfd693fcb73bbaa130e8fa354e468b85a76`
- Original permanent signer certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- **Infinity remains exact 2103437 component**, `INFINITY.zip` SHA-256: `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d`.
- **Minimal/shared Android component** baseline SHA-256: `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`.
- **Chooser shell component** baseline SHA-256: `cfc83c9caf57bc4978d8a12625537e90515be400a48d0f6359695c962d20f1da`.
- Previous signed 2103442 preserved as independent recovery baseline.
- Actual acceptance target: Samsung Galaxy Fold 8 Ultra / Android 17, folded front and unfolded inner screens.

## Absolutely forbidden changes

**Do not modify Infinity, Kodi core, native libraries, shared Android engine/Media3 bridge, skin, add-ons, providers, command/watched/resume systems, user stores, background services, shutdown, original signing/security policy, chooser behavior, icons, unrelated resources, or other unrelated Cobra features.** This includes enhancements to anything merely discovered during an audit without specific user authorization.

Preserve original Cobra mode behavior, existing functions, channel navigation, EPG, Favorites, saved settings, data, modes, Cards LIVE sole-pulse policy, Cards Preview and context menus, Pro approved inner geometry and two-column rows, front/cover layout, Pro Sports, Multi-View, 439 Display visibility, 440 Preview/menu, current button action mapping (Fullscreen / PiP / More / Display), and theme light/dark/OLED compatibility. Existing separate padlock control stays untouched.

The signing/build pipeline and version metadata may only be updated to the narrow extent *required* to produce a truthful higher-version Cobra-only package; no test-gate relaxation. Any new scope crossing into native/shared/Infinity/shutdown requires **explicit separate approval**, not an inferred dependency exception.

## Authorized refinement 1 — universal two-state rotation button

Keep the **existing Cobra rotation button**, implement one **global Cobra rotation policy owner** honored consistently by all actual installed view modes (including Cards, Pro, Pro Sports, Multi-View, mobile/grid/compact as relevant) and their Fullscreen playback surface.

Behavior (exact):
1. **First press while rotation is locked/inactive: turn automatic rotation ACTIVE.** Display follows supported device orientation.
2. **Second press while active: lock to the exact orientation CURRENTLY DISPLAYED**, landscape or portrait. **Do not force a flip or snap back to a default.**
3. Every subsequent press alternates ACTIVE -> LOCK CURRENT -> ACTIVE. No modal or unrelated extra controls.

Honor supported physical orientation and Fold/window restrictions. Preserve the currently selected state while switching mode, entering/exiting Fullscreen, handling PiP return and folding/resizing as the platform permits. Do not reset the rotation policy silently or restart video. Ensure existing icon reflects active-vs-locked status in all themes, but do not change the independent padlock control. Use lifecycle-safe ownership and no duplicate orientation listeners. Do not change global Android auto-rotate setting or unrelated apps.

## Authorized refinement 2 — universal Fullscreen mute/unmute

Insert **exactly one new Mute/Unmute button** on **every Cobra view mode's Fullscreen bottom toolbar**, **between Channels and Display**, with the exact order:

**Channels | Mute/Unmute | Display | Multi-View | PiP**

Use the approved existing Cobra button language/style and native player audio ownership; adjust spacing adaptively to fit all five buttons with readable icons/touch targets on the Fold cover and inner screen. Keep safe-area/insets compatibility without clipping, overlap or unexpected video resizing.

**Tap to mute the actual currently audible Cobra playback stream. Tap again to unmute and restore the prior player audio volume**, with correct icon/audio state. Keep actual player session and stream uninterrupted. Synchronize with actual audio state, external volume/routes and Multi-View's existing active-audio-owner policy; do not override another stream's selection, reset player, change global phone/ringer volume or affect audio in unrelated apps.

Preserve the original actions, routing, labels and order of **all other controls**. Test Mute/Unmute on each Fullscreen entry path and across pause, buffer, channel changes, orientation changes, fold/unfold, PiP and return to mode.

## End-to-end implementation and nonregression gates

1. Start from **exact signed source 2103444**, never signed 2103442 or rejected 2103441. Reuse accepted work, do not roll back the three 2103444 measured presentation optimizations or other already accepted 2103444 behavior.
2. Map real rotation handler/state and Fullscreen control renderer/audio owner. Edit only the minimum Cobra-owned methods and tightly scoped Cobra presentation assets required for the two new refinements; changes to another mode are allowed only to implement the same universal behavior or prove regression coverage. Document exact diff per class/method.
3. **Before each change and before signing** compare all protected source files/class owners against pinned 2103444. Build allowlist, denylist and hashes. All unchanged APK member bytes must match 2103444; explicitly verify every one of the **47 existing native libraries**, Infinity DEX and all Infinity ZIP bytes, chooser DEX/assets, protected shared DEX/resources, Icons, shutdown pathways and signature policies. If any hash drifts, **FAIL the build**; investigate, revert drift, do not sign/promote.
4. New APK `com.projectinfinity.kodi` must use higher `versionCode` than 2103444, same original signing certificate, install OVER (no uninstall, clearing data, reset, migration or user-setting loss). Only approved Cobra DEX/classes and truthful version metadata may differ from 2103444; document signature members regenerated by original signer.
5. Test mode × screen × orientation × theme × Fullscreen and back, including front/inner Fold simulation, portrait/landscape, small window/insets, Cards Preview/LIVE, Pro geometry, Pro Sports, Multi-View, existing player controls and PiP. Explicitly test multiple rotation taps and locking CURRENT landscape/portrait, preserving state when switching modes. Explicitly test mute/unmute and audio state/restore while stream continues. Long-press, menus, context, Display, More and Favorites must remain functional. Use host/Android hardware test provenance accurately.
6. Do not report 2103444 as full Android matrix PASS: its exact signed original-key install-over succeeded and host tests passed, but candidate Android observer timed out (2,084 ms against 2,000 ms readiness limit), preventing completion of its full interaction matrix. Do not conceal or reclassify that evidence; separately verify the new candidate against its actual tests.
7. Continue through safe, separately tested checkpoints. **One final original-key signed install-over APK** with matching individual component ZIPs, signature/checksum/source/run links, hash-preservation proof and user-facing physical Galaxy Fold acceptance checklist. **Do not lock successor automatically; user approval required.**

## Stop conditions / deliverables

A breaking change to any out-of-scope byte/member, native library, Infinity package or unrelated Cobra owner is a release BLOCKER. Restore it, do not rationalize it as harmless. If required behavior cannot be delivered without modifying protected code, stop *that particular feature*, explain exactly which owner blocks it, and wait for explicit authorization; safe independent Cobra-owned work may continue.

Report **implemented vs specified**, full list of touched classes, exact byte comparisons, pass/fail/blocked tests, latency/memory evidence where available, original-signature correctness, and separately physical Fold acceptance. Never claim signed APK delivered without an actual successful signing run and verified artifact.

**Approval record:** user requested universal rotation first, universal Fullscreen Mute/Unmute next, followed by explicit preservation of Infinity/Kodi and all unrelated components. This document is specification only, not a claim that features have been implemented.
