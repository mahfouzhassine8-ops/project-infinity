# Infinity 303 / skin 194 repair checkpoint — NOT an installable release

Work authorized October 4, 2026. This is a **partial source repair**, not completion
of the end-to-end brief and not a new locked APK/theme. Neither version number has
been bumped and no APK or installable skin ZIP has been produced by this repair
pass. The user authorized pushing the repair branch and running validation builds.

## Locked preimage and rollback

- Application: `com.projectinfinity.kodi`, version code **2103303**.
- APK SHA-256: `ee9d82463f35594ed595e50dc8913499e79110b63fbf27ad456a0b87b396fa83`.
- Skin: **1.0.5.194**, internal ID **skin.infinity.diggz**, visible name Infinity.
- Original skin ZIP SHA-256: `7e20256adb34354cea6eb9cc1ec696885c2f9c6625ba4667a1210bbe14e4782a`.
- Android source export: commit `0a8d8a13efff44cc8be0c99416a1d239b3066e8c`,
  successful packaging workflow run `37170612805`, source artifact `11291800261`.
- Local skin-preimage commit: `cc8bcf02c047581fdca7f969304e9e50e9f99637`.
- Original APK, original ZIP and rollback receipt were archived **before edits**
  and saved successfully. Archive SHA-256:
  `a5803fb27c3a985ca2e2008b40541dba990037d2d8d66436bb6071150a8a2f59`.
- This rollback does **not** contain a backup of the phone's current user data.

The seven edited XML files are under `addons/skin.infinity.diggz/unified`. That
directory is the authoritative working skin. No replacement skin or add-on-ID
rename is involved. Existing image/texture resources remain byte-for-byte intact.

## Implemented in source

| Area | Change | Validation boundary |
| --- | --- | --- |
| Home capsule | Vertical official emblem/hamburger; reduced header overlap; transparent resting button; return underlying touch focus to home navigation before opening drawer | XML bounds checks, no phone screenshot acceptance |
| Drawer | Removed More options and its visibility gates; retained entries in one scrolling viewport; UI Theme immediately above Power, using existing InterfaceSettings route; matching top-left anchor | Routes/structure and bounds checked; animation/touch on device pending |
| Power | Bundle routes normal/force close to existing Android PowerControlActivity; retain non-Android commands conditionally; normal close is default, not force close | Existing activity/action names verified in exported Android source; shutdown/relaunch untested |
| Native row input | Permit taps on visible portions of partially clipped scrolling rows; reject clipped-out portions; keep keyboard navigation policy unchanged | Old production method fails regression; proposed production method passes both-axis tests |
| Player | Initial rail starts at Drawer; original 12 actions/order retained in one horizontal viewport; volume capsule lower-left; vertical fill and slider; state-specific existing Repeat icons plus focused state label | Structure/geometry/actions checked, rendering/drag/timeout pending |
| Player menus | Remove duplicate Audio settings entry; preserve its route in Audio & Subtitles; move Rotation policy into Display Mode; theme-aware menu text | XML checked; actual playback menus pending |
| Light appearance | Player variables select existing light assets instead of dark assets | Real asset existence and palette branches checked; OLED/dark branches retained |
| Add file source | One centered bounded panel, logo/title/X, scrolling form, legible Browse/Add/Remove buttons, contained name field and bottom actions | Original native control IDs preserved; tested mathematical bounds at 11 canvas sizes |
| Android editor | Cyan/OLED/light field and button styling, sans-serif text, scrollable panel and safe width bound; original editor/token/IME semantics preserved | Helpers compile against Android API 35; real Samsung/Gboard/Back behavior pending |
| Experience options | First three choices are one mutually exclusive launch-behaviour section with one action; Health Center/Recovery kept separate; preserve existing callback indices and dismissal guard | Java compilation only; runtime selection/reflow tests still required |

The historical source ZIP can overwrite on-resume Power XML patches while the
activity remains resumed. The new skin routes avoid depending on a later resume
to reapply them. This is **not proof** that every reported exit fault shares that
cause. Likewise the reproducible partial-row input defect is **not proof** that
every unclickable Settings/Power button is explained by it.

## Checks actually completed

