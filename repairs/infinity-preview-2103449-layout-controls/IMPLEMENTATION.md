# Preview responsive frame and control polish

Continue exact signed 449 while retaining user-selected signed 448 as recovery.
Only four Preview Activity methods change: buildUi, layoutChrome, size and
updateButtons. In the Chrome helper only the native Control drawing changes.

The old frame always used 16:9 and placed controls independently at the bottom.
The corrected Best Fit frame uses actual media width/height and the largest
contained rectangle after reserving header, system insets and controls. The
video, timeline and toolbar form one group with a consistent small gap. Portrait,
square and landscape media retain their proportions. Fill remains explicit crop;
it uses the available video region. Existing video-tap hide/show now releases
that reserved space while chrome is hidden, without replacing the player or
surface. Showing chrome restores the adjacent controls.

A landscape clip cannot fill a tall portrait display without cropping or
stretching. Best Fit preserves the picture; it does not fabricate extra image.
The remaining exterior space depends on video and viewport proportions.

Auto rotation uses a persistent cyan selected treatment, distinct from temporary
pressed/focus feedback. Locked clears Auto selection and retains the Locked
caption. Android state description follows the existing orientation state.
Rotation policy and its saved state are unchanged.

The duplicate Volume dialog/button is removed at the user's request. The native
inline volume slider beside Audio remains the sole level control. Play/Pause,
Stop/Close, Mute, Audio, Subtitles, Display, rotation, seeking and horizontal
scrolling remain. The two seek glyphs are mirrored round arrows with matching
size/alignment; their original ten-second callbacks are unchanged.

Ten focused host checks pass using actual Activity/View dispatch and native
Canvas. A layout fixture initially observed old child positions immediately
following a viewport change. Requesting the queued layout traversal before
measuring resolves that observation; production timing was not delayed. The
host decoder remains a terminal spy, not decoding evidence. Current renders
were visually inspected at cover, inner and landscape in Light/Dark.

The first Android attempt compiled production successfully, then failed while
installing the emulator SDK before any app execution. This remains FAIL. The
next bounded setup attempt prints and uploads installation logs. No Android
behavior PASS is inferred from compilation. The second attempt decoded video and completed both real ten-second seeks, then
failed because the QA observer did not export AccessibilityNodeInfo.selected.
The observer was corrected without changing production code. That run remains
FAIL and its exact completed seek evidence is reused.

The remaining selected Android checks passed in run41539406515 on the same
production DEX. Actual input confirms Auto selected/Locked unselected, no duplicate
Volume button, real inline volume changes, Light/Dark rendering and non-overlap
at1080x2520,1600x1680,2520x1080 and1080x960, unobstructed video after hiding chrome,
and actual portrait/square decoding with corresponding frame proportions. Back
returns to the source and releases the decoder; Kodi did not start. Actual app
renders were visually inspected. All six release-protection checks pass.

Signature and actual APK-member results are recorded in delivery evidence after
original-key packaging. No failed workflow is relabeled PASS. Android emulator
results do not constitute physical Fold, carrier-call or final visual acceptance.

The compiler reports 637 complete class definitions unchanged from signed449.
Only the two now-unreachable duplicate Volume handlers are removed. The source
scope guard preserves every Activity method outside the four selected methods,
all other Chrome drawables, the decoder, request state, resume store, call/focus
handling, lifecycle and external routing. Native, Cobra, Kodi, Splash, chooser,
launcher, shared payload and shutdown are frozen. No user data is accessed or
migrated, and no shutdown suite is selected.
