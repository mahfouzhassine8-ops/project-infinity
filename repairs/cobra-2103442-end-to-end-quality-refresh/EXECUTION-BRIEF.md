# COBRA — End-to-End Polish, Stability & Performance Refresh

**AUTHORIZATION: PROCEED — INVESTIGATE, IMPLEMENT, VERIFY, BUILD & DELIVER. THIS IS NOT AUDIT-ONLY.**

- Repository: `mahfouzhassine8-ops/project-infinity`
- Scope: **COBRA ONLY**, including Cobra-owned UI, modes, player interactions, performance, lifecycle and fit/finish.
- Working branch: `work/cobra-2103442-end-to-end-quality-refresh-20261101`
- **Accepted combined baseline:** Infinity/Cobra **2103442**
- Locked reference: `lock/infinity-cobra-2103442-user-approved-20261101`
- **Exact signed source:** `2e88f85250ef2e46952192cf0fdb42ac5af7c9c8`
- Signed APK: `Infinity-2103442-Combined-Original-Signer.apk`
- Baseline APK SHA-256: `88f968c53eb3d306db57de72419744f427554f7146f4f86e147b192f4f5e0bf5`
- Original signer certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`
- Acceptance target: Samsung Galaxy Fold 8 Ultra, Android 17, folded/front and unfolded/inner displays.
- Final deliverable: **one original-key signed combined APK, higher versionCode, install-over, with matching component ZIPs and hashes.** User acceptance required before any new lock.

## Primary mission

Perform a systematic **entire-Cobra** stability, performance, loading/refresh, responsiveness, interaction and visual-consistency upgrade. Trace measured or reproducible defects to their actual Cobra owner and implement minimal, tested corrections. Keep prior approvals byte-for-byte or behaviorally exact, where applicable. This is not a redesign and not a code-cleanup excuse.

## Absolute preservation: boundaries and reference behavior

1. **Infinity remains completely untouched**, with the exact **2103437** component carried by 2103442: skin, add-ons, provider integrations, persistence, tracking, resume/watchlist, loading, services and UI. Do not touch protected shared/native Android engine, chooser shell, chooser behavior, resources/launcher icons, signing/security infrastructure, user data, shutdown system, or unrelated build logic. Only a truthful, strictly scoped Cobra version/packaging update is allowed.
2. Preserve **every currently approved Cobra feature** and working screen. Do not restore rejected 2103441 or any older UI as a shortcut. No speculative refactoring, dead-code removal, global UI restyling, new controls or backend changes without evidence and authorization.
3. **Cards:** Existing cyan **LIVE** dot in its approved original position is the **sole** subtly pulsing playing indicator for the actively playing/ready channel. All other live dots are static; pause, buffering, idle or stop return to static. **No separate blue Now Playing dot**. Maintain Cards Preview, real tap-to-show menus, long-press/context menus, light/dark compatibility and the approved front/inner arrangement.
4. **Normal Pro on unfolded inner display:** Preserve approved wide player, adjacent original Now Playing information, horizontal existing channel navigation/tabs and spacious two-column lower channel rows—not rejected441's narrow right sidebar/empty-left design. Front, cover landscape, compact windows, Pro Sports and other modes retain their own existing layouts. Keep player/control callbacks, real channel identity and native row actions.
5. Retain accepted **2103439 Display visibility** and **2103440 Preview/menu** fixes, as preserved in 2103442; correct **Fullscreen / PiP / More** semantics, playback, mode persistence, Pro Sports, Multi-View, navigation, channel favorites/filters and existing three-dot ordering. Avoid arbitrary behavior changes.
6. **Never uninstall, clear app data, reset, replace signer or downgrade**. Deliver `com.projectinfinity.kodi` install-over using the original permanent certificate and a strictly higher `versionCode`. Protect every prior signed APK and lock; 2103442 is the only accepted reference until the user explicitly approves a successor.
7. **Cobra-owned edits only.** If the actual root cause requires a shared/native/Infinity/shutdown change, report precise evidence and **stop that subfix pending separate user authorization**. Other authorized Cobra fixes continue. Do not disable or weaken any safety gate or conceal test limitations.
8. Keep approved shutdown unchanged and do not turn unrelated shutdown requalification into an artificial final blocker; apply mandatory signing/security/package checks and relevant lifecycle tests.

## Workstreams — do ALL, with scoped independent checkpoints

### A. End-to-end owner inventory and defect baseline
- Map the *actual* registered Cobra mode list, UI routes, theme owners, channel/EPG/data bindings, player views, async workers, caches, layouts, overlay controls and restore paths. Include **Cards, normal Pro, Pro Sports, Multi-View and every other installed Cobra mode** without assuming an incomplete predefined list.
- Trace prior approved 439/440/442 behaviors and rejected441 regressions. Capture screenshot/interaction references and reproducible bugs.
- Establish comparable baseline measurements (including p50/p95 where appropriate): warm/cold time-to-usable, channel switch, EPG/load/refresh, scrolling/frame pacing, touch response, menu reveal, memory and allocation, mode change, player/return latency, crash/ANR evidence. State exactly which tests use live device, emulator, host, synthetic EPG or no real decoding.

### B. Lifecycle, stability and recovery
- Find and repair proven Cobra-owned crashes, freezes, ANRs, main-thread stalls, stale session callbacks, observer/listener leaks and lifecycle state loss.
- Exercise background/foreground, screen off/on as permitted by existing behavior, configuration changes, rotation, fold/unfold, window resize, back/home return, interrupted requests, channel and view switching, buffering/recovery and PiP enter/exit/reentry. Preserve actual playback and state.
- Avoid blanket catch-and-ignore, destructive resets, stale snapshots or excessive retries.

### C. Loading, refresh and smooth performance
- Profile cold/warm rendering and real EPG/provider/channel refresh, logo and artwork loading, redundant fetches/rebinds, excessive UI invalidation, focus transitions, allocation pressure and janky scrolling/transitions.
- Optimize confirmed hot paths only: coalesce redundant work, cancel obsolete tasks, cache with correct freshness/invalidation, preserve live updates, prevent duplicate listeners and bound memory use. Don't trade freshness or correctness for a misleading quicker load.
- Quantify before/after under comparable test conditions; report improvements and regressions honestly. No guessed percentages or unverified 'butter smooth' claims.

### D. Consistent polished appearance and accessibility
- Verify (and repair when clearly broken) safe-area insets, touch targets, menu location/reveal, long-press behavior, clipping, typography, text contrast, status/player control visibility, spacing, animation pacing, icon/selection visibility and actual color theme handling.
- Test existing Light/Dark/OLED palettes across all modes, including Cards. Keep established visual language, original layouts, previous polish and approved artwork. **No large-scale redesign, replacements or extra menus.**

### E. Playback, controls and cross-mode functionality
- Exercise actual Live/EPG/channel interactions: Play/Pause, active vs inactive/buffering channel indicators, Preview, Fullscreen, PiP, More, controls reveal/hide on tap, focus/long-press/context menus, channel selection, Favorites/All, navigation, Multi-View layout and return to previous mode.
- Verify routing, target ownership, cancellation and state after returning from PiP, Fullscreen, different channels, rotation and fold state. Don't mix up button action mapping.

### F. Galaxy Fold adaptive matrix
- Test **front folded, unfolded inner, portrait, landscape, resized/small window, font scaling, system bars/insets and fold/resize transitions**, including restoration of selected channel, focus, scroll and controls.
- Verify all relevant mode × screen × theme cases; layouts must remain fully usable without giant unused spaces, clipped sheets, unresponsive overlays or surprise changed proportions. Pro's approved inner composition is the reference, cover designs are preserved.
- Physical Android 17 Fold user acceptance is distinct from host/emulator assertions. Do not claim true-device PASS without actual evidence.

## Implementation and verification protocol

1. **Branch from exact source above.** Check the baseline lock/evidence before editing. Never change locked 2103442 or overwrite its binary/artifacts.
2. Start with a read-only inventory and prioritized register `finding / reproduction / owner / severity / baseline metric / proposed minimal correction`. Then **implement** confirmed issues rather than stopping at an audit.
3. Use reviewable checkpoints (stability, rendering/UI, refresh/performance, interactions, matrix integration). Each fix should have root cause, touched owner, minimal diff, tests, regression coverage and measured outcome where applicable.
4. Run focused tests promptly after each edit; reuse verified unaffected evidence with exact source/hash proof. Then perform broad end-to-end Cobra-mode regression and build/package verification. No fabricated outcomes or silent skips.
5. Verify protected component vector and member hashes against **signed 2103442**. Keep Infinity 2103437, minimal Android/shared/native, chooser shell, assets and protected DEX/classes unchanged except explicitly approved Cobra methods/resources and required version evidence. Include a machine-readable changed-member and class/method allowlist.
6. Require correct package ID, version monotonicity, original signer, alignment and exact matching signed APK/component ZIPs. Do not bypass safety, signing or version gates.
7. Final target is a **real permanently signed testable combined APK** (not an unsigned artifact, mockup, checklist or audit-only report), plus matching individual component ZIPs, signing/workflow links, sha256 sums and preservation receipt. Keep 2103442 available.
8. If a gate truly cannot be performed, report exact error and previous passing evidence and continue independent safe work. Never falsely declare an APK created or Android acceptance complete.
9. **No automatic acceptance or new lock.** User runs the install-over APK on the actual Galaxy Fold and decides promotion.

## Required completion report

- Workstream/checkpoint status: confirmed / repaired / tested / deferred / out-of-scope.
- Every Cobra mode covered, every Fold display/rotation/theme tested, and what remains a real-device acceptance check.
- Comparative performance/ANR/memory/crash evidence with environment and conditions.
- Preservation diff and component hashes against protected signed 2103442.
- Actual successful original-key signed APK and exact component ZIP links/checksums, install-over verification.
- Physical Galaxy Fold acceptance checklist including Cards LIVE pulse/Preview/menu; Pro wide inner two-column layout and unchanged cover; Pro Sports/Multi-View; Fullscreen/PiP/More; scrolling/EPG; Light/Dark/OLED; fold/unfold; resume/return.
- Known blockers must be explicit and categorized; never present synthetic host coverage as native Samsung verification.

**DO NOT finish as audit-only. DO NOT widen the source ownership. DO NOT introduce unrelated regressions. Drive the approved Cobra-only scope to tested implementation and signed APK delivery.**

_2026-11-01 kickoff: this file is the execution assignment only. No repair, test result, rebuilt APK or completed signed release is claimed by creating it._