1. All 250 files in the exported Android source proof matched before edits.
2. After edits, 248 remain unchanged; only `InfinityAndroidKeyboard.java.in` and
   `InfinityGlassOptions.java.in` differ. Weather bridge/startup/exit/native bridge
   Java sources were not changed.
3. Eight skin tests pass. They parse the complete unified XML set and check selected
   route, geometry, theme, action and identity contracts. Geometry inputs cover 11
   tall, square, landscape and small-window canvas sizes. These are **not** rendered
   phone, fold, font-scale, or live-resize tests.
4. Both modified Android helpers compile against the real Android 35 API and core
   stubs using Eclipse ECJ 3.37.0. Only the Main Activity dependency is stubbed;
   unchanged CosmicArt/CobraEmblem implementations are compiled. The inherited
   `SOFT_INPUT_ADJUST_RESIZE` deprecation warning remains. This is not a full APK build.
5. C++ regression harness compiles the actual old/proposed `SendMouseEvent` method,
   not a rewritten approximation. It covers both orientations, partially visible
   first/last rows, off-viewport hits and smaller viewport resizing.
6. `git diff --check` passes. No artwork, provider configuration, weather snapshot,
   Resume Hub state, or VideoFullScreen/video-positioning file was edited.

## Still unresolved — do not call these fixed

- Source chooser/resolver: the user confirmed **Umbrella** as the screenshot owner
  and reports that other add-ons may share the problem. Investigate the shared
  native window geometry and Back paths as well as Umbrella's windows. The installed
  Umbrella version/window XML has not yet been matched. No global guessed replacement
  or provider behavior change has been made. Native Back cancellation, possible
  freeze/crash, orientation changes and foreground ownership remain open.
- Idle movie/screensaver takeover: owner/timer/decoder is not established. No
  indiscriminate stop of user playback or addon deletion has been performed.
- Full cover-landscape home layout, settings category/grid and all settings controls.
- Global confirmation/context-menu/ambient dialogs, complete touch/long-press audit,
  source selection UI, and remaining branding audit.
- Exact visual match to locked player/drawer references across themes and sizes.
  The selected player icons/volume fill need actual rendering verification; this
  checkpoint must not be presented as a restored-and-accepted player.
- Native SIGSEGV ownership/symbolication, excessive CPU cause, completed native exit
  milestone, bounded recovery, immediate/delayed relaunch and black-screen regression.
- Watchdog/health classification and real geometry/profile telemetry on the phone.
- Full Android IME/Back/cursor/paste/password behavior and touch target sizes in dp.

## Build and acceptance gates

The native clone used for the isolated input test is **not a complete reconstructed
303 build tree**. Reconstruct the exact native lineage in the existing CI workflow,
verify its preimage, then apply `native_patch.transform` to the one declared file.
Its SHA-256 guard is recorded in `native_patch.py`; none of the prior 303 transforms
modify that file. Do not build or ship the partially reconstructed diagnostic clone.

`android_patch.py` verifies the complete 303 source proof and emits only the two
Java changes. The `.java.in` files in this folder are the candidate templates.
`native_patch.py` emits the corresponding single-file native delta. Both emit
`apply_patch` format and do not silently write their input trees.

GitHub push/build permission was granted. The validation branch carries the exact
seven-file skin delta as `skin-194-repair.patch`, with a preimage/postimage hash
manifest. It is an overlay against the retained authoritative 194 ZIP, not a full
or independently installable replacement skin. Local full-skin tests do not imply
CI has rendered or packaged that skin. The CI jobs validate Android and native
source separately and deliberately do not publish an APK.

Produce a **matched** APK/skin/controller bundle only after full builds,
signing and inherited weather/exit/IME tests pass. Do not publish a skin-only fix as
if it contained the native tap repair. No signing credentials were extracted here.

Physical acceptance must cover front/cover and unfolded/main screens; portrait and
landscape; light, dark and OLED; split-screen, popup and live resize; cold/warm launch;
immediate/delayed relaunch; background/foreground; active/inactive playback; touch;
and Android IME open/closed. All remain pending for this checkpoint.

**Hard caution:** the approved references are the target. Do not redesign or replace
the drawer/player, disturb the weather snapshot bridge, or modify the explicitly
deferred movie-video vertical framing/positioning issue.
