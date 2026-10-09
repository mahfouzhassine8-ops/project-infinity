# Infinity 2103339 — selective Kodi 22 shutdown test candidate

Implementation branch only. No accepted or rollback reference is moved. No release lock, device acceptance or claim that every shutdown hang is repaired.

## Exact parent

The implementation uses the approved 2103327 payload, not the experimental 3334 engine used during comparison.
- APK source: `2bb8f12f700ee69fe5d86629e6639bc0b1a0b79e`, successful APK run `37687616440`.
- APK SHA-256: `02449fea9c76ad6a370f2ca26a88fdee3a681f83bdc3efa73f8e213f22d4c4d5`.
- Packaged native SHA-256: `a3f95a64b4433a999df37c18ecc48a3a43876c0cc49ae6c5433e82c98835764c`.
- Native source: `541fdbb25dae16d6e38d7814948a5a8ae54ad13e`, successful native run `37687334233`.
- Full native source-map digest: `cb7a8610093b5e2d3eef627e789f2ced674a77ab4e5031ca6a70adc7719a6a13`, 9373 files.
- Permanent signer certificate SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Skin: preserve exact bundled `skin.infinity.diggz`, parent 1.0.5.201. No skin reinstall or user-data migration.

## Applied behavior delta

Upstream Kodi commit `843ed46fc638b0623fd0d25e865e16f676f61273` releases the graphics-context and frame-move locks around `CApplication::StopPlaying()`'s `ClosePlayer()` call, then reads the active window after closing. The entire parent Application.cpp is hash checked before transformation. A second native file changes only the diagnostic engine tag to `infinity-shutdown-2103339-v1`.

The actual reconstructed source has passed the full-map gate. Six host scenarios (null GUI, inactive player, unowned guards, recursive ownership, exceptional close, and script/player lock cycle) pass against both the parent and patched methods, each repeated three times. The tests compile the actual Kodi POSIX mutex, CountingLockable and CSingleExit helpers with Android conditionals. Player and GUI APIs are simulated. The negative parent case is released by the test fixture after observing the blocked condition; no production join or timeout is altered.

## Deliberately not changed

Scanner ordering commit `6332b0f9a7eab93531751039fac837540c39f12e` is not transplanted literally: this parent already closes JobManager admission at `PrepareAndroidShutdownScripts` and early `Stop`, before the later scanner calls. A final CancelJobs reorder alone would not implement the intended contract. This broader ordering change remains deferred, not completed or declared safe.

No wholesale Kodi 22 / Python ABI migration, reverted GLES teardown port, diagnostic worker replacement, new save/checkpoint system, process-kill fallback, shorter cooperative grace or removed final join. Experimental 3330/3334/3336/3337 engine deltas are not silently added to the approved parent.

## Build association

- Native implementation commit: `bd4e25402ee77e94ab745a05ad4bc348d1226c18`.
- Native build run: `37865197244`. Source reconstruction and production-method host tests passed; native compilation was still running when this note was written.
- APK implementation commit: `bcb805f1f9c6750667bd2158aa1174b939617bf8`.
- APK build run: `37865645821`. Exact parent APK/source/signature and identity-only Android prechecks passed; it waits for the exact successful native run. No old-engine fallback.

The APK changes two Android diagnostic identity files only, builds the matching Android shell, runs all inherited 3327 regression suites without reducing the accepted test counts, and checks unrelated DEX behavior, JNI declarations, manifest structure, resource IDs and every protected APK payload entry. Permanent signing is verified against the parent certificate. These final gates are not yet reported as passed.

Expected output: `Infinity-2103339-Kodi22-Selective-Shutdown-RC1.apk`, package `com.projectinfinity.kodi`, version 2103339. It is a test candidate, not a locked release. Native hash and APK hash must come from completed proof files, never be guessed.

## Physical acceptance still required

Test idle close, active audio/video stop and close, service/widgets active, background playback return, repeated close/reopen, fold/rotation, and retained resume/watched/settings/provider state. Match close request, actual native completion and process exit to the same current PID. A successful CI run is not physical Fold acceptance.
