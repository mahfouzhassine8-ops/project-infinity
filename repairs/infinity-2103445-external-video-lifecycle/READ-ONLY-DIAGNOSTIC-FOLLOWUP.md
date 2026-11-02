# Read-only follow-up from1a7cfc89 — native Stop wait and private-file access

The request-order correction and nine passing host tests at1a7cfc89 are retained, not restarted or rerun. No production, native/shared, Cobra, chooser or shutdown code is changed by this follow-up. No successor APK is signed.

## Consuming-executor access confirmation

The coordinator supplied the verified identity of the original private archive:1,067,923bytes, SHA256 `874a8df7ae1798a86e5b8e30555529e7caeca44381ffeb72ab7b25586680697a`. That verification belongs to the coordinator's inspection. **This executor still cannot read the archive or the newly attached readable records as actual file bytes.** There is no matching local file; tool discovery and the available skill catalog expose no Library materialization workflow. The available `download_file` tool accepts Sediment-backed files only, not the supplied Library File Service backing ID. The Pages file reader does not support ZIP archives, and no exact authorized private extracted-text Page reference was supplied. No guessed URL, wrong-provider download or public transfer was attempted. No repeated upload or nonexistent recording is requested.

The following stack observations are therefore explicitly secondhand archive-inspection leads, not claims of locally reading the raw ANR:

- `traces/1-1793579659114.anr.txt`, PID7723, supplied lines509–561: Kodi thread sleeping in `CVideoPlayer::~CVideoPlayer+192` through ClosePlayer→StopPlaying→PlayerControl→GUI click, nested in modal dialog/Fullscreen OSD processing.
- Supplied lines27–48: Android main thread synchronously waiting through SendMsg→XBMC_DestroyDisplay→surfaceDestroyed. The actual reported ANR trigger is SCREEN_OFF broadcast timeout10s.
- `report.txt`, supplied line625:5257ms native UI heartbeat gap, window12005/dialog12901/player_flags1.12901 is Video OSD, not a confirmed Loading/Busy owner.
- Archive export reportedly occurred2026-11-02 01:03:36.566UTC on installed2103445/Android17. Historical exit producer versions are explicitly unknown, and native histories are truncated. Export-time installation does not assign every old ANR/tombstone to445; missing events do not prove successful handling.

## Independently verified signed445 reference binary/source mapping

The actual signed445 APK's ARM64 libkodi SHA256 is `151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e`. Read-only ELF parsing confirms destructor D1/D2 at address24832632, size896bytes. Its call at offset168 resolves to `CJobQueue::IsProcessing`; the call at offset192 resolves to the millisecond `CThread::Sleep` template. The available source has:

    CloseFile();
    DestroyPlayers();
    while (m_outboundEvents->IsProcessing())
      CThread::Sleep(10ms);

This is a **signed445 reference mapping compatible with the supplied symbol/offset**, not identification of the historical ANR producer. No GNU build-ID section was obtained from this reference; the historical library identity remains unbound. See [mapping receipt](evidence/NATIVE-STOP-REFERENCE-MAPPING.json). The parser reads the signed library in memory without modifying/loading/executing it.

`m_outboundEvents` is a serial playback CJobQueue (one job at once). Normal IsProcessing checks JobManager running and either pending or processing work. Its existing protected checkpoint branch checks pending/processing work directly. CVideoPlayer::OnExit submits video-settings persistence, file-close/bookmark persistence and playback stopped/ended/error callbacks to this queue. The available StopPlaying implementation already releases the graphics and frame-move guards around ClosePlayer. A graphics lock cycle must not be inferred without the blocked worker stack.

Android's native XBMC_DestroyDisplay synchronously sends TMSG_DISPLAY_DESTROY to the application messenger. If the Kodi application thread is occupied in this destructor wait, that provides a concrete dependency explaining why display-destruction handling can also remain blocked. It does **not** establish which outbound job stalled, why it could not finish, whether a permanent deadlock existed, or whether screen-off preceded/caused the Stop problem.

## Boundary and remaining proof

Do not remove/timeout the destructor wait, cancel persistence jobs, weaken checkpoint/durability guards, skip surfaceDestroyed or move protected native teardown onto an arbitrary worker. Those would change protected native/shared/persistence behavior and could lose saves or violate callback lifetimes. Any proven correction in that path needs separate user authorization after the job/lock dependency is established. Read-only investigation is authorized; such production writes are not.

Still required: actual ANR thread contents and library/version/session binding, particularly the worker processing this player's outbound job and any owner it awaits. The currently supplied stack lead narrows Stop investigation but does not establish the native root cause. The tombstone is separately unresolved and must not be conflated with either the screen-off ANR or the historical emulator constructor crash.

The actual MiXplorer ACTION_VIEW MIME, URI scheme, flags/ClipData and request timeline remain unobserved. The correction intentionally applies only to supplied `video/` MIME with file/content URIs; no broadening is justified to make it appear applicable without evidence. Splash preserves a copied intent but is protected and unchanged. Native content-URI resolution and progress/dialog lifetimes retain their original contracts.

The Loading overlay remains independently unidentified. Existing video A playing is not readiness proof for request B. Do not globally close native Busy/Progress on any player-start event. Obtain its actual window/dialog owner and operation/session timing before any retirement correction.

The exact current blocker and supported next transfer are in [access status](evidence/PRIVATE-DIAGNOSTIC-ACCESS-STATUS.json): make Library materialization callable on this executor, or provide exact actor-authorized private Page file references for already extracted readable ANR/report/lifecycle records. Raw diagnostics stay private. Locked445, all protected components and the existing source checkpoint remain intact; signing stays blocked until the remaining issues are safely resolved and verified.
