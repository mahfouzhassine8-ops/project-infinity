# INFINITY — External Local Video Intent, Stuck Loading & Stop/Return Freeze

**Status: reported and diagnostics inspected; no source repair or APK is claimed by this brief.**

**Authorized scope:** Investigate and correct **Infinity-owned** local-file, external-player handoff and associated playback-UI lifecycle defects only. Preserve existing behavior and all unrelated code. This is a targeted follow-up, **not** a reopened broad quality refresh, Cobra update, native engine overhaul or shutdown rewrite.

## Protected baseline (November 1, 2026)

- App `com.projectinfinity.kodi`, last user-approved **combined 2103445** (rotation/audio Cobra refinements locked).
- Exact successful original-key signed 2103445 source: `6cf75639a46ec6b0c858ae32abc102450fdc0974`.
- Lock: `lock/infinity-cobra-2103445-user-approved-20261101`; preserve exact SHA and signed APK/checksum.
- Authorized read-only/targeted work branch: `work/infinity-2103445-external-video-lifecycle-20261101`.
- **Cobra 2103445 frozen byte-for-byte.** Infinity baseline component is 2103437; preserve every unrelated Infinity function, add-on, provider, skin, profile, saved state, Kodi native libraries, shared Android, original signer, chooser, services, cleanup and **protected shutdown**. No uninstall, clearing data, replacing certificates or speculative media-engine rewrite.
- A real final APK, if a permitted correction is implemented and user authorizes delivery, must be original-key-signed and install over 2103445; no auto-acceptance/lock. No bypass of integrity/security gates.
- If root cause requires touching a protected Kodi-native/shared/surface lifecycle or shutdown owner, **STOP THAT FIX and report precise evidence requesting distinct user authorization**.

## User reproduction — distinct symptoms

User opens a local movie on a Galaxy Fold 8 Ultra via **MiXplorer > Open with > Infinity (Splash)**; the file launches into Infinity Kodi and plays correctly.

1. **Stale loading overlay after actual video playback:** Sometimes a visible `Loading` message/dialog persists *on top of the movie* and blocks or obscures playback UI. An Android system Back gesture dismisses that message, **without stopping the movie**. No screenshot of this overlay was available. It has not yet been identified as native Kodi Busy/Progress, skin cue, Android notification or unrelated modal. Do **not** infer owner from wording alone.
2. **Freeze during Stop/return/reopen:** On one occasion Infinity froze around the user's press of Kodi Stop or exit from video to select a different local file with MiXplorer. The user is **not sure** whether Stop, returning to the file manager, or the subsequent second external-open request triggered it. Do not conflate these paths or claim causation without timing evidence.
3. Related but separate: prior abnormal-shutdown warning and diagnostic native crash/ANR may indicate additional lifecycle contention. Investigate correlation read-only, but DO NOT assume these are a single bug.

## Existing uploaded local diagnostic inspected, no raw private files committed

User-provided **Infinity-Diagnostics-20261101-200333.zip** (20:03 local), installed package reports **2103445**, Android 17 / Samsung SM-F976U1. The ZIP has an Android ANR text trace, a tombstone protobuf, startup/relaunch history and shutdown records, **but does not include the complete playback Kodi log or explicit Android ACTION_VIEW URI/overlay show-hide timestamps.** It cannot prove which specific Stop/Back event caused the issue.

Privacy-safe grounded observations:

- **19:33:18 local:** internal native UI responsiveness observer recorded **5,257 ms** heartbeat gap. At capture time player flags `video=1`, `kodi_window=12005` (fullscreen video), `active_dialog=12901` (**Video OSD**). This observation is not itself an Android official ANR and **does not establish the identity of the user's described Loading overlay**.
- **19:32:35–19:41:26 local:** multiple `Splash` live-Main handoffs and `Main.newIntent` entries occur; confirms the app's **reused running Main activity** path is exercised. The diagnostic does not record URI contents or prove each intent represents a file selection. A second activity/process startup also occurred in this period.
- **19:34 local:** recorded Android SCREEN_OFF broadcast ANR, 10s limit, main thread waiting via `XBMCMainView.surfaceDestroyed -> CXBMCApp::XBMC_DestroyDisplay -> CApplicationMessenger::SendMsg -> CEvent::Wait`. It occurred in Kodi `:kodi` process. **Separate candidate native/display issue**; do not patch shared/native without new permission.
- **Earlier native crash:** Android exit `native crash`, signal 11 (SIGSEGV) in `:kodi`. Specific underlying caller is unresolved here. Do not claim root cause or link to external-file Stop absent proof.
- Later explicit close has `checkpoint.safe_to_terminate` and authorized termination; not a blanket failed shutdown.

