# Infinity 7.1 — architecture audit and repair record

Date: 2026-09-08. Status: source repairs and local preflight passed; full native CI and device acceptance remain separate gates.

## Scope and provenance

This audit compares the real source, not candidate names or token-presence assertions. Kodi is pinned to 21.3-Omega, commit `a3a448d26b8d560a65655dab2cd122994dc4e146`. G2 means Candidate G at `9d39904dc95f950628c5f1657fbfde7c4cf59101` with its debug-keystore prerequisite; this repair is a separate **Architecture Audited** build. The existing G2 workflow and source scripts are not rewritten by this repair.

The older G2 donor ID `9987818547`, described in its workflow as “7.0,” resolves to `Infinity-Stable2-PiP-v3`. The actual 7.0 presentation reference is artifact `10037657045`, `Infinity-Fold-Tablet-7.0-OLED-Lock-TouchRefresh`, from run `34177152129` and commit `09ed2a0c7f45e3fb6c8b5d9714bbb46dff245d6e`. Its artifact ZIP SHA-256 is `2d98f01bd8e7d7b4fe2e1d718ca265432a99c7f3484d50c3d21bc539b6b212d3`. Preserved asset hashes and original paths are recorded in `assets/infinity-7.1/provenance.json`.

The actual 7.0 APK's bundled add-ons were inspected. It does not contain a bundled custom Infinity Python controller/add-on to transplant. That does not establish what is installed in the user's private Kodi userdata. The separate Standalone V1 APK was not retrieved; its binary behavior was not independently verified. Prior scope and known device observations are retained in `docs/INFINITY-7.1-CORE-UNIFORM-AUDIT.md`.

## Findings and changes

| Finding in G/G2 | Evidence | Repair |
| --- | --- | --- |
| A real JNI hook was present, but “verified hook” overstated what had been tested. | Native tables and virtual dispatch exist in the old hook scripts. Original checks mainly look for strings. | Match declarations, registered descriptors, generated Java bytecode and actual DEX native flags; exercise state and packaging invariants. |
| Fresh upper-layer packaging is blocked before the bridge call is inserted. | `patch-infinity-7.1-uniform-app.py` requires `updateInfinityPictureInPictureParams` inside freshly decoded Main before inserting it; pristine Main does not contain it. | Replace post-build smali surgery with a source-built Java adapter and explicit CMake packaging entry. The new pipeline never invokes that script. |
| The intermediate base APK does not declare the added native methods yet. | G2 registers new methods in native code but adds their Java declarations only in the later decoded APK. | Compile Java declarations, native registration and adapter together before producing the independently reusable engine base. |
| Modern PiP and legacy pause logic are not reconciled. | Exact Kodi `CXBMCApp::onPause` tests `m_hasReqVisible`, while the new Java layer enters modern PiP. | Preserve the NativeActivity lifecycle; consult Android's actual PiP state before the video-pause branch. Keep audio focus and normal background/stop handling. |
| PiP eligibility is insufficiently distinguished from active video. | Active video includes a paused or external-player session; G2 disables API 31 auto-enter instead of publishing state ahead of Home. | Use existing Kodi Player announcements to publish current active/playing/internal facts and video aspect ratio; Java rereads facts on the UI thread. API 31+ gets early auto-enter parameters, API 26–30 gets gated explicit entry. |
| Fold refresh updates display-mode enumeration but not the complete render/input geometry chain. | Original helper calls UpdateDisplayModes and DPI, while native surfaceChanged is still effectively unhandled. | Publish actual laid-out view dimensions; coalesce requests; apply buffer/render/graphics/input/GUI changes on Kodi's main/render thread through its existing ApplyModeChange path. |
| Resize and surface lifetime are conflated. | Old patch resets `m_window` during resize. | Keep window ownership until the existing surfaceDestroyed path; invalidate committed geometry on destruction and retry after recreation. |
| UI callbacks can touch render state or wait for a native window. | Old sync directly calls window-system mutation, and width/height call GetNativeWindow. | UI callbacks publish snapshots only. Getters return committed atomic size, or -1 while unknown. Physical mode re-enumeration is also queued to the render thread; its completion event remains on the callback path to avoid blocking SetDisplayMode. |
| The supposed 7.0 donor is a different artifact; the original lock is replaced with a reduced dialog. | Downloaded artifact metadata and both decoded APKs. | Preserve actual 7.0 lock dialog, its timers/unlock behavior, lock/unlock images and icon by hash. Do not transplant old Java/native libraries or stock Kodi add-ons. |
| Theme/resume changes are presented as compatibility work without end-to-end evidence. | G2 creates replacement palettes and broad text substitutions; existing stabilization scope says not to re-enable the crashing theme experiment. | Keep stock 21.3 resume/database and current skin framework. Expose system-theme facts, but do not activate an automatic OLED/light theme consumer or rewrite resume wording. |
| A presentation failure discards the expensive native result. | G2 uploads only after the entire monolithic job succeeds. | Separate preflight, engine and presentation jobs. Upload engine base and complete inventory before the skin overlay. A dedicated repackage workflow has no native compilation. |
| Signing identity changes between candidates. | Existing workflows generate fresh keys. | Support optional persistent signing secrets, explicitly label ephemeral signing as test-only, and make no install-over claim without a matching certificate. |

