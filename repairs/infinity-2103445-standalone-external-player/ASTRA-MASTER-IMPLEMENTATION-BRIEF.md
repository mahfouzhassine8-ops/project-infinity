# ASTRA PRO — INFINITY UNIVERSAL EXTERNAL VIDEO PLAYER
## Reuse existing Splash, independent playback runtime, one combined app

**AUTHORIZATION: INVESTIGATE NECESSARY OWNERS → IMPLEMENT TARGETED FEATURE → RUN FOCUSED TESTS → BUILD ORIGINAL-KEY SIGNED INSTALL-OVER TEST APK. NOT AUDIT-ONLY.**

### Exact protected starting point

- Repository: `mahfouzhassine8-ops/project-infinity`
- Work ONLY on `work/infinity-2103445-standalone-external-player-20261101`
- Branch was created at exact signed/user-approved source `6cf75639a46ec6b0c858ae32abc102450fdc0974`.
- **Authoritative accepted combined build: 2103445**; lock `lock/infinity-cobra-2103445-user-approved-20261101`.
- Signed 2103445 APK: `Infinity-2103445-Combined-Original-Signer.apk`; SHA-256 `b7e78393ade7e52d8653823a0ad72ae99614a5a8e0b6cdedf5d5d15a9e643400`.
- Original signing certificate SHA-256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Component preservation controls: independently derive **all exact 2103445 component ZIP SHA-256 hashes** from its signed matching artifacts before using them as comparison gates. The 2103446 release receipt records `COBRA.zip` SHA-256 `f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8` and minimal Android contract ZIP SHA-256 `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8` as unchanged versus 2103445; verify this relationship from actual baseline packages rather than trusting text. Do not use any unverified INFINITY or CHOOSER ZIP digests.
- Do **NOT** base the new feature on 2103446, which the user rejected after native crashes and failure to play local movies. 2103446's external intent-ticket patch and the emulator test scripts are background evidence only, **not source to merge**. Preserve 2103445 as recovery.
- Target: Samsung Galaxy Fold 8 Ultra, Android 17; front and inner displays. No user uninstall, clearing data, account reset or data migrations.

### User decision: EXACT architecture and product behavior

User wants **ONE Infinity application** and **ONE existing visible Infinity/Splash chooser entry**. They specifically reject a second visible "Infinity player" app, duplicate competing "Open with" options, or an independent player that conflicts with normal Infinity Kodi.

**New explicit naming requirement: Android's external-video `Open with` selection MUST be visibly labeled `Preview`, NOT `Splash`.** Do not change the original `.Splash` class name, normal app launcher name `Infinity`, or the existing Infinity/Cobra chooser appearance. Use a scoped video `ACTION_VIEW` intent-filter `android:label` (prefer a string resource if needed) rather than changing the Splash Activity/application label globally; Android supports filter-level labels. If existing video/audio/image share a single filter, split only the minimal video filter necessary to assign `Preview` without renaming unrelated audio/image routes or creating duplicate matching video choices. Keep the current approved Infinity icon artwork for the application launcher; do not create a second user-facing icon or change the launcher drawable. Verify the **actual installed Android 17 resolver** shows `Preview` (some OEM surfaces can display the app name as a prefix) and still shows exactly one Infinity video choice. The term `Splash` may remain internally in logs/source; only the video-handling option must read `Preview`. Do not assume an `android:label` alone is sufficient without testing on Android.

**Keep the existing Splash entry point. Give it a narrowly scoped EXTERNAL VIDEO routing path that sends supported video requests to a lightweight internal player powered by an Android-native playback engine. Do NOT initialize the Kodi engine/process for these requests.**

Normal tap on Infinity app icon → the **unchanged existing Infinity / Cobra Choose Your Experience**, startup and Kodi/Cobra routes. Kodi's original internal VideoPlayer remains unchanged for the full Infinity experience.

Video from a compatible external application → **existing Splash** detects a supported VIDEO request → launches **ONE non-exported internal playback Activity** in a separate, independently managed playback path (ideally its own `:externalplayer` process only if measured startup/ownership proves it safe) → renders video straight away without Infinity Home or Kodi UI → Stop/Back/Exit releases this player's playback resources and returns via Android's normal activity/task stack to the originating app when available. It must NOT open Infinity/Cobra automatically after Exit, restart the Kodi process, or stop any existing Kodi/Cobra session. If the source app/task no longer exists, allow Android's ordinary Home/back behavior.

