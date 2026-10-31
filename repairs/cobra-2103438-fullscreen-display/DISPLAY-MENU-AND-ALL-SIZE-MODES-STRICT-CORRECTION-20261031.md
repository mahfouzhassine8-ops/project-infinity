# Cobra 2103438 — Fullscreen Display button and ALL existing Display/size-mode options
**AUTHORIZED SCOPE AND NON-NEGOTIABLE PRESERVATION — October 31, 2026**

## Direct user report / intent
The user supplied an actual Galaxy Fold screenshot `20797.jpg` showing **Cobra fullscreen playback** of USA: Nicktoons, with the bottom navigation/control strip **Channels | Display | Multi-View | PiP | More**.

**Physical-device defect reported:** **"Pressing on display does not pop out menu"**. The **Display** control is the **second button in the bottom fullscreen control row**, immediately next to Channels. This is **not** the top system brightness/sun icon, another Cobra view selector, the chooser, or More/overflow.

**User's additional authorization:** "also might as well have codex look for issues for each size mode thats in there and Repair if needed." Interpret this as an **end-to-end audit of every EXISTING size/aspect choice exposed by the fullscreen Display/Aspect menu**, followed by targeted repairs **only to defects demonstrated in those options**. This is **not an authorization for a generic Cobra-wide audit or new display features**.

**User's preservation instruction:** "Everything else besides that scope is preserved and not to be touched".

The screenshot establishes what control and playback presentation were on screen, not click dispatch or the root cause. Do not attribute a fault to a specific listener, hidden sheet or video-transform method without direct reproduction.