The native video window IDs are documented by Kodi: 12005 = Fullscreen video; 12901 = Video OSD; 10138 = Busy dialog; 10101 = Progress dialog. The recorded freeze's 12901 is **not the Busy dialog ID**, so do not call it a proven stuck loading modal.

Existing Infinity 2103437 loading implementation deliberately preserves native progress/cancel/error dialog lifetimes and does not change protected player/OSD XML. It must not be globally disabled merely because a player is active.

## Read-only investigation / reproduction matrix

Inspect the actual signed 2103445 Android Manifest, Splash chooser intent routing and Kodi Main `onCreate/onNewIntent`, playback bridge, native window/dialog state and the actual installed Infinity 2103437 observer/skin. Do not rely on historical sources to identify exact installed bytes.

Use a **nonpersonal synthetic local MP4** from MiXplorer or Android `ACTION_VIEW` with appropriate URI permission and MIME types and run each path separately:

A. Cold start -> Open with Infinity -> first video frame -> wait; determine if `Loading` is a native Busy/Progress, action-loading UI, Android notification or another dialog; capture current Kodi window id/active dialog and owner token, screenshot and timestamps. Test successful initial playback and failed/unsupported URI distinctly.

B. While first movie visibly plays, tap **Stop** -> player stops -> Kodi previous surface/route returned; confirm no freeze, stale media-session notification, stale busy token or blocked touch. Reopen *same* local video.

C. Instead of Stop, use Android **Back** from active video to exit playback/return to MiXplorer -> select video B -> Open with Infinity; confirm second intent plays **B exactly once**, correct URI grant lifetime and no leaked old player/surface/overlay.

D. MiXplorer opens new video B **while A remains playing** / app is backgrounded: test `Splash` handoff to live Main, `onNewIntent`, rapid repeated intents, stale completion race, cancel/replace, correct selected target, no duplicate playback or background loading remaining.

E. During opening/playing, screen off/on, Home/back, fold/unfold, system Back gesture and PiP return; keep **native display/surface** investigation separate when protected ownership applies. Capture ANR trace and reproducer exact location before any native edit.

F. Preserve and independently verify internal provider movie/TV playback, user-approved loading cues, buffering and genuine long-running progress: fix must never suppress legitimate progress/errors, globally close another operation's dialog, force stop unrelated tasks, or fake playback readiness.

## Engineering acceptance criteria

1. **Loading owner identified from real evidence**, preferably `dialogId`, request/session generation, action origin, show/hide notifications and actual first frame/readiness. A stale external-file startup overlay must retire on *its own* terminal event (playback confirmed/first frame, failure, cancellation, replacement), regardless of current screen or subsequent Back. **Do not dismiss a global progress dialog solely because ANY player is playing**; preexisting video A does not imply new request B finished.
2. **External intent one-shot and reentry:** Preserve Android read grants for `content://` where permitted, safely transfer to Kodi's existing file-opening mechanism without duplicate launches; route new file selection to the live player appropriately; serialize state transitions under per-request generation/cancelation so old work cannot dismiss new UI or play the wrong file. Do not reset Kodi or data just to switch files.
3. **Stop/Back return safety:** Stop is idempotent, old playback/player callbacks retire exactly once, UI remains responsive and underlying previous window/file-manager return is not blocked by stale modal, busy loop or synchronous UI-thread wait. Do not invoke protected shutdown machinery to solve local-player navigation.
4. Test all A–F on selected source across relevant Android screen modes. Include deterministic host tests and **real Android 17 runtime evidence** where possible; separately report Fold-only checks. Trigger no unrelated shutdown tests. Record before/after freeze and overlay timelines and untouched component bytes.
5. Release/signing only from explicit narrowly scoped source/owner allowlists. Preserve **Cobra, all shared/native libraries, unrelated Infinity functions and shutdown** byte-identical to 2103445. If unavoidable protected owner involvement, document blocker and seek explicit authorization before any edit.
6. Do not claim SIGSEGV, SCREEN_OFF ANR or Android Fold reliability repaired without direct proof. A loading-overlay fix alone is not a native crash fix.

## Deliverable

First produce a report with root cause, precisely touched owner, proof of stale dialog lifetime and unique request identity. If fully within allowed Infinity ownership, make the minimal scoped correction and its tests, then prepare **one verified original-key install-over signed APK** with matching ZIPs/checksums and explicit physical-fold acceptance. Do not alter accepted 2103445 or automatically lock a successor.

**The report is the handoff and analysis; it does not constitute an implemented repair or a delivered APK.**
