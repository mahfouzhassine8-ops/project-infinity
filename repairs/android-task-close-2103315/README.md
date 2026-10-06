# Infinity 2103315 — Android task close

Parent: locked APK 2103312, permanent signer, Infinity skin 1.0.5.201, Cobra Pro Teams preserved.

The Kodi NativeActivity is declared in Android process :kodi. Splash/Choose Your Experience remains in the app's default process. The Close Kodi action now requests Android's task-removal lifecycle with finishAndRemoveTask() on Main, suppresses the normal-stop JSON-RPC Application.Quit dispatch, and lets Main.onDestroy() run Android's normal NativeActivity destruction. The separate Force Close button remains unchanged.

This is an Android-only candidate. The locked Kodi native library, all other libraries, Cobra bytecode, assets, resources, manifest permissions, data and skin are protected and byte-verified. The source change affects only InfinityExitCompletion, which owns both explicit power routes. DEX comparison allows only that class family and BuildConfig to differ.

## Engine/build clarification

The 2103314 Actions artifact contains the native build log, not a distributable native library. Its log reaches `[100%] Built target kodi`, but the overall compile/validation step failed afterward and did not publish an engine binary. This fast 2103315 package therefore intentionally inherits and byte-verifies the native engine from the locked 2103312 APK; it does not claim to package the 2103314 engine output.

## Verification

CI runs the production Plan phase tests with Robolectric, verifies the source change against the complete locked source map, compiles the APK Android layer, compares every protected APK entry, checks the stable signing certificate and confirms all other compiled classes including Cobra are unchanged.

This does not claim physical device acceptance. Install over APK 2103312 without uninstalling or clearing data. Press Close Kodi, immediately open Choose Your Experience, and test Infinity and Cobra. Confirm ordinary Cobra close and the separate Force Close command remain functional. If Android task removal still waits at NativeActivity destruction, export Health Center after reopening; the ANDROID_TASK_REMOVAL phase will show that the request was accepted while the Kodi process remained alive.