## Authoritative immutable signed release (working baseline with one issue)
- Repository: `mahfouzhassine8-ops/project-infinity`.
- **Exact signed 2103438 commit:** `a5f721578c53e026a26cf21d929fbdad530f6d17`.
- User-approved recovery lock **`lock/infinity-cobra-2103438-user-approved-pending-one-fix-20261031`** must stay at that SHA.
- Signed APK `Infinity-2103438-Combined-Original-Signer.apk` SHA256 `a1907acbcb3a36f5b2312f8a11cd4e38d8fcdbed2f435b6ab45d369adc8e9f35`; original signing run `41250066560`.
- Original signer certificate SHA256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`, Android package `com.projectinfinity.kodi`.
- Development ONLY on `work/cobra-fullscreen-display-from-2103438-20261031`, forked directly from the signed 438 commit.
- Frozen `INFINITY.zip` SHA256 `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d` (Infinity 2103437 working implementation).
- Frozen `MINIMAL_ANDROID_CONTRACT.zip` SHA256 `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`.
- Cobra 438 baseline `COBRA.zip` SHA256 `2229274553616f4febb7ef80925eddc23f6f2346bddf4eeabee18e819158399e`.
- Keep signed 437/436 and older protected original APKs and their lock refs unchanged. Preserve exact signed 438 original as recovery.

## Required correction A — the actual fullscreen Display popup
1. Reproduce on actual signed438 fullscreen view (enter via Cards like screenshot). Press the visible **Display** control with real touchscreen coordinates; also test appropriate D-pad/remote accessibility activation. Determine whether pressed/focused feedback occurs and whether original handler executes.
2. Trace native `cobraBuildPlayerChrome`/player-strip construction → visible Display view/tag/id/actual hitbox → actual click callback → original `showCobraAspectPicker` or current438 equivalent → original `cobraOpenSheet`/modal host → attachment/visibility/alpha/z-order/close. Determine whether playback chrome auto-hide, another overlay, incorrect action mapping, hidden `mMultiOverlay`, or a stale activity/channel/modal owner prevents visible menu. These are **hypotheses**, not proven causes.
3. Preserve **the existing original Aspect / Display menu** with its existing options/order/labels/selection, styling and accessibility. A normal press should open it **exactly once and visibly**, without stopping video, entering PiP, invoking More or switching view modes. Back/close and reopen work. No new menu design or extra controls.
4. Preserve other fullscreen strip actions (Channels, Multi-View, PiP, More), top playback actions (Back, Favorites, timeshift, lock) and system/sun controls. Correct only verified Display touch/dispatch/modal-visibility defects. Do not revive earlier reverted 434/435 experimental hacks or change a proven working Pro handler without a mode-scoped need.

## Required correction B — examine EACH existing video size/aspect option; repair only proven failures
1. Enumerate the **actual signed438** menu and every supported global and per-channel display setting, their labels, IDs, ordering, availability and preference owner. Historical code `repairs/cobra-fold-adaptive-aspect-2103194/apply.py` and `repairs/cobra-power-audit-2103199/tests/Cobra2103199DisplayRegressionTest.java` show **13 modes indexed 0..12**, including Fold Adaptive (12), Best Fit, fit/fill/crop/zoom variants and Custom (11), but historical tests are **not proof that current438 presents precisely the same options**. Establish the exact source/runtime list before claiming coverage.
2. For each actual option verify that selecting it: executes once; sets the intended selected/default/channel override (as applicable); transforms the **current video TextureView/surface** correctly using original ratio, source pixel aspect and viewport; visually changes only the selected display geometry; updates any selection indicator; persists/restores according to existing policy; and returns to fullscreen without killing or rebuffering the active player.
3. Verify Best Fit preserves the full correct picture and letterboxing when appropriate. **The screenshot's black bands in portrait are not automatically a defect.** Do not force crop/stretch for aesthetics. Inspect Fit, Fill, aspect-ratio overrides (16:9, 4:3 when present), width/height adjustments, Zoom choices, Fold Adaptive and Custom percentage editor. Preserve existing calculations for working options.
4. Test 16:9, 4:3, portrait video, non-square pixel ratio, missing/late video size, live TV/timeshift, channel change/source change and returning to previously configured channels. Validate global default vs per-channel inheritance and reset; do not let a previous channel's choice leak into the current channel.
5. Test Galaxy Fold **front and unfolded inner displays**, portrait/landscape, fold/unfold while player is active, rotation/window resize/split-window where supported, PiP entry (retain original safe behavior) and PiP return restoring the selected display mode. Preserve correct captions/subtitle placement and decoder/Surface/Texture identity across sizing changes.
6. Keep each existing supported option, label, range, order and preference schema; do NOT remove an intentional video size mode, rewrite all geometry math or add a new mode. Any change must match **a demonstrated signed438 defect** and be scoped to its exact player sizing pathway.

## Absolute preservation outside scope
- **INFINITY 2103437/combined438: 100% untouched** — all loading work, skin, providers/add-ons, Search, playback, background/PiP, watched/Resume, Command/Health Center, settings, service/data, native components and Essential-First shutdown. Exact Infinity owner ZIP/DEX/resources must match signed438.
- **ALL unrelated Cobra view-mode UI/logic frozen** — Cards main wall, compact two-column FRONT and four-column INNER density, drawer resizing fix, Light/Dark/OLED Cards theme correction, Mobile, Compact, TV Grid, Pro, Pro Sports, Sports, Multi-View, all non-Display features. If a shared player Display method is legitimately broken across modes, guard its repair narrowly, document affected consumers and negative-test all unchanged view modes.
- **ALL unrelated Cobra behavior frozen** — channel inventory/EPG/logos/selection, search/filter/Favorites, playback transport/seek/timeshift, decoder audio/video, subtitles track selection, PiP, More/sun/brightness, player chrome order, appearance settings, ambient/night, startup/recovery and performance.
- **Chooser, launcher, global themes, native shared engine, JNI/47 libraries, Android manifest other than required typed version, original cert/package and user data** frozen. No uninstall, clear data, reset, source/playlist/password changes, database/schema migration, background job/timer or shutdown code/testing.

## Verification and failure gate
- Preimage: compare **exact signed 438** vs candidate (not merely latest engineering branch), including original APK, Cobra ZIP, all DEX class/method signatures, native libraries, resources and chooser. Predeclare a **short method/file allowlist** of proven causes.
- For **Display popup** test actual end-to-end touchscreen path, sheet visible after settling, Back/close/reopen, repeated taps, active video and host/player overlay. Verify no More/PiP/Channels misrouting.
- For **every actual signed438 Display mode**, build a tabular PASS/FAIL/not applicable matrix: label/id, chosen option, source ratio, viewport, expected and actual texture transform, callback/persistence/prefs, channel override, caption alignment, PiP/return. Reuse existing tests but run specific regressions for any new fixes. Never claim thirteen working on physical device from historical unit tests.
- Front/inner screen, portrait/landscape, theme switching, viewer return, source retune, fold transition, rotating with menu visible, and other Cobra modes as **negative controls only**. Confirm unchanged identity, gestures, focus, scroll, playback and preferences outside authorized sizing settings.
- Actual candidate APK member-by-member preservation: **Infinity ZIP exact original hash, Cobra only allowlisted Display methods, no other player/view-mode method edits**, no native/shared/chooser executable changes, only required truthful version metadata and original-key signature differences. Fail closed on unknown changed members. Preserve 438 lock and recovery artifacts.
- Complete mandatory focused source/host/Android checks available; declare exact physical Fold limitations honestly. Do not weaken existing checks, claim unviewed media acceptance, or run unrelated shutdown stress.
- Deliver **one original-key signed install-over testing APK** with the next valid versionCode, matching owner ZIPs, original signer verification, SHA256, source commit, Actions run and actual download links **only after safe gates pass**. No auto-acceptance/promotion/lock; the user must verify on their Fold.
- **If any necessary fix would alter unrelated Cobra behaviors, Infinity, native shared engine, data or shutdown, STOP and request separate authorization.**

## Current status
This instruction captures an approved *repair scope*. The user screenshot and historical source establish the location of the button and existence of aspect policy, **not the current438 defect's code-level root cause**. **No production change or APK is created by this document**.
