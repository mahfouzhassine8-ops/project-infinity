# Cobra 2103164 playback stability audit

## Identity and status

Audited source: exact passed 2103163 commit `8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261`, Actions run `35331099172`.
Protected Candidate 14 remains `1465eabb045badad56142642c48292df94caaa12` / versionCode 2103162.
Candidate 2103164 is isolated, not a replacement lock. This report distinguishes verified source defects from device reproduction: no physical phone was attached, so the user's exact installed-build behavior was not reproduced here.

The final 2103163 Activity and service were reconstructed from the successful run's evidence and checked against the final source receipt. The exact pre-audit signed APK is SHA-256 `501781d42d87839d8f1f64f3791bee32a6feae023321286f73437e12107b5df3`. Its artifact ZIP is `895d47d6c267fc53b31f29c18ead28d34712b723fe59c25ea1fd6bd88009729a`.
Rollback source branch: `rollback-cobra-2103163-before-stability-audit-20260918`.

## Confirmed source defects and implemented corrections

| Finding | Original behavior | Correction in isolated candidate |
|---|---|---|
| PiP close lifecycle gap | onStop skipped pausing whenever cached/framework PiP was true; the later false callback only restored UI. | Explicit visibility/PiP ownership policy. Both close callback orders halt hidden playback, clear lifecycle auto-resume entries, and revoke mini audio. Expanding PiP into a resumed Activity is distinct from closing it. |
| Two PiP entry mechanisms | Android 12 auto-entry coexisted with manual entry from onUserLeaveHint. Eligibility did not consistently follow requested playback. | Android 12+ uses auto-entry for single video; older/manual multiview handoff remains explicit. Paused video is ineligible; buffering remains eligible when play is requested. Add video source bounds hint. |
| Background start/stop race | A pending service start was not canceled when stop saw neither running flag set. | Synchronous ownership generation revocation, including pending starts. Old intents cannot grant a session; old notification commands and old Activity owners cannot control a replacement. |
| Incorrect native media session | Always STATE_PLAYING at position zero; no transport callbacks or notification controls. | Real playing/buffering/paused state and position, native Play/Pause/Stop bound to the exact existing preview player, no second player, and notification return to existing Cobra Activity. |
| Teardown and failure gaps | Media presence could be detached from live player ownership; a service failure did not reliably pause the owner. | Permission/service failures, unavailable owners, natural end, task removal, and teardown revoke ownership and pause as appropriate. Returning to foreground merely detaches media presence without restarting the stream. |
| Late playback callbacks | Fallback and next-episode callbacks could outlive a pause/dismissal. | Capture a playback epoch and recheck current session, request state, visibility/mini ownership, and dismissal before retry/advance. Preserve ordinary lifecycle resume entries. |
| Audio focus | Audible Media3 players opted out of automatic focus handling. | Existing audible player uses Media3-managed focus. Multiview releases old tile focus before the selected tile claims it. No additional AudioManager competes for ownership. |
| Video-pane menu geometry | Preview More opened a generic channel sheet using window center/bottom gravity; the prior fix only special-cased player-settings. Nested menus discarded the invoking button. | Resolve actual preview/fullscreen button and pane, convert into scrim-local coordinates, clamp within safe window and pane width, choose available space above/below, preserve anchor through nested sheets, and remove layout observers on dismissal. Header and actions share bounded scrolling. |
| Diagnostic ambiguity | PiP/background flags did not expose which session owned continued audio. | Add visibility, PiP ownership, mini player ownership/media status, and playback epoch to existing health diagnostics. |

## Intended behavior

Fullscreen leaving the app belongs to PiP. Closing PiP must stop continued sound and must never silently transfer to mini-player background audio. Expanding PiP should preserve the same active stream.

Only an already-playing mini-player, with PLAY IN BACKGROUND enabled, may retain audio after leaving the app. Android transport controls operate that exact player. Explicit stop, revoked permission, or loss of a valid owner must not leave an invisible or falsely advertised playing session. Native media Pause remains resumable via its current session; Stop revokes it.

## Verification and limits

Executed locally: exact source identity checks, Python syntax checks, 25 executable JVM scenarios using classes extracted from production source, 23 source-wiring checks, 20,000 deterministic randomized geometry cases, and Java parser checks for reconstructed production/test units. These do not simulate physical Android SystemUI or decoding.

CI definition: compile/sign only the Android shell; re-run all 62 inherited Android tests (navigation, guide/Health Center, experience, themes/layout, Candidate 14 rotation/background); run 26 new Activity/service/popup tests; verify signer and version; compare all native libraries, assets, resources, and resources.arsc byte-for-byte against both 2103163 and protected Candidate 14. Publish the signed APK only after every gate passes. CI results are recorded separately in ACCEPTANCE.json; this source report does not assert that CI has passed.

Not certified here: physical PiP gestures/callback timing, fold/unfold, SystemUI media presentation, real audio focus/Bluetooth/calls, decoder recovery, provider network behavior, recording/casting, third-party add-ons, long-duration battery/memory behavior, or upgrade on the user's exact phone. See DEVICE-TEST.md. onStop during PiP is conservatively treated as hidden playback that must pause; lock/unlock behavior requires device acceptance.

No Kodi C/C++ rebuild or native renderer change; no skin/assets/resource changes; no protected branch moved; no uninstall, data clearing, or installation performed. These lifecycle and service changes require an APK runtime update, not a presentation-only theme ZIP.

## Primary references

- Immutable original recipe and service: https://github.com/mahfouzhassine8-ops/project-infinity/tree/8f2c9c7b0fdd7bfcaa0d903f8df997a139c23261/repairs/cobra-candidate14-five-fixes-2103163
- Original successful build: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/35331099172
- Android PiP lifecycle and auto-entry: https://developer.android.com/develop/ui/views/picture-in-picture
- Android audio-focus/ExoPlayer guidance: https://developer.android.com/media/optimize/audio-focus
- Android media controls: https://developer.android.com/media/implement/surfaces/mobile
- MediaSession callbacks: https://developer.android.com/reference/android/media/session/MediaSession.Callback
