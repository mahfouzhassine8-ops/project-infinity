# Cobra 2103206 — Media During Calls

Parent: locked 2103205, d4abe960873929ebee3f13af6a976c19011d0cdc.
New setting: Channel playback → Media During Calls. Applies to all Cobra playback.
Default: Normal Android Behavior. Opt-in: Allow When Manually Resumed.

Calls/focus loss yield audio; the existing video/session remains owned and intact.
The opt-in lets an explicit Play request normal MEDIA/MOVIE focus again. Denial or
delayed focus stays muted until an accepted grant. No automatic retry on call
arrival, mode change, PiP return or same-player handoff. During a known active
communication mode, the existing transport shows Play when audio needs manual
resume; one tap reasserts the same player's pause/play intent without preparing,
seeking, retuning, or replacing it. Switching off revokes call-time authorization.

AudioManager mode is a communication hint, not proof of a cellular call. API 31+
mode observation is registered and removed with the existing focus owner; older
Android samples mode at focus/Play events. No telephony permission, call details,
route forcing, Samsung private API, or system volume changes. Unknown modes retain
normal focus handling. Call-time audibility cannot be proven by the app or tests.

The runtime patch changes one existing Java template. No native engine, manifest,
provider, timeshift transport, renderer, source ownership or theme changes. The
existing PiP/background MediaSessions remain the owners of their controls.
Health Center reports policy, mode hint, manual attempt, current focus grant and
app mute independently from real audibility.

Verification gates: immutable parent inventory; frozen patch/test hashes; protected
non-audio members; 637 inherited Android case identities plus exact new cases;
two independently signed Java-only replicas; permanent signer/package/version;
native/assets/resources byte preservation; no new permissions/exported components.
Host/Android tests do not establish physical call mixing, Fold, PiP/SystemUI,
decoding, update installation, provider streaming, or timeshift during a real call.
Physical acceptance remains required, and this candidate is not automatically locked.

Platform references reviewed 2026-09-21:
- https://developer.android.com/media/optimize/audio-focus
- https://developer.android.com/reference/android/media/AudioManager#getMode()
- https://developer.android.com/reference/android/media/AudioManager#addOnModeChangedListener(java.util.concurrent.Executor,%20android.media.AudioManager.OnModeChangedListener)

Android may continue muting an already active player or deny/delay media focus.
The implementation attempts user-requested media playback, not a telephony bypass
or a guarantee of YouTube's internal implementation. Actual Samsung behavior must
be tested with the user's OS, call type, route, and optional Multi Sound setup.
