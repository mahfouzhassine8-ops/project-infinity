# Infinity 2103316 — Close progress and Cobra isolation

Locked parent: APK 2103312, skin 1.0.5.201. APK 2103315 is a test candidate and supplies the tested Android task-removal delta. This candidate does not change the native engine or shorten the measured 60.371-second cleanup.

The old Infinity gear drew 120-degree completed-phase segments, leaving a stationary partial ring during native destruction. The replacement is a rotating, changing-length indeterminate blue arc while the same Kodi owner is pending. Time controls animation only. A full still ring requires the existing production monitor's matching PID/native-cleanup timestamp plus observed process death. Missing or stale cleanup evidence shows an incomplete amber ring; a force request is never represented as successful cleanup. A newly opened chooser does not replay an old success. Hidden/detached views release callbacks; system reduced motion is respected.

Splash now gates only Infinity against Kodi shutdown. Explicit Cobra selection cancels this chooser's queued Kodi handoff and launches Cobra with the original flags, profile, welcome token and recovery behavior. A remembered Cobra default also bypasses Kodi state/preparation. An existing explicit Infinity selection or deep link is never replaced by a default. Cobra's player, controls, power-menu close code, gear drawing and process ownership are unchanged.

## Evidence and verification

Source hashes restrict changes to InfinityExitCompletion (the retained 3315 delta), InfinityGlassChooser (busy arc), and Splash (dispatch). Production Robolectric tests cover a 60.371-second close, continuous rendered motion, matching completion, stale PID/time receipts, missing cleanup, five minutes with no completion, force/cancel, hidden/detached/recreated views, reduced motion, Cobra's unchanged gear pixels, twelve window/palette combinations, Cobra launch/default/recovery during Kodi shutdown, and post-completion Infinity handoff.

Packaging compares protected APK entries and compiled classes against the exact locked APK: the native engine, libraries, bundled skin/data, assets/resources and Cobra player/close classes must be identical. The permanent signing certificate and resource/JNI/manifest contracts are checked. Only the declared close/gear/Splash/version class families may differ.

The signed APK is a device-test candidate. The locked base remains 2103312. Physical acceptance of both paths is required before locking; see DEVICE-TEST.txt.