## Cross-reference: the actual upstream flow used

**Java/JNI:** Kodi `tools/android/packaging/xbmc/src/Main.java.in` native declarations and existing lifecycle supercalls; `xbmc/platform/android/activity/JNIMainActivity.{h,cpp}` RegisterNatives and `m_appInstance` dispatch. Existing `_onNewIntent`, `_onActivityResult`, `_doFrame`, `_callNative` and `_onVisibleBehindCanceled` stay intact. Java templates are included by `cmake/scripts/android/Install.cmake`, not merely placed on disk.

**Player:** `CXBMCApp::Announce` receives existing Player announcements; `CApplicationPlayer` supplies IsPlaying, HasVideo, IsPaused, IsExternalPlaying and GetRenderAspectRatio. These publish atomic facts. Java receives a no-argument signal, marshals onto the UI thread and rereads current state instead of applying a queued stale boolean. No new JSON-RPC polling or timer is added.

**Window/render/input:** Main's real laid-out view publishes an immutable dimension snapshot; layout and existing surface callbacks queue the request. `CWinSystemAndroid::MessagePump` consumes it after normal event pumping, on Kodi's core thread. Existing native surface ownership is preserved. Buffer geometry and ResizeWindow are reconciled with the current RESOLUTION_INFO; `CGraphicContext::ApplyModeChange` runs Kodi's own graphics/scissor, mouse resolution and GUI resize path. The active resolution enum, physical display mode/refresh identity, and TV fullscreen GUI-limit policy are preserved. Rapid requests coalesce to the latest dimensions. A zero-size transient cannot overwrite a valid request; committed getters do not claim a requested size has already been applied.

**PiP lifecycle:** Keep native lifecycle callbacks, use Android's real PiP state for the pause exception, and retain normal stop behavior. The Java adapter checks SDK support, platform feature, activity lifecycle and native internal-video eligibility. Source-rectangle and aspect data are supplied before entry. A source-level check is not proof that every OEM gesture or hardware-decoder surface transition works.

**Presentation:** Repackage the verified base ZIP with only four allowlisted skin members changed. Preserve original 7.0 lock dialog/images and insert its OSD button into fresh 21.3 Estuary. DEX, all native libraries, binary resources, manifest, native resume code and every other base member must remain byte-identical. The branding icon is included in the source-built base; no old resource table is copied.

## Contract

ABI version 3: `_infinityHasActiveVideo()Z`, `_infinitySyncDisplayState()V`, `_infinitySystemThemeMode()I`, `_infinityWindowWidth()I`, `_infinityWindowHeight()I`, `_infinityBridgeVersion()I`, `_infinityCanEnterPictureInPicture()Z`, `_infinityVideoAspectRatio()F`, `_infinityWindowMode()I`.

Theme values: 0 unknown, 1 light, 2 dark. Window mode bits: 1 PiP, 2 multi-window. Window getters report the committed native geometry, -1 before a valid commit. Bridge version is checked before the Java adapter attaches. This is a deliberately bounded bridge, not a promise that arbitrary future engine changes can be implemented outside native code.

## Validation actually performed locally

All checks were rerun against the final source postimages after the raw-resolution/stereo comparison correction.

