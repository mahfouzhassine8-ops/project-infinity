# INFINITY — CONSOLIDATED FOUR-CORRECTION HANDOFF

**Status:** Brief assembled. **Three UI corrections are approved; crash case is confirmed as an abnormal engine exit, root cause and trigger still unverified.** No code changes or builds authorized by this document alone.

**Locked base:** Android APK `2103384`, `com.projectinfinity.kodi`, permanent release signature unchanged; SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`. Do not modify or overwrite `locked-infinity-apk-2103384-user-passed-20261017`. Existing skin 1.0.5.225 is experimentally installed; separately locked skin 1.0.5.223 must remain intact. Preserve all Diggz/add-ons, Cobra, player, PiP, watched and database state, and proven Essential-First Close. No uninstall or data clear.

## 1 — Rotate OSD control

**Physical Fold observation:** The video OSD Rotate slot is wired to **Repeat**, confirmed by the `Repeat: Off` overlay after pressing it. This is a wrong function, not a mere icon problem.

**Exact target:** Restore original Rotate button and actual Android orientation policy in the same slot: **Follow Device (white)** versus **Infinity-controlled (cyan)**, correct icon and state. Remove `PlayerControl(Repeat)` from this slot, without altering neighboring controls or player/PiP/background playback.

**Additional explicit user correction — REMOVE `Display Mode` from Playback menu:** New physical Fold screenshot shows the **Playback** popup during active video; its options include **Video Settings**, **Player Settings**, then **Display Mode** immediately above **Playback Info**. User confirms they found rotation through **Display Mode** and asks that **Display Mode be removed from the Playback menu**. This is part of **Repair #1**, not a separate fifth repair.

**Required final interface (bite-for-bite):**
1. Remove the standalone **Display Mode** row from the **Playback** popup altogether; it must not remain as a redundant rotation shortcut or a renamed duplicate.
2. Restore the actual **Rotate** action to the previously approved **player OSD Rotate slot** (currently miswired to Repeat), using **Follow Device (white)** and **Infinity-controlled (cyan)** with correct functionality, not merely an icon swap. Do not put Repeat in the slot again; retain Repeat elsewhere only if independently intended and already approved.
3. Verify the **Display Mode** handler before removal: if it exposes additional independent video/aspect/zoom controls, preserve those appropriate controls in the existing **Video Settings** experience rather than silently deleting unrelated features. Do not replace the Playback menu with an unrelated redesign or change the other rows/order.
4. Test both Fold orientations, fold/unfold, fullscreen, safe Stop → movie choices and optional return to Home, plus pop-up dismissal and player return. Verify orientation behavior and absence of the redundant row on device, with no effects on video color, aspect settings, PiP, background playback, player teardown, resume state or Essential-First Close.

**Evidence privacy:** Screenshot shows the Playback menu at approximately **12:54 AM**, close in time to the **00:55:31** abnormal exit, but it does **not** prove the menu or rotation command caused the crash. Do not publish the user's screenshot, content title, or watch history.

**Reuse:** The reviewed experimental `repairs/full-system-20261017/player_rotate_226.py` candidate already targets skin 1.0.5.226; review installed source and reuse/correct this rather than independently recreating it. Source tests alone are not physical Fold acceptance.

## 2 — Home Continue Watching/Continue Playing press-and-hold

**Physical Fold observation:** Continue Watching cards populate and normal clicks can correctly show `Resume from 00:02:44 / Play from beginning`, then a provider chooser. This is **not** the missing item-level context popup.

**Recovered existing behavior:** The original Command Center Resume Hub `plugin.py` still defines the actual item options and attaches them with `li.addContextMenuItems(context)`:
- Mark Watched / Mark Unwatched
- Reset Progress
- Add to / Remove from Watchlist
- Add to / Remove from Collection
- Rate / Change Rating
- Add to Custom List
- Remove from Continue Playing when item is in that bucket

This was recovered in `repairs/resume-hub-2103292/src/controller/plugin.py` and supporting watched-bridge code. **Do not replace the original items with arbitrary menus or the generic All Add-ons popup.**

**Exact target:** Restore press-and-hold on the selected Home media card to open its proper existing item-specific menu without launching playback or losing focus/scroll position. Preserve a normal tap's Resume/Play choice, provider resolution, play counts, watched state, progress and local data. Trace current Home/rail touch dispatch and context-menu listener; do not assume native engine changes are required.

## 3 — All Add-ons → Video Sources selection and menu (bite-for-bite approved)

**Physical Fold observation:** Reaching right-side tiles presently requires launching first and pressing Back. `Disable` is confusingly presented as though it might mean Hide.

**Exact approved gesture contract:** First tap highlights without launching; second tap on same selected tile launches; select then press-and-hold opens selected add-on's compact context popup. Both columns identical, focus and scroll preserved after dismiss. Merely highlighting a popup action must not execute it.

**Exact top-level order:**
1. Open
2. Add-on Information
3. Add-on Settings (only where supported)
4. Add to Favourites
5. Add to Infinity Rails (only when supported)
6. Hide from This View — **only hides grid tile; NEVER disables or deletes the add-on**
7. More / Manage Add-on — actual Disable only here, with explicit warning and confirmation

AutoWidget/Super Favourites only when supported in advanced options; Resume Hub actions only for genuinely relevant items. No irrelevant top-level buttons, black/narrow popup, automatic launch, focus trap, or visual redesign.

**Controlling approved source:** `repairs/full-system-20261017/APPROVED-ADDON-VIDEO-SOURCES-MENU-EXACT-CONTRACT.md`.

## 4 — NEW physical Fold abnormal Kodi engine exit

**New read-only evidence:** Private `Infinity-Diagnostics-20261018-005618.zip` supplied after the UI assessment. **Do not publish the private ZIP, personal logs, individual playback history, or screenshots into this public GitHub repository.**

**What this evidence actually establishes:**
- Device report at **2026-10-18 00:56 local (EDT)** identifies installed APK version **`1.0.9-Optional-VFS-SaveFix-TEST1` / versionCode `2103384`** and skin `skin.infinity.diggz` **1.0.5.225**. The capture identifies the installed build; Android's historical exit record does **not** itself cryptographically include the exiting APK's build hash.
- Android's **most recent historical process exit** was **2026-10-18 00:55:31 EDT**, process `com.projectinfinity.kodi:kodi`, **Reason: self exit; status: 139; importance: 100**, reported RSS about 1,045,220 KB. Status **139 often corresponds to 128 + signal 11**, making a native fault plausible, but a self-exit code **does NOT prove SIGSEGV or name a faulting library/thread**. Do not label it a confirmed renderer, addon, memory or shutdown defect without native stack evidence.
- Last Android record for a normal coordinated shutdown is from a **different earlier session** around **2026-10-17 23:38**, and reported `COMPLETE`, all 16 essential save owners committed/durable, `checkpoint_saved=true`, authorization consumed and engine process death, about **6.63 seconds**. This historic receipt is NOT a crash receipt and proves neither that the 00:55 exit was a clean Close nor that previously locked successful Close stopped working.
- The diagnostic bundle did **not** contain `crash/native-crash-last.txt` (`not_present`), native tombstones, or a crash-time Java exception/stack trace; `exit-manifest.json` has `records: []`. Shutdown native/critical mirror logs are attributable to **earlier PIDs and earlier Close sessions**, not the 00:55 failing process. Do NOT misuse them as a crash-time stack.
- The persistent Kodi process-state JSON still says `RUNNING` with an earlier PID; it is **stale or unverified after this abnormal exit**, not proof that Kodi is currently alive.
- The report shows the Android chooser reappearing shortly after the exit, without a supported reconstruction of the triggering user action.

**Root cause: UNKNOWN**. The fourth item is an evidence-backed crash regression/forensics request, not an authorized speculative fix.

**New physical-device trigger testimony (user follow-up, October 18):** The user was **playing a video**, then **pressed Stop**. Infinity **returned to the movie choices/selection screen**. The user cannot recall whether they subsequently navigated back to **Home** before the crash, or whether the process crashed while on/just after the movie choices screen. This is the strongest available interaction clue, but **does not establish that Stop itself directly caused the native exit**, nor does it exclude a later navigation/lifecycle callback. Do not invent missing gestures, timing, or a native backtrace.

**Reproduction split (preserve both plausible paths):**
- **Path A — Stop → movie choices → exit:** play a representative video with normal existing providers; invoke the actual player **Stop** control; verify return to movie choices, then watch for crash/abnormal exit without further navigation.
- **Path B — Stop → movie choices → Back/Home → exit:** repeat the same session and Stop transition, then navigate back to **Home** as the user may have done; correlate the exact event with the process death.
- Include the preceding player teardown, resume-progress write, provider/list refresh, GUI window activation, and Android native lifecycle transitions in trace correlation. **Do not presuppose which subsystem failed.** Capture crashes during both paths and maintain normal playback, safe stop, Resume Hub data, and Essential-First Close.

**Next technical investigation, once trigger is known:**
1. Reproduce the **two observed/plausible post-playback sequences (Path A and Path B above)** on exact signed **2103384** with existing user data preserved. Collect crash-time **native tombstone / Android bugreport or `logcat -b crash`**, ideally preserving PID, signal, backtrace and relevant build IDs. An explicit `adb bugreport` can help if developer access is available; do not require uninstall or data wiping.
2. Compare the crash timestamp with Kodi native player/GUI, Java Android lifecycle, add-on callbacks, rendering, Fold orientation, background return and native engine build IDs. An RSS reading alone is NOT proof of OOM.
3. Trace the **faulting native stack** and reproduce before choosing a correction; isolate skin/helper vs Java/native boundary. Avoid removing add-ons or disabling protected services as a guess.
4. Fix the smallest proven component in a new experimental candidate. If skin/helper-only, no native recompilation; if native defect confirmed, rebuild **from 2103384** with exactly reviewed changes and permanently sign an update; never replace locked baseline.
5. Confirm absence of this crash under its exact reproducible trigger and no regression in OSD Rotate, removal of Playback → Display Mode, preservation of independent video settings, Continue Playing item menu, Video Sources selection, player/PiP/background/fold, saved data, and normal Close.
6. If native APK changes: the exact new signed APK must pass Android fresh + loaded/upgrade native Close/reopen and physical Fold normal Close/reopen, with zero essential write blockers; user must explicitly approve promotion. A passing test does not establish every crash vector eliminated.

## Promotion / preservation requirements

- Three UI changes **already have clear approved behavior**, but **are not yet implemented** or physically retested on 2103384. The fourth crash is **confirmed as an abnormal exit but root cause and trigger are pending**.
- Prefer skin/helper repairs from verified current installed skin; do not preemptively rewrite `libkodi.so` just to restore menus or Rotate.
- Lock branch is immutable; staging happens only on `work/infinity-post-2103384-feature-restoration`.
- Preserve other implemented Infinity features and the complete five-workstream project; this brief is **only the four currently identified targeted corrections**, not a new feature list.
- Final implementation approval, signed artifact acceptance, and any future user lock are separate explicit gates.

**Current action:** evidence review and brief assembly only. No new candidate APK/skin ZIP, CI feature test, or device mutation has been requested or performed by this brief.
