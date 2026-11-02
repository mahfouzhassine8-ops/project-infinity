# 2103447 verification and limits

Android feature run [41411542660](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41411542660)
passed on the selected API37.1 x86_64 emulator. Its hash-verified artifact and
individual evidence hashes are recorded in `final-evidence/ANDROID-EVIDENCE.json`.
The runtime's DEX and manifest outputs match the locally reviewed production
outputs exactly. Packaging requires these exact outputs; the only subsequent
manifest difference is the controlled final version code.

Passed: 14 host request/state tests, six release/preservation tests, and the
finite actual Android journey. Android evidence includes 26 actual control
touches and seven decoded playback sessions: granted content, video SEND, rapid
A/B/C ending on C, same-file reopening and direct HTTP. Play/Pause, seek, mute,
audio-track selection, displayed text subtitles, Display selection, rotation
button state, Stop and Back were exercised. Denied access, invalid media and an
audio-only source produced errors with Retry and no stale loading. Natural end
returned to the source. Final OS evidence confirms the source was resumed and
focused, the external Activity was removed and no external MediaPlayer client
remained. The selected journey log has no FATAL EXCEPTION.

The video decoder reported actual H264 frames; AudioFlinger had an active AAC
48kHz output track for the external process. The emulator uses `-noaudio`, so this
is decoder/output evidence, not a claim of audible physical-device verification.
No `:kodi` process appeared during the observed external playback checks.

The captured viewport changed from 1080×2520 to 1600×1680 and playback remained
visible. Both larger screenshots were 1600×1680 even after the second wm request;
the recorded `landscape_resize` step means that request executed, **not** that a
landscape geometry assertion or physical Fold transition passed. Actual hinge,
orientation, split-screen, Samsung insets, screen-off and audio-interruption
behavior remain physical acceptance checks.

The known baseline native-library compatibility notice was acknowledged with OK
in the disposable emulator only. No Don't Show Again, native-library change or
compatibility-setting override was used. Earlier failed runs remain failures:
initial setup/observation issues, the real queued-intent defect (corrected), the
obsolete final-state field and the late platform notice are retained in evidence.
The final successful journey has no waived assertion or continue-on-error.

Every original Infinity class and every Cobra/shared/native payload outside the
reviewed routing/manifest exception is protected by compilation and package
comparison. Actual coexisting Kodi/Cobra playback cannot be claimed from source
preservation: it remains a physical check. No shutdown suite was selected.

App-specific Open with presentation, account/provider permissions, supported
codecs/DRM and real Fold acceptance are documented in `LABEL-COMPATIBILITY.md` and
`FOLD-ACCEPTANCE.md`. No benchmark or universal third-party compatibility claim is
made from the synthetic fixture.