- Exact preimage/dry-run/postimage SHA-256 checks over 14 changed/new text source files, plus the preserved icon. Mixed or unpinned source is rejected; a fully applied source set is idempotent.
- Real changed Main and InfinityCoreBridge, with three unchanged Kodi Android supporting classes, compiled against Android API 34. Unchanged TV scheduling, JSON-RPC and generated R collaborators are explicitly compile-only stubs. This is an API/descriptor check, not a whole application or Android runtime test.
- D8 generated a real DEX at min API 21. All nine new compiled JNI descriptors matched, and tests parsed the actual DEX native flags/prototypes rather than searching for strings.
- 18 Python regression tests passed, including source wiring, lifecycle retention, provenance, package identity, strict base inventory and tampering rejection. Package fixtures contain non-installable placeholder native bytes; they prove packaging invariants, not ARM64 execution.
- Host C++ state tests compiled with C++17, `-Wall -Wextra -Werror -pthread` and passed: playback eligibility, committed/unknown geometry, zero-size rejection, surface recreation, event coalescing, physical mode request flag and 20,000 concurrent packed-size updates.
- Both new YAML workflows parsed and the signing shell script passed `bash -n`.

## CI gates and what remains unproven

The full build is gated on preflight. Once the unchanged Kodi dependency toolchain has configured the native build, the workflow uses the actual generated compile_commands.json and recorded cross-compiler to syntax-check all three changed C++ translation units before the full engine build. This full Android C++ gate has not yet run at the time of this local audit record. A compile failure must be fixed before claiming a native build result.

A successful compile/link/package still does not prove cold boot, JNI load/registration on device, modern Home gesture PiP, pause/audio focus behavior, Fold input alignment, hardware-decoder surface recreation, lock interaction or TV compatibility. Those remain device acceptance tests. No claim of “all mistakes eliminated” is made.

Persistent signing material has not been retrieved or configured by this audit. When the four documented signing secrets are absent, the workflow emits a test-only APK and a warning. Do not uninstall an existing Infinity installation to work around a certificate mismatch without a verified backup of userdata. A debug/base keystore is not the final stable signing identity.

Automatic OLED/light presentation, a generalized Python controller bridge and a custom resume UI are not newly enabled here. Stock native Kodi resume is preserved. Installed user add-ons/settings and the separate Standalone V1 binary are outside this verified scope.

## How iteration changes

`build-infinity-7.1-audited.yml`: preflight -> engine -> saved `Infinity-7.1-Audited-Engine` -> presentation -> `Infinity-7.1-Audited-Candidate`.

`repackage-infinity-7.1-audited.yml`: explicitly select a successful matching engine run -> verify its base, patch hash, package, ABI and every member -> overlay -> sign -> re-verify. No C++, Java or Kodi dependency build. It can be requested by workflow_dispatch, or by committing `build/infinity71-repackage.json` with a positive `engine_run_id` on the working branch. That request path is not watched by the engine workflow.

Native/ABI/rendering changes still require native verification and a new engine build. A four-file presentation change does not. The reusable engine artifact has finite retention; preserve it before expiry. This reduces unnecessary waits, not all future waits.

## Device acceptance checklist

Cold boot under `com.projectinfinity.kodi` alongside official Kodi; verify expected Infinity branding and no native-load error. Fold inner-to-cover and back while idle and during playback, checking pointer alignment after every transition. Test Home PiP while actively playing, paused, stopped and using an external player; return to fullscreen and repeat. Test split-screen/PiP exit, audio interruptions and app stop/resume. Test original lock overlay and unlock timers. Check normal resume bookmarks. Do not promote the engine as frozen/verified until these checks pass on the intended device.

## Primary references

Exact Kodi files above at `a3a448d26b8d560a65655dab2cd122994dc4e146`, plus `xbmc/windowing/GraphicContext.cpp`, `xbmc/windowing/android/WinSystemAndroidGLESContext.cpp`, `xbmc/platform/android/activity/AndroidUtils.cpp`, `xbmc/application/ApplicationPlayer.{h,cpp}`, and `cmake/platform/android/android.cmake`. Android's official Picture-in-Picture guidance and JNI tips were also consulted for lifecycle, feature/API guards and JNI reference/exception handling. Donor-derived assets retain their upstream project licensing.
