# Targeted VFS shutdown evidence

Continue from accepted Android receipt 12220187 (274 tests) and full-native receipt 567d70a (run 38367761382). Both new physical captures fail at the existing 25-second deadline. The fully-loaded capture has one named pending Python service: plugin.video.playlistbrowser/service.py. These captures do not include its installed source hashes or the native backend identity. No responsible backend or shutdown correction is asserted.

## Diagnostic scope

The exact green native source receives six observation edits and one header. The matching saved native-entry wrapper is retained. The tracer selects only Playlist Browser's service invoker worker. It retains bounded atomic operation records before Close, samples them from the existing shutdown path, and uses the existing native trace/export mechanism. It cannot authorize termination, cancel an operation, change timeouts, remove an add-on, or modify a persistence receipt.

Each observed open reports a process-unique operation ID, parent ID, original monotonic start timestamp, fixed resource/backend/stage categories, existing shutdown notification events, boolean/exception return, and subsequent interpreter receipt outcome. Actual factory branches identify their backend; wake-on-access, VFS add-on lookup, directory-cache, authentication, backend open, stream-buffer work, and Curl polling have distinct stages. Redirected unclassified implementations are explicitly unknown. Curl's existing Cancel callback and numeric transfer result are observed; zero callback observations are not proof that another backend supports cancellation. Poll iterations update atoms without per-iteration file output. A full registry or event budget is reported as incomplete evidence.

No resource paths, URLs, query strings, headers, credentials, playlists, exception messages, pointer values, or unrelated userdata enter the added trace. The existing trace producer and PID/session clocks remain authoritative. A returned open is not a durability verdict. Only the existing persistence ledger determines interpreter retirement.

## Explicit diagnostic APK

The diagnostic APK has version code 2103377 and version name `1.0.9-VFS-Open-Diagnostic-RC1`. It is permanently signed only after full compilation, trace checks, source preservation, ELF export/dependency checks and exact locked payload checks. Its Java/Dex, resources/assets, and other native libraries are byte-identical to the locked 2103376 APK. Only libkodi.so and the manifest version fields differ. The saved 274-test lifecycle implementation is preserved separately for the final repair and is not claimed deployed by this diagnostic.

This diagnostic is not the completed 2103377 repair. No shutdown fix, physical acceptance, promotion or lock is claimed. Original signed 2103376 APK and skin 1.0.5.211 remain the protected rollback artifacts.

## Next exact device capture

1. Install the separately delivered diagnostic APK as an update to the current app; retain app data and skin 1.0.5.211.
2. Fully load Infinity. Run the existing **Infinity Shutdown Evidence (one-shot)** add-on and save its generated `Infinity-Playlist-Probe-*.zip`. Dismiss its final OK dialog and let the add-on exit.
3. Select normal **Close Infinity**. Let the close or failure settle, allowing about 45 seconds so post-deadline operation return and interpreter retirement can be captured. This does not change the checkpoint's deadline or classify a failure as success.
4. Export diagnostics through the existing Health Center. Share that `Infinity-Diagnostics-*.zip` plus the generated Playlist Probe ZIP. Avoid a second Close before this export so the relevant current/previous trace is retained.
5. Record whether this was fully loaded or early Close and what the close dialog displayed. No playlists, account settings, passwords or whole userdata export is needed.

The required final repair still needs an identified backend/cancellation failure, evidence-backed correction, unchanged 274 tests plus targeted regressions, final full-native verification, integrated lifecycle packaging, permanent signing and physical approval.
