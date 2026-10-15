# Infinity 2103303 repair candidate — validation in progress

The authoritative starting point is 2103302 commit e0bd90006c71c605010172c919358f6939c91ae8 and its verified 246-file Android source export. The existing Infinity skin is `skin.infinity.diggz`, version 1.0.5.190. Its internal ID is preserved. `skin-baseline-sha256.json` records all 2,892 original skin files; transforms refuse any different preimage. Rollback branch/tag: `rollback-infinity-2103302-before-e2e-repair-20261003`.

## Implemented source candidate

- Chooser slogans removed; the main line is exactly `TWO UNIVERSES.`. Weather and startup-preparation implementations remain protected by exact preimages and the compiled weather isolation audit. Chooser waiting and Kodi handoff timing are separate.
- Existing skin: compact logo/hamburger capsule, downward drawer expansion, corrected Infinity hub routes, centered busy/confirmation/select/context panels, compact settings category grid, radio-label reservation, official logo assets, and one horizontally scrolling player rail with separate vertical volume mode.
- Movie details: contained content and scroll ownership; custom Back/Trailer/Cast IDs no longer collide with Kodi's native artwork/extras/review actions. The movie-video rectangle is unchanged. The preview layer is visible only after an explicit trailer request.
- Ambient glass sampling: 6 Hz cap, lazy allocation, release when ineligible, on layout changes and when materials become hidden; session destruction is idempotent. This does not start or stop Kodi playback.
- Actual native touch recognizer: stale-hold, cancelled-pointer, movement-versus-hold and duplicate-up handling. Existing gesture detectors are preserved.
- Mobile Android IME bridge: editable text, selection, paste, Unicode, search/enter, password masking, numeric/PIN/address/date/time paths; TV/remote-only fallback preserved. Native and Java halves must be packaged together.
- Evidence-only watchdog: bounded foreground UI/native heartbeat observations, recovery times, stacks, window/dialog/player/ambient state, session and skin-load identity. Android exit records are correlated separately. Current Android bounds and native render-owner requested/accepted dimensions replace historical-only diagnostics.
- Native cleanup completion record after CXBMCApp::Destroy. A 15-second exit observer records a stalled close; chooser recovery requires an explicit user action. No automatic process kill or automatic reset is introduced. The active unified power-menu profile now uses the existing lifecycle-safe exit routes.

## Validation status and limits

The Java-only workflow reconstructs and tests the actual source lineage, including inherited tests, Robolectric API 35 IME/lifecycle tests, ten weather tests, and compiled weather no-JNI checks. Successful runs before the latest extension include 37164130135 and 37163817756; the latest run is authoritative for current-source results.

The native workflow reconstructs every inherited engine transform, runs its existing compiled tests, applies only declared candidate changes, and builds the full ARM64 library. It preserves hashes for all captured native source files. A successful native build is required before APK packaging; an uploaded partial audit artifact is not a successful build.

Locally, all 2,026 skin XML files parse. Seven compiled scenarios exercise the real modified touch recognizer and original gesture detectors under AddressSanitizer/UndefinedBehaviorSanitizer. Three resource tests exercise the actual ambient session/material owners. These are not visual/device acceptance. LeakSanitizer is unavailable in the local container; tests disable that component only.

No Samsung/ADB connection is available. Every physical acceptance case remains pending: cover/inner, portrait/landscape, split/pop-up/live resize, cold/warm launch, immediate/delayed relaunch, background/foreground, active/no playback, light/OLED, touch and IME open/closed. Provider-owned source windows also need runtime verification; the contained standard DialogSelect cannot prove every external provider's custom window.

Historical SIGSEGV ownership remains unproven. The provided diagnostic TXT replaced binary protobuf bytes with UTF-8 replacement characters. Its three native crashes predate completion of the 2103302 CI build. Original binary tombstones and exact build-ID-matched symbols are needed for symbolication. The old collector's hardcoded native hash is not ownership evidence. The exported raw-trace ZIP preserves future evidence without decoding native bytes.

The delayed takeover's original owner, historical native crashes, actual CPU usage, teardown completion, and black-screen relaunch require device evidence. Do not describe this source checkpoint as accepted or all 27 requirements as verified. No installable APK has been produced by these validation workflows.
