# 2103377 — coordinated native entry and task retirement candidate

Continue from df1261820c8484aa8708da3d04b319bb6e5387bf and the exact green runtime artifact from 38351703759. This directory stages a reviewed delta on a COPY of that source. The saved green runtime, original test files, protected APK 2103376, Skin 211, native owner lease, checkpoint coordinator and termination authorization are not replaced or bypassed.

## Scope

A Kodi process takes a nonblocking, process-lifetime shared file lease before startup preparation. The task-retirement method takes the exclusive side for its complete ownership validation and task-removal call. A pending replacement is protected even before its asynchronous owner JSON is published. If removal wins first, native entry is not admitted while it holds the lease. No Activity pause/stop/destroy callback releases the entry lease; process death does.

A process-local single-use intent ticket binds Main to the existing preparation/chooser path. Cold Main restoration has no valid ticket. The matching NativeActivity entry wrapper declines native_app_glue startup and lets Java return to the existing chooser. Declined-creation callbacks do not publish checkpoint completion, stop other playback services, or overwrite an accepted Main ownership slot. The admitted path retains the existing lifecycle/checkpoint operations, but moving initialization behind admission still requires full Android/native lifecycle validation; behavior preservation is not inferred from the host tests.

The Android delta changes only Main, InfinityKodiEntryActivity, the scoped retirement method in InfinityCloseGuardService, Main's native entry metadata and CMake registration, and adds two helper classes. It preserves 259 of the 264 previous runtime files byte-for-byte. The native delta adds one header include to the exact 2103376 android_main.cpp and adds the entry wrapper header. No timeout, source/provider integration, skin or Cobra implementation changes are included.

## Mandatory pairing and open gates

**Do not package the staged Java with the old native engine.** Main's manifest selects InfinityNativeActivity_onCreate, which must be exported by the matching fully compiled native engine. apply_native requires the complete exact native source manifest and checks the entry translation-unit hash. The host C++ test verifies wrapper decisions with controlled peers, not Android ABI or full Kodi linkage.

The local draft Android workflow is configured to compile and rerun the exact 234 old cases plus 40 additional cases, enforcing original source/fixture hashes and case names. It has not been published or run. None of those 274 tests is counted as a fresh pass. Separate host tests use real process file locks and exercise native callback decisions. A workflow green is not a Fold acceptance, shutdown fix or signing authorization.

The shutdown-blocking backend and actual cancellation/retirement repair are still unresolved. The uploaded continuation archive is not a new device probe. Exact installed Playlist Browser evidence and a correlated native operation trace remain required. Do not disable its service or call a reader durable to satisfy this gate. No APK should be presented as a completed repair while these gates remain open.

## Platform basis

The Android NativeActivity metadata API supports a selected entry function. Native callbacks default to null, so a declined wrapper need not start Kodi native_app_glue to complete the superclass lifecycle. AOSP AppTaskImpl calls task removal without the kill-process flag and serializes task state under the window-manager lock. The source design still needs full native integration and physical lifecycle verification on the user's Fold.

Primary references reviewed on 2026-10-13:
- Android NDK Native Activity reference: https://developer.android.com/ndk/reference/group/native-activity
- AOSP NativeActivity.java: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/app/NativeActivity.java
- AOSP AppTaskImpl.java: https://android.googlesource.com/platform/frameworks/base/+/master/services/core/java/com/android/server/wm/AppTaskImpl.java
- Android FileLock reference: https://developer.android.com/reference/java/nio/channels/FileLock
