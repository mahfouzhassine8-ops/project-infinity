# Cobra 2103202 requested player refinement — test candidate

Parent: locked 2103201, commit 57a7b93abc073154ff36d717e2638b778dc378ba. A complete product rollback was verified and saved before edits. The locked branch/APK remain unchanged. This candidate is not locked or physically accepted.

Requested changes: both saved language preferences moved into Audio & subtitles; duplicate Channel playback display route removed, dedicated Display retained; existing Recents surfaced in Channel playback; Restart live playback reconnects without clearing settings; channel PiP/background/rewind overrides support inheritance; subtitle size and screen adaptation are profile-scoped; existing timeline shades the available rewind window and marks its live end (provider catch-up is not mislabeled live); Multi-View order/audio selection/pause intent are restored after PiP, including app-icon return.

Proven baseline touch defect: real Android MotionEvent dispatch through extracted production row methods reproduced swallowed icon taps in both subtitle and file-picker rows. The candidate makes decorative children non-interactive so the existing row receives the tap. Text taps and cancelled gestures remain protected. This is Android/Robolectric evidence, not a physical touch-latency measurement.

Open sheet size now follows the current window and rebinds a replaced player-toolbar anchor. Fold Adaptive remains proportional whole-frame fitting using actual TextureView dimensions. It cannot fill a differently shaped screen without cropping or stretching; neither is silently introduced. All 13 display-mode regressions remain required.

Changing one preferred language no longer clears the other track type's manual session choice. Stream subtitle availability and real caption decoding remain device/provider acceptance gates. Subtitle preferences cannot create absent tracks.

Background audio reuses the existing Android media-service owner; only the selected screen is eligible. PiP has precedence. Global defaults remain unchanged; explicitly saved channel overrides win. Rewind preference changes reconnect only the affected active channel and preserve pause intent. No universal buffer/network tweak, native-engine modification, transport rewrite, or new provider session architecture was introduced.

Runtime diagnostics include effective channel policies, actual background audio owner, subtitle sizing/adaptation and pending Multi-View count without recording provider URLs or credentials.

Verification categories are separate: source/hash preservation; host collaborators; Android/Robolectric view/lifecycle/track tests; APK/signing/payload checks; physical-device acceptance. Build success alone is not product acceptance. See DEVICE-TEST.md and the machine-readable acceptance receipt for completed automated results.

Android lifecycle reference used for PiP callbacks and view ownership: [Android PiP documentation](https://developer.android.com/develop/ui/views/picture-in-picture). No migration to a different player or PiP architecture is part of this patch.

Remaining limitations: no connected physical Android/Fold endpoint; no controlled captures of the user's problem streams; no guarantee of state after operating-system process termination; existing native 16 KiB compatibility questions and unrelated prior audit limitations remain documented in the locked parent's report. File-picker OS/provider behavior beyond the reproduced row-touch defect must be checked on the device.
