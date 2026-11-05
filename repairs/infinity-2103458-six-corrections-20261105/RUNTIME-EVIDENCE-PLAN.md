# Current-runtime evidence, without changing the application

Source binding: existing Health Center files were read from the preserved payload and their hashes checked against signed 2103458's ALL-APK-MEMBER-HASHES.json. No Health Center code is changed.

## What existing evidence establishes

The supplied November 5 archive is a chooser-side capture of 2103456. Its disk skin metadata differs from packaged source, and its runtime_active fields are UNKNOWN. It cannot establish the currently selected 2103458 skin or loaded modules. No Android device/ADB connection is available in this executor. Current identity and navigation observations remain NOT RUN.

## Supported existing collection path

In **Kodi Health Center → Crash Center → Export Infinity / active-skin details**, the existing handler calls `export_report(current_only=True, include_skin=True)`. It reads `xbmc.getSkinDir()` and the selected add-on's resolved path, then includes:

- environment-now.json: active skin ID/version and current recorder session.
- runtime-component-identity.json: actual Kodi-resolved module/add-on paths, versions, source hashes and existing native signature verification outcome.
- active-skin/*.xml: definitions from that resolved skin (subject to bounded export limits).
- manifest/omission records: distinguish absent evidence from unequal files.

`Send Logs for Help` also includes runtime-component-identity.json, but does NOT request active-skin XML. Use the active-skin export for drawer attribution. Do not invoke Start Fresh, repair, cleaning, test arming or shutdown actions for this observation. Exports remain private and are reviewed before sharing; no automatic upload. The archive can contain private log text despite filtering. No new export of the already supplied historical ZIP is needed.

Compare the current resolved unified/Custom_1198_InfinityNav.xml, unified/MyVideoNav.xml and module hashes with signed 2103458, not with 2103456. Resolve skin identity and native layout selection separately: packaged `infinity-native-responsive-v1.disabled.json` does not enable `UsesNativeResponsiveLayout()`. A present live `.json` marker would change resolver behavior and must be observed, not inferred from the existence of responsive folders.

## Direct-library transition evidence

On the same identified session, observe drawer Infinity Movies and Infinity TV Shows separately, including starting window, clicked control, target window, container path, loading completion/failure and Back return. Use existing Kodi debug output or already-authorized local JSON-RPC read access if available; do not enable remote access or expose credentials. Record only scheme/route class and library type; omit titles, media paths and account data.

Packaged controls already dispatch `ActivateWindow(Videos,videodb://movies/titles/,return)` and the equivalent `tvshows/titles/`. In GUIMediaWindow, `return` can retain a previous directory when the requested path equals the window start directory. Failed directory retrieval can also fall back through history/root. Neither mechanism is yet attributed to the Fold report. Dropping `return` without observing the transition could change Back/history; no such edit is made.

## Search failure and actual stress evidence

The historical archive has two signal11 summaries but no failing native stack, no trace member, empty native-crash-last.txt and no exit-manifest trace records. Do not label either crash fixed or attribute it to a specific provider.

Safest next collection uses the existing Crash Center incident export, with its optional Android evidence consent, immediately following a naturally reproduced failure. Bind PID, timestamp, package version, native SHA/BuildId and Search operation timing. If Android withholds a tombstone, report that limitation. A legitimate connected Android device can additionally provide existing logcat crash output / a user-authorized bugreport; no rooting, forced crash, restricted-path bypass or production instrumentation is proposed.

After identity is established, run at least 30 real Search All operations on the supported device, recording completion, provider outcomes, cancellation ownership, concurrent outstanding work and process memory where existing diagnostics expose it. Stop at a crash and preserve evidence rather than automatically relaunching 30 times. Separate the crash result from the two known state_changed outcomes. Host synthetic RPC calls do not satisfy this gate. No real Android/provider stress was executed here.
