# 2103164 audit: exact 8f2c9c7 follow-up

Accepted source parent: 8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261, build 2103163. Exact signed APK SHA-256: 501781d42d87839d8f1f64f3791bee32a6feae023321286f73437e12107b5df3. Existing Candidate 14 and HM Theme 2.0.3 remain unchanged; this branch is an unapproved follow-up candidate.

## Reproduced defects, not speculative replacements

The four unchanged tests in Cobra2103164RegressionTest fail against the exact accepted source: landscape Display submenu is right-middle instead of bottom-center; explicit Cobra reentry retains the old fullscreen overlay; closing PiP before its mode flag clears leaves audio active; clearing the mode flag before onStop instead queues that video to resume. The same four tests pass against the corrected source.

## Corrections

All video settings sheets use current window bounds, capped height and system-bar/cutout safe areas, including submenus and rotation while open. Normal nonplayer sheets keep their prior layout. Menu contents are unchanged.

PiP visibility ends at onStop, independent of PiP callback order. Dismissal latches an explicit stop before callbacks, clears resumable sessions, disposes existing player bindings and prevents stale playback recovery. Native PiP expansion without stop retains its session. Android 12+ auto-entry no longer competes with a second manual request.

Selecting Cobra emits a consumed, Cobra-only browse intent. It does not act as a playback command. Existing live fullscreen-to-preview handoff retains the player; dismissed playback stays silent. Infinity startup is unchanged.

The existing background service is connected to the actual Activity-owned mini-player via non-owning callbacks. Native media Pause/Play/Stop, playback state and position now control/report that same player. Only a foreground, explicitly enabled mini-player handoff grants background playback. There is no onStop service-start fallback, no second decoder, and no sticky fake-playing session after process restart. Generation-scoped media actions cannot stop a replacement session. Foreground return detaches media presence without restarting the player; explicit Stop/task removal ends playback.

## Verification and limitations

Local javac compilation and Android/Robolectric regression tests pass. The 62 inherited tests remain unchanged; 30 additional cases cover the four reproductions, PiP ordering/expansion/reentry, foreground-only mini ownership, media-session callbacks, stale notification actions, service failure/permission/task removal, five display sizes, submenus, safe insets, rotation and palette styling. The source audit preserves 436 of 456 catalogued Activity methods byte-for-byte and proves Splash changes only the Cobra launch intent. CI reruns all 92 tests and exact signing/native/assets/resources comparisons before publishing an APK.

No Kodi native rebuild, signer replacement, playlist migration, EPG/provider algorithm change, system auto-rotate write, or theme ZIP modification. Actual OEM PiP, Fold posture, external SystemUI/Binder delivery, provider playback and hardware decoding require the attached device acceptance checks; automated success is not a real-device claim.