The word *Splash* is the gateway/activity, **not an independent decoder**. The new internal player uses Media3/ExoPlayer or another technically justified *non-Kodi* playback engine. Do NOT claim to extract the standalone Kodi VideoPlayer out of native Kodi: it has deep native dependencies. If reusing already packaged Android media libraries, analyze their owner/class/initialization dependencies and assure there is **no Cobra runtime startup, mutation or duplicate classes**. Prefer separately owned player classes and public engine interfaces; do not borrow Cobra's playback state, audio service, PiP owner or controller. No second application ID, app icon, shortcut, visible chooser entry or competing external Video VIEW handler.

### Existing implementation evidence — verify against **actual signed 2103445** before edits

Repository templates show `Splash` is a chooser-shell-owned exported Activity with `ACTION_VIEW` filters for video/audio/image and file/content/network schemes; internal `InfinityKodiEntryActivity` runs in `:kodi`. Current historical Splash code routes non-MAIN intents into `startXBMC` / Kodi preparation and `Main`. Read the **actual locked compiled manifest, Splash, Main, component ZIPs and owner policy** before relying on historical template bytes. Splash currently begins startup/handoff watchers in `onCreate`; route eligible video requests **early enough to avoid initializing Kodi or chooser preparation**. Existing Android package contains Media3 classes within the Cobra-owned class family; do not assume that permits depending on Cobra's player UI/service without boundary proof.

### Allowed modifications — strictly limited

The user **expressly authorizes minimal, necessary edits to the existing Splash external-video routing**, a new private internal player Activity and its isolated playback/controller classes, *minimal manifest registration/intent-filter or styling/resource changes strictly for this feature*, and required controlled build/version/ownership registration. The prior general freeze on Splash is lifted **ONLY** for this bounded external-video routing change. No permission to redesign the normal Splash/chooser, alter its normal launch paths, replace Kodi VideoPlayer, modify its native libs or perform general refactors.

Preserve byte-for-byte wherever feasible:
- all accepted COBRA 2103445 behaviors including Cards LIVE, Pro and Pro Sports, Multi-View, universal rotation, fullscreen Mute/Unmute, PiP/Display/More;
- Infinity Kodi, Main normal media-center playback, native core `libkodi.so`, other 47 original native libraries, Python/skin/add-ons/providers, favorites/tracking/resume, data, settings, playback and shutdown;
- chooser layout, icons/launcher, existing experience choices/preferences and normal app startup; shared Android/Media3 player policy outside newly owned external player; original signer/security/release gates; protected shutdown durability.
- Do not touch old accepted locks/artifacts. If truly unavoidable dependency requires changing these protected owners, STOP that sub-change and describe precise evidence for separate user authorization. Do not silently broaden scope.

### Universal external video ingress, without overpromising

Video from **MiXplorer, Samsung My Files, Android Files, Google Drive and other cloud document providers, Downloads, Gallery, supported browsers, messaging apps and other compatible Android apps**—MiXplorer is only an example.

- Support the appropriate existing `ACTION_VIEW` video intents with `content://`, `file://`, and supported directly playable `http(s)://` streams; preserve URI, MIME, caller flags, `ClipData`, permission grants and relevant extras. Inspect the actual manifest before altering its filters.
- Handle Android's video `ACTION_SEND` / shared URI only when securely and explicitly authorized by the actual share contract; don't capture unrelated audio/image/share intents or silently broaden app defaults.
- Never assume every cloud link is raw playable media or that DRM, authorization, proprietary protocols, unseekable/ephemeral provider streams, offline-only items, or inaccessible grants are supported. Use `ContentResolver`/approved URI access, detect unsupported sources, show an honest error and return without waking Kodi or requesting broad storage access. No attempts to bypass DRM or provider authentication.
- One active external player session and **one current media request** at a time. Use generation-safe latest-request ownership (inspired by the 2103446 failure analysis but independently reimplemented and tested). New video B replaces A intentionally, stale callback for A cannot replay, mislabel or close B; same-file reopening is allowed; no ambiguous duplicate launch/Activity instance.
- Splash must not hand the same video to both the external player **and** Kodi. Eliminate duplicate *internal* VIEW handlers and overlapping media sessions. If Kodi was already running, leave its process/state intact and do not hijack Kodi's audio session or shutdown it.
- Define a documented video-session state machine: idle/opening/preparing/ready/playing/paused/ended/error/released. Spinner/loading belongs to the specific request, not a generic Kodi Busy dialog; hide on actual playback readiness or request-specific failure/cancellation; never leave stale Loading visible or claim ready based on another stream. Do not block Android Back with a modal.
- **Stop:** stop playback, release track/decoder/surface resources and leave the player in a safe closed state, with an obvious way to return to the source. **Back/Exit:** finish only the external Activity and restore the originating task when Android permits. **Natural end:** visibly finished state and clear back/close behavior, with no automatic Kodi startup.
- Support play/pause, seek/scrub, mute/volume, track selection/subtitles where engine/source permits, compatible aspect/rotation/resize controls and accessible touch/back gestures. Preserve user-approved look as a visual reference; do NOT promise literal Kodi VideoPlayer OSD or codecs if the new engine differs. PiP only if lifecycle and ownership tested; otherwise document limitation rather than hijack Cobra/Kodi PiP.
- No unnecessary foreground service, leaked wake locks, persistent dialog, background decoding after close, crash loops or hidden second player.

