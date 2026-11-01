# Selected follow-up: repeated preview PiP layout requests

Android run 41281620906 records repeated `requestLayout()` warnings for the same
preview CobraIconButton on the exact accepted 2103442 owner. This is separate from
the proven QA Home-gesture failure. The native `CobraSix.smallPreviewPip()` is
called by preview and preview-label layout listeners and unconditionally applies
new FrameLayout parameters even when the calculated rectangle is unchanged.

Before any production change, select one actual-owner host observation:
`PreviewLayoutObservationTest.unchangedPreviewPlacementRequestsLayout`.
Measure repeated same-bounds application, preserving the original rectangle,
visibility and actual button identity. No shutdown or provider operations are
selected. Do not infer crash repair or a device frame-rate gain from this check.

## Confirmed result and correction

The actual accepted method requested layout32 times for32 calls with the same
`96,96,51,4,160,0,0` FrameLayout parameters. The candidate requests zero in the
same observation. Only the `setLayoutParams` call is routed through a strict
equality guard; native placement calculations and subsequent visibility decision
remain unchanged. A separate check proves real resizing, visibility transitions,
Pro exclusion and retained player/texture. All39 current host checks pass.

The candidate advances to2103444 because2103443 was already permanently signed
for internal QA.443 is withheld; one final testing APK will be delivered. No
accepted baseline, lock, key or user data changes.