### Test matrix — selected functional work only, not unrelated shutdown suite

1. **Baseline owner/manifest audit**: signed 2103445 source and compiled bytes; compare startup normal and exported intent routes and existing processes. Capture baseline normal launcher/Infinity/Cobra behavior without changing state.
2. **Normal app launch remains exact**: Infinity app launcher → chooser → Infinity/Cobra unchanged; existing Kodi native VideoPlayer retains independent operation.
   **External-label verification**: Android `Open with` option for a video reads `Preview` rather than `Splash`, while the standalone app launcher stays `Infinity`; verify one matching external video handler and no duplicate entries, using a real Android resolver test.
3. **External cold launch** on synthetic granted local MP4: Splash → external player; confirm A renders and audio plays via actual decoders, source URI granted; process inspection **proves no new `:kodi` startup** and no Infinity Home/chooser playback route. Beware tests on device where Kodi was already running: it must remain running, not be stopped or replaced.
4. **External warm launch / rapid replacements**: A→B→C, same URI reopened, share/view intent differences, background return, delayed callbacks. Latest accepted target plays once; old requests cannot win.
5. **Android source matrix**: Files/My Files, MiXplorer, Google Drive `content://` (if real-account tests possible), downloaded file from browser, file vs content URI, direct playable HTTP(S), revoked grants, unsupported DRM/unseekable URI/error/timeout. Never demand private accounts in CI.
6. **Stop, Back, finish and return**: actual on-screen Stop, Android gesture Back, repeat opens, background/Home, screen off/on, fold/unfold/rotation/front/inner, audio focus/phone interruption, decoder release, zero leftover stale Loading. Return to source when task is available; no Kodi/Cobra process affected.
7. **Independent player resource/stability**: short and repeated sessions, memory/decoder cleanup, no ANRs, no user-data resets, settings persistence, no simultaneous dual players, no duplicate notifications. Check compatibility on Android17/One UI and realistic font/insets.
8. **Exact preservation gates**: verify all unchanged Cobra, Kodi, native, unrelated Infinity and shared component members, original 2103445 signer and protected hashes. Only allow signed-diff entries for precisely reviewed Splash routing, private player classes, minimal manifest/resources, registered component/version metadata and original signature members. Enumerate every changed method and resource. Preserve complete older component vectors and original shutdown; shutdown tests NOT SELECTED.
9. Explicit distinction: host/synthetic checks ≠ actual Android decoding/physical Fold acceptance. If Android emulator cannot start Kodi, an **independent-player path should still run**, so it should be tested on its own without blocking on old Kodi first-run prompts. Actual Fold remains the user's approval gate.
10. Do not fake tests, turn blocked tests green, sign an untested unrelated rewrite or auto-lock a version.

### Focused deliverables and workflow

**Checkpoint A**: brief owner map + exact signed baseline source/manifest audit + chosen bounded architecture and dependency proof. Do not get stuck in unbounded historical native ANR/SIGSEGV diagnosis: those are separate rejected-446/Kodi native issues, not prerequisites to an independent video path.

**Checkpoint B**: implement the new private player/activity and the minimal single-Splash intent routing; host tests and actual emulator video playback test. Proven external-only code paths only; preserve intact normal Kodi/Cobra launch. No second launcher icon/application.

**Checkpoint C**: comprehensive targeted Android return/Stop/back/URI/permission/lifecycle coverage and byte-for-byte preservation checks. Fix verified defects confined to this scope. Report limitations.

**Checkpoint D**: deliver **one real original-permanent-key signed combined install-over APK** with versionCode above 2103446 (version monotonicity) yet from **the exact 2103445 source baseline**, containing only the new approved feature and required version/packaging exceptions; matching INFINITY/COBRA/CHOOSER/shared component ZIPs, original signer proof, full changed-member list, SHA-256 sums, actual downloadable GitHub artifact link and Fold acceptance checklist. No uninstall or data clear. **Do not automatically lock**—user accepts after physical Fold testing.

A signed APK for a newly added player with a second app ID, altered existing Cobra methods, restarted Kodi on video VIEW, or weakened shutdown/dual-experience permissions is **NOT ACCEPTABLE**.

**Proceed with implementation after exact source-owner audit. Do not deliver an audit only.**

_This is an authorization and implementation plan; creating this file is not evidence the independent player is built or verified._
